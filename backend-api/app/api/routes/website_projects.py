from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.website_project import (
    WebsiteApproveOut,
    WebsiteMessageIn,
    WebsiteProjectOut,
    WebsiteProjectPatch,
)
from app.services.website_project_service import (
    append_website_message,
    approve_website_project,
    get_website_project,
    patch_website_project,
)

router = APIRouter(prefix="/website/ideas", tags=["Website projects"])


@router.get(
    "/{idea_id}",
    response_model=WebsiteProjectOut,
    status_code=200,
    summary="Lire (ou initialiser) le projet website d'une idée",
)
def read_website_project(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_website_project(db, idea_id, current_user.id)


@router.patch(
    "/{idea_id}",
    response_model=WebsiteProjectOut,
    status_code=200,
    summary="Mettre à jour le projet website (patch partiel)",
)
def update_website_project(
    idea_id: int,
    payload: WebsiteProjectPatch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return patch_website_project(db, idea_id, current_user.id, payload)


@router.post(
    "/{idea_id}/messages",
    response_model=WebsiteProjectOut,
    status_code=200,
    summary="Ajouter un message à la conversation website",
)
def add_website_message(
    idea_id: int,
    payload: WebsiteMessageIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return append_website_message(db, idea_id, current_user.id, payload)


@router.post(
    "/{idea_id}/approve",
    response_model=WebsiteApproveOut,
    status_code=200,
    summary="Approuver la version finale du website",
)
def approve_website(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = approve_website_project(db, idea_id, current_user.id)
    return WebsiteApproveOut(
        success=True,
        idea_id=idea_id,
        approved=row.approved,
        approved_at=row.approved_at,
    )

