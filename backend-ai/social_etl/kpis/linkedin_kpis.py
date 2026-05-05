from __future__ import annotations

import logging
import sys
from pathlib import Path

import asyncpg

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

logger = logging.getLogger(__name__)

PERIOD_TYPE = "30days"


async def update_daily_engagement(
    conn: asyncpg.Connection,
    connection_id: int,
    *,
    last_30_days_only: bool = True,
) -> None:
    if last_30_days_only:
        await conn.execute(
            """
            DELETE FROM social_daily_engagement
            WHERE connection_id = $1
              AND date >= (CURRENT_DATE - INTERVAL '30 days')::date
            """,
            connection_id,
        )
        await conn.execute(
            """
            INSERT INTO social_daily_engagement (connection_id, date, total_engagement)
            SELECT
                $1 AS connection_id,
                DATE(published_at) AS date,
                COALESCE(SUM(COALESCE(likes, 0) + COALESCE(comments, 0) + COALESCE(shares, 0)), 0)::int AS total_engagement
            FROM social_posts
            WHERE connection_id = $1
              AND published_at >= (CURRENT_DATE - INTERVAL '30 days')
            GROUP BY DATE(published_at)
            ON CONFLICT (connection_id, date) DO UPDATE SET
                total_engagement = EXCLUDED.total_engagement
            """,
            connection_id,
        )
    else:
        await conn.execute(
            """
            INSERT INTO social_daily_engagement (connection_id, date, total_engagement)
            SELECT
                $1 AS connection_id,
                DATE(published_at) AS date,
                COALESCE(SUM(COALESCE(likes, 0) + COALESCE(comments, 0) + COALESCE(shares, 0)), 0)::int AS total_engagement
            FROM social_posts
            WHERE connection_id = $1
            GROUP BY DATE(published_at)
            ON CONFLICT (connection_id, date) DO UPDATE SET
                total_engagement = EXCLUDED.total_engagement
            """,
            connection_id,
        )


