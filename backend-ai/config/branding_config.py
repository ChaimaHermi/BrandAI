# ══════════════════════════════════════════════════════════════
# config/branding_config.py
# ══════════════════════════════════════════════════════════════

LLM_CONFIG = {
    "model": "openai/gpt-oss-120b",
    "temperature": 0.3,   # ↓ plus stable pour JSON
    "max_tokens": 8000,   # ↑ réduit les truncations
}
