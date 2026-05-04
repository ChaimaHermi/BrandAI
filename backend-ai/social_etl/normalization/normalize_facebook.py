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


def _facebook_media_type_from_post(post: dict[str, Any], post_type_api: str) -> str:
    t = str(post_type_api or "").strip().lower()
    if t and t != "unknown":
        return t
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


def normalize_facebook_data(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Transforme la sortie ``extract_facebook`` en structure alignée sur ``social_posts``.

    Retourne ``platform``, ``followers_count``, ``posts`` (sans écriture fichier).
    """
    posts_detailed = raw.get("posts_detailed") if isinstance(raw.get("posts_detailed"), list) else []
    normalized_posts: list[dict[str, Any]] = []
    for row in posts_detailed:
        if not isinstance(row, dict):
            continue
        post = row.get("post") if isinstance(row.get("post"), dict) else {}
        interactions = row.get("interactions") if isinstance(row.get("interactions"), dict) else {}
        post_insights = row.get("post_insights") if isinstance(row.get("post_insights"), list) else None

        pid = post.get("id")
        if pid is None:
            continue
        msg = post.get("message")
        text = msg.strip() if isinstance(msg, str) else None
        if text == "":
            text = None

        media_type = _facebook_media_type_from_post(post, str(row.get("post_type_api") or ""))
        permalink = post.get("permalink_url")
        permalink_url = permalink.strip() if isinstance(permalink, str) and permalink.strip() else None

        likes = safe_int(interactions.get("reactions_count"))
        comments = safe_int(interactions.get("comments_count"))
        shares = safe_int(interactions.get("shares_count"))
        reach = _opt_int(interactions.get("reach"))
        impressions = _opt_int(interactions.get("impressions"))
        clicks = _insight_value(post_insights, "post_clicks")
        video_views = _insight_value(post_insights, "post_video_views")

        reactions_like = _insight_value(post_insights, "post_reactions_like_total")
        reactions_love = _insight_value(post_insights, "post_reactions_love_total")
        reactions_haha = _insight_value(post_insights, "post_reactions_haha_total")
        reactions_wow = _insight_value(post_insights, "post_reactions_wow_total")
        reactions_sad = _insight_value(post_insights, "post_reactions_sorry_total")
        reactions_angry = _insight_value(post_insights, "post_reactions_anger_total")

        normalized_posts.append(
            {
                "post_external_id": str(pid),
                "published_at": _iso_published_at(post.get("created_time")),
                "text": text,
                "media_type": media_type,
                "media_url": None,
                "permalink_url": permalink_url,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "saves": None,
                "clicks": clicks,
                "reach": reach,
                "impressions": impressions,
                "video_views": video_views,
                "reactions_like": reactions_like,
                "reactions_love": reactions_love,
                "reactions_haha": reactions_haha,
                "reactions_wow": reactions_wow,
                "reactions_sad": reactions_sad,
                "reactions_angry": reactions_angry,
            }
        )

    page_social = raw.get("page_social") if isinstance(raw.get("page_social"), dict) else {}
    followers = page_social.get("followers_count")
    if not isinstance(followers, (int, float)) and followers is not None:
        followers = None
    elif isinstance(followers, (int, float)):
        followers = int(followers)

    return {
        "platform": "facebook",
        "followers_count": followers,
        "posts_count": len(normalized_posts),
        "posts": normalized_posts,
    }


def build_normalized_facebook(raw: dict[str, Any]) -> dict[str, Any]:
    """Alias rétrocompatible : même sortie que ``normalize_facebook_data``."""
    return normalize_facebook_data(raw)


def main() -> None:
    src = RESULTS_DIR / "facebook_extract_result.json"
    raw = load_json(src)
    out = normalize_facebook_data(raw)
    dump_json(NORMALIZED_DIR / "facebook_normalized.json", out)
    print(f"normalized facebook -> {NORMALIZED_DIR / 'facebook_normalized.json'}")


if __name__ == "__main__":
    main()
