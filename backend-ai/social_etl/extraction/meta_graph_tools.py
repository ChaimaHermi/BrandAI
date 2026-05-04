"""Utilitaires async communs Graph API Meta (pagination, lectures sûres, insights)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.social_publishing.meta_client import (  # noqa: E402
    MetaGraphError,
    _graph_get,
)


async def safe_graph_get(path: str, params: dict[str, Any]) -> dict[str, Any] | None:
    try:
        return await _graph_get(path, params)
    except Exception:
        return None


async def safe_graph_get_with_error(
    path: str, params: dict[str, Any]
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    try:
        return await _graph_get(path, params), None
    except MetaGraphError as e:
        return None, {"message": str(e), "code": e.code}
    except Exception as e:
        return None, {"message": str(e), "code": None}


async def fetch_graph_collection(
    *,
    path: str,
    params: dict[str, Any],
    max_items: int,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    try:
        data = await _graph_get(path, params)
    except Exception:
        return results

    while True:
        page_items = data.get("data") or []
        if isinstance(page_items, list):
            for item in page_items:
                if isinstance(item, dict):
                    results.append(item)
                if len(results) >= max_items:
                    return results[:max_items]

        next_url = ((data.get("paging") or {}).get("next") or "").strip()
        if not next_url or len(results) >= max_items:
            return results[:max_items]

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.get(next_url)
                data = r.json() if r.content else {}
            if r.status_code != 200:
                return results[:max_items]
        except Exception:
            return results[:max_items]


def extract_insight_value(insights: list[dict[str, Any]] | None, metric_name: str) -> int | None:
    if not insights:
        return None
    for item in insights:
        if not isinstance(item, dict):
            continue
        if str(item.get("name") or "") != metric_name:
            continue
        values = item.get("values")
        if isinstance(values, list) and values:
            raw = values[0] if isinstance(values[0], dict) else {}
            value = raw.get("value") if isinstance(raw, dict) else None
            if isinstance(value, (int, float)):
                return int(value)
    return None
