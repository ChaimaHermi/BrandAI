# ══════════════════════════════════════════════════════════════
# config/branding_config.py
# ══════════════════════════════════════════════════════════════

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

# PaletteAgent : nombre de palettes de couleurs complètes à proposer
PALETTE_TARGET_COUNT = 3

# LogoAgent : LLM pour rédiger le prompt image (Azure recommandé, ex. gpt-4.1 via déploiement dédié)
LOGO_LLM_CONFIG = {
    "provider": "azure",
    "temperature": 0.4,
    "max_tokens": 900,
}
# openrouter_flux (FLUX via OpenRouter, défaut) | pollinations | none
LOGO_IMAGE_PROVIDER = "openrouter_flux"
LOGO_IMAGE_SIZE = 512
# Modèle image OpenRouter (ex. black-forest-labs/flux.2-pro). Surcharge : env LOGO_OPENROUTER_MODEL
LOGO_OPENROUTER_MODEL = "black-forest-labs/flux.2-pro"
