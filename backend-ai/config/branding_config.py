# ══════════════════════════════════════════════════════════════
# config/branding_config.py
# ══════════════════════════════════════════════════════════════

import os

LLM_CONFIG = {
    "provider": "azure",
    "model": "gpt-4o",
    "temperature": 0.65,
    "max_tokens": 4000,
}

# NameAgent
NAME_TARGET_COUNT = 3
NAME_AGENT_RECURSION_LIMIT = 55
NAME_AGENT_VERBOSE_REACT = True
NAME_SHORT_TERM_MEMORY_DIR = "data/memory/short_term"
NAME_SHORT_TERM_SQLITE_PATH = "data/memory/short_term/naming_short_term.db"
NAME_EXISTS_MEMORY_MAX = 20

# SloganAgent
SLOGAN_TARGET_COUNT = 3
SLOGAN_AGENT_RECURSION_LIMIT = 45
SLOGAN_AGENT_VERBOSE_REACT = True

# PaletteAgent
PALETTE_TARGET_COUNT = 3
PALETTE_AGENT_RECURSION_LIMIT = 40
PALETTE_AGENT_VERBOSE_REACT = True

# LogoAgent — prompt image via NVIDIA NIM openai/gpt-oss-120b (clés NVIDIA_API_KEY_*)
LOGO_LLM_CONFIG = {
    "provider": "nvidia",
    "model": "openai/gpt-oss-120b",
    "temperature": 0.4,
    "max_tokens": 4096,
}
LOGO_AGENT_RECURSION_LIMIT = 10
LOGO_AGENT_VERBOSE_REACT = True
LOGO_IMAGE_PROVIDER = "nvidia"
LOGO_HF_IMAGE_MODEL = "flux.2-klein-4b"

def _env_flag(name: str, default: str = "1") -> bool:
    v = (os.getenv(name) or default).strip().lower()
    return v not in ("0", "false", "no", "off")

# Vérification originalité via SerpApi Google Lens + Cloudinary (100 req/mois gratuit)
LOGO_ORIGINALITY_CHECK_ENABLED = _env_flag("LOGO_ORIGINALITY_CHECK_ENABLED", "1")
LOGO_ORIGINALITY_MAX_RETRIES = int((os.getenv("LOGO_ORIGINALITY_MAX_RETRIES") or "2").strip())
LOGO_ORIGINALITY_MAX_SIMILAR = int((os.getenv("LOGO_ORIGINALITY_MAX_SIMILAR") or "2").strip())
