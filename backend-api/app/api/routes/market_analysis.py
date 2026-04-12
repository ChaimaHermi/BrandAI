from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.market_analysis import (
    MarketAnalysisCreate,
    MarketAnalysisListOut,
    MarketAnalysisOut,
)
from app.services.market_analysis_service import (
    create_market_analysis,
    get_latest_market_analysis_by_idea,
    list_market_analysis_by_idea,
)


router = APIRouter(prefix="/market-analysis", tags=["Market Analysis"])


@router.post(
    "/{idea_id}",
    response_model=MarketAnalysisOut,
    status_code=201,
    summary="Créer un résultat d'analyse de marché",
)
def create_market_analysis_result(
    idea_id: int,
    payload: MarketAnalysisCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_market_analysis(db, idea_id, current_user.id, payload)


@router.get(
    "/{idea_id}/latest",
    response_model=MarketAnalysisOut,
    status_code=200,
    responses={204: {"description": "Idée OK mais aucune analyse enregistrée"}},
    summary="Récupérer le dernier résultat d'analyse de marché",
)
def get_latest_market_analysis_result(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = get_latest_market_analysis_by_idea(db, idea_id, current_user.id)
    if row is None:
        return Response(status_code=204)
    return row


@router.get(
    "/{idea_id}/history",
    response_model=MarketAnalysisListOut,
    status_code=200,
    summary="Lister l'historique des analyses de marché",
)
def list_market_analysis_results(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = list_market_analysis_by_idea(db, idea_id, current_user.id)
    return MarketAnalysisListOut(items=rows, total=len(rows))
