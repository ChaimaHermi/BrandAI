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
    GENERATION_MODEL,
    GENERATION_TEMPERATURE,
    WEBSITE_GENERATION_TIMEOUT_SECONDS,
)
from prompts.website_builder.prompt_coder import (
    WEBSITE_CODER_SYSTEM,
    build_coder_user_prompt,
)
from tools.website_builder.context.brand_context_fetch import BrandContext
from tools.website_builder.infra.langsmith_traces import (
    TAGS_TOOL,
    process_coder_inputs,
    process_coder_outputs,
)
from tools.website_builder.generation.website_renderer import extract_html_document, repair_html_document

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


def _check_html_quality(html: str, brand_name: str) -> list[str]:
    """
    Vérifie rapidement la qualité du HTML généré.
    Retourne la liste des problèmes détectés (vide = HTML correct).
    """
    problems: list[str] = []
    if not html or not html.strip():
        problems.append("HTML vide")
        return problems
    if len(html) < 3000:
        problems.append(f"HTML trop court ({len(html)} chars) — site probablement incomplet")
    lower = html.lower()
    if "<html" not in lower:
        problems.append("balise <html manquante")
    if "</html>" not in lower:
        problems.append("balise </html> manquante — HTML tronqué")
    if brand_name and brand_name.lower() not in lower:
        problems.append(f"nom de marque '{brand_name}' absent du HTML")
    if "sm:" not in html and "md:" not in html:
        problems.append("aucune classe responsive Tailwind (sm:/md:) — site non responsive")
    return problems


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
    metadata={"step": "html_generation", "model": GENERATION_MODEL},
    process_inputs=process_coder_inputs,
    process_outputs=process_coder_outputs,
)
async def build_website_html(
    *,
    ctx: BrandContext,
    architecture: dict[str, Any],
    content: dict[str, Any],
    invoke_llm: Callable[..., Awaitable[str]],
    stream_llm: Callable[..., Any] | None = None,
    on_chunk: Callable[[str, str], Awaitable[None]] | None = None,
) -> str:
    """
    Genere le HTML du site vitrine (Phase 3).

    - Si `stream_llm` est fourni, l'appel passe en mode SSE via GLM-4.7
      (`z-ai/glm4.7`) servi par NVIDIA NIM. `on_chunk(kind, text)` est appele
      pour chaque morceau (kind = 'content' | 'reasoning') pour le relai SSE.
    - Sinon, fallback non-streaming via `invoke_llm` (compatibilite arriere).
    """
    logger.info(
        "[website_builder] PHASE 3 (CODER) START idea_id=%s model=%s stream=%s",
        ctx.idea_id,
        GENERATION_MODEL,
        bool(stream_llm),
    )

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
    current_user_prompt = user_prompt

    for attempt in range(1, max_attempts + 1):
        try:
            if stream_llm is not None:
                buffer: list[str] = []
                reasoning_buffer: list[str] = []
                async for chunk in stream_llm(
                    WEBSITE_CODER_SYSTEM,
                    current_user_prompt,
                    model=GENERATION_MODEL,
                    temperature=GENERATION_TEMPERATURE,
                    max_tokens=GENERATION_MAX_TOKENS,
                    phase="generation",
                ):
                    if not isinstance(chunk, dict):
                        continue
                    piece = chunk.get("content") or ""
                    reasoning = chunk.get("reasoning") or ""
                    if piece:
                        buffer.append(piece)
                        if on_chunk is not None:
                            await on_chunk("content", piece)
                    if reasoning:
                        reasoning_buffer.append(reasoning)
                        if on_chunk is not None:
                            await on_chunk("reasoning", reasoning)
                raw = "".join(buffer)
                reasoning_raw = "".join(reasoning_buffer)
                logger.info(
                    "[website_builder] PHASE 3 stream done attempt=%s/%s content_chars=%d",
                    attempt, max_attempts, len(raw),
                )
                if not raw.strip() and reasoning_raw:
                    rl = reasoning_raw.lower()
                    if "<!doctype" in rl or "<html" in rl:
                        raw = reasoning_raw
                if not raw.strip():
                    raise RuntimeError(
                        f"Le modèle {GENERATION_MODEL} n'a produit aucun contenu. "
                        f"Vérifiez GLM_NVIDIA_API_KEY ou NVIDIA_API_KEY_* dans .env."
                    )
            else:
                raw = await invoke_llm(
                    WEBSITE_CODER_SYSTEM,
                    current_user_prompt,
                    temperature=GENERATION_TEMPERATURE,
                    max_tokens=GENERATION_MAX_TOKENS,
                    phase="generation",
                    timeout_seconds=WEBSITE_GENERATION_TIMEOUT_SECONDS,
                )

            # ── Vérification qualité — retry si problèmes détectés ────────
            candidate = extract_html_document(raw)
            problems = _check_html_quality(candidate, ctx.brand_name)
            if problems and attempt < max_attempts:
                problems_str = " | ".join(problems)
                logger.warning(
                    "[website_builder] PHASE 3 qualité insuffisante attempt=%s/%s "
                    "idea_id=%s problèmes=%s → retry",
                    attempt, max_attempts, ctx.idea_id, problems_str,
                )
                current_user_prompt = (
                    user_prompt
                    + f"\n\n⚠️ TENTATIVE PRÉCÉDENTE REJETÉE — problèmes détectés : {problems_str}\n"
                    "Régénère le site complet en corrigeant ces problèmes."
                )
                continue

            break

        except Exception as exc:  # noqa: BLE001
            if attempt >= max_attempts or not _is_transient_provider_error(exc):
                raise
            logger.warning(
                "[website_builder] CODER erreur transitoire attempt=%s/%s idea_id=%s err=%s",
                attempt, max_attempts, ctx.idea_id, exc,
            )
            await asyncio.sleep(1.2 * attempt)
    html = extract_html_document(raw)
    html = repair_html_document(html)
    logger.info(
        "[website_builder] PHASE 3 (CODER) SUCCESS idea_id=%s html_chars=%d model=%s",
        ctx.idea_id,
        len(html),
        GENERATION_MODEL,
    )
    return html
