import os
from pydantic_settings import BaseSettings

# Chemin absolu vers le .env à la racine du projet
# config.py est dans : backend-api/app/core/config.py
# .env est dans      : Brand AI/.env
# On remonte 3 fois  : core/ → app/ → backend-api/ → Brand AI/
ENV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
)


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    APP_ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ENV_PATH
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()