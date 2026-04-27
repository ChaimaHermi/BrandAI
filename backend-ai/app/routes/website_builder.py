"""
Routes HTTP — Website Builder Agent.

Exposées sous /api/ai/website/...

Endpoints :
  GET  /api/ai/website/context?idea_id=...      → Phase 1 (CONTEXT)
  POST /api/ai/website/description              → Phase 1 + Phase 2
  POST /api/ai/website/generate                  → Phase 1 + 2 + 3
  POST /api/ai/website/revise                    → Phase 4 (HTML existant + instruction)
  POST /api/ai/website/deploy                    → Phase 5 (Vercel)

Tous les endpoints exigent un access_token (JWT backend-api FastAPI) pour
récupérer l'idée et le brand kit côté backend-api.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from agents.website_builder.website_builder_agent import WebsiteBuilderAgent
from config.website_builder_config import vercel_is_configured
from tools.website_builder.brand_context_fetch import BrandContext
from tools.website_builder.description_renderer import (
    render_context_summary,
    render_description_summary,
)
from tools.website_builder.website_project_persistence import (
    append_website_message,
    build_message,
    patch_website_project,
)
from tools.website_builder.website_renderer import html_stats

logger = logging.getLogger("brandai.website_builder.route")

router = APIRouter(prefix="/website", tags=["Website Builder"])


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _extract_token(authorization: str | None, fallback: str | None = None) -> str:
    """Récupère le JWT depuis l'header Authorization ou le body (legacy)."""
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


def _ctx_payload(ctx: BrandContext) -> dict[str, Any]:
    return {
        **ctx.as_dict(),
        "summary_md": render_context_summary(ctx),
    }


async def _persist_required(
    *,
    idea_id: int,
    token: str,
    patch: dict[str, Any] | None = None,
    message: dict[str, Any] | None = None,
) -> None:
    if patch:
        await patch_website_project(idea_id=idea_id, access_token=token, patch=patch)
    if message:
        await append_website_message(idea_id=idea_id, access_token=token, message=message)


# ─────────────────────────────────────────────────────────────────────────────
# Schémas Pydantic
# ─────────────────────────────────────────────────────────────────────────────
class DescriptionRequest(BaseModel):
    idea_id: int = Field(..., ge=1)
    access_token: str | None = Field(
        None,
        description="JWT (optionnel si fourni via header Authorization).",
    )


class GenerateRequest(BaseModel):
    idea_id: int = Field(..., ge=1)
    access_token: str | None = None
    description: dict[str, Any] | None = Field(
        None,
        description=(
            "Description Phase 2 déjà validée par l'utilisateur. "
            "Si None, l'agent la régénère à la volée."
        ),
    )


class ReviseRequest(BaseModel):
    idea_id: int = Field(..., ge=1)
    access_token: str | None = None
    current_html: str = Field(..., min_length=200)
    instruction: str = Field(..., min_length=1)


class DeployRequest(BaseModel):
    idea_id: int = Field(..., ge=1)
    access_token: str | None = None
    html: str = Field(..., min_length=200, description="HTML complet à déployer.")


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


class DeployResponse(BaseModel):
    idea_id: int
    deployment: dict[str, Any]
    summary_md: str


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────
@router.get(
    "/context",
    response_model=ContextResponse,
    summary="Phase 1 — récupère idée + brand kit",
)
async def website_context(
    idea_id: int = Query(..., ge=1),
    authorization: str | None = Header(default=None),
) -> ContextResponse:
    token = _extract_token(authorization)
    agent = WebsiteBuilderAgent()
    try:
        ctx = await agent.fetch_context(idea_id=idea_id, access_token=token)
    except Exception as exc:
        logger.exception("[website_builder] context failed")
        raise HTTPException(status_code=502, detail=f"Contexte indisponible : {exc!s}") from exc
    return ContextResponse(**_ctx_payload(ctx))


