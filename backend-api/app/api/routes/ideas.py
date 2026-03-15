# app/api/routes/ideas.py
# ─────────────────────────────────────────
# Endpoints HTTP pour les idées.
# Toutes les routes sont protégées → token JWT requis.
#
# POST   /api/ideas/       → soumettre une idée
# GET    /api/ideas/       → lister mes idées
# GET    /api/ideas/{id}   → voir une idée
# DELETE /api/ideas/{id}   → supprimer une idée
#
# ❌ PUT absent intentionnellement
#    Modifier l'idée après pipeline = résultats incohérents
# ─────────────────────────────────────────

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.idea import IdeaCreate, IdeaOut, IdeaListOut
from app.services.idea_service import (
    create_idea,
    get_user_ideas,
    get_idea_by_id,
    delete_idea,
)

router = APIRouter(prefix="/ideas", tags=["Idées"])


@router.post(
    "/",
    response_model=IdeaOut,
    status_code=201,
    summary="Soumettre une idée",
)
def create(
    data: IdeaCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Sauvegarde une nouvelle idée de projet.
    Status initial = "pending".

    ```json
    {
        "name": "EcoShop",
        "sector": "ecommerce",
        "description": "Une marketplace durable et locale..."
    }
    ```
    """
    return create_idea(data, current_user.id, db)


@router.get(
    "/",
    response_model=IdeaListOut,
    status_code=200,
    summary="Lister mes idées",
)
def list_ideas(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retourne toutes les idées de l'utilisateur connecté.
    """
    ideas = get_user_ideas(current_user.id, db)
    return IdeaListOut(ideas=ideas, total=len(ideas))


@router.get(
    "/{idea_id}",
    response_model=IdeaOut,
    status_code=200,
    summary="Voir une idée",
)
def get_one(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retourne les détails d'une idée.
    """
    return get_idea_by_id(idea_id, current_user.id, db)


@router.delete(
    "/{idea_id}",
    status_code=200,
    summary="Supprimer une idée",
)
def delete(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Supprime une idée.
    Impossible si le pipeline est en cours (status = running).
    """
    return delete_idea(idea_id, current_user.id, db)
