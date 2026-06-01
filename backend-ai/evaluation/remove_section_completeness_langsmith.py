"""
Supprime les feedback *_section_completeness d'une expérience LangSmith existante.

Usage (depuis backend-ai):
  python evaluation/remove_section_completeness_langsmith.py --experiment resultat-final-complet-fef19ca9
  python evaluation/remove_section_completeness_langsmith.py --experiment resultat-final-complet-fef19ca9 --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

import config.settings  # noqa: F401

from langsmith import Client

SECTION_SUFFIX = "section_completeness"
SECTION_PREFIXES = (
    "keywords",
    "market",
    "competitor",
    "voc",
    "trends",
    "strategy",
    "planner",
)
SECTION_KEYS = {f"{p}_{SECTION_SUFFIX}" for p in SECTION_PREFIXES}


def remove_section_feedback(client: Client, experiment: str, *, dry_run: bool) -> int:
    runs = list(
        client.list_runs(
            project_name=experiment,
            filter="eq(is_root, true)",
            limit=20,
        )
    )
    deleted = 0
    for run in runs:
        for fb in client.list_feedback(run_ids=[str(run.id)], limit=100):
            if fb.key not in SECTION_KEYS:
                continue
            if dry_run:
                print(f"  [dry-run] would delete {fb.key} on run {run.id}")
            elif fb.id:
                client.delete_feedback(fb.id)
                print(f"  deleted {fb.key} on run {run.id}")
            deleted += 1
    return deleted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Supprime les feedback section_completeness d'une expérience LangSmith",
    )
    parser.add_argument(
        "--experiment",
        default="resultat-final-complet-fef19ca9",
        help="Nom du projet/expérience LangSmith",
    )
    parser.add_argument("--dry-run", action="store_true", help="Liste sans supprimer")
    args = parser.parse_args()

    client = Client()
    print(f"[remove-section] experiment={args.experiment} dry_run={args.dry_run}")
    n = remove_section_feedback(client, args.experiment, dry_run=args.dry_run)
    print(f"\n{'Would delete' if args.dry_run else 'Deleted'} {n} feedback(s).")
    if not args.dry_run and n:
        print("Rafraîchir l'expérience dans LangSmith — colonnes section_completeness retirées.")


if __name__ == "__main__":
    main()
