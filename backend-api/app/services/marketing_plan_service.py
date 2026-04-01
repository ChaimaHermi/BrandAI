from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.idea import Idea
from app.models.marketing_plan import MarketingPlan
from app.schemas.marketing_plan import MarketingPlanCreate


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


def create_marketing_plan(
    db: Session,
    idea_id: int,
    user_id: int,
    payload: MarketingPlanCreate,
) -> MarketingPlan:
    idea = _get_user_idea_or_404(db, idea_id, user_id)

    row = MarketingPlan(
        idea_id=idea_id,
        result_json=payload.result_json,
        status=payload.status,
    )
    db.add(row)

    if payload.status == "done":
        idea.status = "done"
    elif payload.status == "error":
        idea.status = "error"
    elif payload.status in {"pending", "running"}:
        idea.status = "running"

    db.commit()
    db.refresh(row)
    return row


def get_latest_marketing_plan_by_idea(
    db: Session,
    idea_id: int,
    user_id: int,
) -> MarketingPlan:
    _get_user_idea_or_404(db, idea_id, user_id)
    row = (
        db.query(MarketingPlan)
        .filter(MarketingPlan.idea_id == idea_id)
        .order_by(MarketingPlan.created_at.desc(), MarketingPlan.id.desc())
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun plan marketing pour cette idée",
        )
    return row


def list_marketing_plans_by_idea(
    db: Session,
    idea_id: int,
    user_id: int,
) -> list[MarketingPlan]:
    _get_user_idea_or_404(db, idea_id, user_id)
    return (
        db.query(MarketingPlan)
        .filter(MarketingPlan.idea_id == idea_id)
        .order_by(MarketingPlan.created_at.desc(), MarketingPlan.id.desc())
        .all()
    )
