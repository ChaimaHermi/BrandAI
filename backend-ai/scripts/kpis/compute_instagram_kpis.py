from __future__ import annotations

from typing import Any

from kpi_common import NORMALIZED_DIR, dump_json, pct, post_days_span, safe_div
from kpi_common import load_json as _load_json


def main() -> None:
    src = NORMALIZED_DIR / "instagram_normalized.json"
    normalized = _load_json(src)
    posts = normalized.get("posts") if isinstance(normalized.get("posts"), list) else []
    followers = normalized.get("followers_count")

    total_likes = sum(int(p.get("likes") or 0) for p in posts if isinstance(p, dict))
    total_comments = sum(int(p.get("comments") or 0) for p in posts if isinstance(p, dict))
    total_saves = sum(int(p.get("saves") or 0) for p in posts if isinstance(p, dict) and p.get("saves") is not None)
    total_shares = sum(int(p.get("shares") or 0) for p in posts if isinstance(p, dict) and p.get("shares") is not None)
    total_interactions = total_likes + total_comments + total_saves + total_shares

    reach_values = [int(p.get("reach")) for p in posts if isinstance(p, dict) and isinstance(p.get("reach"), int)]
    reach_total = sum(reach_values) if reach_values else None
    nb_posts = len(posts)
    nb_days = post_days_span(posts)

    enriched_posts: list[dict[str, Any]] = []
    er_values: list[float] = []
    post_type_counts: dict[str, int] = {}
    for p in posts:
        if not isinstance(p, dict):
            continue
        likes = int(p.get("likes") or 0)
        comments = int(p.get("comments") or 0)
        saves = int(p.get("saves") or 0) if p.get("saves") is not None else 0
        reach = p.get("reach") if isinstance(p.get("reach"), int) else None
        er_post = pct(likes + comments + saves, reach) if reach else None
        if er_post is not None:
            er_values.append(er_post)
        ptype = str(p.get("post_type") or "unknown")
        post_type_counts[ptype] = post_type_counts.get(ptype, 0) + 1
        enriched_posts.append({**p, "engagement_rate_post": er_post})

    kpis = {
        "platform": "instagram",
        "credibility": {
            "followers_count": followers,
            "posts_count": nb_posts,
            "days_span": nb_days or None,
            "publication_rate_per_day": safe_div(nb_posts, nb_days) if nb_days else None,
        },
        "reach": {
            "reach_total": reach_total,
            "reach_mean_per_post": safe_div(reach_total, nb_posts) if reach_total is not None and nb_posts else None,
            "reach_rate_pct": pct(
                safe_div(reach_total, nb_posts) if reach_total is not None and nb_posts else 0,
                followers or 0,
            )
            if followers
            else None,
        },
        "engagement": {
            "engagement_rate_mean_pct": round(sum(er_values) / len(er_values), 4) if er_values else None,
            "save_rate_pct": pct(total_saves, reach_total) if reach_total else None,
            "comment_ratio_pct": pct(total_comments, total_interactions) if total_interactions else None,
        },
        "content": {
            "top_5_posts": sorted(
                enriched_posts,
                key=lambda x: (x.get("engagement_rate_post") is not None, x.get("engagement_rate_post") or 0),
                reverse=True,
            )[:5],
            "interactions_breakdown": {
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_saves": total_saves,
                "total_shares": total_shares,
            },
        },
        "trend": {
            "curve": sorted(
                [
                    {"published_at": p.get("published_at"), "engagement_rate_post": p.get("engagement_rate_post")}
                    for p in enriched_posts
                ],
                key=lambda x: str(x.get("published_at") or ""),
            )
        },
        "post_types": {
            "counts": post_type_counts,
            "pct": {k: pct(v, nb_posts) if nb_posts else None for k, v in post_type_counts.items()},
        },
    }
    out_path = NORMALIZED_DIR.parent / "kpis" / "instagram_kpis.json"
    dump_json(out_path, kpis)
    print(f"instagram kpis -> {out_path}")


if __name__ == "__main__":
    main()
