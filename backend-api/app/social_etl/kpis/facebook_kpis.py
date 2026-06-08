from __future__ import annotations

import logging

import asyncpg

logger = logging.getLogger(__name__)

PERIOD_TYPE = "synced"

SYNCED_PERIOD_CTE = """
        WITH posts_scope AS (
            SELECT sp.*
            FROM social_posts sp
            WHERE sp.connection_id = $1
        ),
        period AS (
            SELECT
                COALESCE(MIN(DATE(published_at)), CURRENT_DATE)::date AS start_date,
                COALESCE(MAX(DATE(published_at)), CURRENT_DATE)::date AS end_date
            FROM posts_scope
        ),
"""


async def update_daily_engagement(
    conn: asyncpg.Connection,
    connection_id: int,
) -> None:
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
            WHERE platform IN ('facebook_page', 'facebook')
              AND (is_active = TRUE OR is_active IS NULL)
            """
        )
    else:
        rows = await conn.fetch(
            """
            SELECT id
            FROM social_connections
            WHERE platform IN ('facebook_page', 'facebook')
            """
        )
    return [row["id"] for row in rows]


async def compute_facebook_kpis(pool: asyncpg.Pool) -> int:
    aggregate_query = f"""
{SYNCED_PERIOD_CTE}
        posts_with_reach AS (
            SELECT sp.*
            FROM posts_scope sp
            WHERE COALESCE(sp.reach, 0) > 0
        ),
        top_posts_source AS (
            SELECT
                post_external_id,
                LEFT(COALESCE(text, ''), 200) AS text,
                (COALESCE(likes, 0) + COALESCE(comments, 0) + COALESCE(shares, 0)) AS engagement_total,
                permalink_url
            FROM posts_scope
            ORDER BY engagement_total DESC, published_at DESC
            LIMIT 5
        ),
        posts_data AS (
            SELECT
                (SELECT COUNT(*)::int FROM posts_scope) AS posts_count,
                COALESCE(SUM(COALESCE(likes, 0) + COALESCE(comments, 0) + COALESCE(shares, 0)), 0)::int AS total_engagement,
                CASE
                    WHEN COUNT(*) = 0 THEN NULL
                    ELSE COALESCE(SUM(COALESCE(reach, 0)), 0)::int
                END AS total_reach,
                CASE
                    WHEN COUNT(*) = 0 THEN NULL
                    ELSE COALESCE(SUM(COALESCE(clicks, 0)), 0)::int
                END AS clicks,
                COALESCE(SUM(COALESCE(shares, 0)), 0)::int AS shares,
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
            FROM posts_with_reach
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
            pd.total_reach,
            pd.clicks,
            COALESCE(pd.shares, 0) AS shares,
            pd.reactions_breakdown,
            tp.value AS top_posts
        FROM period p
        LEFT JOIN posts_data pd ON TRUE
        LEFT JOIN top_posts tp ON TRUE
    """

    upsert_query = f"""
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
            '{PERIOD_TYPE}',
            $2,
            $3,
            $4,
            $5,
            $6,
            $7,
            $8,
            $9,
            $10,
            $11,
            $12
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
            await _compute_facebook_kpis_for_connection(conn, connection_id, aggregate_query, upsert_query)
            updated += 1
        return updated


async def compute_facebook_kpis_for_connection(pool: asyncpg.Pool, connection_id: int) -> None:
    aggregate_query = f"""
{SYNCED_PERIOD_CTE}
        posts_with_reach AS (
            SELECT sp.*
            FROM posts_scope sp
            WHERE COALESCE(sp.reach, 0) > 0
        ),
        top_posts_source AS (
            SELECT
                post_external_id,
                LEFT(COALESCE(text, ''), 200) AS text,
                (COALESCE(likes, 0) + COALESCE(comments, 0) + COALESCE(shares, 0)) AS engagement_total,
                permalink_url
            FROM posts_scope
            ORDER BY engagement_total DESC, published_at DESC
            LIMIT 5
        ),
        posts_data AS (
            SELECT
                (SELECT COUNT(*)::int FROM posts_scope) AS posts_count,
                COALESCE(SUM(COALESCE(likes, 0) + COALESCE(comments, 0) + COALESCE(shares, 0)), 0)::int AS total_engagement,
                CASE
                    WHEN COUNT(*) = 0 THEN NULL
                    ELSE COALESCE(SUM(COALESCE(reach, 0)), 0)::int
                END AS total_reach,
                CASE
                    WHEN COUNT(*) = 0 THEN NULL
                    ELSE COALESCE(SUM(COALESCE(clicks, 0)), 0)::int
                END AS clicks,
                COALESCE(SUM(COALESCE(shares, 0)), 0)::int AS shares,
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
            FROM posts_with_reach
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
            pd.total_reach,
            pd.clicks,
            COALESCE(pd.shares, 0) AS shares,
            pd.reactions_breakdown,
            tp.value AS top_posts
        FROM period p
        LEFT JOIN posts_data pd ON TRUE
        LEFT JOIN top_posts tp ON TRUE
    """
    upsert_query = f"""
        INSERT INTO social_kpi_summary (
            connection_id, period_type, period_start, period_end, followers_count, posts_count,
            total_engagement, total_reach, engagement_rate, clicks, shares, reactions_breakdown, top_posts
        ) VALUES ($1, '{PERIOD_TYPE}', $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
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
        await _compute_facebook_kpis_for_connection(conn, connection_id, aggregate_query, upsert_query)


async def _compute_facebook_kpis_for_connection(
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
        result["total_reach"],
        round((result["total_engagement"] * 100.0) / result["total_reach"], 2)
        if result["total_reach"] and result["total_reach"] > 0
        else None,
        result["clicks"],
        result["shares"],
        result["reactions_breakdown"],
        result["top_posts"],
    )
    await update_daily_engagement(conn, connection_id)
    logger.info("facebook_kpis upserted connection_id=%s", connection_id)
