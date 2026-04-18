"""
Contexte & specs — étapes « logiques » (sans @tool).

Ces fonctions sont appelées **depuis** les outils LangChain dans
`content_react_agent.py`. Elles mettent à jour `ContentPipelineState` et
appliquent des guards (merge avant spec, etc.).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from tools.content_generation.idea_fetch import fetch_idea_row, idea_to_content_context
from tools.content_generation.platform_specs import get_spec_for_platform

logger = logging.getLogger("brandai.content_context_steps")


class ContentPipelineState(dict[str, Any]):
    """État mutable partagé par les outils (merge → spec → LLM → image)."""

    def __init__(self) -> None:
        super().__init__()

    def ensure_merged(self) -> None:
        if not self.get("merged"):
            raise RuntimeError("Guard: merge_context doit être exécuté en premier.")

    def ensure_spec(self) -> None:
        self.ensure_merged()
        if not self.get("spec"):
            raise RuntimeError("Guard: get_platform_spec doit suivre merge_context.")


async def merge_context_step(
    state: ContentPipelineState,
    *,
    idea_id: int,
    platform: str,
    brief: dict[str, Any],
    access_token: str | None,
) -> dict[str, Any]:
    """Fusionne brief utilisateur + contexte idée (API métier si JWT fourni)."""
    align = brief.get("align_with_project")
    if align is None:
        align = True
    align = bool(align)

    idea_block: dict[str, Any] = {}
    if align and access_token:
        try:
            row = await fetch_idea_row(idea_id, access_token)
            idea_block = idea_to_content_context(row)
        except Exception as e:
            logger.warning("[merge_context] idée non chargée (%s) — brief seul.", e)

    merged = {
        "idea_id": idea_id,
        "platform": platform,
        "brief": brief,
        "align_with_project": align,
        "idea": idea_block,
    }
    state["merged"] = True
    state["merged_context"] = merged
    logger.info("[merge_context] ok | idea_id=%s platform=%s", idea_id, platform)
    return merged


def get_platform_spec_step(state: ContentPipelineState, platform: str) -> dict[str, Any]:
    """Retourne les règles techniques pour la plateforme."""
    state.ensure_merged()
    spec = get_spec_for_platform(platform)
    state["spec"] = spec
    logger.info("[get_platform_spec] ok | platform=%s", platform)
    return spec


def merged_json_for_llm(state: ContentPipelineState) -> str:
    state.ensure_spec()
    return json.dumps(state["merged_context"], ensure_ascii=False, indent=2)


def spec_json_for_llm(state: ContentPipelineState) -> str:
    state.ensure_spec()
    return json.dumps(state["spec"], ensure_ascii=False, indent=2)
