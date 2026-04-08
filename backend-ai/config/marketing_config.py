# ─────────────────────────────────────────
# MARKETING AGENT LLM CONFIG
# ─────────────────────────────────────────

MARKETING_LLM_CONFIG = {
    "model": "openai/gpt-oss-120b",

    # marketing = raisonnement + créativité contrôlée
    "temperature": 0.2,

    # output structuré mais long (JSON complet)
    "max_tokens": 3500,

    # optionnel (si tu utilises reasoning param)
    "reasoning": "medium",

    # sécurité JSON
    "response_format": "json"
}