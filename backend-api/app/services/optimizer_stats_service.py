"""Statistiques Optimizer lues depuis PostgreSQL (tables ETL/KPI)."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


PLATFORM_TO_DB = {
    "facebook": "facebook_page",
    "instagram": "instagram_business",
    "linkedin": "linkedin",
}
DB_TO_UI = {v: k for k, v in PLATFORM_TO_DB.items()}


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _fetch_connection_ids(db: Session, idea_id: int, user_id: int, platform: str) -> list[int]:
    pf = (platform or "global").strip().lower()
    if pf in PLATFORM_TO_DB:
        rows = db.execute(
            text(
                """
                SELECT id
                FROM social_connections
                WHERE idea_id = :idea_id
                  AND user_id = :user_id
                  AND platform = :platform
                """
            ),
            {"idea_id": idea_id, "user_id": user_id, "platform": PLATFORM_TO_DB[pf]},
        ).fetchall()
    else:
        rows = db.execute(
            text(
                """
                SELECT id
                FROM social_connections
                WHERE idea_id = :idea_id
                  AND user_id = :user_id
                  AND platform IN ('facebook_page', 'instagram_business', 'linkedin')
                """
            ),
            {"idea_id": idea_id, "user_id": user_id},
        ).fetchall()
    return [int(r[0]) for r in rows]


def _fetch_latest_summary_rows(db: Session, connection_ids: list[int]) -> list[dict[str, Any]]:
    if not connection_ids:
        return []
    rows = db.execute(
        text(
            """
            SELECT DISTINCT ON (connection_id)
                   connection_id, followers_count, posts_count, total_engagement,
                   total_reach, engagement_rate, clicks, shares, reactions_breakdown
            FROM social_kpi_summary
            WHERE connection_id = ANY(:connection_ids)
              AND period_type = '30days'
            ORDER BY connection_id, period_start DESC, calculated_at DESC, id DESC
            """
        ),
        {"connection_ids": connection_ids},
    ).mappings().all()
    return [dict(r) for r in rows]


def _aggregate_reactions(rows: list[dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        rb = row.get("reactions_breakdown")
        if not isinstance(rb, dict):
            continue
        for key, value in rb.items():
            v = _safe_int(value) or 0
            out[key] = out.get(key, 0) + v
    return out


def _build_kpis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    followers_total = 0
    posts_total = 0
    total_engagement = 0
    total_reach = 0
    total_clicks = 0
    total_shares = 0
    has_reach = False
    has_clicks = False
    has_followers = False

    for row in rows:
        followers = _safe_int(row.get("followers_count"))
        posts_count = _safe_int(row.get("posts_count")) or 0
        engagement = _safe_int(row.get("total_engagement")) or 0
        reach = _safe_int(row.get("total_reach"))
        clicks = _safe_int(row.get("clicks"))
        shares = _safe_int(row.get("shares")) or 0

        if followers is not None:
            followers_total += followers
            has_followers = True
        posts_total += posts_count
        total_engagement += engagement
        if reach is not None:
            total_reach += reach
            has_reach = True
        if clicks is not None:
            total_clicks += clicks
            has_clicks = True
        total_shares += shares

    has_linkedin = any(str(r.get("platform") or "") == "linkedin" for r in rows)

    engagement_rate: float | None = None
    if has_reach and total_reach > 0:
        engagement_rate = round((total_engagement * 100.0) / total_reach, 2)
    elif has_followers and followers_total > 0:
        engagement_rate = round((total_engagement * 100.0) / followers_total, 2)

    return {
        "followers": followers_total if has_followers else None,
        "engagement_rate": engagement_rate,
        "reach": None if has_linkedin else (total_reach if has_reach else None),
        "post_count": posts_total,
        "total_engagement": total_engagement,
        "comments": None,
        "clicks": None if has_linkedin else (total_clicks if has_clicks else None),
        "shares": total_shares,
    }


def _fetch_post_level_totals(db: Session, connection_ids: list[int]) -> dict[str, int]:
    if not connection_ids:
        return {"comments": 0}
    row = db.execute(
        text(
            """
            SELECT
                COALESCE(SUM(COALESCE(comments, 0)), 0)::int AS comments
            FROM social_posts
            WHERE connection_id = ANY(:connection_ids)
              AND published_at >= (CURRENT_DATE - INTERVAL '30 days')
            """
        ),
        {"connection_ids": connection_ids},
    ).mappings().first()
    if not row:
        return {"comments": 0}
    return {"comments": _safe_int(row.get("comments")) or 0}


def _fetch_evolution(db: Session, connection_ids: list[int]) -> list[dict[str, Any]]:
    if not connection_ids:
        return []
    rows = db.execute(
        text(
            """
            WITH days AS (
                SELECT generate_series(
                    (CURRENT_DATE - INTERVAL '29 days')::date,
                    CURRENT_DATE::date,
                    INTERVAL '1 day'
                )::date AS date
            ),
            agg AS (
                SELECT date::date AS date, SUM(total_engagement)::float AS value
                FROM social_daily_engagement
                WHERE connection_id = ANY(:connection_ids)
                  AND date >= (CURRENT_DATE - INTERVAL '29 days')::date
                GROUP BY date::date
            )
            SELECT
                d.date::text AS date,
                COALESCE(a.value, 0)::float AS value
            FROM days d
            LEFT JOIN agg a ON a.date = d.date
            ORDER BY d.date ASC
            """
        ),
        {"connection_ids": connection_ids},
    ).mappings().all()
    return [dict(r) for r in rows]


def _fetch_top_posts(db: Session, connection_ids: list[int]) -> list[dict[str, Any]]:
    if not connection_ids:
        return []
    rows = db.execute(
        text(
            """
            SELECT
                sp.post_external_id,
                LEFT(COALESCE(sp.text, ''), 200) AS preview,
                sc.platform,
                sp.media_type,
                sp.likes,
                sp.comments,
                sp.reach,
                sp.permalink_url,
                sp.published_at
            FROM social_posts sp
            JOIN social_connections sc ON sc.id = sp.connection_id
            WHERE sp.connection_id = ANY(:connection_ids)
              AND sp.published_at >= (CURRENT_DATE - INTERVAL '30 days')
            ORDER BY (COALESCE(sp.likes, 0) + COALESCE(sp.comments, 0) + COALESCE(sp.shares, 0)) DESC,
                     sp.published_at DESC
            LIMIT 5
            """
        ),
        {"connection_ids": connection_ids},
    ).mappings().all()

    mapped: list[dict[str, Any]] = []
    for r in rows:
        platform_key = DB_TO_UI.get(str(r["platform"]), "facebook")
        mapped.append(
            {
                "id": str(r["post_external_id"] or ""),
                "preview": r["preview"],
                "platform": platform_key,
                "media_type": str(r["media_type"]) if r["media_type"] is not None else "unknown",
                "likes": _safe_int(r["likes"]),
                "comments": _safe_int(r["comments"]),
                "reach": _safe_int(r["reach"]),
                "permalink_url": str(r["permalink_url"]) if r["permalink_url"] is not None else None,
                "published_at": str(r["published_at"]) if r["published_at"] is not None else None,
            }
        )
    return mapped


def get_optimizer_stats_for_idea(db: Session, idea_id: int, user_id: int, platform: str) -> dict[str, Any]:
    connection_ids = _fetch_connection_ids(db, idea_id, user_id, platform)
    rows = _fetch_latest_summary_rows(db, connection_ids)
    platforms = db.execute(
        text(
            """
            SELECT id, platform
            FROM social_connections
            WHERE id = ANY(:connection_ids)
            """
        ),
        {"connection_ids": connection_ids or [-1]},
    ).mappings().all()
    platform_by_id = {int(r["id"]): str(r["platform"]) for r in platforms}
    for row in rows:
        row["platform"] = platform_by_id.get(int(row["connection_id"]), "")

    kpis = _build_kpis(rows)
    post_level_totals = _fetch_post_level_totals(db, connection_ids)
    kpis["comments"] = post_level_totals["comments"]

    return {
        "kpis": kpis,
        "evolution": _fetch_evolution(db, connection_ids),
        "top_posts": _fetch_top_posts(db, connection_ids),
        "reactions_breakdown": _aggregate_reactions(rows),
    }
