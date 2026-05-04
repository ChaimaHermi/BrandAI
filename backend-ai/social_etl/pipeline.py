"""
Pipeline social : extraction (API) puis normalisation, sans calcul KPI.

Sorties dans ``social_etl/load/output/`` ou, si la config contient ``idea_id``,
dans ``load/output/idea_{idea_id}/`` pour isoler les analyses par idée.

Lancement (depuis ``backend-ai``)::

    python social_etl/pipeline.py --config social_etl/load/pipeline.example.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
NORM_DIR = BACKEND_ROOT / "social_etl" / "normalization"
LOAD_OUTPUT_DIR = Path(__file__).resolve().parent / "load" / "output"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(NORM_DIR) not in sys.path:
    sys.path.insert(0, str(NORM_DIR))

from normalize_common import dump_json  # noqa: E402
from normalize_facebook import build_normalized_facebook  # noqa: E402
from normalize_instagram import build_normalized_instagram  # noqa: E402
from normalize_linkedin import build_normalized_linkedin  # noqa: E402
from social_etl.extraction.facebook_extractor import extract_facebook  # noqa: E402
from social_etl.extraction.instagram_extractor import extract_instagram  # noqa: E402
from social_etl.extraction.linkedin_extractor import extract_linkedin  # noqa: E402


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


def _resolve_output_dir(cfg: dict[str, Any], output_base: Path | None) -> Path:
    base = (output_base or LOAD_OUTPUT_DIR).resolve()
    raw_idea = cfg.get("idea_id")
    if raw_idea is not None and str(raw_idea).strip() != "":
        try:
            return base / f"idea_{int(raw_idea)}"
        except (TypeError, ValueError):
            pass
    return base


async def _run_one(account: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    platform = str(account.get("platform") or "").strip().lower()
    token = str(account.get("access_token") or "").strip()
    account_id = str(account.get("account_id") or "").strip()
    limit = int(account.get("limit") or 10)

    if platform not in ("facebook", "instagram", "linkedin"):
        raise ValueError(f"Plateforme inconnue: {platform!r}")
    if not token or not account_id:
        raise ValueError(f"{platform}: access_token et account_id sont requis.")

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

    raw_path = out_dir / f"{platform}_raw.json"
    norm_path = out_dir / f"{platform}_normalized.json"
    dump_json(raw_path, raw)
    dump_json(norm_path, normalized)

    return {
        "platform": platform,
        "raw_path": str(raw_path.resolve()),
        "normalized_path": str(norm_path.resolve()),
        "posts_count": normalized.get("posts_count"),
    }


async def run_pipeline_async(
    cfg: dict[str, Any],
    *,
    output_base: Path | None = None,
) -> tuple[Path, list[dict[str, Any]]]:
    """
    Exécute le pipeline à partir d'un dict (utilisable depuis l'API backend).

    ``cfg`` peut inclure ``idea_id`` (int) pour écrire sous ``output/idea_{id}/``.
    """
    cfg = _validate_config_dict(cfg)
    out_dir = _resolve_output_dir(cfg, output_base)
    out_dir.mkdir(parents=True, exist_ok=True)

    accounts = cfg.get("accounts") or []
    results: list[dict[str, Any]] = []
    for acc in accounts:
        if not isinstance(acc, dict):
            continue
        row = await _run_one(acc, out_dir)
        results.append(row)
    return out_dir, results


async def run_pipeline_events(
    cfg: dict[str, Any],
    *,
    output_base: Path | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """
    Même exécution que ``run_pipeline_async`` mais émet un événement JSON par étape (SSE).

    Types d'événements : ``started``, ``platform_start``, ``platform_done``,
    ``platform_error``, ``complete``.
    """
    cfg = _validate_config_dict(cfg)
    out_dir = _resolve_output_dir(cfg, output_base)
    out_dir.mkdir(parents=True, exist_ok=True)

    accounts_list = [a for a in (cfg.get("accounts") or []) if isinstance(a, dict)]
    yield {
        "type": "started",
        "idea_id": cfg.get("idea_id"),
        "output_dir": str(out_dir.resolve()),
        "platforms_total": len(accounts_list),
    }

    results: list[dict[str, Any]] = []
    for acc in accounts_list:
        platform = str(acc.get("platform") or "").strip().lower()
        yield {"type": "platform_start", "platform": platform}
        try:
            row = await _run_one(acc, out_dir)
            results.append(row)
            yield {"type": "platform_done", **row}
        except Exception as e:
            yield {
                "type": "platform_error",
                "platform": platform,
                "error": str(e),
            }

    yield {
        "type": "complete",
        "output_dir": str(out_dir.resolve()),
        "runs": results,
    }


async def run_pipeline(
    config_path: Path,
    *,
    output_dir: Path | None = None,
) -> tuple[Path, list[dict[str, Any]]]:
    cfg = _load_config(config_path)
    return await run_pipeline_async(cfg, output_base=output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline extract + normalize → load/output/")
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
        help=f"Dossier racine de sortie (défaut: {LOAD_OUTPUT_DIR})",
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
