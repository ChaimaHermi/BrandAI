# ══════════════════════════════════════════════════════════════
# market_analysis_tools.py
# Tous les outils API pour le MarketAnalysisAgent
#
# APIs utilisées (free tiers) :
#   - Tavily           → insights + Reddit via site:reddit.com
#   - SerpAPI          → Google Search + Maps + Google Trends + TikTok
#   - NewsAPI          → actualités sectorielles
#   - YouTube Data v3  → signaux VOC vidéo
#   - WorldBank API    → macro (PIB, population, internet) — no key
#   - Regulatory       → réglementation via Tavily ciblé
#
# Rate limiting :
#   - SerpAPI         : asyncio.Semaphore(5)  — 100 req/h free
#   - Tavily          : asyncio.Semaphore(10) — 1000 req/mois free
#   - NewsAPI         : asyncio.Semaphore(5)  — 100 req/j free
#   - YouTube         : asyncio.Semaphore(5)  — 10 000 units/j free
#   - WorldBank       : asyncio.Semaphore(10) — illimité
# ══════════════════════════════════════════════════════════════

import asyncio
import logging
import os
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ── Semaphores rate limiting ───────────────────────────────────
_SEM_SERP   = asyncio.Semaphore(5)
_SEM_TAVILY = asyncio.Semaphore(10)
_SEM_NEWS   = asyncio.Semaphore(5)
_SEM_YT     = asyncio.Semaphore(5)
_SEM_WB     = asyncio.Semaphore(10)

TIMEOUT = httpx.Timeout(15.0, connect=5.0)


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _get_env(key: str) -> str:
    val = os.getenv(key, "")
    if not val:
        logger.warning(f"[tools] env var {key} manquant")
    return val


def _safe_list(obj: Any, max_items: int = 10) -> list:
    """Garantit une liste, tronquée à max_items."""
    if not isinstance(obj, list):
        return []
    return obj[:max_items]


async def _get(url: str, params: dict, sem: asyncio.Semaphore) -> dict:
    """GET async avec semaphore, timeout et gestion d'erreur."""
    async with sem:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                return r.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"[tools] HTTP {e.response.status_code} → {url}")
            return {}
        except Exception as e:
            logger.error(f"[tools] erreur → {url} : {e}")
            return {}


async def _post(url: str, payload: dict, headers: dict, sem: asyncio.Semaphore) -> dict:
    """POST async avec semaphore, timeout et gestion d'erreur."""
    async with sem:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                r = await client.post(url, json=payload, headers=headers)
                r.raise_for_status()
                return r.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"[tools] HTTP {e.response.status_code} → {url}")
            return {}
        except Exception as e:
            logger.error(f"[tools] erreur → {url} : {e}")
            return {}


# ══════════════════════════════════════════════════════════════
# TOOL 1 — TAVILY : insights + Reddit VOC
# ══════════════════════════════════════════════════════════════

async def fetch_tavily_insights(query: str, max_results: int = 5) -> dict:
    """
    Recherche web enrichie via Tavily.
    Retourne titres, URLs et extraits nettoyés.
    """
    key = _get_env("TAVILY_API_KEY")
    if not key:
        return {"source": "tavily", "results": [], "error": "API key missing"}

    payload = {
        "api_key": key,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": False,
    }
    data = await _post(
        "https://api.tavily.com/search",
        payload,
        {"Content-Type": "application/json"},
        _SEM_TAVILY,
    )
    results = _safe_list(data.get("results", []), max_results)
    return {
        "source": "tavily",
        "query": query,
        "results": [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", "")[:400],
                "score": r.get("score", 0),
            }
            for r in results
        ],
    }


async def fetch_reddit_voc(query: str, max_results: int = 5) -> dict:
    """
    VOC Reddit via Tavily avec site:reddit.com.
    Évite les 403 de l'API Reddit directe.
    """
    reddit_query = f"site:reddit.com {query}"
    raw = await fetch_tavily_insights(reddit_query, max_results)
    raw["source"] = "reddit_via_tavily"
    raw["query"] = query
    return raw


