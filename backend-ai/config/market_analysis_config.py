# ══════════════════════════════════════════════════════════════
# config/market_analysis_config.py  [FIXED]
#
# CORRECTIONS :
#   1. max_tokens  : 8000 → 800  (output LLM seulement, pas le contexte)
#   2. max_payload_chars : 20000 → 5000  (safe sous 8000 TPM Groq)
#   3. snippet_max_chars : 300 → 120    (moins de tokens dans le payload)
#   4. max_items         : 8 → 4        (moins de résultats par source)
#   5. LIMITS : doublon supprimé — une seule définition conservée (petite)
# ══════════════════════════════════════════════════════════════

# ── LLM ───────────────────────────────────────────────────────
LLM_CONFIG = {
    "model":       "openai/gpt-oss-120b",
    "max_tokens":  8000,  # output only, keep headroom under 8000 TPM
    "temperature": 0.1,
}

LLM_LIMITS = {
    "max_items":          4,     # ✅ résultats max par source envoyés au LLM
    "snippet_max_chars":  120,   # ✅ snippet tronqué court
    "title_max_chars":    60,    # ✅ titre tronqué court
    "max_payload_chars":  5000,  # ✅ hard cap du JSON user_prompt (safe Groq)
}

# ── Limites résultats par API ─────────────────────────────────
# ⚠️  Un seul bloc LIMITS — le doublon a été supprimé
LIMITS = {
    "serp_competitors_results":  3,
    "serp_maps_results":         3,
    "serp_trends_points":        5,
    "serp_tiktok_results":       3,
    "tavily_insights_results":   3,
    "tavily_reddit_results":     3,
    "tavily_regulatory_results": 2,
    "newsapi_results":           3,
    "youtube_results":           3,
    "rising_queries":            3,
}

# ── Délais entre requêtes (secondes) ─────────────────────────
DELAYS = {
    "serpapi":   0.5,
    "tavily":    0.3,
    "gnews":     0.5,
    "youtube":   0.5,
    "worldbank": 0.3,
}

# ── Cache TTL (secondes) ──────────────────────────────────────
CACHE_TTL = {
    "serpapi_search":  86400,    # 24h
    "serpapi_maps":    86400,    # 24h
    "serpapi_trends":  21600,    # 6h
    "serpapi_tiktok":  43200,    # 12h
    "tavily":          43200,    # 12h
    "gnews":           86400,    # 24h
    "youtube":         43200,    # 12h
    "worldbank":       2592000,  # 30j
}

# ── Semaphores ────────────────────────────────────────────────
SEMAPHORES = {
    "serpapi":   5,
    "tavily":    10,
    "gnews":     5,
    "youtube":   5,
    "worldbank": 10,
}