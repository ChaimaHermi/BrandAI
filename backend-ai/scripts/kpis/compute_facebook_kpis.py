from __future__ import annotations

from typing import Any

from kpi_common import NORMALIZED_DIR, dump_json, pct, post_days_span, safe_div
from kpi_common import load_json as _load_json


def main() -> None:
    src = NORMALIZED_DIR / "facebook_normalized.json"
    normalized = _load_json(src)
    posts = normalized.get("posts") if isinstance(normalized.get("posts"), list) else []
    followers = normalized.get("followers_count")

    total_reactions_global = sum(int(p.get("likes") or 0) for p in posts if isinstance(p, dict))
    total_comments = sum(int(p.get("comments") or 0) for p in posts if isinstance(p, dict))
    total_shares = sum(int(p.get("shares") or 0) for p in posts if isinstance(p, dict))
    total_clicks = sum(int(p.get("clicks") or 0) for p in posts if isinstance(p, dict) and p.get("clicks") is not None)
    total_interactions = total_reactions_global + total_comments + total_shares

    reach_values = [int(p.get("reach")) for p in posts if isinstance(p, dict) and isinstance(p.get("reach"), int)]
    reach_total = sum(reach_values) if reach_values else None

    reactions_map: dict[str, int] = {}
    enriched_posts: list[dict[str, Any]] = []
    er_values: list[float] = []
    post_type_counts: dict[str, int] = {}
    for p in posts:
        if not isinstance(p, dict):
            continue
        reach = p.get("reach") if isinstance(p.get("reach"), int) else None
        reactions = int(p.get("likes") or 0)
        comments = int(p.get("comments") or 0)
        er_post = pct(reactions + comments, reach) if reach else None
        if er_post is not None:
            er_values.append(er_post)
        ptype = str(p.get("post_type") or "unknown")
        post_type_counts[ptype] = post_type_counts.get(ptype, 0) + 1
        breakdown = p.get("reactions_breakdown") if isinstance(p.get("reactions_breakdown"), dict) else {}
        for k, v in breakdown.items():
            if isinstance(v, int):
                reactions_map[k] = reactions_map.get(k, 0) + v
        enriched_posts.append({**p, "engagement_rate_post": er_post})

    nb_posts = len(posts)
    nb_days = post_days_span(posts)
    total_reactions_typed = sum(reactions_map.values())
    reactions_gap = total_reactions_global - total_reactions_typed
    reactions_pct = {
        k: pct(v, total_reactions_typed) if total_reactions_typed else None for k, v in reactions_map.items()
    }

    kpis = {
        "platform": "facebook",
        "credibility": {
            "followers_count": followers,
            "posts_count": nb_posts,
            "days_span": nb_days or None,
            "publication_rate_per_day": safe_div(nb_posts, nb_days) if nb_days else None,
        },
        "reach": {
            "reach_total": reach_total,
            "reach_mean_per_post": safe_div(reach_total, nb_posts) if reach_total is not None and nb_posts else None,
            "clicks_per_post": safe_div(total_clicks, nb_posts) if nb_posts else None,
        },
        "engagement": {
            "engagement_rate_mean_pct": round(sum(er_values) / len(er_values), 4) if er_values else None,
            "comment_ratio_pct": pct(total_comments, total_interactions) if total_interactions else None,
        },
        "content": {
            "top_5_posts": sorted(
                enriched_posts,
                key=lambda x: (x.get("engagement_rate_post") is not None, x.get("engagement_rate_post") or 0),
                reverse=True,
            )[:5],
            "interactions_breakdown": {
                "total_reactions_global": total_reactions_global,
                "total_reactions_typed": total_reactions_typed,
                "reactions_gap_global_minus_typed": reactions_gap,
                "total_comments": total_comments,
                "total_shares": total_shares,
                "total_clicks": total_clicks,
            },
            "reactions_breakdown_pct": reactions_pct,
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
    out_path = NORMALIZED_DIR.parent / "kpis" / "facebook_kpis.json"
    dump_json(out_path, kpis)
    print(f"facebook kpis -> {out_path}")


if __name__ == "__main__":
    main()
