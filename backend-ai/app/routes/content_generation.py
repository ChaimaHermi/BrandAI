"""
================================================================================
Route HTTP — Génération de contenu social
================================================================================

POST /api/ai/content/generate

Une seule voie d'exécution : l'agent ReAct (`run_content_generation` dans
`content_react_agent.py`) — merge, specs plateforme, légende LLM, prompts image,
génération d'image et upload Cloudinary via des outils @tool.
================================================================================
"""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator, model_validator

from agents.content_generation.content_react_agent import (
    run_content_generation,
    stream_content_generation,
)

logger = logging.getLogger("brandai.content_generation_route")

router = APIRouter(tags=["Content Generation"])


class BriefIn(BaseModel):
    subject: str = Field(..., min_length=1)
    tone: str = Field(..., min_length=1)
    content_type: str = Field(..., min_length=1)
    hashtags: bool | None = None
    include_image: bool | None = None
    call_to_action: str | None = None
    align_with_project: bool = Field(
        True,
        description="False = post éducatif/libre sans ancrage sur l’idée projet ; true = utilise le contexte idée.",
    )

    @field_validator("subject", mode="before")
    @classmethod
    def strip_subject(cls, v: object) -> str:
        if v is None:
            return ""
        return str(v).strip()


class ContentGenerateRequest(BaseModel):
    idea_id: int = Field(..., ge=1)
    platform: Literal["instagram", "facebook", "linkedin"]
    brief: BriefIn
    access_token: str | None = Field(
        None,
        description="JWT utilisateur (backend-api FastAPI) pour enrichir le merge avec GET /ideas/{id}",
    )

    @model_validator(mode="after")
    def validate_brief_vs_platform(self) -> ContentGenerateRequest:
        b = self.brief
        subject = (b.subject or "").strip()
        if len(subject) < 1:
            raise ValueError("brief.subject must not be empty")

        if self.platform == "instagram":
            if b.hashtags is None or b.include_image is None:
                raise ValueError(
                    "instagram requires brief.hashtags and brief.include_image (booleans)"
                )
            if b.call_to_action is not None:
                raise ValueError("instagram expects brief.call_to_action to be null")
        elif self.platform == "facebook":
            if b.hashtags is not None:
                raise ValueError("facebook expects brief.hashtags to be null")
            if b.include_image is None:
                raise ValueError("facebook requires brief.include_image")
            if not (b.call_to_action or "").strip():
                raise ValueError("facebook requires brief.call_to_action")
        else:
            if b.hashtags is not False:
                raise ValueError("linkedin expects brief.hashtags to be false")
            if b.include_image is None:
                raise ValueError("linkedin requires brief.include_image")
            if not (b.call_to_action or "").strip():
                raise ValueError("linkedin requires brief.call_to_action")

        return self


class ContentGenerateResponse(BaseModel):
    caption: str
    image_url: str | None
    char_count: int
    platform: str


@router.post("/content/generate/stream")
async def content_generate_stream(body: ContentGenerateRequest) -> StreamingResponse:
    """Délègue à stream_content_generation — retourne un flux SSE text/event-stream."""

    async def _gen():
        async for chunk in stream_content_generation(
            idea_id=body.idea_id,
            platform=body.platform,
            brief=body.brief.model_dump(),
            access_token=body.access_token,
        ):
            yield chunk

    return StreamingResponse(
        _gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/content/generate", response_model=ContentGenerateResponse)
async def content_generate(body: ContentGenerateRequest) -> ContentGenerateResponse:
    """Délègue entièrement à l'agent ReAct + validation du state final."""
    try:
        out = await run_content_generation(
            idea_id=body.idea_id,
            platform=body.platform,
            brief=body.brief.model_dump(),
            access_token=body.access_token,
        )
    except Exception as e:
        logger.exception("content_generate failure")
        raise HTTPException(
            status_code=503,
            detail=f"Génération indisponible : {e!s}",
        ) from e

    return ContentGenerateResponse(
        caption=out["caption"],
        image_url=out.get("image_url"),
        char_count=int(out["char_count"]),
        platform=str(out["platform"]),
    )
