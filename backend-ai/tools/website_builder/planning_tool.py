from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from config.website_builder_config import (
    DESCRIPTION_MAX_TOKENS,
    DESCRIPTION_TEMPERATURE,
    WEBSITE_DESCRIPTION_TIMEOUT_SECONDS,
)
from prompts.website_builder.prompt_website_description import (
    WEBSITE_DESCRIPTION_SYSTEM,
    build_website_description_user_prompt,
)
from tools.website_builder.brand_context_fetch import BrandContext
from tools.website_builder.validator_tool import validate_description_payload

logger = logging.getLogger("brandai.website_builder.planning_tool")


async def generate_website_plan(
    *,
    ctx: BrandContext,
    invoke_llm: Callable[..., Awaitable[str]],
    parse_json: Callable[[str], dict[str, Any]],
) -> dict[str, Any]:
    logger.info("[website_builder] PHASE 2 (DESCRIPTION) START idea_id=%s", ctx.idea_id)
    user_prompt = build_website_description_user_prompt(ctx)
    raw = await invoke_llm(
        WEBSITE_DESCRIPTION_SYSTEM,
        user_prompt,
        temperature=DESCRIPTION_TEMPERATURE,
        max_tokens=DESCRIPTION_MAX_TOKENS,
        phase="description",
        timeout_seconds=WEBSITE_DESCRIPTION_TIMEOUT_SECONDS,
    )
    data = parse_json(raw)
    validate_description_payload(data)
    logger.info(
        "[website_builder] PHASE 2 (DESCRIPTION) SUCCESS idea_id=%s sections=%d animations=%d",
        ctx.idea_id,
        len(data.get("sections") or []),
        len(data.get("animations") or []),
    )
    return data

