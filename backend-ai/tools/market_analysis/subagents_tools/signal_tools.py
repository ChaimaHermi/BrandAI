# ══════════════════════════════════════════════════════════════
# tools/market_analysis/subagents_tools/signal_tools.py  [v2]
# Changements :
#   fetch_google_trends : 3 data_types en parallèle au lieu de TIMESERIES seul
#     → TIMESERIES       : timeline (inchangé)
#     → RELATED_QUERIES  : rising_queries fiables même avec faible volume
#     → RELATED_TOPICS   : topics montants — plus robuste marchés émergents
#   fetch_google_autocomplete (NOUVEAU) : suggestions temps réel → tendances
#   fetch_tavily_trends (NOUVEAU)       : tendances via news Tavily
#   fetch_tiktok_signals : inchangé (désactivé)
#   fetch_regulatory     : inchangé
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


# ── Cache ──────────────────────────────────────────────────────

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


# ── HTTP ───────────────────────────────────────────────────────

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
                r = await c.post(url, json=payload,
                                 headers={"Content-Type": "application/json"})
                r.raise_for_status()
                return r.json()
        except Exception as e:
            logger.error(f"[signal_tools] POST {url}: {e}")
            return {}

def _sl(obj: Any, n: int) -> list:
    return obj[:n] if isinstance(obj, list) else []


# ══════════════════════════════════════════════════════════════
# TOOL 1 — Google Trends via SerpAPI [VERSION AMÉLIORÉE]
# Lance 3 data_types en parallèle pour maximiser les résultats
# ══════════════════════════════════════════════════════════════

async def fetch_google_trends(keyword: str, country_code: str = "TN") -> dict:
    """
    Lance 3 requêtes SerpAPI Google Trends en parallèle :
    - TIMESERIES      → timeline historique
    - RELATED_QUERIES → rising_queries (fonctionne même avec faible volume)
    - RELATED_TOPICS  → topics montants (plus robuste que RELATED_QUERIES)
    """
    k = _key("trends_v2", keyword, country_code)
    if c := _cget(k): return c

    api_key = os.getenv("SERPAPI_KEY", "")
    if not api_key:
        return {"source": "google_trends", "keyword": keyword, "error": "missing key"}

    base_params = {
        "engine":  "google_trends",
        "q":       keyword,
        "api_key": api_key,
        "geo":     country_code.upper(),
        "date":    "today 12-m",
    }

    # 3 appels en parallèle
    timeseries_data, related_queries_data, related_topics_data = await asyncio.gather(
        _get(_SERP_BASE, {**base_params, "data_type": "TIMESERIES"},      _SEM_SERP, DELAYS["serpapi"]),
        _get(_SERP_BASE, {**base_params, "data_type": "RELATED_QUERIES"}, _SEM_SERP, DELAYS["serpapi"]),
        _get(_SERP_BASE, {**base_params, "data_type": "RELATED_TOPICS"},  _SEM_SERP, DELAYS["serpapi"]),
    )

    # ── TIMESERIES → timeline ─────────────────────────────────
    timeline_raw = _sl(
        timeseries_data.get("interest_over_time", {}).get("timeline_data", []),
        LIMITS["serp_trends_points"],
    )
    timeline = []
    for p in timeline_raw:
        v = p.get("values", [{}])
        if v and isinstance(v[0], dict):
            timeline.append({
                "date":  p.get("date", ""),
                "value": v[0].get("extracted_value", 0),
            })

    # ── RELATED_QUERIES → rising_queries ──────────────────────
    rq_data      = related_queries_data.get("related_queries", {})
    rising_raw   = _sl(rq_data.get("rising", []), LIMITS.get("rising_queries", 8))
    top_raw      = _sl(rq_data.get("top",    []), 5)

    rising_queries = [q.get("query", "") for q in rising_raw if q.get("query")]
    top_queries    = [q.get("query", "") for q in top_raw    if q.get("query")]

    # ── RELATED_TOPICS → rising_topics ────────────────────────
    rt_data         = related_topics_data.get("related_topics", {})
    rising_topics_r = _sl(rt_data.get("rising", []), 5)
    top_topics_r    = _sl(rt_data.get("top",    []), 5)

    rising_topics = [
        t.get("topic", {}).get("title", "") or t.get("title", "")
        for t in rising_topics_r
        if t.get("topic", {}).get("title") or t.get("title")
    ]
    top_topics = [
        t.get("topic", {}).get("title", "") or t.get("title", "")
        for t in top_topics_r
        if t.get("topic", {}).get("title") or t.get("title")
    ]

    # ── Fusion rising : queries + topics ──────────────────────
    all_rising = list(dict.fromkeys(rising_queries + rising_topics))  # dédupliqué

    result = {
        "source":         "google_trends",
        "keyword":        keyword,
        "country":        country_code.upper(),
        "timeline":       timeline,
        "rising_queries": all_rising,           # fusion queries + topics
        "top_queries":    top_queries,
        "rising_topics":  rising_topics,        # gardé séparément pour le LLM
        "top_topics":     top_topics,
        # Diagnostic : savoir quelle source a fourni des données
        "_debug": {
            "timeseries_points":   len(timeline),
            "rising_queries_raw":  len(rising_queries),
            "rising_topics_raw":   len(rising_topics),
        },
    }

    _cset(k, result, CACHE_TTL["serpapi_trends"])
    logger.info(
        f"[signal_tools] Trends '{keyword}' ({country_code}): "
        f"{len(timeline)} pts, {len(all_rising)} rising"
    )
    return result


