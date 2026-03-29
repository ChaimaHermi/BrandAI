# ══════════════════════════════════════════════════════════════
# agents/market_analysis/subagents/competitor_agent.py
# ══════════════════════════════════════════════════════════════

import asyncio
import json

from agents.base_agent import BaseAgent, PipelineState
from config.market_analysis_config import LLM_CONFIG
from schemas.market_analysis_schemas import CompetitorSection
from tools.market_analysis.subagents_tools.competitor_tools import (
    fetch_serp_competitors, fetch_serp_maps,
    fetch_tavily_competitor_insights,
)
 
 
class CompetitorAgent(BaseAgent):
 
    def __init__(self):
        super().__init__(
            agent_name="competitor_agent",
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=LLM_CONFIG["max_tokens"],
            temperature=LLM_CONFIG["temperature"],
        )
 
    async def run(self, state: PipelineState, queries: dict) -> dict:
        """
        queries reçues de l'orchestrateur :
        {
            "competitors": "application livraison repas Tunisie",
            "maps":        "livraison repas Tunis",
            "tavily":      "Jumia Food Glovo avis problèmes Tunisie",
            "country":     "TN"
        }
        """
        self._log_start(state)
        country = queries.get("country", "TN")
 
        try:
            serp_search, serp_maps, tavily = await asyncio.gather(
                fetch_serp_competitors(queries["competitors"], country),
                fetch_serp_maps(queries["maps"], country),
                fetch_tavily_competitor_insights(queries["tavily"]),
            )
 
            raw_data = {
                "serp_search": serp_search,
                "serp_maps":   serp_maps,
                "tavily":      tavily,
            }
 
            llm_response = await self._call_llm(
                system_prompt=self._load_prompt("competitor_agent.txt", state),
                user_prompt=json.dumps(raw_data, ensure_ascii=False, default=str),
            )
 
            data   = self._parse_json(llm_response)
            output = CompetitorSection(**data)
            self._log_success(output)
            return output.dict()
 
        except Exception as e:
            self._log_error(e)
            raise
 
    def _load_prompt(self, filename: str, state: PipelineState) -> str:
        fallback = f"""Tu es un expert en intelligence concurrentielle pour : {state.sector}.
Zone géographique : {getattr(state, 'country', 'TN')}.

Tu reçois des données de Google Search (serp_search), Google Maps (serp_maps) et Tavily (tavily).

MISSION : Extraire les concurrents réels depuis serp_search et leurs faiblesses depuis tavily.

Retourne UNIQUEMENT un JSON valide :
{{
  "top_competitors": [
    {{
      "nom": "Nom extrait depuis serp_search.results[].title",
      "type": "digital | local | regional | international",
      "faiblesse_principale": "extraite depuis snippet tavily ou serp — mot clé négatif obligatoire",
      "weaknesses": ["faiblesse1 extraite des snippets", "faiblesse2"],
      "key_strengths": ["force1 extraite des snippets", "force2"],
      "positioning": "description du positionnement depuis snippet"
    }}
  ],
  "opportunite_niveau": "fenetre_ouverte | partielle | saturee | absente",
  "opportunite_summary": "Résumé en 2 phrases basé sur les faiblesses trouvées"
}}

Règles OBLIGATOIRES :
- top_competitors : extraire 3 à 5 concurrents depuis serp_search.results
  en respectant l'ordre des positions Google
- NE JAMAIS retourner top_competitors vide
- faiblesse_principale : chercher dans les snippets tavily ET serp
  les mots négatifs : "problème", "bug", "lent", "manque", "difficile",
  "complexe", "limité", "guerre des prix", "saturation", "cher",
  "mauvais", "artificiel", "trompeur", "plainte", "insatisfait"
  → Si trouvé : écrire la faiblesse en 1 phrase claire
  → Si non trouvé : écrire "Manque d'adaptation au contexte local"
  → NE JAMAIS écrire "Aucune faiblesse détectée"
- weaknesses : extraire au minimum 1 faiblesse par concurrent
  depuis les snippets disponibles — jamais []
- key_strengths : extraire depuis les snippets — jamais []
  si le snippet mentionne des points positifs
- opportunite_niveau :
  → "fenetre_ouverte" si faiblesses majeures détectées
  → "partielle" si faiblesses mineures ou peu de données
  → "saturee" UNIQUEMENT si concurrents très bien notés
     ET aucune frustration dans les données
  → jamais "saturee" si top_voc contient des frustrations
- Retourne UNIQUEMENT le JSON"""

        try:
            with open(f"prompts/market_analysis/{filename}", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            return fallback

        if filename == "competitor_agent.txt" and "faiblesse_principale" not in content:
            return fallback

        return content