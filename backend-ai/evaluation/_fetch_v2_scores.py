"""Lecture exacte des scores LangSmith — market-analysis-v2 (pas de relance eval)."""
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
import config.settings  # noqa: F401
from langsmith import Client

EXPERIMENT_PROJECT = "market-analysis-v2-d2575e5a"

AGENTS = [
    ("keywords", "Idea Keyword Extractor", False),
    ("market", "Market Sizing Agent", True),
    ("competitor", "Competitor Agent", True),
    ("voc", "VOC Agent", True),
    ("trends", "Trends & Risks Agent", True),
    ("strategy", "Analyse stratégique", True),
    ("planner", "Marketing Planner", False),
]


def _idea_id(run) -> str:
    inp = run.inputs or {}
    if isinstance(inp, dict):
        if inp.get("idea_id"):
            return str(inp["idea_id"])
        nested = inp.get("inputs")
        if isinstance(nested, dict) and nested.get("idea_id"):
            return str(nested["idea_id"])
    return "?"


def fetch_scores() -> list[dict]:
    client = Client()
    runs = list(
        client.list_runs(
            project_name=EXPERIMENT_PROJECT,
            filter="eq(is_root, true)",
            limit=10,
        )
    )
    rows = []
    for run in sorted(runs, key=_idea_id):
        fb = {f.key: f.score for f in client.list_feedback(run_ids=[str(run.id)], limit=50)}
        row: dict = {"idea_id": _idea_id(run), "run_id": str(run.id)}
        for prefix, _, has_faith in AGENTS:
            row[f"{prefix}_format_compliance"] = fb.get(f"{prefix}_format_compliance")
            row[f"{prefix}_context_coherence"] = fb.get(f"{prefix}_context_coherence")
            if has_faith:
                row[f"{prefix}_faithfulness"] = fb.get(f"{prefix}_faithfulness")
        rows.append(row)
    return rows


if __name__ == "__main__":
    print(json.dumps(fetch_scores(), indent=2, ensure_ascii=False))
