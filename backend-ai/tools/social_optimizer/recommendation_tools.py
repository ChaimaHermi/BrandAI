"""Data tools for social optimizer recommendations."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import asyncpg
import httpx
from langsmith import traceable

BACKEND_API_BASE_URL = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")


def _normalize_platform(platform: str) -> str:
    pf = (platform or "global").strip().lower()
    return pf if pf in ("global", "facebook", "instagram", "linkedin") else "global"


@traceable(name="social_optimizer.tool.get_project_context", run_type="tool", tags=["social_optimizer", "tool", "db"])
async def get_project_context(idea_id: int, access_token: str) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(f"{BACKEND_API_BASE_URL}/ideas/{idea_id}", headers=headers)
        r.raise_for_status()
        data = r.json()
    return {
        "idea_id": data.get("id"),
        "name": data.get("name"),
        "sector": data.get("sector"),
        "description": data.get("description"),
    }


@traceable(name="social_optimizer.tool.get_current_kpis", run_type="tool", tags=["social_optimizer", "tool", "db"])
async def get_current_kpis(idea_id: int, platform: str, access_token: str) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {access_token}"}
    pf = _normalize_platform(platform)
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(
            f"{BACKEND_API_BASE_URL}/ideas/{idea_id}/optimizer/stats",
            params={"platform": pf},
            headers=headers,
        )
        r.raise_for_status()
        return r.json()


async def _get_conn() -> asyncpg.Connection:
    dsn = (os.getenv("DATABASE_URL") or "").strip()
    if not dsn:
        raise RuntimeError("DATABASE_URL manquant pour enregistrer les recommandations.")
    return await asyncpg.connect(dsn=dsn)


@traceable(name="social_optimizer.tool.get_latest_recommendation", run_type="tool", tags=["social_optimizer", "tool", "db"])
async def get_latest_recommendation(idea_id: int, platform: str) -> dict[str, Any] | None:
    pf = _normalize_platform(platform)
    conn = await _get_conn()
    try:
        row = await conn.fetchrow(
            """
            SELECT id, idea_id, platform, generated_at, content
            FROM recommandation_result
            WHERE idea_id = $1 AND platform = $2
            ORDER BY generated_at DESC, id DESC
            LIMIT 1
            """,
            int(idea_id),
            pf,
        )
        return dict(row) if row else None
    finally:
        await conn.close()


@traceable(name="social_optimizer.tool.save_recommendation", run_type="tool", tags=["social_optimizer", "tool", "db"])
async def save_recommendation(idea_id: int, platform: str, content: str) -> dict[str, Any]:
    pf = _normalize_platform(platform)
    conn = await _get_conn()
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO recommandation_result (idea_id, platform, generated_at, content)
            VALUES ($1, $2, NOW(), $3)
            RETURNING id, idea_id, platform, generated_at, content
            """,
            int(idea_id),
            pf,
            str(content or ""),
        )
        out = dict(row)
        if not isinstance(out.get("generated_at"), datetime):
            out["generated_at"] = datetime.utcnow()
        return out
    finally:
        await conn.close()

