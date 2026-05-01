"""
Routes HTTP — Website Builder Agent.

Exposees sous /api/ai/website/...

Endpoints classiques (JSON) :
  GET  /api/ai/website/context?idea_id=...      → Phase 1 (CONTEXT)
  POST /api/ai/website/description              → Phase 1 + Phase 2
  POST /api/ai/website/description/refine       → Phase 2.5 (affinage du concept)
  POST /api/ai/website/description/approve      → marque le concept comme approuve
  POST /api/ai/website/generate                 → Phase 1 + 2 + 3
  POST /api/ai/website/revise                   → Phase 4 (HTML existant + instruction)
  POST /api/ai/website/save                     → sauvegarde HTML edite manuellement
  POST /api/ai/website/deploy                   → Phase 5 (Vercel)

Endpoints SSE (Server-Sent Events) — temps reel "XAI" :
  POST /api/ai/website/description/stream
  POST /api/ai/website/description/refine/stream
  POST /api/ai/website/generate/stream
  POST /api/ai/website/revise/stream

Tous les endpoints ACTIFS exigent un access_token (JWT backend-api FastAPI)
pour recuperer l'idee et le brand kit cote backend-api.

Exception legacy (depreciee) :
  POST /api/ai/website/contact-form
  Cet endpoint ne requiert pas de token et renvoie 410 Gone, car le flux
  officiel est desormais le formulaire `mailto:` direct (sans relay backend).
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


class DescriptionResponse(BaseModel):
    context: dict[str, Any]
    description: dict[str, Any]
    description_summary_md: str


class GenerateResponse(BaseModel):
    context: dict[str, Any]
    description: dict[str, Any]
    description_summary_md: str
    html: str
    html_stats: dict[str, int]


class ReviseResponse(BaseModel):
    idea_id: int
    instruction: str
    html: str
    html_stats: dict[str, int]


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
# Endpoints classiques (JSON)
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
    "/description",
    response_model=DescriptionResponse,
    summary="Phases 1 + 2 — contexte + description creative",
)
async def website_description(
    body: DescriptionRequest,
    authorization: str | None = Header(default=None),
) -> DescriptionResponse:
    token = _extract_token(authorization, body.access_token)
    try:
        payload = await orchestrator.generate_description(idea_id=body.idea_id, token=token)
    except RuntimeError as exc:
        logger.exception("[website_builder] description failed (validation)")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("[website_builder] description failed")
        raise HTTPException(status_code=503, detail=f"Description indisponible : {exc!s}") from exc

    return DescriptionResponse(**payload)


@router.post(
    "/description/refine",
    response_model=DescriptionResponse,
    summary="Phase 2.5 — affine la description selon les retours utilisateur",
)
async def website_description_refine(
    body: DescriptionRefineRequest,
    authorization: str | None = Header(default=None),
) -> DescriptionResponse:
    token = _extract_token(authorization, body.access_token)
    try:
        payload = await orchestrator.refine_description(
            idea_id=body.idea_id,
            token=token,
            current_description=body.description,
            user_feedback=body.instruction,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("[website_builder] description/refine failed (validation)")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("[website_builder] description/refine failed")
        raise HTTPException(
            status_code=503,
            detail=f"Affinage de la description impossible : {exc!s}",
        ) from exc
    return DescriptionResponse(**payload)


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
    "/generate",
    response_model=GenerateResponse,
    summary="Phases 1 + 2 + 3 — contexte, description et site HTML/Tailwind/JS complet",
)
async def website_generate(
    body: GenerateRequest,
    authorization: str | None = Header(default=None),
) -> GenerateResponse:
    token = _extract_token(authorization, body.access_token)
    try:
        payload = await orchestrator.generate_website(
            idea_id=body.idea_id,
            token=token,
            description=body.description,
        )
    except RuntimeError as exc:
        msg = str(exc)
        if "timeout" in msg.lower():
            logger.exception("[website_builder] generate failed (timeout)")
            raise HTTPException(status_code=504, detail=msg) from exc
        logger.exception("[website_builder] generate failed (validation)")
        raise HTTPException(status_code=422, detail=msg) from exc
    except Exception as exc:
        logger.exception("[website_builder] generate failed")
        raise HTTPException(status_code=503, detail=f"Generation indisponible : {exc!s}") from exc

    return GenerateResponse(**payload)


@router.post(
    "/revise",
    response_model=ReviseResponse,
    summary="Phase 4 — applique une modification ciblee au HTML existant",
)
async def website_revise(
    body: ReviseRequest,
    authorization: str | None = Header(default=None),
) -> ReviseResponse:
    token = _extract_token(authorization, body.access_token)
    try:
        payload = await orchestrator.revise_website(
            idea_id=body.idea_id,
            token=token,
            current_html=body.current_html,
            instruction=body.instruction,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.exception("[website_builder] revise failed (validation)")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("[website_builder] revise failed")
        raise HTTPException(status_code=503, detail=f"Revision indisponible : {exc!s}") from exc

    return ReviseResponse(**payload)


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


@router.post(
    "/contact-form",
    summary="DÉSACTIVÉ — les sites générés utilisent désormais mailto: directement",
    deprecated=True,
)
async def website_contact_form() -> None:
    """
    DÉSACTIVÉ — par décision produit, les messages des formulaires de contact
    des sites vitrines générés ne transitent PLUS par Brand AI. Le formulaire
    ouvre maintenant directement le client mail du visiteur via `mailto:` et
    le mail part de son adresse vers celle du propriétaire du site.

    Brand AI ne voit donc jamais le contenu de ces messages. Cet endpoint est
    conservé temporairement (compat anciens sites déjà déployés) mais renvoie
    410 Gone : aucun message n'est plus relayé.
    """
    logger.info("[website_builder] contact-form call ignored (endpoint deprecated, mailto-only)")
    raise HTTPException(
        status_code=410,
        detail=(
            "Le relais de messages via Brand AI est désactivé. "
            "Le formulaire doit utiliser un lien mailto: pointant directement "
            "vers le propriétaire du site."
        ),
    )


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
