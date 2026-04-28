from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from config.website_builder_config import (
    GENERATION_MAX_TOKENS,
    GENERATION_TEMPERATURE,
    WEBSITE_GENERATION_TIMEOUT_SECONDS,
)
from prompts.website_builder.prompt_website_generation import (
    WEBSITE_GENERATION_SYSTEM,
    build_website_generation_user_prompt,
)
from tools.website_builder.brand_context_fetch import BrandContext
from tools.website_builder.website_renderer import extract_html_document, repair_html_document

logger = logging.getLogger("brandai.website_builder.build_tool")


async def build_website_html(
    *,
    ctx: BrandContext,
    description: dict[str, Any],
    invoke_llm: Callable[..., Awaitable[str]],
) -> str:
    logger.info("[website_builder] PHASE 3 (GENERATION) START idea_id=%s", ctx.idea_id)
    user_prompt = build_website_generation_user_prompt(ctx, description)
    raw = await invoke_llm(
        WEBSITE_GENERATION_SYSTEM,
        user_prompt,
        temperature=GENERATION_TEMPERATURE,
        max_tokens=GENERATION_MAX_TOKENS,
        phase="generation",
        timeout_seconds=WEBSITE_GENERATION_TIMEOUT_SECONDS,
    )
    html = extract_html_document(raw)
    return repair_html_document(html)

