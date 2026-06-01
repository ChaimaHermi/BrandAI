"""
Recalcule les scores market en fusionnant deux expériences LangSmith.

Usage (depuis backend-ai):
  python evaluation/_recalc_market_scores.py \\
    --base market-analysis-v3-e97c36a4 \\
    --retry market-analysis-v4-mkt04-XXXX \\
    --replace-idea mkt-04
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import importlib.util

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
import config.settings  # noqa: F401

from langsmith import Client

_SCHEMAS_PATH = Path(__file__).parent / "analyse-de-marche" / "market_schemas.py"
_spec = importlib.util.spec_from_file_location("market_schemas", _SCHEMAS_PATH)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)
REPORT_METRICS = _mod.all_report_metrics()

AGENTS = ["keywords", "market", "competitor", "voc", "trends", "strategy", "planner"]


def _idea_id(run) -> str:
    inp = run.inputs or {}
    if isinstance(inp, dict):
        if inp.get("idea_id"):
            return str(inp["idea_id"])
        nested = inp.get("inputs")
        if isinstance(nested, dict) and nested.get("idea_id"):
            return str(nested["idea_id"])
    return "?"


def fetch_project_scores(client: Client, project_name: str) -> dict[str, dict]:
    runs = list(
        client.list_runs(
            project_name=project_name,
            filter="eq(is_root, true)",
            limit=20,
        )
    )
    out: dict[str, dict] = {}
    for run in runs:
        iid = _idea_id(run)
        fb = {f.key: f.score for f in client.list_feedback(run_ids=[str(run.id)], limit=60)}
        row = {"run_id": str(run.id), "status": (run.outputs or {}).get("status")}
        for key in REPORT_METRICS:
            row[key] = fb.get(key)
        out[iid] = row
    return out


def merge_scores(
    base: dict[str, dict],
    retry: dict[str, dict],
    replace_idea: str,
) -> dict[str, dict]:
    merged = dict(base)
    if replace_idea in retry:
        merged[replace_idea] = retry[replace_idea]
    return merged


def merge_block_scores(
    base: dict[str, dict],
    retry: dict[str, dict],
    block_prefix: str,
) -> dict[str, dict]:
    """Remplace les métriques d'un agent (ex. competitor_*) depuis retry dans base."""
    merged = {iid: dict(row) for iid, row in base.items()}
    prefix = f"{block_prefix}_"
    for iid, retry_row in retry.items():
        if iid not in merged:
            merged[iid] = dict(retry_row)
        for key in REPORT_METRICS:
            if key.startswith(prefix) and retry_row.get(key) is not None:
                merged[iid][key] = retry_row[key]
    return merged


def print_table(merged: dict[str, dict]) -> None:
    ids = sorted(merged.keys())
    print(f"\n=== Scores fusionnes ({len(ids)} cas) ===")
    for iid in ids:
        row = merged[iid]
        status = row.get("status", "?")
        err = " OK" if status == "success" else f" ERR({status})"
        print(f"\n  [{iid}]{err}")
        for prefix in AGENTS:
            keys = [k for k in REPORT_METRICS if k.startswith(f"{prefix}_")]
            if not keys:
                continue
            parts = []
            for k in keys:
                v = row.get(k)
                if v is not None:
                    parts.append(f"{k.split('_', 1)[1][:4]}={v}")
            if parts:
                print(f"    {prefix}: " + " | ".join(parts))

    print("\n=== Moyennes ===")
    for key in REPORT_METRICS:
        vals = [merged[iid][key] for iid in ids if merged[iid].get(key) is not None]
        if vals:
            avg = sum(float(v) for v in vals) / len(vals)
            print(f"  {key}: {avg * 100:.1f}%  ({vals})")
        else:
            print(f"  {key}: N/A")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fusionner scores market LangSmith")
    parser.add_argument("--base", required=True, help="Projet base (ex. market-analysis-v3-e97c36a4)")
    parser.add_argument("--retry", required=True, help="Projet retry (ex. market-analysis-v4-mkt04-...)")
    parser.add_argument("--replace-idea", default="mkt-04")
    parser.add_argument(
        "--merge-block",
        default=None,
        help="Fusionner métriques d'un agent (ex. competitor) depuis --retry pour tous les cas",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    client = Client()
    base = fetch_project_scores(client, args.base)
    retry = fetch_project_scores(client, args.retry)
    if args.merge_block:
        merged = merge_block_scores(base, retry, args.merge_block)
        mode = f"merge-block={args.merge_block}"
    else:
        merged = merge_scores(base, retry, args.replace_idea)
        mode = f"replace-idea={args.replace_idea}"

    if args.json:
        print(json.dumps(merged, indent=2, ensure_ascii=False))
    else:
        print(f"Base  : {args.base} ({len(base)} runs)")
        print(f"Retry : {args.retry} ({len(retry)} runs)")
        print(f"Mode  : {mode}")
        print_table(merged)


if __name__ == "__main__":
    main()
