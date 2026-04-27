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

    def _compress_competitors(self, competitor_block, n=8):
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

    def _extract_voc_pains(self, voc_block, n=8):
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
                # Full raw outputs from subagents to preserve context fidelity.
                "market_data_full": market,
                "competitor_full": competitor,
                "voc_full": voc,
                "trends_risks_full": trends,
                "keywords_full": keywords,
                # Digest views to guide LLM attention.
                "market_highlights": {
                    "market_size": market.get("market_size"),
                    "growth_rate": market.get("growth_rate"),
                    "key_segments": self._top_n(market.get("segments", []), n=8),
                },
                "competitors_top": self._compress_competitors(competitor, n=8),
                "voc_pains_top": self._extract_voc_pains(voc, n=8),
                "trends_top": self._top_n(trends.get("market_trends", []), n=8),
                "risks_top": self._top_n(trends.get("market_risks", []), n=8),
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