async def fetch_regulatory(query: str, country_code: str = "") -> dict:
    """
    Informations réglementaires via Tavily ciblé.
    Cherche licences, conformité, barrières légales.
    """
    reg_query = f"réglementation légale conformité {query}"
    if country_code:
        reg_query += f" {country_code}"
    raw = await fetch_tavily_insights(reg_query, max_results=4)
    raw["source"] = "regulatory_via_tavily"
    raw["query"] = query
    return raw


# ══════════════════════════════════════════════════════════════
# TOOL 2 — SERPAPI : Search + Maps + Trends + TikTok
# ══════════════════════════════════════════════════════════════

_SERP_BASE = "https://serpapi.com/search"


async def fetch_serp_competitors(query: str, country_code: str = "fr") -> dict:
    """
    Google Search via SerpAPI pour identifier les concurrents.
    country_code : 'fr' | 'tn' | 'ma' | 'dz' etc.
    """
    key = _get_env("SERPAPI_KEY")
    if not key:
        return {"source": "serpapi_google_search", "results": [], "error": "API key missing"}

    params = {
        "engine": "google",
        "q": query,
        "api_key": key,
        "gl": country_code.lower(),
        "hl": "fr",
        "num": 10,
    }
    data = await _get(_SERP_BASE, params, _SEM_SERP)
    organic = _safe_list(data.get("organic_results", []), 8)
    return {
        "source": "serpapi_google_search",
        "query": query,
        "results": [
            {
                "title": r.get("title", ""),
                "url": r.get("link", ""),
                "snippet": r.get("snippet", "")[:300],
                "position": r.get("position", 0),
            }
            for r in organic
        ],
    }


async def fetch_serp_maps(query: str, country_code: str = "fr") -> dict:
    """
    Google Maps via SerpAPI pour les acteurs locaux avec ratings.
    """
    key = _get_env("SERPAPI_KEY")
    if not key:
        return {"source": "serpapi_google_maps", "results": [], "error": "API key missing"}

    params = {
        "engine": "google_maps",
        "q": query,
        "api_key": key,
        "gl": country_code.lower(),
        "hl": "fr",
        "type": "search",
    }
    data = await _get(_SERP_BASE, params, _SEM_SERP)
    places = _safe_list(data.get("local_results", []), 8)
    return {
        "source": "serpapi_google_maps",
        "query": query,
        "results": [
            {
                "name": p.get("title", ""),
                "rating": p.get("rating", 0),
                "reviews": p.get("reviews", 0),
                "address": p.get("address", ""),
                "type": p.get("type", ""),
                "website": p.get("website", ""),
            }
            for p in places
        ],
    }


