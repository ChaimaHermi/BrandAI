"""Statistiques Optimizer lues depuis PostgreSQL (tables ETL/KPI)."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings

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
              AND period_type IN ('synced', '30days')
            ORDER BY connection_id,
                     CASE period_type WHEN 'synced' THEN 0 ELSE 1 END,
                     period_start DESC,
                     calculated_at DESC,
                     id DESC
            """
        ),
        {"connection_ids": connection_ids},
    ).mappings().all()
    return [dict(r) for r in rows]


def _fetch_followers_total(
    rows: list[dict[str, Any]],
    *,
    linkedin_connection_ids: set[int] | None = None,
) -> int | None:
    followers_total = 0
    has_followers = False
    for row in rows:
        cid = _safe_int(row.get("connection_id"))
        followers = _safe_int(row.get("followers_count"))
        if (
            linkedin_connection_ids
            and cid is not None
            and cid in linkedin_connection_ids
            and followers is not None
            and followers > 50_000
        ):
            followers = None
        if followers is not None:
            followers_total += followers
            has_followers = True
    return followers_total if has_followers else None


def _fetch_daily_network_size(db: Session, connection_ids: list[int]) -> int | None:
    if not connection_ids:
        return None
    rows = db.execute(
        text(
            """
            SELECT DISTINCT ON (connection_id)
                   connection_id, followers_count
            FROM social_daily_insights
            WHERE connection_id = ANY(:connection_ids)
            ORDER BY connection_id, date DESC
            """
        ),
        {"connection_ids": connection_ids},
    ).mappings().all()
    total = 0
    has_value = False
    for row in rows:
        value = _safe_int(row.get("followers_count"))
        if value is not None and value <= 50_000:
            total += value
            has_value = True
    return total if has_value else None


