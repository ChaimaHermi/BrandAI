from __future__ import annotations

from typing import Any

import httpx

from tools.social_optimizer.collectors.base_collector import BaseCollector


class LinkedInCollector(BaseCollector):
    async def fetch_recent_posts(
        self,
        account_ref: dict[str, Any],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        account_ref:
        {
          "access_token": "...",
          "author_urn": "urn:li:person:xxxx" | "urn:li:organization:xxxx"
        }
        """
        token = str(account_ref.get("access_token") or "").strip()
        author_urn = str(account_ref.get("author_urn") or "").strip()
        if not token or not author_urn:
            raise ValueError("access_token et author_urn sont requis")

        url = "https://api.linkedin.com/v2/ugcPosts"
        params = {
            "q": "authors",
            "authors": f"List({author_urn})",
            "count": limit,
            "sortBy": "LAST_MODIFIED",
        }
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.get(url, params=params, headers=headers)
            r.raise_for_status()
            data = r.json() if r.content else {}
        return list(data.get("elements") or [])

    async def fetch_post_metrics(
        self,
        account_ref: dict[str, Any],
        post_id: str,
    ) -> dict[str, Any]:
        token = str(account_ref.get("access_token") or "").strip()
        if not token or not post_id.strip():
            raise ValueError("access_token et post_id sont requis")

        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://api.linkedin.com/v2/socialActions/{post_id}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
            return r.json() if r.content else {}

