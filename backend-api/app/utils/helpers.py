# ==============================================================
#  app/utils/helpers.py
#  RÔLE : Fonctions utilitaires PURES et RÉUTILISABLES
#         Non liées à FastAPI (pas de Request, pas de Depends)
#
#  RÈGLE : Si une fonction ne dépend pas de FastAPI
#          → elle va dans utils/
#          Si une fonction est injectée dans une route avec Depends()
#          → elle va dans deps.py
#
#  ANALOGUE NODE.JS :
#    // utils/helpers.js
#    const formatDate = (date) => date.toISOString()
#    const paginate = (page, limit) => ({ skip: (page-1)*limit, limit })
#    module.exports = { formatDate, paginate }
# ==============================================================

from datetime import datetime, timezone


# ==============================================================
#  FORMATAGE
# ==============================================================

def format_user_response(user) -> dict:
    """
    Convertit un objet User SQLAlchemy en dict JSON-sérialisable.
    Utilisé dans auth_service.py pour construire la réponse.

    EXEMPLE :
      user = db.query(User).first()
      format_user_response(user)
      → { "id": 1, "name": "Ahmed", "email": "ahmed@gmail.com" }

    NOTE : On n'inclut PAS hashed_password — jamais exposé au client.
    """
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "avatar_url": user.avatar_url,
    }


# ==============================================================
#  PAGINATION
# ==============================================================

def compute_pagination(page: int = 1, limit: int = 10) -> dict:
    """
    Calcule offset et limit pour les requêtes paginées.
    Utilisé dans les routes qui retournent des listes.

    EXEMPLE :
      compute_pagination(page=2, limit=10)
      → { "skip": 10, "limit": 10 }

    Utilisation dans une route :
      projects = db.query(Project)
                   .offset(pagination["skip"])
                   .limit(pagination["limit"])
                   .all()
    """
    if page < 1:
        page = 1
    if limit < 1 or limit > 100:
        limit = 10
    return {
        "skip": (page - 1) * limit,
        "limit": limit,
        "page": page,
    }


# ==============================================================
#  DATES
# ==============================================================

def now_utc() -> datetime:
    """
    Retourne l'heure actuelle en UTC avec timezone.
    Toujours utiliser cette fonction plutôt que datetime.now()
    → évite les bugs de timezone.
    """
    return datetime.now(timezone.utc)