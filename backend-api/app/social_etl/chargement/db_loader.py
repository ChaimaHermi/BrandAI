from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any

import asyncpg


def _to_int_or_none(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.strip():
        try:
            return int(float(value.strip()))
        except ValueError:
            return None
    return None


def _to_datetime_or_now(value: Any) -> datetime:
    dt: datetime
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str) and value.strip():
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)

    # social_posts.published_at is TIMESTAMP (without timezone):
    # normalize every value to UTC-naive to avoid asyncpg aware/naive mismatch.
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _to_json_text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        txt = value.strip()
        return txt if txt else None
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return None


async def upsert_posts(
    connection_id: int,
    posts: list[dict[str, Any]],
    pool: asyncpg.Pool,
) -> None:
    if not posts:
        return

    query = """
        INSERT INTO social_posts (
            connection_id,
            post_external_id,
            published_at,
            text,
            media_type,
            media_url,
            permalink_url,
            likes,
            comments,
            shares,
            saves,
            clicks,
            reach,
            impressions,
            video_views,
            reactions_breakdown,
            updated_at
        )
        VALUES (
            $1,  $2,  $3,  $4,  $5,  $6,  $7,  $8,  $9,  $10, $11,
            $12, $13, $14, $15, $16::jsonb, NOW()
        )
        ON CONFLICT (post_external_id) DO NOTHING
    """

    records: list[tuple[Any, ...]] = []
    for post in posts:
        if not isinstance(post, dict):
            continue
        post_external_id = str(post.get("post_external_id") or "").strip()
        if not post_external_id:
            continue

        records.append(
            (
                connection_id,
                post_external_id,
                _to_datetime_or_now(post.get("published_at")),
                post.get("text"),
                post.get("media_type"),
                post.get("media_url"),
                post.get("permalink_url"),
                _to_int_or_none(post.get("likes")) or 0,
                _to_int_or_none(post.get("comments")) or 0,
                _to_int_or_none(post.get("shares")) or 0,
                _to_int_or_none(post.get("saves")),
                _to_int_or_none(post.get("clicks")),
                _to_int_or_none(post.get("reach")),
                _to_int_or_none(post.get("impressions")),
                _to_int_or_none(post.get("video_views")),
                json.dumps(post.get("reactions_breakdown"), ensure_ascii=False)
                if post.get("reactions_breakdown") is not None
                else None,
            )
        )

    if not records:
        return

    async with pool.acquire() as conn:
        await conn.executemany(query, records)


async def upsert_daily_insights(
    connection_id: int,
    insights: list[dict[str, Any]],
    pool: asyncpg.Pool,
) -> None:
    if not insights:
        return

    query = """
        INSERT INTO social_daily_insights (
            connection_id,
            date,
            followers_count,
            reach,
            impressions,
            post_engagements
        )
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (connection_id, date) DO UPDATE SET
            followers_count = EXCLUDED.followers_count,
            reach = EXCLUDED.reach,
            impressions = EXCLUDED.impressions,
            post_engagements = EXCLUDED.post_engagements
    """

    records: list[tuple[Any, ...]] = []
    for row in insights:
        if not isinstance(row, dict):
            continue
        d = row.get("date")
        if isinstance(d, datetime):
            day = d.date()
        elif isinstance(d, date):
            day = d
        elif isinstance(d, str) and d.strip():
            day = date.fromisoformat(d.strip()[:10])
        else:
            day = datetime.now(timezone.utc).date()

        records.append(
            (
                connection_id,
                day,
                _to_int_or_none(row.get("followers_count")),
                _to_int_or_none(row.get("reach")),
                _to_int_or_none(row.get("impressions")),
                _to_int_or_none(row.get("post_engagements")),
            )
        )

    if not records:
        return

    async with pool.acquire() as conn:
        await conn.executemany(query, records)


async def log_sync(
    connection_id: int | None,
    status: str,
    posts_fetched: int,
    error_message: str | None,
    pool: asyncpg.Pool,
    sync_start: datetime,
) -> None:
    query = """
        INSERT INTO sync_logs (
            connection_id,
            sync_start,
            sync_end,
            status,
            posts_fetched,
            error_message
        )
        VALUES ($1, $2, NOW(), $3, $4, $5)
    """
    async with pool.acquire() as conn:
        await conn.execute(
            query,
            connection_id,
            sync_start,
            status,
            int(posts_fetched or 0),
            error_message,
        )


async def get_active_connections(pool: asyncpg.Pool) -> list[dict[str, Any]]:
    async with pool.acquire() as conn:
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
            rows = await conn.fetch("SELECT * FROM social_connections WHERE is_active = TRUE")
        else:
            rows = await conn.fetch("SELECT * FROM social_connections")
    return [dict(row) for row in rows]
