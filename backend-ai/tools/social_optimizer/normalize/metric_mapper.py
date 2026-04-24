from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from tools.social_optimizer.enums import ContentType, Platform
from tools.social_optimizer.normalize.engagement import compute_engagement_rate
from tools.social_optimizer.schemas import NormalizedPostMetric


def _parse_datetime(value: Any, fallback: datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    if not value:
        return fallback
    raw = str(value).strip()
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return fallback


def _to_content_type(platform: Platform, raw_post: dict[str, Any]) -> ContentType:
    if platform == Platform.INSTAGRAM:
        mt = str(raw_post.get("media_type") or "").upper()
        if mt == "IMAGE":
            return ContentType.IMAGE
        if mt == "VIDEO":
            return ContentType.VIDEO
        if mt == "CAROUSEL_ALBUM":
            return ContentType.CAROUSEL
        return ContentType.OTHER

    if platform == Platform.FACEBOOK:
        status_type = str(raw_post.get("status_type") or "").lower()
        if "video" in status_type:
            return ContentType.VIDEO
        if "photo" in status_type:
            return ContentType.IMAGE
        return ContentType.TEXT

    # v1: LinkedIn simplifié à TEXT (à enrichir plus tard via media category)
    return ContentType.TEXT


def _extract_meta_insights(raw_metrics: dict[str, Any]) -> tuple[int, int]:
    impressions = 0
    reach = 0
    insights = raw_metrics.get("insights", {})
    if not isinstance(insights, dict):
        return impressions, reach
    for item in insights.get("data") or []:
        if not isinstance(item, dict):
            continue
        metric_name = str(item.get("name") or "")
        values = item.get("values") or []
        value = 0
        if values and isinstance(values[0], dict):
            value = int(values[0].get("value") or 0)
        if metric_name == "impressions":
            impressions = value
        elif metric_name == "reach":
            reach = value
    return impressions, reach


def _extract_shares(raw_metrics: dict[str, Any]) -> int:
    shares_obj = raw_metrics.get("shares")
    if isinstance(shares_obj, dict):
        return int(shares_obj.get("count") or 0)
    if isinstance(shares_obj, (int, float)):
        return int(shares_obj)
    return int(raw_metrics.get("shareStatistics", {}).get("shareCount") or 0)


def normalize_post(
    *,
    idea_id: int,
    platform: Platform,
    raw_post: dict[str, Any],
    raw_metrics: dict[str, Any],
    collected_at: datetime | None = None,
) -> NormalizedPostMetric:
    collected_at = collected_at or datetime.now(timezone.utc)

    external_post_id = str(raw_post.get("id") or raw_metrics.get("id") or "").strip()
    if not external_post_id:
        raise ValueError("external_post_id introuvable dans raw_post/raw_metrics")

    published_raw = (
        raw_post.get("timestamp")
        or raw_post.get("created_time")
        or raw_post.get("lastModified")
    )
    published_at = _parse_datetime(published_raw, collected_at)

    likes = int(
        raw_metrics.get("like_count")
        or raw_metrics.get("reactions", {}).get("summary", {}).get("total_count")
        or 0
    )
    comments = int(
        raw_metrics.get("comments_count")
        or raw_metrics.get("comments", {}).get("summary", {}).get("total_count")
        or raw_metrics.get("commentsSummary", {}).get("totalFirstLevelComments")
        or 0
    )
    shares = _extract_shares(raw_metrics)

    impressions, reach = _extract_meta_insights(raw_metrics)
    engagement_rate = compute_engagement_rate(impressions, likes, comments, shares)

    return NormalizedPostMetric(
        idea_id=idea_id,
        platform=platform,
        external_post_id=external_post_id,
        published_at=published_at,
        content_type=_to_content_type(platform, raw_post),
        reach=reach,
        impressions=impressions,
        likes=likes,
        comments=comments,
        shares=shares,
        engagement_rate=engagement_rate,
        collected_at=collected_at,
    )