# ══════════════════════════════════════════════════════════════
# TOOL 2 — Google Autocomplete via SerpAPI (NOUVEAU)
# Suggestions en temps réel = proxy fiable des tendances actuelles
# ══════════════════════════════════════════════════════════════

async def fetch_google_autocomplete(keyword: str, country_code: str = "TN") -> dict:
    """
    Google Autocomplete = ce que les gens tapent MAINTENANT.
    Fonctionne même avec un faible volume de recherche local.
    Retourne 5-10 suggestions ordonnées par popularité.
    """
    k = _key("autocomplete", keyword, country_code)
    if c := _cget(k): return c

    api_key = os.getenv("SERPAPI_KEY", "")
    if not api_key:
        return {"source": "google_autocomplete", "keyword": keyword, "suggestions": []}

    data = await _get(_SERP_BASE, {
        "engine":  "google_autocomplete",
        "q":       keyword,
        "api_key": api_key,
        "gl":      country_code.lower(),
        "hl":      "fr",
    }, _SEM_SERP, DELAYS["serpapi"])

    suggestions_raw = data.get("suggestions", [])
    suggestions = [
        s.get("value", "")
        for s in _sl(suggestions_raw, 10)
        if s.get("value") and s.get("value", "").lower() != keyword.lower()
    ]

    result = {
        "source":      "google_autocomplete",
        "keyword":     keyword,
        "country":     country_code.upper(),
        "suggestions": suggestions,
    }
    _cset(k, result, CACHE_TTL.get("serpapi_autocomplete", 3600))
    logger.info(f"[signal_tools] Autocomplete '{keyword}': {len(suggestions)} suggestions")
    return result


# ══════════════════════════════════════════════════════════════
# TOOL 3 — Trending topics via Tavily (NOUVEAU)
# Extrait les tendances depuis les titres de news récentes
# Gratuit, aucune clé supplémentaire nécessaire
# ══════════════════════════════════════════════════════════════

async def fetch_tavily_trends(query: str, country_code: str = "TN") -> dict:
    """
    Utilise Tavily pour extraire les tendances actuelles du secteur
    depuis les articles récents. Complète Google Trends quand le
    volume local est trop faible.
    """
    k = _key("tavily_trends", query, country_code)
    if c := _cget(k): return c

    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return {"source": "tavily_trends", "query": query, "signals": []}

    # Query orientée actualités récentes pour capter les tendances
    trend_query = f"{query} trending popular growing demand 2025"

    data = await _post("https://api.tavily.com/search", {
        "api_key":       api_key,
        "query":         trend_query,
        "search_depth":  "basic",
        "max_results":   5,
        "include_answer": False,
    }, _SEM_TAVILY)

    results_raw = _sl(data.get("results", []), 5)

    # Extraire les titres comme signaux de tendance
    signals = [
        r.get("title", "")
        for r in results_raw
        if r.get("title") and len(r.get("title", "")) > 10
    ]

    # Extraire des mots-clés depuis les snippets (proxy rising_queries)
    snippet_keywords = []
    for r in results_raw:
        snippet = r.get("content", "")[:200]
        # Garder les extraits qui contiennent des signaux positifs
        if any(w in snippet.lower() for w in [
            "growing", "trending", "popular", "increase", "demand",
            "croissance", "tendance", "populaire", "hausse",
        ]):
            snippet_keywords.append(snippet[:100])

    result = {
        "source":            "tavily_trends",
        "query":             query,
        "country":           country_code.upper(),
        "signals":           signals,           # titres d'articles récents
        "snippet_keywords":  snippet_keywords,  # extraits avec signaux positifs
    }
    _cset(k, result, CACHE_TTL.get("tavily", 3600))
    logger.info(f"[signal_tools] Tavily trends '{query}': {len(signals)} signaux")
    return result


# ══════════════════════════════════════════════════════════════
# TOOL 4 — TikTok (désactivé — plan payant SerpAPI)
# ══════════════════════════════════════════════════════════════

async def fetch_tiktok_signals(query: str) -> dict:
    logger.debug(f"[signal_tools] TikTok désactivé pour: {query}")
    return {
        "source":               "tiktok",
        "query":                query,
        "results":              [],
        "hashtags":             [],
        "hashtags_disponibles": False,
        "disponible":           False,
    }


# ══════════════════════════════════════════════════════════════
# TOOL 5 — Regulatory via Tavily (inchangé)
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

    data = await _post("https://api.tavily.com/search", {
        "api_key":       api_key,
        "query":         reg_query,
        "search_depth":  "basic",
        "max_results":   LIMITS["tavily_regulatory_results"],
        "include_answer": False,
    }, _SEM_TAVILY)

    results = _sl(data.get("results", []), LIMITS["tavily_regulatory_results"])
    result  = {
        "source":  "regulatory_via_tavily",
        "query":   query,
        "results": [
            {"title": r.get("title", ""), "snippet": r.get("content", "")[:300]}
            for r in results
        ],
    }
    _cset(k, result, CACHE_TTL["tavily"])
    logger.info(f"[signal_tools] Regulatory: {len(result['results'])} résultats")
    return result