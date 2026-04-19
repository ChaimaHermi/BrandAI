# ══════════════════════════════════════════════════════════════
# config/branding_config.py
# ══════════════════════════════════════════════════════════════

import os

LLM_CONFIG = {
    # provider: "azure" → AzureChatOpenAI (GPT-4o via Azure)
    #           "groq"  → ChatGroq (openai/gpt-oss-120b via Groq)
    "provider": "azure",
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 1200,
}

# NameAgent (ReAct): nombre de noms "libres" Brandfetch à livrer
NAME_TARGET_COUNT = 5
# Budget de pas LangGraph (plus élevé si NAME_TARGET_COUNT augmente)
NAME_AGENT_RECURSION_LIMIT = 55
# Afficher dans le terminal le déroulé type ReAct (Thought / Action / Observation)
NAME_AGENT_VERBOSE_REACT = True

# Short-term memory for already existing names (Brandfetch = exists)
# Dossier mémoire courte (JSON legacy + base SQLite).
NAME_SHORT_TERM_MEMORY_DIR = "data/memory/short_term"
# Stockage SQLite (même contenu JSON qu’avant : {"idea_id", "exists_names"}).
NAME_SHORT_TERM_SQLITE_PATH = "data/memory/short_term/naming_short_term.db"
NAME_EXISTS_MEMORY_MAX = 20

# SloganAgent : nombre de slogans à proposer
SLOGAN_TARGET_COUNT = 5
SLOGAN_AGENT_RECURSION_LIMIT = 45
SLOGAN_AGENT_VERBOSE_REACT = True

# PaletteAgent : toujours exactement 3 palettes (produit + validation stricte)
PALETTE_TARGET_COUNT = 3
PALETTE_AGENT_RECURSION_LIMIT = 40
PALETTE_AGENT_VERBOSE_REACT = True

# LogoAgent : LLM pour rédiger le prompt image (Azure recommandé, ex. gpt-4.1 via déploiement dédié)
LOGO_LLM_CONFIG = {
    "provider": "azure",
    "temperature": 0.4,
    "max_tokens": 900,
}
LOGO_AGENT_RECURSION_LIMIT = 35
LOGO_AGENT_VERBOSE_REACT = True
# none = pas de génération d’image ; sinon Hugging Face Inference (Replicate) + Qwen Image
LOGO_IMAGE_PROVIDER = "huggingface"
# Modèle Hub pour text_to_image. Surcharge : env LOGO_HF_IMAGE_MODEL
LOGO_HF_IMAGE_MODEL = "Qwen/Qwen-Image"

# Si Hugging Face échoue ou s’il n’y a pas de clé HF, fallback Pollinations (GET image.pollinations.ai).
# Désactiver le fallback : LOGO_POLLINATIONS_FALLBACK=0
def _env_flag(name: str, default: str = "1") -> bool:
    v = (os.getenv(name) or default).strip().lower()
    return v not in ("0", "false", "no", "off")


LOGO_POLLINATIONS_FALLBACK = _env_flag("LOGO_POLLINATIONS_FALLBACK", "1")
# Slug Pollinations par défaut = Z-Image Turbo (catalogue). Surcharge : LOGO_POLLINATIONS_MODEL dans .env (ex. Z-Image Turbo ou zimage)
LOGO_POLLINATIONS_MODEL_DEFAULT = "zimage"
# Libellé / valeur .env pour logo_concepts.image_model (source Pollinations). Si vide → nom lisible pour le défaut zimage.
_pm_env = (os.getenv("LOGO_POLLINATIONS_MODEL") or "").strip()
LOGO_POLLINATIONS_IMAGE_MODEL = _pm_env if _pm_env else "Z-Image Turbo"
