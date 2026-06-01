"""
Évaluation analyse de marché (graph complet) — métriques PAR AGENT dans LangSmith.

Usage (depuis backend-ai) — NE PAS lancer avant validation du golden set :
  python evaluation/market_eval.py --upload-only
  python evaluation/market_eval.py --no-upload --prefix market-analysis-v1 --concurrency 1

Prompts LLM-as-Judge : evaluation/analyse-de-marche/llm_judge_evaluators.py
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Callable

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import config.settings  # noqa: F401

os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_EVAL_PROJECT", "brand-ai-eval")
os.environ["LANGCHAIN_TRACING_V2"] = "true"

from langsmith import Client
from langsmith.evaluation import aevaluate

from pipeline.market_graph import build_market_graph

_EVAL_DIR = Path(__file__).parent / "analyse-de-marche"
_SCHEMAS_PATH = _EVAL_DIR / "market_schemas.py"
_LLM_JUDGE_PATH = _EVAL_DIR / "llm_judge_evaluators.py"

_schemas_spec = importlib.util.spec_from_file_location("market_schemas", _SCHEMAS_PATH)
_schemas_mod = importlib.util.module_from_spec(_schemas_spec)
assert _schemas_spec.loader is not None
_schemas_spec.loader.exec_module(_schemas_mod)

_llm_spec = importlib.util.spec_from_file_location("market_llm_judge", _LLM_JUDGE_PATH)
_llm_mod = importlib.util.module_from_spec(_llm_spec)
assert _llm_spec.loader is not None
_llm_spec.loader.exec_module(_llm_mod)

block_format_compliance = _schemas_mod.block_format_compliance
all_report_metrics = _schemas_mod.all_report_metrics
EVAL_BLOCKS = _schemas_mod.EVAL_BLOCKS
build_judge_evaluators = _llm_mod.build_judge_evaluators

GOLDEN_PATH = _EVAL_DIR / "market_golden.jsonl"
DATASET_NAME = "brandai-market-analyse-de-marche"

REPORT_METRICS = all_report_metrics()

_market_graph = None


def _get_market_graph():
    global _market_graph
    if _market_graph is None:
        _market_graph = build_market_graph()
    return _market_graph


def load_golden() -> list[dict]:
    if not GOLDEN_PATH.is_file():
        raise FileNotFoundError(f"Golden set introuvable: {GOLDEN_PATH}")
    rows: list[dict] = []
    with GOLDEN_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


async def market_target(inputs: dict) -> dict:
    """Exécute le graph market complet (1 idée = 1 run LangSmith)."""
    idea_id = inputs.get("idea_id", "eval")
    clarified_idea = inputs.get("clarified_idea") or {}
    if not clarified_idea:
        return {
            "status": "error",
            "error": "clarified_idea manquant",
            "market_analysis": {},
            "collected_corpus": {},
            "marketing_plan": None,
        }

    graph = _get_market_graph()
    initial = {
        "idea_id": idea_id,
        "clarified_idea": clarified_idea,
        "market_analysis": {},
        "collected_corpus": {},
    }
    try:
        final = await graph.ainvoke(initial)
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "market_analysis": {},
            "collected_corpus": {},
            "marketing_plan": None,
        }

    ma = (final or {}).get("market_analysis") or {}
    corpus = (final or {}).get("collected_corpus") or {}
    return {
        "status": "success",
        "market_analysis": ma,
        "collected_corpus": corpus if isinstance(corpus, dict) else {},
        "marketing_plan": None,
    }


def _get_block_data(outputs: dict, block: str) -> dict:
    if block == "planner":
        plan = outputs.get("marketing_plan")
        return plan if isinstance(plan, dict) else {}
    ma = outputs.get("market_analysis") or {}
    if not isinstance(ma, dict):
        return {}
    data = ma.get(block)
    return data if isinstance(data, dict) else {}


def _make_format_eval(block: str) -> Callable:
    key = f"{block}_format_compliance"

    def _eval(run, example) -> dict:
        out = run.outputs or {}
        if out.get("status") == "error" and block != "planner":
            return {"key": key, "score": 0.0, "comment": out.get("error", "pipeline error")}
        if block == "planner":
            return {
                "key": key,
                "score": None,
                "comment": "N/A — Marketing Planner hors scope market_eval",
            }
        data = _get_block_data(out, block)
        score, comment = block_format_compliance(block, data)
        return {"key": key, "score": score, "comment": comment}

    _eval.__name__ = key
    return _eval


def build_all_evaluators() -> list[Callable]:
    evaluators: list[Callable] = []
    evaluators.append(_make_format_eval("keywords"))
    for block in EVAL_BLOCKS:
        evaluators.append(_make_format_eval(block))
    evaluators.append(_make_format_eval("planner"))
    evaluators.extend(build_judge_evaluators())
    return evaluators


def _feedback_score_value(feedback) -> float | None:
    if feedback.score is not None:
        try:
            return float(feedback.score)
        except (TypeError, ValueError):
            pass
    if feedback.value is not None:
        try:
            return float(feedback.value)
        except (TypeError, ValueError):
            pass
    return None


def _collect_metric_scores(results, client: Client) -> dict[str, list[float]]:
    totals: dict[str, list[float]] = {k: [] for k in REPORT_METRICS}
    allowed = set(REPORT_METRICS)
    run_ids: list[str] = []
    stray_keys: set[str] = set()

    for row in results._results:
        run = row.get("run")
        if run and getattr(run, "id", None):
            run_ids.append(str(run.id))
        eval_results = row.get("evaluation_results") or {}
        for res in eval_results.get("results") or []:
            key = getattr(res, "key", None) or (res.get("key") if isinstance(res, dict) else None)
            score = getattr(res, "score", None) if not isinstance(res, dict) else res.get("score")
            if not key:
                continue
            if key not in allowed:
                stray_keys.add(key)
                continue
            if score is not None:
                totals[key].append(float(score))

    if run_ids:
        for fb in client.list_feedback(run_ids=run_ids, limit=2000):
            if fb.key not in allowed:
                if fb.key == "score":
                    stray_keys.add("score")
                continue
            val = _feedback_score_value(fb)
            if val is not None:
                totals[fb.key].append(val)

    totals["_stray_feedback_keys"] = list(stray_keys)  # type: ignore[assignment]
    return totals


def _error_stats(results) -> tuple[int, int]:
    total = len(results._results)
    errors = 0
    for row in results._results:
        run = row.get("run")
        if run and getattr(run, "error", None):
            errors += 1
        else:
            out = getattr(run, "outputs", None) or {}
            if isinstance(out, dict) and out.get("status") == "error":
                errors += 1
    return errors, total


def _experiment_compare_url(results) -> str | None:
    manager = getattr(results, "_manager", None)
    experiment = getattr(manager, "_experiment", None) if manager else None
    if not experiment:
        return None
    dataset_id = getattr(experiment, "reference_dataset_id", None) or getattr(
        manager, "reference_dataset_id", None
    )
    session_id = getattr(experiment, "id", None)
    url = getattr(experiment, "url", None)
    if not url or not dataset_id or not session_id:
        return None
    base_url = url.split("/projects/p/")[0]
    return f"{base_url}/datasets/{dataset_id}/compare?selectedSessions={session_id}"


def _print_experiment_summary(results, client: Client) -> None:
    totals = _collect_metric_scores(results, client)
    stray = totals.pop("_stray_feedback_keys", [])
    avgs = {
        k: (sum(v) / len(v) if v else None)
        for k, v in totals.items()
        if k in REPORT_METRICS
    }
    errors, total = _error_stats(results)
    error_rate = (errors / total * 100) if total else 0.0
    compare_url = _experiment_compare_url(results)

    print("\n=== Resume experience (analyse de marche — metriques par agent) ===")
    print(f"Experience : {results.experiment_name}")
    print(f"Runs       : {total}")
    print(f"Taux erreur: {error_rate:.1f}% ({errors}/{total} runs en echec)")
    if compare_url:
        print(f"Lien       : {compare_url}")

    groups = [
        ("Idea Keyword Extractor", "keywords"),
        ("Market Sizing Agent", "market"),
        ("Competitor Agent", "competitor"),
        ("VOC Agent", "voc"),
        ("Trends & Risks Agent", "trends"),
        ("Analyse strategique", "strategy"),
        ("Marketing Planner", "planner"),
    ]
    for label, prefix in groups:
        print(f"\n  [{label}]")
        for suffix in (
            "format_compliance",
            "context_coherence",
            "faithfulness",
        ):
            key = f"{prefix}_{suffix}"
            if key not in REPORT_METRICS:
                continue
            avg = avgs.get(key)
            if avg is None:
                print(f"    {key}: N/A")
            else:
                print(f"    {key}: {avg * 100:.1f}%")

    if stray:
        print(
            "\n[AVERTISSEMENT] Feedback ignore (evaluators UI sur le dataset) : "
            + ", ".join(sorted(stray))
        )


def upload_dataset(client: Client, examples: list[dict], *, replace: bool) -> str:
    try:
        ds = client.read_dataset(dataset_name=DATASET_NAME)
        if replace:
            for ex in client.list_examples(dataset_id=ds.id):
                client.delete_example(example_id=ex.id)
            print(f"Dataset '{DATASET_NAME}' vide ({ds.id}).")
    except Exception:
        ds = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Golden set pilote — epic analyse de marché BrandAI (5 idées clarifiées)",
        )
        print(f"Dataset '{DATASET_NAME}' cree ({ds.id}).")

    for ex in examples:
        client.create_example(
            inputs=ex["inputs"],
            outputs=ex.get("outputs") or {},
            dataset_id=ds.id,
        )
    print(f"  -> {len(examples)} exemple(s) charges.")
    return str(ds.id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Évaluer le graph analyse de marché via LangSmith")
    parser.add_argument("--upload-only", action="store_true")
    parser.add_argument("--no-upload", action="store_true")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--prefix", default="market-analysis-v1")
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument(
        "--idea-id",
        default=None,
        help="Relancer un seul cas (ex. mkt-04). Filtre le golden set.",
    )
    args = parser.parse_args()

    api_key = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        print("ERREUR: LANGCHAIN_API_KEY (ou LANGSMITH_API_KEY) manquant dans Brand AI/.env")
        sys.exit(1)

    project = os.environ.get("LANGCHAIN_PROJECT", "brand-ai-eval")
    examples = load_golden()
    if args.idea_id:
        examples = [ex for ex in examples if ex.get("inputs", {}).get("idea_id") == args.idea_id]
        if not examples:
            print(f"ERREUR: idea_id '{args.idea_id}' introuvable dans {GOLDEN_PATH}")
            sys.exit(1)
        print(f"[eval] Filtre idea_id={args.idea_id} -> 1 cas")
    evaluators = build_all_evaluators()

    print(f"[eval] LangSmith projet: {project}")
    print(f"[eval] Golden: {GOLDEN_PATH} ({len(examples)} cas)")
    print(f"[eval] {len(REPORT_METRICS)} metriques par agent")
    print(f"[eval] Judges LLM: {_LLM_JUDGE_PATH}")

    if args.idea_id and not args.no_upload and not args.upload_only:
        print("[eval] --idea-id actif -> pas de re-upload dataset (utilise --no-upload)")
        args.no_upload = True

    client = Client()

    if not args.no_upload:
        upload_dataset(client, examples, replace=args.replace)

    if args.upload_only:
        print("\nUpload termine.")
        print("Validez le golden set, puis lancez :")
        print(
            "  python evaluation/market_eval.py --no-upload --prefix market-analysis-v1 --concurrency 1"
        )
        return

    print(f"\n[eval] Lancement '{args.prefix}' — {len(evaluators)} evaluators, {len(examples)} cas...")
    if args.idea_id:
        retry_ds = f"brandai-market-retry-{args.idea_id}"
        try:
            ds = client.read_dataset(dataset_name=retry_ds)
            for ex in client.list_examples(dataset_id=ds.id):
                client.delete_example(example_id=ex.id)
        except Exception:
            ds = client.create_dataset(
                dataset_name=retry_ds,
                description=f"Retry eval market — {args.idea_id}",
            )
        for ex in examples:
            client.create_example(
                inputs=ex["inputs"],
                outputs=ex.get("outputs") or {},
                dataset_id=ds.id,
            )
        eval_data = retry_ds
        print(f"[eval] Dataset retry: {retry_ds}")
    else:
        eval_data = DATASET_NAME
    results = asyncio.run(
        aevaluate(
            market_target,
            data=eval_data,
            evaluators=evaluators,
            experiment_prefix=args.prefix,
            max_concurrency=max(1, args.concurrency),
        )
    )

    _print_experiment_summary(results, client)
    print("\n=== Termine ===")
    print("LangSmith: https://smith.langchain.com")
    print(f"  Projet: {project}")
    print(f"  Dataset: {DATASET_NAME}")


if __name__ == "__main__":
    main()
