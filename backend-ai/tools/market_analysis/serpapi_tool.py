import os
import logging
import requests

from config.market_analysis_config import MARKET_ANALYSIS_CONFIG

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
logger = logging.getLogger("brandai.market_api")


def serpapi_search(query: str):
    try:
        max_results = int(MARKET_ANALYSIS_CONFIG["api"]["serp"]["max_results"])
    except (KeyError, TypeError, ValueError):
        max_results = 5

    if not SERPAPI_KEY:
        logger.error("[API_KO] provider=SERPAPI status=missing_key query=%r", (query or "")[:120])
        return []

    url = "https://serpapi.com/search"

    params = {
        "q": query,
        "engine": "google",
        "api_key": SERPAPI_KEY,
        "num": max_results,
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        res.raise_for_status()
        data = res.json()
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        logger.error(
            "[API_KO] provider=SERPAPI status=%s query=%r err=%s",
            status,
            (query or "")[:120],
            str(e)[:200],
        )
        return []
    except requests.RequestException as e:
        logger.error(
            "[API_KO] provider=SERPAPI status=network query=%r err=%s",
            (query or "")[:120],
            str(e)[:200],
        )
        return []
    except Exception as e:
        logger.error(
            "[API_KO] provider=SERPAPI status=unknown query=%r err=%s",
            (query or "")[:120],
            str(e)[:200],
        )
        return []

    results = []

    try:
        organic = data.get("organic_results") or []
        for r in organic[:max_results]:
            results.append({
                "title": r.get("title"),
                "snippet": r.get("snippet"),
                "link": r.get("link"),
            })
    except Exception:
        return []

    return results
