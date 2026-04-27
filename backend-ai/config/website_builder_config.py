"""
Configuration de l'agent Website Builder.

L'agent utilise Azure OpenAI (déploiement `gpt-4.1` par défaut, voir `.env`)
pour la génération créative (description, HTML, révision).
"""

from __future__ import annotations

import os

from config.settings import AZURE_OPENAI_DEPLOYMENT


# Déploiement Azure utilisé par l'agent. Par défaut on suit AZURE_OPENAI_DEPLOYMENT
# (gpt-4.1 dans le .env actuel) ; possibilité de surcharger via une variable dédiée.
WEBSITE_BUILDER_AZURE_DEPLOYMENT: str = (
    os.getenv("WEBSITE_BUILDER_AZURE_DEPLOYMENT") or AZURE_OPENAI_DEPLOYMENT
)

# Description (phase 2) : on laisse de la marge pour un concept détaillé,
# clair et structuré (sections + animations + tone + résumé).
DESCRIPTION_TEMPERATURE: float = float(os.getenv("WEBSITE_DESCRIPTION_TEMPERATURE", "0.6"))
DESCRIPTION_MAX_TOKENS: int = int(os.getenv("WEBSITE_DESCRIPTION_MAX_TOKENS", "3200"))

# Génération HTML/Tailwind = grosse sortie (site complet) :
# l'utilisateur souhaite exploiter le maximum output dispo.
GENERATION_TEMPERATURE: float = float(os.getenv("WEBSITE_GENERATION_TEMPERATURE", "0.4"))
GENERATION_MAX_TOKENS: int = int(os.getenv("WEBSITE_GENERATION_MAX_TOKENS", "32000"))

# Révision = renvoie le HTML complet modifié :
# on garde la même capacité max pour éviter la troncature sur gros HTML.
REVISION_TEMPERATURE: float = float(os.getenv("WEBSITE_REVISION_TEMPERATURE", "0.3"))
REVISION_MAX_TOKENS: int = int(os.getenv("WEBSITE_REVISION_MAX_TOKENS", "32000"))

# Timeout hard par phase LLM Azure.
# La génération HTML complète peut être nettement plus longue qu'une description.
WEBSITE_DESCRIPTION_TIMEOUT_SECONDS: float = float(
    os.getenv("WEBSITE_DESCRIPTION_TIMEOUT_SECONDS", "90")
)
WEBSITE_GENERATION_TIMEOUT_SECONDS: float = float(
    os.getenv("WEBSITE_GENERATION_TIMEOUT_SECONDS", "300")
)
WEBSITE_REVISION_TIMEOUT_SECONDS: float = float(
    os.getenv("WEBSITE_REVISION_TIMEOUT_SECONDS", "180")
)

# Nombre de retries réseau/timeout côté LLM (en plus de l'appel initial).
WEBSITE_LLM_MAX_RETRIES: int = int(os.getenv("WEBSITE_LLM_MAX_RETRIES", "1"))

# URL du backend FastAPI (idea + branding bundle).
BACKEND_API_BASE_URL: str = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")
BACKEND_API_TIMEOUT_SECONDS: float = float(os.getenv("BACKEND_API_TIMEOUT_SECONDS", "30"))

# Garde-fous de validation Phase 2.
REQUIRED_SECTIONS_MIN: int = 5
REQUIRED_ANIMATIONS_MIN: int = 4

# Garde-fous Phase 3 / 4 : un site doit contenir ces marqueurs élémentaires.
HTML_MIN_LENGTH: int = 1500
HTML_REQUIRED_MARKERS: tuple[str, ...] = ("<html", "<body", "</body", "</html")

# Polices par défaut quand le brand kit n'en fournit pas (fonts non générées par l'agent palette).
DEFAULT_TITLE_FONT: str = "Playfair Display"
DEFAULT_BODY_FONT: str = "Inter"


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5 — Vercel deployment
# ─────────────────────────────────────────────────────────────────────────────
# Token personnel Vercel — créé sur https://vercel.com/account/tokens
# Lu en priorité dans VERCEL_API_KEY (terminologie projet) puis VERCEL_TOKEN (alias).
VERCEL_API_KEY: str = (
    os.getenv("VERCEL_API_KEY") or os.getenv("VERCEL_TOKEN") or ""
).strip()

# ID d'équipe Vercel (optionnel, requis si le compte est en mode team).
VERCEL_TEAM_ID: str = (os.getenv("VERCEL_TEAM_ID") or "").strip()

VERCEL_API_BASE: str = os.getenv("VERCEL_API_BASE", "https://api.vercel.com").rstrip("/")

# Préfixe du nom de projet sur Vercel : nom final = "{prefix}{idea_id}" (slugifié).
VERCEL_PROJECT_NAME_PREFIX: str = os.getenv("VERCEL_PROJECT_NAME_PREFIX", "brandai-")

# Polling : on ré-interroge Vercel toutes les N secondes jusqu'à READY / ERROR.
VERCEL_POLL_INTERVAL_SECONDS: float = float(os.getenv("VERCEL_POLL_INTERVAL_SECONDS", "2.5"))
VERCEL_POLL_TIMEOUT_SECONDS: float = float(os.getenv("VERCEL_POLL_TIMEOUT_SECONDS", "180"))

# Timeout HTTP par requête Vercel (création + chaque poll).
VERCEL_HTTP_TIMEOUT_SECONDS: float = float(os.getenv("VERCEL_HTTP_TIMEOUT_SECONDS", "30"))


def vercel_is_configured() -> bool:
    """Garde-fou utilisé par les routes pour renvoyer 503 si la clé manque."""
    return bool(VERCEL_API_KEY)
