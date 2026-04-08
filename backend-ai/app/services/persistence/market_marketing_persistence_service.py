from __future__ import annotations

import os
from datetime import datetime

import httpx


async def persist_market_result(
    *,
    idea_id: int,
    result_json: dict,
    started_at: datetime,
    completed_at: datetime,
    access_token: str,
) -> dict:
    """Persist market analysis result to backend-api."""
    base = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")
    url = f"{base}/market-analysis/{idea_id}"
    payload = {
        "status": "done",
        "result_json": result_json,
        "data_quality_json": result_json.get("data_quality"),
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def persist_marketing_result(
    *,
    idea_id: int,
    result_json: dict,
    access_token: str,
) -> dict:
    """Persist marketing plan result to backend-api."""
    base = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")
    url = f"{base}/marketing-plans/{idea_id}"
    payload = {
        "status": "done",
        "result_json": result_json,
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()
