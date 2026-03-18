# app/schemas/idea.py
# ─────────────────────────────────────────
# Schémas Pydantic pour les idées
# ─────────────────────────────────────────

from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime


class IdeaCreate(BaseModel):
    """
    Corps de POST /api/ideas/
    Ce que l'utilisateur envoie pour soumettre une idée.

    {
        "name": "EcoShop",
        "sector": "ecommerce" | "",
        "target_audience": "PME, entrepreneurs" | "",
        "description": "Une marketplace durable et locale..."
    }
    """

    # Approche texte libre : le nom peut être vide au départ.
    name: Optional[str] = ""
    # Approche B : le secteur peut être vide au moment de la création,
    # il sera détecté automatiquement par l'Idea Clarifier.
    sector: str | None = ""
    # Idem pour le public cible : champ libre optionnel.
    target_audience: str | None = ""
    description: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> str:
        """
        Le nom peut être vide ("") — il sera généré plus tard
        par le Brand Identity Agent si nécessaire.
        """
        if v is None:
            return ""
        v = v.strip()
        # Si un nom est fourni, on applique quand même une validation minimale.
        if v and len(v) < 2:
            raise ValueError("Le nom doit contenir au moins 2 caractères")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 20:
            raise ValueError("La description doit contenir au moins 20 caractères")
        return v

    @field_validator("sector")
    @classmethod
    def validate_sector(cls, v: str | None) -> str | None:
        """
        En Approche B, sector peut être vide ("") ou None.
        On laisse le Clarifier le déduire à partir de la description.
        """
        if v is None:
          return ""
        v = v.strip()
        return v


class IdeaOut(BaseModel):
    """
    Ce que le serveur retourne au client après création / lecture.
    """
    id: int
    user_id: int
    name: str
    sector: str
    target_audience: str | None = None
    description: str
    status: str           # pending | running | done | error
    created_at: datetime

    # Résultat Clarifier
    clarity_status: Optional[str] = None
    clarity_score: Optional[int] = None
    clarity_sector: Optional[str] = None
    clarity_target_users: Optional[str] = None
    clarity_problem: Optional[str] = None
    clarity_solution: Optional[str] = None
    clarity_short_pitch: Optional[str] = None
    clarity_agent_message: Optional[str] = None
    clarity_questions: Optional[Any] = None
    clarity_answers: Optional[Any] = None
    clarity_refused_reason: Optional[str] = None
    clarity_refused_message: Optional[str] = None

    # Progression de pipeline (historique des étapes)
    pipeline_progress: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class IdeaListOut(BaseModel):
    """
    Réponse de GET /api/ideas/
    Liste de toutes les idées + total
    """
    ideas: list[IdeaOut]
    total: int
