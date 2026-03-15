 
# ==============================================================
#  app/core/database.py
#  RÔLE : Gérer la connexion à PostgreSQL
#
#  3 choses importantes dans ce fichier :
#    1. engine      → la connexion physique à PostgreSQL
#    2. SessionLocal → fabrique de sessions (1 session = 1 requête HTTP)
#    3. Base        → classe mère de tous tes modèles SQLAlchemy
#

#  COMMENT ÇA MARCHE :
#    - Chaque requête HTTP ouvre une session BDD
#    - La session est utilisée dans la route
#    - La session est fermée proprement à la fin (même si erreur)
#    → C'est le rôle de get_db()
# ==============================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings


# ── 1. Engine : connexion physique à PostgreSQL ───────────────
# pool_pre_ping=True : teste la connexion avant chaque requête
# Utile si PostgreSQL redémarre → évite l'erreur "connection closed"
#
# echo=True en dev → affiche les requêtes SQL dans le terminal
# Pratique pour déboguer, à désactiver en production
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=(settings.APP_ENV == "development"),
)


# ── 2. SessionLocal : fabrique de sessions ────────────────────
# autocommit=False → tu dois appeler db.commit() manuellement
#                    Donne le contrôle sur quand sauvegarder
# autoflush=False  → SQLAlchemy n'envoie pas les changements
#                    à PostgreSQL avant que tu le demandes
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ── 3. Base : classe mère des modèles ─────────────────────────
# Tous tes modèles héritent de Base :
#   class User(Base): ...
#   class Project(Base): ...
# SQLAlchemy utilise Base.metadata pour connaître toutes les tables
class Base(DeclarativeBase):
    pass


# ── 4. get_db() : dépendance FastAPI ─────────────────────────
# C'est un "generator" Python (yield au lieu de return)
# FastAPI l'utilise avec Depends(get_db) dans les routes
#
# FLUX D'EXÉCUTION :
#   1. Requête HTTP arrive
#   2. FastAPI appelle get_db() → ouvre une session
#   3. La session est injectée dans la route (paramètre db)
#   4. La route fait ses opérations BDD
#   5. FastAPI exécute le bloc finally → ferme la session

def get_db():
    db = SessionLocal()
    try:
        yield db        # ← donne la session à la route
    finally:
        db.close()      # ← toujours fermé, même si erreur