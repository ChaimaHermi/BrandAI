"""
Génération logo : LLM (prompt image) puis image via Hugging Face Inference (Replicate, ex. Qwen Image).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.branding_service import BrandingService

logger = logging.getLogger("brandai.logo_route")
router = APIRouter(tags=["Logo"])


class LogoGenerateRequest(BaseModel):
    idea_id: int
    brand_name: Optional[str] = Field(
        None,
        description="Si omis, utilise chosen_name de l’étape naming (backend-api).",
    )
    slogan_hint: Optional[str] = Field(
        None,
        description="Si omis, utilise chosen_slogan (slogan) en base.",
    )
    palette_color_hint: Optional[str] = Field(
        None,
        description="Texte libre couleurs ; si omis, tente d’extraire les hex depuis l’étape palette.",
    )
    previous_image_prompt: Optional[str] = Field(
        None,
        description="image_prompt du logo précédent — indique au LLM ce qu’il doit éviter absolument.",
    )
    user_remarks: Optional[str] = Field(
        None,
        description="Remarques libres de l’utilisateur pour orienter la régénération.",
    )
    access_token: str
    persist: bool = True
    persist_image_base64: bool = Field(
        False,
        description="Si True, inclut image_base64 dans la persistance (fichiers lourds).",
    )


class LogoGenerateResponse(BaseModel):
    idea_id: int
    status: str
    logo_concepts: list[dict[str, Any]] = Field(default_factory=list)
    branding_status: str | None = None
    logo_error: str | None = None
    logo_image_error: str | None = None
    errors: list[str] = Field(default_factory=list)
    persisted: bool = False
    resolved_brand_name: str | None = None
    resolved_slogan_hint: str = ""
    resolved_palette_hint: str = ""


@router.post("/logo/generate", response_model=LogoGenerateResponse)
async def logo_generate(body: LogoGenerateRequest) -> LogoGenerateResponse:
    logger.info(
        "[logo/generate] idea_id=%s brand_name=%r",
        body.idea_id,
        (body.brand_name or "")[:80],
    )
    data = await BrandingService.generate_logo(
        idea_id=body.idea_id,
        brand_name=body.brand_name,
        slogan_hint=body.slogan_hint,
        palette_color_hint=body.palette_color_hint,
        previous_image_prompt=body.previous_image_prompt,
        user_remarks=body.user_remarks,
        access_token=body.access_token,
        persist=body.persist,
        persist_image_base64=body.persist_image_base64,
    )
    return LogoGenerateResponse(**data)
