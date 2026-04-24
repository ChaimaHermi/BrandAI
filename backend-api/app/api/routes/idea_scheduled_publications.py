# Routes : publications planifiées (calendrier) par idée.

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.scheduled_publication import (
    ScheduledPublicationCreate,
    ScheduledPublicationListOut,
    ScheduledPublicationOut,
    ScheduledPublicationPatch,
)
import app.services.scheduled_publication_service as sp_svc

router = APIRouter(prefix="/ideas", tags=["Publications planifiées"])


@router.post(
    "/{idea_id}/scheduled-publications",
    response_model=ScheduledPublicationOut,
    status_code=201,
    summary="Planifier une publication à partir d'un contenu généré",
)
def create_scheduled_publication(
    idea_id: int,
    body: ScheduledPublicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        row = sp_svc.create_scheduled_publication(
            db,
            idea_id=idea_id,
            user_id=current_user.id,
            data=body,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not row:
        raise HTTPException(
            status_code=404,
            detail="Idée ou contenu généré introuvable.",
        )
    return row


@router.get(
    "/{idea_id}/scheduled-publications/{schedule_id}",
    response_model=ScheduledPublicationOut,
    summary="Détail d'une publication planifiée",
)
def get_scheduled_publication(
    idea_id: int,
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = sp_svc.get_scheduled_publication(
        db,
        idea_id=idea_id,
        schedule_id=schedule_id,
        user_id=current_user.id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Planification introuvable")
    return row


@router.get(
    "/{idea_id}/scheduled-publications",
    response_model=ScheduledPublicationListOut,
    summary="Lister les publications planifiées pour une idée",
)
def list_scheduled_publications(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    date_from: datetime | None = Query(None, description="Filtrer scheduled_at >= (UTC)"),
    date_to: datetime | None = Query(None, description="Filtrer scheduled_at <= (UTC)"),
):
    rows = sp_svc.list_scheduled_publications(
        db,
        idea_id=idea_id,
        user_id=current_user.id,
        date_from=date_from,
        date_to=date_to,
    )
    if rows is None:
        raise HTTPException(status_code=404, detail="Idée introuvable")
    out = [ScheduledPublicationOut.model_validate(r) for r in rows]
    return ScheduledPublicationListOut(items=out, total=len(out))


@router.patch(
    "/{idea_id}/scheduled-publications/{schedule_id}",
    response_model=ScheduledPublicationOut,
    summary="Reporter ou annuler une publication planifiée",
)
def patch_scheduled_publication(
    idea_id: int,
    schedule_id: int,
    body: ScheduledPublicationPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        row = sp_svc.patch_scheduled_publication(
            db,
            idea_id=idea_id,
            schedule_id=schedule_id,
            user_id=current_user.id,
            patch=body,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not row:
        raise HTTPException(status_code=404, detail="Planification introuvable")
    return row


@router.delete(
    "/{idea_id}/scheduled-publications/{schedule_id}",
    status_code=204,
    summary="Supprimer une planification (statut scheduled uniquement)",
)
def delete_scheduled_publication(
    idea_id: int,
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        ok = sp_svc.delete_scheduled_publication(
            db,
            idea_id=idea_id,
            schedule_id=schedule_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not ok:
        raise HTTPException(status_code=404, detail="Planification introuvable")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
