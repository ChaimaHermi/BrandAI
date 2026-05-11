"""Lance le pipeline social ETL pour une idée.

Le pipeline ETL (extraction Meta / LinkedIn / Apify, normalisation, chargement DB,
calcul des KPIs) reside desormais dans `app.social_etl`. Ce runner ne fait que
preparer la configuration et invoquer le pipeline local — plus aucune dependance
vers backend-ai.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy import text

from app.core.config import settings
import app.services.social_connection_service as social_svc
from app.social_etl.pipeline import run_pipeline_async, run_pipeline_events

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def build_social_etl_config(
    db,
    *,
    idea_id: int,
    user_id: int,
    post_limit: int | None = None,
    retry_failed_only: bool = True,
) -> tuple[dict[str, Any] | None, list[str], str | None]:
    """
    Prépare ``{"idea_id", "accounts"}`` pour le pipeline.

    Retourne ``(cfg | None, warnings, erreur)`` où ``erreur`` est un message si aucun compte.
    """
    limit = int(post_limit if post_limit is not None else settings.SOCIAL_ETL_POST_LIMIT)
    logger.info(
        "social_etl config start idea_id=%s user_id=%s retry_failed_only=%s post_limit=%s",
        idea_id,
        user_id,
        retry_failed_only,
        limit,
    )
    accounts, warnings = social_svc.build_social_etl_pipeline_accounts(
        db,
        idea_id,
        user_id,
        post_limit=limit,
        apify_token=settings.APIFY_TOKEN or None,
        apify_actor_id=settings.APIFY_LINKEDIN_ACTOR_ID or None,
    )

    if retry_failed_only and accounts:
        conn_ids = [int(a["connection_id"]) for a in accounts if isinstance(a.get("connection_id"), int)]
        if conn_ids:
            try:
                rows = db.execute(
                    text(
                        """
                        SELECT DISTINCT ON (connection_id)
                               connection_id, status, sync_start
                        FROM sync_logs
                        WHERE connection_id = ANY(:ids)
                        ORDER BY connection_id, sync_start DESC, id DESC
                        """
                    ),
                    {"ids": conn_ids},
                ).fetchall()
                latest_status_by_connection = {int(r[0]): str(r[1] or "").strip().lower() for r in rows}
                filtered_accounts: list[dict[str, Any]] = []
                skipped = 0
                for acc in accounts:
                    cid = acc.get("connection_id")
                    status = latest_status_by_connection.get(int(cid)) if isinstance(cid, int) else None
                    if status == "success":
                        skipped += 1
                        logger.info(
                            "social_etl account skipped connection_id=%s platform=%s reason=already_success",
                            cid,
                            acc.get("platform"),
                        )
                        continue
                    filtered_accounts.append(acc)
                if skipped > 0:
                    warnings.append(
                        f"{skipped} plateforme(s) déjà synchronisée(s) avec succès ignorée(s) (retry failed only)."
                    )
                    logger.info(
                        "social_etl retry_failed_only filtered skipped=%s kept=%s",
                        skipped,
                        len(filtered_accounts),
                    )
                accounts = filtered_accounts
            except Exception:
                # sync_logs may be absent in environments where migration has not run yet.
                logger.exception("social_etl retry_failed_only status lookup failed")

    if not accounts:
        logger.warning(
            "social_etl config empty idea_id=%s warnings=%s apify_token_set=%s",
            idea_id,
            len(warnings),
            bool((settings.APIFY_TOKEN or "").strip()),
        )
        return (
            None,
            warnings,
            "Aucune source exploitable : connectez au moins une page Facebook / Instagram "
            "ou configurez LinkedIn (URL profil + APIFY_TOKEN dans l’API).",
        )
    logger.info(
        "social_etl config ready idea_id=%s accounts=%s warnings=%s",
        idea_id,
        len(accounts),
        len(warnings),
    )
    return {"idea_id": idea_id, "accounts": accounts}, warnings, None


def run_social_etl_for_idea(
    db,
    *,
    idea_id: int,
    user_id: int,
    post_limit: int | None = None,
    retry_failed_only: bool = True,
) -> tuple[dict, list[str]]:
    """
    Exécute extraction + normalisation pour les connexions sociales de l'idée.

    Retourne ``({"output_dir": str, "runs": [...]}, warnings)``.
    """
    logger.info("social_etl run start idea_id=%s user_id=%s", idea_id, user_id)
    cfg, warnings, err = build_social_etl_config(
        db,
        idea_id=idea_id,
        user_id=user_id,
        post_limit=post_limit,
        retry_failed_only=retry_failed_only,
    )
    if err or not cfg:
        logger.warning("social_etl run aborted idea_id=%s reason=%s", idea_id, err)
        raise ValueError(err or "Configuration pipeline vide.")

    logger.info(
        "social_etl pipeline invoke idea_id=%s accounts=%s",
        idea_id,
        len(cfg.get("accounts") or []),
    )
    out_dir, runs = asyncio.run(run_pipeline_async(cfg))
    summary = {"output_dir": str(out_dir.resolve()), "runs": runs}
    logger.info("social_etl done idea_id=%s runs=%s", idea_id, len(runs))
    return summary, warnings


async def stream_social_etl_events(
    cfg: dict[str, Any],
    warnings: list[str],
) -> AsyncIterator[dict[str, Any]]:
    """Événements JSON pour SSE (après lecture DB — ne pas passer la session ici)."""
    if warnings:
        yield {"type": "warnings", "warnings": warnings}

    async for ev in run_pipeline_events(cfg):
        yield ev
