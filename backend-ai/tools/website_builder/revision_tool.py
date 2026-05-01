from __future__ import annotations

import logging
import asyncio
from collections.abc import Awaitable, Callable

from config.website_builder_config import (
    REVISION_MAX_TOKENS,
    REVISION_TEMPERATURE,
    WEBSITE_REVISION_TIMEOUT_SECONDS,
)
from prompts.website_builder.prompt_website_revision import (
    WEBSITE_REVISION_SYSTEM,
    build_website_revision_user_prompt,
)
from tools.website_builder.brand_context_fetch import BrandContext
from tools.website_builder.website_renderer import extract_html_document, repair_html_document

logger = logging.getLogger("brandai.website_builder.revision_tool")

_TRANSIENT_STATUS_CODES = {502, 503, 504}


def _is_transient_provider_error(exc: Exception) -> bool:
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if isinstance(status, int) and status in _TRANSIENT_STATUS_CODES:
        return True
    msg = str(exc).lower()
    return "bad gateway" in msg or "gateway timeout" in msg or "service unavailable" in msg


async def revise_website_html(
    *,
    ctx: BrandContext,
    current_html: str,
    instruction: str,
    invoke_llm: Callable[..., Awaitable[str]],
) -> str:
    instruction = (instruction or "").strip()
    if not instruction:
        raise ValueError("instruction vide : impossible de reviser le site.")
    if not current_html or "<html" not in current_html.lower():
        raise ValueError("current_html invalide : pas de balise <html>.")

    logger.info(
        "[website_builder] PHASE 4 (REVISION) START idea_id=%s instruction=%r",
        ctx.idea_id,
        instruction[:120],
    )
    user_prompt = build_website_revision_user_prompt(ctx, current_html, instruction)
    max_attempts = 2
    raw = ""
    for attempt in range(1, max_attempts + 1):
        try:
            raw = await invoke_llm(
                WEBSITE_REVISION_SYSTEM,
                user_prompt,
                temperature=REVISION_TEMPERATURE,
                max_tokens=REVISION_MAX_TOKENS,
                phase="revision",
                timeout_seconds=WEBSITE_REVISION_TIMEOUT_SECONDS,
            )
            break
        except Exception as exc:  # noqa: BLE001
            if attempt >= max_attempts or not _is_transient_provider_error(exc):
                raise
            logger.warning(
                "[website_builder] REVISION transient provider error attempt=%s/%s idea_id=%s err=%s",
                attempt,
                max_attempts,
                ctx.idea_id,
                exc,
            )
            await asyncio.sleep(1.2 * attempt)
    html = extract_html_document(raw)
    return repair_html_document(html)

