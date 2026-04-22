# ══════════════════════════════════════════════════════════════
# Publication Meta (Facebook / Instagram) + LinkedIn — variables .env
# ══════════════════════════════════════════════════════════════

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Base publique du service backend-ai (OAuth callbacks). Pas de slash final.
# Ex. http://localhost:8001 — doit être la même origine/port que uvicorn pour éviter ERR_CONNECTION_REFUSED.
_BRANDAI_AI_BASE = (os.getenv("BRANDAI_AI_BASE_URL") or "http://localhost:8001").rstrip("/")

GRAPH_API_VERSION = (os.getenv("META_GRAPH_API_VERSION") or "v25.0").strip()

# Meta (Facebook + Instagram pro via Page)
FACEBOOK_APP_ID = (os.getenv("FACEBOOK_APP_ID") or "").strip()
FACEBOOK_APP_SECRET = (os.getenv("FACEBOOK_APP_SECRET") or "").strip()
# Callback doit être enregistré dans l’app Meta (ex. http://localhost:8001/api/ai/social/meta/callback)
_META_RAW = (os.getenv("META_OAUTH_REDIRECT_URI") or "").strip()
if not _META_RAW:
    _META_RAW = (
        os.getenv("FACEBOOK_REDIRECT_URI") or os.getenv("INSTAGRAM_REDIRECT_URI") or ""
    ).strip()
if not _META_RAW:
    META_OAUTH_REDIRECT_URI = f"{_BRANDAI_AI_BASE}/api/ai/social/meta/callback"
else:
    _legacy_meta = any(f":{p}" in _META_RAW for p in ("8765", "8766", "8767"))
    if _legacy_meta:
        import logging

        logging.getLogger("brandai.social_config").warning(
            "Redirect Meta obsolète (%s) — utilisation de %s/api/ai/social/meta/callback",
            _META_RAW,
            _BRANDAI_AI_BASE,
        )
        META_OAUTH_REDIRECT_URI = f"{_BRANDAI_AI_BASE}/api/ai/social/meta/callback"
    else:
        META_OAUTH_REDIRECT_URI = _META_RAW

# Publication sans OAuth interactif (optionnel)
FACEBOOK_PAGE_ID = (os.getenv("FACEBOOK_PAGE_ID") or "").strip()
FACEBOOK_PAGE_ACCESS_TOKEN = (os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN") or "").strip()

# LinkedIn
LINKEDIN_CLIENT_ID = (os.getenv("LINKEDIN_CLIENT_ID") or "").strip()
LINKEDIN_CLIENT_SECRET = (
    os.getenv("LINKEDIN_CLIENT_SECRET")
    or os.getenv("LINKEDIN_PRIMARY_CLIENT_SECRET")
    or ""
).strip()
# Ex. http://localhost:8766/callback (script local) — backend-ai démarre alors un proxy vers /api/ai/social/linkedin/callback.
_LINKEDIN_REDIRECT_RAW = (os.getenv("LINKEDIN_REDIRECT_URI") or "").strip()
LINKEDIN_REDIRECT_URI = _LINKEDIN_REDIRECT_RAW or f"{_BRANDAI_AI_BASE}/api/ai/social/linkedin/callback"

# Alias pour le démarrage du proxy OAuth (main.py)
BRANDAI_AI_BASE = _BRANDAI_AI_BASE
LINKEDIN_SCOPE = (
    os.getenv("LINKEDIN_SCOPE") or "openid profile email w_member_social r_profile_basicinfo"
).strip()

# Front (postMessage origin)
FRONTEND_ORIGIN = (
    os.getenv("SOCIAL_OAUTH_FRONTEND_ORIGIN")
    or os.getenv("FRONTEND_URL")
    or "http://localhost:5173"
).strip()

META_DEFAULT_SCOPES = [
    "pages_show_list",
    "pages_read_engagement",
    "pages_manage_posts",
    "instagram_basic",
    "instagram_content_publish",
]
