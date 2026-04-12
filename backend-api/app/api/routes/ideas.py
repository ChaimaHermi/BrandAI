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

from typing import Any, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.idea import Idea
from app.schemas.idea import IdeaCreate, IdeaOut, IdeaListOut
from app.schemas.pipeline_availability import PipelineAvailabilityOut
from app.services.idea_service import (
    create_idea,
    get_user_ideas,
    get_idea_by_id,
    delete_idea,
)
from app.services.pipeline_availability_service import get_pipeline_availability

router = APIRouter(prefix="/ideas", tags=["Idées"])


class ClarifierSaveRequest(BaseModel):
    """Corps de PATCH /api/ideas/{idea_id}/clarifier-result"""
    clarity_status: Optional[str] = None
    clarity_score: Optional[int] = None
    clarity_sector: Optional[str] = None
    clarity_target_users: Optional[str] = None
    clarity_problem: Optional[str] = None
    clarity_solution: Optional[str] = None
    clarity_short_pitch: Optional[str] = None
    clarity_agent_message: Optional[str] = None
    clarity_country: Optional[str] = None
    clarity_country_code: Optional[str] = None
    clarity_language: Optional[str] = None
    clarity_questions: Optional[list] = None
    clarity_answers: Optional[dict] = None
    clarity_refused_reason: Optional[str] = None
    clarity_refused_message: Optional[str] = None
    pipeline_progress: Optional[Any] = None


class PipelineProgressMergeRequest(BaseModel):
    """Fusionne des clés dans `ideas.pipeline_progress` (ex. brand_identity)."""
    brand_identity: Optional[Dict[str, Any]] = None


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
    "/{idea_id}/pipeline-availability",
    response_model=PipelineAvailabilityOut,
    status_code=200,
    summary="Indicateurs market / marketing / branding (sans requêtes 404)",
)
def pipeline_availability(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_pipeline_availability(db, idea_id, current_user.id)


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


@router.patch(
    "/{idea_id}/clarifier-result",
    status_code=200,
    summary="Sauvegarder le résultat du Clarifier",
)
def save_clarifier_result(
    idea_id: int,
    body: ClarifierSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Enregistre l'état du Clarifier (clarified / refused / questions) sur l'idée.
    """
    idea = (
        db.query(Idea)
        .filter(Idea.id == idea_id, Idea.user_id == current_user.id)
        .first()
    )
    if not idea:
        raise HTTPException(status_code=404, detail="Idée introuvable")

    # Mettre à jour le statut pour refléter la progression dans la liste
    if body.clarity_status == "questions":
        idea.status = "in_progress"
    elif body.clarity_status == "clarified":
        idea.status = "clarifier_done"
    elif body.clarity_status == "refused":
        idea.status = "error"

    fields = body.model_dump(exclude_none=True)
    for field, value in fields.items():
        if hasattr(idea, field):
            setattr(idea, field, value)

    db.commit()
    db.refresh(idea)
    return {"success": True, "idea_id": idea_id}


@router.patch(
    "/{idea_id}/pipeline-progress",
    status_code=200,
    summary="Fusionner pipeline_progress (brand_identity, etc.)",
)
def merge_pipeline_progress(
    idea_id: int,
    body: PipelineProgressMergeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Met à jour le JSON pipeline_progress sans écraser les autres clés existantes.
    """
    idea = (
        db.query(Idea)
        .filter(Idea.id == idea_id, Idea.user_id == current_user.id)
        .first()
    )
    if not idea:
        raise HTTPException(status_code=404, detail="Idée introuvable")

    progress = dict(idea.pipeline_progress or {})
    if body.brand_identity is not None:
        progress["brand_identity"] = body.brand_identity
    idea.pipeline_progress = progress

    db.commit()
    db.refresh(idea)
    return {"success": True, "idea_id": idea_id}
