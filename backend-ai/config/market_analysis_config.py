# ══════════════════════════════════════════════════════════════
# config/market_analysis_config.py
# ══════════════════════════════════════════════════════════════


# ── LLM GLOBAL ────────────────────────────────────────────────
LLM_CONFIG = {
    "model": "openai/gpt-oss-120b",
    "max_tokens": 8000,
    "temperature": 0.1,
}


# ── MARKET SIZING LLM (spécifique) ───────────────────────────
MARKET_SIZING_LLM_CONFIG = {
    "model": LLM_CONFIG["model"],
    "temperature": 0.1,
    "max_tokens": 65_536,  # max NVIDIA gpt-oss-120b
}


# ── GLOBAL MARKET ANALYSIS CONFIG ─────────────────────────────
MARKET_ANALYSIS_CONFIG = {

    # ─────────────────────
    # CONTEXT LIMITS (CRITICAL)
    # ─────────────────────
    "context": {
        "max_chars": 10000,
        "max_items": 15,
    },

    # ─────────────────────
    # API LIMITS
    # ─────────────────────
    "api": {
        "tavily": {
            "max_results": 5
        },
        "serp": {
            "max_results": 5
        },
        "scrape": {
            "enabled": True,
            "max_pages": 5,
            "max_chars_per_page": 3000
        }
    },

    # ─────────────────────
    # AGENT-SPECIFIC LIMITS
    # ─────────────────────
    "agents": {
        "market_sizing": {
            "max_keywords": 5
        },
        "competitor": {
            "max_results": 10,
            "max_scraped": 5
        },
        "voc": {
            "max_reviews": 20
        },
        "trends": {
            "max_trends": 10
        }
    }
}

# LLM_LIMITS = {
#     "max_items":          4,     # ✅ résultats max par source envoyés au LLM
#     "snippet_max_chars":  120,   # ✅ snippet tronqué court
#     "title_max_chars":    60,    # ✅ titre tronqué court
#     "max_payload_chars":  5000,  # ✅ hard cap du JSON user_prompt (safe Groq)
# }

# # ── Limites résultats par API ─────────────────────────────────
# # ⚠️  Un seul bloc LIMITS — le doublon a été supprimé
# LIMITS = {
#     "market_sizing_max_keywords": 5,
#     "serp_competitors_results":  3,
#     "serp_maps_results":         3,
#     "serp_trends_points":        5,
#     "serp_tiktok_results":       3,
#     "tavily_insights_results":   3,
#     "tavily_reddit_results":     3,
#     "tavily_regulatory_results": 2,
#     "newsapi_results":           3,
#     "youtube_results":           3,
#     "rising_queries":            3,
# }

# # ── Délais entre requêtes (secondes) ─────────────────────────
# DELAYS = {
#     "serpapi":   0.5,
#     "tavily":    0.3,
#     "gnews":     0.5,
#     "youtube":   0.5,
#     "worldbank": 0.3,
# }

# # ── Cache TTL (secondes) ──────────────────────────────────────
# CACHE_TTL = {
#     "serpapi_search":  86400,    # 24h
#     "serpapi_maps":    86400,    # 24h
#     "serpapi_trends":  21600,    # 6h
#     "serpapi_tiktok":  43200,    # 12h
#     "tavily":          43200,    # 12h
#     "gnews":           86400,    # 24h
#     "youtube":         43200,    # 12h
#     "worldbank":       2592000,  # 30j
# }

# # ── Semaphores ────────────────────────────────────────────────
# SEMAPHORES = {
#     "serpapi":   5,
#     "tavily":    10,
#     "gnews":     5,
#     "youtube":   5,
#     "worldbank": 10,
# }