from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.brand_identity import BrandIdentityCreate, BrandIdentityOut
from app.services.brand_identity_service import (
    create_brand_identity,
    get_latest_brand_identity_by_idea,
)

router = APIRouter(prefix="/brand-identity", tags=["Brand Identity"])


@router.post(
    "/{idea_id}",
    response_model=BrandIdentityOut,
    status_code=201,
    summary="Enregistrer un résultat Brand Identity",
)
def create_brand_identity_result(
    idea_id: int,
    payload: BrandIdentityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_brand_identity(db, idea_id, current_user.id, payload)


@router.get(
    "/{idea_id}/latest",
    response_model=BrandIdentityOut,
    status_code=200,
    summary="Dernier résultat Brand Identity pour une idée",
)
def get_latest_brand_identity_result(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_latest_brand_identity_by_idea(db, idea_id, current_user.id)
