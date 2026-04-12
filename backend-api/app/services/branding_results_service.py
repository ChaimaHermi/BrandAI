"""CRUD résultats branding (naming, slogan, palette, logo, kit) par idée."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.branding_results import (
    BrandKit,
    LogoResult,
    NamingResult,
    PaletteResult,
    SloganResult,
)
from app.models.idea import Idea
from app.schemas.branding_results import (
    BrandingBundleOut,
    BrandKitPatch,
    LogoResultPatch,
    NamingResultPatch,
    PaletteResultPatch,
    SloganResultPatch,
)


def _require_idea_for_user(db: Session, idea_id: int, user_id: int) -> Idea:
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


def _assert_result_belongs_to_idea(
    db: Session,
    idea_id: int,
    result_id: UUID | None,
    model_cls: type,
) -> None:
    if result_id is None:
        return
    row = (
        db.query(model_cls)
        .filter(model_cls.id == result_id, model_cls.idea_id == idea_id)
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le résultat référencé n'appartient pas à cette idée.",
        )


# --- Naming ---


def get_naming_result(db: Session, idea_id: int, user_id: int) -> NamingResult | None:
    """Ligne naming ou None si l’idée existe mais aucun enregistrement (→ route renvoie 204)."""
    _require_idea_for_user(db, idea_id, user_id)
    return db.query(NamingResult).filter(NamingResult.idea_id == idea_id).first()


def patch_naming_result(
    db: Session,
    idea_id: int,
    user_id: int,
    payload: NamingResultPatch,
) -> NamingResult:
    _require_idea_for_user(db, idea_id, user_id)
    row = db.query(NamingResult).filter(NamingResult.idea_id == idea_id).first()
    if row is None:
        row = NamingResult(idea_id=idea_id)
        db.add(row)
        db.flush()

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


# --- Slogan ---


def get_slogan_result(db: Session, idea_id: int, user_id: int) -> SloganResult | None:
    _require_idea_for_user(db, idea_id, user_id)
    return db.query(SloganResult).filter(SloganResult.idea_id == idea_id).first()


def patch_slogan_result(
    db: Session,
    idea_id: int,
    user_id: int,
    payload: SloganResultPatch,
) -> SloganResult:
    _require_idea_for_user(db, idea_id, user_id)
    row = db.query(SloganResult).filter(SloganResult.idea_id == idea_id).first()
    if row is None:
        row = SloganResult(idea_id=idea_id)
        db.add(row)
        db.flush()
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


# --- Palette ---


def get_palette_result(db: Session, idea_id: int, user_id: int) -> PaletteResult | None:
    _require_idea_for_user(db, idea_id, user_id)
    return db.query(PaletteResult).filter(PaletteResult.idea_id == idea_id).first()


def patch_palette_result(
    db: Session,
    idea_id: int,
    user_id: int,
    payload: PaletteResultPatch,
) -> PaletteResult:
    _require_idea_for_user(db, idea_id, user_id)
    row = db.query(PaletteResult).filter(PaletteResult.idea_id == idea_id).first()
    if row is None:
        row = PaletteResult(idea_id=idea_id)
        db.add(row)
        db.flush()
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


# --- Logo ---


def get_logo_result(db: Session, idea_id: int, user_id: int) -> LogoResult | None:
    _require_idea_for_user(db, idea_id, user_id)
    return db.query(LogoResult).filter(LogoResult.idea_id == idea_id).first()


def patch_logo_result(
    db: Session,
    idea_id: int,
    user_id: int,
    payload: LogoResultPatch,
) -> LogoResult:
    _require_idea_for_user(db, idea_id, user_id)
    row = db.query(LogoResult).filter(LogoResult.idea_id == idea_id).first()
    if row is None:
        row = LogoResult(idea_id=idea_id)
        db.add(row)
        db.flush()
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


# --- Brand kit ---


def get_brand_kit(db: Session, idea_id: int, user_id: int) -> BrandKit | None:
    """Retourne la ligne brand kit ou None si l’idée existe mais aucun kit encore créé."""
    _require_idea_for_user(db, idea_id, user_id)
    return db.query(BrandKit).filter(BrandKit.idea_id == idea_id).first()


def get_branding_bundle(db: Session, idea_id: int, user_id: int) -> BrandingBundleOut:
    """Tous les résultats branding en une requête (200, champs nulls si absents)."""
    _require_idea_for_user(db, idea_id, user_id)
    naming = db.query(NamingResult).filter(NamingResult.idea_id == idea_id).first()
    slogan = db.query(SloganResult).filter(SloganResult.idea_id == idea_id).first()
    palette = db.query(PaletteResult).filter(PaletteResult.idea_id == idea_id).first()
    logo = db.query(LogoResult).filter(LogoResult.idea_id == idea_id).first()
    brand_kit = db.query(BrandKit).filter(BrandKit.idea_id == idea_id).first()
    return BrandingBundleOut(
        naming=naming,
        slogan=slogan,
        palette=palette,
        logo=logo,
        brand_kit=brand_kit,
    )


def patch_brand_kit(
    db: Session,
    idea_id: int,
    user_id: int,
    payload: BrandKitPatch,
) -> BrandKit:
    _require_idea_for_user(db, idea_id, user_id)

    data = payload.model_dump(exclude_unset=True)
    if "naming_id" in data:
        _assert_result_belongs_to_idea(db, idea_id, data["naming_id"], NamingResult)
    if "slogan_id" in data:
        _assert_result_belongs_to_idea(db, idea_id, data["slogan_id"], SloganResult)
    if "palette_id" in data:
        _assert_result_belongs_to_idea(db, idea_id, data["palette_id"], PaletteResult)
    if "logo_id" in data:
        _assert_result_belongs_to_idea(db, idea_id, data["logo_id"], LogoResult)

    row = db.query(BrandKit).filter(BrandKit.idea_id == idea_id).first()
    if row is None:
        row = BrandKit(idea_id=idea_id)
        db.add(row)
        db.flush()

    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row
