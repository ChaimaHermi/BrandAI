"""
Évaluation Idea Clarifier — résultats dans LangSmith (projet brand-ai-eval).

Usage (depuis backend-ai):
  python evaluation/clarifier_eval.py
  python evaluation/clarifier_eval.py --upload-only
  python evaluation/clarifier_eval.py --prefix clarifier-v2 --no-upload
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config.settings  # noqa: F401 — charge LANGCHAIN_API_KEY depuis Brand AI/.env

# Après settings.py (qui force brand-ai) : projet dédié évaluation
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_EVAL_PROJECT", "brand-ai-eval")
os.environ["LANGCHAIN_TRACING_V2"] = "true"

from langsmith import Client
from langsmith.evaluation import aevaluate

from agents.base_agent import PipelineState
from agents.clarifier.idea_clarifier_agent import IdeaClarifierAgent

_LLM_JUDGE_PATH = Path(__file__).parent / "clarification-de-lidee" / "llm_judge_evaluators.py"
_llm_spec = importlib.util.spec_from_file_location("llm_judge_evaluators", _LLM_JUDGE_PATH)
_llm_mod = importlib.util.module_from_spec(_llm_spec)
assert _llm_spec.loader is not None
_llm_spec.loader.exec_module(_llm_mod)
eval_questions_relevance = _llm_mod.eval_questions_relevance
eval_brief_coherence = _llm_mod.eval_brief_coherence

GOLDEN_PATH = (
    Path(__file__).parent / "clarification-de-lidee" / "clarifier_golden.jsonl"
)
DATASET_NAME = "brandai-clarifier-clarification-idee"


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


async def clarifier_target(inputs: dict) -> dict:
    """Fonction cible LangSmith — reproduit run_start / run_answer."""
    state = PipelineState(
        idea_id=inputs.get("idea_id", "eval"),
        name=inputs.get("name") or "",
        sector=inputs.get("sector") or "",
        description=inputs["description"],
        target_audience=inputs.get("target_audience") or "",
    )
    agent = IdeaClarifierAgent()
    answers = inputs.get("answers")
    if inputs.get("phase") == "answer" and answers:
        return await agent.run_answer(state, answers)
    return await agent.run_start(state)


def eval_status_correctness(run, example) -> dict:
    expected = (example.outputs or {}).get("expected_type")
    got = (run.outputs or {}).get("type")
    if not expected:
        return {"key": "status_correctness", "score": None, "comment": "no expected_type"}
    match = got == expected
    return {
        "key": "status_correctness",
        "score": 1.0 if match else 0.0,
        "comment": f"expected={expected} got={got}",
    }


def eval_brief_completeness(run, example) -> dict:
    out = run.outputs or {}
    if out.get("type") != "clarified":
        return {"key": "brief_completeness", "score": None, "comment": "N/A"}
    required = [
        "short_pitch",
        "problem",
        "target_users",
        "solution_description",
        "sector",
        "score",
    ]
    missing = [k for k in required if not str(out.get(k) or "").strip()]
    ok = not missing
    return {
        "key": "brief_completeness",
        "score": 1.0 if ok else 0.0,
        "comment": "ok" if ok else f"missing: {missing}",
    }


def eval_format_compliance(run, example) -> dict:
    got = (run.outputs or {}).get("type")
    ok = got in ("refused", "questions", "clarified")
    return {
        "key": "format_compliance",
        "score": 1.0 if ok else 0.0,
        "comment": str(got),
    }


REPORT_METRICS = (
    "status_correctness",
    "format_compliance",
    "brief_completeness",
    "questions_relevance",
    "brief_coherence",
)


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
    """Agrège uniquement les 5 métriques officielles (ignore 'score' UI LangSmith)."""
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
        for fb in client.list_feedback(run_ids=run_ids, limit=500):
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

    print("\n=== Resume experience ===")
    print(f"Experience : {results.experiment_name}")
    print(f"Runs       : {total}")
    print(f"Taux erreur: {error_rate:.1f}% ({errors}/{total} runs en echec)")
    for metric in REPORT_METRICS:
        avg = avgs.get(metric)
        if avg is None:
            print(f"  {metric}: N/A (absent de l'experience)")
        else:
            print(f"  {metric}: {avg * 100:.1f}%")
    if compare_url:
        print(f"Lien       : {compare_url}")

    missing = [m for m in REPORT_METRICS if avgs.get(m) is None]
    if missing:
        print(f"\n[AVERTISSEMENT] Metriques sans score : {', '.join(missing)}")

    if stray:
        print(
            "\n[AVERTISSEMENT] Feedback LangSmith ignore (hors les 5 metriques) : "
            + ", ".join(sorted(stray))
        )
        print(
            "  -> Supprimez les evaluators UI sur le dataset qui publient 'score' "
            "(doublon / All Failed). Gardez uniquement clarifier_eval.py."
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
            description="Golden set — epic clarification intelligente de l'idée (BrandAI)",
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
    parser = argparse.ArgumentParser(description="Évaluer Idea Clarifier via LangSmith")
    parser.add_argument("--upload-only", action="store_true", help="Upload dataset sans lancer l'expérience")
    parser.add_argument("--no-upload", action="store_true", help="Lancer l'expérience sans re-upload")
    parser.add_argument("--replace", action="store_true", help="Supprimer les anciens exemples du dataset avant upload")
    parser.add_argument("--prefix", default="clarifier-v1", help="Préfixe nom d'expérience LangSmith")
    parser.add_argument("--concurrency", type=int, default=2)
    args = parser.parse_args()

    api_key = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
    if not api_key:
        print("ERREUR: LANGCHAIN_API_KEY (ou LANGSMITH_API_KEY) manquant dans Brand AI/.env")
        sys.exit(1)

    project = os.environ.get("LANGCHAIN_PROJECT", "brand-ai-eval")
    print(f"[eval] LangSmith projet: {project}")
    print(f"[eval] Golden: {GOLDEN_PATH}")

    examples = load_golden()
    client = Client()

    if not args.no_upload:
        upload_dataset(client, examples, replace=args.replace)

    if args.upload_only:
        print("\nUpload termine.")
        print("LangSmith - Projet:", project)
        print("  - Datasets -", DATASET_NAME)
        print("  - Puis: python evaluation/clarifier_eval.py --no-upload")
        return

    print(
        "[eval] Metriques (5): "
        + ", ".join(REPORT_METRICS)
    )
    print(f"\n[eval] Lancement expérience '{args.prefix}' sur {len(examples)} cas...")
    results = asyncio.run(
        aevaluate(
            clarifier_target,
            data=DATASET_NAME,
            evaluators=[
                eval_format_compliance,
                eval_status_correctness,
                eval_brief_completeness,
                eval_questions_relevance,
                eval_brief_coherence,
            ],
            experiment_prefix=args.prefix,
            max_concurrency=max(1, args.concurrency),
        )
    )

    _print_experiment_summary(results, client)
    print("\n=== Termine ===")
    print("Voir les resultats dans LangSmith:")
    print("  1. https://smith.langchain.com")
    print(f"  2. Projet (en haut a gauche): {project}")
    print(f"  3. Datasets - {DATASET_NAME} - onglet Experiments")
    print(f"  4. Ouvrir l'experience la plus recente (prefixe {args.prefix})")
    print(
        "  5. Colonnes attendues: status_correctness, format_compliance, "
        "brief_completeness, questions_relevance, brief_coherence"
    )
    print("  6. Clic sur une ligne - Output + lien Trace (clarifier.run_start / llm_call)")


if __name__ == "__main__":
    main()
