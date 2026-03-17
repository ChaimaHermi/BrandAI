 
# ==============================================================
#  app/api/routes/auth.py
#  RÔLE : Définir les endpoints HTTP d'authentification
#
#  RÈGLE DES ROUTES :
#    Une route doit faire UNE seule chose :
#    → Lire les données HTTP (body, headers, query params)
#    → Appeler le service correspondant
#    → Retourner la réponse HTTP
#    La logique métier est dans services/auth_service.py
#
#  ENDPOINTS DÉFINIS ICI :
#    POST /api/auth/register → créer un compte
#    POST /api/auth/login    → se connecter
#    GET  /api/auth/me       → voir son profil (protégé)
#
#  ANALOGUE EXPRESS :
#    // routes/auth.js
#    router.post('/register', async (req, res) => {
#      const result = await authService.register(req.body)
#      res.status(201).json(result)
#    })
# ==============================================================

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.oauth import oauth
from app.core.config import settings
from app.core.security import create_access_token
from app.api.deps import get_current_user
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserOut
from app.models.user import User
from app.services.auth_service import register_user, login_user
from app.utils.helpers import format_user_response


# APIRouter = équivalent de express.Router()
# prefix="/auth" → toutes les routes commencent par /auth
# tags=["..."]   → groupe dans Swagger UI
router = APIRouter(prefix="/auth", tags=["Authentification"])
logger = logging.getLogger(__name__)


# ==============================================================
#  POST /api/auth/register
# ==============================================================

@router.post(
    "/register",
    response_model=TokenResponse,   # Pydantic valide aussi la RÉPONSE
    status_code=201,                # 201 Created (convention REST)
    summary="Créer un compte",
)
def register(
    data: RegisterRequest,          # body JSON → validé par Pydantic automatiquement
    db: Session = Depends(get_db),  # session BDD injectée par FastAPI
):
    """
    Crée un nouveau compte utilisateur.

    **Body :**
    ```json
    {
        "name": "Ahmed Ben Ali",
        "email": "ahmed@gmail.com",
        "password": "monpassword123"
    }
    ```

    **Réponse 201 :**
    ```json
    {
        "access_token": "eyJhbGci...",
        "token_type": "bearer",
        "user": { "id": 1, "name": "Ahmed Ben Ali", "email": "ahmed@gmail.com" }
    }
    ```

    **Erreurs :**
    - 400 : email déjà utilisé
    - 422 : données invalides (email malformé, password trop court)
    """
    return register_user(data, db)


# ==============================================================
#  POST /api/auth/login
# ==============================================================

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=200,
    summary="Se connecter",
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authentifie un utilisateur et retourne un token JWT.

    **Body :**
    ```json
    {
        "email": "ahmed@gmail.com",
        "password": "monpassword123"
    }
    ```

    **Réponse 200 :**
    ```json
    {
        "access_token": "eyJhbGci...",
        "token_type": "bearer",
        "user": { "id": 1, "name": "Ahmed Ben Ali", "email": "ahmed@gmail.com" }
    }
    ```

    **Erreurs :**
    - 401 : email ou mot de passe incorrect
    """
    return login_user(data, db)


# ==============================================================
#  GET /api/auth/me  (route protégée)
# ==============================================================

@router.get(
    "/me",
    response_model=UserOut,         # retourne le profil sans hashed_password
    status_code=200,
    summary="Mon profil",
)
def get_me(
    # get_current_user vérifie le token JWT avant d'exécuter la route
    # Si token invalide → 401 automatique, la route n'est pas appelée
    current_user: User = Depends(get_current_user),
):
    """
    Retourne le profil de l'utilisateur connecté.

    **Header requis :**
    ```
    Authorization: Bearer eyJhbGci...
    ```

    **Réponse 200 :**
    ```json
    {
        "id": 1,
        "name": "Ahmed Ben Ali",
        "email": "ahmed@gmail.com",
        "created_at": "2026-03-14T10:30:00Z"
    }
    ```

    **Erreurs :**
    - 401 : token manquant ou invalide
    """
    return current_user


# ── Routes Google OAuth ───────────────────────────────────────

@router.get("/google", summary="Connexion avec Google")
async def google_login(request: Request):
    """
    Redirige l'utilisateur vers la page de connexion Google.
    Le frontend appelle cette URL directement.
    """
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", summary="Callback Google OAuth")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Google rappelle cette route avec un code.
    On échange ce code contre les infos utilisateur.
    Puis on crée/connecte l'utilisateur et on redirige le frontend.
    """
    try:
        # 1. Échanger le code contre un token Google
        token = await oauth.google.authorize_access_token(request)

        # 2. Récupérer les infos de l'utilisateur depuis Google
        user_info = token.get("userinfo")
        if not user_info:
            # Fallback : appeler l'API Google manuellement
            user_info = await oauth.google.userinfo(token=token)

        google_id = user_info.get("sub")       # ID unique Google
        email     = user_info.get("email")
        name      = user_info.get("name")
        picture   = user_info.get("picture")   # URL photo de profil

        if not email:
            raise ValueError("Google n'a pas renvoyé d'email.")

        safe_name = name or (email.split("@")[0] if email else None) or "Utilisateur Google"

        # 3. Chercher l'utilisateur par google_id
        user = db.query(User).filter(User.google_id == google_id).first()

        if not user:
            # 4a. Chercher par email (compte existant sans Google)
            user = db.query(User).filter(User.email == email).first()

            if user:
                # Lier le compte Google au compte existant
                user.google_id = google_id
                user.avatar_url = picture
                db.commit()
                db.refresh(user)
            else:
                # 4b. Créer un nouveau compte
                user = User(
                    name=safe_name,
                    email=email,
                    google_id=google_id,
                    avatar_url=picture,
                    hashed_password=None,  # pas de mot de passe pour Google
                )
                db.add(user)
                db.commit()
                db.refresh(user)

        # 5. Générer le JWT BrandAI
        jwt_token = create_access_token(user.id)

        # 6. Rediriger le frontend avec le token dans l'URL
        frontend_url = f"{settings.FRONTEND_CALLBACK_URL}?token={jwt_token}"
        return RedirectResponse(url=frontend_url)

    except Exception as e:
        logger.exception("Google OAuth callback failed")
        # En cas d'erreur → rediriger vers login avec message
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=google_auth_failed"
        )