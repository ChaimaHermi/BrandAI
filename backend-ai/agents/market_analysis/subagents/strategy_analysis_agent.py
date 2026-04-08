from agents.base_agent import BaseAgent
from prompts.market_analysis.prompt_strategy_analysis import PROMPT_STRATEGY_ANALYSIS

import json


class StrategyAnalysisAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            agent_name="strategy_analysis",
            temperature=0.2
        )

    def _top_n(self, items, n=5):
        if not isinstance(items, list):
            return []
        out = []
        for item in items:
            if item is None:
                continue
            if isinstance(item, str):
                item = item.strip()
                if not item:
                    continue
            out.append(item)
            if len(out) >= n:
                break
        return out

    def _compress_competitors(self, competitor_block, n=5):
        competitors = (competitor_block or {}).get("competitors", [])
        out = []
        for c in competitors[:n]:
            if not isinstance(c, dict):
                continue
            out.append({
                "name": c.get("name"),
                "positioning": c.get("positioning"),
                "target_users": c.get("target_users"),
                "type": c.get("type"),
                "scope": c.get("scope"),
            })
        return out

    def _extract_voc_pains(self, voc_block, n=5):
        vb = voc_block or {}
        pains = []
        pains.extend(vb.get("pain_points", []) or [])
        pains.extend(vb.get("frustrations", []) or [])
        return self._top_n(pains, n=n)

    def build_context(self, state):
        idea = state.clarified_idea or {}
        ma = state.market_analysis or {}

        if not idea:
            raise ValueError("missing_clarified_idea")

        trends = ma.get("trends", {}) or {}

        context_data = {
            "user_business_idea": {
                "short_pitch": idea.get("short_pitch"),
                "problem": idea.get("problem"),
                "solution_description": idea.get("solution_description"),
                "target_users": idea.get("target_users"),
                "sector": idea.get("sector"),
                "country": idea.get("country"),
                "country_code": idea.get("country_code"),
                "language": idea.get("language"),
            },
            "market_intelligence": {
                "competitors_top5": self._compress_competitors(ma.get("competitor", {}), n=5),
                "market_trends_top5": self._top_n(trends.get("market_trends", []), n=5),
                "market_risks_top5": self._top_n(trends.get("market_risks", []), n=5),
                "voc_pain_points_top5": self._extract_voc_pains(ma.get("voc", {}), n=5),
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