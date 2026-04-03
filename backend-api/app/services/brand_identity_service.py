from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.idea import Idea
from app.models.brand_identity import BrandIdentity
from app.schemas.brand_identity import BrandIdentityCreate


def _get_user_idea_or_404(db: Session, idea_id: int, user_id: int) -> Idea:
    idea = (
        db.query(Idea)
        .filter(Idea.id == idea_id, Idea.user_id == user_id)
        .first()
    )
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idée introuvable",
        )
    return idea


def create_brand_identity(
    db: Session,
    idea_id: int,
    user_id: int,
    payload: BrandIdentityCreate,
) -> BrandIdentity:
    _get_user_idea_or_404(db, idea_id, user_id)
    row = BrandIdentity(
        idea_id=idea_id,
        status=payload.status,
        result_json=payload.result_json,
        error_message=payload.error_message,
        started_at=payload.started_at,
        completed_at=payload.completed_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_latest_brand_identity_by_idea(
    db: Session,
    idea_id: int,
    user_id: int,
) -> BrandIdentity:
    _get_user_idea_or_404(db, idea_id, user_id)
    row = (
        db.query(BrandIdentity)
        .filter(BrandIdentity.idea_id == idea_id)
        .order_by(BrandIdentity.created_at.desc(), BrandIdentity.id.desc())
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun résultat Brand Identity pour cette idée",
        )
    return row
