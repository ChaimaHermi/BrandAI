# ══════════════════════════════════════════════════════════════
#  market_tools.py
#  Wrappers pour chaque API externe
#  Tous les appels sont async pour permettre asyncio.gather()
# ══════════════════════════════════════════════════════════════

import os
import asyncio
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("brandai.market_tools")

# ── Timeout global pour toutes les requêtes
TIMEOUT = httpx.Timeout(30.0)


# ══════════════════════════════════════════════════════════════
# SERPAPI
# ══════════════════════════════════════════════════════════════

async def fetch_serpapi(queries: dict) -> dict:
    """Recherche concurrents + signaux organiques via SerpAPI."""

    logger.info("[tools] SERPAPI start")
    api_key = os.getenv("SERPAPI_KEY")

    if not api_key:
        logger.warning("[tools] SERPAPI_KEY manquante")
        return {"competitors": [], "organic_signals": []}

    results = {"competitors": [], "organic_signals": []}
    all_queries = queries.get("competitors", []) + queries.get("trends", [])

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        tasks = [
            client.get(
                "https://serpapi.com/search",
                params={"q": q, "api_key": api_key, "hl": "fr", "num": 10},
            )
            for q in all_queries
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    for resp in responses:
        if isinstance(resp, Exception):
            logger.warning(f"[tools] SERPAPI error: {resp}")
            continue
        try:
            data = resp.json()
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
        except Exception as e:
            logger.warning(f"[tools] SERPAPI parse error: {e}")

    logger.info(f"[tools] SERPAPI done — {len(results['competitors'])} results")
    return results


# ══════════════════════════════════════════════════════════════
# YOUTUBE
# ══════════════════════════════════════════════════════════════

async def fetch_youtube(queries: dict) -> dict:
    """Recherche vidéos YouTube pour signaux de comportement utilisateur."""

    logger.info("[tools] YOUTUBE start")
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        logger.warning("[tools] YOUTUBE_API_KEY manquante")
        return {"trending_videos": []}

    results = {"trending_videos": []}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        tasks = [
            client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part":       "snippet",
                    "q":          q,
                    "key":        api_key,
                    "maxResults": 5,
                    "type":       "video",
                    "order":      "viewCount",
                },
            )
            for q in queries.get("youtube", [])
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    for resp in responses:
        if isinstance(resp, Exception):
            logger.warning(f"[tools] YOUTUBE error: {resp}")
            continue
        try:
            data = resp.json()
            for item in data.get("items", []):
                snippet = item.get("snippet", {})
                results["trending_videos"].append({
                    "title":       snippet.get("title", ""),
                    "description": snippet.get("description", "")[:200],
                    "channel":     snippet.get("channelTitle", ""),
                    "published":   snippet.get("publishedAt", ""),
                })
        except Exception as e:
            logger.warning(f"[tools] YOUTUBE parse error: {e}")

    logger.info(f"[tools] YOUTUBE done — {len(results['trending_videos'])} videos")
    return results


# ══════════════════════════════════════════════════════════════
# NEWS API
# ══════════════════════════════════════════════════════════════

async def fetch_news(queries: dict) -> dict:
    """Récupère actualités, signaux funding et régulation."""

    logger.info("[tools] NEWS start")
    api_key = os.getenv("NEWSAPI_KEY")

    if not api_key:
        logger.warning("[tools] NEWSAPI_KEY manquante")
        return {"articles": [], "funding_signals": [], "regulatory_signals": []}

    results = {
        "articles":            [],
        "funding_signals":     [],
        "regulatory_signals":  [],
    }

    news_queries = queries.get("news", ["startup funding"])

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        tasks = [
            client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q":        q,
                    "apiKey":   api_key,
                    "pageSize": 5,
                    "sortBy":   "relevancy",
                },
            )
            for q in news_queries
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    for resp in responses:
        if isinstance(resp, Exception):
            logger.warning(f"[tools] NEWS error: {resp}")
            continue
        try:
            data = resp.json()
            for a in data.get("articles", []):
                article = {
                    "title":       a.get("title", ""),
                    "description": a.get("description", ""),
                    "source":      a.get("source", {}).get("name", ""),
                    "url":         a.get("url", ""),
                    "publishedAt": a.get("publishedAt", ""),
                }
                results["articles"].append(article)

                # Classement automatique
                title_lower = (article["title"] or "").lower()
                if any(kw in title_lower for kw in ["funding", "raises", "investment", "série", "seed"]):
                    results["funding_signals"].append(article["title"])
                if any(kw in title_lower for kw in ["regulation", "law", "ban", "compliance", "gdpr"]):
                    results["regulatory_signals"].append(article["title"])
        except Exception as e:
            logger.warning(f"[tools] NEWS parse error: {e}")

    logger.info(f"[tools] NEWS done — {len(results['articles'])} articles")
    return results


# ══════════════════════════════════════════════════════════════
# REDDIT (APIFY)
# ══════════════════════════════════════════════════════════════

