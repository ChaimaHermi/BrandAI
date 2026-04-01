from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.marketing_plan import (
    MarketingPlanCreate,
    MarketingPlanListOut,
    MarketingPlanOut,
)
from app.services.marketing_plan_service import (
    create_marketing_plan,
    get_latest_marketing_plan_by_idea,
    list_marketing_plans_by_idea,
)


router = APIRouter(prefix="/marketing-plans", tags=["Marketing Plans"])


@router.post(
    "/{idea_id}",
    response_model=MarketingPlanOut,
    status_code=201,
    summary="Créer un résultat de stratégie marketing",
)
def create_marketing_plan_result(
    idea_id: int,
    payload: MarketingPlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_marketing_plan(db, idea_id, current_user.id, payload)


@router.get(
    "/{idea_id}/latest",
    response_model=MarketingPlanOut,
    status_code=200,
    summary="Récupérer le dernier plan marketing",
)
def get_latest_marketing_plan_result(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_latest_marketing_plan_by_idea(db, idea_id, current_user.id)


@router.get(
    "/{idea_id}/history",
    response_model=MarketingPlanListOut,
    status_code=200,
    summary="Lister l'historique des plans marketing",
)
def list_marketing_plan_results(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = list_marketing_plans_by_idea(db, idea_id, current_user.id)
    return MarketingPlanListOut(items=rows, total=len(rows))
