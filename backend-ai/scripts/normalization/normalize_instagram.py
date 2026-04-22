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
    src = RESULTS_DIR / "instagram_extract_result.json"
    raw = load_json(src)

    media_detailed = raw.get("media_detailed") if isinstance(raw.get("media_detailed"), list) else []
    normalized_posts: list[dict[str, Any]] = []
    for row in media_detailed:
        if not isinstance(row, dict):
            continue
        media = row.get("media") if isinstance(row.get("media"), dict) else {}
        interactions = row.get("interactions") if isinstance(row.get("interactions"), dict) else {}
        insights = row.get("insights") if isinstance(row.get("insights"), list) else None

        reach = interactions.get("reach")
        impressions = interactions.get("impressions")
        saves = _insight_value(insights, "saved")
        shares = _insight_value(insights, "shares")
        clicks = _insight_value(insights, "profile_activity")

        normalized_posts.append(
            {
                "platform": "instagram",
                "post_id": media.get("id"),
                "post_type": str(row.get("post_type_api") or "unknown"),
                "message_preview": first_phrase(media.get("caption")),
                "published_at": media.get("timestamp"),
                "published_at_ts": parse_dt(media.get("timestamp")).timestamp()
                if parse_dt(media.get("timestamp"))
                else None,
                "likes": safe_int(interactions.get("likes_count")),
                "comments": safe_int(interactions.get("comments_count")),
                "shares": safe_int(shares) if shares is not None else None,
                "saves": safe_int(saves) if saves is not None else None,
                "clicks": safe_int(clicks) if clicks is not None else None,
                "reach": safe_int(reach) if isinstance(reach, (int, float)) else None,
                "impressions": safe_int(impressions) if isinstance(impressions, (int, float)) else None,
                "interactions_total": safe_int(interactions.get("interactions_total")),
                "reactions_breakdown": {},
            }
        )

    out = {
        "platform": "instagram",
        "followers_count": raw.get("instagram_social", {}).get("followers_count")
        if isinstance(raw.get("instagram_social"), dict)
        else None,
        "posts_count": len(normalized_posts),
        "posts": normalized_posts,
    }
    dump_json(NORMALIZED_DIR / "instagram_normalized.json", out)
    print(f"normalized instagram -> {NORMALIZED_DIR / 'instagram_normalized.json'}")


if __name__ == "__main__":
    main()
