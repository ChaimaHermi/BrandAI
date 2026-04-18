"""Charge le contexte idée depuis l’API FastAPI backend-api (GET /ideas/{id}, même schéma que le pipeline)."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("brandai.content_idea_fetch")


async def fetch_idea_row(idea_id: int, access_token: str) -> dict[str, Any]:
    base = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")
    url = f"{base}/ideas/{idea_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


def idea_to_content_context(row: dict[str, Any]) -> dict[str, Any]:
    """Extrait un résumé utile pour la rédaction (pas de mock)."""
    desc = (row.get("description") or "").strip()
    return {
        "name": (row.get("name") or "").strip(),
        "description": desc,
        "clarity_short_pitch": (row.get("clarity_short_pitch") or "").strip(),
        "clarity_solution": (row.get("clarity_solution") or "").strip(),
        "clarity_target_users": (row.get("clarity_target_users") or "").strip(),
        "clarity_sector": (row.get("clarity_sector") or row.get("sector") or "").strip(),
        "clarity_language": (row.get("clarity_language") or "fr").strip(),
        "sector": (row.get("sector") or "").strip(),
    }
