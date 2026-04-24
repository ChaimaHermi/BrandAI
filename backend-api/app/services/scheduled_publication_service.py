from datetime import datetime, timedelta, timezone

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.generated_content import GeneratedContent
from app.models.idea import Idea
from app.models.scheduled_publication import ScheduledPublication
from app.schemas.scheduled_publication import (
    ScheduledPublicationCreate,
    ScheduledPublicationPatch,
)


def _get_owned_idea(db: Session, idea_id: int, user_id: int) -> Idea | None:
    return (
        db.query(Idea)
        .filter(Idea.id == idea_id, Idea.user_id == user_id)
        .first()
    )


def _get_generated_for_idea(
    db: Session,
    *,
    idea_id: int,
    content_id: int,
) -> GeneratedContent | None:
    return (
        db.query(GeneratedContent)
        .filter(
            GeneratedContent.id == content_id,
            GeneratedContent.idea_id == idea_id,
        )
        .first()
    )


def create_scheduled_publication(
    db: Session,
    *,
    idea_id: int,
    user_id: int,
    data: ScheduledPublicationCreate,
) -> ScheduledPublication | None:
    idea = _get_owned_idea(db, idea_id, user_id)
    if not idea:
        return None
    gc = _get_generated_for_idea(db, idea_id=idea_id, content_id=data.generated_content_id)
    if not gc:
        return None

    when = data.scheduled_at
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    else:
        when = when.astimezone(timezone.utc)

    now = datetime.now(timezone.utc)
    if when < now - timedelta(minutes=1):
        raise ValueError("scheduled_at doit être dans le futur.")

    row = ScheduledPublication(
        user_id=user_id,
        idea_id=idea_id,
        generated_content_id=gc.id,
        platform=gc.platform,
        caption_snapshot=gc.caption.strip(),
        image_url_snapshot=(gc.image_url or "").strip() or None,
        scheduled_at=when,
        timezone=(data.timezone or "UTC").strip()[:64] if data.timezone else "UTC",
        status="scheduled",
        title=(data.title or "").strip()[:255] or None,
        notes=(data.notes or "").strip() or None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_scheduled_publications(
    db: Session,
    *,
    idea_id: int,
    user_id: int,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[ScheduledPublication] | None:
    if not _get_owned_idea(db, idea_id, user_id):
        return None
    q = db.query(ScheduledPublication).filter(ScheduledPublication.idea_id == idea_id)
    if date_from is not None:
        df = date_from
        if df.tzinfo is None:
            df = df.replace(tzinfo=timezone.utc)
        q = q.filter(ScheduledPublication.scheduled_at >= df)
    if date_to is not None:
        dt = date_to
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        q = q.filter(ScheduledPublication.scheduled_at <= dt)
    return q.order_by(ScheduledPublication.scheduled_at.asc()).all()


def get_scheduled_publication(
    db: Session,
    *,
    idea_id: int,
    schedule_id: int,
    user_id: int,
) -> ScheduledPublication | None:
    if not _get_owned_idea(db, idea_id, user_id):
        return None
    return (
        db.query(ScheduledPublication)
        .filter(
            and_(
                ScheduledPublication.id == schedule_id,
                ScheduledPublication.idea_id == idea_id,
                ScheduledPublication.user_id == user_id,
            )
        )
        .first()
    )


def patch_scheduled_publication(
    db: Session,
    *,
    idea_id: int,
    schedule_id: int,
    user_id: int,
    patch: ScheduledPublicationPatch,
) -> ScheduledPublication | None:
    row = get_scheduled_publication(db, idea_id=idea_id, schedule_id=schedule_id, user_id=user_id)
    if not row:
        return None
    if row.status not in ("scheduled",):
        raise ValueError("Seules les publications au statut « scheduled » peuvent être modifiées.")

    if patch.status == "cancelled":
        row.status = "cancelled"
        db.commit()
        db.refresh(row)
        return row

    if patch.scheduled_at is not None:
        when = patch.scheduled_at
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        else:
            when = when.astimezone(timezone.utc)
        now = datetime.now(timezone.utc)
        if when < now - timedelta(minutes=1):
            raise ValueError("scheduled_at doit être dans le futur.")
        row.scheduled_at = when

    if patch.timezone is not None:
        row.timezone = patch.timezone.strip()[:64] or "UTC"
    if patch.title is not None:
        row.title = patch.title.strip()[:255] or None
    if patch.notes is not None:
        row.notes = patch.notes.strip() or None

    if patch.caption_snapshot is not None:
        row.caption_snapshot = patch.caption_snapshot.strip()
    if patch.image_url_snapshot is not None:
        v = (patch.image_url_snapshot or "").strip()
        row.image_url_snapshot = v or None

    db.commit()
    db.refresh(row)
    return row


def delete_scheduled_publication(
    db: Session,
    *,
    idea_id: int,
    schedule_id: int,
    user_id: int,
) -> bool:
    row = get_scheduled_publication(db, idea_id=idea_id, schedule_id=schedule_id, user_id=user_id)
    if not row:
        return False
    if row.status != "scheduled":
        raise ValueError("Impossible de supprimer : statut différent de « scheduled ».")
    db.delete(row)
    db.commit()
    return True
