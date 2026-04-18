"""
================================================================================
Agent ReAct — génération de contenu social (BrandAI)
================================================================================

Mode d'exécution UNIQUE pour la génération : LangGraph `create_react_agent`
avec 5 outils (@tool). L'orchestrateur LLM (NVIDIA NIM / gpt-oss-120b uniquement) enchaîne les
appels selon le prompt système ; l'état partagé `ContentPipelineState` est
rempli par chaque outil.

Flux des outils (ordre attendu, renforcé par le system prompt + guards dans les tools) :
  1. merge_context      → brief + contexte idée (API FastAPI backend-api, optionnel si JWT)
  2. get_platform_spec  → limites / ratios par réseau
  3. draft_post         → légende (LLM via ContentLLMRunner)
  4. build_image_prompt → JSON image_prompt / negative_prompt (si image demandée)
  5. image_client       → HF → Pollinations → upload Cloudinary → URL publique

La route HTTP appelle `run_content_generation` (alias public) qui invoque
l'agent puis valide le résultat avec `_build_generation_result`.

Traçabilité LangSmith : activer `LANGCHAIN_API_KEY` dans `.env` (voir `config/settings.py`).
Projet LangSmith : `brand-ai`. Spans : `content_generation.run` et `content_react_agent.invoke`.

Terminal : `CONTENT_AGENT_VERBOSE_TERMINAL=1` (défaut) affiche Thought / Action / Observation
(`react_trace.py`). Mettre `0` pour désactiver en production.
================================================================================
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

from agents.content_generation.content_llm_runner import ContentLLMRunner
from agents.content_generation.react_trace import invoke_react_with_optional_terminal_trace
from config.content_generation_config import (
    CONTENT_AGENT_VERBOSE_TERMINAL,
    CONTENT_LLM_CONFIG,
)
from llm.llm_factory import create_react_orchestrator_llm
from tools.content_generation.brief_helpers import should_include_image_in_post
from tools.content_generation.cloudinary_upload import (
    cloudinary_configured,
    is_brandai_cloudinary_url,
    upload_image_bytes,
)
from tools.content_generation.context_steps import (
    ContentPipelineState,
    get_platform_spec_step,
    merge_context_step,
    merged_json_for_llm,
    spec_json_for_llm,
)
from tools.content_generation.content_image_client import fetch_content_image_hf_then_pollinations

logger = logging.getLogger("brandai.content_react_agent")

# -----------------------------------------------------------------------------
# Corps réutilisables (outils LangChain + secours si l'orchestrateur saute des étapes)
# -----------------------------------------------------------------------------
async def _tool_build_image_prompt_body(
    state: ContentPipelineState,
    platform: str,
    brief: dict[str, Any],
    runner: ContentLLMRunner,
) -> str:
    if not should_include_image_in_post(platform, brief):
        return json.dumps({"skipped": True, "reason": "include_image false"}, ensure_ascii=False)
    state.ensure_spec()
    cap = state.get("caption") or ""
    if not cap:
        return json.dumps({"error": "draft_post requis avant build_image_prompt"}, ensure_ascii=False)
    merged_j = merged_json_for_llm(state)
    spec_j = spec_json_for_llm(state)
    ip, np = await runner.build_image_prompt(merged_j, spec_j, cap.strip())
    state["image_prompt"] = ip
    state["negative_prompt"] = np
    return json.dumps({"image_prompt": ip[:500], "negative_prompt": np[:300]}, ensure_ascii=False)


async def _tool_image_client_body(
    state: ContentPipelineState,
    platform: str,
    brief: dict[str, Any],
) -> str:
    if not should_include_image_in_post(platform, brief):
        return json.dumps({"skipped": True}, ensure_ascii=False)
    if not state.get("image_prompt"):
        return json.dumps({"error": "build_image_prompt requis avant image_client"}, ensure_ascii=False)
    if not cloudinary_configured():
        return json.dumps(
            {"error": "Cloudinary non configuré (CONTENT_CLOUDINARY_* ou CLOUDINARY_*)"},
            ensure_ascii=False,
        )
    data, mime, src = await fetch_content_image_hf_then_pollinations(
        str(state["image_prompt"]),
        str(state.get("negative_prompt") or ""),
    )
    url = upload_image_bytes(data, mime=mime)
    if not is_brandai_cloudinary_url(url):
        logger.error("[image_client] URL inattendue (pas le compte Cloudinary projet) : %s", url[:120])
    state["image_url"] = url
    state["image_source"] = src
    return url


async def _ensure_image_pipeline_when_brief_requires(
    state: ContentPipelineState,
    *,
    platform: str,
    brief: dict[str, Any],
    runner: ContentLLMRunner,
) -> None:
    """
    L'orchestrateur ReAct peut terminer sans appeler build_image_prompt / image_client
    alors que le brief impose une image. On rejoue alors les mêmes étapes que les outils.
    """
    if not should_include_image_in_post(platform, brief) or state.get("image_url"):
        return
    if not (state.get("caption") or "").strip():
        return
    try:
        state.ensure_spec()
    except RuntimeError as e:
        logger.warning(
            "[content_react_agent] image de secours ignorée (état incomplet) : %s",
            e,
        )
        return
    await _tool_build_image_prompt_body(state, platform, brief, runner)
    if not state.get("image_prompt"):
        return
    await _tool_image_client_body(state, platform, brief)


# -----------------------------------------------------------------------------
# Prompt système — contrat pour le modèle orchestrateur (outil par outil)
# -----------------------------------------------------------------------------
REACT_ORCHESTRATOR_SYSTEM = """Tu es l'orchestrateur de génération de contenu social BrandAI.

