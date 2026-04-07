import os
import requests

from config.market_analysis_config import MARKET_ANALYSIS_CONFIG

SCRAPE_DO_API_KEY = os.getenv("SCRAPE_DO_API_KEY")


def scrape_page(url: str):
    try:
        scrape_cfg = MARKET_ANALYSIS_CONFIG["api"]["scrape"]
        enabled = bool(scrape_cfg.get("enabled", True))
        max_chars = int(scrape_cfg.get("max_chars_per_page", 3000))
    except (KeyError, TypeError, ValueError):
        enabled = True
        max_chars = 3000

    if not url:
        return {"url": url or "", "content": ""}

    if not enabled:
        return {"url": url, "content": ""}

    endpoint = "http://api.scrape.do"

    params = {
        "token": SCRAPE_DO_API_KEY,
        "url": url,
        "render": "true",
    }

    try:
        res = requests.get(endpoint, params=params, timeout=15)
        res.raise_for_status()
        text = res.text or ""
        if max_chars > 0:
            text = text[:max_chars]
        return {"url": url, "content": text}
    except Exception:
        return {"url": url, "content": ""}
