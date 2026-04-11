"""
Génération de palettes : idée clarifiée + nom de marque (body ou base). Pas de préférences utilisateur.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.branding_service import BrandingService

router = APIRouter(tags=["Palette"])


class PaletteGenerateRequest(BaseModel):
    idea_id: int
    brand_name: Optional[str] = Field(
        None,
        description="Si omis, utilise chosen_name naming (backend-api).",
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


@router.post("/palette/generate", response_model=PaletteGenerateResponse)
async def palette_generate(body: PaletteGenerateRequest) -> PaletteGenerateResponse:
    data = await BrandingService.generate_palette(
        idea_id=body.idea_id,
        brand_name=body.brand_name,
        access_token=body.access_token,
        persist=body.persist,
    )
    return PaletteGenerateResponse(**data)
