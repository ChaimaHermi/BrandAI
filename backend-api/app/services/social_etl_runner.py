"""Lance le pipeline social ETL (backend-ai) pour une idée."""

from __future__ import annotations

import asyncio
import logging
import sys
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from app.core.config import settings
import app.services.social_connection_service as social_svc

logger = logging.getLogger(__name__)


def backend_ai_root() -> Path:
    raw = (settings.BACKEND_AI_ROOT or "").strip()
    if raw:
        return Path(raw).resolve()
    return Path(__file__).resolve().parents[2].parent / "backend-ai"


def build_social_etl_config(
    db,
    *,
    idea_id: int,
    user_id: int,
    post_limit: int | None = None,
) -> tuple[dict[str, Any] | None, list[str], str | None]:
    """
    Prépare ``{"idea_id", "accounts"}`` pour le pipeline.

    Retourne ``(cfg | None, warnings, erreur)`` où ``erreur`` est un message si aucun compte.
    """
    limit = int(post_limit if post_limit is not None else settings.SOCIAL_ETL_POST_LIMIT)
    accounts, warnings = social_svc.build_social_etl_pipeline_accounts(
        db,
        idea_id,
        user_id,
        post_limit=limit,
        apify_token=settings.APIFY_TOKEN or None,
        apify_actor_id=settings.APIFY_LINKEDIN_ACTOR_ID or None,
    )
    if not accounts:
        return (
            None,
            warnings,
            "Aucune source exploitable : connectez au moins une page Facebook / Instagram "
            "ou configurez LinkedIn (URL profil + APIFY_TOKEN dans l’API).",
        )
    return {"idea_id": idea_id, "accounts": accounts}, warnings, None


def run_social_etl_for_idea(
    db,
    *,
    idea_id: int,
    user_id: int,
    post_limit: int | None = None,
) -> tuple[dict, list[str]]:
    """
    Exécute extraction + normalisation pour les connexions sociales de l'idée.

    Retourne ``({"output_dir": str, "runs": [...]}, warnings)``.
    """
    cfg, warnings, err = build_social_etl_config(db, idea_id=idea_id, user_id=user_id, post_limit=post_limit)
    if err or not cfg:
        raise ValueError(err or "Configuration pipeline vide.")

    root = backend_ai_root()
    if not root.is_dir():
        raise FileNotFoundError(
            f"Dossier backend-ai introuvable : {root}. Définissez BACKEND_AI_ROOT dans .env."
        )

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from social_etl.pipeline import run_pipeline_async  # noqa: WPS433

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

    root = backend_ai_root()
    if not root.is_dir():
        yield {"type": "fatal", "detail": f"Dossier backend-ai introuvable : {root}"}
        return

    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from social_etl.pipeline import run_pipeline_events  # noqa: WPS433

    async for ev in run_pipeline_events(cfg):
        yield ev
