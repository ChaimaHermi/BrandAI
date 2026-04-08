"""
Génération de palettes : idée + nom (body ou base) + indice slogan (body ou base).
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.branding_service import BrandingService

router = APIRouter(tags=["Palette"])


class PalettePreferencesIn(BaseModel):
    ambiance: str = ""
    style_couleur: list[str] = Field(default_factory=list)
    contraste: str = ""
    couleurs_eviter: str = ""
    user_remarks: str = ""


class PaletteGenerateRequest(BaseModel):
    idea_id: int
    brand_name: Optional[str] = Field(
        None,
        description="Si omis, utilise chosen_name naming (backend-api).",
    )
    preferences: PalettePreferencesIn = Field(default_factory=PalettePreferencesIn)
    slogan_hint: Optional[str] = Field(
        None,
        description="Si omis, utilise chosen_slogan (backend-api) si présent.",
    )
    access_token: str
    persist: bool = True


class PaletteGenerateResponse(BaseModel):
    idea_id: int
    status: str
    palette_options: list[dict[str, Any]] = Field(default_factory=list)
    color_palette: dict[str, Any] = Field(default_factory=dict)
    branding_status: str | None = None
    palette_error: str | None = None
    errors: list[str] = Field(default_factory=list)
    persisted: bool = False
    resolved_brand_name: str | None = None
    resolved_slogan_hint: str | None = None


def _prefs_dict(p: PalettePreferencesIn) -> dict[str, Any]:
    return {
        "ambiance": p.ambiance or "",
        "style_couleur": list(p.style_couleur or []),
        "contraste": p.contraste or "",
        "couleurs_eviter": (p.couleurs_eviter or "").strip(),
        "user_remarks": (p.user_remarks or "").strip(),
    }


@router.post("/palette/generate", response_model=PaletteGenerateResponse)
async def palette_generate(body: PaletteGenerateRequest) -> PaletteGenerateResponse:
    data = await BrandingService.generate_palette(
        idea_id=body.idea_id,
        brand_name=body.brand_name,
        palette_preferences=_prefs_dict(body.preferences),
        slogan_hint=body.slogan_hint,
        access_token=body.access_token,
        persist=body.persist,
    )
    return PaletteGenerateResponse(**data)
