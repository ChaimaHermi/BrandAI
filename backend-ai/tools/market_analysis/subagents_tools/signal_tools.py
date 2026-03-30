# ══════════════════════════════════════════════════════════════
# tools/market_analysis/subagents_tools/signal_tools.py
# Robust signal extraction: multi-query, normalization, enrichment
# ══════════════════════════════════════════════════════════════

import asyncio
import hashlib
import logging
import os
import shelve
import tempfile
import time
from typing import Any

import httpx

from config.market_analysis_config import CACHE_TTL, DELAYS, LIMITS, SEMAPHORES

logger = logging.getLogger("brandai.signal_tools")
_SEM_SERP = asyncio.Semaphore(SEMAPHORES["serpapi"])
_SEM_TAVILY = asyncio.Semaphore(SEMAPHORES["tavily"])
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


def _clean_text(text: str, max_len: int = 500) -> str:
    s = (text or "").replace("\n", " ").replace("\r", " ").strip()
    s = " ".join(s.split())
    return s[:max_len]


def _norm(text: str) -> str:
    return _clean_text(text, 500).lower().strip()


def _dedup_str(items: list[str], keep_case: bool = True, max_items: int | None = None) -> list[str]:
    out = []
    seen = set()
    for x in items:
        val = _clean_text(str(x), 250)
        key = _norm(val)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(val if keep_case else key)
        if max_items and len(out) >= max_items:
            break
    return out


def _dedup_dict(items: list[dict], keys: tuple[str, ...], max_items: int | None = None) -> list[dict]:
    out = []
    seen = set()
    for it in items:
        sig = tuple(_norm(str(it.get(k, ""))) for k in keys)
        if not any(sig) or sig in seen:
            continue
        seen.add(sig)
        out.append(it)
        if max_items and len(out) >= max_items:
            break
    return out


def _extract_peak_period(timeline: list[dict]) -> str | None:
    best_date = None
    best_value = -1
    for p in timeline:
        v = p.get("value", 0) or 0
        if v > best_value:
            best_value = v
            best_date = p.get("date")
    return best_date


async def fetch_google_trends(keyword: str, country_code: str = "TN") -> dict:
    k = _key("trends_v3", keyword, country_code)
    if c := _cget(k):
        return c

    api_key = os.getenv("SERPAPI_KEY", "").strip()
    if not api_key:
        return {"source": "google_trends", "keyword": keyword, "country": country_code.upper(), "timeline": [], "rising_queries": [], "rising_topics": [], "top_queries": [], "peak_period": None, "source_count": 0, "_debug": {"error": "missing key"}}

    base_params = {
        "engine": "google_trends",
        "q": keyword,
        "api_key": api_key,
        "geo": country_code.upper(),
        "date": "today 12-m",
    }

    ts, rq, rt = await asyncio.gather(
        _get(_SERP_BASE, {**base_params, "data_type": "TIMESERIES"}, _SEM_SERP, DELAYS["serpapi"]),
        _get(_SERP_BASE, {**base_params, "data_type": "RELATED_QUERIES"}, _SEM_SERP, DELAYS["serpapi"]),
        _get(_SERP_BASE, {**base_params, "data_type": "RELATED_TOPICS"}, _SEM_SERP, DELAYS["serpapi"]),
    )

    timeline_raw = _sl(ts.get("interest_over_time", {}).get("timeline_data", []), LIMITS["serp_trends_points"])
    timeline = []
    for row in timeline_raw:
        vals = row.get("values", [{}])
        value = vals[0].get("extracted_value", 0) if vals and isinstance(vals[0], dict) else 0
        timeline.append({"date": row.get("date", ""), "value": value})

    rq_data = rq.get("related_queries", {})
    rising_q = [q.get("query", "") for q in _sl(rq_data.get("rising", []), LIMITS.get("rising_queries", 8)) if q.get("query")]
    top_q = [q.get("query", "") for q in _sl(rq_data.get("top", []), 8) if q.get("query")]

    rt_data = rt.get("related_topics", {})
    rising_t = [
        t.get("topic", {}).get("title", "") or t.get("title", "")
        for t in _sl(rt_data.get("rising", []), 8)
        if t.get("topic", {}).get("title") or t.get("title")
    ]

    result = {
        "source": "google_trends",
        "keyword": keyword,
        "country": country_code.upper(),
        "timeline": timeline,
        "rising_queries": _dedup_str(rising_q + rising_t, max_items=12),
        "rising_topics": _dedup_str(rising_t, max_items=8),
        "top_queries": _dedup_str(top_q, max_items=8),
        "peak_period": _extract_peak_period(timeline),
        "source_count": 3,
        "_debug": {
            "timeseries_points": len(timeline),
            "related_queries_count": len(rising_q),
            "related_topics_count": len(rising_t),
        },
    }
    _cset(k, result, CACHE_TTL["serpapi_trends"])
    logger.info(f"[signal_tools] Trends '{keyword}' ({country_code}): {len(result['rising_queries'])} rising")
    return result


