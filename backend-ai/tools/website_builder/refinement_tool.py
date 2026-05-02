"""
Phase 2.5 — Affinage iteratif du concept creatif (avant generation HTML).

L'utilisateur peut, depuis le chat, demander des ajustements de la description
generee en Phase 2. Cet outil reinjecte la description existante + les retours
dans le LLM et renvoie une description mise a jour, validee.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langsmith import traceable

from config.website_builder_config import (
    DESCRIPTION_MAX_TOKENS,
    DESCRIPTION_TEMPERATURE,
    WEBSITE_DESCRIPTION_TIMEOUT_SECONDS,
)
from prompts.website_builder.prompt_description_refinement import (
    WEBSITE_DESCRIPTION_REFINE_SYSTEM,
    build_description_refine_user_prompt,
)
from tools.website_builder.brand_context_fetch import BrandContext
from tools.website_builder.langsmith_traces import (
    TAGS_TOOL,
    process_refine_inputs,
    process_refine_outputs,
)
from tools.website_builder.validator_tool import validate_description_payload

logger = logging.getLogger("brandai.website_builder.refinement_tool")


@traceable(
    name="website_builder.tool.refine_description",
    run_type="tool",
    tags=[*TAGS_TOOL, "phase_2_5"],
    metadata={"step": "description_refinement"},
    process_inputs=process_refine_inputs,
    process_outputs=process_refine_outputs,
)
async def refine_website_description(
    *,
    ctx: BrandContext,
    current_description: dict[str, Any],
    user_feedback: str,
    invoke_llm: Callable[..., Awaitable[str]],
    parse_json: Callable[[str], dict[str, Any]],
) -> dict[str, Any]:
    feedback = (user_feedback or "").strip()
    if not feedback:
        raise ValueError("Retour utilisateur vide : impossible d'affiner la description.")
    if not isinstance(current_description, dict) or not current_description:
        raise ValueError(
            "Description actuelle introuvable : genere d'abord une description (Phase 2)."
        )

    logger.info(
        "[website_builder] PHASE 2.5 (REFINE) START idea_id=%s feedback=%r",
        ctx.idea_id,
        feedback[:120],
    )
    user_prompt = build_description_refine_user_prompt(ctx, current_description, feedback)
    raw = await invoke_llm(
        WEBSITE_DESCRIPTION_REFINE_SYSTEM,
        user_prompt,
        temperature=DESCRIPTION_TEMPERATURE,
        max_tokens=DESCRIPTION_MAX_TOKENS,
        phase="description_refine",
        timeout_seconds=WEBSITE_DESCRIPTION_TIMEOUT_SECONDS,
    )
    data = parse_json(raw)
    validate_description_payload(data)
    logger.info(
        "[website_builder] PHASE 2.5 (REFINE) SUCCESS idea_id=%s sections=%d animations=%d",
        ctx.idea_id,
        len(data.get("sections") or []),
        len(data.get("animations") or []),
    )
    return data
