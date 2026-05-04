"""
Extraction Facebook (Graph API) — async, sans OAuth ni persistance fichier.

`access_token` : jeton Page (long-lived) déjà stocké côté app.
`account_id`   : identifiant de la Page Facebook.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from social_etl.extraction.meta_graph_tools import (  # noqa: E402
    extract_insight_value,
    fetch_graph_collection,
    safe_graph_get,
    safe_graph_get_with_error,
)
from social_etl.extraction.meta_insights_constants import (  # noqa: E402
    FACEBOOK_PAGE_INSIGHT_METRICS,
    FACEBOOK_POST_INSIGHT_METRICS,
)
from tools.social_optimizer.collectors.meta_collector import MetaCollector  # noqa: E402
from tools.social_publishing.meta_client import BASE  # noqa: E402


async def _fetch_insights_metrics_debug(
    *,
    object_id: str,
    metrics: list[str],
    access_token: str,
    period: str | None = None,
) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
    combined: list[dict[str, Any]] = []
    accepted: list[str] = []
    rejected: list[dict[str, Any]] = []

    for metric in metrics:
        params: dict[str, str] = {"metric": metric, "access_token": access_token}
        if period:
            params["period"] = period
        data, err = await safe_graph_get_with_error(f"{object_id}/insights", params)
        if data and isinstance(data.get("data"), list):
            rows = [x for x in (data.get("data") or []) if isinstance(x, dict)]
            if rows:
                combined.extend(rows)
                accepted.append(metric)
                continue
        rejected.append({"metric": metric, "error": err})

    debug = {
        "requested_metrics": metrics,
        "accepted_metrics": accepted,
        "rejected_metrics": rejected,
    }
    return (combined or None), debug


def _facebook_post_type_api(post: dict[str, Any]) -> str:
    status_type = str(post.get("status_type") or "").strip().lower()
    attachments = post.get("attachments")
    if isinstance(attachments, dict):
        data = attachments.get("data")
        if isinstance(data, list) and data:
            first = data[0] if isinstance(data[0], dict) else {}
            media_type = str(first.get("media_type") or "").strip().lower()
            typ = str(first.get("type") or "").strip().lower()
            if "video" in media_type or "video" in typ:
                return "video"
            if "photo" in media_type or "photo" in typ:
                return "image"
            if "album" in media_type or "album" in typ or "carousel" in typ:
                return "carousel"
            if "link" in typ:
                return "link"
    if "video" in status_type:
        return "video"
    if "photo" in status_type:
        return "image"
    if "link" in status_type:
        return "link"
    if status_type:
        return status_type
    return "unknown"


def _has_post_like_content(item: dict[str, Any]) -> bool:
    return bool(
        (item.get("message") or "").strip()
        or item.get("attachments")
        or item.get("full_picture")
        or (item.get("story") or "").strip()
    )


def _is_system_story(item: dict[str, Any]) -> bool:
    story_text = str(item.get("story") or "").lower()
    return (
        "a changé sa photo de profil" in story_text
        or "a changé sa photo de couverture" in story_text
    )


async def _fetch_page_posts_with_fallback(
    *,
    page_id: str,
    page_token: str,
    limit: int,
) -> list[dict[str, Any]]:
    posts_fields_min = "id,message,created_time,permalink_url"
    posts_fields_feed = (
        "id,message,story,created_time,permalink_url,status_type,"
        "full_picture,attachments{media_type,type,url,target,media}"
    )
    candidates: list[tuple[str, str, int, int, str]] = [
        (
            "published_posts",
            f"{page_id}/published_posts",
            min(limit, 100),
            max(limit * 3, 30),
            posts_fields_min,
        ),
        (
            "posts",
            f"{page_id}/posts",
            min(limit, 100),
            max(limit * 3, 30),
            posts_fields_min,
        ),
        (
            "feed",
            f"{page_id}/feed",
            min(max(limit * 3, 30), 100),
            max(limit * 6, 60),
            posts_fields_feed,
        ),
    ]

    merged: dict[str, dict[str, Any]] = {}
    for _source_name, source_path, req_limit, max_items, fields in candidates:
        rows = await fetch_graph_collection(
            path=source_path,
            params={
                "fields": fields,
                "limit": req_limit,
                "access_token": page_token,
            },
            max_items=max_items,
        )
        for row in rows:
            if not isinstance(row, dict):
                continue
            post_id = str(row.get("id") or "").strip()
            if not post_id:
                continue
            if not _has_post_like_content(row):
                continue
            if _is_system_story(row):
                continue
            if post_id not in merged:
                merged[post_id] = row

    ordered = sorted(
        merged.values(),
        key=lambda x: str(x.get("created_time") or ""),
        reverse=True,
    )
    return ordered[:limit]


async def extract_facebook(
    access_token: str,
    account_id: str,
    *,
    limit: int = 10,
    comments_limit: int = 100,
    reactions_limit: int = 100,
) -> dict[str, Any]:
    """
    Récupère métadonnées Page, insights, posts et engagements (schéma
    ``facebook_extract_result.json`` / normalisation ``build_normalized_facebook``).
    """
    page_id = str(account_id).strip()
    page_token = str(access_token).strip()
    if not page_id or not page_token:
        raise ValueError("access_token et account_id sont requis.")

    page = await safe_graph_get(
        page_id,
        {"fields": "id,name", "access_token": page_token},
    )
    page_name = str((page or {}).get("name") or "")

    posts = await _fetch_page_posts_with_fallback(
        page_id=page_id, page_token=page_token, limit=limit
    )

    collector = MetaCollector()
    account_ref: dict[str, Any] = {
        "platform": "facebook",
        "page_access_token": page_token,
        "facebook_page_id": page_id,
    }

    page_metrics = await safe_graph_get(
        page_id,
        {
            "fields": "id,name,category,link,fan_count,followers_count,verification_status",
            "access_token": page_token,
        },
    )
    page_insights_data, page_insights_debug = await _fetch_insights_metrics_debug(
        object_id=page_id,
        metrics=FACEBOOK_PAGE_INSIGHT_METRICS,
        access_token=page_token,
        period="day",
    )

    posts_detailed: list[dict[str, Any]] = []
    aggregate_post_reach = 0
    aggregate_post_impressions = 0
    aggregate_post_likes = 0
    aggregate_post_comments = 0
    aggregate_post_shares = 0
    aggregate_post_interactions = 0
    reach_known_count = 0
    impressions_known_count = 0

    for post in posts:
        post_id = str(post.get("id") or "").strip()
        if not post_id:
            continue

        metrics: dict[str, Any] | None = None
        try:
            metrics = await collector.fetch_post_metrics(account_ref, post_id)
        except Exception:
            metrics = None

        comments = await fetch_graph_collection(
            path=f"{post_id}/comments",
            params={
                "fields": (
                    "id,from{id,name},message,created_time,"
                    "like_count,comment_count,permalink_url,attachment,"
                    "comments.limit(50){id,from{id,name},message,created_time,like_count}"
                ),
                "limit": min(comments_limit, 100),
                "access_token": page_token,
            },
            max_items=comments_limit,
        )
        if not comments:
            comments = None

        post_insights, post_insights_debug = await _fetch_insights_metrics_debug(
            object_id=post_id,
            metrics=FACEBOOK_POST_INSIGHT_METRICS,
            access_token=page_token,
        )

        reactions = await fetch_graph_collection(
            path=f"{post_id}/reactions",
            params={
                "fields": "id,name,type",
                "limit": min(reactions_limit, 100),
                "access_token": page_token,
            },
            max_items=reactions_limit,
        )
        if not reactions:
            reactions = None

        reactions_count = int(
            ((metrics or {}).get("reactions") or {}).get("summary", {}).get("total_count") or 0
        )
        comments_count = int(
            ((metrics or {}).get("comments") or {}).get("summary", {}).get("total_count") or 0
        )
        shares_count = int((((metrics or {}).get("shares") or {}).get("count") or 0))
        interactions_total = reactions_count + comments_count + shares_count
        post_reach = extract_insight_value(post_insights, "post_impressions_unique")
        post_impressions = extract_insight_value(post_insights, "post_impressions")

        if post_reach is not None:
            aggregate_post_reach += post_reach
            reach_known_count += 1
        if post_impressions is not None:
            aggregate_post_impressions += post_impressions
            impressions_known_count += 1
        aggregate_post_likes += reactions_count
        aggregate_post_comments += comments_count
        aggregate_post_shares += shares_count
        aggregate_post_interactions += interactions_total

        posts_detailed.append(
            {
                "post": post,
                "post_type_api": _facebook_post_type_api(post),
                "metrics": metrics,
                "post_insights": post_insights,
                "post_insights_debug": post_insights_debug,
                "comments": comments,
                "reactions": reactions,
                "comments_count_fetched": (
                    len([c for c in comments if isinstance(c, dict) and c.get("id")])
                    if comments
                    else None
                ),
                "reactions_count_fetched": (
                    len([r for r in reactions if isinstance(r, dict) and r.get("id")])
                    if reactions
                    else None
                ),
                "interactions": {
                    "reactions_count": reactions_count,
                    "comments_count": comments_count,
                    "shares_count": shares_count,
                    "interactions_total": interactions_total,
                    "reach": post_reach,
                    "impressions": post_impressions,
                },
            }
        )

    page_followers = int((page_metrics or {}).get("followers_count") or 0)
    page_likes = int((page_metrics or {}).get("fan_count") or 0)
    page_reach_daily = extract_insight_value(page_insights_data, "page_impressions_unique")
    page_impressions_daily = extract_insight_value(page_insights_data, "page_impressions")
    page_post_engagements_daily = extract_insight_value(
        page_insights_data, "page_post_engagements"
    )

    return {
        "platform": "facebook",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "page": {"id": page_id, "name": page_name or (page or {}).get("name")},
        "page_metrics": page_metrics,
        "page_insights": page_insights_data,
        "page_insights_debug": page_insights_debug,
        "page_social": {
            "followers_count": page_followers or None,
            "likes_count": page_likes or None,
            "reach_daily": page_reach_daily,
            "impressions_daily": page_impressions_daily,
            "post_engagements_daily": page_post_engagements_daily,
        },
        "posts_count": len(posts),
        "posts": posts,
        "posts_detailed": posts_detailed,
        "posts_social_totals": {
            "likes_count": aggregate_post_likes,
            "comments_count": aggregate_post_comments,
            "shares_count": aggregate_post_shares,
            "interactions_total": aggregate_post_interactions,
            "reach_total_known_posts": aggregate_post_reach if reach_known_count else None,
            "impressions_total_known_posts": (
                aggregate_post_impressions if impressions_known_count else None
            ),
            "reach_known_posts_count": reach_known_count,
            "impressions_known_posts_count": impressions_known_count,
        },
        "extract_config": {
            "posts_limit": limit,
            "comments_limit_per_post": comments_limit,
            "reactions_limit_per_post": reactions_limit,
            "null_when_unavailable": True,
        },
        "api_base": BASE,
    }