async def fetch_google_trends_multi(keywords: list[str], country_code: str = "TN") -> dict:
    clean = _dedup_str([str(k) for k in (keywords or []) if str(k).strip()], max_items=12)
    cache_key = _key("trends_multi_v1", country_code, *clean)
    if c := _cget(cache_key):
        return c
    if not clean:
        return {"source": "google_trends_multi", "country": country_code.upper(), "keywords": [], "timeline": [], "rising_queries": [], "rising_topics": [], "top_queries": [], "peak_period": None, "source_count": 0, "_debug": {"batches": 0}}

    batches = await asyncio.gather(*[fetch_google_trends(k, country_code) for k in clean])
    timeline = []
    rising = []
    topics = []
    tops = []
    for b in batches:
        timeline.extend(b.get("timeline", []))
        rising.extend(b.get("rising_queries", []))
        topics.extend(b.get("rising_topics", []))
        tops.extend(b.get("top_queries", []))
    timeline = _dedup_dict(timeline, ("date", "value"), max_items=200)
    result = {
        "source": "google_trends_multi",
        "country": country_code.upper(),
        "keywords": clean,
        "timeline": timeline,
        "rising_queries": _dedup_str(rising, max_items=20),
        "rising_topics": _dedup_str(topics, max_items=20),
        "top_queries": _dedup_str(tops, max_items=20),
        "peak_period": _extract_peak_period(timeline),
        "source_count": len(batches),
        "_debug": {"batches": len(batches)},
    }
    _cset(cache_key, result, CACHE_TTL["serpapi_trends"])
    return result


async def fetch_google_autocomplete(keyword: str, country_code: str = "TN") -> dict:
    k = _key("autocomplete_v2", keyword, country_code)
    if c := _cget(k):
        return c

    api_key = os.getenv("SERPAPI_KEY", "").strip()
    if not api_key:
        return {"source": "google_autocomplete", "keyword": keyword, "country": country_code.upper(), "suggestions": [], "source_count": 0}

    data = await _get(
        _SERP_BASE,
        {
            "engine": "google_autocomplete",
            "q": keyword,
            "api_key": api_key,
            "gl": country_code.lower(),
            "hl": "en",
        },
        _SEM_SERP,
        DELAYS["serpapi"],
    )

    suggestions_raw = data.get("suggestions", [])
    cleaned = []
    key_norm = _norm(keyword)
    for s in _sl(suggestions_raw, 20):
        v = _clean_text(s.get("value", ""), 180)
        v_norm = _norm(v)
        if not v_norm or v_norm == key_norm:
            continue
        # retire variantes inutiles trop proches (prefix/suffix simples)
        if v_norm.startswith(key_norm) and len(v_norm.split()) <= len(key_norm.split()) + 1:
            continue
        cleaned.append(v)

    cleaned = _dedup_str(cleaned, max_items=10)
    result = {
        "source": "google_autocomplete",
        "keyword": keyword,
        "country": country_code.upper(),
        "suggestions": cleaned,
        "source_count": 1,
    }
    _cset(k, result, CACHE_TTL.get("serpapi_autocomplete", 3600))
    logger.info(f"[signal_tools] Autocomplete '{keyword}': {len(cleaned)} suggestions")
    return result


