from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.social_connection import (
    LinkedInConnectionUpsert,
    MetaConnectionUpsert,
    MetaSelectedPagePatch,
    SocialConnectionsOut,
)
import app.services.social_connection_service as social_svc

router = APIRouter(prefix="/me/social-connections", tags=["Connexions sociales"])


@router.get("", response_model=SocialConnectionsOut)
def get_social_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SocialConnectionsOut:
    return social_svc.get_connections_for_user(db, current_user.id)


@router.put("/meta", response_model=SocialConnectionsOut)
def put_meta_connection(
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

    social_svc.upsert_meta(
        db,
        user_id=current_user.id,
        user_access_token=body.user_access_token,
        pages=pages,
        selected_page_id=sid,
    )
    return social_svc.get_connections_for_user(db, current_user.id)


@router.patch("/meta", response_model=SocialConnectionsOut)
def patch_meta_selected_page(
    body: MetaSelectedPagePatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SocialConnectionsOut:
    ok = social_svc.patch_meta_selected_page(
        db,
        user_id=current_user.id,
        selected_page_id=body.selected_page_id,
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connexion Meta introuvable ou page invalide.",
        )
    return social_svc.get_connections_for_user(db, current_user.id)


@router.put("/linkedin", response_model=SocialConnectionsOut)
def put_linkedin_connection(
    body: LinkedInConnectionUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SocialConnectionsOut:
    social_svc.upsert_linkedin(
        db,
        user_id=current_user.id,
        access_token=body.access_token,
        person_urn=body.person_urn,
        name=body.name,
    )
    return social_svc.get_connections_for_user(db, current_user.id)


@router.delete("/meta")
def delete_meta(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    social_svc.delete_meta(db, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/linkedin")
def delete_linkedin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    social_svc.delete_linkedin(db, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
