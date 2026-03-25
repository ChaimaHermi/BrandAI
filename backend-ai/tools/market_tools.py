# ══════════════════════════════════════════════════════════════
#  market_tools.py  —  BrandAI
#
#  CORRECTIONS vs version précédente :
#  P4 — Tavily + Serper ajoutés (principaux pour web+VOC)
#  P5 — Reddit via Tavily site:reddit.com (plus de 403)
#  P6 — Google Trends via SerpAPI (plus d'Apify payant)
#  P7 — Semaphore rate limiting SerpAPI
#  + SerpAPI Maps (ratings locaux)
#  + SerpAPI TikTok (signaux viraux)
#  + Pricing tool (nouveau)
#  + Regulatory tool (nouveau)
# ══════════════════════════════════════════════════════════════

import os
import asyncio
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("brandai.market_tools")

TIMEOUT      = httpx.Timeout(30.0)
TIMEOUT_LONG = httpx.Timeout(60.0)

# Rate limiting SerpAPI — max 2 requêtes simultanées
_SERP_SEM = asyncio.Semaphore(2)


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _serp_key() -> str:
    return os.getenv("SERPAPI_KEY", "") or os.getenv("SERPAPI_KEY_2", "")

def _tavily_key() -> str:
    return os.getenv("TAVILY_API_KEY", "")

def _serper_key() -> str:
    return os.getenv("SERPER_API_KEY", "")


async def _serp(client: httpx.AsyncClient, params: dict) -> dict:
    """Appel SerpAPI avec rate limiting."""
    key = _serp_key()
    if not key:
        return {}
    async with _SERP_SEM:
        try:
            r = await client.get(
                "https://serpapi.com/search",
                params={**params, "api_key": key},
                timeout=TIMEOUT,
            )
            return r.json() if r.status_code == 200 else {}
        except Exception as e:
            logger.warning(f"[tools] SerpAPI error: {e}")
            return {}


async def _tavily(client: httpx.AsyncClient, query: str, topic: str = "general", n: int = 5) -> list:
    """Appel Tavily — résumés riches optimisés LLM."""
    key = _tavily_key()
    if not key:
        return []
    try:
        r = await client.post(
            "https://api.tavily.com/search",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "query": query,
                "search_depth": "basic",
                "topic": topic,
                "max_results": n,
                "include_answer": True,
            },
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            if data.get("answer"):
                results.insert(0, {"title": "Résumé Tavily", "content": data["answer"], "url": ""})
            return results
        return []
    except Exception as e:
        logger.warning(f"[tools] Tavily error: {e}")
        return []


