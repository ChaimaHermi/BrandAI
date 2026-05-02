"""
Phase 3 — Codeur HTML : transforme architecture + contenu en site complet.

Le LLM ne fait que coder — pas d'invention de contenu ni de structure.
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Awaitable, Callable
from typing import Any

from langsmith import traceable

from config.website_builder_config import (
    GENERATION_MAX_TOKENS,
    GENERATION_TEMPERATURE,
    WEBSITE_GENERATION_TIMEOUT_SECONDS,
)
from prompts.website_builder.prompt_coder import (
    WEBSITE_CODER_SYSTEM,
    build_coder_user_prompt,
)
from tools.website_builder.brand_context_fetch import BrandContext
from tools.website_builder.langsmith_traces import (
    TAGS_TOOL,
    process_coder_inputs,
    process_coder_outputs,
)
from tools.website_builder.website_renderer import extract_html_document, repair_html_document

logger = logging.getLogger("brandai.website_builder.coder_tool")

_PLATFORM_EMAIL_RE = re.compile(r"(brand\s*ai|brandai|support@brandai)", re.IGNORECASE)
_TRANSIENT_STATUS_CODES = {502, 503, 504}


def _is_platform_email(email: str) -> bool:
    return bool(_PLATFORM_EMAIL_RE.search(email or ""))


def _is_transient_provider_error(exc: Exception) -> bool:
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if isinstance(status, int) and status in _TRANSIENT_STATUS_CODES:
        return True
    msg = str(exc).lower()
    return "bad gateway" in msg or "gateway timeout" in msg or "service unavailable" in msg


def _extract_contact_email(architecture: dict[str, Any], content: dict[str, Any]) -> str | None:
    """Cherche l'email de contact dans le JSON content en se basant sur le type 'contact'."""
    arch_sections = architecture.get("sections") or []
    content_sections = (content.get("sections") or {}) if isinstance(content, dict) else {}
    for sec in arch_sections:
        if not isinstance(sec, dict):
            continue
        if str(sec.get("type") or "").lower() == "contact":
            sec_id = str(sec.get("id") or "").strip()
            if sec_id:
                sec_content = content_sections.get(sec_id) or {}
                email = sec_content.get("email")
                if email and isinstance(email, str) and "@" in email:
                    normalized = email.strip()
                    if _is_platform_email(normalized):
                        logger.warning(
                            "[website_builder] contact email ignored (platform address) value=%s",
                            normalized,
                        )
                        return None
                    return normalized
    return None


@traceable(
    name="website_builder.tool.coder_html",
    run_type="tool",
    tags=[*TAGS_TOOL, "phase_3"],
    metadata={"step": "html_generation"},
    process_inputs=process_coder_inputs,
    process_outputs=process_coder_outputs,
)
async def build_website_html(
    *,
    ctx: BrandContext,
    architecture: dict[str, Any],
    content: dict[str, Any],
    invoke_llm: Callable[..., Awaitable[str]],
) -> str:
    logger.info("[website_builder] PHASE 3 (CODER) START idea_id=%s", ctx.idea_id)

    contact_email = _extract_contact_email(architecture, content)
    logger.info(
        "[website_builder] PHASE 3 contact_email=%s (mailto: direct, no backend relay)",
        contact_email or "(none)",
    )

    user_prompt = build_coder_user_prompt(
        ctx,
        architecture,
        content,
        contact_email=contact_email,
    )
    max_attempts = 2
    raw = ""
    for attempt in range(1, max_attempts + 1):
        try:
            raw = await invoke_llm(
                WEBSITE_CODER_SYSTEM,
                user_prompt,
                temperature=GENERATION_TEMPERATURE,
                max_tokens=GENERATION_MAX_TOKENS,
                phase="generation",
                timeout_seconds=WEBSITE_GENERATION_TIMEOUT_SECONDS,
            )
            break
        except Exception as exc:  # noqa: BLE001
            if attempt >= max_attempts or not _is_transient_provider_error(exc):
                raise
            logger.warning(
                "[website_builder] CODER transient provider error attempt=%s/%s idea_id=%s err=%s",
                attempt,
                max_attempts,
                ctx.idea_id,
                exc,
            )
            await asyncio.sleep(1.2 * attempt)
    html = extract_html_document(raw)
    html = repair_html_document(html)
    logger.info(
        "[website_builder] PHASE 3 (CODER) SUCCESS idea_id=%s html_chars=%d",
        ctx.idea_id,
        len(html),
    )
    return html
