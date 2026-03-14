 
# ==============================================================
#  app/core/security.py
#  RÔLE : Deux responsabilités de sécurité
#    1. Hash/vérification des mots de passe (bcrypt)
#    2. Création/décodage des tokens JWT
#
#
#  POURQUOI BCRYPT ?
#    Un hash bcrypt de "password123" donne :
#    "$2b$12$eImiTXuWVxfM37uY4JANjQ..."
#    → impossible de retrouver le mot de passe original
#    → même si la BDD est volée, les mots de passe sont protégés
#
#  POURQUOI JWT ?
#    Après le login, le serveur envoie un token au client.
#    Le client l'envoie à chaque requête :
#    Header: Authorization: Bearer eyJhbGci...
#    Le serveur vérifie la signature → sait que c'est authentique
#    → pas besoin de session en mémoire côté serveur
# ==============================================================

from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import HTTPException, status
from app.core.config import settings


# ── Contexte bcrypt ───────────────────────────────────────────
# schemes=["bcrypt"] → utilise l'algorithme bcrypt
# deprecated="auto" → gère automatiquement les anciens algorithmes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==============================================================
#  PARTIE 1 : Mots de passe
# ==============================================================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:

    return pwd_context.verify(plain_password, hashed_password)


# ==============================================================
#  PARTIE 2 : JWT (JSON Web Token)
# ==============================================================
#
#  Structure d'un JWT :
#    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9   ← header (encodé base64)
#    .eyJzdWIiOiI0MiIsImV4cCI6MTIzNDU2Nzg5MH0  ← payload (encodé base64)
#    .SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c  ← signature
#
#  Le payload contient :
#    { "sub": "42", "exp": 1234567890, "type": "access" }
#    "sub" = subject = l'id de l'utilisateur
#    "exp" = expiration timestamp

def create_access_token(user_id: int) -> str:
    """
    Crée un token JWT signé pour un utilisateur.
    Le token expire après ACCESS_TOKEN_EXPIRE_MINUTES minutes.

    EXEMPLE :
      create_access_token(42)
      → "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

    Ce token est envoyé au client après login/register.
    Le client le stocke (localStorage) et l'envoie dans chaque requête.

  
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),    # toujours une string dans JWT
        "exp": expire,           # date d'expiration
        "type": "access",        # utile si on ajoute un refresh token plus tard
    }
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,   # HS256
    )


def decode_access_token(token: str) -> int:
    """
    Décode un token JWT et retourne l'user_id.

    FLUX :
      1. Vérifie que la signature est valide (SECRET_KEY)
      2. Vérifie que le token n'est pas expiré
      3. Extrait et retourne l'user_id (payload["sub"])

    ERREURS :
      → HTTPException 401 si token invalide
      → HTTPException 401 si token expiré

    Utilisé dans deps.py pour protéger les routes.

    ANALOGUE NODE.JS :
      jwt.verify(token, process.env.SECRET_KEY)
    """
    # On prépare l'exception à l'avance (réutilisée dans plusieurs cas)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré. Reconnectez-vous.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        return int(user_id_str)

    except JWTError:
        # Token mal formé, signature incorrecte ou expiré
        raise credentials_exception