@router.post(
    "/description",
    response_model=DescriptionResponse,
    summary="Phases 1 + 2 — contexte + description créative",
)
async def website_description(
    body: DescriptionRequest,
    authorization: str | None = Header(default=None),
) -> DescriptionResponse:
    token = _extract_token(authorization, body.access_token)
    agent = WebsiteBuilderAgent()
    try:
        ctx = await agent.fetch_context(idea_id=body.idea_id, access_token=token)
        description = await agent.generate_description(ctx=ctx)
    except RuntimeError as exc:
        logger.exception("[website_builder] description failed (validation)")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("[website_builder] description failed")
        raise HTTPException(status_code=503, detail=f"Description indisponible : {exc!s}") from exc

    try:
        await _persist_required(
            idea_id=body.idea_id,
            token=token,
            patch={
                "status": "draft",
                "description_json": description,
            },
            message=build_message(
                role="assistant",
                msg_type="description_result",
                content="Description du site générée.",
                meta={
                    "sections": len(description.get("sections") or []),
                    "animations": len(description.get("animations") or []),
                },
            ),
        )
    except Exception as exc:
        logger.exception("[website_builder] persistence failed (description)")
        raise HTTPException(status_code=503, detail=f"Persistance website indisponible : {exc!s}") from exc

    return DescriptionResponse(
        context=_ctx_payload(ctx),
        description=description,
        description_summary_md=render_description_summary(description),
    )


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
    agent = WebsiteBuilderAgent()
    try:
        ctx = await agent.fetch_context(idea_id=body.idea_id, access_token=token)
        description = body.description or await agent.generate_description(ctx=ctx)
        html = await agent.generate_website(ctx=ctx, description=description)
    except RuntimeError as exc:
        msg = str(exc)
        if "timeout" in msg.lower():
            logger.exception("[website_builder] generate failed (timeout)")
            raise HTTPException(status_code=504, detail=msg) from exc
        logger.exception("[website_builder] generate failed (validation)")
        raise HTTPException(status_code=422, detail=msg) from exc
    except Exception as exc:
        logger.exception("[website_builder] generate failed")
        raise HTTPException(status_code=503, detail=f"Génération indisponible : {exc!s}") from exc

    stats = html_stats(html)
    try:
        await _persist_required(
            idea_id=body.idea_id,
            token=token,
            patch={
                "status": "generated",
                "description_json": description,
                "current_html": html,
                "current_version": 1,
            },
            message=build_message(
                role="assistant",
                msg_type="generation_result",
                content="Site HTML généré.",
                meta=stats,
            ),
        )
    except Exception as exc:
        logger.exception("[website_builder] persistence failed (generation)")
        raise HTTPException(status_code=503, detail=f"Persistance website indisponible : {exc!s}") from exc

    return GenerateResponse(
        context=_ctx_payload(ctx),
        description=description,
        description_summary_md=render_description_summary(description),
        html=html,
        html_stats=stats,
    )


@router.post(
    "/revise",
    response_model=ReviseResponse,
    summary="Phase 4 — applique une modification ciblée au HTML existant",
)
async def website_revise(
    body: ReviseRequest,
    authorization: str | None = Header(default=None),
) -> ReviseResponse:
    token = _extract_token(authorization, body.access_token)
    agent = WebsiteBuilderAgent()
    try:
        ctx = await agent.fetch_context(idea_id=body.idea_id, access_token=token)
        html = await agent.revise_website(
            ctx=ctx,
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
        raise HTTPException(status_code=503, detail=f"Révision indisponible : {exc!s}") from exc

    rev_stats = html_stats(html)
    try:
        await _persist_required(
            idea_id=body.idea_id,
            token=token,
            patch={
                "status": "generated",
                "current_html": html,
            },
            message=build_message(
                role="user",
                msg_type="revision_instruction",
                content=body.instruction.strip(),
            ),
        )
        await _persist_required(
            idea_id=body.idea_id,
            token=token,
            message=build_message(
                role="assistant",
                msg_type="revision_result",
                content="Modification appliquée sur le site.",
                meta=rev_stats,
            ),
        )
    except Exception as exc:
        logger.exception("[website_builder] persistence failed (revision)")
        raise HTTPException(status_code=503, detail=f"Persistance website indisponible : {exc!s}") from exc

    return ReviseResponse(
        idea_id=body.idea_id,
        instruction=body.instruction.strip(),
        html=html,
        html_stats=rev_stats,
    )


@router.post(
    "/deploy",
    response_model=DeployResponse,
    summary="Phase 5 — déploie le HTML sur Vercel et retourne l'URL finale",
)
async def website_deploy(
    body: DeployRequest,
    authorization: str | None = Header(default=None),
) -> DeployResponse:
    if not vercel_is_configured():
        raise HTTPException(
            status_code=503,
            detail="Vercel non configuré : ajoute VERCEL_API_KEY dans .env.",
        )

    token = _extract_token(authorization, body.access_token)
    agent = WebsiteBuilderAgent()
    try:
        ctx = await agent.fetch_context(idea_id=body.idea_id, access_token=token)
        deployment = await agent.deploy_website(ctx=ctx, html=body.html)
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
        raise HTTPException(status_code=503, detail=f"Déploiement indisponible : {exc!s}") from exc

    summary_md = (
        "🎉 **Ton site est en ligne !**\n\n"
        f"👉 [{deployment.full_url}]({deployment.full_url})\n\n"
        f"_Projet Vercel : `{deployment.project_name}` · "
        f"déploiement `{deployment.deployment_id}` · "
        f"{deployment.elapsed_seconds:.1f}s_"
    )

    try:
        await _persist_required(
            idea_id=body.idea_id,
            token=token,
            patch={
                "status": "deployed",
                "current_html": body.html,
                "last_deployment_id": deployment.deployment_id,
                "last_deployment_url": deployment.full_url,
                "last_deployment_state": deployment.state,
            },
            message=build_message(
                role="assistant",
                msg_type="deploy_result",
                content=f"Site déployé: {deployment.full_url}",
                meta=deployment.as_dict(),
            ),
        )
    except Exception as exc:
        logger.exception("[website_builder] persistence failed (deploy)")
        raise HTTPException(status_code=503, detail=f"Persistance website indisponible : {exc!s}") from exc

    return DeployResponse(
        idea_id=body.idea_id,
        deployment=deployment.as_dict(),
        summary_md=summary_md,
    )
