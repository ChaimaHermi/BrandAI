# ══════════════════════════════════════════════════════════════
# agents/market_analysis/subagents/signal_agent.py  [v2]
# Changements :
#   1. fetch_google_trends : maintenant 3 data_types en parallèle
#   2. fetch_google_autocomplete (NOUVEAU) : suggestions temps réel
#   3. fetch_tavily_trends (NOUVEAU)       : news récentes comme proxy tendances
#   4. raw_data enrichi → LLM a plus de données pour rising_queries
# ══════════════════════════════════════════════════════════════

import asyncio, json, logging
from agents.base_agent import BaseAgent, PipelineState
from config.market_analysis_config import LLM_CONFIG
from schemas.market_analysis_schemas import Tendances
from tools.market_analysis.subagents_tools.signal_tools import (
    fetch_google_trends,
    fetch_google_autocomplete,   # NOUVEAU
    fetch_tavily_trends,         # NOUVEAU
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
        queries reçues :
        {
            "trends_1":   "livraison repas sains",
            "trends_2":   "healthy food delivery Tunisia",
            "tiktok":     "repas sain livraison",
            "regulatory": "réglementation livraison repas Tunisie",
            "country":    "TN"
        }
        """
        self._log_start(state)
        country = queries.get("country", "TN")

        try:
            # ── 6 appels en parallèle ─────────────────────────
            (
                trends_1,
                trends_2,
                autocomplete_1,   # NOUVEAU — suggestions pour trends_1
                autocomplete_2,   # NOUVEAU — suggestions pour trends_2
                tavily_trends,    # NOUVEAU — news récentes comme proxy
                tiktok,
                regulatory,
            ) = await asyncio.gather(
                fetch_google_trends(queries["trends_1"], country),
                fetch_google_trends(queries["trends_2"], country),
                fetch_google_autocomplete(queries["trends_1"], country),
                fetch_google_autocomplete(queries["trends_2"], country),
                fetch_tavily_trends(queries["trends_1"], country),
                fetch_tiktok_signals(queries["tiktok"]),
                fetch_regulatory(queries["regulatory"], country),
            )

            raw_data = {
                "trends_1":       trends_1,
                "trends_2":       trends_2,
                "autocomplete_1": autocomplete_1,  # suggestions temps réel
                "autocomplete_2": autocomplete_2,
                "tavily_trends":  tavily_trends,   # news récentes du secteur
                "tiktok":         tiktok,
                "regulatory":     regulatory,
            }

            llm_response = await self._call_llm(
                system_prompt=self._load_prompt("signal_agent.txt", state),
                user_prompt=json.dumps(raw_data, ensure_ascii=False, default=str),
            )

            data   = self._parse_json(llm_response)

            # ── Post-processing : si rising_queries toujours vide,
            #    utiliser les suggestions autocomplete comme fallback ──
            if not data.get("rising_queries"):
                fallback = []
                for src in (autocomplete_1, autocomplete_2):
                    fallback.extend(src.get("suggestions", []))
                # Dédupliquer et garder max 5
                seen = set()
                unique = []
                for q in fallback:
                    if q.lower() not in seen:
                        seen.add(q.lower())
                        unique.append(q)
                    if len(unique) >= 5:
                        break
                if unique:
                    data["rising_queries"] = unique
                    logger.info(
                        f"[signal_agent] rising_queries vide → "
                        f"fallback autocomplete : {unique}"
                    )

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

Tu reçois :
- trends_1, trends_2      : données Google Trends (TIMESERIES + RELATED_QUERIES + RELATED_TOPICS)
- autocomplete_1/2        : suggestions Google Autocomplete temps réel
- tavily_trends           : news récentes du secteur (signaux de tendance)
- tiktok                  : désactivé
- regulatory              : barrières réglementaires

RISING_QUERIES — NOUVELLE RÈGLE :
Cherche dans CET ORDRE :
1. trends_1.rising_queries et trends_2.rising_queries  (RELATED_QUERIES SerpAPI)
2. trends_1.rising_topics  et trends_2.rising_topics   (RELATED_TOPICS SerpAPI)
3. autocomplete_1.suggestions et autocomplete_2.suggestions (temps réel)
4. tavily_trends.signals   (titres de news récentes comme proxy)
→ Combine toutes les sources disponibles, déduplique, garde max 8

SECTOR_CONTEXT :
Synthétise depuis tavily_trends.signals + regulatory.results en 2-3 phrases.

Retourne UNIQUEMENT un JSON valide :
{{
  "direction": "RISING|STABLE|FALLING",
  "signal_strength": "HIGH|MEDIUM|LOW",
  "peak_period": null,
  "rising_queries": ["q1", "q2", "q3"],
  "hashtags": [],
  "hashtags_disponibles": false,
  "viral_score": "NONE",
  "viral_signals": [],
  "sector_context": "2-3 phrases ou chaîne vide",
  "news_signals": [],
  "regulatory_barriers": []
}}"""