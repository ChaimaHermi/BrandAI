from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.optimizer import (
    OptimizerConnectionsSummaryOut,
    PlatformStatsOut,
    SocialEtlSyncOut,
)
import app.services.social_connection_service as social_svc
from app.services.optimizer_stats_service import get_optimizer_stats_for_idea
from app.services.social_etl_runner import (
    build_social_etl_config,
    run_social_etl_for_idea,
    stream_social_etl_events,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ideas/{idea_id}/optimizer", tags=["Optimizer"])


def _connections_summary(db, idea_id: int, user_id: int) -> OptimizerConnectionsSummaryOut:
    out = social_svc.get_connections_for_idea(db, idea_id, user_id)
    blockers: list[str] = []
    has_fb = bool(out.meta and out.meta.pages)
    has_ig = bool(out.meta and out.meta.instagram_business)
    has_li = bool(out.linkedin)

    li_url = None
    if out.linkedin:
        li_url = out.linkedin.profile_url

    fb_label = None
    if out.meta and out.meta.pages:
        sid = out.meta.selected_page_id
        for p in out.meta.pages:
            if sid and str(p.id) == str(sid):
                fb_label = p.name or f"Page {p.id}"
                break
        if not fb_label:
            fb_label = out.meta.pages[0].name or f"Page {out.meta.pages[0].id}"

    ig_label = None
    if out.meta and out.meta.instagram_business:
        ig = out.meta.instagram_business
        ig_label = ig.account_name or ig.page_name or "Instagram"

    apify_ok = bool((settings.APIFY_TOKEN or "").strip())
    can = has_fb or has_ig or (has_li and bool(li_url) and apify_ok)
    if not (has_fb or has_ig or has_li):
        blockers.append("Aucun compte social connecté pour cette idée.")
    if has_li and not li_url:
        blockers.append("LinkedIn : renseignez l’URL du profil (PATCH social-connections).")
    elif has_li and li_url and not apify_ok:
        blockers.append(
            "LinkedIn : configurez APIFY_TOKEN (et optionnellement APIFY_LINKEDIN_ACTOR_ID) sur l’API pour analyser les posts."
        )

    return OptimizerConnectionsSummaryOut(
        has_meta_facebook=has_fb,
        has_instagram=has_ig,
        has_linkedin=has_li,
        linkedin_profile_url=li_url,
        facebook_page_label=fb_label,
        instagram_label=ig_label,
        can_run_social_etl=can,
        blockers=blockers,
    )


@router.get("/connections", response_model=OptimizerConnectionsSummaryOut)
def optimizer_connections_summary(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OptimizerConnectionsSummaryOut:
    return _connections_summary(db, idea_id, current_user.id)


@router.get("/stats", response_model=PlatformStatsOut)
def optimizer_stats(
    idea_id: int,
    platform: str = Query("global", description="global | facebook | instagram | linkedin"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlatformStatsOut:
    social_svc._assert_idea_owned(db, idea_id, current_user.id)
    raw = get_optimizer_stats_for_idea(idea_id, platform)
    return PlatformStatsOut.model_validate(raw)


@router.post("/sync-social-etl", response_model=SocialEtlSyncOut)
def optimizer_sync_social_etl(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SocialEtlSyncOut:
    social_svc._assert_idea_owned(db, idea_id, current_user.id)
    try:
        summary, warnings = run_social_etl_for_idea(db, idea_id=idea_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e
    except Exception as e:
        logger.exception("social_etl failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Échec du pipeline social ETL : {e!s}",
        ) from e

    return SocialEtlSyncOut(
        output_dir=summary["output_dir"],
        runs=summary.get("runs") or [],
        warnings=warnings,
    )


@router.post("/sync-social-etl/stream")
async def optimizer_sync_social_etl_stream(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """SSE : progression du pipeline (événements JSON par ligne ``data:``)."""
    social_svc._assert_idea_owned(db, idea_id, current_user.id)
    cfg, warnings, err = build_social_etl_config(db, idea_id=idea_id, user_id=current_user.id)
    if err or not cfg:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err or "Configuration vide.")

    async def sse_iter():
        try:
            async for ev in stream_social_etl_events(cfg, warnings):
                line = f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
                yield line.encode("utf-8")
        except Exception as e:
            logger.exception("social_etl stream failed")
            err_ev = {"type": "fatal", "detail": f"Échec du pipeline : {e!s}"}
            yield f"data: {json.dumps(err_ev, ensure_ascii=False)}\n\n".encode("utf-8")

    return StreamingResponse(
        sse_iter(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
