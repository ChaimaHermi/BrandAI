"""
Évaluation Competitor Agent seul (keyword extractor + Competitor) — LangSmith.

Usage (depuis backend-ai):
  python evaluation/competitor_eval.py --upload-only --replace
  python evaluation/competitor_eval.py --no-upload --prefix competitor-analysis-v2 --concurrency 1
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
from agents.market_analysis.subagents.competitor_agent import CompetitorAgent

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
build_competitor_judge_evaluators = _llm_mod.build_competitor_judge_evaluators

GOLDEN_PATH = _EVAL_DIR / "market_golden.jsonl"
DATASET_NAME = "brandai-competitor-eval"

REPORT_METRICS = (
    "competitor_format_compliance",
    "competitor_context_coherence",
    "competitor_faithfulness",
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


async def competitor_target(inputs: dict) -> dict:
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
            "competitor_queries": list(bundle.competitor_queries or []),
        }
        if not ps.market_analysis["competitor_queries"]:
            return {
                "status": "error",
                "error": "no competitor_queries from keyword extractor",
                "market_analysis": {},
                "collected_corpus": {},
            }

        result = await CompetitorAgent().run(ps)
        if result.get("status") != "success":
            return {
                "status": "error",
                "error": result.get("error", "competitor run failed"),
                "market_analysis": {"competitor": result.get("data") or {}},
                "collected_corpus": {},
            }

        ctx = result.get("collected_context") or ""
        return {
            "status": "success",
            "market_analysis": {"competitor": result.get("data") or {}},
            "collected_corpus": {"competitor": ctx} if ctx.strip() else {},
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "market_analysis": {},
            "collected_corpus": {},
        }


def _competitor_data(outputs: dict) -> dict:
    ma = outputs.get("market_analysis") or {}
    if isinstance(ma, dict):
        data = ma.get("competitor")
        if isinstance(data, dict):
            return data
    return {}


def eval_competitor_format_compliance(run, example) -> dict:
    out = run.outputs or {}
    if out.get("status") == "error":
        return {"key": "competitor_format_compliance", "score": 0.0, "comment": out.get("error", "error")}
    score, comment = block_format_compliance("competitor", _competitor_data(out))
    return {"key": "competitor_format_compliance", "score": score, "comment": comment}


def build_competitor_evaluators() -> list[Callable]:
    return [
        eval_competitor_format_compliance,
        *build_competitor_judge_evaluators(),
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
            description="Eval Competitor seul — 5 idées clarifiées (BrandAI)",
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
    parser = argparse.ArgumentParser(description="Évaluer Competitor Agent seul via LangSmith")
    parser.add_argument("--upload-only", action="store_true")
    parser.add_argument("--no-upload", action="store_true")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--prefix", default="competitor-analysis-v2")
    parser.add_argument("--concurrency", type=int, default=1)
    args = parser.parse_args()

    if not os.getenv("LANGCHAIN_API_KEY") and not os.getenv("LANGSMITH_API_KEY"):
        print("ERREUR: LANGCHAIN_API_KEY manquant")
        sys.exit(1)

    examples = load_golden()
    client = Client()
    print(f"[competitor-eval] {len(examples)} cas | metriques: {', '.join(REPORT_METRICS)}")

    if not args.no_upload:
        upload_dataset(client, examples, replace=args.replace)

    if args.upload_only:
        print("\nUpload termine.")
        return

    results = asyncio.run(
        aevaluate(
            competitor_target,
            data=DATASET_NAME,
            evaluators=build_competitor_evaluators(),
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


if __name__ == "__main__":
    main()