async def _serper(client: httpx.AsyncClient, query: str, stype: str = "search") -> list:
    """Appel Serper.dev — fallback général."""
    key = _serper_key()
    if not key:
        return []
    try:
        r = await client.post(
            f"https://google.serper.dev/{stype}",
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            json={"q": query, "num": 5},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            data = r.json()
            items = data.get("organic", []) or data.get("news", [])
            return [{"title": i.get("title"), "content": i.get("snippet"), "url": i.get("link")} for i in items]
        return []
    except Exception as e:
        logger.warning(f"[tools] Serper error: {e}")
        return []


# ══════════════════════════════════════════════════════════════
# TOOL 1 — SERPAPI (concurrents + signaux)
# Corrigé : + Maps + rate limiting
# ══════════════════════════════════════════════════════════════

async def fetch_serpapi(queries: dict) -> dict:
    """
    Concurrents via SerpAPI Google Search + Google Maps.
    - serpapi_local  → concurrents langue locale
    - serpapi_global → benchmarks EN
    - serpapi_maps   → ratings locaux (économisé — 1-2 req max)
    """
    logger.info("[tools] SERPAPI start")
    results = {"competitors": [], "organic_signals": [], "local_ratings": []}

    local_q  = queries.get("serpapi_local", [])[:4]
    global_q = queries.get("serpapi_global", [])[:3]
    maps_q   = queries.get("serpapi_maps", [])[:1]  # économisé

    async with httpx.AsyncClient() as client:

        # ── Google Search local + global ──────────────────────
        all_search = local_q + global_q
        tasks = [_serp(client, {"q": q, "hl": "fr", "num": 8}) for q in all_search]
        responses = await asyncio.gather(*tasks)

        for data in responses:
            for r in data.get("organic_results", [])[:5]:
                results["competitors"].append({
                    "title":   r.get("title", ""),
                    "link":    r.get("link", ""),
                    "snippet": r.get("snippet", ""),
                })
            for s in data.get("related_searches", []):
                q = s.get("query")
                if q:
                    results["organic_signals"].append(q)

        # ── Google Maps — ratings locaux ──────────────────────
        if maps_q and _serp_key():
            maps_data = await _serp(client, {"engine": "google_maps", "q": maps_q[0], "hl": "fr"})
            for r in maps_data.get("local_results", [])[:4]:
                results["local_ratings"].append({
                    "name":    r.get("title"),
                    "rating":  r.get("rating"),
                    "reviews": r.get("reviews"),
                    "website": r.get("website"),
                })

    logger.info(f"[tools] SERPAPI done — {len(results['competitors'])} competitors")
    return results


# ══════════════════════════════════════════════════════════════
# TOOL 2 — TAVILY COMPETITOR (nouveau — principal pour web)
# ══════════════════════════════════════════════════════════════

async def fetch_tavily_competitor(queries: dict) -> dict:
    """
    Recherche concurrents via Tavily — résumés riches pour LLM.
    Principal outil web (économise SerpAPI).
    """
    logger.info("[tools] TAVILY COMPETITOR start")
    results = {"competitor_summaries": [], "source": "tavily"}

    tavily_q = queries.get("tavily_competitor", [])[:3]

    async with httpx.AsyncClient() as client:
        tasks = [_tavily(client, q, topic="general", n=5) for q in tavily_q]
        responses = await asyncio.gather(*tasks)

        for batch in responses:
            results["competitor_summaries"].extend(batch)

    # Fallback Serper si Tavily vide
    if not results["competitor_summaries"]:
        logger.info("[tools] Tavily competitor empty — Serper fallback")
        async with httpx.AsyncClient() as client:
            fallback_q = queries.get("serpapi_global", ["startup market"])[:2]
            tasks = [_serper(client, q) for q in fallback_q]
            responses = await asyncio.gather(*tasks)
            for batch in responses:
                results["competitor_summaries"].extend(batch)
        results["source"] = "serper_fallback"

    logger.info(f"[tools] TAVILY COMPETITOR done — {len(results['competitor_summaries'])} results")
    return results


# ══════════════════════════════════════════════════════════════
# TOOL 3 — YOUTUBE
# ══════════════════════════════════════════════════════════════

async def fetch_youtube(queries: dict) -> dict:
    """Vidéos YouTube populaires — signaux comportement utilisateur."""
    logger.info("[tools] YOUTUBE start")
    api_key = os.getenv("YOUTUBE_API_KEY", "")

    if not api_key:
        logger.warning("[tools] YOUTUBE_API_KEY manquante")
        return {"trending_videos": []}

    results = {"trending_videos": []}
    youtube_q = queries.get("youtube", [])[:3]

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        tasks = [
            client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet", "q": q, "key": api_key,
                    "maxResults": 5, "type": "video", "order": "viewCount",
                },
            )
            for q in youtube_q
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    for resp in responses:
        if isinstance(resp, Exception):
            continue
        try:
            for item in resp.json().get("items", []):
                s = item.get("snippet", {})
                results["trending_videos"].append({
                    "title":       s.get("title", ""),
                    "description": s.get("description", "")[:200],
                    "channel":     s.get("channelTitle", ""),
                    "published":   s.get("publishedAt", ""),
                    "video_id":    item.get("id", {}).get("videoId", ""),
                })
        except Exception as e:
            logger.warning(f"[tools] YOUTUBE parse: {e}")

    logger.info(f"[tools] YOUTUBE done — {len(results['trending_videos'])} videos")
    return results


# ══════════════════════════════════════════════════════════════
# TOOL 4 — NEWS (NewsAPI + Newsdata.io)
# ══════════════════════════════════════════════════════════════

