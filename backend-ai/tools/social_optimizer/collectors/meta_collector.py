from __future__ import annotations

from typing import Any

from tools.social_optimizer.collectors.base_collector import BaseCollector
from tools.social_publishing.meta_client import _graph_get


class MetaCollector(BaseCollector):
    async def fetch_recent_posts(
        self,
        account_ref: dict[str, Any],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        account_ref:
        {
          "platform": "instagram" | "facebook",
          "page_access_token": "...",
          "ig_user_id": "...",         # requis si instagram
          "facebook_page_id": "..."    # requis si facebook
        }
        """
        platform = str(account_ref.get("platform") or "").lower()
        token = str(account_ref.get("page_access_token") or "").strip()
        if not token:
            raise ValueError("page_access_token requis pour MetaCollector")

        if platform == "instagram":
            ig_user_id = str(account_ref.get("ig_user_id") or "").strip()
            if not ig_user_id:
                raise ValueError("ig_user_id requis pour collecte Instagram")
            data = await _graph_get(
                f"{ig_user_id}/media",
                {
                    "fields": "id,caption,media_type,timestamp,permalink",
                    "limit": limit,
                    "access_token": token,
                },
            )
            return list(data.get("data") or [])

        page_id = str(account_ref.get("facebook_page_id") or "").strip()
        if not page_id:
            raise ValueError("facebook_page_id requis pour collecte Facebook")
        data = await _graph_get(
            f"{page_id}/posts",
            {
                "fields": "id,message,created_time,permalink_url,status_type",
                "limit": limit,
                "access_token": token,
            },
        )
        return list(data.get("data") or [])

    async def fetch_post_metrics(
        self,
        account_ref: dict[str, Any],
        post_id: str,
    ) -> dict[str, Any]:
        platform = str(account_ref.get("platform") or "").lower()
        token = str(account_ref.get("page_access_token") or "").strip()
        if not token:
            raise ValueError("page_access_token requis pour MetaCollector")
        if not post_id.strip():
            raise ValueError("post_id requis")

        if platform == "instagram":
            return await _graph_get(
                post_id,
                {
                    "fields": (
                        "id,like_count,comments_count,"
                        "insights.metric(impressions,reach,saved,shares)"
                    ),
                    "access_token": token,
                },
            )

        return await _graph_get(
            post_id,
            {
                "fields": "id,reactions.summary(true),comments.summary(true),shares",
                "access_token": token,
            },
        )

