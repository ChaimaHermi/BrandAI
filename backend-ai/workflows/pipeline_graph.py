from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from agents.base_agent import PipelineState
from agents.idea_clarifier import IdeaClarifierAgent
from agents.market_analysis.market_analysis_agent import MarketAnalysisAgent


class GraphState(TypedDict):
    idea_id: int
    name: str
    sector: str
    description: str
    target_audience: str
    clarified_idea: dict[str, Any]
    market_analysis: dict[str, Any]
    status: str
    errors: list[str]


clarifier = IdeaClarifierAgent()
market = MarketAnalysisAgent()


def _to_pipeline_state(state: GraphState) -> PipelineState:
    ps = PipelineState(
        idea_id=state.get("idea_id"),
        name=state.get("name", ""),
        sector=state.get("sector", ""),
        description=state.get("description", ""),
        target_audience=state.get("target_audience", ""),
    )
    ps.clarified_idea = state.get("clarified_idea", {}) or {}
    ps.market_analysis = state.get("market_analysis", {}) or {}
    ps.status = state.get("status", "running")
    ps.errors = state.get("errors", []) or []
    return ps


async def run_clarifier(state: GraphState) -> dict[str, Any]:
    # Skip clarifier if payload already validated and provided.
    if state.get("clarified_idea"):
        return {"status": "clarified"}

    ps = _to_pipeline_state(state)
    result = await clarifier.run_start(ps)
    result_type = result.get("type")

    if result_type == "clarified":
        return {
            "status": "clarified",
            "clarified_idea": {
                "short_pitch": result.get("short_pitch") or ps.name,
                "solution_description": result.get("solution_description") or ps.description,
                "target_users": result.get("target_users") or ps.target_audience,
                "problem": result.get("problem") or ps.description,
                "sector": result.get("sector") or ps.sector,
                "country_code": result.get("country_code") or "TN",
                "language": result.get("language") or "fr",
                "score": result.get("score", 0),
            },
        }

    # questions or refused: stop pipeline and propagate status.
    return {
        "status": result_type or "error",
        "errors": [*state.get("errors", []), f"clarifier_result:{result_type}"],
        "clarified_idea": {},
    }


async def run_market_analysis(state: GraphState) -> dict[str, Any]:
    if not state.get("clarified_idea"):
        return {
            "status": "error",
            "errors": [*state.get("errors", []), "market_analysis: missing clarified_idea"],
        }

    ps = _to_pipeline_state(state)
    ps = await market.run(ps)
    return {
        "status": "market_done",
        "market_analysis": ps.market_analysis,
    }


def _route_entry(state: GraphState):
    if state.get("clarified_idea"):
        return "market_analysis"
    return "idea_clarifier"


def _route_after_clarifier(state: GraphState):
    if state.get("status") == "clarified" and state.get("clarified_idea"):
        return "market_analysis"
    return END


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("idea_clarifier", run_clarifier)
    graph.add_node("market_analysis", run_market_analysis)

    graph.add_conditional_edges(START, _route_entry, {
        "idea_clarifier": "idea_clarifier",
        "market_analysis": "market_analysis",
    })
    graph.add_conditional_edges("idea_clarifier", _route_after_clarifier, {
        "market_analysis": "market_analysis",
        END: END,
    })
    graph.add_edge("market_analysis", END)
    return graph.compile()