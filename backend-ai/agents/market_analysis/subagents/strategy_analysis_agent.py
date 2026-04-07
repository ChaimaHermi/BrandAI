from agents.base_agent import BaseAgent
from prompts.market_analysis.prompt_strategy_analysis import PROMPT_STRATEGY_ANALYSIS

import json


_CONTEXT_MAX = 6000


class StrategyAnalysisAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            agent_name="strategy_analysis",
            temperature=0.2
        )

    def build_context(self, state):
        ma = state.market_analysis or {}

        context_data = {
            "market": ma.get("market", {}),
            "competitors": ma.get("competitor", {}),
            "voc": ma.get("voc", {}),
            "trends": ma.get("trends", {})
        }

        context = json.dumps(context_data, indent=2, ensure_ascii=False)

        if len(context) > _CONTEXT_MAX:
            context = context[:_CONTEXT_MAX]

        return context

    async def run(self, state):

        context = self.build_context(state)

        print("[DEBUG STRATEGY] CONTEXT LENGTH:", len(context))
        print("[DEBUG STRATEGY] APPROX TOKENS:", len(context) // 4)

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