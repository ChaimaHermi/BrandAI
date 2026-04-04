import asyncio
import base64
import json
import logging
import os
import sys
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

from agents.base_agent import BaseAgent, PipelineState
from config.branding_config import (
    LOGO_IMAGE_PROVIDER,
    LOGO_IMAGE_SIZE,
    LOGO_LLM_CONFIG,
    LOGO_OPENROUTER_MODEL,
)
from llm.llm_factory import create_azure_openai_client
from prompts.branding.logo_prompt import LOGO_IMAGE_PROMPT_SYSTEM, build_logo_user_message
from tools.branding.logo_image_client import (
    fetch_logo_image_openrouter_flux,
    fetch_logo_image_pollinations,
)

logger = logging.getLogger("brandai.logo_agent")


def _trunc_log(text: str, max_len: int = 2500) -> str:
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[:max_len] + f"... [tronqué, {len(t)} caractères au total]"


def _print_prompt_to_terminal(image_prompt: str, negative_prompt: str) -> None:
    """Affiche le prompt image sur stderr (visible même si les loggers sont mal configurés). Désactiver : LOGO_PRINT_IMAGE_PROMPT=0."""
    v = (os.getenv("LOGO_PRINT_IMAGE_PROMPT") or "1").strip().lower()
    if v in ("0", "false", "no", "off"):
        return
    lines = [
        "",
        "======== [logo_agent] PROMPT IMAGE (LLM) ========",
        (image_prompt or "").strip(),
    ]
    if (negative_prompt or "").strip():
        lines.extend(["-------- negative_prompt --------", negative_prompt.strip()])
    lines.append("======== fin prompt image ========\n")
    print("\n".join(lines), file=sys.stderr, flush=True)


def _extract_json_object(raw: str) -> dict[str, Any]:
    t = (raw or "").strip()
    if t.startswith("```"):
        lines = t.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines).strip()
    start = t.find("{")
    end = t.rfind("}")
    if start >= 0 and end > start:
        t = t[start : end + 1]
    data = json.loads(t)
    if not isinstance(data, dict):
        raise ValueError("LLM output is not a JSON object")
    return data


def _normalize_logo_result(data: dict[str, Any]) -> tuple[str, str]:
    ip = str(data.get("image_prompt") or "").strip()
    np = str(data.get("negative_prompt") or "").strip()
    if not ip:
        raise ValueError("Missing image_prompt in LLM JSON")
    return ip, np


