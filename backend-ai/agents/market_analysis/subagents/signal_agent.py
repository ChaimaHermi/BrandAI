# ══════════════════════════════════════════════════════════════
# agents/market_analysis/subagents/signal_agent.py
# ══════════════════════════════════════════════════════════════
 
import asyncio, json, logging
from agents.base_agent import BaseAgent, PipelineState
from config.market_analysis_config import LLM_CONFIG
from schemas.market_analysis_schemas import Tendances
from tools.market_analysis.subagents_tools.signal_tools import (
    fetch_google_trends,
    fetch_tiktok_signals,
    fetch_regulatory,
)
 
logger = logging.getLogger("brandai.signal_agent")
 
 
class SignalAgent(BaseAgent):
 
    def __init__(self):
        super().__init__(
            agent_name="signal_agent",
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=LLM_CONFIG["max_tokens"],
            temperature=LLM_CONFIG["temperature"],
        )
 
    async def run(self, state: PipelineState, queries: dict) -> dict:
        """
        queries reçues de l'orchestrateur :
        {
            "trends_1":   "livraison repas",
            "trends_2":   "food delivery Tunisia",
            "tiktok":     "livraison repas Tunisie",
            "regulatory": "réglementation livraison repas Tunisie",
            "country":    "TN"
        }
        """
        self._log_start(state)
        country = queries.get("country", "TN")
 
        try:
            trends_1, trends_2, tiktok, regulatory = await asyncio.gather(
                fetch_google_trends(queries["trends_1"], country),
                fetch_google_trends(queries["trends_2"], country),
                fetch_tiktok_signals(queries["tiktok"]),
                fetch_regulatory(queries["regulatory"], country),
            )

            raw_data = {
                "trends_1": trends_1,
                "trends_2": trends_2,
                "tiktok": tiktok,
                "regulatory": regulatory,
            }
 
            llm_response = await self._call_llm(
                system_prompt=self._load_prompt("signal_agent.txt", state),
                user_prompt=json.dumps(raw_data, ensure_ascii=False, default=str),
            )
 
            data   = self._parse_json(llm_response)
            output = Tendances(**data)
            self._log_success(output)
            return output.dict()
 
        except Exception as e:
            self._log_error(e)
            raise
 
    def _load_prompt(self, filename: str, state: PipelineState) -> str:
        try:
            with open(f"prompts/market_analysis/{filename}", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"""Tu es un expert en signaux marché pour : {state.sector}.
Tu reçois des données brutes de Google Trends, TikTok et sources réglementaires.
Retourne UNIQUEMENT un JSON valide avec cette structure :
{{
  "direction": "RISING|STABLE|FALLING",
  "signal_strength": "HIGH|MEDIUM|LOW",
  "peak_period": "null ou ex: juillet 2024",
  "rising_queries": [],
  "hashtags": [],
  "hashtags_disponibles": false,
  "viral_score": "HIGH|MEDIUM|LOW|NONE",
  "viral_signals": [],
  "sector_context": "",
  "news_signals": [],
  "regulatory_barriers": []
}}"""
 
 