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


def _extract_reactions_map(raw_post: dict[str, Any]) -> dict[str, int]:
    engagement = raw_post.get("engagement") if isinstance(raw_post.get("engagement"), dict) else {}
    reactions = engagement.get("reactions") if isinstance(engagement.get("reactions"), list) else []
    out: dict[str, int] = {}
    for reaction in reactions:
        if not isinstance(reaction, dict):
            continue
        label = str(reaction.get("type") or reaction.get("reactionType") or "").strip().lower()
        count = safe_int(reaction.get("count"))
        if label:
            out[label] = out.get(label, 0) + count
    return out


def main() -> None:
    src = RESULTS_DIR / "linkedin_extract_result.json"
    raw = load_json(src)
    posts = raw.get("posts") if isinstance(raw.get("posts"), list) else []

    normalized_posts: list[dict[str, Any]] = []
    for post in posts:
        if not isinstance(post, dict):
            continue
        raw_post = post.get("raw") if isinstance(post.get("raw"), dict) else {}
        engagement = raw_post.get("engagement") if isinstance(raw_post.get("engagement"), dict) else {}
        published = post.get("published_at")
        published_dt = parse_dt(published)

        likes = safe_int(post.get("likes")) or safe_int(engagement.get("likes"))
        comments = safe_int(post.get("comments")) or safe_int(engagement.get("comments"))
        reposts = safe_int(post.get("reposts")) or safe_int(engagement.get("shares"))
        reactions_breakdown = _extract_reactions_map(raw_post)
        interactions_total = likes + comments + reposts

        normalized_posts.append(
            {
                "platform": "linkedin",
                "post_id": post.get("id"),
                "post_type": str(post.get("post_type_api") or "unknown"),
                "message_preview": first_phrase(post.get("text")),
                "published_at": published,
                "published_at_ts": published_dt.timestamp() if published_dt else None,
                "likes": likes,
                "comments": comments,
                "shares": reposts,
                "saves": None,
                "clicks": None,
                "reach": None,
                "impressions": None,
                "interactions_total": interactions_total,
                "reactions_breakdown": reactions_breakdown,
            }
        )

    profile_social = raw.get("profile_social") if isinstance(raw.get("profile_social"), dict) else {}
    out = {
        "platform": "linkedin",
        "followers_count": profile_social.get("followers_count"),
        "posts_count": len(normalized_posts),
        "posts": normalized_posts,
    }
    dump_json(NORMALIZED_DIR / "linkedin_normalized.json", out)
    print(f"normalized linkedin -> {NORMALIZED_DIR / 'linkedin_normalized.json'}")


if __name__ == "__main__":
    main()
