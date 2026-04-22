from __future__ import annotations

from typing import Any

from normalize_common import (
    NORMALIZED_DIR,
    RESULTS_DIR,
    dump_json,
    first_phrase,
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


def main() -> None:
    src = RESULTS_DIR / "facebook_extract_result.json"
    raw = load_json(src)

    posts_detailed = raw.get("posts_detailed") if isinstance(raw.get("posts_detailed"), list) else []
    normalized_posts: list[dict[str, Any]] = []
    for row in posts_detailed:
        if not isinstance(row, dict):
            continue
        post = row.get("post") if isinstance(row.get("post"), dict) else {}
        interactions = row.get("interactions") if isinstance(row.get("interactions"), dict) else {}
        post_insights = row.get("post_insights") if isinstance(row.get("post_insights"), list) else None

        reactions_breakdown = {
            "like": _insight_value(post_insights, "post_reactions_like_total"),
            "love": _insight_value(post_insights, "post_reactions_love_total"),
            "haha": _insight_value(post_insights, "post_reactions_haha_total"),
            "wow": _insight_value(post_insights, "post_reactions_wow_total"),
            "sad": _insight_value(post_insights, "post_reactions_sorry_total"),
            "angry": _insight_value(post_insights, "post_reactions_anger_total"),
        }
        clicks = _insight_value(post_insights, "post_clicks")
        created = post.get("created_time")
        created_dt = parse_dt(created)

        normalized_posts.append(
            {
                "platform": "facebook",
                "post_id": post.get("id"),
                "post_type": str(row.get("post_type_api") or "unknown"),
                "message_preview": first_phrase(post.get("message")),
                "published_at": created,
                "published_at_ts": created_dt.timestamp() if created_dt else None,
                "likes": safe_int(interactions.get("reactions_count")),
                "comments": safe_int(interactions.get("comments_count")),
                "shares": safe_int(interactions.get("shares_count")),
                "saves": None,
                "clicks": safe_int(clicks) if clicks is not None else None,
                "reach": safe_int(interactions.get("reach"))
                if isinstance(interactions.get("reach"), (int, float))
                else None,
                "impressions": safe_int(interactions.get("impressions"))
                if isinstance(interactions.get("impressions"), (int, float))
                else None,
                "interactions_total": safe_int(interactions.get("interactions_total")),
                "reactions_breakdown": reactions_breakdown,
            }
        )

    page_social = raw.get("page_social") if isinstance(raw.get("page_social"), dict) else {}
    out = {
        "platform": "facebook",
        "followers_count": page_social.get("followers_count"),
        "posts_count": len(normalized_posts),
        "posts": normalized_posts,
    }
    dump_json(NORMALIZED_DIR / "facebook_normalized.json", out)
    print(f"normalized facebook -> {NORMALIZED_DIR / 'facebook_normalized.json'}")


if __name__ == "__main__":
    main()
