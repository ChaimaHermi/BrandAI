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


def _iso_published_at(value: Any) -> str | None:
    dt = parse_dt(value)
    if dt:
        return dt.isoformat()
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _linkedin_media_url(raw_post: dict[str, Any]) -> str | None:
    images = raw_post.get("images")
    if isinstance(images, list) and images:
        first = images[0]
        if isinstance(first, dict):
            u = first.get("url") or first.get("source") or first.get("downloadUrl")
            if isinstance(u, str) and u.strip():
                return u.strip()
        if isinstance(first, str) and first.strip():
            return first.strip()
    img = raw_post.get("image")
    if isinstance(img, str) and img.strip():
        return img.strip()
    if isinstance(img, dict):
        u = img.get("url") or img.get("source")
        if isinstance(u, str) and u.strip():
            return u.strip()
    return None


def normalize_linkedin_data(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Transforme la sortie ``extract_linkedin`` en structure alignée sur ``social_posts``.

    Les champs ``reactions_*`` restent vides (types LinkedIn variés) ; ``reactions_breakdown``
    reprend les types renvoyés par Apify pour usages analytiques ultérieurs.
    """
    posts = raw.get("posts") if isinstance(raw.get("posts"), list) else []
    normalized_posts: list[dict[str, Any]] = []
    for post in posts:
        if not isinstance(post, dict):
            continue
        raw_post = post.get("raw") if isinstance(post.get("raw"), dict) else {}
        engagement = raw_post.get("engagement") if isinstance(raw_post.get("engagement"), dict) else {}

        pid = post.get("id")
        if pid is None:
            continue

        body = post.get("text")
        text = body.strip() if isinstance(body, str) else None
        if text == "":
            text = None

        likes = (
            safe_int(post.get("likes"))
            if post.get("likes") is not None
            else safe_int(engagement.get("likes"))
        )
        comments = (
            safe_int(post.get("comments"))
            if post.get("comments") is not None
            else safe_int(engagement.get("comments"))
        )
        shares = (
            safe_int(post.get("reposts"))
            if post.get("reposts") is not None
            else safe_int(engagement.get("shares"))
        )
        reactions_breakdown = _extract_reactions_map(raw_post)

        url = post.get("post_url") or post.get("url")
        permalink_url = url.strip() if isinstance(url, str) and url.strip() else None

        normalized_posts.append(
            {
                "post_external_id": str(pid),
                "published_at": _iso_published_at(post.get("published_at")),
                "text": text,
                "media_type": str(post.get("post_type_api") or "unknown"),
                "media_url": _linkedin_media_url(raw_post),
                "permalink_url": permalink_url,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "saves": None,
                "clicks": None,
                "reach": None,
                "impressions": None,
                "video_views": None,
                "reactions_like": None,
                "reactions_love": None,
                "reactions_haha": None,
                "reactions_wow": None,
                "reactions_sad": None,
                "reactions_angry": None,
                "reactions_breakdown": reactions_breakdown or {},
            }
        )

    profile_social = raw.get("profile_social") if isinstance(raw.get("profile_social"), dict) else {}
    followers = profile_social.get("followers_count")
    if not isinstance(followers, (int, float)) and followers is not None:
        followers = None
    elif isinstance(followers, (int, float)):
        followers = int(followers)

    return {
        "platform": "linkedin",
        "followers_count": followers,
        "posts_count": len(normalized_posts),
        "posts": normalized_posts,
    }


def build_normalized_linkedin(raw: dict[str, Any]) -> dict[str, Any]:
    """Alias rétrocompatible : même sortie que ``normalize_linkedin_data``."""
    return normalize_linkedin_data(raw)


def main() -> None:
    src = RESULTS_DIR / "linkedin_extract_result.json"
    raw = load_json(src)
    out = normalize_linkedin_data(raw)
    dump_json(NORMALIZED_DIR / "linkedin_normalized.json", out)
    print(f"normalized linkedin -> {NORMALIZED_DIR / 'linkedin_normalized.json'}")


if __name__ == "__main__":
    main()
