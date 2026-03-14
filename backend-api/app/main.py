 
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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine

# Import des modèles OBLIGATOIRE avant create_all
# Sans ça, SQLAlchemy ne connaît pas les tables à créer
import app.models.user  # noqa: F401

# Import des routers
from app.api.routes import auth


# ── Création de l'app ─────────────────────────────────────────
app = FastAPI(
    title="BrandAI API",
    description="Backend de la plateforme BrandAI — IA Générative & Agentique",
    version="1.0.0",
    # Swagger UI disponible sur : http://localhost:8000/docs
    # ReDoc disponible sur      : http://localhost:8000/redoc
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
        settings.FRONTEND_URL,       # depuis .env
        "http://localhost:5173",     # fallback
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,          # autorise le header Authorization
    allow_methods=["*"],             # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],             # Content-Type, Authorization, etc.
)


# ── Création des tables au démarrage ─────────────────────────
# SQLAlchemy crée les tables manquantes automatiquement.
# En production on utilisera Alembic pour les migrations.
@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées / vérifiées")


# ── Enregistrement des routers ────────────────────────────────
# prefix="/api" → toutes les routes commencent par /api/...
# Résultat :
#   POST /api/auth/register
#   POST /api/auth/login
#   GET  /api/auth/me
app.include_router(auth.router, prefix="/api")


# ── Route de santé ────────────────────────────────────────────
# GET /health → vérifie que l'API est en ligne
# Utile pour les outils de monitoring
@app.get("/health", tags=["Santé"])
def health_check():
    return {
        "status": "ok",
        "app": "BrandAI API",
        "version": "1.0.0",
        "env": settings.APP_ENV,
    }