async def fetch_tavily_news(queries: dict) -> dict:
    """
    Fallback news via Tavily.

    Utilise les mêmes "signaux" (funding/regulatory) que fetch_news(),
    et renvoie un format compatible (title/description/source/url/publishedAt).
    """
    logger.info("[tools] TAVILY NEWS fallback start")

    results = {"articles": [], "funding_signals": [], "regulatory_signals": []}
    if not _tavily_key():
        return results

    news_q = queries.get("newsapi", [])[:3]  # on réutilise les requêtes générées pour NewsAPI
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        tasks = [_tavily(client, q, topic="news", n=5) for q in news_q]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    seen_urls = set()
    for batch in responses:
        if isinstance(batch, Exception):
            continue
        for item in batch:
            title = item.get("title", "") or ""
            content = item.get("content", "") or ""
            url = item.get("url", "") or ""
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            article = {
                "title": title,
                "description": content,
                "source": "tavily",
                "url": url,
                "publishedAt": "",
            }
            results["articles"].append(article)

            text = (title + " " + content).lower()
            if any(k in text for k in ["funding", "raises", "investment", "série", "seed", "levée"]):
                results["funding_signals"].append(title)
            if any(k in text for k in ["regulation", "law", "ban", "compliance", "rgpd", "réglementation"]):
                results["regulatory_signals"].append(title)

    results["articles"] = results["articles"][:12]
    return results


