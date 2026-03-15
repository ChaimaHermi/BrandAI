 # ==============================================================
#  app/schemas/auth.py
#  RÔLE : Valider et typer les données qui entrent et sortent
#         des routes d'authentification
#
#  ANALOGUE NODE.JS :
#    const Joi = require('joi')
#    const registerSchema = Joi.object({
#      name: Joi.string().min(2).required(),
#      email: Joi.string().email().required(),
#      password: Joi.string().min(6).required()
#    })
#
#  DIFFÉRENCE MODÈLE vs SCHÉMA :
#    models/user.py  → structure de la TABLE en base de données
#    schemas/auth.py → structure des DONNÉES HTTP (request/response)
#
#    Exemple : le schéma RegisterRequest a "password"
#              mais le modèle User a "hashed_password"
#              → on ne stocke jamais le mot de passe en clair
#
#  COMMENT PYDANTIC VALIDE :
#    Si le client envoie { "email": "pas-un-email" }
#    → Pydantic lève automatiquement une erreur 422
#    → FastAPI retourne { "detail": [{"msg": "value is not a valid email"}] }
#    → la route n'est même pas appelée
# ==============================================================

from pydantic import BaseModel, EmailStr, field_validator


# ==============================================================
#  REQUÊTES (ce que le client ENVOIE au serveur)
# ==============================================================

class RegisterRequest(BaseModel):
    """
    Corps de POST /api/auth/register

    Le client envoie :
    {
        "name": "Ahmed Ben Ali",
        "email": "ahmed@gmail.com",
        "password": "monpassword123"
    }

    Pydantic valide automatiquement :
    - name   → string non vide (min 2 caractères via validator)
    - email  → format email valide (EmailStr)
    - password → string (min 6 caractères via validator)
    """
    name: str
    email: EmailStr    # EmailStr vérifie le format "xxx@xxx.xx"
    password: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Nettoie les espaces et vérifie la longueur minimale."""
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Le nom doit contenir au moins 2 caractères")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Vérifie que le mot de passe est assez long."""
        if len(v) < 6:
            raise ValueError("Le mot de passe doit contenir au moins 6 caractères")
        return v


class LoginRequest(BaseModel):
    """
    Corps de POST /api/auth/login

    Le client envoie :
    {
        "email": "ahmed@gmail.com",
        "password": "monpassword123"
    }
    """
    email: EmailStr
    password: str


# ==============================================================
#  RÉPONSES (ce que le serveur RENVOIE au client)
# ==============================================================

class TokenResponse(BaseModel):
    """
    Réponse de /register et /login quand c'est OK.

    Le serveur renvoie :
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "name": "Ahmed Ben Ali",
            "email": "ahmed@gmail.com"
        }
    }

    Le frontend stocke access_token dans localStorage
    et l'envoie dans chaque requête :
    Authorization: Bearer eyJhbGci...
    """
    access_token: str
    token_type: str = "bearer"   # valeur par défaut
    user: dict                   # { id, name, email }
