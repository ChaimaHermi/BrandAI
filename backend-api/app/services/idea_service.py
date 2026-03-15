# app/services/idea_service.py
# ─────────────────────────────────────────
# Logique métier des idées.
# ─────────────────────────────────────────

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.idea import Idea
from app.schemas.idea import IdeaCreate


def create_idea(data: IdeaCreate, user_id: int, db: Session) -> Idea:
    """
    Sauvegarde une nouvelle idée en BDD.
    Status initial = "pending" → pipeline pas encore lancé.
    """
    idea = Idea(
        user_id=user_id,
        name=data.name,
        sector=data.sector,
        target_audience=data.target_audience,
        description=data.description,
        status="pending",
    )
    db.add(idea)
    db.commit()
    db.refresh(idea)
    return idea


def get_user_ideas(user_id: int, db: Session) -> list[Idea]:
    """
    Retourne toutes les idées d'un utilisateur.
    Triées de la plus récente à la plus ancienne.
    """
    return (
        db.query(Idea)
        .filter(Idea.user_id == user_id)
        .order_by(Idea.created_at.desc())
        .all()
    )


def get_idea_by_id(idea_id: int, user_id: int, db: Session) -> Idea:
    """
    Retourne une idée par son ID.
    Vérifie que l'idée appartient bien à l'utilisateur connecté.

    Raises:
        404 si l'idée n'existe pas
        403 si l'idée appartient à un autre utilisateur
    """
    idea = db.query(Idea).filter(Idea.id == idea_id).first()

    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idée introuvable",
        )

    if idea.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé. Cette idée ne vous appartient pas.",
        )

    return idea


def delete_idea(idea_id: int, user_id: int, db: Session) -> dict:
    """
    Supprime une idée.
    Vérifie que l'idée appartient à l'utilisateur connecté.
    Une idée avec status "running" ne peut pas être supprimée.
    """
    idea = get_idea_by_id(idea_id, user_id, db)

    # Sécurité : bloquer la suppression si pipeline en cours
    if idea.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de supprimer une idée dont le pipeline est en cours.",
        )

    name = idea.name
    db.delete(idea)
    db.commit()

    return {"message": f"Idée '{name}' supprimée avec succès"}
