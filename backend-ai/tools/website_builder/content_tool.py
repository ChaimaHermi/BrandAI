"""
Phase 2B — Génération du contenu textuel pour chaque section.

Reçoit l'architecture et produit le contenu de chaque section (textes, icônes Lucide).
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from config.website_builder_config import (
    CONTENT_MAX_TOKENS,
    CONTENT_TEMPERATURE,
    WEBSITE_DESCRIPTION_TIMEOUT_SECONDS,
)
from prompts.website_builder.prompt_content import (
    WEBSITE_CONTENT_SYSTEM,
    build_content_user_prompt,
)
from tools.website_builder.brand_context_fetch import BrandContext
from tools.website_builder.validator_tool import validate_content_payload

logger = logging.getLogger("brandai.website_builder.content_tool")


async def generate_website_content(
    *,
    ctx: BrandContext,
    architecture: dict[str, Any],
    invoke_llm: Callable[..., Awaitable[str]],
    parse_json: Callable[[str], dict[str, Any]],
) -> dict[str, Any]:
    logger.info("[website_builder] PHASE 2B (CONTENT) START idea_id=%s", ctx.idea_id)
    user_prompt = build_content_user_prompt(ctx, architecture)
    raw = await invoke_llm(
        WEBSITE_CONTENT_SYSTEM,
        user_prompt,
        temperature=CONTENT_TEMPERATURE,
        max_tokens=CONTENT_MAX_TOKENS,
        phase="content",
        timeout_seconds=WEBSITE_DESCRIPTION_TIMEOUT_SECONDS,
    )
    data = parse_json(raw)
    validate_content_payload(data, architecture)
    section_count = len((data.get("sections") or {}).keys())
    logger.info(
        "[website_builder] PHASE 2B (CONTENT) SUCCESS idea_id=%s sections=%d",
        ctx.idea_id,
        section_count,
    )
    return data
