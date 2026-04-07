import json
import re
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from agents.base_agent import PipelineState
from agents.market_analysis.orchestrator.keyword_extractor import KeywordExtractor
from agents.market_analysis.subagents.competitor_agent import CompetitorAgent
from agents.market_analysis.subagents.market_sizing_agent import MarketSizingAgent
from agents.market_analysis.subagents.strategy_analysis_agent import StrategyAnalysisAgent
from agents.market_analysis.subagents.trends_risks_agent import TrendsRisksAgent
from agents.market_analysis.subagents.voc_agent import VOCAgent


_WORKFLOWS_DIR = Path(__file__).resolve().parent.parent / "workflows"


class MarketGraphState(TypedDict, total=False):
    idea_id: Any
    clarified_idea: dict
    market_analysis: dict


def _to_pipeline(state: MarketGraphState) -> PipelineState:
    ps = PipelineState(idea_id=state.get("idea_id"))
    ps.clarified_idea = dict(state.get("clarified_idea") or {})
    ps.market_analysis = dict(state.get("market_analysis") or {})
    return ps


def _debug_ma(agent_name: str, ma: dict) -> None:
    print("\n====================")
    print(f"AFTER {agent_name}")
    snap = {k: ma.get(k) for k in ("keywords", "market", "competitor", "voc", "trends", "strategy")}
    print(json.dumps(snap, indent=2, ensure_ascii=False))


def _safe_filename_part(value: Any) -> str:
    s = re.sub(r"[^\w\-.]+", "_", str(value), flags=re.UNICODE).strip("_")
    return (s or "run")[:120]


def _merge_trend_queries(bundle) -> list:
    ft = bundle.for_trends()
    out = []
    seen = set()
    for x in (ft.get("trend_keywords") or []) + (ft.get("primary_keywords") or []):
        if not x:
            continue
        s = str(x).strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out[:12]


def _store_agent_data(ma: dict, key: str, result: dict) -> None:
    if result.get("status") == "success":
        data = result.get("data")
        ma[key] = data if data is not None else {}
    else:
        ma[key] = {}


def _final_market_analysis(ma: dict) -> dict:
    return {
        "keywords": ma.get("keywords") or {},
        "market": ma.get("market") or {},
        "competitor": ma.get("competitor") or {},
        "voc": ma.get("voc") or {},
        "trends": ma.get("trends") or {},
        "strategy": ma.get("strategy") or {},
    }


async def node_keyword_extractor(state: MarketGraphState) -> dict:
    extractor = KeywordExtractor()
    ps = _to_pipeline(state)
    bundle = await extractor.extract(ps.clarified_idea or {})
    ma = dict(state.get("market_analysis") or {})
    ma["keywords"] = bundle.to_dict()
    ma["market"] = {}
    ma["competitor"] = {}
    ma["voc"] = {}
    ma["trends"] = {}
    ma["strategy"] = {}
    ma["market_keywords"] = list(bundle.market_keywords or [])
    ma["competitor_queries"] = list(bundle.competitor_queries or [])
    ma["voc_queries"] = list(bundle.voc_keywords or [])
    ma["trend_queries"] = _merge_trend_queries(bundle)
    _debug_ma("keyword_extractor", ma)
    return {"market_analysis": ma}


async def node_market_sizing(state: MarketGraphState) -> dict:
    ps = _to_pipeline(state)
    agent = MarketSizingAgent()
    result = await agent.run(ps)
    ma = dict(state.get("market_analysis") or {})
    _store_agent_data(ma, "market", result)
    _debug_ma("market_sizing", ma)
    return {"market_analysis": ma}


async def node_competitor(state: MarketGraphState) -> dict:
    ps = _to_pipeline(state)
    agent = CompetitorAgent()
    result = await agent.run(ps)
    ma = dict(state.get("market_analysis") or {})
    _store_agent_data(ma, "competitor", result)
    _debug_ma("competitor", ma)
    return {"market_analysis": ma}


async def node_voc(state: MarketGraphState) -> dict:
    ps = _to_pipeline(state)
    agent = VOCAgent()
    result = await agent.run(ps)
    ma = dict(state.get("market_analysis") or {})
    _store_agent_data(ma, "voc", result)
    _debug_ma("voc", ma)
    return {"market_analysis": ma}


async def node_trends_risks(state: MarketGraphState) -> dict:
    ps = _to_pipeline(state)
    agent = TrendsRisksAgent()
    result = await agent.run(ps)
    ma = dict(state.get("market_analysis") or {})
    _store_agent_data(ma, "trends", result)
    _debug_ma("trends_risks", ma)
    return {"market_analysis": ma}


async def node_strategy_analysis(state: MarketGraphState) -> dict:
    ps = _to_pipeline(state)
    agent = StrategyAnalysisAgent()
    result = await agent.run(ps)
    ma = dict(state.get("market_analysis") or {})
    _store_agent_data(ma, "strategy", result)
    _debug_ma("strategy_analysis", ma)
    return {"market_analysis": ma}


async def node_save_results(state: MarketGraphState) -> dict:
    ma = dict(state.get("market_analysis") or {})
    idea_id = state.get("idea_id")
    clean_ma = _final_market_analysis(ma)
    payload = {
        "idea_id": idea_id,
        "clarified_idea": dict(state.get("clarified_idea") or {}),
        "market_analysis": clean_ma,
    }
    _WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
    name = f"market_analysis_{_safe_filename_part(idea_id)}.json"
    out_path = _WORKFLOWS_DIR / name
    out_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("\n====================")
    print(f"SAVED: {out_path}")
    return {"market_analysis": clean_ma}


def build_market_graph():
    g = StateGraph(MarketGraphState)
    g.add_node("keyword_extractor", node_keyword_extractor)
    g.add_node("market_sizing", node_market_sizing)
    g.add_node("competitor", node_competitor)
    g.add_node("voc", node_voc)
    g.add_node("trends_risks", node_trends_risks)
    g.add_node("strategy_analysis_agent", node_strategy_analysis)
    g.add_node("save_results", node_save_results)
    g.add_edge(START, "keyword_extractor")
    g.add_edge("keyword_extractor", "market_sizing")
    g.add_edge("market_sizing", "competitor")
    g.add_edge("competitor", "voc")
    g.add_edge("voc", "trends_risks")
    g.add_edge("trends_risks", "strategy_analysis_agent")
    g.add_edge("strategy_analysis_agent", "save_results")
    g.add_edge("save_results", END)
    return g.compile()
