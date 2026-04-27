# ─────────────────────────────────────────
# MARKETING AGENT LLM CONFIG
# ─────────────────────────────────────────

MARKETING_LLM_CONFIG = {
    "model": "openai/gpt-oss-120b",

    # marketing = raisonnement + créativité contrôlée
    "temperature": 0.2,

    # output structuré mais long (JSON complet)
    "max_tokens": 3500,

    # optionnel (actuellement non branché dans MarketingAgent/BaseAgent)
    "reasoning": "medium",

    # optionnel (documentaire: le prompt force déjà du JSON strict)
    "response_format": "json"
}