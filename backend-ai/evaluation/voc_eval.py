"""
Évaluation VOC Agent seul (keyword extractor + VOC) — LangSmith brand-ai-eval.

Usage (depuis backend-ai):
  python evaluation/voc_eval.py --upload-only --replace
  python evaluation/voc_eval.py --no-upload --prefix voc-analysis-v1 --concurrency 1
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

from agents.base_agent import PipelineState
from agents.market_analysis.orchestrator.keyword_extractor import KeywordExtractor
from agents.market_analysis.subagents.voc_agent import VOCAgent

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
build_voc_judge_evaluators = _llm_mod.build_voc_judge_evaluators

GOLDEN_PATH = _EVAL_DIR / "market_golden.jsonl"
DATASET_NAME = "brandai-voc-eval"

REPORT_METRICS = (
    "voc_format_compliance",
    "voc_context_coherence",
    "voc_faithfulness",
)


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


async def voc_target(inputs: dict) -> dict:
    """Keyword extractor + VOC uniquement (pas le graph market complet)."""
    idea_id = inputs.get("idea_id", "eval")
    clarified_idea = inputs.get("clarified_idea") or {}
    if not clarified_idea:
        return {
            "status": "error",
            "error": "clarified_idea manquant",
            "market_analysis": {},
            "collected_corpus": {},
        }

    ps = PipelineState(idea_id=idea_id)
    ps.clarified_idea = clarified_idea

    try:
        bundle = await KeywordExtractor().extract(clarified_idea)
        ps.market_analysis = {
            "voc_queries": list(bundle.voc_keywords or []),
        }
        if not ps.market_analysis["voc_queries"]:
            return {
                "status": "error",
                "error": "no voc_queries from keyword extractor",
                "market_analysis": {},
                "collected_corpus": {},
            }

        result = await VOCAgent().run(ps)
        if result.get("status") != "success":
            return {
                "status": "error",
                "error": result.get("error", "voc run failed"),
                "market_analysis": {"voc": result.get("data") or {}},
                "collected_corpus": {},
            }

        ctx = result.get("collected_context") or ""
        return {
            "status": "success",
            "market_analysis": {"voc": result.get("data") or {}},
            "collected_corpus": {"voc": ctx} if ctx.strip() else {},
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "market_analysis": {},
            "collected_corpus": {},
        }


def _voc_data(outputs: dict) -> dict:
    ma = outputs.get("market_analysis") or {}
    if isinstance(ma, dict):
        data = ma.get("voc")
        if isinstance(data, dict):
            return data
    return {}


def eval_voc_format_compliance(run, example) -> dict:
    out = run.outputs or {}
    if out.get("status") == "error":
        return {"key": "voc_format_compliance", "score": 0.0, "comment": out.get("error", "error")}
    score, comment = block_format_compliance("voc", _voc_data(out))
    return {"key": "voc_format_compliance", "score": score, "comment": comment}


def build_voc_evaluators() -> list[Callable]:
    return [
        eval_voc_format_compliance,
        *build_voc_judge_evaluators(),
    ]


def upload_dataset(client: Client, examples: list[dict], *, replace: bool) -> str:
    try:
        ds = client.read_dataset(dataset_name=DATASET_NAME)
        if replace:
            for ex in client.list_examples(dataset_id=ds.id):
                client.delete_example(example_id=ex.id)
    except Exception:
        ds = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="Eval VOC seul — 5 idées clarifiées (BrandAI)",
        )
    for ex in examples:
        client.create_example(
            inputs=ex["inputs"],
            outputs=ex.get("outputs") or {},
            dataset_id=ds.id,
        )
    print(f"  -> {len(examples)} exemple(s) dans '{DATASET_NAME}'.")
    return str(ds.id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Évaluer VOC Agent seul via LangSmith")
    parser.add_argument("--upload-only", action="store_true")
    parser.add_argument("--no-upload", action="store_true")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--prefix", default="voc-analysis-v1")
    parser.add_argument("--concurrency", type=int, default=1)
    args = parser.parse_args()

    if not os.getenv("LANGCHAIN_API_KEY") and not os.getenv("LANGSMITH_API_KEY"):
        print("ERREUR: LANGCHAIN_API_KEY manquant")
        sys.exit(1)

    examples = load_golden()
    client = Client()
    print(f"[voc-eval] {len(examples)} cas | metriques: {', '.join(REPORT_METRICS)}")

    if not args.no_upload:
        upload_dataset(client, examples, replace=args.replace)

    if args.upload_only:
        print("\nUpload termine.")
        print("LangSmith: https://smith.langchain.com")
        print(f"  Projet : {os.environ.get('LANGCHAIN_PROJECT', 'brand-ai-eval')}")
        print(f"  Dataset: {DATASET_NAME} -> onglet Experiments")
        print("Puis lancer : python evaluation/voc_eval.py --no-upload --prefix voc-analysis-v1 --concurrency 1")
        return

    results = asyncio.run(
        aevaluate(
            voc_target,
            data=DATASET_NAME,
            evaluators=build_voc_evaluators(),
            experiment_prefix=args.prefix,
            max_concurrency=max(1, args.concurrency),
        )
    )

    totals = {k: [] for k in REPORT_METRICS}
    for row in results._results:
        eval_results = row.get("evaluation_results") or {}
        for res in eval_results.get("results") or []:
            key = getattr(res, "key", None)
            score = getattr(res, "score", None)
            if key in totals and score is not None:
                totals[key].append(float(score))

    print(f"\n=== {results.experiment_name} ===")
    for m in REPORT_METRICS:
        vals = totals[m]
        if vals:
            print(f"  {m}: {sum(vals)/len(vals)*100:.1f}% ({vals})")
        else:
            print(f"  {m}: N/A")

    compare_url = getattr(results, "experiment_url", None) or ""
    print("\n=== LangSmith ===")
    print("https://smith.langchain.com")
    print(f"  Projet  : {os.environ.get('LANGCHAIN_PROJECT', 'brand-ai-eval')}")
    print(f"  Dataset : {DATASET_NAME} -> Experiments -> {results.experiment_name}")
    if compare_url:
        print(f"  Lien    : {compare_url}")


if __name__ == "__main__":
    main()
