import os
import logging
import requests

from config.market_analysis_config import MARKET_ANALYSIS_CONFIG

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
logger = logging.getLogger("brandai.market_api")


def tavily_search(query: str):
    try:
        max_results = int(MARKET_ANALYSIS_CONFIG["api"]["tavily"]["max_results"])
    except (KeyError, TypeError, ValueError):
        max_results = 5

    if not TAVILY_API_KEY:
        logger.error("[API_KO] provider=TAVILY status=missing_key query=%r", (query or "")[:120])
        return []

    url = "https://api.tavily.com/search"

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "max_results": max_results,
    }

    try:
        res = requests.post(url, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        logger.error(
            "[API_KO] provider=TAVILY status=%s query=%r err=%s",
            status,
            (query or "")[:120],
            str(e)[:200],
        )
        return []
    except requests.RequestException as e:
        logger.error(
            "[API_KO] provider=TAVILY status=network query=%r err=%s",
            (query or "")[:120],
            str(e)[:200],
        )
        return []
    except Exception as e:
        logger.error(
            "[API_KO] provider=TAVILY status=unknown query=%r err=%s",
            (query or "")[:120],
            str(e)[:200],
        )
        return []

    results = []

    try:
        for r in (data.get("results") or [])[:max_results]:
            results.append({
                "title": r.get("title"),
                "content": r.get("content"),
                "url": r.get("url"),
            })
    except Exception:
        return []

    return results
