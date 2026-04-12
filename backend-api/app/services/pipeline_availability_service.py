"""Agrège la présence de résultats market / marketing / branding pour une idée."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.branding_results import NamingResult
from app.models.idea import Idea
from app.models.market_analysis import MarketAnalysisResult
from app.models.marketing_plan import MarketingPlan
from app.schemas.pipeline_availability import PipelineAvailabilityOut


def get_pipeline_availability(
    db: Session,
    idea_id: int,
    user_id: int,
) -> PipelineAvailabilityOut:
    idea = (
        db.query(Idea.id)
        .filter(Idea.id == idea_id, Idea.user_id == user_id)
        .first()
    )
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idée introuvable",
        )

    has_market = (
        db.query(MarketAnalysisResult.id)
        .filter(MarketAnalysisResult.idea_id == idea_id)
        .first()
        is not None
    )
    has_marketing = (
        db.query(MarketingPlan.id)
        .filter(MarketingPlan.idea_id == idea_id)
        .first()
        is not None
    )
    has_branding = (
        db.query(NamingResult.id)
        .filter(NamingResult.idea_id == idea_id)
        .first()
        is not None
    )

    return PipelineAvailabilityOut(
        has_market_analysis=has_market,
        has_marketing_plan=has_marketing,
        has_branding_naming=has_branding,
    )
