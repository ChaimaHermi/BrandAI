from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.social_optimizer.recommendation_agent import SocialOptimizerRecommendationAgent

router = APIRouter(tags=["Social Optimizer"])


class OptimizerRecommendationRequest(BaseModel):
    idea_id: int = Field(..., ge=1)
    platform: str = "global"
    access_token: str = Field(..., min_length=10)
    force: bool = False


class OptimizerRecommendationResponse(BaseModel):
    class RecommendationItem(BaseModel):
        id: int
        title: str
        description: str
        actions: list[str]
        priority: str

    platform: str
    summary: str
    recommendations: list[RecommendationItem]
    generated_at: str


@router.post("/optimizer/recommendation", response_model=OptimizerRecommendationResponse)
async def optimizer_recommendation(body: OptimizerRecommendationRequest):
    agent = SocialOptimizerRecommendationAgent()
    try:
        out = await agent.generate_recommendation(
            idea_id=body.idea_id,
            platform=body.platform,
            access_token=body.access_token,
            force=bool(body.force),
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Optimizer indisponible: {e!s}") from e
    return OptimizerRecommendationResponse(
        platform=str(out["platform"]),
        generated_at=str(out["generated_at"]),
        summary=str(out.get("summary") or ""),
        recommendations=list(out.get("recommendations") or []),
    )


@router.post("/optimizer/recommendation/regenerate", response_model=OptimizerRecommendationResponse)
async def optimizer_recommendation_regenerate(body: OptimizerRecommendationRequest):
    body.force = True
    return await optimizer_recommendation(body)

