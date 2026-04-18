from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.generated_content import GeneratedContent
from app.models.idea import Idea
from app.schemas.generated_content import GeneratedContentCreate, GeneratedContentPatch


def _get_owned_idea(db: Session, idea_id: int, user_id: int) -> Idea | None:
    return (
        db.query(Idea)
        .filter(Idea.id == idea_id, Idea.user_id == user_id)
        .first()
    )


def create_generated_content(
    db: Session,
    *,
    idea_id: int,
    user_id: int,
    data: GeneratedContentCreate,
) -> GeneratedContent | None:
    if not _get_owned_idea(db, idea_id, user_id):
        return None
    row = GeneratedContent(
        idea_id=idea_id,
        platform=data.platform,
        caption=data.caption.strip(),
        image_url=(data.image_url or "").strip() or None,
        char_count=data.char_count,
        status="generated",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_generated_contents(
    db: Session, *, idea_id: int, user_id: int
) -> list[GeneratedContent] | None:
    """Retourne None si l’idée n’existe pas ou n’appartient pas à l’utilisateur."""
    if not _get_owned_idea(db, idea_id, user_id):
        return None
    return (
        db.query(GeneratedContent)
        .filter(GeneratedContent.idea_id == idea_id)
        .order_by(GeneratedContent.created_at.desc())
        .all()
    )


def count_generated_contents(db: Session, *, idea_id: int, user_id: int) -> int | None:
    """Retourne None si idée introuvable / accès refusé."""
    if not _get_owned_idea(db, idea_id, user_id):
        return None
    return (
        db.query(GeneratedContent)
        .filter(GeneratedContent.idea_id == idea_id)
        .count()
    )


def patch_generated_content(
    db: Session,
    *,
    idea_id: int,
    content_id: int,
    user_id: int,
    patch: GeneratedContentPatch,
) -> GeneratedContent | None:
    if not _get_owned_idea(db, idea_id, user_id):
        return None
    row = (
        db.query(GeneratedContent)
        .filter(
            GeneratedContent.id == content_id,
            GeneratedContent.idea_id == idea_id,
        )
        .first()
    )
    if not row:
        return None

    if patch.status is not None:
        row.status = patch.status
        if patch.status == "published":
            row.published_at = datetime.now(timezone.utc)
            row.publish_error = None
        elif patch.status == "publish_failed":
            row.published_at = None
            if patch.publish_error is not None:
                row.publish_error = patch.publish_error
        elif patch.status == "generated":
            row.published_at = None
            row.publish_error = None
    elif patch.publish_error is not None:
        row.publish_error = patch.publish_error

    db.commit()
    db.refresh(row)
    return row
