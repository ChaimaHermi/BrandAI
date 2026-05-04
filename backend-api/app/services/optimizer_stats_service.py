"""Lit les JSON normalisés produits par le social ETL (par idée) pour l’UI Optimizer."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


def _default_backend_ai_root() -> Path:
    return Path(__file__).resolve().parents[2].parent / "backend-ai"


def idea_etl_output_dir(idea_id: int) -> Path:
    root = (settings.BACKEND_AI_ROOT or "").strip()
    base = Path(root).resolve() if root else _default_backend_ai_root()
    return base / "social_etl" / "load" / "output" / f"idea_{idea_id}"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("Lecture %s: %s", path, e)
        return None
    return data if isinstance(data, dict) else None


def _sum_reach(posts: list[dict[str, Any]]) -> int:
    total = 0
    for p in posts:
        if not isinstance(p, dict):
            continue
        r = p.get("reach")
        if isinstance(r, (int, float)):
            total += int(r)
    return total


def _post_interactions_score(p: dict[str, Any]) -> int:
    it = p.get("interactions_total")
    if isinstance(it, (int, float)):
        return int(it)
    return int(p.get("likes") or 0) + int(p.get("comments") or 0) + int(p.get("shares") or 0)


def _sum_interactions(posts: list[dict[str, Any]]) -> int:
    total = 0
    for p in posts:
        if not isinstance(p, dict):
            continue
        total += _post_interactions_score(p)
    return total


def _engagement_rate_pct(posts: list[dict[str, Any]], reach_sum: int) -> float | None:
    if reach_sum <= 0:
        return None
    inter = _sum_interactions(posts)
    return round(100.0 * inter / reach_sum, 2)


def _top_posts_from_normalized(
    posts: list[dict[str, Any]],
    platform: str,
    *,
    limit: int = 12,
) -> list[dict[str, Any]]:
    scored: list[tuple[int, dict[str, Any]]] = []
    for p in posts:
        if not isinstance(p, dict):
            continue
        scored.append((_post_interactions_score(p), p))
    scored.sort(key=lambda x: x[0], reverse=True)
    out: list[dict[str, Any]] = []
    for _s, p in scored[:limit]:
        preview = p.get("text")
        if not isinstance(preview, str):
            preview = p.get("message_preview")
        if not isinstance(preview, str):
            preview = None
        pub = p.get("published_at")
        pub_s = None
        if isinstance(pub, str):
            pub_s = pub
        elif isinstance(pub, dict):
            pub_s = str(pub.get("date") or "") or None
        ext_id = p.get("post_external_id") or p.get("post_id")
        out.append(
            {
                "id": str(ext_id or ""),
                "preview": preview,
                "platform": platform,
                "likes": int(p.get("likes") or 0) if p.get("likes") is not None else None,
                "comments": int(p.get("comments") or 0) if p.get("comments") is not None else None,
                "reach": int(p["reach"]) if isinstance(p.get("reach"), (int, float)) else None,
                "published_at": pub_s,
            }
        )
    return out


def _evolution_placeholder(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Histogramme simple par date (jour) à partir des posts."""
    buckets: dict[str, int] = {}
    for p in posts:
        if not isinstance(p, dict):
            continue
        pub = p.get("published_at")
        day = None
        if isinstance(pub, str) and len(pub) >= 10:
            day = pub[:10]
        elif isinstance(pub, dict):
            d = pub.get("date")
            if isinstance(d, str) and len(d) >= 10:
                day = d[:10]
        if not day:
            continue
        v = _post_interactions_score(p)
        buckets[day] = buckets.get(day, 0) + v
    return [{"date": k, "value": float(v)} for k, v in sorted(buckets.items())]


def _stats_one_platform(normalized: dict[str, Any] | None, platform: str) -> dict[str, Any]:
    if not normalized:
        return {
            "kpis": {
                "followers": None,
                "engagement_rate": None,
                "reach": None,
                "post_count": 0,
            },
            "evolution": [],
            "top_posts": [],
        }
    posts = normalized.get("posts") if isinstance(normalized.get("posts"), list) else []
    posts = [p for p in posts if isinstance(p, dict)]
    followers = normalized.get("followers_count")
    if not isinstance(followers, (int, float)) and followers is not None:
        followers = None
    elif isinstance(followers, (int, float)):
        followers = int(followers)

    reach_sum = _sum_reach(posts)
    er = _engagement_rate_pct(posts, reach_sum)

    return {
        "kpis": {
            "followers": int(followers) if isinstance(followers, (int, float)) else followers,
            "engagement_rate": er,
            "reach": reach_sum if reach_sum else None,
            "post_count": len(posts),
        },
        "evolution": _evolution_placeholder(posts),
        "top_posts": _top_posts_from_normalized(posts, platform),
    }


def get_optimizer_stats_for_idea(idea_id: int, platform: str) -> dict[str, Any]:
    """
    ``platform`` : global | facebook | instagram | linkedin
    """
    d = idea_etl_output_dir(idea_id)
    pf = (platform or "global").strip().lower()

    fb = _read_json(d / "facebook_normalized.json")
    ig = _read_json(d / "instagram_normalized.json")
    li = _read_json(d / "linkedin_normalized.json")

    if pf == "facebook":
        return _stats_one_platform(fb, "facebook")
    if pf == "instagram":
        return _stats_one_platform(ig, "instagram")
    if pf == "linkedin":
        return _stats_one_platform(li, "linkedin")

    # global — agrège posts et KPIs grossiers
    all_posts: list[dict[str, Any]] = []
    followers_total = 0
    for plat, doc in (("facebook", fb), ("instagram", ig), ("linkedin", li)):
        if not doc:
            continue
        fc = doc.get("followers_count")
        if isinstance(fc, (int, float)):
            followers_total += int(fc)
        posts = doc.get("posts") if isinstance(doc.get("posts"), list) else []
        for p in posts:
            if isinstance(p, dict):
                q = {**p, "platform": plat}
                all_posts.append(q)

    reach_sum = _sum_reach(all_posts)
    er = _engagement_rate_pct(all_posts, reach_sum)
    top = sorted(all_posts, key=lambda p: _post_interactions_score(p), reverse=True)[:12]
    mapped: list[dict[str, Any]] = []
    for p in top:
        pl = str(p.get("platform") or "facebook")
        one = _top_posts_from_normalized([{k: v for k, v in p.items() if k != "platform"}], pl)
        if one:
            mapped.append(one[0])

    return {
        "kpis": {
            "followers": followers_total or None,
            "engagement_rate": er,
            "reach": reach_sum if reach_sum else None,
            "post_count": len(all_posts),
        },
        "evolution": _evolution_placeholder(all_posts),
        "top_posts": mapped,
    }
