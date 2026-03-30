# ══════════════════════════════════════════════════════════════
# tools/market_analysis/subagents_tools/competitor_tools.py
# APIs : SerpAPI Search + SerpAPI Maps + Tavily (advanced + multi-query)
# ══════════════════════════════════════════════════════════════

import asyncio
import hashlib
import logging
import os
import shelve
import tempfile
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from config.market_analysis_config import CACHE_TTL, DELAYS, LIMITS, SEMAPHORES

logger = logging.getLogger("brandai.competitor_tools")
_SEM_SERP = asyncio.Semaphore(SEMAPHORES["serpapi"])
_SEM_TAV = asyncio.Semaphore(SEMAPHORES["tavily"])
TIMEOUT = httpx.Timeout(15.0, connect=5.0)
_SERP_BASE = "https://serpapi.com/search"
_TAVILY_URL = "https://api.tavily.com/search"
_CACHE_FILE = os.path.join(tempfile.gettempdir(), "ma_cache")


def _key(*args) -> str:
    return hashlib.md5(":".join(str(a) for a in args).encode()).hexdigest()


def _cget(key: str) -> Any | None:
    try:
        with shelve.open(_CACHE_FILE) as db:
            entry = db.get(key)
            if entry and time.time() < entry["exp"]:
                return entry["data"]
    except Exception:
        pass
    return None


def _cset(key: str, data: Any, ttl: int) -> None:
    try:
        with shelve.open(_CACHE_FILE) as db:
            db[key] = {"data": data, "exp": time.time() + ttl}
    except Exception as e:
        logger.warning(f"[cache] {e}")


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


def _clean_text(text: str, max_len: int = 500) -> str:
    t = (text or "").replace("\n", " ").replace("\r", " ").strip()
    t = " ".join(t.split())
    return t[:max_len]


def _domain_from_url(url: str) -> str:
    if not url:
        return ""
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc[4:] if netloc.startswith("www.") else netloc
    except Exception:
        return ""


def _dedup_dicts(items: list[dict], keys: tuple[str, ...]) -> list[dict]:
    seen = set()
    out = []
    for it in items:
        sig = tuple((it.get(k) or "").strip().lower() for k in keys)
        if not any(sig):
            continue
        if sig in seen:
            continue
        seen.add(sig)
        out.append(it)
    return out


async def fetch_serp_competitors(query: str, country_code: str = "TN") -> dict:
    k = _key("serp_competitors", query, country_code)
    if c := _cget(k):
        return c

    api_key = os.getenv("SERPAPI_KEY", "").strip()
    if not api_key:
        return {"source": "serpapi_search", "query": query, "country": country_code.upper(), "results": []}

    data = await _get(
        _SERP_BASE,
        {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": country_code.lower(),
            "hl": "en",
            "num": LIMITS["serp_competitors_results"],
        },
        _SEM_SERP,
        DELAYS["serpapi"],
    )
    organic = _sl(data.get("organic_results", []), LIMITS["serp_competitors_results"])
    enriched = []
    for i, r in enumerate(organic, start=1):
        url = r.get("link", "") or ""
        enriched.append(
            {
                "position": r.get("position") or i,
                "title": _clean_text(r.get("title", ""), 180),
                "url": url,
                "domain": _domain_from_url(url),
                "snippet": _clean_text(r.get("snippet", ""), 500),
                "source": "serpapi_search",
            }
        )
    enriched = _dedup_dicts(enriched, ("url", "title"))
    result = {
        "source": "serpapi_search",
        "query": query,
        "country": country_code.upper(),
        "results": enriched,
    }
    _cset(k, result, CACHE_TTL["serpapi_search"])
    logger.info(f"[competitor_tools] Search: {len(enriched)} results")
    return result


async def fetch_serp_maps(query: str, country_code: str = "TN") -> dict:
    k = _key("serp_maps", query, country_code)
    if c := _cget(k):
        return c

    api_key = os.getenv("SERPAPI_KEY", "").strip()
    if not api_key:
        return {"source": "serpapi_maps", "query": query, "country": country_code.upper(), "results": []}

    data = await _get(
        _SERP_BASE,
        {
            "engine": "google_maps",
            "q": query,
            "api_key": api_key,
            "gl": country_code.lower(),
            "hl": "en",
            "type": "search",
        },
        _SEM_SERP,
        DELAYS["serpapi"],
    )
    places = _sl(data.get("local_results", []), LIMITS["serp_maps_results"])
    normalized = []
    for p in places:
        website = p.get("website", "") or ""
        normalized.append(
            {
                "name": _clean_text(p.get("title", ""), 140),
                "rating": p.get("rating"),
                "reviews": p.get("reviews"),
                "address": _clean_text(p.get("address", ""), 220),
                "type": _clean_text(p.get("type", ""), 100),
                "website": website,
                "domain": _domain_from_url(website),
                "source": "serpapi_maps",
            }
        )
    normalized = _dedup_dicts(normalized, ("name", "address"))
    result = {
        "source": "serpapi_maps",
        "query": query,
        "country": country_code.upper(),
        "results": normalized,
    }
    _cset(k, result, CACHE_TTL["serpapi_maps"])
    logger.info(f"[competitor_tools] Maps: {len(normalized)} results")
    return result


async def fetch_tavily_competitor_insights(query: str) -> dict:
    k = _key("tavily_competitor", query)
    if c := _cget(k):
        return c

    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        return {"source": "tavily_competitor", "query": query, "results": []}

    data = await _post(
        _TAVILY_URL,
        {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": LIMITS["tavily_insights_results"],
            "include_answer": False,
            "include_raw_content": False,
        },
        _SEM_TAV,
    )
    rows = _sl(data.get("results", []), LIMITS["tavily_insights_results"])
    normalized = []
    for r in rows:
        url = r.get("url", "") or ""
        normalized.append(
            {
                "title": _clean_text(r.get("title", ""), 220),
                "url": url,
                "domain": _domain_from_url(url),
                "source": _clean_text(r.get("source", ""), 120) or _domain_from_url(url),
                "snippet": _clean_text(r.get("content", ""), 1000),
            }
        )
    normalized = _dedup_dicts(normalized, ("url", "title", "snippet"))
    result = {"source": "tavily_competitor", "query": query, "results": normalized}
    _cset(k, result, CACHE_TTL["tavily"])
    logger.info(f"[competitor_tools] Tavily: {len(normalized)} results")
    return result


async def fetch_tavily_multi(queries: list[str]) -> dict:
    clean_queries = [q.strip() for q in (queries or []) if isinstance(q, str) and q.strip()]
    cache_key = _key("tavily_multi", *clean_queries)
    if c := _cget(cache_key):
        return c

    if not clean_queries:
        return {"source": "tavily_multi", "queries": [], "results": []}

    batches = await asyncio.gather(*[fetch_tavily_competitor_insights(q) for q in clean_queries])
    merged = []
    for b in batches:
        merged.extend(b.get("results", []))
    merged = _dedup_dicts(merged, ("url", "title", "snippet"))

    result = {
        "source": "tavily_multi",
        "queries": clean_queries,
        "results": merged,
        "batches": [{"query": b.get("query", ""), "count": len(b.get("results", []))} for b in batches],
    }
    _cset(cache_key, result, CACHE_TTL["tavily"])
    logger.info(f"[competitor_tools] Tavily multi: {len(clean_queries)} queries, {len(merged)} merged results")
    return result