# ══════════════════════════════════════════════════════════════
# config/market_analysis_config.py
# ══════════════════════════════════════════════════════════════

# ── LLM ───────────────────────────────────────────────────────
LLM_CONFIG = {
    "model":       "openai/gpt-oss-120b",
    "max_tokens":  8000,
    "temperature": 0.1,
}

# ── Limites résultats par API ─────────────────────────────────
LIMITS = {
    "serp_competitors_results":  8,
    "serp_maps_results":         8,
    "serp_trends_points":        12,
    "serp_tiktok_results":       6,
    "tavily_insights_results":   6,
    "tavily_reddit_results":     5,
    "tavily_regulatory_results": 4,
    "newsapi_results":           8,
    "youtube_results":           6,
    "rising_queries":            5,
}

# ── Délais entre requêtes (secondes) ─────────────────────────
DELAYS = {
    "serpapi":   0.5,
    "tavily":    0.3,
    "gnews":      0.5,
    "youtube":   0.5,
    "worldbank": 0.3,
}

# ── Cache TTL (secondes) ──────────────────────────────────────
CACHE_TTL = {
    "serpapi_search":  86400,   # 24h
    "serpapi_maps":    86400,   # 24h
    "serpapi_trends":  21600,   # 6h
    "serpapi_tiktok":  43200,   # 12h
    "tavily":          43200,   # 12h
    "gnews":            86400,   # 24h
    "youtube":         43200,   # 12h
    "worldbank":       2592000, # 30j
}

# ── Semaphores ────────────────────────────────────────────────
SEMAPHORES = {
    "serpapi":   5,
    "tavily":    10,
    "gnews":      5,
    "youtube":   5,
    "worldbank": 10,
}