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

# ── Agent timeouts (seconds) ───────────────────────────────────────────────────
TIMEOUTS = {
    "llm":         30,
    "web_search":  15,
    "scraping":    20,
    "world_bank":  15,
    "news_api":    10,
}
 
# ── Rate limits (requests per minute) ─────────────────────────────────────────
RATE_LIMITS = {
    "serpapi":   100,   # free: 100/month total — use sparingly
    "serper":    2500,  # free: 2500/month
    "tavily":    1000,  # free tier
    "newsapi":   100,   # free: 100/day
    "newsdata":  200,   # free: 200/day
    "gnews":     100,   # free: 100/day
    "youtube":   10000, # free: 10,000 units/day
    "scrape_do": 1000,  # depends on plan
}
 
# ── World Bank indicators used by agent_market ─────────────────────────────────
WORLD_BANK_INDICATORS = {
    "gdp_usd":               "NY.GDP.MKTP.CD",
    "gdp_growth_pct":        "NY.GDP.MKTP.KD.ZG",
    "inflation_pct":         "FP.CPI.TOTL.ZG",
    "internet_penetration":  "IT.NET.USER.ZS",
    "population":            "SP.POP.TOTL",
    "urban_population_pct":  "SP.URB.TOTL.IN.ZS",
}
 
# ── Agent output schema version ────────────────────────────────────────────────
OUTPUT_SCHEMA_VERSION = "1.0"