Obligation : appeler les outils dans cet ordre, sans sauter d'étape nécessaire :
  1) merge_context — une fois
  2) get_platform_spec — une fois
  3) draft_post — une fois (produit la légende du post)
  4) build_image_prompt — si une image est demandée : lis merged_context.brief.include_image.
     Instagram : image requise sauf si include_image est explicitement false.
     Facebook / LinkedIn : image requise si include_image est true.
  5) image_client — immédiatement après build_image_prompt lorsqu'une image est requise.

Ne rédige pas toi-même le post final dans le chat : délègue aux outils.
Termine par un court message de confirmation une fois les outils nécessaires exécutés."""


# -----------------------------------------------------------------------------
# Fabrique d'outils LangChain — closure sur `state` + paramètres de la requête
# -----------------------------------------------------------------------------
def build_content_react_tools(
    *,
    idea_id: int,
    platform: str,
    brief: dict[str, Any],
    access_token: str | None,
    state: ContentPipelineState,
    runner: ContentLLMRunner,
) -> list:
    """
    Construit les 5 tools @tool. Ils partagent le même `state` (dict mutable)
    pour que merge → spec → … alimentent les étapes suivantes (guards inclus).
    """
    from langchain_core.tools import tool

    # --- 1) Contexte fusionné (brief + idée backend-api FastAPI si token) ---
    @tool
    async def merge_context() -> str:
        """Fusionne le brief utilisateur et le contexte idée (API si JWT). À appeler en premier."""
        await merge_context_step(
            state,
            idea_id=idea_id,
            platform=platform,
            brief=brief,
            access_token=access_token,
        )
        return json.dumps({"status": "merged", "idea_id": idea_id}, ensure_ascii=False)

    # --- 2) Règles techniques plateforme (caractères, ratio image, …) ---
    @tool
    async def get_platform_spec() -> str:
        """Retourne les contraintes techniques (longueur, ratio image) pour la plateforme cible. Après merge_context."""
        spec = get_platform_spec_step(state, platform)
        return json.dumps(spec, ensure_ascii=False)

    # --- 3) Légende finale (appel LLM gpt-oss-120b) ---
    @tool
    async def draft_post() -> str:
        """Génère le texte du post (légende) via le LLM à partir du contexte fusionné et des specs."""
        state.ensure_spec()
        merged_j = merged_json_for_llm(state)
        spec_j = spec_json_for_llm(state)
        caption = await runner.draft_post(merged_j, spec_j)
        state["caption"] = caption
        # Pas de troncature : l’état et l’observation doivent refléter la légende complète.
        return caption

    # --- 4) Prompts pour le générateur d'image (LLM → JSON) ---
    @tool
    async def build_image_prompt() -> str:
        """Produit image_prompt et negative_prompt pour le modèle text-to-image. Après draft_post si image demandée."""
        return await _tool_build_image_prompt_body(state, platform, brief, runner)

    # --- 5) Image bytes (HF / Pollinations) + URL Cloudinary ---
    @tool
    async def image_client() -> str:
        """Génère l'image puis l'upload sur Cloudinary. Après build_image_prompt si image demandée."""
        return await _tool_image_client_body(state, platform, brief)

    return [
        merge_context,
        get_platform_spec,
        draft_post,
        build_image_prompt,
        image_client,
    ]


# -----------------------------------------------------------------------------
# Validation du state après la boucle ReAct → payload API
# -----------------------------------------------------------------------------
def _build_generation_result(
    state: ContentPipelineState,
    *,
    platform: str,
    brief: dict[str, Any],
) -> dict[str, Any]:
    """
    Transforme l'état partagé en réponse HTTP. Lève une erreur explicite si
    l'agent n'a pas mené la génération jusqu'au bout (caption manquante, image
    demandée mais URL absente, etc.).
    """
    caption = (state.get("caption") or "").strip()
    if not caption:
        raise RuntimeError(
            "L'agent n'a pas produit de légende. Vérifiez les clés NVIDIA (NVIDIA_API_KEY_*) "
            "ou augmentez la limite de récursion de l'agent."
        )

    want_image = should_include_image_in_post(platform, brief)
    image_url = state.get("image_url")

    if want_image:
        if not image_url:
            if not cloudinary_configured():
                raise RuntimeError(
                    "Image demandée : configurez Cloudinary (CONTENT_CLOUDINARY_* ou "
                    "CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET) "
                    "pour obtenir une URL publique."
                )
            raise RuntimeError(
                "Image demandée mais aucune URL produite : l'agent doit appeler "
                "build_image_prompt puis image_client dans l'ordre. Réessayez ou augmentez recursion_limit."
            )

    return {
        "caption": caption,
        "image_url": image_url if want_image else None,
        "char_count": len(caption),
        "platform": platform,
    }


# -----------------------------------------------------------------------------
# Point d'entrée principal — utilisé par la route FastAPI
# -----------------------------------------------------------------------------
@traceable(
    name="content_generation.run",
    tags=["content_generation", "api", "brandai"],
)
async def run_content_generation(
    *,
    idea_id: int,
    platform: str,
    brief: dict[str, Any],
    access_token: str | None = None,
    recursion_limit: int = 40,
) -> dict[str, Any]:
    """
    Exécute l'agent ReAct puis retourne un dict { caption, image_url, char_count, platform }.

    C'est la **seule** méthode d'orchestration exposée pour la génération de contenu.
    """
    state = await run_content_react_agent(
        idea_id=idea_id,
        platform=platform,
        brief=brief,
        access_token=access_token,
        recursion_limit=recursion_limit,
    )
    await _ensure_image_pipeline_when_brief_requires(
        state,
        platform=platform,
        brief=brief,
        runner=ContentLLMRunner(),
    )
    return _build_generation_result(state, platform=platform, brief=brief)


@traceable(
    name="content_react_agent.invoke",
    tags=["content_generation", "react", "langgraph", "brandai"],
)
async def run_content_react_agent(
    *,
    idea_id: int,
    platform: str,
    brief: dict[str, Any],
    access_token: str | None = None,
    recursion_limit: int = 40,
) -> ContentPipelineState:
    """
    Lance uniquement le graphe LangGraph ReAct et retourne l'état mutable rempli par les tools.
    Préférez `run_content_generation` depuis l'API pour inclure la validation finale.
    """
    # Métadonnées visibles dans LangSmith (run racine + enfant graphe)
    rt = get_current_run_tree()
    if rt:
        rt.metadata.update({
            "idea_id": idea_id,
            "platform": platform,
            "brief_subject": ((brief.get("subject") or "")[:240]),
            "recursion_limit": recursion_limit,
            "verbose_terminal": CONTENT_AGENT_VERBOSE_TERMINAL,
        })

    state = ContentPipelineState()
    runner = ContentLLMRunner()

    tools = build_content_react_tools(
        idea_id=idea_id,
        platform=platform,
        brief=brief,
        access_token=access_token,
        state=state,
        runner=runner,
    )

    llm = create_react_orchestrator_llm(
        model=CONTENT_LLM_CONFIG["model"],
        temperature=float(CONTENT_LLM_CONFIG.get("temperature", 0.35)),
        max_tokens=int(CONTENT_LLM_CONFIG.get("max_tokens", 4096)),
    )

    agent = create_react_agent(
        llm,
        tools,
        prompt=REACT_ORCHESTRATOR_SYSTEM,
        name="content_react",
    )

    user_msg = (
        "Exécute la génération de contenu pour ce projet. "
        f"Plateforme cible : {platform}. "
        "Respecte l'ordre des outils décrit dans les instructions système."
    )

    initial = {"messages": [HumanMessage(content=user_msg)]}
    result = await invoke_react_with_optional_terminal_trace(
        agent,
        initial=initial,
        recursion_limit=recursion_limit,
        verbose=CONTENT_AGENT_VERBOSE_TERMINAL,
    )

    n_msg = len(result.get("messages") or [])
    logger.info(
        "[content_react_agent] terminé | messages=%d | verbose_terminal=%s",
        n_msg,
        CONTENT_AGENT_VERBOSE_TERMINAL,
    )
    return state


# Alias explicite pour imports externes
__all__ = [
    "build_content_react_tools",
    "run_content_generation",
    "run_content_react_agent",
    "REACT_ORCHESTRATOR_SYSTEM",
]
