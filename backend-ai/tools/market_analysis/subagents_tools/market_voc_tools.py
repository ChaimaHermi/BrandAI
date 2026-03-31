# ══════════════════════════════════════════════════════════════
# tools/market_analysis/subagents_tools/market_voc_tools.py
# APIs : Tavily insights + Tavily Reddit + YouTube + GNews + WorldBank
# ══════════════════════════════════════════════════════════════

import asyncio, hashlib, logging, os, shelve, tempfile, time
from datetime import datetime, timedelta
from typing import Any
import httpx
import config.settings  # charge .env racine (GNEWS_API_KEY, TAVILY, YOUTUBE…)
from config.market_analysis_config import LIMITS, DELAYS, CACHE_TTL, SEMAPHORES

logger      = logging.getLogger("brandai.market_voc_tools")
_SEM_TAVILY = asyncio.Semaphore(SEMAPHORES["tavily"])
_SEM_NEWS   = asyncio.Semaphore(SEMAPHORES["gnews"])
_SEM_YT     = asyncio.Semaphore(SEMAPHORES["youtube"])
_SEM_WB     = asyncio.Semaphore(SEMAPHORES["worldbank"])
TIMEOUT     = httpx.Timeout(15.0, connect=5.0)
_CACHE_FILE = os.path.join(tempfile.gettempdir(), "ma_cache")

_WB_INDICATORS = {
    "population":     "SP.POP.TOTL",
    "gdp_per_capita": "NY.GDP.PCAP.CD",
    "internet_pct":   "IT.NET.USER.ZS",
    "mobile_per100":  "IT.CEL.SETS.P2",
    "urban_pct":      "SP.URB.TOTL.IN.ZS",
    "youth_pct":      "SP.POP.1564.TO.ZS",
}


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
            logger.error(f"[market_voc_tools] GET {url}: {e}")
            return {}

async def _post(url: str, payload: dict, sem: asyncio.Semaphore) -> dict:
    async with sem:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as c:
                r = await c.post(url, json=payload, headers={"Content-Type": "application/json"})
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.error(f"[market_voc_tools] POST {url}: {e}")
            return {}

def _sl(obj: Any, n: int) -> list:
    return obj[:n] if isinstance(obj, list) else []


# ══════════════════════════════════════════════════════════════
# TOOL 1 — Tavily insights
# ══════════════════════════════════════════════════════════════

async def fetch_tavily_insights(query: str) -> dict:
    k = _key("tavily_insights", query)
    if c := _cget(k): return c

    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return {"source": "tavily", "query": query, "results": []}

    data    = await _post("https://api.tavily.com/search", {
        "api_key": api_key, "query": query,
        "search_depth": "basic",
        "max_results": LIMITS["tavily_insights_results"],
        "include_answer": False,
    }, _SEM_TAVILY)

    results = _sl(data.get("results", []), LIMITS["tavily_insights_results"])
    result  = {
        "source":  "tavily",
        "query":   query,
        "results": [{"title": r.get("title",""), "snippet": r.get("content","")[:400]} for r in results],
    }
    _cset(k, result, CACHE_TTL["tavily"])
    logger.info(f"[market_voc_tools] Tavily insights: {len(result['results'])} résultats")
    return result


# ══════════════════════════════════════════════════════════════
# TOOL 2 — Reddit VOC via Tavily
# ══════════════════════════════════════════════════════════════

async def fetch_reddit_voc(query: str) -> dict:
    k = _key("reddit_voc", query)
    if c := _cget(k): return c

    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return {"source": "reddit_via_tavily", "query": query, "results": []}

    data    = await _post("https://api.tavily.com/search", {
        "api_key": api_key,
        "query":   f"site:reddit.com {query}",
        "search_depth": "basic",
        "max_results": LIMITS["tavily_reddit_results"],
        "include_answer": False,
    }, _SEM_TAVILY)

    results = _sl(data.get("results", []), LIMITS["tavily_reddit_results"])
    result  = {
        "source":  "reddit_via_tavily",
        "query":   query,
        "results": [{"title": r.get("title",""), "snippet": r.get("content","")[:500]} for r in results],
    }
    _cset(k, result, CACHE_TTL["tavily"])
    logger.info(f"[market_voc_tools] Reddit VOC: {len(result['results'])} posts")
    return result


# ══════════════════════════════════════════════════════════════
# TOOL 3 — YouTube VOC
# ══════════════════════════════════════════════════════════════

