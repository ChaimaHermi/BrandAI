"""Notification REST + SSE stream routes."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
import app.services.notification_service as notif_svc
from app.schemas.notification import NotificationListOut, NotificationOut

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListOut)
def list_notifications(
    limit: int = Query(50, ge=1, le=200),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows, unread_count = notif_svc.list_notifications(
        db, user_id=current_user.id, limit=limit, unread_only=unread_only,
    )
    items = [NotificationOut.model_validate(r) for r in rows]
    return NotificationListOut(items=items, total=len(items), unread_count=unread_count)


@router.patch("/{notification_id}/read", status_code=204)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif_svc.mark_read(db, user_id=current_user.id, notification_id=notification_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/read-all", status_code=204)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif_svc.mark_all_read(db, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/stream")
async def notification_stream(
    token: str = Query(..., description="JWT bearer token (EventSource can't send headers)"),
    db: Session = Depends(get_db),
):
    user_id = decode_access_token(token)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    q = notif_svc.subscribe_sse(user.id)

    async def event_generator():
        try:
            while True:
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield {
                        "event": "notification",
                        "data": json.dumps(payload, ensure_ascii=False),
                    }
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": ""}
        except asyncio.CancelledError:
            pass
        finally:
            notif_svc.unsubscribe_sse(user.id, q)

    return EventSourceResponse(event_generator())