async def fetch_news(queries: dict) -> dict:
    """Actualités secteur — NewsAPI FR+EN + Newsdata MENA."""
    logger.info("[tools] NEWS start")
    results = {
        "articles": [],
        "funding_signals": [],
        "regulatory_signals": [],
        "sources_used": [],
    }

    news_q   = queries.get("newsapi", [])[:3]
    main_q   = " OR ".join(news_q[:2]) if news_q else "startup"
    api_key  = os.getenv("NEWSAPI_KEY", "")
    nd_key   = os.getenv("NEWSDATA_API_KEY", "")

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        tasks = []  # list of (source_label, coroutine)

        # NewsAPI FR
        if api_key:
            tasks.append(("newsapi", client.get(
                "https://newsapi.org/v2/everything",
                params={"q": main_q, "apiKey": api_key, "pageSize": 6,
                        "sortBy": "publishedAt", "language": "fr"},
            )))
        # NewsAPI EN
        if api_key:
            tasks.append(("newsapi", client.get(
                "https://newsapi.org/v2/everything",
                params={"q": main_q, "apiKey": api_key, "pageSize": 4,
                        "sortBy": "publishedAt", "language": "en"},
            )))
        # Newsdata MENA
        if nd_key:
            tasks.append(("newsdata", client.get(
                "https://newsdata.io/api/1/news",
                params={"apikey": nd_key, "q": main_q,
                        "language": "fr,ar,en", "country": "tn,ma,dz,sa,ae"},
            )))

        sources = [s for s, _ in tasks]
        responses = await asyncio.gather(*(c for _, c in tasks), return_exceptions=True)

    newsapi_count = 0
    newsdata_count = 0
    seen_urls = set()
    for src, resp in zip(sources, responses):
        if isinstance(resp, Exception):
            continue
        try:
            data = resp.json()
            # NewsAPI format
            for a in data.get("articles", []):
                url = a.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                if src == "newsapi":
                    newsapi_count += 1
                article = {
                    "title":       a.get("title", ""),
                    "description": a.get("description", ""),
                    "source":      a.get("source", {}).get("name", ""),
                    "url":         url,
                    "publishedAt": a.get("publishedAt", ""),
                }
                results["articles"].append(article)
                t = (article["title"] or "").lower()
                if any(k in t for k in ["funding", "raises", "investment", "série", "seed", "levée"]):
                    results["funding_signals"].append(article["title"])
                if any(k in t for k in ["regulation", "law", "ban", "compliance", "rgpd", "réglementation"]):
                    results["regulatory_signals"].append(article["title"])
            # Newsdata format
            for a in data.get("results", []):
                url = a.get("link", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                if src == "newsdata":
                    newsdata_count += 1
                results["articles"].append({
                    "title":       a.get("title", ""),
                    "description": a.get("description", ""),
                    "source":      a.get("source_id", ""),
                    "url":         url,
                    "publishedAt": a.get("pubDate", ""),
                })
        except Exception as e:
            logger.warning(f"[tools] NEWS parse: {e}")

    # Si les deux sources retournent 0 articles → fallback Tavily
    if newsapi_count == 0 and newsdata_count == 0:
        fallback = await fetch_tavily_news(queries)
        results["articles"] = fallback.get("articles", [])
        results["funding_signals"] = fallback.get("funding_signals", [])
        results["regulatory_signals"] = fallback.get("regulatory_signals", [])
        results["sources_used"].append("tavily_news_fallback")

    results["articles"] = results["articles"][:12]
    logger.info(f"[tools] NEWS done — {len(results['articles'])} articles")
    return results


# ══════════════════════════════════════════════════════════════
# TOOL 5 — REDDIT via TAVILY (corrigé — plus de 403)
# ══════════════════════════════════════════════════════════════

async def fetch_reddit(queries: dict) -> dict:
    """
    VOC Reddit + Quora via Tavily site: filter.
    CORRIGÉ : Reddit public API → 403 en prod.
    Solution : Tavily site:reddit.com + site:quora.com
    Fallback : Serper
    """
    logger.info("[tools] REDDIT (Tavily) start")
    results = {"posts": [], "pain_points": [], "competitor_mentions": []}

    voc_q = queries.get("tavily_voc", [])[:3]

    async with httpx.AsyncClient() as client:

        # ── Tavily Reddit + Quora ─────────────────────────────
        if _tavily_key():
            tasks = [_tavily(client, q, topic="general", n=6) for q in voc_q]
            responses = await asyncio.gather(*tasks)

            for batch in responses:
                for item in batch:
                    title   = item.get("title", "")
                    content = item.get("content", "")
                    url     = item.get("url", "")

                    results["posts"].append({
                        "title":     title,
                        "body":      content[:300],
                        "subreddit": "reddit" if "reddit" in url else "quora",
                        "url":       url,
                    })

                    text = (title + " " + content).lower()
                    if any(k in text for k in ["problem", "issue", "frustrated", "hate", "broken", "can't", "worst"]):
                        results["pain_points"].append(title)
                    if any(k in text for k in ["vs", "alternative", "better than", "switch"]):
                        results["competitor_mentions"].append(title)

        # ── Serper fallback si Tavily vide ────────────────────
        if not results["posts"] and _serper_key():
            logger.info("[tools] Reddit Tavily empty — Serper fallback")
            fallback_q = queries.get("serpapi_local", ["startup"])[:2]
            async with httpx.AsyncClient() as c:
                tasks = [_serper(c, f"site:reddit.com {q}") for q in fallback_q]
                responses = await asyncio.gather(*tasks)
                for batch in responses:
                    for item in batch:
                        results["posts"].append({
                            "title": item.get("title", ""),
                            "body":  item.get("content", "")[:300],
                            "subreddit": "reddit",
                            "url": item.get("url", ""),
                        })

    results["posts"]               = results["posts"][:20]
    results["pain_points"]         = list(dict.fromkeys(results["pain_points"]))[:8]
    results["competitor_mentions"] = list(dict.fromkeys(results["competitor_mentions"]))[:8]

    logger.info(f"[tools] REDDIT done — {len(results['posts'])} posts")
    return results


# ══════════════════════════════════════════════════════════════
# TOOL 6 — TRENDS via SerpAPI (corrigé — plus d'Apify)
# ══════════════════════════════════════════════════════════════

async def fetch_trends(queries: dict) -> dict:
    """
    Google Trends + TikTok via SerpAPI.
    CORRIGÉ : Apify payant → SerpAPI engine=google_trends (gratuit avec clé existante)
    """
    logger.info("[tools] TRENDS start")
    results = {"trends": [], "tiktok_signals": []}

    trends_kw = queries.get("serpapi_trends", [])[:3]
    tiktok_kw = queries.get("serpapi_tiktok", [])[:2]

    if not _serp_key():
        logger.warning("[tools] SERPAPI_KEY manquante pour Trends")
        return results

    async with httpx.AsyncClient() as client:

        # ── Google Trends ─────────────────────────────────────
        trends_tasks = [
            _serp(client, {
                "engine": "google_trends",
                "q": kw,
                "date": "today 12-m",
                "geo": "",
            })
            for kw in trends_kw
        ]
        trends_responses = await asyncio.gather(*trends_tasks)

        for kw, data in zip(trends_kw, trends_responses):
            if data.get("interest_over_time"):
                timeline = data["interest_over_time"].get("timeline_data", [])
                averages = data["interest_over_time"].get("averages", [])
                results["trends"].append({
                    "keyword":   kw,
                    "timeline":  timeline[-6:],
                    "averages":  averages,
                    "rising_queries": [
                        r.get("query") for r in
                        data.get("related_queries", {}).get("rising", [])[:5]
                    ],
                })

        # ── TikTok signaux viraux ─────────────────────────────
        tiktok_tasks = [
            _serp(client, {"engine": "tiktok", "q": kw, "type": "item"})
            for kw in tiktok_kw
        ]
        tiktok_responses = await asyncio.gather(*tiktok_tasks)

        for data in tiktok_responses:
            for v in data.get("video_results", [])[:4]:
                results["tiktok_signals"].append({
                    "title":      v.get("title", ""),
                    "play_count": v.get("plays"),
                    "like_count": v.get("likes"),
                })

    logger.info(f"[tools] TRENDS done — {len(results['trends'])} trends")
    return results


# ══════════════════════════════════════════════════════════════
# TOOL 7 — WORLD BANK
# ══════════════════════════════════════════════════════════════

async def fetch_worldbank(country_code: str = "TN") -> dict:
    """Indicateurs macro World Bank — gratuit, sans clé."""
    logger.info(f"[tools] WORLDBANK start — {country_code}")

    indicators = {
        "gdp_per_capita":       "NY.GDP.PCAP.CD",
        "internet_penetration": "IT.NET.USER.ZS",
        "mobile_per_100":       "IT.CEL.SETS.P2",
        "population":           "SP.POP.TOTL",
        "youth_population_pct": "SP.POP.1564.TO.ZS",
    }

    result = {"country": country_code}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        tasks = {
            key: client.get(
                f"https://api.worldbank.org/v2/country/{country_code}/indicator/{ind}",
                params={"format": "json", "mrv": 1},
            )
            for key, ind in indicators.items()
        }
        responses = await asyncio.gather(*tasks.values(), return_exceptions=True)

    for key, resp in zip(tasks.keys(), responses):
        if isinstance(resp, Exception):
            result[key] = None
            continue
        try:
            data = resp.json()
            entries = data[1] if isinstance(data, list) and len(data) > 1 else []
            result[key] = entries[0].get("value") if entries else None
        except Exception:
            result[key] = None

    logger.info(f"[tools] WORLDBANK done — {result}")
    return result


# ══════════════════════════════════════════════════════════════
# TOOL 9 — REGULATORY (nouveau)
# ══════════════════════════════════════════════════════════════

async def fetch_regulatory(queries: dict) -> dict:
    """Contexte réglementaire via Tavily + NewsAPI."""
    logger.info("[tools] REGULATORY start")
    results = {"regulatory_data": [], "source": []}

    reg_q = queries.get("regulatory", [])[:2]

    async with httpx.AsyncClient() as client:

        if _tavily_key():
            tasks = [_tavily(client, q, n=4) for q in reg_q]
            responses = await asyncio.gather(*tasks)
            for batch in responses:
                results["regulatory_data"].extend(batch)
            if results["regulatory_data"]:
                results["source"].append("tavily")

        if not results["regulatory_data"] and _serper_key():
            tasks = [_serper(client, q) for q in reg_q]
            responses = await asyncio.gather(*tasks)
            for batch in responses:
                results["regulatory_data"].extend(batch)
            if results["regulatory_data"]:
                results["source"].append("serper_fallback")

    logger.info(f"[tools] REGULATORY done — {len(results['regulatory_data'])} results")
    return results