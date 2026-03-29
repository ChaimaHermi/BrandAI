# ══════════════════════════════════════════════════════════════
# agents/market_analysis/subagents/market_voc_agent.py
# ══════════════════════════════════════════════════════════════

import asyncio
import json

from agents.base_agent import BaseAgent, PipelineState
from config.market_analysis_config import LLM_CONFIG
from schemas.market_analysis_schemas import MarketVoc
from tools.market_analysis.subagents_tools.market_voc_tools import (
    fetch_tavily_insights, fetch_reddit_voc,
    fetch_youtube_voc, fetch_newsapi, fetch_worldbank,
)
 
 
class MarketVocAgent(BaseAgent):
 
    def __init__(self):
        super().__init__(
            agent_name="market_voc_agent",
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=LLM_CONFIG["max_tokens"],
            temperature=LLM_CONFIG["temperature"],
        )
 
    async def run(self, state: PipelineState, queries: dict) -> dict:
        """
        queries reçues de l'orchestrateur :
        {
            "tavily":   "marché livraison repas Tunisie",
            "reddit":   "food delivery Tunisia review problem",
            "youtube":  "livraison repas Tunisie avis",
            "news":     "startup livraison repas Tunisie",
            "country":  "TN",
            "language": "fr"
        }
        """
        self._log_start(state)
        country  = queries.get("country", "TN")
        language = queries.get("language", "fr")
 
        try:
            tavily, reddit, youtube, news, worldbank = await asyncio.gather(
                fetch_tavily_insights(queries["tavily"]),
                fetch_reddit_voc(queries["reddit"]),
                fetch_youtube_voc(queries["youtube"]),
                fetch_newsapi(queries["news"], language),
                fetch_worldbank(country),
            )
 
            raw_data = {
                "tavily": tavily, "reddit": reddit,
                "youtube": youtube, "news": news, "worldbank": worldbank,
            }
 
            llm_response = await self._call_llm(
                system_prompt=self._load_prompt("market_voc_agent.txt", state),
                user_prompt=json.dumps(raw_data, ensure_ascii=False, default=str),
            )
 
            data   = self._parse_json(llm_response)
            output = MarketVoc(**data)
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
            return f"""Tu es un expert VOC pour : {state.sector}.
Tu reçois des données de Tavily, Reddit, YouTube, NewsAPI et World Bank.
Retourne UNIQUEMENT un JSON valide :
{{
  "demand_level": "fort|modere|faible|inexistant",
  "demand_summary": "",
  "top_voc": [{{"theme":"","recurrence":"","citation":"","source":""}}],
  "personas": [{{"segment":"","tranche_age":"","comportement":"","pain_points":[],"motivations":[],"signal_niveau":""}}],
  "macro": {{"population":null,"gdp_per_capita":null,"internet_pct":null,"mobile_per100":null,"urban_pct":null,"youth_pct":null}},
  "news_signals": []
}}
Règle absolue : citations = texte réel extrait des données, jamais inventé."""
 