async def fetch_tavily_trends(query: str, country_code: str = "TN") -> dict:
    k = _key("tavily_trends_v3", query, country_code)
    if c := _cget(k):
        return c

    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        return {"source": "tavily_trends", "query": query, "country": country_code.upper(), "results": [], "signals": [], "snippet_keywords": [], "source_count": 0}

    trend_query = f"{query} market trend growth demand"
    data = await _post(
        _TAVILY_URL,
        {
            "api_key": api_key,
            "query": trend_query,
            "search_depth": "advanced",
            "max_results": max(5, LIMITS.get("tavily_insights_results", 6)),
            "include_answer": False,
            "include_raw_content": False,
        },
        _SEM_TAVILY,
    )

    raw_results = _sl(data.get("results", []), 10)
    enriched = []
    for r in raw_results:
        title = _clean_text(r.get("title", ""), 220)
        url = _clean_text(r.get("url", ""), 300)
        snippet = _clean_text(r.get("content", ""), 600)
        enriched.append({"title": title, "url": url, "snippet": snippet})
    enriched = _dedup_dict(enriched, ("url", "title", "snippet"), max_items=10)

    signals = _dedup_str([x["title"] for x in enriched if x.get("title")], max_items=10)
    snippet_keywords = []
    for x in enriched:
        sn = x.get("snippet", "")
        s_norm = _norm(sn)
        if any(w in s_norm for w in ("growing", "trending", "popular", "increase", "demand", "croissance", "tendance", "hausse")):
            snippet_keywords.append(sn[:140])
    snippet_keywords = _dedup_str(snippet_keywords, max_items=10)

    result = {
        "source": "tavily_trends",
        "query": query,
        "country": country_code.upper(),
        "results": enriched,
        "signals": signals,
        "snippet_keywords": snippet_keywords,
        "source_count": len(enriched),
    }
    _cset(k, result, CACHE_TTL.get("tavily", 3600))
    logger.info(f"[signal_tools] Tavily trends '{query}': {len(enriched)} results")
    return result


async def fetch_tavily_trends_multi(queries: list[str], country_code: str = "TN") -> dict:
    clean = _dedup_str([str(q) for q in (queries or []) if str(q).strip()], max_items=12)
    cache_key = _key("tavily_trends_multi_v1", country_code, *clean)
    if c := _cget(cache_key):
        return c
    if not clean:
        return {"source": "tavily_trends_multi", "country": country_code.upper(), "queries": [], "results": [], "signals": [], "snippet_keywords": [], "source_count": 0}

    batches = await asyncio.gather(*[fetch_tavily_trends(q, country_code) for q in clean])
    results = []
    signals = []
    snippets = []
    for b in batches:
        results.extend(b.get("results", []))
        signals.extend(b.get("signals", []))
        snippets.extend(b.get("snippet_keywords", []))

    results = _dedup_dict(results, ("url", "title", "snippet"), max_items=30)
    result = {
        "source": "tavily_trends_multi",
        "country": country_code.upper(),
        "queries": clean,
        "results": results,
        "signals": _dedup_str(signals, max_items=20),
        "snippet_keywords": _dedup_str(snippets, max_items=20),
        "source_count": len(results),
        "_debug": {"batches": len(batches)},
    }
    _cset(cache_key, result, CACHE_TTL.get("tavily", 3600))
    return result


async def fetch_tiktok_signals(query: str) -> dict:
    logger.debug(f"[signal_tools] TikTok disabled for: {query}")
    return {
        "source": "tiktok",
        "query": query,
        "results": [],
        "hashtags": [],
        "hashtags_disponibles": False,
        "disponible": False,
        "source_count": 0,
    }


async def fetch_regulatory(query: str, country_code: str = "") -> dict:
    k = _key("regulatory_v2", query, country_code)
    if c := _cget(k):
        return c

    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        return {"source": "regulatory_via_tavily", "query": query, "results": [], "source_count": 0}

    reg_query = f"regulation legal compliance license {query}"
    if country_code:
        reg_query += f" {country_code}"

    data = await _post(
        _TAVILY_URL,
        {
            "api_key": api_key,
            "query": reg_query,
            "search_depth": "advanced",
            "max_results": LIMITS["tavily_regulatory_results"],
            "include_answer": False,
        },
        _SEM_TAVILY,
    )

    rows = _sl(data.get("results", []), LIMITS["tavily_regulatory_results"])
    results = []
    for r in rows:
        results.append(
            {
                "title": _clean_text(r.get("title", ""), 220),
                "url": _clean_text(r.get("url", ""), 300),
                "snippet": _clean_text(r.get("content", ""), 400),
            }
        )
    results = _dedup_dict(results, ("url", "title", "snippet"))

    result = {
        "source": "regulatory_via_tavily",
        "query": query,
        "country": country_code.upper() if country_code else "",
        "results": results,
        "source_count": len(results),
    }
    _cset(k, result, CACHE_TTL["tavily"])
    logger.info(f"[signal_tools] Regulatory: {len(results)} results")
    return result