"""
================================================================================
Agent Website Builder — BrandAI
================================================================================

Agent linéaire (4 phases déterministes) construit au-dessus de BaseAgent
mais routant vers Azure OpenAI (déploiement gpt-4.1) au lieu de NVIDIA NIM.

Phases exposées :
  1. CONTEXT     → fetch_context()        : idée + brand kit (parallèle)
  2. DESCRIPTION → generate_description() : concept créatif (JSON)
  3. GENERATION  → generate_website()     : HTML/Tailwind/JS complet
  4. REVISION    → revise_website()       : modification ciblée du HTML
  5. DEPLOYMENT  → deploy_website()       : publication Vercel + URL finale

Chaque méthode a une responsabilité unique et peut être appelée indépendamment
par les routes HTTP (cf. `app/routes/website_builder.py`).
================================================================================
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from agents.base_agent import BaseAgent, PipelineState
from config.website_builder_config import (
    DESCRIPTION_MAX_TOKENS,
    DESCRIPTION_TEMPERATURE,
    GENERATION_MAX_TOKENS,
    GENERATION_TEMPERATURE,
    REQUIRED_ANIMATIONS_MIN,
    REQUIRED_SECTIONS_MIN,
    REVISION_MAX_TOKENS,
    REVISION_TEMPERATURE,
    WEBSITE_BUILDER_AZURE_DEPLOYMENT,
    WEBSITE_DESCRIPTION_TIMEOUT_SECONDS,
    WEBSITE_GENERATION_TIMEOUT_SECONDS,
    WEBSITE_LLM_MAX_RETRIES,
    WEBSITE_REVISION_TIMEOUT_SECONDS,
)
from llm.llm_factory import create_azure_openai_client
from prompts.website_builder.prompt_website_description import (
    WEBSITE_DESCRIPTION_SYSTEM,
    build_website_description_user_prompt,
)
from prompts.website_builder.prompt_website_generation import (
    WEBSITE_GENERATION_SYSTEM,
    build_website_generation_user_prompt,
)
from prompts.website_builder.prompt_website_revision import (
    WEBSITE_REVISION_SYSTEM,
    build_website_revision_user_prompt,
)
from tools.website_builder.brand_context_fetch import (
    BrandContext,
    fetch_full_brand_context,
)
from tools.website_builder.vercel_deploy import (
    VercelDeployment,
    deploy_html_to_vercel,
)
from tools.website_builder.website_renderer import (
    extract_html_document,
    html_stats,
    repair_html_document,
    validate_html_document,
)

logger = logging.getLogger("brandai.website_builder.agent")


class WebsiteBuilderAgent(BaseAgent):
    """Pilote les 4 phases du Website Builder via Azure OpenAI gpt-4.1."""

    def __init__(self) -> None:
        super().__init__(
            agent_name="website_builder",
            temperature=DESCRIPTION_TEMPERATURE,
            llm_max_tokens=DESCRIPTION_MAX_TOKENS,
            llm_model=f"azure/{WEBSITE_BUILDER_AZURE_DEPLOYMENT}",
        )

    # ─── BaseAgent.run : non utilisé directement (pipeline classique) ────────
    async def run(self, state: PipelineState) -> Any:
        raise NotImplementedError(
            "WebsiteBuilderAgent : utilise fetch_context / generate_description / "
            "generate_website / revise_website / deploy_website."
        )

    # ─── Override de _call_llm : route vers Azure (BaseAgent route NVIDIA) ──
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        Surchargé pour rester sur Azure OpenAI gpt-4.1.

        BaseAgent._call_llm route vers NVIDIA NIM pour `openai/gpt-oss-120b`
        — on ne veut pas de ça ici.
        """
        return await self._invoke_azure(
            system_prompt,
            user_prompt,
            temperature=self.temperature,
            max_tokens=self.llm_max_tokens,
        )

    async def _invoke_azure(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float,
        max_tokens: int,
        phase: str = "unknown",
        timeout_seconds: float = 90.0,
    ) -> str:
        client = create_azure_openai_client(
            temperature=temperature,
            max_tokens=max_tokens,
            azure_deployment=WEBSITE_BUILDER_AZURE_DEPLOYMENT,
            max_retries=1,
        )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = None
        timeout_exc: Exception | None = None
        for attempt in range(1 + max(0, WEBSITE_LLM_MAX_RETRIES)):
            started = time.monotonic()
            logger.info(
                "[website_builder] AZURE CALL START phase=%s attempt=%d/%d deployment=%s temp=%.2f max_tokens=%d prompt_chars=%d timeout=%s",
                phase,
                attempt + 1,
                1 + max(0, WEBSITE_LLM_MAX_RETRIES),
                WEBSITE_BUILDER_AZURE_DEPLOYMENT,
                temperature,
                max_tokens,
                len(system_prompt) + len(user_prompt),
                f"{timeout_seconds:.1f}s" if timeout_seconds and timeout_seconds > 0 else "disabled",
            )
            try:
                if timeout_seconds and timeout_seconds > 0:
                    response = await asyncio.wait_for(
                        client.ainvoke(messages),
                        timeout=timeout_seconds,
                    )
                else:
                    response = await client.ainvoke(messages)
                break
            except (TimeoutError, asyncio.TimeoutError) as exc:
                timeout_exc = exc
                elapsed = time.monotonic() - started
                logger.warning(
                    "[website_builder] AZURE CALL TIMEOUT phase=%s attempt=%d after %.2fs",
                    phase,
                    attempt + 1,
                    elapsed,
                )
                if attempt < WEBSITE_LLM_MAX_RETRIES:
                    await asyncio.sleep(1.2 * (attempt + 1))
                continue
            except Exception as exc:
                elapsed = time.monotonic() - started
                logger.error(
                    "[website_builder] AZURE CALL ERROR phase=%s attempt=%d after %.2fs error=%s: %s",
                    phase,
                    attempt + 1,
                    elapsed,
                    type(exc).__name__,
                    str(exc)[:300],
                )
                if attempt < WEBSITE_LLM_MAX_RETRIES:
                    await asyncio.sleep(1.2 * (attempt + 1))
                    continue
                raise RuntimeError(
                    f"Azure OpenAI erreur non-récupérable phase={phase}: {exc}"
                ) from exc

        if response is None:
            if timeout_exc is not None:
                raise RuntimeError(
                    f"Azure OpenAI timeout pendant la phase {phase} "
                    f"(>{timeout_seconds:.0f}s, retries={WEBSITE_LLM_MAX_RETRIES})."
                ) from timeout_exc
            raise RuntimeError(
                f"Azure OpenAI n'a retourné aucune réponse exploitable (phase={phase})."
            )

        elapsed = time.monotonic() - started
        content = (response.content or "").strip()
        logger.info(
            "[website_builder] AZURE CALL SUCCESS phase=%s elapsed=%.2fs output_chars=%d",
            phase,
            elapsed,
            len(content),
        )
        if not content:
            raise RuntimeError("Azure OpenAI a renvoyé une réponse vide.")
        return content

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 1 — CONTEXT
    # ─────────────────────────────────────────────────────────────────────────
    async def fetch_context(
        self,
        *,
        idea_id: int,
        access_token: str,
    ) -> BrandContext:
        """Phase 1 : récupère idea + brand kit normalisés."""
        return await fetch_full_brand_context(idea_id, access_token)

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 2 — DESCRIPTION
    # ─────────────────────────────────────────────────────────────────────────
    async def generate_description(self, *, ctx: BrandContext) -> dict[str, Any]:
        """Phase 2 : décrit le site à construire (JSON créatif)."""
        logger.info("[website_builder] PHASE 2 (DESCRIPTION) START idea_id=%s", ctx.idea_id)
        user_prompt = build_website_description_user_prompt(ctx)
        raw = await self._invoke_azure(
            WEBSITE_DESCRIPTION_SYSTEM,
            user_prompt,
            temperature=DESCRIPTION_TEMPERATURE,
            max_tokens=DESCRIPTION_MAX_TOKENS,
            phase="description",
            timeout_seconds=WEBSITE_DESCRIPTION_TIMEOUT_SECONDS,
        )
        data = self._parse_json(raw)
        _validate_description_payload(data)
        logger.info(
            "[website_builder] PHASE 2 (DESCRIPTION) SUCCESS idea_id=%s sections=%d animations=%d",
            ctx.idea_id,
            len(data.get("sections") or []),
            len(data.get("animations") or []),
        )
        return data

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 3 — GENERATION
    # ─────────────────────────────────────────────────────────────────────────
    async def generate_website(
        self,
        *,
        ctx: BrandContext,
        description: dict[str, Any],
    ) -> str:
        """Phase 3 : produit le HTML/Tailwind/JS complet."""
        logger.info("[website_builder] PHASE 3 (GENERATION) START idea_id=%s", ctx.idea_id)
        user_prompt = build_website_generation_user_prompt(ctx, description)
        raw = await self._invoke_azure(
            WEBSITE_GENERATION_SYSTEM,
            user_prompt,
            temperature=GENERATION_TEMPERATURE,
            max_tokens=GENERATION_MAX_TOKENS,
            phase="generation",
            timeout_seconds=WEBSITE_GENERATION_TIMEOUT_SECONDS,
        )
        html = extract_html_document(raw)
        html = repair_html_document(html)
        validate_html_document(html)
        stats = html_stats(html)
        logger.info(
            "[website_builder] PHASE 3 (GENERATION) SUCCESS idea_id=%s length=%d lines=%d",
            ctx.idea_id,
            stats["length"],
            stats["approx_lines"],
        )
        return html

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 4 — REVISION
    # ─────────────────────────────────────────────────────────────────────────
    async def revise_website(
        self,
        *,
        ctx: BrandContext,
        current_html: str,
        instruction: str,
    ) -> str:
        """Phase 4 : applique une modification ciblée et renvoie le HTML modifié."""
        instruction = (instruction or "").strip()
        if not instruction:
            raise ValueError("instruction vide : impossible de réviser le site.")
        if not current_html or "<html" not in current_html.lower():
            raise ValueError("current_html invalide : pas de balise <html>.")

        logger.info(
            "[website_builder] PHASE 4 (REVISION) START idea_id=%s instruction=%r",
            ctx.idea_id,
            instruction[:120],
        )
        user_prompt = build_website_revision_user_prompt(ctx, current_html, instruction)
        raw = await self._invoke_azure(
            WEBSITE_REVISION_SYSTEM,
            user_prompt,
            temperature=REVISION_TEMPERATURE,
            max_tokens=REVISION_MAX_TOKENS,
            phase="revision",
            timeout_seconds=WEBSITE_REVISION_TIMEOUT_SECONDS,
        )
        html = extract_html_document(raw)
        html = repair_html_document(html)
        validate_html_document(html)
        stats = html_stats(html)
        logger.info(
            "[website_builder] PHASE 4 (REVISION) SUCCESS idea_id=%s length=%d lines=%d",
            ctx.idea_id,
            stats["length"],
            stats["approx_lines"],
        )
        return html

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 5 — DEPLOYMENT (Vercel)
    # ─────────────────────────────────────────────────────────────────────────
    async def deploy_website(
        self,
        *,
        ctx: BrandContext,
        html: str,
    ) -> VercelDeployment:
        """Phase 5 : publie le HTML sur Vercel et attend l'état READY."""
        validate_html_document(html)
        return await deploy_html_to_vercel(
            html=html,
            idea_id=ctx.idea_id,
            brand_name=ctx.brand_name,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Validation Phase 2
# ─────────────────────────────────────────────────────────────────────────────
def _validate_description_payload(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise RuntimeError("Description invalide : payload non dict.")

    sections = data.get("sections")
    if not isinstance(sections, list) or len(sections) < REQUIRED_SECTIONS_MIN:
        raise RuntimeError(
            f"Description invalide : il faut au moins {REQUIRED_SECTIONS_MIN} sections "
            f"(reçu: {len(sections) if isinstance(sections, list) else 0})."
        )
    for idx, section in enumerate(sections):
        if not isinstance(section, dict):
            raise RuntimeError(f"Description invalide : section #{idx} n'est pas un objet.")
        if not str(section.get("title") or "").strip():
            raise RuntimeError(f"Description invalide : section #{idx} sans titre.")

    animations = data.get("animations")
    if not isinstance(animations, list) or len(animations) < REQUIRED_ANIMATIONS_MIN:
        raise RuntimeError(
            f"Description invalide : il faut au moins {REQUIRED_ANIMATIONS_MIN} animations "
            f"(reçu: {len(animations) if isinstance(animations, list) else 0})."
        )

    for required_key in ("hero_concept", "user_summary", "tone_of_voice"):
        if not str(data.get(required_key) or "").strip():
            raise RuntimeError(f"Description invalide : champ '{required_key}' manquant.")
