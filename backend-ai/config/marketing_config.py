# ─────────────────────────────────────────
# MARKETING AGENT LLM CONFIG — Azure GPT-4
# ─────────────────────────────────────────

from config.llm_defaults import DEFAULT_AZURE_DEPLOYMENT

MARKETING_LLM_CONFIG = {
    "provider": "azure",
    "model": DEFAULT_AZURE_DEPLOYMENT,
    "temperature": 0.2,
    "max_tokens": 3500,
    "response_format": "json",
}