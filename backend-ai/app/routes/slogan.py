"""
Génération de slogans : contexte projet + nom (body ou chosen_name en base) + préférences.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.branding_service import BrandingService

router = APIRouter(tags=["Slogan"])


class SloganPreferencesIn(BaseModel):
    positionnement: str = ""
    style_ton_slogan: list[str] = Field(default_factory=list)
    message_usp: list[str] = Field(default_factory=list)
    format: list[str] = Field(default_factory=list)
    style_linguistique: list[str] = Field(default_factory=list)
    longueur: str = ""
    langue: str = ""
    mots_eviter: str = ""
    user_remarks: str = ""


class SloganGenerateRequest(BaseModel):
    idea_id: int
    brand_name: Optional[str] = Field(
        None,
        description="Si omis, utilise chosen_name de l’étape naming (backend-api).",
    )
    preferences: SloganPreferencesIn = Field(default_factory=SloganPreferencesIn)
    access_token: str
    persist: bool = True


class SloganGenerateResponse(BaseModel):
    idea_id: int
    status: str
    slogan_options: list[dict[str, Any]] = Field(default_factory=list)
    branding_status: str | None = None
    slogan_error: str | None = None
    errors: list[str] = Field(default_factory=list)
    persisted: bool = False
    resolved_brand_name: str | None = None


def _prefs_dict(p: SloganPreferencesIn) -> dict[str, Any]:
    return {
        "positionnement": p.positionnement or "",
        "style_ton_slogan": list(p.style_ton_slogan or []),
        "message_usp": list(p.message_usp or []),
        "format": list(p.format or []),
        "style_linguistique": list(p.style_linguistique or []),
        "longueur": p.longueur or "",
        "langue": p.langue or "",
        "mots_eviter": (p.mots_eviter or "").strip(),
        "user_remarks": (p.user_remarks or "").strip(),
    }


@router.post("/slogan/generate", response_model=SloganGenerateResponse)
async def slogan_generate(body: SloganGenerateRequest) -> SloganGenerateResponse:
    data = await BrandingService.generate_slogan(
        idea_id=body.idea_id,
        brand_name=body.brand_name,
        slogan_preferences=_prefs_dict(body.preferences),
        access_token=body.access_token,
        persist=body.persist,
    )
    return SloganGenerateResponse(**data)
