# ══════════════════════════════════════════════════════════════
# tools/market_analysis/subagents_tools/signal_tools.py
# APIs : SerpAPI Trends + SerpAPI TikTok + Tavily regulatory
# ══════════════════════════════════════════════════════════════

import asyncio, hashlib, logging, os, shelve, tempfile, time
from typing import Any
import httpx
from config.market_analysis_config import LIMITS, DELAYS, CACHE_TTL, SEMAPHORES

logger      = logging.getLogger("brandai.signal_tools")
_SEM_SERP   = asyncio.Semaphore(SEMAPHORES["serpapi"])
_SEM_TAVILY = asyncio.Semaphore(SEMAPHORES["tavily"])
TIMEOUT     = httpx.Timeout(15.0, connect=5.0)
_SERP_BASE  = "https://serpapi.com/search"
_CACHE_FILE = os.path.join(tempfile.gettempdir(), "ma_cache")


# ── Cache ─────────────────────────────────────────────────────

def _key(*args) -> str:
    return hashlib.md5(":".join(str(a) for a in args).encode()).hexdigest()

def _cget(key: str) -> Any | None:
    try:
        with shelve.open(_CACHE_FILE) as db:
            e = db.get(key)
            if e and time.time() < e["exp"]:
                return e["data"]
    except Exception:
        pass
    return None

def _cset(key: str, data: Any, ttl: int) -> None:
    try:
        with shelve.open(_CACHE_FILE) as db:
            db[key] = {"data": data, "exp": time.time() + ttl}
    except Exception as e:
        logger.warning(f"[cache] {e}")


# ── HTTP ──────────────────────────────────────────────────────

async def _get(url: str, params: dict, sem: asyncio.Semaphore, delay: float = 0) -> dict:
    async with sem:
        if delay:
            await asyncio.sleep(delay)
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as c:
                r = await c.get(url, params=params)
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.error(f"[signal_tools] GET {url}: {e}")
            return {}

async def _post(url: str, payload: dict, sem: asyncio.Semaphore) -> dict:
    async with sem:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as c:
                r = await c.post(url, json=payload, headers={"Content-Type": "application/json"})
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.error(f"[signal_tools] POST {url}: {e}")
            return {}

def _sl(obj: Any, n: int) -> list:
    return obj[:n] if isinstance(obj, list) else []


# ══════════════════════════════════════════════════════════════
# TOOL 1 — Google Trends via SerpAPI
# ══════════════════════════════════════════════════════════════

async def fetch_google_trends(keyword: str, country_code: str = "TN") -> dict:
    k = _key("trends", keyword, country_code)
    if c := _cget(k): return c

    api_key = os.getenv("SERPAPI_KEY", "")
    if not api_key:
        return {"source": "google_trends", "keyword": keyword, "error": "missing key"}

    data = await _get(_SERP_BASE, {
        "engine": "google_trends", "q": keyword,
        "api_key": api_key, "geo": country_code.upper(),
        "data_type": "TIMESERIES", "date": "today 12-m",
    }, _SEM_SERP, DELAYS["serpapi"])

    timeline_raw = _sl(data.get("interest_over_time", {}).get("timeline_data", []),
                       LIMITS["serp_trends_points"])

    timeline = []
    for p in timeline_raw:
        v = p.get("values", [{}])
        if v and isinstance(v[0], dict):
            timeline.append({"date": p.get("date", ""), "value": v[0].get("extracted_value", 0)})

    related = data.get("related_queries", {})
    rising  = _sl(related.get("rising", []), LIMITS["rising_queries"])
    top_q   = _sl(related.get("top", []), 5)

    result = {
        "source":         "google_trends",
        "keyword":        keyword,
        "country":        country_code.upper(),
        "timeline":       timeline,
        "rising_queries": [q.get("query", "") for q in rising],
        "top_queries":    [q.get("query", "") for q in top_q],
    }
    _cset(k, result, CACHE_TTL["serpapi_trends"])
    logger.info(f"[signal_tools] Trends: {keyword} — {len(timeline)} pts")
    return result


# ══════════════════════════════════════════════════════════════
# TOOL 2 — TikTok — SUPPRIMÉ (SerpAPI TikTok = plan payant)
# Retourne toujours un résultat vide propre
# ══════════════════════════════════════════════════════════════

async def fetch_tiktok_signals(query: str) -> dict:
    """TikTok via SerpAPI nécessite un plan payant — désactivé."""
    logger.debug(f"[signal_tools] TikTok désactivé — retourne vide pour: {query}")
    return {
        "source":               "tiktok",
        "query":                query,
        "results":              [],
        "hashtags":             [],
        "hashtags_disponibles": False,
        "disponible":           False,
    }


# ══════════════════════════════════════════════════════════════
# TOOL 3 — Regulatory via Tavily
# ══════════════════════════════════════════════════════════════

async def fetch_regulatory(query: str, country_code: str = "") -> dict:
    k = _key("regulatory", query, country_code)
    if c := _cget(k): return c

    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return {"source": "regulatory", "query": query, "results": []}

    reg_query = f"réglementation légale conformité licence {query}"
    if country_code:
        reg_query += f" {country_code}"

    data    = await _post("https://api.tavily.com/search", {
        "api_key": api_key, "query": reg_query,
        "search_depth": "basic",
        "max_results": LIMITS["tavily_regulatory_results"],
        "include_answer": False,
    }, _SEM_TAVILY)

    results = _sl(data.get("results", []), LIMITS["tavily_regulatory_results"])
    result  = {
        "source":  "regulatory_via_tavily",
        "query":   query,
        "results": [{"title": r.get("title",""), "snippet": r.get("content","")[:300]} for r in results],
    }
    _cset(k, result, CACHE_TTL["tavily"])
    logger.info(f"[signal_tools] Regulatory: {len(result['results'])} résultats")
    return result