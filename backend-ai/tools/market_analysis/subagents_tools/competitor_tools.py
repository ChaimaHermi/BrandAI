# ══════════════════════════════════════════════════════════════
# tools/market_analysis/subagents_tools/competitor_tools.py
# APIs : SerpAPI Search + SerpAPI Maps + Tavily
# Play Store supprimé — trop fragile
# ══════════════════════════════════════════════════════════════

import asyncio, hashlib, logging, os, shelve, tempfile, time
from typing import Any
import httpx
from config.market_analysis_config import LIMITS, DELAYS, CACHE_TTL, SEMAPHORES

logger     = logging.getLogger("brandai.competitor_tools")
_SEM_SERP  = asyncio.Semaphore(SEMAPHORES["serpapi"])
_SEM_TAV   = asyncio.Semaphore(SEMAPHORES["tavily"])
TIMEOUT    = httpx.Timeout(15.0, connect=5.0)
_SERP_BASE = "https://serpapi.com/search"
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
            logger.error(f"[competitor_tools] GET {url}: {e}")
            return {}

async def _post(url: str, payload: dict, sem: asyncio.Semaphore) -> dict:
    async with sem:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as c:
                r = await c.post(url, json=payload, headers={"Content-Type": "application/json"})
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.error(f"[competitor_tools] POST {url}: {e}")
            return {}

def _sl(obj: Any, n: int) -> list:
    return obj[:n] if isinstance(obj, list) else []


# ══════════════════════════════════════════════════════════════
# TOOL 1 — Google Search via SerpAPI
# ══════════════════════════════════════════════════════════════

async def fetch_serp_competitors(query: str, country_code: str = "TN") -> dict:
    """
    Identifie les concurrents web.
    Retourne les 5 premiers résultats organiques — pas de filtrage complexe.
    """
    k = _key("serp_competitors", query, country_code)
    if c := _cget(k): return c

    api_key = os.getenv("SERPAPI_KEY", "")
    if not api_key:
        return {"source": "serpapi_search", "query": query, "results": []}

    data    = await _get(_SERP_BASE, {
        "engine": "google", "q": query, "api_key": api_key,
        "gl": country_code.lower(), "hl": "fr",
        "num": LIMITS["serp_competitors_results"],
    }, _SEM_SERP, DELAYS["serpapi"])

    organic = _sl(data.get("organic_results", []), LIMITS["serp_competitors_results"])
    result  = {
        "source":  "serpapi_search",
        "query":   query,
        "country": country_code.upper(),
        "results": [
            {
                "title":   r.get("title", ""),
                "url":     r.get("link", ""),
                "snippet": r.get("snippet", "")[:300],
            }
            for r in organic
        ],
    }
    _cset(k, result, CACHE_TTL["serpapi_search"])
    logger.info(f"[competitor_tools] Search: {len(result['results'])} résultats")
    return result


# ══════════════════════════════════════════════════════════════
# TOOL 2 — Google Maps via SerpAPI
# ══════════════════════════════════════════════════════════════

async def fetch_serp_maps(query: str, country_code: str = "TN") -> dict:
    """
    Acteurs locaux avec nom, type et avis.
    Retourne les 5 premiers — pas de filtrage complexe.
    """
    k = _key("serp_maps", query, country_code)
    if c := _cget(k): return c

    api_key = os.getenv("SERPAPI_KEY", "")
    if not api_key:
        return {"source": "serpapi_maps", "query": query, "results": []}

    data   = await _get(_SERP_BASE, {
        "engine": "google_maps", "q": query, "api_key": api_key,
        "gl": country_code.lower(), "hl": "fr", "type": "search",
    }, _SEM_SERP, DELAYS["serpapi"])

    places = _sl(data.get("local_results", []), LIMITS["serp_maps_results"])
    result = {
        "source":  "serpapi_maps",
        "query":   query,
        "country": country_code.upper(),
        "results": [
            {
                "name":    p.get("title", ""),
                "rating":  p.get("rating"),        # peut être None — pas obligatoire
                "reviews": p.get("reviews"),        # peut être None
                "address": p.get("address", ""),
                "type":    p.get("type", ""),
            }
            for p in places
        ],
    }
    _cset(k, result, CACHE_TTL["serpapi_maps"])
    logger.info(f"[competitor_tools] Maps: {len(result['results'])} lieux")
    return result


# ══════════════════════════════════════════════════════════════
# TOOL 3 — Tavily competitor insights
# ══════════════════════════════════════════════════════════════

async def fetch_tavily_competitor_insights(query: str) -> dict:
    """
    Faiblesses, forces et positionnement des concurrents via Tavily.
    """
    k = _key("tavily_competitor", query)
    if c := _cget(k): return c

    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return {"source": "tavily_competitor", "query": query, "results": []}

    data    = await _post("https://api.tavily.com/search", {
        "api_key": api_key, "query": query,
        "search_depth": "basic",
        "max_results": LIMITS["tavily_insights_results"],
        "include_answer": False,
    }, _SEM_TAV)

    results = _sl(data.get("results", []), LIMITS["tavily_insights_results"])
    result  = {
        "source":  "tavily_competitor",
        "query":   query,
        "results": [{"title": r.get("title",""), "snippet": r.get("content","")[:400]} for r in results],
    }
    _cset(k, result, CACHE_TTL["tavily"])
    logger.info(f"[competitor_tools] Tavily competitor: {len(result['results'])} résultats")
    return result