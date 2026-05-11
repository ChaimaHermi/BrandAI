from agents.base_agent import BaseAgent
from prompts.market_analysis.prompt_strategy_analysis import PROMPT_STRATEGY_ANALYSIS

import json


class StrategyAnalysisAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            agent_name="strategy_analysis",
            temperature=0.2
        )

    def build_context(self, state):
        idea = state.clarified_idea or {}
        ma = state.market_analysis or {}

        if not idea:
            raise ValueError("missing_clarified_idea")

        trends = ma.get("trends", {}) or {}
        market = ma.get("market", {}) or {}
        competitor = ma.get("competitor", {}) or {}
        voc = ma.get("voc", {}) or {}
        keywords = ma.get("keywords", {}) or {}

        context_data = {
            "source_1_idea": {
                "idea_id": state.idea_id,
                "short_pitch": idea.get("short_pitch"),
                "problem": idea.get("problem"),
                "solution_description": idea.get("solution_description"),
                "target_users": idea.get("target_users"),
                "sector": idea.get("sector"),
                "country": idea.get("country"),
                "country_code": idea.get("country_code"),
                "language": idea.get("language"),
                "budget_min": idea.get("budget_min"),
                "budget_max": idea.get("budget_max"),
                "budget_currency": idea.get("budget_currency"),
            },
            "source_2_market_intelligence": {
                "market_data": market,
                "competitor_data": competitor,
                "voc_data": voc,
                "trends_risks_data": trends,
            },
        }

        context = json.dumps(context_data, indent=2, ensure_ascii=False)
        return context

    async def run(self, state):

        try:
            context = self.build_context(state)
        except Exception as e:
            return {
                "agent": "strategy_analysis",
                "status": "error",
                "error": str(e),
                "data": {}
            }

        response = await self._call_llm(
            system_prompt=PROMPT_STRATEGY_ANALYSIS,
            user_prompt=context
        )

        if not response:
            return {
                "agent": "strategy_analysis",
                "status": "error",
                "error": "Empty LLM response",
                "data": {}
            }

        data = self._parse_json(response)

        return {
            "agent": "strategy_analysis",
            "status": "success",
            "data": data
        }