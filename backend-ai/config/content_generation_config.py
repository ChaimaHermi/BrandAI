# ══════════════════════════════════════════════════════════════
# Content generation — config (LLM, HF image, Pollinations, Cloudinary)
# ══════════════════════════════════════════════════════════════

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Même racine que `config/settings.py` : ce module peut être importé avant settings.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

def content_http_timeout() -> httpx.Timeout:
    """
    Timeout HTTP pour tout le pipeline contenu / weekly plan.
    Par défaut : aucune limite (attendre la fin des appels NVIDIA, Cloudinary, API idée).
    Pour un plafond optionnel : CONTENT_HTTP_TIMEOUT_S=600
    """
    raw = (os.getenv("CONTENT_HTTP_TIMEOUT_S") or "").strip()
    if raw in ("0", "none", "off", ""):
        return httpx.Timeout(None)
    try:
        return httpx.Timeout(float(raw))
    except ValueError:
        return httpx.Timeout(None)


def _int_env(name: str, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


# Contexte gpt-oss-120b ≈ 128k tokens ; la sortie **max** côté API NVIDIA est 65 536 tokens.
# On aligne max_tokens sur cette plafond pour éviter une coupure de génération en milieu de phrase.
_CONTENT_MAX_OUT = min(_int_env("CONTENT_LLM_MAX_OUTPUT_TOKENS", 65_536), 65_536)

# ── LLM texte (caption, prompts image) — NVIDIA NIM openai/gpt-oss-120b uniquement
CONTENT_LLM_CONFIG = {
    "model": "openai/gpt-oss-120b",
    "temperature": 0.35,
    "max_tokens": _CONTENT_MAX_OUT,
    "reasoning": "medium",
}

def _env_flag(name: str, default: str = "1") -> bool:
    v = (os.getenv(name) or default).strip().lower()
    return v not in ("0", "false", "no", "off")

# ── Cloudinary — upload image générée → URL publique
# Préférence : CONTENT_CLOUDINARY_* ; sinon les noms usuels CLOUDINARY_* (déjà présents sur beaucoup de projets)
def _cloudinary_env(primary: str, fallback: str) -> str:
    return (os.getenv(primary) or os.getenv(fallback) or "").strip()


CONTENT_CLOUDINARY_CLOUD_NAME = _cloudinary_env(
    "CONTENT_CLOUDINARY_CLOUD_NAME",
    "CLOUDINARY_CLOUD_NAME",
)
CONTENT_CLOUDINARY_API_KEY = _cloudinary_env(
    "CONTENT_CLOUDINARY_API_KEY",
    "CLOUDINARY_API_KEY",
)
CONTENT_CLOUDINARY_API_SECRET = _cloudinary_env(
    "CONTENT_CLOUDINARY_API_SECRET",
    "CLOUDINARY_API_SECRET",
)
_upload_folder = (
    os.getenv("CONTENT_CLOUDINARY_UPLOAD_FOLDER")
    or os.getenv("CLOUDINARY_UPLOAD_FOLDER")
    or ""
).strip()
CONTENT_CLOUDINARY_UPLOAD_FOLDER = _upload_folder or "brandai/content"

# ── Terminal : Thought / Action / Observation — désactiver : CONTENT_AGENT_VERBOSE_TERMINAL=0
CONTENT_AGENT_VERBOSE_TERMINAL = _env_flag("CONTENT_AGENT_VERBOSE_TERMINAL", "1")
