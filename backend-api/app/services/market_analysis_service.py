from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.idea import Idea
from app.models.market_analysis import MarketAnalysisResult
from app.schemas.market_analysis import MarketAnalysisCreate


def _get_user_idea_or_404(db: Session, idea_id: int, user_id: int) -> Idea:
    idea = (
        db.query(Idea)
        .filter(Idea.id == idea_id, Idea.user_id == user_id)
        .first()
    )
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idée introuvable",
        )
    return idea


def create_market_analysis(
    db: Session,
    idea_id: int,
    user_id: int,
    payload: MarketAnalysisCreate,
) -> MarketAnalysisResult:
    _get_user_idea_or_404(db, idea_id, user_id)
    row = MarketAnalysisResult(
        idea_id=idea_id,
        status=payload.status,
        result_json=payload.result_json,
        data_quality_json=payload.data_quality_json,
        error_message=payload.error_message,
        started_at=payload.started_at,
        completed_at=payload.completed_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_latest_market_analysis_by_idea(
    db: Session,
    idea_id: int,
    user_id: int,
) -> MarketAnalysisResult:
    _get_user_idea_or_404(db, idea_id, user_id)
    row = (
        db.query(MarketAnalysisResult)
        .filter(MarketAnalysisResult.idea_id == idea_id)
        .order_by(MarketAnalysisResult.created_at.desc(), MarketAnalysisResult.id.desc())
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun résultat d'analyse de marché pour cette idée",
        )
    return row


def list_market_analysis_by_idea(
    db: Session,
    idea_id: int,
    user_id: int,
) -> list[MarketAnalysisResult]:
    _get_user_idea_or_404(db, idea_id, user_id)
    return (
        db.query(MarketAnalysisResult)
        .filter(MarketAnalysisResult.idea_id == idea_id)
        .order_by(MarketAnalysisResult.created_at.desc(), MarketAnalysisResult.id.desc())
        .all()
    )
