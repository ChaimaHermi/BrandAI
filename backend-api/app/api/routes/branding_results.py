"""Endpoints résultats branding par idée (nouvelles tables)."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.branding_results import (
    BrandingBundleOut,
    BrandKitOut,
    BrandKitPatch,
    LogoResultOut,
    LogoResultPatch,
    NamingResultOut,
    NamingResultPatch,
    PaletteResultOut,
    PaletteResultPatch,
    SloganResultOut,
    SloganResultPatch,
)
from app.services.branding_results_service import (
    get_brand_kit,
    get_branding_bundle,
    get_logo_result,
    get_naming_result,
    get_palette_result,
    get_slogan_result,
    patch_brand_kit,
    patch_logo_result,
    patch_naming_result,
    patch_palette_result,
    patch_slogan_result,
)

router = APIRouter(
    prefix="/branding/ideas",
    tags=["Branding results"],
)


@router.get(
    "/{idea_id}/bundle",
    response_model=BrandingBundleOut,
    status_code=200,
    summary="Tous les résultats branding (naming, slogan, palette, logo, brand-kit)",
)
def read_branding_bundle(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_branding_bundle(db, idea_id, current_user.id)


@router.get(
    "/{idea_id}/naming",
    response_model=NamingResultOut,
    responses={204: {"description": "Idée OK mais aucun résultat naming"}},
    summary="Résultat naming pour une idée",
)
def read_naming(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_naming_result(db, idea_id, current_user.id)
    if row is None:
        return Response(status_code=204)
    return row


@router.patch(
    "/{idea_id}/naming",
    response_model=NamingResultOut,
    summary="Créer ou mettre à jour le résultat naming",
)
def update_naming(
    idea_id: int,
    payload: NamingResultPatch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return patch_naming_result(db, idea_id, current_user.id, payload)


@router.get(
    "/{idea_id}/slogan",
    response_model=SloganResultOut,
    responses={204: {"description": "Idée OK mais aucun résultat slogan"}},
    summary="Résultat slogan pour une idée",
)
def read_slogan(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_slogan_result(db, idea_id, current_user.id)
    if row is None:
        return Response(status_code=204)
    return row


@router.patch(
    "/{idea_id}/slogan",
    response_model=SloganResultOut,
    summary="Créer ou mettre à jour le résultat slogan",
)
def update_slogan(
    idea_id: int,
    payload: SloganResultPatch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return patch_slogan_result(db, idea_id, current_user.id, payload)


@router.get(
    "/{idea_id}/palette",
    response_model=PaletteResultOut,
    responses={204: {"description": "Idée OK mais aucun résultat palette"}},
    summary="Résultat palette pour une idée",
)
def read_palette(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_palette_result(db, idea_id, current_user.id)
    if row is None:
        return Response(status_code=204)
    return row


@router.patch(
    "/{idea_id}/palette",
    response_model=PaletteResultOut,
    summary="Créer ou mettre à jour le résultat palette",
)
def update_palette(
    idea_id: int,
    payload: PaletteResultPatch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return patch_palette_result(db, idea_id, current_user.id, payload)


@router.get(
    "/{idea_id}/logo",
    response_model=LogoResultOut,
    responses={204: {"description": "Idée OK mais aucun résultat logo"}},
    summary="Résultat logo pour une idée",
)
def read_logo(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_logo_result(db, idea_id, current_user.id)
    if row is None:
        return Response(status_code=204)
    return row


@router.patch(
    "/{idea_id}/logo",
    response_model=LogoResultOut,
    summary="Créer ou mettre à jour le résultat logo",
)
def update_logo(
    idea_id: int,
    payload: LogoResultPatch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return patch_logo_result(db, idea_id, current_user.id, payload)


@router.get(
    "/{idea_id}/brand-kit",
    response_model=BrandKitOut,
    summary="Brand kit assemblé pour une idée",
    responses={204: {"description": "Idée OK mais aucun brand kit enregistré encore"}},
)
def read_brand_kit(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_brand_kit(db, idea_id, current_user.id)
    if row is None:
        return Response(status_code=204)
    return row


@router.patch(
    "/{idea_id}/brand-kit",
    response_model=BrandKitOut,
    summary="Créer ou mettre à jour le brand kit (FKs vers les résultats)",
)
def update_brand_kit(
    idea_id: int,
    payload: BrandKitPatch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return patch_brand_kit(db, idea_id, current_user.id, payload)
