import os
import requests

from config.market_analysis_config import MARKET_ANALYSIS_CONFIG

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


def tavily_search(query: str):
    try:
        max_results = int(MARKET_ANALYSIS_CONFIG["api"]["tavily"]["max_results"])
    except (KeyError, TypeError, ValueError):
        max_results = 5

    if not TAVILY_API_KEY:
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
    except Exception:
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
