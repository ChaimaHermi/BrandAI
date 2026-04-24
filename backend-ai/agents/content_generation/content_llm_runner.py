"""
================================================================================
ContentLLMRunner — sous-couche LLM pour les tools ReAct
================================================================================

Utilisé **uniquement** depuis les outils `draft_post` et `build_image_prompt`
(`content_react_agent.py`). Ne pilote pas l’ordre des étapes : c’est le rôle
de l’agent ReAct.

- `draft_post` : légende du post (texte libre, prompts dans `prompt_draft_post.py`).
- `build_image_prompt` : JSON { image_prompt, negative_prompt } (`prompt_build_image.py`).

Le modèle est `openai/gpt-oss-120b` via `BaseAgent._call_llm` (NVIDIA NIM uniquement).
================================================================================
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from agents.base_agent import BaseAgent, PipelineState
from config.content_generation_config import CONTENT_LLM_CONFIG
from prompts.content_generation.prompt_build_image import PROMPT_BUILD_IMAGE_SYSTEM
from prompts.content_generation.prompt_draft_post import PROMPT_DRAFT_POST_SYSTEM

logger = logging.getLogger("brandai.content_llm_runner")


class ContentLLMRunner(BaseAgent):
    """Deux appels LLM : légende + prompts image (JSON)."""

    def __init__(self) -> None:
        c = CONTENT_LLM_CONFIG
        super().__init__(
            "content_llm_runner",
            temperature=float(c.get("temperature", 0.35)),
            llm_model=c.get("model", "openai/gpt-oss-120b"),
            llm_max_tokens=int(c.get("max_tokens", 65_536)),
        )

    async def run(self, state: PipelineState) -> dict[str, Any]:
        return {}

    async def draft_post(
        self,
        merged_json: str,
        spec_json: str,
        *,
        previous_caption: str | None = None,
        regeneration_instruction: str | None = None,
    ) -> str:
        user = (
            "Contexte fusionné (merged_context) :\n"
            f"{merged_json}\n\n"
            "Spécifications plateforme (spec) :\n"
            f"{spec_json}\n"
        )
        prev = (previous_caption or "").strip()
        instruction = (regeneration_instruction or "").strip()
        if prev and instruction:
            user += (
                "\n\nMode régénération guidée :\n"
                "Texte généré précédent (à améliorer, pas à ignorer) :\n"
                f"{prev}\n\n"
                "Consigne utilisateur à appliquer :\n"
                f"{instruction}\n"
            )
        raw = await self._call_llm(PROMPT_DRAFT_POST_SYSTEM, user)
        caption = (raw or "").strip()
        if not caption:
            raise RuntimeError("draft_post : légende vide.")
        logger.info("[draft_post] len=%d", len(caption))
        return caption

    async def build_image_prompt(self, merged_json: str, spec_json: str, caption: str) -> tuple[str, str]:
        user = (
            "Contexte fusionné :\n"
            f"{merged_json}\n\n"
            "Spec plateforme :\n"
            f"{spec_json}\n\n"
            "Légende du post (pour cohérence visuelle) :\n"
            f"{caption}\n"
        )
        raw = await self._call_llm(PROMPT_BUILD_IMAGE_SYSTEM, user)
        data = self._parse_image_json(raw)
        ip = str(data.get("image_prompt") or "").strip()
        np = str(data.get("negative_prompt") or "").strip()
        if not ip:
            raise RuntimeError("build_image_prompt : image_prompt manquant.")
        logger.info("[build_image_prompt] image_prompt len=%d", len(ip))
        return ip, np

    def _parse_image_json(self, raw: str) -> dict[str, Any]:
        s = (raw or "").strip()
        s = re.sub(r"```(?:json)?\s*|\s*```", "", s, flags=re.IGNORECASE).strip()
        try:
            data = json.loads(s)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        start = s.find("{")
        end = s.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(s[start : end + 1])
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass
        raise RuntimeError("build_image_prompt : JSON invalide.")
