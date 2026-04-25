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

