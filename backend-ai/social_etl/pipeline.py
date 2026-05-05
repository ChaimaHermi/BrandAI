"""Pipeline social : extraction (API), normalisation puis chargement en DB."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
NORM_DIR = BACKEND_ROOT / "social_etl" / "normalization"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(NORM_DIR) not in sys.path:
    sys.path.insert(0, str(NORM_DIR))

from config.database import create_db_pool  # noqa: E402
from normalize_facebook import build_normalized_facebook  # noqa: E402
from normalize_instagram import build_normalized_instagram  # noqa: E402
from normalize_linkedin import build_normalized_linkedin  # noqa: E402
from social_etl.chargement.db_loader import (  # noqa: E402
    log_sync,
    upsert_daily_insights,
    upsert_posts,
)
from social_etl.extraction.facebook_extractor import extract_facebook  # noqa: E402
from social_etl.extraction.instagram_extractor import extract_instagram  # noqa: E402
from social_etl.extraction.linkedin_extractor import extract_linkedin  # noqa: E402
from social_etl.kpis.facebook_kpis import compute_facebook_kpis_for_connection  # noqa: E402
from social_etl.kpis.instagram_kpis import compute_instagram_kpis_for_connection  # noqa: E402
from social_etl.kpis.linkedin_kpis import compute_linkedin_kpis_for_connection  # noqa: E402

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _validate_config_dict(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("La configuration doit être un objet.")
    accounts = data.get("accounts")
    if not isinstance(accounts, list):
        raise ValueError('La config doit contenir une clé "accounts" (liste).')
    return data


def _load_config(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return _validate_config_dict(raw)


async def _run_one(account: dict[str, Any], pool) -> dict[str, Any]:
    platform = str(account.get("platform") or "").strip().lower()
    token = str(account.get("access_token") or "").strip()
    account_id = str(account.get("account_id") or "").strip()
    connection_id = account.get("connection_id")
    limit = int(account.get("limit") or 10)

    if platform not in ("facebook", "instagram", "linkedin"):
        raise ValueError(f"Plateforme inconnue: {platform!r}")
    if not token or not account_id:
        raise ValueError(f"{platform}: access_token et account_id sont requis.")
    if not isinstance(connection_id, int):
        raise ValueError(f"{platform}: connection_id requis pour le chargement DB.")

    logger.info(
        "social_etl platform start platform=%s connection_id=%s account_id=%s limit=%s",
        platform,
        connection_id,
        account_id,
        limit,
    )
    sync_start = datetime.now(timezone.utc)
    await log_sync(
        connection_id=connection_id,
        status="started",
        posts_fetched=0,
        error_message=None,
        pool=pool,
        sync_start=sync_start,
    )

    try:
        if platform == "facebook":
            raw = await extract_facebook(
                token,
                account_id,
                limit=limit,
                comments_limit=int(account.get("comments_limit") or 100),
                reactions_limit=int(account.get("reactions_limit") or 100),
            )
            normalized = build_normalized_facebook(raw)
        elif platform == "instagram":
            raw = await extract_instagram(
                token,
                account_id,
                limit=limit,
                comments_limit=int(account.get("comments_limit") or 100),
            )
            normalized = build_normalized_instagram(raw)
        else:
            raw = await extract_linkedin(
                token,
                account_id,
                limit=limit,
                actor_id=account.get("actor_id"),
            )
            normalized = build_normalized_linkedin(raw)

        normalized_posts = [
            p for p in (normalized.get("posts") or []) if isinstance(p, dict)
        ]
        logger.info(
            "social_etl platform normalized platform=%s connection_id=%s posts=%s",
            platform,
            connection_id,
            len(normalized_posts),
        )
        await upsert_posts(connection_id, normalized_posts, pool)

        daily_row = {
            "date": datetime.now(timezone.utc).date(),
            "followers_count": normalized.get("followers_count"),
            "reach": normalized.get("reach"),
            "impressions": normalized.get("impressions"),
            "post_engagements": normalized.get("post_engagements"),
        }
        await upsert_daily_insights(connection_id, [daily_row], pool)

        # Chainage ETL -> KPI: recalcul immediat des KPIs 30 jours
        # pour la connexion dont le chargement vient de reussir.
        if platform == "facebook":
            await compute_facebook_kpis_for_connection(pool, connection_id)
        elif platform == "instagram":
            await compute_instagram_kpis_for_connection(pool, connection_id)
        else:
            await compute_linkedin_kpis_for_connection(pool, connection_id)

        await log_sync(
            connection_id=connection_id,
            status="success",
            posts_fetched=len(normalized_posts),
            error_message=None,
            pool=pool,
            sync_start=sync_start,
        )

        logger.info(
            "social_etl platform success platform=%s connection_id=%s",
            platform,
            connection_id,
        )
        return {
            "platform": platform,
            "connection_id": connection_id,
            "posts_count": len(normalized_posts),
            "storage": "database",
            "kpis_computed": True,
        }
    except Exception as exc:
        logger.exception(
            "social_etl platform failed platform=%s connection_id=%s error=%s",
            platform,
            connection_id,
            exc,
        )
        await log_sync(
            connection_id=connection_id,
            status="failed",
            posts_fetched=0,
            error_message=str(exc),
            pool=pool,
            sync_start=sync_start,
        )
        raise


async def run_pipeline_async(
    cfg: dict[str, Any],
    *,
    output_base: Path | None = None,  # rétrocompatibilité signature
) -> tuple[Path, list[dict[str, Any]]]:
    """
    Exécute le pipeline à partir d'un dict (utilisable depuis l'API backend).

    ``cfg`` peut inclure ``idea_id`` (int). Les données sont chargées en DB.
    """
    cfg = _validate_config_dict(cfg)
    out_dir = Path("database://social_etl")

    accounts = cfg.get("accounts") or []
    logger.info(
        "social_etl pipeline start idea_id=%s accounts_total=%s",
        cfg.get("idea_id"),
        len(accounts),
    )
    results: list[dict[str, Any]] = []
    pool = await create_db_pool()
    try:
        for acc in accounts:
            if not isinstance(acc, dict):
                logger.warning("social_etl skip invalid account entry type=%s", type(acc).__name__)
                continue
            row = await _run_one(acc, pool)
            results.append(row)
    finally:
        await pool.close()
    logger.info(
        "social_etl pipeline done idea_id=%s accounts_done=%s",
        cfg.get("idea_id"),
        len(results),
    )
    return out_dir, results


async def run_pipeline_events(
    cfg: dict[str, Any],
    *,
    output_base: Path | None = None,  # rétrocompatibilité signature
) -> AsyncIterator[dict[str, Any]]:
    """
    Même exécution que ``run_pipeline_async`` mais émet un événement JSON par étape (SSE).

    Types d'événements : ``started``, ``platform_start``, ``platform_done``,
    ``platform_error``, ``complete``.
    """
    cfg = _validate_config_dict(cfg)
    out_dir = Path("database://social_etl")

    accounts_list = [a for a in (cfg.get("accounts") or []) if isinstance(a, dict)]
    yield {
        "type": "started",
        "idea_id": cfg.get("idea_id"),
        "output_dir": str(out_dir.resolve()),
        "platforms_total": len(accounts_list),
    }

    results: list[dict[str, Any]] = []
    failed_count = 0
    pool = await create_db_pool()
    try:
        for acc in accounts_list:
            platform = str(acc.get("platform") or "").strip().lower()
            yield {"type": "platform_start", "platform": platform}
            try:
                row = await _run_one(acc, pool)
                results.append(row)
                yield {"type": "platform_done", **row}
            except Exception as e:
                failed_count += 1
                yield {
                    "type": "platform_error",
                    "platform": platform,
                    "error": str(e),
                }
    finally:
        await pool.close()

    yield {
        "type": "complete",
        "output_dir": str(out_dir.resolve()),
        "runs": results,
        "platforms_total": len(accounts_list),
        "platforms_done": len(results),
        "platforms_failed": failed_count,
        "status": "success" if failed_count == 0 else ("failed" if len(results) == 0 else "partial"),
    }


async def run_pipeline(
    config_path: Path,
    *,
    output_dir: Path | None = None,
) -> tuple[Path, list[dict[str, Any]]]:
    cfg = _load_config(config_path)
    return await run_pipeline_async(cfg, output_base=output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline extract + normalize → DB")
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Chemin vers le JSON de configuration (liste accounts, option idea_id).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Option conservée pour rétrocompatibilité (non utilisée).",
    )
    args = parser.parse_args()
    config_path = args.config.resolve()
    if not config_path.is_file():
        raise SystemExit(f"Fichier introuvable: {config_path}")

    cfg = _load_config(config_path)
    out_dir, runs = asyncio.run(
        run_pipeline_async(cfg, output_base=args.output_dir.resolve() if args.output_dir else None)
    )
    print(json.dumps({"output_dir": str(out_dir), "runs": runs}, indent=2))


if __name__ == "__main__":
    main()