async def _fetch_active_connection_ids(conn: asyncpg.Connection) -> list[int]:
    has_is_active = await conn.fetchval(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'social_connections'
              AND column_name = 'is_active'
        )
        """
    )
    if has_is_active:
        rows = await conn.fetch(
            """
            SELECT id
            FROM social_connections
            WHERE platform IN ('linkedin_page', 'linkedin')
              AND (is_active = TRUE OR is_active IS NULL)
            """
        )
    else:
        rows = await conn.fetch(
            """
            SELECT id
            FROM social_connections
            WHERE platform IN ('linkedin_page', 'linkedin')
            """
        )
    return [row["id"] for row in rows]


async def compute_linkedin_kpis(pool: asyncpg.Pool) -> int:
    aggregate_query = """
        WITH period AS (
            SELECT
                (CURRENT_DATE - INTERVAL '30 days')::date AS start_date,
                CURRENT_DATE::date AS end_date
        ),
        posts_scope AS (
            SELECT sp.*
            FROM social_posts sp
            CROSS JOIN period p
            WHERE sp.connection_id = $1
              AND sp.published_at >= p.start_date
        ),
        top_posts_source AS (
            SELECT
                post_external_id,
                LEFT(COALESCE(text, ''), 200) AS text,
                (COALESCE(likes, 0) + COALESCE(comments, 0) + COALESCE(shares, 0)) AS engagement_total,
                permalink_url
            FROM posts_scope
            ORDER BY engagement_total DESC, published_at DESC
            LIMIT 3
        ),
        posts_data AS (
            SELECT
                COUNT(*)::int AS posts_count,
                COALESCE(SUM(COALESCE(likes, 0) + COALESCE(comments, 0) + COALESCE(shares, 0)), 0)::int AS total_engagement,
                COALESCE(SUM(COALESCE(shares, 0)), 0)::int AS shares,
                CASE
                    WHEN COUNT(*) = 0 THEN NULL
                    ELSE JSONB_BUILD_OBJECT(
                        'like', COALESCE(SUM(COALESCE((reactions_breakdown->>'like')::int, 0)), 0),
                        'praise', COALESCE(SUM(COALESCE((reactions_breakdown->>'praise')::int, 0)), 0),
                        'empathy', COALESCE(SUM(COALESCE((reactions_breakdown->>'empathy')::int, 0)), 0),
                        'interest', COALESCE(SUM(COALESCE((reactions_breakdown->>'interest')::int, 0)), 0),
                        'appreciation', COALESCE(SUM(COALESCE((reactions_breakdown->>'appreciation')::int, 0)), 0),
                        'entertainment', COALESCE(SUM(COALESCE((reactions_breakdown->>'entertainment')::int, 0)), 0)
                    )
                END AS reactions_breakdown
            FROM posts_scope
        ),
        top_posts AS (
            SELECT
                COALESCE(
                    JSONB_AGG(
                        JSONB_BUILD_OBJECT(
                            'post_external_id', post_external_id,
                            'text', text,
                            'engagement_total', engagement_total,
                            'permalink_url', permalink_url
                        )
                        ORDER BY engagement_total DESC
                    ),
                    '[]'::jsonb
                ) AS value
            FROM top_posts_source
        ),
        followers AS (
            SELECT followers_count
            FROM social_daily_insights
            WHERE connection_id = $1
            ORDER BY date DESC
            LIMIT 1
        )
        SELECT
            p.start_date,
            p.end_date,
            (SELECT followers_count FROM followers) AS followers_count,
            COALESCE(pd.posts_count, 0) AS posts_count,
            COALESCE(pd.total_engagement, 0) AS total_engagement,
            COALESCE(pd.shares, 0) AS shares,
            pd.reactions_breakdown,
            tp.value AS top_posts
        FROM period p
        LEFT JOIN posts_data pd ON TRUE
        LEFT JOIN top_posts tp ON TRUE
    """

    upsert_query = """
        INSERT INTO social_kpi_summary (
            connection_id,
            period_type,
            period_start,
            period_end,
            followers_count,
            posts_count,
            total_engagement,
            total_reach,
            engagement_rate,
            clicks,
            shares,
            reactions_breakdown,
            top_posts
        )
        VALUES (
            $1,
            '30days',
            $2,
            $3,
            $4,
            $5,
            $6,
            NULL,
            $7,
            NULL,
            $8,
            $9,
            $10
        )
        ON CONFLICT (connection_id, period_type, period_start) DO UPDATE SET
            period_end = EXCLUDED.period_end,
            followers_count = EXCLUDED.followers_count,
            posts_count = EXCLUDED.posts_count,
            total_engagement = EXCLUDED.total_engagement,
            total_reach = EXCLUDED.total_reach,
            engagement_rate = EXCLUDED.engagement_rate,
            clicks = EXCLUDED.clicks,
            shares = EXCLUDED.shares,
            reactions_breakdown = EXCLUDED.reactions_breakdown,
            top_posts = EXCLUDED.top_posts,
            calculated_at = NOW()
    """

    async with pool.acquire() as conn:
        connection_ids = await _fetch_active_connection_ids(conn)
        updated = 0
        for connection_id in connection_ids:
            await _compute_linkedin_kpis_for_connection(conn, connection_id, aggregate_query, upsert_query)
            updated += 1
        return updated


async def compute_linkedin_kpis_for_connection(pool: asyncpg.Pool, connection_id: int) -> None:
    aggregate_query = """
        WITH period AS (
            SELECT
                (CURRENT_DATE - INTERVAL '30 days')::date AS start_date,
                CURRENT_DATE::date AS end_date
        ),
        posts_scope AS (
            SELECT sp.*
            FROM social_posts sp
            CROSS JOIN period p
            WHERE sp.connection_id = $1
              AND sp.published_at >= p.start_date
        ),
        top_posts_source AS (
            SELECT
                post_external_id,
                LEFT(COALESCE(text, ''), 200) AS text,
                (COALESCE(likes, 0) + COALESCE(comments, 0) + COALESCE(shares, 0)) AS engagement_total,
                permalink_url
            FROM posts_scope
            ORDER BY engagement_total DESC, published_at DESC
            LIMIT 3
        ),
        posts_data AS (
            SELECT
                COUNT(*)::int AS posts_count,
                COALESCE(SUM(COALESCE(likes, 0) + COALESCE(comments, 0) + COALESCE(shares, 0)), 0)::int AS total_engagement,
                COALESCE(SUM(COALESCE(shares, 0)), 0)::int AS shares,
                CASE
                    WHEN COUNT(*) = 0 THEN NULL
                    ELSE JSONB_BUILD_OBJECT(
                        'like', COALESCE(SUM(COALESCE((reactions_breakdown->>'like')::int, 0)), 0),
                        'praise', COALESCE(SUM(COALESCE((reactions_breakdown->>'praise')::int, 0)), 0),
                        'empathy', COALESCE(SUM(COALESCE((reactions_breakdown->>'empathy')::int, 0)), 0),
                        'interest', COALESCE(SUM(COALESCE((reactions_breakdown->>'interest')::int, 0)), 0),
                        'appreciation', COALESCE(SUM(COALESCE((reactions_breakdown->>'appreciation')::int, 0)), 0),
                        'entertainment', COALESCE(SUM(COALESCE((reactions_breakdown->>'entertainment')::int, 0)), 0)
                    )
                END AS reactions_breakdown
            FROM posts_scope
        ),
        top_posts AS (
            SELECT
                COALESCE(
                    JSONB_AGG(
                        JSONB_BUILD_OBJECT(
                            'post_external_id', post_external_id,
                            'text', text,
                            'engagement_total', engagement_total,
                            'permalink_url', permalink_url
                        )
                        ORDER BY engagement_total DESC
                    ),
                    '[]'::jsonb
                ) AS value
            FROM top_posts_source
        ),
        followers AS (
            SELECT followers_count
            FROM social_daily_insights
            WHERE connection_id = $1
            ORDER BY date DESC
            LIMIT 1
        )
        SELECT
            p.start_date,
            p.end_date,
            (SELECT followers_count FROM followers) AS followers_count,
            COALESCE(pd.posts_count, 0) AS posts_count,
            COALESCE(pd.total_engagement, 0) AS total_engagement,
            COALESCE(pd.shares, 0) AS shares,
            pd.reactions_breakdown,
            tp.value AS top_posts
        FROM period p
        LEFT JOIN posts_data pd ON TRUE
        LEFT JOIN top_posts tp ON TRUE
    """
    upsert_query = """
        INSERT INTO social_kpi_summary (
            connection_id, period_type, period_start, period_end, followers_count, posts_count,
            total_engagement, total_reach, engagement_rate, clicks, shares, reactions_breakdown, top_posts
        ) VALUES ($1, '30days', $2, $3, $4, $5, $6, NULL, $7, NULL, $8, $9, $10)
        ON CONFLICT (connection_id, period_type, period_start) DO UPDATE SET
            period_end = EXCLUDED.period_end,
            followers_count = EXCLUDED.followers_count,
            posts_count = EXCLUDED.posts_count,
            total_engagement = EXCLUDED.total_engagement,
            total_reach = EXCLUDED.total_reach,
            engagement_rate = EXCLUDED.engagement_rate,
            clicks = EXCLUDED.clicks,
            shares = EXCLUDED.shares,
            reactions_breakdown = EXCLUDED.reactions_breakdown,
            top_posts = EXCLUDED.top_posts,
            calculated_at = NOW()
    """
    async with pool.acquire() as conn:
        await _compute_linkedin_kpis_for_connection(conn, connection_id, aggregate_query, upsert_query)


async def _compute_linkedin_kpis_for_connection(
    conn: asyncpg.Connection,
    connection_id: int,
    aggregate_query: str,
    upsert_query: str,
) -> None:
    result = await conn.fetchrow(aggregate_query, connection_id)
    if result is None:
        return
    await conn.execute(
        upsert_query,
        connection_id,
        result["start_date"],
        result["end_date"],
        result["followers_count"],
        result["posts_count"],
        result["total_engagement"],
        round((result["total_engagement"] * 100.0) / result["followers_count"], 2)
        if result["followers_count"] and result["followers_count"] > 0
        else None,
        result["shares"],
        result["reactions_breakdown"],
        result["top_posts"],
    )
    await update_daily_engagement(conn, connection_id, last_30_days_only=True)
    logger.info("linkedin_kpis upserted connection_id=%s", connection_id)
