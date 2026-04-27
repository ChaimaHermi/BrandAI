from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.idea import Idea
from app.models.website_project import WebsiteProject
from app.schemas.website_project import WebsiteMessageIn, WebsiteProjectPatch


def _require_idea_for_user(db: Session, idea_id: int, user_id: int) -> Idea:
    idea = (
        db.query(Idea)
        .filter(Idea.id == idea_id, Idea.user_id == user_id)
        .first()
    )
    if not idea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Idée introuvable",
        )
    return idea


def get_or_create_website_project(db: Session, idea_id: int, user_id: int) -> WebsiteProject:
    _require_idea_for_user(db, idea_id, user_id)
    row = db.query(WebsiteProject).filter(WebsiteProject.idea_id == idea_id).first()
    if row is None:
        row = WebsiteProject(idea_id=idea_id, status="draft", conversation_json=[])
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def get_website_project(db: Session, idea_id: int, user_id: int) -> WebsiteProject:
    return get_or_create_website_project(db, idea_id, user_id)


def patch_website_project(
    db: Session,
    idea_id: int,
    user_id: int,
    payload: WebsiteProjectPatch,
) -> WebsiteProject:
    row = get_or_create_website_project(db, idea_id, user_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


def append_website_message(
    db: Session,
    idea_id: int,
    user_id: int,
    message: WebsiteMessageIn,
) -> WebsiteProject:
    row = get_or_create_website_project(db, idea_id, user_id)

    conv = list(row.conversation_json or [])
    msg: dict[str, Any] = {
        "id": message.id or f"msg-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        "role": message.role,
        "type": message.type,
        "content": message.content,
        "created_at": (message.created_at or datetime.now(timezone.utc)).isoformat(),
    }
    if message.meta is not None:
        msg["meta"] = message.meta
    conv.append(msg)

    row.conversation_json = conv
    db.commit()
    db.refresh(row)
    return row


def approve_website_project(db: Session, idea_id: int, user_id: int) -> WebsiteProject:
    row = get_or_create_website_project(db, idea_id, user_id)
    now = datetime.now(timezone.utc)
    row.approved = True
    row.approved_at = now
    row.status = "approved"
    db.commit()
    db.refresh(row)
    return row

