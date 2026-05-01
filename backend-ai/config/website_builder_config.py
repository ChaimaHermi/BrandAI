"""
Configuration de l'agent Website Builder.

L'agent utilise openai/gpt-oss-120b via NVIDIA NIM avec rotation des clés
NVIDIA_API_KEY_1 … NVIDIA_API_KEY_4 (gérée par BaseAgent).
"""

from __future__ import annotations

import os


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline 3-tools : architecture → content → coder
# Modèle : openai/gpt-oss-120b (NVIDIA NIM) — fenêtre 128k input / 65k output.
# ─────────────────────────────────────────────────────────────────────────────

# Phase 2A — Architecture : structure JSON (sections, nav, animations).
# Sortie courte et focalisée → tokens limités.
ARCHITECTURE_TEMPERATURE: float = float(os.getenv("WEBSITE_ARCHITECTURE_TEMPERATURE", "0.5"))
ARCHITECTURE_MAX_TOKENS: int = int(os.getenv("WEBSITE_ARCHITECTURE_MAX_TOKENS", "2500"))

# Phase 2B — Content : remplit chaque section avec du texte réel + icônes Lucide.
# Sortie moyenne (texte structuré).
CONTENT_TEMPERATURE: float = float(os.getenv("WEBSITE_CONTENT_TEMPERATURE", "0.7"))
CONTENT_MAX_TOKENS: int = int(os.getenv("WEBSITE_CONTENT_MAX_TOKENS", "5000"))

# Aliases description = architecture + content combinés (pour compat orchestrateur).
DESCRIPTION_TEMPERATURE: float = float(os.getenv("WEBSITE_DESCRIPTION_TEMPERATURE", "0.7"))
DESCRIPTION_MAX_TOKENS: int = int(os.getenv("WEBSITE_DESCRIPTION_MAX_TOKENS", "4000"))

# Phase 3 — Coder : pure implémentation HTML/Tailwind à partir de architecture+content.
# Le LLM n'invente plus de contenu, il code seulement → temp basse.
GENERATION_TEMPERATURE: float = float(os.getenv("WEBSITE_GENERATION_TEMPERATURE", "0.3"))
GENERATION_MAX_TOKENS: int = int(os.getenv("WEBSITE_GENERATION_MAX_TOKENS", "24000"))

# Phase 4 — Révision : modification chirurgicale du HTML existant.
# Le HTML d'entrée peut faire 6k–10k tokens → besoin de marge en sortie.
REVISION_TEMPERATURE: float = float(os.getenv("WEBSITE_REVISION_TEMPERATURE", "0.3"))
REVISION_MAX_TOKENS: int = int(os.getenv("WEBSITE_REVISION_MAX_TOKENS", "32000"))

# Timeout par phase LLM Azure.
# 0 = timeout desactive (attente illimitee jusqu'a reponse finale du provider).
# L'utilisateur a demande de ne jamais couper la generation pour delai d'attente.
WEBSITE_DESCRIPTION_TIMEOUT_SECONDS: float = float(
    os.getenv("WEBSITE_DESCRIPTION_TIMEOUT_SECONDS", "0")
)
WEBSITE_GENERATION_TIMEOUT_SECONDS: float = float(
    os.getenv("WEBSITE_GENERATION_TIMEOUT_SECONDS", "0")
)
WEBSITE_REVISION_TIMEOUT_SECONDS: float = float(
    os.getenv("WEBSITE_REVISION_TIMEOUT_SECONDS", "0")
)

# 0 retry de notre côté : le SDK openai gère déjà ses propres retries (voir max_retries
# dans create_azure_openai_client). On évite le double-retry qui cause les blocages.
WEBSITE_LLM_MAX_RETRIES: int = int(os.getenv("WEBSITE_LLM_MAX_RETRIES", "0"))

# URL du backend FastAPI (idea + branding bundle).
BACKEND_API_BASE_URL: str = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")
BACKEND_API_TIMEOUT_SECONDS: float = float(os.getenv("BACKEND_API_TIMEOUT_SECONDS", "30"))
# Timeout max alloué à la normalisation du logo pendant la phase contexte.
# Si dépassé, on garde l'URL logo brute pour éviter de bloquer /website/context.
WEBSITE_CONTEXT_LOGO_NORMALIZE_TIMEOUT_SECONDS: float = float(
    os.getenv("WEBSITE_CONTEXT_LOGO_NORMALIZE_TIMEOUT_SECONDS", "8")
)

# Garde-fous de validation Phase 2.
REQUIRED_SECTIONS_MIN: int = 4  # min 4, max 6 imposé par le prompt
REQUIRED_ANIMATIONS_MIN: int = 1

# Garde-fous Phase 3 / 4 : un site doit contenir ces marqueurs élémentaires.
HTML_STRICT_VALIDATION: bool = os.getenv("WEBSITE_HTML_STRICT_VALIDATION", "0").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
HTML_MIN_LENGTH: int = int(os.getenv("WEBSITE_HTML_MIN_LENGTH", "1"))
_markers_raw = os.getenv("WEBSITE_HTML_REQUIRED_MARKERS", "<html,</html>").strip()
HTML_REQUIRED_MARKERS: tuple[str, ...] = tuple(
    marker.strip().lower() for marker in _markers_raw.split(",") if marker.strip()
)

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


# (Contact form relay removed: generated websites use mailto directly.)
