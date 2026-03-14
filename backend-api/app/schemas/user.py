# ==============================================================
#  app/schemas/user.py
#  RÔLE : Définir ce qu'on renvoie au client quand il
#         demande des infos sur un utilisateur
#
#  RÈGLE DE SÉCURITÉ FONDAMENTALE :
#    Ce schéma n'inclut JAMAIS "hashed_password"
#    → même si quelqu'un intercepte la réponse,
#      il ne voit jamais le hash du mot de passe
#
#  ANALOGUE NODE.JS :
#    // Avant de renvoyer l'user, on supprime le mot de passe
#    const { password, ...userWithoutPassword } = user
#    res.json(userWithoutPassword)
#
#  AVEC PYDANTIC : c'est automatique
#    On définit exactement les champs à exposer
#    → les autres champs du modèle sont ignorés
# ==============================================================

from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserOut(BaseModel):
    """
    Ce que le serveur renvoie quand le client demande GET /api/auth/me

    Contient seulement les champs PUBLICS de l'utilisateur.
    "hashed_password" est volontairement absent.

    {
        "id": 1,
        "name": "Ahmed Ben Ali",
        "email": "ahmed@gmail.com",
        "created_at": "2026-03-14T10:30:00Z"
    }
    """
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    # model_config with from_attributes=True permet à Pydantic
    # de lire les données depuis un objet SQLAlchemy (pas seulement un dict)
    #
    # Sans ça : UserOut(**user.__dict__) → erreur
    # Avec ça  : UserOut.model_validate(user) → fonctionne
    model_config = {"from_attributes": True}