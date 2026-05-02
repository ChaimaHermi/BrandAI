"""
Routes HTTP — Website Builder Agent.

Base : /api/ai/website/

Surface exposee (alignee sur l’app React) :
  GET  /context                              → Phase 1 (idee + brand kit)
  POST /description/stream                   → Phase 2 (concept, SSE)
  POST /description/refine/stream            → Phase 2.5 (affinage chat, SSE)
  POST /description/approve                → approbation concept (JSON)
  POST /generate/stream                      → Phase 3 (HTML, SSE)
  POST /revise/stream                        → Phase 4 (modif site par chat, SSE)
  POST /save                                 → sauvegarde edition manuelle sans LLM
  POST /deploy, /deploy/delete               → Vercel

Tous les endpoints exigent un JWT (header Authorization ou body access_token).
Les formulaires de contact des sites utilisent mailto: (pas de relay HTTP dedie).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from agents.website_builder.orchestrator import WebsiteBuilderOrchestrator
from config.website_builder_config import vercel_is_configured
from tools.website_builder.step_streamer import StepEmitter, sse_response_stream

logger = logging.getLogger("brandai.website_builder.route")

router = APIRouter(prefix="/website", tags=["Website Builder"])
orchestrator = WebsiteBuilderOrchestrator()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _extract_token(authorization: str | None, fallback: str | None = None) -> str:
    """Recupere le JWT depuis l'header Authorization ou le body (legacy)."""
    if authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1]:
            return parts[1]
    if fallback:
        return fallback.strip()
    raise HTTPException(
        status_code=401,
        detail="Token requis (header Authorization: Bearer <jwt>).",
    )


# Conserve une reference forte aux taches d'orchestration en cours pour eviter
# que le GC ne les ramasse pendant que le client consomme le flux SSE.
_BACKGROUND_TASKS: set[asyncio.Task[Any]] = set()


def _spawn_streamer(coro: Any) -> asyncio.Task[Any]:
    task = asyncio.create_task(coro)
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)
    return task


def _sse_response(emitter: StepEmitter) -> StreamingResponse:
    """Construit la StreamingResponse SSE standard du Website Builder."""
    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # nginx hint : pas de buffering
    }
    return StreamingResponse(
        sse_response_stream(emitter),
        media_type="text/event-stream",
        headers=headers,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Schemas Pydantic
# ─────────────────────────────────────────────────────────────────────────────
class DescriptionRequest(BaseModel):
    idea_id: int = Field(..., ge=1)
    access_token: str | None = Field(
        None,
        description="JWT (optionnel si fourni via header Authorization).",
    )


class DescriptionRefineRequest(BaseModel):
    idea_id: int = Field(..., ge=1)
    access_token: str | None = None
    description: dict[str, Any] = Field(
        ...,
        description="Description Phase 2 actuellement affichee a l'utilisateur.",
    )
    instruction: str = Field(
        ...,
        min_length=1,
        description="Retours utilisateur a appliquer sur la description.",
    )


class DescriptionApproveRequest(BaseModel):
    idea_id: int = Field(..., ge=1)
    access_token: str | None = None


class GenerateRequest(BaseModel):
    idea_id: int = Field(..., ge=1)
    access_token: str | None = None
    description: dict[str, Any] | None = Field(
        None,
        description=(
            "Description Phase 2 deja validee par l'utilisateur. "
            "Si None, l'agent la regenere a la volee."
        ),
    )


class ReviseRequest(BaseModel):
    idea_id: int = Field(..., ge=1)
    access_token: str | None = None
    current_html: str = Field(..., min_length=1)
    instruction: str = Field(..., min_length=1)


class SaveHtmlRequest(BaseModel):
    idea_id: int = Field(..., ge=1)
    access_token: str | None = None
    html: str = Field(..., min_length=1)


class DeployRequest(BaseModel):
    idea_id: int = Field(..., ge=1)
    access_token: str | None = None
    html: str = Field(..., min_length=200, description="HTML complet a deployer.")


class DeployDeleteRequest(BaseModel):
    idea_id: int = Field(..., ge=1)
    access_token: str | None = None
    deployment_id: str = Field(..., min_length=1)


class ContextResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    idea_id: int
    summary_md: str


class SaveHtmlResponse(BaseModel):
    idea_id: int
    html: str
    html_stats: dict[str, int]


class ApproveResponse(BaseModel):
    idea_id: int
    approved: bool


class DeployResponse(BaseModel):
    idea_id: int
    deployment: dict[str, Any]
    summary_md: str


class DeployDeleteResponse(BaseModel):
    idea_id: int
    deployment_id: str
    deleted: bool


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints JSON (hors flux SSE)
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/context",
    response_model=ContextResponse,
    summary="Phase 1 — recupere idee + brand kit",
)
async def website_context(
    idea_id: int = Query(..., ge=1),
    authorization: str | None = Header(default=None),
) -> ContextResponse:
    token = _extract_token(authorization)
    try:
        payload = await orchestrator.fetch_context(idea_id=idea_id, token=token)
    except Exception as exc:
        logger.exception("[website_builder] context failed")
        raise HTTPException(status_code=502, detail=f"Contexte indisponible : {exc!s}") from exc
    return ContextResponse(**payload)


