"""
Génération de noms (Naming) avec préférences utilisateur — délégué à BrandingService.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.branding_service import BrandingService

router = APIRouter(tags=["Naming"])


class StyleTonIn(BaseModel):
    brand_values: list[str] = Field(default_factory=list)
    personality: list[str] = Field(default_factory=list)
    user_feelings: list[str] = Field(default_factory=list)


class ConstraintsIn(BaseModel):
    name_language: str = "fr"
    name_length: str = "medium"
    include_keywords: str = ""
    exclude_keywords: str = ""


class NamingGenerateRequest(BaseModel):
    idea_id: int
    style_ton: StyleTonIn = Field(default_factory=StyleTonIn)
    constraints: ConstraintsIn = Field(default_factory=ConstraintsIn)
    user_remarks: str = Field(
        default="",
        description="Remarques libres (régénération) pour affiner le brief.",
    )
    access_token: str = Field(..., description="JWT utilisateur pour GET /ideas/{id} et persistance")
    persist: bool = True


class NamingGenerateResponse(BaseModel):
    idea_id: int
    status: str
    name_options: list[dict[str, Any]] = Field(default_factory=list)
    branding_status: str | None = None
    name_error: str | None = None
    agent_errors: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    persisted: bool = False


def _prefs_from_body(body: NamingGenerateRequest) -> dict[str, Any]:
    return {
        "brand_values": list(body.style_ton.brand_values or []),
        "personality": list(body.style_ton.personality or []),
        "user_feelings": list(body.style_ton.user_feelings or []),
        "name_language": body.constraints.name_language or "",
        "name_length": body.constraints.name_length or "",
        "include_keywords": body.constraints.include_keywords or "",
        "exclude_keywords": body.constraints.exclude_keywords or "",
        "user_remarks": (body.user_remarks or "").strip(),
    }


@router.post("/naming/generate", response_model=NamingGenerateResponse)
async def naming_generate(body: NamingGenerateRequest) -> NamingGenerateResponse:
    data = await BrandingService.generate_naming(
        idea_id=body.idea_id,
        naming_preferences=_prefs_from_body(body),
        access_token=body.access_token,
        persist=body.persist,
    )
    return NamingGenerateResponse(**data)
