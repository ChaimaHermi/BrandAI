"""
Extraction Instagram Business (Graph API) — async, sans OAuth ni fichier.

`access_token` : jeton Page Facebook associé au compte professionnel Instagram.
`account_id`   : identifiant de la Page Facebook **ou** identifiant du compte
                 Instagram Business (IG user id).
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
    safe_graph_get_with_error,
)
from social_etl.extraction.meta_insights_constants import (  # noqa: E402
    INSTAGRAM_ACCOUNT_INSIGHT_METRICS,
    INSTAGRAM_MEDIA_INSIGHT_METRICS,
)
from tools.social_publishing.meta_client import (  # noqa: E402
    MetaGraphError,
    get_instagram_business_account_id,
)


async def _fetch_ig_insights_metrics_debug(
    *,
    object_id: str,
    metrics: list[str],
    access_token: str,
    period: str | None = None,
    use_fields_syntax: bool = False,
) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
    combined: list[dict[str, Any]] = []
    accepted: list[str] = []
    rejected: list[dict[str, Any]] = []

    for metric in metrics:
        if use_fields_syntax:
            params: dict[str, str] = {
                "fields": f"insights.metric({metric})",
                "access_token": access_token,
            }
            data, err = await safe_graph_get_with_error(object_id, params)
            rows = None
            if data and isinstance((data.get("insights") or {}).get("data"), list):
                rows = [
                    x for x in (data.get("insights") or {}).get("data") if isinstance(x, dict)
                ]
        else:
            params = {"metric": metric, "access_token": access_token}
            if period:
                params["period"] = period
            data, err = await safe_graph_get_with_error(f"{object_id}/insights", params)
            rows = (
                [x for x in (data.get("data") or []) if isinstance(x, dict)]
                if data and isinstance(data.get("data"), list)
                else None
            )

        if rows:
            combined.extend(rows)
            accepted.append(metric)
        else:
            rejected.append({"metric": metric, "error": err})

    debug = {
        "requested_metrics": metrics,
        "accepted_metrics": accepted,
        "rejected_metrics": rejected,
    }
    return (combined or None), debug


def _instagram_post_type_api(media: dict[str, Any]) -> str:
    media_type = str(media.get("media_type") or "").strip().upper()
    if media_type == "IMAGE":
        return "image"
    if media_type == "VIDEO":
        return "video"
    if media_type == "CAROUSEL_ALBUM":
        return "carousel"
    return "unknown"


async def _resolve_page_and_ig_user(
    access_token: str, account_id: str
) -> tuple[str, str, str]:
    """
    Retourne (facebook_page_id, facebook_page_name, instagram_user_id).
    Essaie d'abord `account_id` comme Page Facebook ; sinon comme IG user id.
    """
    token = str(access_token).strip()
    aid = str(account_id).strip()

    page_probe, _ = await safe_graph_get_with_error(
        aid,
        {"fields": "id,name,instagram_business_account", "access_token": token},
    )
    if page_probe and page_probe.get("id"):
        pid = str(page_probe["id"])
        pname = str(page_probe.get("name") or "")
        ig = page_probe.get("instagram_business_account") or {}
        if isinstance(ig, dict) and ig.get("id"):
            return pid, pname, str(ig["id"])
        try:
            ig_id = await get_instagram_business_account_id(pid, token)
            return pid, pname, ig_id
        except MetaGraphError:
            pass

    ig_probe, ig_err = await safe_graph_get_with_error(
        aid,
        {
            "fields": "id,username,name,followers_count,follows_count,media_count",
            "access_token": token,
        },
    )
    if ig_probe and ig_probe.get("id"):
        uname = str(ig_probe.get("username") or ig_probe.get("name") or "")
        return "", uname, str(ig_probe["id"])

    raise MetaGraphError(
        "Impossible de résoudre le compte Instagram : account_id doit être une Page "
        f"Facebook liée à Instagram ou un IG user id valide. Détails: {ig_err}"
    )


async def extract_instagram(
    access_token: str,
    account_id: str,
    *,
    limit: int = 10,
    comments_limit: int = 100,
) -> dict[str, Any]:
    """
    Récupère compte IG, insights compte/médias, commentaires (même forme que
    `instagram_extract_result.json`).
    """
    page_token = str(access_token).strip()
    if not page_token:
        raise ValueError("access_token est requis.")

    page_id, page_name, ig_user_id = await _resolve_page_and_ig_user(page_token, account_id)

    page_block = {"id": page_id or ig_user_id, "name": page_name or None}

    ig_account, ig_account_error = await safe_graph_get_with_error(
        ig_user_id,
        {
            "fields": "id,username,name,followers_count,follows_count,media_count",
            "access_token": page_token,
        },
    )
    ig_account_insights_data, ig_account_insights_debug = await _fetch_ig_insights_metrics_debug(
        object_id=ig_user_id,
        metrics=INSTAGRAM_ACCOUNT_INSIGHT_METRICS,
        access_token=page_token,
        period="day",
    )

    media = await fetch_graph_collection(
        path=f"{ig_user_id}/media",
        params={
            "fields": (
                "id,caption,media_type,media_url,permalink,timestamp,thumbnail_url,"
                "like_count,comments_count"
            ),
            "limit": min(limit, 100),
            "access_token": page_token,
        },
        max_items=limit,
    )

    detailed: list[dict[str, Any]] = []
    total_likes = 0
    total_comments = 0
    total_interactions = 0
    total_reach_known = 0
    total_impressions_known = 0
    total_engagement_known = 0
    reach_known_count = 0
    impressions_known_count = 0
    engagement_known_count = 0

    for item in media:
        media_id = str(item.get("id") or "").strip()
        if not media_id:
            continue

        insights_data, insights_debug = await _fetch_ig_insights_metrics_debug(
            object_id=media_id,
            metrics=INSTAGRAM_MEDIA_INSIGHT_METRICS,
            access_token=page_token,
            use_fields_syntax=True,
        )

        comments = await fetch_graph_collection(
            path=f"{media_id}/comments",
            params={
                "fields": (
                    "id,text,timestamp,username,like_count,replies_count,"
                    "replies{id,text,timestamp,username,like_count}"
                ),
                "limit": min(comments_limit, 100),
                "access_token": page_token,
            },
            max_items=comments_limit,
        )
        if not comments:
            comments = None

        like_count = int(item.get("like_count") or 0)
        comments_count = int(item.get("comments_count") or 0)
        reach = extract_insight_value(insights_data, "reach")
        impressions = extract_insight_value(insights_data, "impressions")
        engagement = extract_insight_value(insights_data, "engagement")
        interactions_total = like_count + comments_count

        total_likes += like_count
        total_comments += comments_count
        total_interactions += interactions_total
        if reach is not None:
            total_reach_known += reach
            reach_known_count += 1
        if impressions is not None:
            total_impressions_known += impressions
            impressions_known_count += 1
        if engagement is not None:
            total_engagement_known += engagement
            engagement_known_count += 1

        detailed.append(
            {
                "media": item,
                "post_type_api": _instagram_post_type_api(item),
                "insights": insights_data,
                "insights_debug": insights_debug,
                "comments": comments,
                "comments_count_fetched": len(comments) if comments else None,
                "interactions": {
                    "likes_count": like_count,
                    "comments_count": comments_count,
                    "interactions_total": interactions_total,
                    "reach": reach,
                    "impressions": impressions,
                    "engagement": engagement,
                },
            }
        )

    followers_count = int((ig_account or {}).get("followers_count") or 0)
    follows_count = int((ig_account or {}).get("follows_count") or 0)
    media_count_total = int((ig_account or {}).get("media_count") or 0)
    account_reach_daily = extract_insight_value(ig_account_insights_data, "reach")
    account_impressions_daily = extract_insight_value(ig_account_insights_data, "impressions")
    account_profile_views_daily = extract_insight_value(
        ig_account_insights_data, "profile_views"
    )

    return {
        "platform": "instagram",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "page": page_block,
        "instagram_user_id": ig_user_id,
        "instagram_account": ig_account,
        "instagram_account_error": ig_account_error,
        "instagram_account_insights": ig_account_insights_data,
        "instagram_account_insights_debug": ig_account_insights_debug,
        "instagram_social": {
            "followers_count": followers_count or None,
            "follows_count": follows_count or None,
            "media_count": media_count_total or None,
            "reach_daily": account_reach_daily,
            "impressions_daily": account_impressions_daily,
            "profile_views_daily": account_profile_views_daily,
        },
        "media_count": len(media),
        "media": media,
        "media_detailed": detailed,
        "media_social_totals": {
            "likes_count": total_likes,
            "comments_count": total_comments,
            "interactions_total": total_interactions,
            "reach_total_known_media": total_reach_known if reach_known_count else None,
            "impressions_total_known_media": (
                total_impressions_known if impressions_known_count else None
            ),
            "engagement_total_known_media": (
                total_engagement_known if engagement_known_count else None
            ),
            "reach_known_media_count": reach_known_count,
            "impressions_known_media_count": impressions_known_count,
            "engagement_known_media_count": engagement_known_count,
        },
        "extract_config": {
            "media_limit": limit,
            "comments_limit_per_media": comments_limit,
            "null_when_unavailable": True,
        },
    }
