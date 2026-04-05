import os
import requests

from config.market_analysis_config import MARKET_ANALYSIS_CONFIG

SERPAPI_KEY = os.getenv("SERPAPI_KEY")


def serpapi_search(query: str):
    try:
        max_results = int(MARKET_ANALYSIS_CONFIG["api"]["serp"]["max_results"])
    except (KeyError, TypeError, ValueError):
        max_results = 5

    if not SERPAPI_KEY:
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
    except Exception:
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
