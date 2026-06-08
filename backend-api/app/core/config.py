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

    # Social ETL — extraction + normalisation + KPIs
    SOCIAL_ETL_POST_LIMIT: int = 10
    SOCIAL_ETL_TOP_POSTS_DISPLAY: int = 5
    SOCIAL_ETL_COMMENTS_LIMIT: int = 100
    APIFY_TOKEN: str = ""
    APIFY_LINKEDIN_ACTOR_ID: str = ""

    # ── OAuth Meta (Facebook + Instagram) ──────────────────────
    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""
    FACEBOOK_GRAPH_API_VERSION: str = "v22.0"
    META_OAUTH_REDIRECT_URI: str = "http://localhost:8000/api/social/meta/callback"
    SOCIAL_OAUTH_FRONTEND_ORIGIN: str = "http://localhost:5173"

    # ── OAuth LinkedIn ──────────────────────────────────────────
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_PRIMARY_CLIENT_SECRET: str = ""
    LINKEDIN_REDIRECT_URI: str = "http://localhost:8766/callback"
    LINKEDIN_SCOPE: str = "openid profile email w_member_social r_profile_basicinfo"
    BRANDAI_API_BASE_URL: str = "http://localhost:8000"

    # Configuration Pydantic v2 / pydantic-settings
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # ignore GEMINI_*, GROQ_*, LLM_* dans .env
    )


settings = Settings()