def _fetch_posts_aggregates(
    db: Session,
    connection_ids: list[int],
    *,
    reach_filter_engagement: bool = False,
) -> dict[str, Any]:
    """Agrège les métriques sur les posts synchronisés.

    - ``post_count`` : tous les posts récupérés.
    - ``reach_filter_engagement=True`` (Facebook) : engagement / portée / taux
      uniquement sur les posts avec ``reach > 0``.
    - ``reach_filter_engagement=False`` (Instagram, global, LinkedIn) :
      engagement sur tous les posts ; portée / clics uniquement si ``reach > 0``.
    """
    empty = {
        "post_count": 0,
        "total_engagement": 0,
        "total_reach": None,
        "total_clicks": None,
        "total_shares": 0,
        "comments": 0,
        "reactions_breakdown": {},
        "posts_with_reach": 0,
    }
    if not connection_ids:
        return empty

    if reach_filter_engagement:
        metrics_sql = """
            SELECT
                COUNT(*)::int AS post_count,
                COUNT(*) FILTER (WHERE COALESCE(reach, 0) > 0)::int AS posts_with_reach,
                COALESCE(
                    SUM(
                        CASE WHEN COALESCE(reach, 0) > 0 THEN
                            COALESCE(likes, 0) + COALESCE(comments, 0) + COALESCE(shares, 0)
                        ELSE 0 END
                    ),
                    0
                )::int AS total_engagement,
                CASE
                    WHEN COUNT(*) FILTER (WHERE COALESCE(reach, 0) > 0) = 0 THEN NULL
                    ELSE COALESCE(
                        SUM(CASE WHEN COALESCE(reach, 0) > 0 THEN reach ELSE 0 END),
                        0
                    )::int
                END AS total_reach,
                CASE
                    WHEN COUNT(*) FILTER (WHERE COALESCE(reach, 0) > 0) = 0 THEN NULL
                    ELSE COALESCE(
                        SUM(CASE WHEN COALESCE(reach, 0) > 0 THEN COALESCE(clicks, 0) ELSE 0 END),
                        0
                    )::int
                END AS total_clicks,
                COALESCE(
                    SUM(
                        CASE WHEN COALESCE(reach, 0) > 0 THEN COALESCE(shares, 0) ELSE 0 END
                    ),
                    0
                )::int AS total_shares,
                COALESCE(
                    SUM(
                        CASE WHEN COALESCE(reach, 0) > 0 THEN COALESCE(comments, 0) ELSE 0 END
                    ),
                    0
                )::int AS comments,
                CASE
                    WHEN COUNT(*) FILTER (WHERE COALESCE(reach, 0) > 0) = 0 THEN NULL
                    ELSE JSONB_BUILD_OBJECT(
                        'like', COALESCE(SUM(
                            CASE WHEN COALESCE(reach, 0) > 0
                            THEN COALESCE((reactions_breakdown->>'like')::int, 0) ELSE 0 END
                        ), 0),
                        'love', COALESCE(SUM(
                            CASE WHEN COALESCE(reach, 0) > 0
                            THEN COALESCE((reactions_breakdown->>'love')::int, 0) ELSE 0 END
                        ), 0),
                        'haha', COALESCE(SUM(
                            CASE WHEN COALESCE(reach, 0) > 0
                            THEN COALESCE((reactions_breakdown->>'haha')::int, 0) ELSE 0 END
                        ), 0),
                        'wow', COALESCE(SUM(
                            CASE WHEN COALESCE(reach, 0) > 0
                            THEN COALESCE((reactions_breakdown->>'wow')::int, 0) ELSE 0 END
                        ), 0),
                        'sad', COALESCE(SUM(
                            CASE WHEN COALESCE(reach, 0) > 0
                            THEN COALESCE((reactions_breakdown->>'sad')::int, 0) ELSE 0 END
                        ), 0),
                        'angry', COALESCE(SUM(
                            CASE WHEN COALESCE(reach, 0) > 0
                            THEN COALESCE((reactions_breakdown->>'angry')::int, 0) ELSE 0 END
                        ), 0)
                    )
                END AS reactions_breakdown
            FROM social_posts
            WHERE connection_id = ANY(:connection_ids)
        """
    else:
        metrics_sql = """
            SELECT
                COUNT(*)::int AS post_count,
                COUNT(*) FILTER (WHERE COALESCE(reach, 0) > 0)::int AS posts_with_reach,
                COALESCE(
                    SUM(COALESCE(likes, 0) + COALESCE(comments, 0) + COALESCE(shares, 0)),
                    0
                )::int AS total_engagement,
                CASE
                    WHEN COUNT(*) FILTER (WHERE COALESCE(reach, 0) > 0) = 0 THEN NULL
                    ELSE COALESCE(
                        SUM(CASE WHEN COALESCE(reach, 0) > 0 THEN reach ELSE 0 END),
                        0
                    )::int
                END AS total_reach,
                CASE
                    WHEN COUNT(*) FILTER (WHERE COALESCE(reach, 0) > 0) = 0 THEN NULL
                    ELSE COALESCE(
                        SUM(CASE WHEN COALESCE(reach, 0) > 0 THEN COALESCE(clicks, 0) ELSE 0 END),
                        0
                    )::int
                END AS total_clicks,
                COALESCE(SUM(COALESCE(shares, 0)), 0)::int AS total_shares,
                COALESCE(SUM(COALESCE(comments, 0)), 0)::int AS comments,
                CASE
                    WHEN COUNT(*) = 0 THEN NULL
                    ELSE JSONB_BUILD_OBJECT(
                        'like', COALESCE(SUM(COALESCE((reactions_breakdown->>'like')::int, 0)), 0),
                        'love', COALESCE(SUM(COALESCE((reactions_breakdown->>'love')::int, 0)), 0),
                        'haha', COALESCE(SUM(COALESCE((reactions_breakdown->>'haha')::int, 0)), 0),
                        'wow', COALESCE(SUM(COALESCE((reactions_breakdown->>'wow')::int, 0)), 0),
                        'sad', COALESCE(SUM(COALESCE((reactions_breakdown->>'sad')::int, 0)), 0),
                        'angry', COALESCE(SUM(COALESCE((reactions_breakdown->>'angry')::int, 0)), 0)
                    )
                END AS reactions_breakdown
            FROM social_posts
            WHERE connection_id = ANY(:connection_ids)
        """

    row = db.execute(
        text(metrics_sql),
        {"connection_ids": connection_ids},
    ).mappings().first()
    if not row:
        return empty
    rb = row.get("reactions_breakdown")
    return {
        "post_count": _safe_int(row.get("post_count")) or 0,
        "posts_with_reach": _safe_int(row.get("posts_with_reach")) or 0,
        "total_engagement": _safe_int(row.get("total_engagement")) or 0,
        "total_reach": _safe_int(row.get("total_reach")),
        "total_clicks": _safe_int(row.get("total_clicks")),
        "total_shares": _safe_int(row.get("total_shares")) or 0,
        "comments": _safe_int(row.get("comments")) or 0,
        "reactions_breakdown": dict(rb) if isinstance(rb, dict) else {},
    }


