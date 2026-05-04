"""Background worker: auto-publish scheduled posts when their time arrives."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_

from app.core.database import SessionLocal
from app.core.social_token_crypto import decrypt_json_payload
from app.models.notification import Notification
from app.models.scheduled_publication import ScheduledPublication
from app.models.user_social_connection import UserSocialConnection
from app.services.notification_service import create_notification
from app.services.platform_publisher import publish_to_platform

logger = logging.getLogger("brandai.scheduled_publisher")

POLL_INTERVAL = 30
MAX_RETRIES = 3
UPCOMING_MINUTES = 15


def _get_social_tokens(db, idea_id: int, user_id: int, platform: str) -> dict:
    provider = "linkedin" if platform == "linkedin" else "meta"
    row = (
        db.query(UserSocialConnection)
        .filter(
            UserSocialConnection.idea_id == idea_id,
            UserSocialConnection.user_id == user_id,
            UserSocialConnection.provider == provider,
        )
        .first()
    )
    if not row:
        raise RuntimeError(f"Aucune connexion {provider} trouvée. Reconnectez votre compte.")
    return decrypt_json_payload(row.payload_encrypted)


_PLATFORM_LABEL = {
    "facebook": "Facebook",
    "instagram": "Instagram",
    "linkedin": "LinkedIn",
}


async def _publish_one(db, pub: ScheduledPublication) -> None:
    pub.status = "publishing"
    pub.attempt_count += 1
    db.commit()

    try:
        tokens = _get_social_tokens(db, pub.idea_id, pub.user_id, pub.platform)
        result = await publish_to_platform(
            platform=pub.platform,
            caption=pub.caption_snapshot,
            image_url=pub.image_url_snapshot,
            social_tokens=tokens,
        )
        pub.status = "published"
        pub.published_at = datetime.now(timezone.utc)
        pub.external_post_id = str(
            result.get("id") or result.get("creation_id") or ""
        )[:255]
        pub.last_error = None
        db.commit()

        label = _PLATFORM_LABEL.get(pub.platform, pub.platform)
        snippet = (pub.title or pub.caption_snapshot[:40]).rstrip()
        create_notification(
            db,
            user_id=pub.user_id,
            type="publication_succeeded",
            title=f"Post publié sur {label}",
            message=f"Votre post « {snippet}… » a été publié avec succès. Consultez votre {label} !",
            idea_id=pub.idea_id,
            scheduled_publication_id=pub.id,
            platform=pub.platform,
        )
        logger.info("published sp=%s platform=%s", pub.id, pub.platform)

    except Exception as exc:
        error_msg = str(exc)[:500]
        pub.last_error = error_msg
        if pub.attempt_count >= MAX_RETRIES:
            pub.status = "failed"
            create_notification(
                db,
                user_id=pub.user_id,
                type="publication_failed",
                title=f"Échec publication {pub.platform}",
                message=f"Après {MAX_RETRIES} tentatives : {error_msg[:200]}",
                idea_id=pub.idea_id,
                scheduled_publication_id=pub.id,
                platform=pub.platform,
            )
        else:
            pub.status = "scheduled"
        db.commit()
        logger.warning(
            "failed sp=%s attempt=%s error=%s",
            pub.id, pub.attempt_count, error_msg[:120],
        )


def _send_upcoming_notifications(db) -> None:
    now = datetime.now(timezone.utc)
    window_start = now + timedelta(minutes=UPCOMING_MINUTES - 2)
    window_end = now + timedelta(minutes=UPCOMING_MINUTES + 2)

    pubs = (
        db.query(ScheduledPublication)
        .filter(
            ScheduledPublication.status == "scheduled",
            ScheduledPublication.scheduled_at >= window_start,
            ScheduledPublication.scheduled_at <= window_end,
        )
        .all()
    )

    for pub in pubs:
        already = (
            db.query(Notification)
            .filter(
                Notification.user_id == pub.user_id,
                Notification.scheduled_publication_id == pub.id,
                Notification.type == "publication_upcoming",
            )
            .first()
        )
        if already:
            continue

        label = _PLATFORM_LABEL.get(pub.platform, pub.platform)
        snippet = (pub.title or pub.caption_snapshot[:40]).rstrip()
        create_notification(
            db,
            user_id=pub.user_id,
            type="publication_upcoming",
            title=f"Publication imminente — {label}",
            message=f"Votre post « {snippet}… » sera publié dans ~{UPCOMING_MINUTES} min.",
            idea_id=pub.idea_id,
            scheduled_publication_id=pub.id,
            platform=pub.platform,
        )


async def run_publisher_loop() -> None:
    logger.info("Worker démarré (poll=%ss, retries=%s)", POLL_INTERVAL, MAX_RETRIES)
    while True:
        try:
            db = SessionLocal()
            try:
                _send_upcoming_notifications(db)

                now = datetime.now(timezone.utc)
                due = (
                    db.query(ScheduledPublication)
                    .filter(
                        and_(
                            ScheduledPublication.status == "scheduled",
                            ScheduledPublication.scheduled_at <= now,
                            ScheduledPublication.attempt_count < MAX_RETRIES,
                        )
                    )
                    .order_by(ScheduledPublication.scheduled_at.asc())
                    .limit(10)
                    .all()
                )
                for pub in due:
                    await _publish_one(db, pub)
            finally:
                db.close()
        except Exception as exc:
            logger.error("loop error: %s", exc)

        await asyncio.sleep(POLL_INTERVAL)
