 
# ==============================================================
#  app/api/deps.py
#  RÔLE : Dépendances FastAPI = Middlewares + Utils injectables
#
#  DIFFÉRENCE AVEC utils/helpers.py :
#    utils/helpers.py → fonctions pures, pas liées à FastAPI
#    deps.py          → fonctions injectées dans les routes
#                       avec Depends() de FastAPI
#
#  COMMENT FONCTIONNE Depends() :
#    FastAPI appelle la fonction AVANT d'exécuter la route.
#    Si la fonction lève une exception → la route n'est pas exécutée.
#    Si la fonction retourne une valeur → elle est injectée comme paramètre.
#
#  ANALOGUE NODE.JS :
#    // middleware/auth.js
#    module.exports = (req, res, next) => {
#      const token = req.headers.authorization?.split(' ')[1]
#      if (!token) return res.status(401).json({ error: 'Token manquant' })
#      const decoded = jwt.verify(token, SECRET_KEY)
#      req.user = decoded
#      next()
#    }
#
#    // Route protégée
#    router.get('/dashboard', authMiddleware, (req, res) => {
#      res.json(req.user)  // req.user injecté par le middleware
#    })
#
#  ÉQUIVALENT FASTAPI :
#    @router.get('/dashboard')
#    def dashboard(user: User = Depends(get_current_user)):
#      return user  // user injecté par Depends
# ==============================================================

from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.utils.helpers import compute_pagination


# ── Schéma Bearer ─────────────────────────────────────────────
# HTTPBearer lit automatiquement le header :
# Authorization: Bearer eyJhbGci...
# auto_error=False → on gère l'erreur nous-mêmes (message en français)
bearer_scheme = HTTPBearer(auto_error=False)


# ==============================================================
#  DEP 1 : get_current_user
#  Protège les routes qui nécessitent d'être connecté
#  Équivalent : authMiddleware dans Express
# ==============================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dépendance qui vérifie le token JWT et retourne l'utilisateur connecté.

    FLUX :
      1. Extrait le token du header Authorization
      2. Décode le JWT → récupère l'user_id
      3. Charge l'utilisateur depuis PostgreSQL
      4. Retourne l'objet User (injecté dans la route)

    UTILISATION DANS UNE ROUTE :
      @router.get("/dashboard")
      def dashboard(user: User = Depends(get_current_user)):
          return { "message": f"Bonjour {user.name}" }

    ERREURS :
      → 401 si pas de token
      → 401 si token invalide ou expiré
      → 401 si utilisateur supprimé entre-temps
    """
    # ── Vérifier que le token est présent ─────────────────────
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token manquant. Connectez-vous d'abord.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Décoder le JWT ────────────────────────────────────────
    # decode_access_token lève 401 si invalide/expiré
    user_id = decode_access_token(credentials.credentials)

    # ── Charger l'utilisateur depuis la BDD ───────────────────
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable. Token invalide.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user  # ← injecté dans la route comme paramètre


# ==============================================================
#  DEP 2 : get_pagination
#  Réutilisable sur toutes les routes qui retournent des listes
#  Équivalent : middleware de pagination dans Express
# ==============================================================

def get_pagination(
    page: int = Query(default=1, ge=1, description="Numéro de page (commence à 1)"),
    limit: int = Query(default=10, ge=1, le=100, description="Nombre d'éléments par page"),
) -> dict:
    """
    Dépendance de pagination réutilisable.

    QUERY PARAMS automatiques dans l'URL :
      GET /api/projects?page=2&limit=5

    UTILISATION DANS UNE ROUTE :
      @router.get("/projects")
      def list_projects(
          pagination: dict = Depends(get_pagination),
          user: User = Depends(get_current_user),
          db: Session = Depends(get_db),
      ):
          projects = db.query(Project)
                       .offset(pagination["skip"])
                       .limit(pagination["limit"])
                       .all()
          return projects

    RETOURNE :
      { "skip": 10, "limit": 5, "page": 2 }
    """
    return compute_pagination(page, limit)


# ==============================================================
#  DEP 3 : require_admin  (pour plus tard)
#  Vérifie que l'utilisateur connecté est admin
#  Chaîne de dépendances : require_admin → get_current_user
# ==============================================================

# def require_admin(user: User = Depends(get_current_user)) -> User:
#     """
#     Vérifie que l'utilisateur a le rôle 'admin'.
#     Dépend de get_current_user → token aussi vérifié.
#
#     UTILISATION :
#       @router.delete("/users/{id}")
#       def delete_user(admin: User = Depends(require_admin)):
#           ...
#     """
#     if user.role != "admin":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Accès refusé. Droits administrateur requis.",
#         )
#     return user