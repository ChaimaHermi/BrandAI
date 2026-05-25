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
from langsmith.evaluation import evaluate

from agents.base_agent import PipelineState
from agents.clarifier.idea_clarifier_agent import IdeaClarifierAgent

GOLDEN_PATH = Path(__file__).parent / "clarifier_golden.jsonl"
DATASET_NAME = "brandai-clarifier-golden"


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


def eval_type_match(run, example) -> dict:
    expected = (example.outputs or {}).get("expected_type")
    got = (run.outputs or {}).get("type")
    if not expected:
        return {"key": "type_match", "score": None, "comment": "no expected_type"}
    match = got == expected
    return {
        "key": "type_match",
        "score": 1.0 if match else 0.0,
        "comment": f"expected={expected} got={got}",
    }


def eval_clarified_complete(run, example) -> dict:
    out = run.outputs or {}
    if out.get("type") != "clarified":
        return {"key": "clarified_complete", "score": None, "comment": "N/A"}
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
        "key": "clarified_complete",
        "score": 1.0 if ok else 0.0,
        "comment": "ok" if ok else f"missing: {missing}",
    }


def eval_json_type_valid(run, example) -> dict:
    got = (run.outputs or {}).get("type")
    ok = got in ("refused", "questions", "clarified")
    return {
        "key": "json_type_valid",
        "score": 1.0 if ok else 0.0,
        "comment": str(got),
    }


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
            description="Golden set Idea Clarifier — BrandAI PFE",
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

    print(f"\n[eval] Lancement expérience '{args.prefix}' sur {len(examples)} cas (dataset existant)...")
    results = evaluate(
        clarifier_target,
        data=DATASET_NAME,
        evaluators=[eval_json_type_valid, eval_type_match, eval_clarified_complete],
        experiment_prefix=args.prefix,
        max_concurrency=max(1, args.concurrency),
    )

    print("\n=== Termine ===")
    print("Voir les resultats dans LangSmith:")
    print("  1. https://smith.langchain.com")
    print(f"  2. Projet (en haut a gauche): {project}")
    print(f"  3. Datasets - {DATASET_NAME} - onglet Experiments")
    print(f"  4. Ouvrir l'experience la plus recente (prefixe {args.prefix})")
    print("  5. Colonnes: type_match, clarified_complete, json_type_valid")
    print("  6. Clic sur une ligne - Output + lien Trace (clarifier.run_start / llm_call)")
    print(results)


if __name__ == "__main__":
    main()
