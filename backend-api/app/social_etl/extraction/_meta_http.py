"""Helpers HTTP minimaux pour appeler la Meta Graph API depuis le pipeline ETL.

Volontairement decouple du module `tools.social_publishing.meta_client` du
backend-ai, qui contient en plus toute la logique OAuth/publication. Ici on
n'a besoin que des helpers de lecture (`_graph_get`) et de la classe d'erreur.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

GRAPH_API_VERSION = os.getenv("META_GRAPH_API_VERSION", "v25.0")
BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class MetaGraphError(RuntimeError):
    def __init__(self, message: str, code: str | int | None = None):
        self.code = code
        super().__init__(message)


async def _graph_get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(f"{BASE}/{path.lstrip('/')}", params=params)
        data = r.json() if r.content else {}
    if r.status_code != 200:
        err = data.get("error") or {}
        raise MetaGraphError(
            err.get("message", f"Graph GET {r.status_code}"),
            err.get("code"),
        )
    return data


async def get_instagram_business_account_id(
    page_id: str, page_access_token: str
) -> str:
    data = await _graph_get(
        page_id,
        {
            "fields": "instagram_business_account",
            "access_token": page_access_token,
        },
    )
    ig = data.get("instagram_business_account") or {}
    ig_id = ig.get("id")
    if not ig_id:
        raise MetaGraphError(
            "Aucun compte Instagram professionnel lié à cette Page Facebook."
        )
    return str(ig_id)


async def fetch_meta_post_metrics(
    *,
    platform: str,
    page_access_token: str,
    post_id: str,
) -> dict[str, Any]:
    """Recupere les metriques d'un post (Facebook ou Instagram)."""
    pf = (platform or "").strip().lower()
    if not page_access_token:
        raise ValueError("page_access_token requis")
    if not post_id.strip():
        raise ValueError("post_id requis")

    if pf == "instagram":
        return await _graph_get(
            post_id,
            {
                "fields": (
                    "id,like_count,comments_count,"
                    "insights.metric(impressions,reach,saved,shares)"
                ),
                "access_token": page_access_token,
            },
        )

    return await _graph_get(
        post_id,
        {
            "fields": "id,reactions.summary(true),comments.summary(true),shares",
            "access_token": page_access_token,
        },
    )


async def fetch_meta_recent_posts(
    *,
    platform: str,
    page_access_token: str,
    ig_user_id: str | None = None,
    facebook_page_id: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Liste les posts recents (Facebook ou Instagram). Equivalent leger du
    `MetaCollector.fetch_recent_posts` de backend-ai, sans dependance externe."""
    pf = (platform or "").strip().lower()
    if not page_access_token:
        raise ValueError("page_access_token requis")

    if pf == "instagram":
        if not ig_user_id:
            raise ValueError("ig_user_id requis pour collecte Instagram")
        data = await _graph_get(
            f"{ig_user_id}/media",
            {
                "fields": "id,caption,media_type,timestamp,permalink",
                "limit": limit,
                "access_token": page_access_token,
            },
        )
        return list(data.get("data") or [])

    if not facebook_page_id:
        raise ValueError("facebook_page_id requis pour collecte Facebook")
    data = await _graph_get(
        f"{facebook_page_id}/posts",
        {
            "fields": "id,message,created_time,permalink_url,status_type",
            "limit": limit,
            "access_token": page_access_token,
        },
    )
    return list(data.get("data") or [])
