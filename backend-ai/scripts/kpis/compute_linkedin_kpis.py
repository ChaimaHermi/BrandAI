from __future__ import annotations

from typing import Any

from kpi_common import NORMALIZED_DIR, dump_json, pct, post_days_span, safe_div
from kpi_common import load_json as _load_json


def main() -> None:
    src = NORMALIZED_DIR / "linkedin_normalized.json"
    normalized = _load_json(src)
    posts = normalized.get("posts") if isinstance(normalized.get("posts"), list) else []

    total_likes = sum(int(p.get("likes") or 0) for p in posts if isinstance(p, dict))
    total_comments = sum(int(p.get("comments") or 0) for p in posts if isinstance(p, dict))
    total_reposts = sum(int(p.get("shares") or 0) for p in posts if isinstance(p, dict))
    total_interactions = total_likes + total_comments + total_reposts

    reactions_map: dict[str, int] = {}
    for p in posts:
        if not isinstance(p, dict):
            continue
        breakdown = p.get("reactions_breakdown") if isinstance(p.get("reactions_breakdown"), dict) else {}
        for k, v in breakdown.items():
            if isinstance(v, int):
                reactions_map[k] = reactions_map.get(k, 0) + v

    dominant_reaction = None
    if reactions_map:
        dominant_reaction = max(reactions_map.items(), key=lambda x: x[1])[0]

    enriched_posts: list[dict[str, Any]] = []
    post_type_counts: dict[str, int] = {}
    for p in posts:
        if not isinstance(p, dict):
            continue
        interactions = int(p.get("interactions_total") or 0)
        ptype = str(p.get("post_type") or "unknown")
        post_type_counts[ptype] = post_type_counts.get(ptype, 0) + 1
        enriched_posts.append({**p, "interactions_per_post": interactions})

    nb_posts = len(posts)
    nb_days = post_days_span(posts)
    total_reactions = sum(reactions_map.values())
    reactions_pct = {
        k: pct(v, total_reactions) if total_reactions else None for k, v in reactions_map.items()
    }

    kpis = {
        "platform": "linkedin",
        "credibility": {
            "followers_count": normalized.get("followers_count"),
            "posts_count": nb_posts,
            "days_span": nb_days or None,
            "publication_rate_per_day": safe_div(nb_posts, nb_days) if nb_days else None,
        },
        "reach": {
            "reach_total": None,
            "reach_mean_per_post": None,
            "reach_rate_pct": None,
        },
        "engagement": {
            "interactions_per_post": safe_div(total_interactions, nb_posts) if nb_posts else None,
            "comment_ratio_pct": pct(total_comments, total_interactions) if total_interactions else None,
            "dominant_reaction": dominant_reaction,
        },
        "content": {
            "top_5_posts": sorted(
                enriched_posts, key=lambda x: int(x.get("interactions_total") or 0), reverse=True
            )[:5],
            "interactions_breakdown": {
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_reposts": total_reposts,
            },
            "reactions_breakdown_pct": reactions_pct,
        },
        "trend": {
            "curve": sorted(
                [
                    {"published_at": p.get("published_at"), "interactions": p.get("interactions_total")}
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
    out_path = NORMALIZED_DIR.parent / "kpis" / "linkedin_kpis.json"
    dump_json(out_path, kpis)
    print(f"linkedin kpis -> {out_path}")


if __name__ == "__main__":
    main()
