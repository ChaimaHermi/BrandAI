# ══════════════════════════════════════════════════════════════
# config/branding_config.py
# ══════════════════════════════════════════════════════════════

LLM_CONFIG = {
    "model": "openai/gpt-oss-120b",
    "temperature": 0.7,   # créativité
    "max_tokens": 800,    # output court
}

LIMITS = {
    "max_name_options": 5,
    "min_name_options": 3,
}