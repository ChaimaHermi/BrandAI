from __future__ import annotations

from typing import Any

from normalize_common import (
    NORMALIZED_DIR,
    RESULTS_DIR,
    dump_json,
    load_json,
    parse_dt,
    safe_int,
)


def _insight_value(insights: list[dict[str, Any]] | None, name: str) -> int | None:
    if not insights:
        return None
    for item in insights:
        if not isinstance(item, dict) or str(item.get("name") or "") != name:
            continue
        values = item.get("values")
        if isinstance(values, list) and values:
            first = values[0] if isinstance(values[0], dict) else {}
            if isinstance(first.get("value"), (int, float)):
                return int(first["value"])
    return None


def _iso_published_at(value: Any) -> str | None:
    dt = parse_dt(value)
    if dt:
        return dt.isoformat()
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _opt_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.strip():
        try:
            return int(float(value.strip()))
        except ValueError:
            return None
    return None


def _instagram_video_views(insights: list[dict[str, Any]] | None) -> int | None:
    for name in ("video_views", "plays"):
        v = _insight_value(insights, name)
        if v is not None:
            return v
    return None


def normalize_instagram_data(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Transforme la sortie ``extract_instagram`` en structure alignée sur ``social_posts``.

    Pas de réactions détaillées (seulement likes côté API).
    """
    media_detailed = raw.get("media_detailed") if isinstance(raw.get("media_detailed"), list) else []
    normalized_posts: list[dict[str, Any]] = []
    for row in media_detailed:
        if not isinstance(row, dict):
            continue
        media = row.get("media") if isinstance(row.get("media"), dict) else {}
        interactions = row.get("interactions") if isinstance(row.get("interactions"), dict) else {}
        insights = row.get("insights") if isinstance(row.get("insights"), list) else None

        mid = media.get("id")
        if mid is None:
            continue

        caption = media.get("caption")
        text = caption.strip() if isinstance(caption, str) else None
        if text == "":
            text = None

        media_type = str(row.get("post_type_api") or "unknown")
        media_url_raw = media.get("media_url")
        media_url = media_url_raw.strip() if isinstance(media_url_raw, str) and media_url_raw.strip() else None
        permalink_raw = media.get("permalink")
        permalink_url = permalink_raw.strip() if isinstance(permalink_raw, str) and permalink_raw.strip() else None

        likes = (
            safe_int(media.get("like_count"))
            if media.get("like_count") is not None
            else safe_int(interactions.get("likes_count"))
        )
        comments = (
            safe_int(media.get("comments_count"))
            if media.get("comments_count") is not None
            else safe_int(interactions.get("comments_count"))
        )

        shares_val = _insight_value(insights, "shares")
        saves = _insight_value(insights, "saved")
        reach = _opt_int(interactions.get("reach"))
        impressions = _opt_int(interactions.get("impressions"))
        video_views = _instagram_video_views(insights) if media_type == "video" else None

        normalized_posts.append(
            {
                "post_external_id": str(mid),
                "published_at": _iso_published_at(media.get("timestamp")),
                "text": text,
                "media_type": media_type,
                "media_url": media_url,
                "permalink_url": permalink_url,
                "likes": likes,
                "comments": comments,
                "shares": shares_val if shares_val is not None else None,
                "saves": saves,
                "clicks": None,
                "reach": reach,
                "impressions": impressions,
                "video_views": video_views,
                "reactions_like": None,
                "reactions_love": None,
                "reactions_haha": None,
                "reactions_wow": None,
                "reactions_sad": None,
                "reactions_angry": None,
            }
        )

    ig_social = raw.get("instagram_social") if isinstance(raw.get("instagram_social"), dict) else {}
    followers = ig_social.get("followers_count")
    if not isinstance(followers, (int, float)) and followers is not None:
        followers = None
    elif isinstance(followers, (int, float)):
        followers = int(followers)

    return {
        "platform": "instagram",
        "followers_count": followers,
        "posts_count": len(normalized_posts),
        "posts": normalized_posts,
    }


def build_normalized_instagram(raw: dict[str, Any]) -> dict[str, Any]:
    """Alias rétrocompatible : même sortie que ``normalize_instagram_data``."""
    return normalize_instagram_data(raw)


def main() -> None:
    src = RESULTS_DIR / "instagram_extract_result.json"
    raw = load_json(src)
    out = normalize_instagram_data(raw)
    dump_json(NORMALIZED_DIR / "instagram_normalized.json", out)
    print(f"normalized instagram -> {NORMALIZED_DIR / 'instagram_normalized.json'}")


if __name__ == "__main__":
    main()
