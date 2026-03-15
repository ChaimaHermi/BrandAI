# app/schemas/idea.py
# ─────────────────────────────────────────
# Schémas Pydantic pour les idées
# ─────────────────────────────────────────

from pydantic import BaseModel, field_validator
from datetime import datetime


class IdeaCreate(BaseModel):
    """
    Corps de POST /api/ideas/
    Ce que l'utilisateur envoie pour soumettre une idée.

    {
        "name": "EcoShop",
        "sector": "ecommerce",
        "target_audience": "PME, entrepreneurs",
        "description": "Une marketplace durable et locale..."
    }
    """
    name: str
    sector: str
    target_audience: str | None = None
    description: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
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
    def validate_sector(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Le secteur est obligatoire")
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

    model_config = {"from_attributes": True}


class IdeaListOut(BaseModel):
    """
    Réponse de GET /api/ideas/
    Liste de toutes les idées + total
    """
    ideas: list[IdeaOut]
    total: int
