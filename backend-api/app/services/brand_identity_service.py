from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.branding_payload import (
    merge_brand_identity_for_api,
    split_brand_identity_payload,
)
from app.models.idea import Idea
from app.models.brand_identity import BrandIdentity
from app.schemas.brand_identity import BrandIdentityCreate, BrandIdentityOut


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


def _normalize_brand_identity_create(
    payload: BrandIdentityCreate,
) -> tuple[dict | None, dict | None, dict | None, dict | None]:
    """Colonne méta + names / slogans / logo ; accepte payload monolithique ou déjà découpé."""
    explicit = (
        payload.result_names is not None
        or payload.result_slogans is not None
        or payload.result_logo is not None
    )
    if explicit:
        meta = dict(payload.result_json) if payload.result_json else None
        return (
            meta,
            payload.result_names,
            payload.result_slogans,
            payload.result_logo,
        )
    if payload.result_json:
        return split_brand_identity_payload(payload.result_json)
    return None, None, None, None


def brand_identity_to_out(row: BrandIdentity) -> BrandIdentityOut:
    merged = merge_brand_identity_for_api(
        result_json=row.result_json if isinstance(row.result_json, dict) else None,
        result_names=row.result_names if isinstance(row.result_names, dict) else None,
        result_slogans=row.result_slogans if isinstance(row.result_slogans, dict) else None,
        result_logo=row.result_logo if isinstance(row.result_logo, dict) else None,
    )
    return BrandIdentityOut(
        id=row.id,
        idea_id=row.idea_id,
        status=row.status,
        result_json=merged if merged else None,
        result_names=row.result_names,
        result_slogans=row.result_slogans,
        result_logo=row.result_logo,
        error_message=row.error_message,
        started_at=row.started_at,
        completed_at=row.completed_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def create_brand_identity(
    db: Session,
    idea_id: int,
    user_id: int,
    payload: BrandIdentityCreate,
) -> BrandIdentityOut:
    _get_user_idea_or_404(db, idea_id, user_id)
    meta, names, slogans, logo = _normalize_brand_identity_create(payload)
    row = BrandIdentity(
        idea_id=idea_id,
        status=payload.status,
        result_json=meta,
        result_names=names,
        result_slogans=slogans,
        result_logo=logo,
        error_message=payload.error_message,
        started_at=payload.started_at,
        completed_at=payload.completed_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return brand_identity_to_out(row)


def get_latest_brand_identity_by_idea(
    db: Session,
    idea_id: int,
    user_id: int,
) -> BrandIdentityOut:
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
    return brand_identity_to_out(row)
