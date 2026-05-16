from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.social_optimizer.recommendation_agent import SocialOptimizerRecommendationAgent
from tools.social_optimizer.recommendation_tools import BACKEND_API_BASE_URL

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


async def _assert_idea_owned(idea_id: int, access_token: str) -> None:
    """Vérifie que l'utilisateur possède bien l'idée avant toute opération."""
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(
            f"{BACKEND_API_BASE_URL}/ideas/{idea_id}",
            headers=headers,
        )
    if r.status_code == 403:
        raise HTTPException(status_code=403, detail="Accès refusé : vous ne possédez pas cette idée.")
    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="Idée introuvable.")
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail="Erreur lors de la vérification de l'idée.")


@router.post("/optimizer/recommendation", response_model=OptimizerRecommendationResponse)
async def optimizer_recommendation(body: OptimizerRecommendationRequest):
    await _assert_idea_owned(body.idea_id, body.access_token)
    agent = SocialOptimizerRecommendationAgent()
    try:
        out = await agent.generate_recommendation(
            idea_id=body.idea_id,
            platform=body.platform,
            access_token=body.access_token,
            force=bool(body.force),
        )
    except HTTPException:
        raise
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

