 
# ==============================================================
#  app/main.py
#  RÔLE : Point d'entrée de l'application FastAPI
#
#  C'est le fichier que uvicorn exécute :
#    uvicorn app.main:app --reload
#    ↑ module  ↑ variable "app" dans ce fichier
#
#  RESPONSABILITÉS :
#    1. Créer l'instance FastAPI
#    2. Configurer CORS (autorise le frontend React)
#    3. Enregistrer tous les routers
#    4. Route /health pour vérifier que l'API tourne
#
#  ANALOGUE EXPRESS :
#    // server.js
#    const app = express()
#    app.use(cors())
#    app.use('/api/auth', authRouter)
#    app.listen(8000)
# ==============================================================





import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.core.database import Base, engine
import app.models.user  # noqa
import app.models.idea  # noqa
import app.models.market_analysis  # noqa
import app.models.marketing_plan  # noqa
import app.models.brand_identity  # noqa
import app.models.branding_results  # noqa
import app.models.generated_content  # noqa
import app.models.user_social_connection  # noqa
import app.models.scheduled_publication  # noqa
import app.models.notification  # noqa
import app.models.website_project  # noqa
from app.api.routes import (
    auth,
    ideas,
    idea_generated_contents,
    market_analysis,
    marketing_plans,
    branding_results,
    social_connections,
    idea_scheduled_publications,
    notifications,
    website_projects,
)

app = FastAPI(
    title="BrandAI API",
    description="Backend BrandAI",
    version="1.0.0",
)

# SessionMiddleware OBLIGATOIRE pour authlib
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
)


# ── CORS ──────────────────────────────────────────────────────
# CORS = Cross-Origin Resource Sharing
# Sans ça, le navigateur bloque les requêtes du frontend (port 5173)
# vers le backend (port 8000) → erreur "CORS policy" dans la console
#
# ANALOGUE EXPRESS :
#   app.use(cors({ origin: 'http://localhost:5173' }))

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ── Création des tables au démarrage ─────────────────────────
# SQLAlchemy crée les tables manquantes automatiquement.
# En production on utilisera Alembic pour les migrations.
@app.on_event("startup")
async def startup():
    import asyncio
    import threading
    from app.workers.scheduled_publisher import run_publisher_loop

    Base.metadata.create_all(bind=engine)

    # Run publisher loop in a dedicated thread/event-loop to avoid
    # blocking the FastAPI main event loop and HTTP responses.
    def _publisher_thread_target():
        asyncio.run(run_publisher_loop())

    threading.Thread(
        target=_publisher_thread_target,
        name="scheduled-publisher",
        daemon=True,
    ).start()
    print("✅ BrandAI API démarrée (+ publisher worker thread)")
# ── Enregistrement des routers ────────────────────────────────
# prefix="/api" → toutes les routes commencent par /api/...
# Résultat :
#   POST /api/auth/register
#   POST /api/auth/login
#   GET  /api/auth/me
app.include_router(auth.router, prefix="/api")
app.include_router(ideas.router, prefix="/api")
app.include_router(idea_generated_contents.router, prefix="/api")
app.include_router(market_analysis.router, prefix="/api")
app.include_router(marketing_plans.router, prefix="/api")
app.include_router(branding_results.router, prefix="/api")
app.include_router(social_connections.router, prefix="/api")
app.include_router(idea_scheduled_publications.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(website_projects.router, prefix="/api")

# ── Route de santé ────────────────────────────────────────────
# GET /health → vérifie que l'API est en ligne
# Utile pour les outils de monitoring
@app.get("/health", tags=["Santé"])
def health_check():
    return {"status": "ok", "app": "BrandAI API"}