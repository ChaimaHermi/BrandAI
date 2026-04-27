from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.content_generation.weekly_plan_agent import (
    WeeklyGenerateInput,
    approve_weekly_plan,
    generate_weekly_content_for_items,
    generate_weekly_plan,
    regenerate_weekly_item,
)

router = APIRouter(tags=["Content Weekly Plan"])


class WeeklyPlanGenerateIn(BaseModel):
    idea_id: int = Field(..., ge=1)
    user_prompt: str = Field(..., min_length=3)
    platforms: list[Literal["linkedin", "facebook", "instagram"]] = Field(
        default_factory=lambda: ["linkedin", "facebook", "instagram"]
    )
    timezone: str = Field(default="UTC", min_length=1)
    align_with_project: bool = True
    include_images: bool = True
    distribution_mode: Literal["auto", "balanced"] = "auto"
    requested_post_count: int | None = Field(default=None, ge=1, le=7)
    access_token: str | None = None


class WeeklyPlanRegenerateIn(BaseModel):
    item: dict
    feedback: str = Field(..., min_length=3)


class WeeklyPlanApproveIn(BaseModel):
    idea_id: int = Field(..., ge=1)
    access_token: str = Field(..., min_length=10)
    timezone: str = Field(default="UTC", min_length=1)
    align_with_project: bool = True
    items: list[dict] = Field(default_factory=list, min_length=1)


class WeeklyPlanGenerateContentIn(BaseModel):
    idea_id: int = Field(..., ge=1)
    access_token: str | None = None
    align_with_project: bool = True
    include_images: bool = True
    items: list[dict] = Field(default_factory=list, min_length=1)


@router.post("/content/weekly-plan/generate")
async def weekly_plan_generate(body: WeeklyPlanGenerateIn):
    try:
        out = await generate_weekly_plan(
            WeeklyGenerateInput(
                idea_id=body.idea_id,
                user_prompt=body.user_prompt,
                platforms=body.platforms or ["linkedin", "facebook", "instagram"],
                timezone=body.timezone,
                align_with_project=body.align_with_project,
                include_images=body.include_images,
                requested_post_count=body.requested_post_count,
                access_token=body.access_token,
                distribution_mode=body.distribution_mode,
            )
        )
        return out
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Weekly plan indisponible: {exc}") from exc


@router.post("/content/weekly-plan/regenerate-item")
async def weekly_plan_regenerate_item(body: WeeklyPlanRegenerateIn):
    try:
        item = await regenerate_weekly_item(item=body.item, feedback=body.feedback)
        return {"item": item}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Régénération indisponible: {exc}") from exc


@router.post("/content/weekly-plan/approve")
async def weekly_plan_approve(body: WeeklyPlanApproveIn):
    try:
        out = await approve_weekly_plan(
            idea_id=body.idea_id,
            access_token=body.access_token,
            timezone_name=body.timezone,
            align_with_project=body.align_with_project,
            items=body.items,
        )
        return out
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Approbation indisponible: {exc}") from exc


@router.post("/content/weekly-plan/generate-content")
async def weekly_plan_generate_content(body: WeeklyPlanGenerateContentIn):
    try:
        out = await generate_weekly_content_for_items(
            idea_id=body.idea_id,
            access_token=body.access_token,
            align_with_project=body.align_with_project,
            include_images=body.include_images,
            items=body.items,
        )
        return out
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Génération contenu indisponible: {exc}") from exc