async def fetch_google_trends(keyword: str, country_code: str = "FR") -> dict:
    """
    Google Trends via SerpAPI.
    Retourne intérêt dans le temps + requêtes associées.
    """
    key = _get_env("SERPAPI_KEY")
    if not key:
        return {"source": "google_trends", "keyword": keyword, "results": {}, "error": "API key missing"}

    params = {
        "engine": "google_trends",
        "q": keyword,
        "api_key": key,
        "geo": country_code.upper(),
        "data_type": "TIMESERIES",
        "date": "today 12-m",
    }
    data = await _get(_SERP_BASE, params, _SEM_SERP)

    interest = data.get("interest_over_time", {})
    timeline = _safe_list(interest.get("timeline_data", []), 12)

    # Calculer direction : comparer 1er tiers vs dernier tiers
    values = []
    for point in timeline:
        v = point.get("values", [{}])
        if v and isinstance(v[0], dict):
            try:
                values.append(int(v[0].get("extracted_value", 0)))
            except (ValueError, TypeError):
                pass

    direction = "STABLE"
    if len(values) >= 4:
        first_avg = sum(values[: len(values) // 3]) / max(len(values) // 3, 1)
        last_avg  = sum(values[-len(values) // 3:]) / max(len(values) // 3, 1)
        if last_avg > first_avg * 1.2:
            direction = "RISING"
        elif last_avg < first_avg * 0.8:
            direction = "FALLING"

    related = _safe_list(data.get("related_queries", {}).get("rising", []), 5)

    return {
        "source": "google_trends",
        "keyword": keyword,
        "direction": direction,
        "signal_strength": "HIGH" if direction == "RISING" else "MEDIUM" if direction == "STABLE" else "LOW",
        "avg_interest_last_month": int(values[-1]) if values else 0,
        "related_rising": [q.get("query", "") for q in related],
    }


async def fetch_tiktok_signals(query: str) -> dict:
    """
    Signaux TikTok via SerpAPI pour détecter tendances virales.
    """
    key = _get_env("SERPAPI_KEY")
    if not key:
        return {"source": "tiktok", "results": [], "error": "API key missing"}

    params = {
        "engine": "tiktok",
        "search_query": query,
        "api_key": key,
    }
    data = await _get(_SERP_BASE, params, _SEM_SERP)
    videos = _safe_list(data.get("videos", []), 6)
    return {
        "source": "tiktok",
        "query": query,
        "results": [
            {
                "title": v.get("description", "")[:200],
                "likes": v.get("likes", 0),
                "plays": v.get("plays", 0),
                "hashtags": _safe_list(v.get("hashtags", []), 5),
            }
            for v in videos
        ],
    }


# ══════════════════════════════════════════════════════════════
# TOOL 3 — NEWSAPI : actualités sectorielles
# ══════════════════════════════════════════════════════════════

async def fetch_newsapi(query: str, language: str = "fr", days: int = 30) -> dict:
    """
    Articles récents via NewsAPI.
    language : 'fr' | 'en' | 'ar'
    """
    key = _get_env("NEWSAPI_KEY")
    if not key:
        return {"source": "newsapi", "articles": [], "error": "API key missing"}

    from datetime import datetime, timedelta
    from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    params = {
        "q": query,
        "language": language,
        "from": from_date,
        "sortBy": "relevancy",
        "pageSize": 10,
        "apiKey": key,
    }
    data = await _get("https://newsapi.org/v2/everything", params, _SEM_NEWS)
    articles = _safe_list(data.get("articles", []), 8)
    return {
        "source": "newsapi",
        "query": query,
        "total_results": data.get("totalResults", 0),
        "articles": [
            {
                "title": a.get("title", ""),
                "source": a.get("source", {}).get("name", ""),
                "published_at": a.get("publishedAt", "")[:10],
                "description": (a.get("description") or "")[:300],
                "url": a.get("url", ""),
            }
            for a in articles
            if a.get("title") and "[Removed]" not in a.get("title", "")
        ],
    }


# ══════════════════════════════════════════════════════════════
# TOOL 4 — YOUTUBE DATA v3 : signaux VOC
# ══════════════════════════════════════════════════════════════

async def fetch_youtube_voc(query: str, max_results: int = 8) -> dict:
    """
    Recherche YouTube pour signaux VOC — titres, vues, commentaires.
    Quota : 100 units/search → ~100 recherches/jour free.
    """
    key = _get_env("YOUTUBE_API_KEY")
    if not key:
        return {"source": "youtube", "videos": [], "error": "API key missing"}

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "relevance",
        "key": key,
    }
    data = await _get(
        "https://www.googleapis.com/youtube/v3/search",
        params,
        _SEM_YT,
    )
    items = _safe_list(data.get("items", []), max_results)
    return {
        "source": "youtube",
        "query": query,
        "videos": [
            {
                "title": item.get("snippet", {}).get("title", ""),
                "channel": item.get("snippet", {}).get("channelTitle", ""),
                "published_at": item.get("snippet", {}).get("publishedAt", "")[:10],
                "description": (item.get("snippet", {}).get("description") or "")[:200],
                "video_id": item.get("id", {}).get("videoId", ""),
            }
            for item in items
        ],
    }


# ══════════════════════════════════════════════════════════════
# TOOL 5 — WORLDBANK API : données macroéconomiques
# Pas de clé API, gratuit et illimité
# ══════════════════════════════════════════════════════════════

_WB_INDICATORS = {
    "gdp_per_capita":            "NY.GDP.PCAP.CD",
    "population":                "SP.POP.TOTL",
    "internet_pct":              "IT.NET.USER.ZS",
    "mobile_per100":             "IT.CEL.SETS.P2",
    "urban_pct":                 "SP.URB.TOTL.IN.ZS",
    "youth_pct":                 "SP.POP.1564.TO.ZS",
    # Indicateurs éducation — réduisent les estimations LLM sur la population cible
    "tertiary_enrollment_pct":   "SE.TER.ENRR",   # % inscrits dans le supérieur
    "secondary_enrollment_pct":  "SE.SEC.ENRR",   # % inscrits dans le secondaire
    "literacy_rate_adult":       "SE.ADT.LITR.ZS", # Taux alphabétisation adultes
}


async def fetch_worldbank(country_code: str) -> dict:
    """
    Indicateurs macroéconomiques WorldBank pour un pays (code ISO2).
    Exemple : country_code = "TN" pour Tunisie.
    """
    if not country_code or len(country_code) != 2:
        return {"source": "worldbank", "country_code": country_code, "indicators": {}, "error": "invalid country_code"}

    results = {}
    tasks = {}

    async def fetch_one(name: str, indicator: str) -> tuple[str, Any]:
        url = f"https://api.worldbank.org/v2/country/{country_code.upper()}/indicator/{indicator}"
        params = {"format": "json", "mrv": 1, "per_page": 1}
        data = await _get(url, params, _SEM_WB)
        try:
            value = data[1][0]["value"] if data and len(data) > 1 and data[1] else None
            return name, round(value, 2) if value is not None else None
        except (IndexError, KeyError, TypeError):
            return name, None

    fetch_tasks = [fetch_one(name, ind) for name, ind in _WB_INDICATORS.items()]
    done = await asyncio.gather(*fetch_tasks)

    for name, value in done:
        results[name] = value

    return {
        "source": "worldbank",
        "country_code": country_code.upper(),
        "indicators": results,
    }


# ══════════════════════════════════════════════════════════════
# ORCHESTRATEUR — Lance tous les outils en parallèle
# ══════════════════════════════════════════════════════════════

async def run_all_tools(queries: dict, country_code: str = "FR") -> dict:
    """
    Lance tous les tools en parallèle (asyncio.gather).

    queries = {
        "competitors":  "plateforme tutorat en ligne Tunisie",
        "maps":         "cours particuliers Tunis",
        "tavily":       "EdTech tutorat marché Tunisie croissance",
        "reddit":       "online tutoring Tunisia student review",
        "news":         "EdTech tutorat éducation Tunisie",
        "trends_1":     "tutorat en ligne",
        "trends_2":     "cours particuliers",
        "youtube":      "tutorat en ligne Tunisie avis",
        "tiktok":       "cours particuliers Tunisie",
        "regulatory":   "réglementation tutorat enseignement Tunisie",
    }
    country_code : "TN" | "FR" | "MA" etc.

    Retourne un dict { source_name: raw_data }
    """
    # Lancer tous en parallèle
    tasks = await asyncio.gather(
        fetch_serp_competitors(queries.get("competitors", ""), country_code),
        fetch_serp_maps(queries.get("maps", ""), country_code),
        fetch_tavily_insights(queries.get("tavily", ""), max_results=6),
        fetch_reddit_voc(queries.get("reddit", ""), max_results=5),
        fetch_newsapi(queries.get("news", ""), language="fr"),
        fetch_google_trends(queries.get("trends_1", ""), country_code),
        fetch_google_trends(queries.get("trends_2", ""), country_code),
        fetch_youtube_voc(queries.get("youtube", ""), max_results=6),
        fetch_tiktok_signals(queries.get("tiktok", "")),
        fetch_regulatory(queries.get("regulatory", ""), country_code),
        fetch_worldbank(country_code),
        return_exceptions=True,
    )

    sources = [
        "serp_competitors", "serp_maps", "tavily", "reddit",
        "newsapi", "trends_1", "trends_2", "youtube",
        "tiktok", "regulatory", "worldbank",
    ]

    raw_data = {}
    for source, result in zip(sources, tasks):
        if isinstance(result, Exception):
            logger.error(f"[tools] {source} failed: {result}")
            raw_data[source] = {"source": source, "error": str(result), "results": []}
        else:
            raw_data[source] = result

    return raw_data