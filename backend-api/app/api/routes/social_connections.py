from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.social_connection import (
    LinkedInConnectionUpsert,
    LinkedInProfileUrlPatch,
    MetaConnectionUpsert,
    MetaSelectedPagePatch,
    SocialConnectionsOut,
)
import app.services.social_connection_service as social_svc

router = APIRouter(
    prefix="/ideas/{idea_id}/social-connections",
    tags=["Connexions sociales"],
)

_DB_SCHEMA_HINT = (
    "Schéma PostgreSQL obsolète (migrations Alembic non appliquées). "
    "Dans le dossier backend-api : exécutez « alembic upgrade head » puis redémarrez l’API."
)


def _handle_db_schema(e: ProgrammingError) -> None:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=_DB_SCHEMA_HINT,
    ) from e


@router.get("", response_model=SocialConnectionsOut)
def get_social_connections(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SocialConnectionsOut:
    try:
        return social_svc.get_connections_for_idea(db, idea_id, current_user.id)
    except ProgrammingError as e:
        db.rollback()
        _handle_db_schema(e)


@router.put("/meta", response_model=SocialConnectionsOut)
def put_meta_connection(
    idea_id: int,
    body: MetaConnectionUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SocialConnectionsOut:
    pages = [
        {
            "id": p.id,
            "name": p.name,
            "access_token": p.access_token,
        }
        for p in body.pages
    ]
    sid = body.selected_page_id
    if sid:
        page_ids = {str(p["id"]) for p in pages}
        if str(sid) not in page_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="selected_page_id ne correspond à aucune page fournie.",
            )
    elif len(pages) == 1:
        sid = str(pages[0]["id"])

    try:
        social_svc.upsert_meta(
            db,
            idea_id=idea_id,
            user_id=current_user.id,
            user_access_token=body.user_access_token,
            pages=pages,
            selected_page_id=sid,
            token_expires_at=body.token_expires_at,
        )
        return social_svc.get_connections_for_idea(db, idea_id, current_user.id)
    except ProgrammingError as e:
        db.rollback()
        _handle_db_schema(e)


@router.patch("/meta", response_model=SocialConnectionsOut)
def patch_meta_selected_page(
    idea_id: int,
    body: MetaSelectedPagePatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SocialConnectionsOut:
    try:
        ok = social_svc.patch_meta_selected_page(
            db,
            idea_id=idea_id,
            user_id=current_user.id,
            selected_page_id=body.selected_page_id,
        )
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connexion Meta introuvable ou page invalide.",
            )
        return social_svc.get_connections_for_idea(db, idea_id, current_user.id)
    except HTTPException:
        raise
    except ProgrammingError as e:
        db.rollback()
        _handle_db_schema(e)


@router.put("/linkedin", response_model=SocialConnectionsOut)
def put_linkedin_connection(
    idea_id: int,
    body: LinkedInConnectionUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SocialConnectionsOut:
    try:
        social_svc.upsert_linkedin(
            db,
            idea_id=idea_id,
            user_id=current_user.id,
            access_token=body.access_token,
            person_urn=body.person_urn,
            name=body.name,
            token_expires_at=body.token_expires_at,
        )
        return social_svc.get_connections_for_idea(db, idea_id, current_user.id)
    except ProgrammingError as e:
        db.rollback()
        _handle_db_schema(e)


@router.patch("/linkedin/url", response_model=SocialConnectionsOut)
def patch_linkedin_profile_url(
    idea_id: int,
    body: LinkedInProfileUrlPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SocialConnectionsOut:
    """URL de profil LinkedIn optionnelle (colonne profile_url ; ex. pour l’agent Optimizer)."""
    try:
        ok = social_svc.patch_linkedin_profile_url(
            db,
            idea_id=idea_id,
            user_id=current_user.id,
            profile_url=body.profile_url,
        )
        if not ok:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connexion LinkedIn introuvable. Connectez LinkedIn d’abord.",
            )
        return social_svc.get_connections_for_idea(db, idea_id, current_user.id)
    except HTTPException:
        raise
    except ProgrammingError as e:
        db.rollback()
        _handle_db_schema(e)


@router.delete("/meta")
def delete_meta(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    try:
        social_svc.delete_meta(db, idea_id=idea_id, user_id=current_user.id)
    except ProgrammingError as e:
        db.rollback()
        _handle_db_schema(e)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/linkedin")
def delete_linkedin(
    idea_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    try:
        social_svc.delete_linkedin(db, idea_id=idea_id, user_id=current_user.id)
    except ProgrammingError as e:
        db.rollback()
        _handle_db_schema(e)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
