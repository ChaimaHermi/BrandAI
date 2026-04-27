"""Notification CRUD + SSE push helpers."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from app.models.notification import Notification

logger = logging.getLogger("brandai.notifications")

_sse_queues: dict[int, list[asyncio.Queue]] = defaultdict(list)


def _notify_sse(user_id: int, payload: dict[str, Any]) -> None:
    for q in _sse_queues.get(user_id, []):
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            pass


def subscribe_sse(user_id: int) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=64)
    _sse_queues[user_id].append(q)
    return q


def unsubscribe_sse(user_id: int, q: asyncio.Queue) -> None:
    try:
        _sse_queues[user_id].remove(q)
    except ValueError:
        pass
    if not _sse_queues[user_id]:
        del _sse_queues[user_id]


def create_notification(
    db: Session,
    *,
    user_id: int,
    type: str,
    title: str,
    message: str,
    idea_id: int | None = None,
    scheduled_publication_id: int | None = None,
    platform: str | None = None,
) -> Notification:
    row = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        idea_id=idea_id,
        scheduled_publication_id=scheduled_publication_id,
        platform=platform,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    payload = {
        "id": row.id,
        "type": row.type,
        "title": row.title,
        "message": row.message,
        "platform": row.platform,
        "idea_id": row.idea_id,
        "scheduled_publication_id": row.scheduled_publication_id,
        "is_read": False,
        "created_at": row.created_at.isoformat(),
    }
    _notify_sse(user_id, payload)
    return row


def list_notifications(
    db: Session,
    *,
    user_id: int,
    limit: int = 50,
    unread_only: bool = False,
) -> tuple[list[Notification], int]:
    q = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        q = q.filter(Notification.is_read == False)  # noqa: E712
    total_unread = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .count()
    )
    rows = q.order_by(Notification.created_at.desc()).limit(limit).all()
    return rows, total_unread


def mark_read(db: Session, *, user_id: int, notification_id: int) -> bool:
    row = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if not row:
        return False
    row.is_read = True
    db.commit()
    return True


def mark_all_read(db: Session, *, user_id: int) -> int:
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .update({"is_read": True})
    )
    db.commit()
    return count
