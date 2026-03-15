 
# ==============================================================
#  app/services/auth_service.py
#  RÔLE : Logique métier de l'authentification
#
#  POURQUOI SÉPARER SERVICE ET ROUTE ?
#    - La route (routes/auth.py) gère uniquement le HTTP
#      (lire le body, retourner une réponse)
#    - Le service gère la LOGIQUE
#      (vérifier si email existe, hasher le password, etc.)
#    - Avantage : on peut tester le service sans HTTP
#    - Avantage : si on change FastAPI pour un autre framework,
#      la logique ne change pas
#

# ==============================================================

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.utils.helpers import format_user_response


def register_user(data: RegisterRequest, db: Session) -> TokenResponse:
    """
    Inscription d'un nouvel utilisateur.

    FLUX :
      1. Vérifier que l'email n'est pas déjà pris
      2. Hasher le mot de passe (bcrypt)
      3. Créer l'utilisateur dans PostgreSQL
      4. Générer un JWT
      5. Retourner { access_token, user }

    ERREURS :
      → 400 Bad Request si l'email existe déjà

    PARAMÈTRES :
      data → RegisterRequest validé par Pydantic
             { name, email, password }
      db   → session PostgreSQL injectée par Depends(get_db)
    """
    # ── Étape 1 : Vérifier l'unicité de l'email ───────────────
    # db.query(User) → SELECT * FROM users
    # .filter(...)   → WHERE email = data.email
    # .first()       → LIMIT 1 (retourne None si pas trouvé)
    existing_user = db.query(User).filter(User.email == data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un compte avec cet email existe déjà",
        )

    # ── Étape 2 + 3 : Hasher + créer l'utilisateur ────────────
    new_user = User(
        name=data.name,
        email=data.email,
        hashed_password=hash_password(data.password),  # jamais en clair !
    )
    db.add(new_user)    # prépare l'INSERT
    db.commit()         # exécute l'INSERT dans PostgreSQL
    db.refresh(new_user)  # recharge l'objet pour avoir l'id généré par PostgreSQL

    # ── Étape 4 + 5 : Générer le JWT et retourner ─────────────
    token = create_access_token(new_user.id)

    return TokenResponse(
        access_token=token,
        user=format_user_response(new_user),
    )


def login_user(data: LoginRequest, db: Session) -> TokenResponse:
    """
    Connexion d'un utilisateur existant.

    FLUX :
      1. Chercher l'utilisateur par email
      2. Vérifier le mot de passe avec bcrypt
      3. Générer un JWT
      4. Retourner { access_token, user }

    SÉCURITÉ IMPORTANTE :
      On retourne TOUJOURS le même message d'erreur
      "Email ou mot de passe incorrect"
      que ce soit l'email ou le mot de passe qui est faux.

      Pourquoi ? Pour éviter l'énumération d'emails :
      Si on dit "email inconnu" → un attaquant sait quels emails existent
      Si on dit toujours la même chose → l'attaquant ne sait rien

    ERREURS :
      → 401 Unauthorized si email inconnu ou mot de passe faux
    """
    # Message générique pour les deux types d'erreur
    invalid_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email ou mot de passe incorrect",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # ── Étape 1 : Chercher l'utilisateur ──────────────────────
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise invalid_error   # email inconnu → même erreur

    # ── Étape 2 : Vérifier le mot de passe ────────────────────
    if not verify_password(data.password, user.hashed_password):
        raise invalid_error   # mauvais mdp → même erreur

    # ── Étape 3 + 4 : Générer le JWT et retourner ─────────────
    token = create_access_token(user.id)

    return TokenResponse(
        access_token=token,
        user=format_user_response(user),
    )