"""
Agent d’analyse de marché : orchestre l’extraction de mots-clés puis (plus tard) les sous-agents.
"""

from agents.base_agent import BaseAgent, PipelineState
from agents.market_analysis.orchestrator.keyword_extractor import extract_keywords
from config.market_analysis_config import LLM_CONFIG, OUTPUT_SCHEMA_VERSION


def _idea_from_state(state: PipelineState) -> dict:
    c = state.clarified_idea or {}
    if isinstance(c, dict) and (c.get("short_pitch") or c.get("solution_description")):
        return {
            "short_pitch": c.get("short_pitch") or state.name or "",
            "solution_description": c.get("solution_description") or state.description or "",
            "problem": c.get("problem") or "",
            "target_users": c.get("target_users") or state.target_audience or "",
            "sector": c.get("sector") or state.sector or "",
            "country_code": c.get("country_code") or getattr(state, "country", None) or "TN",
            "language": c.get("language") or "fr",
        }
    return {
        "short_pitch": state.name or "",
        "solution_description": state.description or "",
        "problem": state.description or "",
        "target_users": state.target_audience or "",
        "sector": state.sector or "",
        "country_code": getattr(state, "country", None) or "TN",
        "language": "fr",
    }


class MarketAnalysisAgent(BaseAgent):
    """Pipeline marché : pour l’instant — extraction KeywordBundle unique."""

    def __init__(self):
        super().__init__(
            agent_name="market_analysis",
            temperature=LLM_CONFIG["temperature"],
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=min(LLM_CONFIG.get("max_tokens") or 4096, 8000),
        )

    async def run(self, state: PipelineState) -> PipelineState:
        idea = _idea_from_state(state)
        self.logger.info(
            "[market_analysis] Extraction mots-clés | idea_id=%s | pitch=%r",
            state.idea_id,
            (idea.get("short_pitch") or "")[:80],
        )

        bundle = await extract_keywords(idea)

        state.market_analysis = {
            "output_schema_version": OUTPUT_SCHEMA_VERSION,
            "keyword_bundle": bundle.to_dict(),
            "keyword_routing": {
                "agent_market": bundle.for_agent_market(),
                "agent_competitors": bundle.for_agent_competitors(),
                "agent_voc": bundle.for_agent_voc(),
                "agent_trends": bundle.for_agent_trends(),
            },
        }

        self.logger.info(
            "[market_analysis] keyword_bundle prêt | primary=%s",
            len(bundle.primary_keywords),
        )
        return state