def _build_kpis(
    *,
    followers: int | None,
    posts: dict[str, Any],
    has_linkedin: bool,
    linkedin_only: bool = False,
) -> dict[str, Any]:
    total_engagement = _safe_int(posts.get("total_engagement")) or 0
    total_reach = _safe_int(posts.get("total_reach"))
    total_clicks = _safe_int(posts.get("total_clicks"))
    post_count = _safe_int(posts.get("post_count")) or 0

    engagement_rate: float | None = None
    if total_reach is not None and total_reach > 0:
        engagement_rate = round((total_engagement * 100.0) / total_reach, 2)
    elif followers is not None and followers > 0:
        engagement_rate = round((total_engagement * 100.0) / followers, 2)
    elif linkedin_only and post_count > 0 and total_engagement > 0:
        # LinkedIn : pas de portée API — taux relatif au réseau indisponible → moyenne par post
        engagement_rate = round(total_engagement / post_count, 2)

    return {
        "followers": followers,
        "engagement_rate": engagement_rate,
        "reach": None if has_linkedin else total_reach,
        "post_count": post_count,
        "total_engagement": total_engagement,
        "comments": _safe_int(posts.get("comments")) or 0,
        "clicks": None if has_linkedin else total_clicks,
        "shares": _safe_int(posts.get("total_shares")) or 0,
    }


def _fetch_evolution(db: Session, connection_ids: list[int]) -> list[dict[str, Any]]:
    """Engagement agrégé par mois de publication (tous les posts synchronisés)."""
    if not connection_ids:
        return []
    rows = db.execute(
        text(
            """
            SELECT
                TO_CHAR(DATE_TRUNC('month', published_at), 'YYYY-MM') AS date,
                COALESCE(
                    SUM(COALESCE(likes, 0) + COALESCE(comments, 0) + COALESCE(shares, 0)),
                    0
                )::float AS value
            FROM social_posts
            WHERE connection_id = ANY(:connection_ids)
            GROUP BY DATE_TRUNC('month', published_at)
            ORDER BY DATE_TRUNC('month', published_at) ASC
            """
        ),
        {"connection_ids": connection_ids},
    ).mappings().all()
    return [dict(r) for r in rows]


def _fetch_top_posts(db: Session, connection_ids: list[int]) -> list[dict[str, Any]]:
    if not connection_ids:
        return []
    post_limit = max(int(settings.SOCIAL_ETL_TOP_POSTS_DISPLAY or 5), 1)
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
            ORDER BY (COALESCE(sp.likes, 0) + COALESCE(sp.comments, 0) + COALESCE(sp.shares, 0)) DESC,
                     sp.published_at DESC
            LIMIT :post_limit
            """
        ),
        {"connection_ids": connection_ids, "post_limit": post_limit},
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

    has_linkedin = any(
        platform_by_id.get(cid) == "linkedin" for cid in connection_ids
    )
    linkedin_ids = {
        cid for cid in connection_ids if platform_by_id.get(cid) == "linkedin"
    }
    pf = (platform or "global").strip().lower()
    posts_aggregates = _fetch_posts_aggregates(
        db,
        connection_ids,
        reach_filter_engagement=(pf == "facebook"),
    )
    kpis = _build_kpis(
        followers=(
            _fetch_followers_total(
                rows,
                linkedin_connection_ids=linkedin_ids if pf in ("linkedin", "global") else None,
            )
            or (
                _fetch_daily_network_size(db, list(linkedin_ids))
                if pf == "linkedin" and linkedin_ids
                else None
            )
        ),
        posts=posts_aggregates,
        has_linkedin=has_linkedin,
        linkedin_only=(pf == "linkedin"),
    )

    return {
        "kpis": kpis,
        "evolution": _fetch_evolution(db, connection_ids),
        "top_posts": _fetch_top_posts(db, connection_ids),
        "reactions_breakdown": posts_aggregates.get("reactions_breakdown") or {},
    }
