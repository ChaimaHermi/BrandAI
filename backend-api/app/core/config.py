import os
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
)


class Settings(BaseSettings):
    # Base de données
    DATABASE_URL: str
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    # App
    APP_ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:5173"
    # Google OAuth — optionnel (None si pas configuré)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"
    FRONTEND_CALLBACK_URL: str = "http://localhost:5173/auth/callback"

    # Meta Graph — enrichissement profil connexion sociale (token page)
    META_GRAPH_API_VERSION: str = "v25.0"

    # Social ETL (backend-ai) — extraction + normalisation pour l’agent Optimizer
    # Dossier racine du repo ``backend-ai`` (sibling de ``backend-api`` si vide).
    BACKEND_AI_ROOT: str = ""
    SOCIAL_ETL_POST_LIMIT: int = 10
    SOCIAL_ETL_COMMENTS_LIMIT: int = 100
    APIFY_TOKEN: str = ""
    APIFY_LINKEDIN_ACTOR_ID: str = ""

    # Configuration Pydantic v2 / pydantic-settings
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # ignore GEMINI_*, GROQ_*, LLM_* dans .env
    )


settings = Settings()