@router.post(
    "/description/approve",
    response_model=ApproveResponse,
    summary="Marque le concept Phase 2 comme approuve par l'utilisateur",
)
async def website_description_approve(
    body: DescriptionApproveRequest,
    authorization: str | None = Header(default=None),
) -> ApproveResponse:
    token = _extract_token(authorization, body.access_token)
    try:
        payload = await orchestrator.approve_description(idea_id=body.idea_id, token=token)
    except Exception as exc:
        logger.exception("[website_builder] description/approve failed")
        raise HTTPException(status_code=503, detail=f"Approbation impossible : {exc!s}") from exc
    return ApproveResponse(**payload)


@router.post(
    "/save",
    response_model=SaveHtmlResponse,
    summary="Sauvegarde le HTML modifie manuellement (mode 'Modifier le site') sans LLM",
)
async def website_save(
    body: SaveHtmlRequest,
    authorization: str | None = Header(default=None),
) -> SaveHtmlResponse:
    token = _extract_token(authorization, body.access_token)
    try:
        payload = await orchestrator.save_html_directly(
            idea_id=body.idea_id,
            token=token,
            html=body.html,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("[website_builder] save failed")
        raise HTTPException(status_code=503, detail=f"Sauvegarde impossible : {exc!s}") from exc
    return SaveHtmlResponse(**payload)


@router.post(
    "/deploy",
    response_model=DeployResponse,
    summary="Phase 5 — deploie le HTML sur Vercel et retourne l'URL finale",
)
async def website_deploy(
    body: DeployRequest,
    authorization: str | None = Header(default=None),
) -> DeployResponse:
    if not vercel_is_configured():
        raise HTTPException(
            status_code=503,
            detail="Vercel non configure : ajoute VERCEL_API_KEY dans .env.",
        )

    token = _extract_token(authorization, body.access_token)
    try:
        payload = await orchestrator.deploy_website(
            idea_id=body.idea_id,
            token=token,
            html=body.html,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except TimeoutError as exc:
        logger.exception("[website_builder] deploy timeout")
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("[website_builder] deploy failed (vercel)")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("[website_builder] deploy failed")
        raise HTTPException(status_code=503, detail=f"Deploiement indisponible : {exc!s}") from exc

    return DeployResponse(**payload)


@router.post(
    "/deploy/delete",
    response_model=DeployDeleteResponse,
    summary="Supprime un deploiement Vercel existant et nettoie l'etat deploiement",
)
async def website_deploy_delete(
    body: DeployDeleteRequest,
    authorization: str | None = Header(default=None),
) -> DeployDeleteResponse:
    if not vercel_is_configured():
        raise HTTPException(
            status_code=503,
            detail="Vercel non configure : ajoute VERCEL_API_KEY dans .env.",
        )

    token = _extract_token(authorization, body.access_token)
    try:
        payload = await orchestrator.delete_deployment(
            idea_id=body.idea_id,
            token=token,
            deployment_id=body.deployment_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("[website_builder] deploy delete failed (vercel)")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("[website_builder] deploy delete failed")
        raise HTTPException(status_code=503, detail=f"Suppression deploiement indisponible : {exc!s}") from exc

    return DeployDeleteResponse(**payload)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints SSE — flux temps-reel "XAI"
# ─────────────────────────────────────────────────────────────────────────────
@router.post(
    "/description/stream",
    summary="Phase 2 (SSE) — emet en temps reel les etapes de generation du concept",
)
async def website_description_stream(
    body: DescriptionRequest,
    authorization: str | None = Header(default=None),
) -> StreamingResponse:
    token = _extract_token(authorization, body.access_token)
    emitter = StepEmitter()
    _spawn_streamer(
        orchestrator.stream_description(
            idea_id=body.idea_id,
            token=token,
            emitter=emitter,
        )
    )
    return _sse_response(emitter)


@router.post(
    "/description/refine/stream",
    summary="Phase 2.5 (SSE) — emet en temps reel les etapes d'affinage du concept",
)
async def website_description_refine_stream(
    body: DescriptionRefineRequest,
    authorization: str | None = Header(default=None),
) -> StreamingResponse:
    token = _extract_token(authorization, body.access_token)
    emitter = StepEmitter()
    _spawn_streamer(
        orchestrator.stream_refine_description(
            idea_id=body.idea_id,
            token=token,
            current_description=body.description,
            user_feedback=body.instruction,
            emitter=emitter,
        )
    )
    return _sse_response(emitter)


@router.post(
    "/generate/stream",
    summary="Phase 3 (SSE) — emet en temps reel les etapes de generation du site",
)
async def website_generate_stream(
    body: GenerateRequest,
    authorization: str | None = Header(default=None),
) -> StreamingResponse:
    token = _extract_token(authorization, body.access_token)
    emitter = StepEmitter()
    _spawn_streamer(
        orchestrator.stream_generate_website(
            idea_id=body.idea_id,
            token=token,
            description=body.description,
            emitter=emitter,
        )
    )
    return _sse_response(emitter)


@router.post(
    "/revise/stream",
    summary="Phase 4 (SSE) — emet en temps reel les etapes de revision du site",
)
async def website_revise_stream(
    body: ReviseRequest,
    authorization: str | None = Header(default=None),
) -> StreamingResponse:
    token = _extract_token(authorization, body.access_token)
    emitter = StepEmitter()
    _spawn_streamer(
        orchestrator.stream_revise_website(
            idea_id=body.idea_id,
            token=token,
            current_html=body.current_html,
            instruction=body.instruction,
            emitter=emitter,
        )
    )
    return _sse_response(emitter)
