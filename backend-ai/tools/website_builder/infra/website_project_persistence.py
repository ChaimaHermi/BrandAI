from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from config.website_builder_config import BACKEND_API_BASE_URL, BACKEND_API_TIMEOUT_SECONDS


def _auth_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


async def _request_json(
    method: str,
    path: str,
    *,
    access_token: str,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{BACKEND_API_BASE_URL}{path}"
    timeout = httpx.Timeout(BACKEND_API_TIMEOUT_SECONDS, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.request(
            method=method.upper(),
            url=url,
            headers=_auth_headers(access_token),
            json=json_body,
        )
    resp.raise_for_status()
    if not resp.content:
        return {}
    return resp.json() or {}


def build_message(
    *,
    role: str,
    msg_type: str,
    content: str,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "role": role,
        "type": msg_type,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if meta is not None:
        payload["meta"] = meta
    return payload


async def patch_website_project(
    *,
    idea_id: int,
    access_token: str,
    patch: dict[str, Any],
) -> dict[str, Any]:
    return await _request_json(
        "PATCH",
        f"/website/ideas/{idea_id}",
        access_token=access_token,
        json_body=patch,
    )


async def append_website_message(
    *,
    idea_id: int,
    access_token: str,
    message: dict[str, Any],
) -> dict[str, Any]:
    return await _request_json(
        "POST",
        f"/website/ideas/{idea_id}/messages",
        access_token=access_token,
        json_body=message,
    )