class LogoAgent(BaseAgent):
    """Rédige un prompt image via LLM puis génère l’image (OpenRouter FLUX / option Pollinations) ou skip si none."""

    def __init__(self):
        super().__init__(
            agent_name="logo_agent",
            temperature=LOGO_LLM_CONFIG["temperature"],
            llm_model="gpt-4.1",
            llm_max_tokens=min(LOGO_LLM_CONFIG.get("max_tokens") or 900, 1200),
        )
        self._provider = LOGO_LLM_CONFIG.get("provider", "azure")
        self._logo_max_tokens = min(LOGO_LLM_CONFIG.get("max_tokens") or 900, 1200)

    async def _invoke_logo_llm(self, system_prompt: str, user_prompt: str) -> str:
        if self._provider == "azure":
            from config.settings import AZURE_OPENAI_LOGO_DEPLOYMENT

            deployment = (AZURE_OPENAI_LOGO_DEPLOYMENT or "").strip() or None
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
            attempt = 0
            last_error = None
            while attempt < self.max_retries:
                try:
                    llm = create_azure_openai_client(
                        temperature=self.temperature,
                        max_tokens=self._logo_max_tokens,
                        azure_deployment=deployment,
                    )
                    response = await llm.ainvoke(messages)
                    content = response.content if response else ""
                    if not (content or "").strip():
                        raise RuntimeError("Empty response from Azure")
                    return content
                except Exception as e:
                    last_error = e
                    attempt += 1
                    await asyncio.sleep(2**attempt)
            raise RuntimeError(f"Azure logo LLM failed: {last_error}")

        return await self._call_llm(system_prompt, user_prompt)

    @staticmethod
    async def _maybe_fetch_image(
        image_prompt: str,
        negative_prompt: str,
    ) -> tuple[bytes | None, str | None]:
        provider = (LOGO_IMAGE_PROVIDER or "openrouter_flux").strip().lower()
        if provider == "none":
            return None, None
        if provider in ("openrouter_flux", "openrouter", "flux"):
            data, mime = await fetch_logo_image_openrouter_flux(
                image_prompt,
                negative_prompt,
                model=LOGO_OPENROUTER_MODEL,
            )
            return data, mime
        if provider == "pollinations":
            full = image_prompt
            if negative_prompt:
                full = f"{image_prompt}. Avoid: {negative_prompt}"
            data = await fetch_logo_image_pollinations(
                full,
                width=LOGO_IMAGE_SIZE,
                height=LOGO_IMAGE_SIZE,
            )
            return data, "image/png"
        logger.warning("LOGO_IMAGE_PROVIDER inconnu: %s — pas d’image générée", provider)
        return None, None

    @traceable(name="logo_agent.run", tags=["branding", "logo_agent"])
    async def run(self, state: PipelineState) -> PipelineState:
        self._log_start(state)

        if not hasattr(state, "brand_identity") or state.brand_identity is None:
            state.brand_identity = {}

        brand_name = str(getattr(state, "brand_name_chosen", "") or "").strip()
        if not brand_name:
            msg = "brand_name_chosen est requis pour générer un logo"
            state.brand_identity["logo_error"] = msg
            state.brand_identity["branding_status"] = "logo_failed"
            state.status = "logo_failed"
            state.errors.append(f"logo_agent: {msg}")
            self._log_error(msg)
            return state

        idea = state.clarified_idea or {}
        slogan_hint = str(getattr(state, "palette_slogan_hint", "") or "").strip()
        palette_hint = str(getattr(state, "logo_palette_hint", "") or "").strip()

        try:
            user_prompt = build_logo_user_message(
                idea,
                brand_name,
                slogan_hint,
                palette_hint,
            )
            logger.info(
                "[logo_agent] Étape 1/2 — Appel LLM pour le prompt image (marque=%r)",
                brand_name,
            )
            raw = await self._invoke_logo_llm(LOGO_IMAGE_PROMPT_SYSTEM, user_prompt)
            data = _extract_json_object(raw)
            image_prompt, negative_prompt = _normalize_logo_result(data)
            logger.info(
                "[logo_agent] Prompt image généré (FLUX / modèle image) — image_prompt:\n%s",
                _trunc_log(image_prompt),
            )
            if negative_prompt:
                logger.info(
                    "[logo_agent] negative_prompt:\n%s",
                    _trunc_log(negative_prompt, max_len=1200),
                )
            _print_prompt_to_terminal(image_prompt, negative_prompt)
        except Exception as e:
            msg = f"logo prompt LLM: {e}"
            logger.exception("logo_agent LLM failed")
            state.brand_identity["logo_error"] = msg
            state.brand_identity["branding_status"] = "logo_failed"
            state.status = "logo_failed"
            state.errors.append(f"logo_agent: {msg}")
            return state

        image_bytes: bytes | None = None
        mime: str | None = None
        provider = (LOGO_IMAGE_PROVIDER or "openrouter_flux").strip().lower()
        try:
            if provider == "none":
                logger.info(
                    "[logo_agent] Étape 2/2 — Génération image désactivée (LOGO_IMAGE_PROVIDER=none)"
                )
            else:
                extra = ""
                if provider in ("openrouter_flux", "openrouter", "flux"):
                    extra = f", modèle={LOGO_OPENROUTER_MODEL}"
                elif provider == "pollinations":
                    extra = f", taille={LOGO_IMAGE_SIZE}px"
                logger.info(
                    "[logo_agent] Étape 2/2 — Génération image (%s%s)",
                    provider,
                    extra,
                )
            image_bytes, mime = await self._maybe_fetch_image(image_prompt, negative_prompt)
        except Exception as e:
            logger.error("logo image fetch failed: %s", e)
            state.brand_identity["logo_image_error"] = str(e)
            logger.info(
                "[logo_agent] Rappel — prompt image conservé (étape 2 échouée) :\n%s",
                _trunc_log(image_prompt, max_len=4000),
            )

        b64: str | None = None
        if image_bytes:
            b64 = base64.standard_b64encode(image_bytes).decode("ascii")
            logger.info(
                "[logo_agent] Image générée OK — %s, %d octets (base64 non loggé)",
                mime or "image",
                len(image_bytes),
            )
        elif not state.brand_identity.get("logo_image_error"):
            if provider == "none":
                pass
            else:
                logger.warning(
                    "[logo_agent] Aucun octet image reçu (provider=%s) — voir logo_image_error si défini",
                    provider,
                )

        concept = {
            "title": "Generated mark",
            "image_prompt": image_prompt,
            "negative_prompt": negative_prompt,
            "image_provider": (LOGO_IMAGE_PROVIDER or "openrouter_flux").lower(),
        }
        if b64 and mime:
            concept["image_base64"] = b64
            concept["image_mime"] = mime

        state.brand_identity["logo_concepts"] = [concept]
        state.brand_identity["branding_status"] = "logo_generated"
        state.brand_identity.pop("logo_error", None)
        state.status = "logo_generated"
        return state
