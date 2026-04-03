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
NAME_SHORT_TERM_MEMORY_DIR = "data/memory/short_term"
NAME_EXISTS_MEMORY_MAX = 20
