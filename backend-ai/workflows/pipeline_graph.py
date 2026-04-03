from typing import Any, TypedDict
import json
import logging

from langgraph.graph import END, START, StateGraph

from agents.base_agent import PipelineState
from agents.branding.branding_orchestrator import BrandingOrchestratorAgent
from agents.idea_clarifier import IdeaClarifierAgent
from agents.market_analysis.market_analysis_agent import MarketAnalysisAgent
from agents.marketing_agent import MarketingAgent

# ─────────────────────────────────────────
# LOGGER
# ─────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pipeline")


def log_state(step: str, state: dict):
    try:
        logger.info(f"\n===== {step} =====")
        logger.info(json.dumps(state, indent=2, ensure_ascii=False))
    except Exception:
        logger.info(f"{step} | state non sérialisable")


# ─────────────────────────────────────────
# STATE
# ─────────────────────────────────────────

class GraphState(TypedDict):
    idea_id: int
    name: str
    sector: str
    description: str
    target_audience: str

    clarified_idea: dict[str, Any]
    market_analysis: dict[str, Any]
    brand_identity: dict[str, Any]
    marketing_plan: dict[str, Any]

    status: str
    errors: list[str]


# ─────────────────────────────────────────
# AGENTS
# ─────────────────────────────────────────

clarifier = IdeaClarifierAgent()
market = MarketAnalysisAgent()
branding = BrandingOrchestratorAgent()
marketing = MarketingAgent()


# ─────────────────────────────────────────
# CONVERTER
# ─────────────────────────────────────────

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
    ps.brand_identity = state.get("brand_identity", {}) or {}
    ps.marketing_plan = state.get("marketing_plan", {}) or {}
    ps.status = state.get("status", "running")
    ps.errors = state.get("errors", []) or []
    return ps


# ─────────────────────────────────────────
# NODE 1 — CLARIFIER
# ─────────────────────────────────────────

async def run_clarifier(state: GraphState) -> dict[str, Any]:
    log_state("INPUT → CLARIFIER", state)

    if state.get("clarified_idea"):
        return {"status": "clarified"}

    ps = _to_pipeline_state(state)
    result = await clarifier.run_start(ps)
    result_type = result.get("type")

    logger.info(f"Clarifier result: {result_type}")

    if result_type == "clarified":
        output = {
            "status": "clarified",
            "clarified_idea": {
                "short_pitch": result.get("short_pitch") or ps.name,
                "solution_description": result.get("solution_description") or ps.description,
                "target_users": result.get("target_users") or ps.target_audience,
                "problem": result.get("problem") or ps.description,
                "sector": result.get("sector") or ps.sector,
                "country": result.get("country") or "Non précisé",
                "country_code": result.get("country_code") or "TN",
                "language": result.get("language") or "fr",
                "score": result.get("score", 0),
            },
        }
        log_state("OUTPUT → CLARIFIER", output)
        return output

    if result_type == "questions":
        return {
            "status": "need_input",
            "questions": result.get("questions", []),
        }

    return {
        "status": "error",
        "errors": [f"clarifier:{result_type}"],
    }


# ─────────────────────────────────────────
# NODE 2 — MARKET
# ─────────────────────────────────────────

async def run_market_analysis(state: GraphState) -> dict[str, Any]:
    log_state("INPUT → MARKET", state)

    if not state.get("clarified_idea"):
        return {"status": "error", "errors": ["missing clarified idea"]}

    ps = _to_pipeline_state(state)

    try:
        ps = await market.run(ps)

        output = {
            "status": "market_done",
            "market_analysis": ps.market_analysis,
        }

        log_state("OUTPUT → MARKET", output)
        return output

    except Exception as e:
        return {"status": "error", "errors": [str(e)]}


# ─────────────────────────────────────────
# NODE 3 — BRANDING
# ─────────────────────────────────────────

async def run_branding(state: GraphState) -> dict[str, Any]:
    log_state("INPUT → BRANDING", state)

    if not state.get("clarified_idea"):
        return {"status": "error", "errors": ["missing clarified idea for branding"]}

    ps = _to_pipeline_state(state)

    try:
        ps = await branding.run(ps)
        output = {
            "status": "branding_done" if ps.status == "branding_done" else ps.status,
            "brand_identity": ps.brand_identity,
        }
        log_state("OUTPUT → BRANDING", output)
        return output
    except Exception as e:
        return {"status": "error", "errors": [str(e)]}


# ─────────────────────────────────────────
# NODE 4 — MARKETING
# ─────────────────────────────────────────

async def run_marketing(state: GraphState) -> dict[str, Any]:
    log_state("INPUT → MARKETING", state)

    if not state.get("market_analysis"):
        return {"status": "error", "errors": ["missing market_analysis"]}

    ps = _to_pipeline_state(state)

    try:
        result = await marketing.run(ps)

        output = {
            "status": "marketing_done",
            "marketing_plan": result,
        }

        log_state("OUTPUT → MARKETING", output)
        return output

    except Exception as e:
        return {"status": "error", "errors": [str(e)]}


# ─────────────────────────────────────────
# ROUTING
# ─────────────────────────────────────────

def _route_entry(state: GraphState):
    logger.info(f"ROUTE ENTRY → clarified? {bool(state.get('clarified_idea'))}")
    return "market_analysis" if state.get("clarified_idea") else "idea_clarifier"


def _route_after_clarifier(state: GraphState):
    return "market_analysis" if state.get("status") == "clarified" else END


def _route_after_market(state: GraphState):
    return "branding" if state.get("status") == "market_done" else END


def _route_after_branding(state: GraphState):
    return "marketing" if state.get("status") == "branding_done" else END


# ─────────────────────────────────────────
# BUILD GRAPH
# ─────────────────────────────────────────

def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("idea_clarifier", run_clarifier)
    graph.add_node("market_analysis", run_market_analysis)
    graph.add_node("branding", run_branding)
    graph.add_node("marketing", run_marketing)

    # ENTRY
    graph.add_conditional_edges(START, _route_entry, {
        "idea_clarifier": "idea_clarifier",
        "market_analysis": "market_analysis",
    })

    # AFTER CLARIFIER
    graph.add_conditional_edges("idea_clarifier", _route_after_clarifier, {
        "market_analysis": "market_analysis",
        END: END,
    })

    # AFTER MARKET
    graph.add_conditional_edges("market_analysis", _route_after_market, {
        "branding": "branding",
        END: END,
    })

    # AFTER BRANDING
    graph.add_conditional_edges("branding", _route_after_branding, {
        "marketing": "marketing",
        END: END,
    })

    # END
    graph.add_edge("marketing", END)

    return graph.compile()