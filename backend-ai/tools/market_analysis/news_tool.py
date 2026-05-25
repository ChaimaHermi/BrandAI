import logging
import os
import threading

import requests

from observability.langsmith_tracing import trace_sync_tool

NEWS_API_KEY = os.getenv("NEWSAPI_KEY")
logger = logging.getLogger("brandai.market_api")

# Verrou global : un seul appel NewsAPI à la fois, tous agents confondus
_NEWS_LOCK = threading.Semaphore(1)


@trace_sync_tool("market.news_search", tags=["market_analysis", "newsapi"])
def news_search(query: str) -> list:
    with _NEWS_LOCK:
        return _news_search_unlocked(query)


def _news_search_unlocked(query: str) -> list:
    if not NEWS_API_KEY:
        logger.error("[API_KO] provider=NEWSAPI status=missing_key query=%r", (query or "")[:120])
        return []

    url = "https://newsapi.org/v2/everything"
    params = {"q": query, "apiKey": NEWS_API_KEY, "pageSize": 5}

    try:
        res = requests.get(url, params=params, timeout=30)
        res.raise_for_status()
        data = res.json()
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        logger.error("[API_KO] provider=NEWSAPI status=%s query=%r err=%s",
                     status, (query or "")[:120], str(e)[:200])
        return []
    except requests.RequestException as e:
        logger.error("[API_KO] provider=NEWSAPI status=network query=%r err=%s",
                     (query or "")[:120], str(e)[:200])
        return []
    except Exception as e:
        logger.error("[API_KO] provider=NEWSAPI status=unknown query=%r err=%s",
                     (query or "")[:120], str(e)[:200])
        return []

    try:
        return [
            {
                "title":       article.get("title"),
                "description": article.get("description"),
                "url":         article.get("url"),
            }
            for article in (data.get("articles") or [])[:5]
        ]
    except Exception:
        return []