async def fetch_youtube_voc(query: str) -> dict:
    k = _key("youtube_voc", query)
    if c := _cget(k): return c

    api_key = os.getenv("YOUTUBE_API_KEY", "")
    if not api_key:
        return {"source": "youtube", "query": query, "videos": []}

    data  = await _get("https://www.googleapis.com/youtube/v3/search", {
        "part": "snippet", "q": query, "type": "video",
        "maxResults": LIMITS["youtube_results"],
        "order": "relevance", "key": api_key,
    }, _SEM_YT, DELAYS["youtube"])

    items  = _sl(data.get("items", []), LIMITS["youtube_results"])
    result = {
        "source": "youtube",
        "query":  query,
        "videos": [
            {
                "title":       item.get("snippet", {}).get("title", ""),
                "channel":     item.get("snippet", {}).get("channelTitle", ""),
                "description": (item.get("snippet", {}).get("description") or "")[:200],
            }
            for item in items
        ],
    }
    _cset(k, result, CACHE_TTL["youtube"])
    logger.info(f"[market_voc_tools] YouTube: {len(result['videos'])} vidéos")
    return result


# ══════════════════════════════════════════════════════════════
# TOOL 4 — GNews API (remplace NewsAPI — gratuit 100 req/jour)
# Inscription : https://gnews.io → clé dans .env : GNEWS_API_KEY
# ══════════════════════════════════════════════════════════════

async def fetch_newsapi(query: str, language: str = "fr") -> dict:
    """
    Utilise GNews API — gratuit 100 req/jour, pas de restriction endpoint.
    Variable d'env : GNEWS_API_KEY
    Doc : https://gnews.io/docs/v4
    """
    k = _key("gnews", query, language)
    if c := _cget(k): return c

    api_key = (
        os.getenv("GNEWS_API_KEY") or os.getenv("GNEWSAPI_KEY") or ""
    ).strip()
    if not api_key:
        logger.warning("[market_voc_tools] GNEWS_API_KEY ou GNEWSAPI_KEY manquant — ajoutez-le dans .env")
        return {"source": "gnews", "query": query, "articles": []}

    # Simplifier la query — garder seulement les 3 premiers mots
    simple_query = " ".join(query.split()[:3])

    data = await _get("https://gnews.io/api/v4/search", {
        "q":      simple_query,
        "lang":   language or "en",
        "max":    min(LIMITS["newsapi_results"], 10),
        "apikey": api_key,
    }, _SEM_NEWS, DELAYS["gnews"])

    articles = _sl(data.get("articles", []), LIMITS["newsapi_results"])

    result = {
        "source":   "gnews",
        "query":    query,
        "articles": [
            {
                "title":        a.get("title", ""),
                "source":       a.get("source", {}).get("name", ""),
                "published_at": a.get("publishedAt", "")[:10],
                "description":  (a.get("description") or "")[:300],
            }
            for a in articles
            if a.get("title")
        ],
    }
    _cset(k, result, CACHE_TTL["gnews"])
    logger.info(f"[market_voc_tools] GNews: {len(result['articles'])} articles")
    return result


# ══════════════════════════════════════════════════════════════
# TOOL 5 — World Bank (sans clé)
# ══════════════════════════════════════════════════════════════

async def fetch_worldbank(country_code: str) -> dict:
    if not country_code or len(country_code) != 2:
        return {"source": "worldbank", "country_code": country_code, "indicators": {}}

    k = _key("worldbank", country_code)
    if c := _cget(k): return c

    async def _one(name: str, indicator: str):
        url  = f"https://api.worldbank.org/v2/country/{country_code.upper()}/indicator/{indicator}"
        data = await _get(url, {"format": "json", "mrv": 1, "per_page": 1}, _SEM_WB, DELAYS["worldbank"])
        try:
            val = data[1][0]["value"] if data and len(data) > 1 and data[1] else None
            return name, round(val, 2) if val is not None else None
        except Exception:
            return name, None

    done       = await asyncio.gather(*[_one(n, i) for n, i in _WB_INDICATORS.items()])
    indicators = {n: v for n, v in done}

    result = {"source": "worldbank", "country_code": country_code.upper(), "indicators": indicators}
    _cset(k, result, CACHE_TTL["worldbank"])
    logger.info(f"[market_voc_tools] WorldBank: {country_code} — {sum(1 for v in indicators.values() if v)} indicateurs")
    return result