async def fetch_reddit(queries: dict) -> dict:
    """Fetch Reddit posts via public Reddit JSON API (free, no Apify)."""

    logger.info("[tools] REDDIT start")

    results = {
        "posts":                [],
        "pain_points":          [],
        "competitor_mentions":  [],
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            reddit_queries = queries.get("reddit", [])[:4]
            headers = {
                # Reddit requires a descriptive User-Agent for public endpoints.
                "User-Agent": "BrandAI/1.0 (market research bot)",
            }

            for q in reddit_queries:
                params = {
                    "q": q,
                    "sort": "top",
                    "t": "year",
                    "limit": 10,
                    "raw_json": 1,
                }
                resp = await client.get(
                    "https://www.reddit.com/search.json",
                    params=params,
                    headers=headers,
                )

                # Some environments are challenged on www.reddit.com.
                # Retry on old.reddit.com before giving up.
                if resp.status_code in (401, 403, 429):
                    resp = await client.get(
                        "https://old.reddit.com/search.json",
                        params=params,
                        headers=headers,
                    )

                if resp.status_code >= 400:
                    logger.warning(
                        f"[tools] REDDIT HTTP {resp.status_code} for query='{q}' | body={resp.text[:200]}"
                    )
                    continue

                payload = resp.json()
                children = (
                    payload.get("data", {}).get("children", [])
                    if isinstance(payload, dict)
                    else []
                )

                for child in children:
                    post = child.get("data", {}) if isinstance(child, dict) else {}
                    clean = {
                        "title":     post.get("title", ""),
                        "body":      (post.get("selftext", "") or "")[:300],
                        "subreddit": post.get("subreddit", ""),
                        "score":     post.get("score", 0),
                        "url":       f"https://www.reddit.com{post.get('permalink', '')}",
                    }
                    if not clean["title"]:
                        continue

                    results["posts"].append(clean)

                    # Détection pain points
                    text = (clean["title"] + " " + clean["body"]).lower()
                    if any(kw in text for kw in ["problem", "issue", "frustrated", "hate", "worst", "broken", "can't"]):
                        results["pain_points"].append(clean["title"])

                    # Détection mentions concurrents
                    if any(kw in text for kw in ["vs", "alternative", "better than", "switch from"]):
                        results["competitor_mentions"].append(clean["title"])

        # Déduplication simple
        seen = set()
        unique_posts = []
        for p in results["posts"]:
            key = (p.get("title", "").strip().lower(), p.get("subreddit", "").strip().lower())
            if key in seen:
                continue
            seen.add(key)
            unique_posts.append(p)
        results["posts"] = unique_posts[:30]
        results["pain_points"] = list(dict.fromkeys(results["pain_points"]))[:10]
        results["competitor_mentions"] = list(dict.fromkeys(results["competitor_mentions"]))[:10]

    except Exception as e:
        logger.warning(f"[tools] REDDIT error: {e}")

    logger.info(f"[tools] REDDIT done — {len(results['posts'])} posts")
    return results


# ══════════════════════════════════════════════════════════════
# GOOGLE TRENDS (APIFY)
# ══════════════════════════════════════════════════════════════

async def fetch_trends(queries: dict) -> dict:
    """Récupère les tendances Google via Apify."""

    logger.info("[tools] TRENDS start")
    token = os.getenv("APIFY_TOKEN")

    if not token:
        logger.warning("[tools] APIFY_TOKEN manquant")
        return {"trends": []}

    results = {"trends": []}

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            resp = await client.post(
                "https://api.apify.com/v2/acts/apify~google-trends-scraper/run-sync-get-dataset-items",
                params={"token": token},
                json={
                    "searchTerms": queries.get("google_trends", []),
                    "geo":         "",        # worldwide
                    "timeRange":   "today 12-m",
                },
            )
        data = resp.json()
        results["trends"] = data if isinstance(data, list) else []

    except Exception as e:
        logger.warning(f"[tools] TRENDS error: {e}")

    logger.info(f"[tools] TRENDS done — {len(results['trends'])} items")
    return results


# ══════════════════════════════════════════════════════════════
# WORLD BANK
# ══════════════════════════════════════════════════════════════

async def fetch_worldbank(country_code: str = "TN") -> dict:
    """
    Récupère indicateurs macro depuis World Bank API.
    country_code : ISO2 (ex: TN=Tunisie, MA=Maroc, DZ=Algérie)
    """

    logger.info(f"[tools] WORLDBANK start — country={country_code}")

    indicators = {
        "gdp_per_capita":        "NY.GDP.PCAP.CD",
        "internet_penetration":  "IT.NET.USER.ZS",
        "mobile_per_100":        "IT.CEL.SETS.P2",
        "population":            "SP.POP.TOTL",
        "youth_population_pct":  "SP.POP.1564.TO.ZS",
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
            logger.warning(f"[tools] WORLDBANK {key} error: {resp}")
            result[key] = None
            continue
        try:
            data = resp.json()
            entries = data[1] if isinstance(data, list) and len(data) > 1 else []
            result[key] = entries[0].get("value") if entries else None
        except Exception as e:
            logger.warning(f"[tools] WORLDBANK {key} parse error: {e}")
            result[key] = None

    logger.info(f"[tools] WORLDBANK done — {result}")
    return result