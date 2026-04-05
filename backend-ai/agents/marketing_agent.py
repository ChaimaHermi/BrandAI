import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent, PipelineState

logger = logging.getLogger("brandai.marketing_agent")


class MarketingAgent(BaseAgent):
    def __init__(self):
        super().__init__("marketing_agent")

    async def run(self, state: PipelineState) -> Dict[str, Any]:
        logger.info(f"[marketing_agent] ▶ START | idea_id={state.idea_id}")

        idea = state.clarified_idea or {}
        market = state.market_analysis or {}

        if not idea:
            logger.error("[marketing_agent] missing clarified idea")
            return {"error": "missing idea"}
        # market_analysis peut rester vide (analyse marché hors pipeline LangGraph)

        prompt = self._build_prompt(idea, market)

        try:
            response = await self._call_llm(
                system_prompt=(
                    "You are a senior marketing strategist. "
                    "Return only valid JSON."
                ),
                user_prompt=prompt,
            )

            result = self._parse_response(response)

            state.marketing_plan = result

            logger.info("[marketing_agent] ✅ SUCCESS")
            return result

        except Exception as e:
            logger.error(f"[marketing_agent] ❌ ERROR: {e}")
            return {"error": str(e)}

    # ─────────────────────────────────────────
    # PROMPT
    # ─────────────────────────────────────────

    def _build_prompt(self, idea: dict, market: dict) -> str:
        return f"""
You are a senior marketing strategist.

Your task is to generate a structured marketing plan based on:
1. Business idea
2. Market analysis (optionnel — peut être vide ; déduis depuis l’idée si besoin)

IMPORTANT:
- Use inference when data is incomplete
- Be realistic and practical
- Do NOT generate content posts
- Only strategy

INPUT:

IDEA:
{idea}

MARKET ANALYSIS (vide = pas encore fourni) :
{market}

OUTPUT FORMAT (STRICT JSON):

{{
  "positioning": {{
    "target_segment": "",
    "value_proposition": "",
    "differentiation": ""
  }},
  "targeting": {{
    "primary_persona": "",
    "secondary_personas": [],
    "market_segment_focus": ""
  }},
  "messaging": {{
    "main_message": "",
    "pain_point_focus": "",
    "emotional_hook": ""
  }},
  "channels": {{
    "primary_channels": [],
    "secondary_channels": [],
    "justification": ""
  }},
  "content_direction": {{
    "angles": [],
    "content_goals": [],
    "platform_focus": [],
    "tone": ""
  }},
  "pricing_strategy": {{
    "model": "",
    "pricing_logic": "",
    "justification": ""
  }},
  "go_to_market": {{
    "target_first_users": "",
    "launch_strategy": "",
    "partnerships": [],
    "early_growth_tactics": []
  }},
  "action_plan": {{
    "short_term": [],
    "mid_term": [],
    "long_term": []
  }},
  "assumptions": [],
  "confidence_level": "low | medium | high"
}}
"""

    # ─────────────────────────────────────────
    # PARSER
    # ─────────────────────────────────────────

    def _parse_response(self, response: str) -> Dict[str, Any]:
        try:
            return self._parse_json(response)
        except Exception:
            logger.warning("[marketing_agent] fallback parsing")
            return {
                "error": "invalid_json",
                "raw": response[:1000]
            }