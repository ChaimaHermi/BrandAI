from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from agents.base_agent import PipelineState
from agents.marketing.marketing_agent import MarketingAgent
from pipeline.market_graph import (
    node_competitor,
    node_keyword_extractor,
    node_market_sizing,
    node_save_results,
    node_strategy_analysis,
    node_trends_risks,
    node_voc,
)


class MarketStrategyGraphState(TypedDict, total=False):
    idea_id: Any
    clarified_idea: dict
    market_analysis: dict
    marketing_plan: dict


async def node_marketing_plan(state: MarketStrategyGraphState) -> dict:
    ps = PipelineState(
        idea_id=state.get("idea_id"),
        name="",
        sector=str((state.get("clarified_idea") or {}).get("sector") or ""),
        description=str((state.get("clarified_idea") or {}).get("solution_description") or ""),
        target_audience=str((state.get("clarified_idea") or {}).get("target_users") or ""),
    )
    ps.clarified_idea = dict(state.get("clarified_idea") or {})
    ps.market_analysis = dict(state.get("market_analysis") or {})
    agent = MarketingAgent()
    result = await agent.run(ps) or {}
    return {"marketing_plan": result}


def build_market_strategy_graph():
    g = StateGraph(MarketStrategyGraphState)
    g.add_node("keyword_extractor", node_keyword_extractor)
    g.add_node("market_sizing", node_market_sizing)
    g.add_node("competitor", node_competitor)
    g.add_node("voc", node_voc)
    g.add_node("trends_risks", node_trends_risks)
    g.add_node("strategy_analysis_agent", node_strategy_analysis)
    g.add_node("save_results", node_save_results)
    g.add_node("marketing_plan", node_marketing_plan)

    g.add_edge(START, "keyword_extractor")
    g.add_edge("keyword_extractor", "market_sizing")
    g.add_edge("market_sizing", "competitor")
    g.add_edge("competitor", "voc")
    g.add_edge("voc", "trends_risks")
    g.add_edge("trends_risks", "strategy_analysis_agent")
    g.add_edge("strategy_analysis_agent", "save_results")
    g.add_edge("save_results", "marketing_plan")
    g.add_edge("marketing_plan", END)

    return g.compile()
