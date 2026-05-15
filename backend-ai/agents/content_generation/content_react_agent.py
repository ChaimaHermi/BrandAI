"""
================================================================================
Content Pipeline — génération séquentielle (BrandAI)
================================================================================
Pipeline fixe en 5 étapes (aucun agent LLM orchestrateur) :
  1. merge_context      — brief + contexte idée
  2. get_platform_spec  — contraintes techniques plateforme
  3. draft_post         — légende (LLM NVIDIA gpt-oss-120b)
  4. build_image_prompt — prompts image (LLM NVIDIA, si image demandée)
  5. image_client       — NVIDIA flux.2-klein-4b → Cloudinary

Points d'entrée publics (inchangés pour les routes FastAPI) :
  - run_content_generation   : retourne dict { caption, image_url, char_count, platform }
  - stream_content_generation : générateur SSE
================================================================================
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, AsyncGenerator

from langsmith import traceable

from agents.content_generation.content_llm_runner import ContentLLMRunner
from tools.content_generation.brief_helpers import should_include_image_in_post
from tools.content_generation.cloudinary_upload import (
    cloudinary_configured,
    is_brandai_cloudinary_url,
    upload_image_bytes,
)
from tools.content_generation.content_image_client import fetch_content_image
from tools.content_generation.context_steps import (
    ContentPipelineState,
    get_platform_spec_step,
    merge_context_step,
    merged_json_for_llm,
    spec_json_for_llm,
)

logger = logging.getLogger("brandai.content_pipeline")


# ---------------------------------------------------------------------------
# SSE helper
# ---------------------------------------------------------------------------
def sse_event(event: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    data_lines = "\n".join(f"data: {line}" for line in payload.splitlines())
    return f"event: {event}\n{data_lines}\n\n"


# ---------------------------------------------------------------------------
# Validation finale de l'état → payload API
# ---------------------------------------------------------------------------
def _build_generation_result(
    state: ContentPipelineState,
    *,
    platform: str,
    brief: dict[str, Any],
) -> dict[str, Any]:
    caption = (state.get("caption") or "").strip()
    if not caption:
        raise RuntimeError("Pipeline : légende vide — vérifiez les clés NVIDIA.")

    want_image = should_include_image_in_post(platform, brief)
    image_url = state.get("image_url")

    if want_image and not image_url:
        image_error = (state.get("image_error") or "").strip()
        if image_error:
            logger.warning("[content_pipeline] image indisponible, retour texte | %s", image_error[:180])
        elif not cloudinary_configured():
            raise RuntimeError("Cloudinary non configuré (CLOUDINARY_*).")
        else:
            logger.warning("[content_pipeline] image demandée mais absente, retour texte seul.")

    return {
        "caption": caption,
        "image_url": image_url if want_image else None,
        "char_count": len(caption),
        "platform": platform,
    }


# ---------------------------------------------------------------------------
# Pipeline séquentielle interne
# ---------------------------------------------------------------------------
async def _run_pipeline(
    *,
    idea_id: int,
    platform: str,
    brief: dict[str, Any],
    access_token: str | None,
    previous_caption: str | None,
    regeneration_instruction: str | None,
    state: ContentPipelineState,
    runner: ContentLLMRunner,
) -> None:
    t0 = time.monotonic()

    # 1 — merge_context
    logger.info("[content_pipeline] 1/5 merge_context")
    await merge_context_step(
        state,
        idea_id=idea_id,
        platform=platform,
        brief=brief,
        access_token=access_token,
    )

    # 2 — get_platform_spec
    logger.info("[content_pipeline] 2/5 get_platform_spec")
    get_platform_spec_step(state, platform)

    # 3 — draft_post
    logger.info("[content_pipeline] 3/5 draft_post")
    merged_j = merged_json_for_llm(state)
    spec_j = spec_json_for_llm(state)
    caption = await runner.draft_post(
        merged_j,
        spec_j,
        previous_caption=previous_caption,
        regeneration_instruction=regeneration_instruction,
    )
    state["caption"] = caption

    if not should_include_image_in_post(platform, brief):
        logger.info("[content_pipeline] image non requise — terminée en %.1fs", time.monotonic() - t0)
        return

    # 4 — build_image_prompt
    logger.info("[content_pipeline] 4/5 build_image_prompt")
    ip, np = await runner.build_image_prompt(merged_j, spec_j, caption)
    state["image_prompt"] = ip
    state["negative_prompt"] = np

    # 5 — image_client (NVIDIA flux.2-klein-4b → Cloudinary)
    logger.info("[content_pipeline] 5/5 image_client (NVIDIA flux.2-klein-4b)")
    try:
        data, mime, src = await fetch_content_image(ip, np)
        url = upload_image_bytes(data, mime=mime)
        if not is_brandai_cloudinary_url(url):
            logger.warning("[content_pipeline] URL Cloudinary inattendue : %s", url[:120])
        state["image_url"] = url
        state["image_source"] = src
        state["image_error"] = None
    except Exception as e:
        err = f"image_generation_failed: {str(e)[:220]}"
        logger.warning("[content_pipeline] échec image, post texte conservé : %s", err)
        state["image_error"] = err
        state["image_url"] = None

    logger.info("[content_pipeline] terminée en %.1fs", time.monotonic() - t0)


# ---------------------------------------------------------------------------
# Point d'entrée principal — route FastAPI
# ---------------------------------------------------------------------------
@traceable(name="content_generation.run", tags=["content_generation", "api", "brandai"])
async def run_content_generation(
    *,
    idea_id: int,
    platform: str,
    brief: dict[str, Any],
    access_token: str | None = None,
    previous_caption: str | None = None,
    regeneration_instruction: str | None = None,
    recursion_limit: int = 40,  # conservé pour compatibilité signature
) -> dict[str, Any]:
    state = ContentPipelineState()
    runner = ContentLLMRunner()
    await _run_pipeline(
        idea_id=idea_id,
        platform=platform,
        brief=brief,
        access_token=access_token,
        previous_caption=previous_caption,
        regeneration_instruction=regeneration_instruction,
        state=state,
        runner=runner,
    )
    return _build_generation_result(state, platform=platform, brief=brief)


# ---------------------------------------------------------------------------
# Streaming SSE — route POST /content/generate/stream
# ---------------------------------------------------------------------------
async def stream_content_generation(
    *,
    idea_id: int,
    platform: str,
    brief: dict[str, Any],
    access_token: str | None = None,
    previous_caption: str | None = None,
    regeneration_instruction: str | None = None,
    recursion_limit: int = 40,  # conservé pour compatibilité signature
) -> AsyncGenerator[str, None]:
    state = ContentPipelineState()
    runner = ContentLLMRunner()
    want_image = should_include_image_in_post(platform, brief)

    try:
        # 1 — merge_context
        yield sse_event("tool_start", {"tool": "merge_context"})
        await merge_context_step(state, idea_id=idea_id, platform=platform, brief=brief, access_token=access_token)
        yield sse_event("tool_end", {"tool": "merge_context"})

        # 2 — get_platform_spec
        yield sse_event("tool_start", {"tool": "get_platform_spec"})
        get_platform_spec_step(state, platform)
        yield sse_event("tool_end", {"tool": "get_platform_spec"})

        # 3 — draft_post
        yield sse_event("tool_start", {"tool": "draft_post"})
        merged_j = merged_json_for_llm(state)
        spec_j = spec_json_for_llm(state)
        caption = await runner.draft_post(
            merged_j, spec_j,
            previous_caption=previous_caption,
            regeneration_instruction=regeneration_instruction,
        )
        state["caption"] = caption
        yield sse_event("tool_end", {"tool": "draft_post"})

        if want_image:
            # 4 — build_image_prompt
            yield sse_event("tool_start", {"tool": "build_image_prompt"})
            ip, np = await runner.build_image_prompt(merged_j, spec_j, caption)
            state["image_prompt"] = ip
            state["negative_prompt"] = np
            yield sse_event("tool_end", {"tool": "build_image_prompt"})

            # 5 — image_client
            yield sse_event("tool_start", {"tool": "image_client"})
            try:
                data, mime, src = await fetch_content_image(ip, np)
                url = upload_image_bytes(data, mime=mime)
                state["image_url"] = url
                state["image_source"] = src
                state["image_error"] = None
            except Exception as e:
                err = f"image_generation_failed: {str(e)[:220]}"
                logger.warning("[content_pipeline] échec image : %s", err)
                state["image_error"] = err
                state["image_url"] = None
            yield sse_event("tool_end", {"tool": "image_client"})

        result = _build_generation_result(state, platform=platform, brief=brief)
        yield sse_event("done", {
            "success": True,
            "caption": result["caption"],
            "image_url": result.get("image_url"),
            "char_count": result["char_count"],
            "platform": result["platform"],
        })

    except Exception as exc:
        logger.exception("[content_pipeline] erreur pendant le stream")
        yield sse_event("error", {"success": False, "message": str(exc)})
        yield sse_event("done", {"success": False})


__all__ = [
    "run_content_generation",
    "stream_content_generation",
]
