 
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

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.user import UserOut
from app.models.user import User
from app.services.auth_service import register_user, login_user


# APIRouter = équivalent de express.Router()
# prefix="/auth" → toutes les routes commencent par /auth
# tags=["..."]   → groupe dans Swagger UI
router = APIRouter(prefix="/auth", tags=["Authentification"])


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