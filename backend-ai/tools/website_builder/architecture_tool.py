"""
Phase 2A — Architecture du site vitrine.

Génère uniquement la structure (sections, navigation, animations) — pas de contenu.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from config.website_builder_config import (
    ARCHITECTURE_MAX_TOKENS,
    ARCHITECTURE_TEMPERATURE,
    WEBSITE_DESCRIPTION_TIMEOUT_SECONDS,
)
from prompts.website_builder.prompt_architecture import (
    WEBSITE_ARCHITECTURE_SYSTEM,
    build_architecture_user_prompt,
)
from tools.website_builder.brand_context_fetch import BrandContext
from tools.website_builder.validator_tool import validate_architecture_payload

logger = logging.getLogger("brandai.website_builder.architecture_tool")


async def generate_website_architecture(
    *,
    ctx: BrandContext,
    invoke_llm: Callable[..., Awaitable[str]],
    parse_json: Callable[[str], dict[str, Any]],
) -> dict[str, Any]:
    logger.info("[website_builder] PHASE 2A (ARCHITECTURE) START idea_id=%s", ctx.idea_id)
    user_prompt = build_architecture_user_prompt(ctx)
    raw = await invoke_llm(
        WEBSITE_ARCHITECTURE_SYSTEM,
        user_prompt,
        temperature=ARCHITECTURE_TEMPERATURE,
        max_tokens=ARCHITECTURE_MAX_TOKENS,
        phase="architecture",
        timeout_seconds=WEBSITE_DESCRIPTION_TIMEOUT_SECONDS,
    )
    data = parse_json(raw)
    validate_architecture_payload(data)
    logger.info(
        "[website_builder] PHASE 2A (ARCHITECTURE) SUCCESS idea_id=%s sections=%d animations=%d",
        ctx.idea_id,
        len(data.get("sections") or []),
        len(data.get("animations") or []),
    )
    return data
