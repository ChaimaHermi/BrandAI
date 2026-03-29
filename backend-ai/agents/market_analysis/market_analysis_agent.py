# ══════════════════════════════════════════════════════════════
# agents/market_analysis/market_analysis_agent.py
# Agent racine — génère queries + orchestre + synthèse finale
# ══════════════════════════════════════════════════════════════

import asyncio, json, logging, time
from datetime import datetime

from agents.base_agent import BaseAgent, PipelineState
from agents.market_analysis.subagents.signal_agent import SignalAgent
from agents.market_analysis.subagents.market_voc_agent import MarketVocAgent
from agents.market_analysis.subagents.competitor_agent import CompetitorAgent
from config.market_analysis_config import LLM_CONFIG

logger = logging.getLogger("brandai.market_analysis_agent")


class MarketAnalysisAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            agent_name="market_analysis_agent",
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=LLM_CONFIG["max_tokens"],
            temperature=LLM_CONFIG["temperature"],
        )
        self.signal_agent     = SignalAgent()
        self.market_voc_agent = MarketVocAgent()
        self.competitor_agent = CompetitorAgent()

    # ──────────────────────────────────────────────────────────
    # ENTRÉE PRINCIPALE
    # ──────────────────────────────────────────────────────────

    async def run(self, state: PipelineState) -> PipelineState:
        self._log_start(state)
        start = time.time()

        try:
            # ── LLM 1 : génère toutes les queries ─────────────
            # Utilise clarified_idea (IdeaClarifier) en priorité
            # Fallback sur les champs de base du state si vide
            logger.info("[market_analysis_agent] LLM 1 — génération queries")
            idea = state.clarified_idea or {}
            queries_raw = await self._call_llm(
                system_prompt=self._queries_system_prompt(),
                user_prompt=json.dumps({
                    "short_pitch":          idea.get("short_pitch",          state.name),
                    "solution_description": idea.get("solution_description", state.description),
                    "target_users":         idea.get("target_users",         state.target_audience),
                    "problem":              idea.get("problem",              state.description),
                    "secteur":              idea.get("sector",               state.sector),
                    "country_code":         idea.get("country_code",         "TN"),
                    "language":             idea.get("language",             "fr"),
                }, ensure_ascii=False),
            )
            queries = self._parse_json(queries_raw)

            # ── 3 sous-agents en parallèle ────────────────────
            logger.info("[market_analysis_agent] Lancement des 3 sous-agents")
            tendances, market_voc, competitor = await asyncio.gather(
                self.signal_agent.run(state, queries["signal"]),
                self.market_voc_agent.run(state, queries["market_voc"]),
                self.competitor_agent.run(state, queries["competitor"]),
            )

            # ── LLM 2 : synthèse finale ───────────────────────
            logger.info("[market_analysis_agent] LLM 2 — synthèse finale")
            synthesis_raw = await self._call_llm(
                system_prompt=self._synthesis_system_prompt(state),
                user_prompt=json.dumps({
                    "tendances":   tendances,
                    "market_voc":  market_voc,
                    "competitor":  competitor,
                }, ensure_ascii=False),
            )
            synthesis = self._parse_json(synthesis_raw)

            # ── Data quality — trace APIs vs LLM ──────────────
            data_quality = self._build_data_quality(tendances, market_voc, competitor)

            # ── Rapport final ─────────────────────────────────
            state.market_analysis = {
                "overview":        synthesis.get("overview", {}),
                "tendances":       tendances,
                "market_voc":      market_voc,
                "competitor":      competitor,
                "swot":            synthesis.get("swot", {}),
                "risques":         synthesis.get("risques", []),
                "recommandations": synthesis.get("recommandations", []),
                "data_quality":    data_quality,
                "meta": {
                    "projet":         state.name,
                    "secteur":        idea.get("sector") or idea.get("secteur") or state.sector,
                    "geo":            queries.get("signal", {}).get("country", "TN"),
                    "date_analyse":   datetime.utcnow().strftime("%Y-%m-%d"),
                    "duree_secondes": round(time.time() - start, 2),
                    "sources": [
                        "google_trends",
                        "tavily", "reddit_via_tavily",
                        "youtube", "gnews",
                        "worldbank", "serpapi_search", "serpapi_maps",
                    ],
                    "appels_llm": 2,
                    "appels_api": 10,
                },
            }

            self._log_success()
            return state

        except Exception as e:
            self._log_error(e)
            state.errors.append(f"market_analysis_agent: {str(e)}")
            raise

    # ──────────────────────────────────────────────────────────
    # PROMPTS
    # ──────────────────────────────────────────────────────────

    def _queries_system_prompt(self) -> str:
        try:
            with open("prompts/market_analysis/market_analysis_agent.txt", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return """Tu es un expert en analyse de marché.
Tu reçois une idée clarifiée (issue de IdeaClarifier) et tu génères
des queries de recherche optimisées pour 3 agents spécialisés.

Champs reçus :
- short_pitch : pitch court
- solution_description : description solution
- target_users : cible utilisateurs
- problem : problème résolu
- secteur : secteur détecté
- country_code : code pays ISO2 (TN, MA, FR, DZ...)
- language : langue cible (fr, en, ar)

- competitor.tavily : citer EXPLICITEMENT les noms des concurrents
  probables du secteur + mots négatifs obligatoires :
  ex: 'Maxxx Chips Cerealis avis négatifs problèmes clients Tunisie'
  ou 'MyStudyLife bugs problèmes utilisateurs avis négatifs'
  NE JAMAIS générer une query générique sans noms de concurrents

Génère des queries précises et adaptées au contexte réel.
Retourne UNIQUEMENT un JSON valide :

{
  "signal": {
    "trends_1":   "mot-clé principal exact tapé par les utilisateurs locaux",
    "trends_2":   "variante anglais pour comparaison internationale",
    "tiktok":     "query courte et populaire TikTok",
    "regulatory": "réglementation + secteur + pays en clair",
    "country":    "code ISO2 — ex: TN"
  },
  "market_voc": {
    "tavily":   "query insights marché + croissance",
    "reddit":   "query VOC anglais — problèmes utilisateurs + secteur",
    "youtube":  "query avis clients + secteur + pays",
    "news":     "query actualités + secteur + pays",
    "country":  "code ISO2",
    "language": "fr|en|ar"
  },
  "competitor": {
    "competitors": "query concurrents + secteur + pays Google Search",
    "maps":        "query service + ville principale Google Maps",
    "tavily":      "nom des concurrents trouvés + avis négatifs clients + problèmes + plaintes + limites + inconvénients + [pays]",
    "country":     "code ISO2"
  }
}"""


    # ──────────────────────────────────────────────────────────
    # DATA QUALITY — trace ce qui vient des APIs vs LLM
    # ──────────────────────────────────────────────────────────

    def _build_data_quality(
        self,
        tendances: dict,
        market_voc: dict,
        competitor: dict,
    ) -> dict:
        """
        Construit un rapport de qualité des données.
        Pour chaque champ clé : indique si la valeur vient
        d'une API (vérifiable) ou a été inférée par le LLM.
        """

        def _has_data(val) -> bool:
            if val is None:
                return False
            if isinstance(val, (list, dict, str)):
                return bool(val)
            return True

        # ── SignalAgent ───────────────────────────────────────
        trends_ok    = _has_data(tendances.get("rising_queries"))
        sector_ctx_ok = _has_data(tendances.get("sector_context"))
        reg_ok       = _has_data(tendances.get("regulatory_barriers"))
        direction_ok = tendances.get("direction") in ("RISING", "STABLE", "FALLING")

        # ── MarketVocAgent ────────────────────────────────────
        voc_ok     = _has_data(market_voc.get("top_voc"))
        macro_ok   = _has_data(market_voc.get("macro", {}).get("population"))
        persona_ok = _has_data(market_voc.get("personas"))
        news_ok    = _has_data(market_voc.get("news_signals"))

        # ── CompetitorAgent ───────────────────────────────────
        comp_ok    = _has_data(competitor.get("top_competitors"))
        n_comp     = len(competitor.get("top_competitors", []))
        with_weak  = sum(
            1 for c in competitor.get("top_competitors", [])
            if _has_data(c.get("weaknesses"))
        )
        with_str   = sum(
            1 for c in competitor.get("top_competitors", [])
            if _has_data(c.get("key_strengths"))
        )

        # ── Score global ──────────────────────────────────────
        checks = [trends_ok, sector_ctx_ok, reg_ok, direction_ok,
                  voc_ok, macro_ok, persona_ok, comp_ok]
        base_score = round(sum(checks) / len(checks) * 100)

        # Pénalités pour données critiques absentes
        penalties = 0
        if not news_ok:       penalties += 10
        if not trends_ok:     penalties += 10
        if with_weak == 0:    penalties += 15
        if with_str == 0:     penalties += 5

        score = max(0, base_score - penalties)

        return {
            "score_global": score,          # % de sections avec données réelles
            "interpretation": (
                "élevée" if score >= 75
                else "moyenne" if score >= 50
                else "faible"
            ),
            "sections": {
                "tendances": {
                    "direction":            {"status": "api" if direction_ok else "llm_inference", "ok": direction_ok},
                    "rising_queries":       {"status": "api" if trends_ok else "absent",          "ok": trends_ok},
                    "sector_context":       {"status": "api" if sector_ctx_ok else "absent",          "ok": sector_ctx_ok},
                    "regulatory_barriers":  {"status": "api" if reg_ok    else "absent",          "ok": reg_ok},
                    "tiktok":               {"status": "desactive", "ok": False},
                },
                "market_voc": {
                    "top_voc":    {"status": "api" if voc_ok     else "absent", "ok": voc_ok},
                    "personas":   {"status": "llm_inference" if persona_ok else "absent", "ok": persona_ok,
                                   "note": "personas inférés par LLM depuis les données VOC"},
                    "macro":      {"status": "api" if macro_ok   else "absent", "ok": macro_ok},
                    "news":       {"status": "api" if news_ok    else "absent", "ok": news_ok},
                },
                "competitor": {
                    "top_competitors":  {"status": "api" if comp_ok else "absent", "ok": comp_ok,
                                         "count": n_comp},
                    "avec_weaknesses":  {"status": "llm_inference", "ok": with_weak > 0,
                                         "count": with_weak,
                                         "note": "weaknesses extraites par LLM depuis les snippets"},
                    "avec_strengths":   {"status": "llm_inference", "ok": with_str > 0,
                                         "count": with_str,
                                         "note": "key_strengths extraites par LLM depuis les snippets"},
                },
            },
            "legende": {
                "api":           "valeur extraite directement depuis une API — vérifiable",
                "llm_inference": "valeur inférée par le LLM à partir des données brutes",
                "absent":        "donnée non disponible — API n'a pas retourné de résultat",
                "desactive":     "source désactivée dans cette version",
            },
        }
    def _synthesis_system_prompt(self, state: PipelineState) -> str:
        try:
            with open("prompts/market_analysis/synthesis_agent.txt", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"""Tu es un expert senior en stratégie pour : {state.sector}.
Tu reçois les outputs de 3 agents spécialisés.
Génère la synthèse finale. Retourne UNIQUEMENT un JSON valide :

{{
  "overview": {{
    "demande":     {{"niveau": "fort|modere|faible|inexistant", "label": "phrase courte"}},
    "probleme":    {{"niveau": "tres_discute|discute|peu|absent", "label": "phrase courte"}},
    "concurrence": {{"niveau": "vulnerable|forte|saturee|absente", "label": "phrase courte"}},
    "tendance":    {{"niveau": "hausse|stable|baisse", "label": "phrase courte"}}
  }},
  "swot": {{
    "forces":       [{{"point": "", "source": ""}}],
    "faiblesses":   [{{"point": "", "source": ""}}],
    "opportunites": [{{"point": "", "source": ""}}],
    "menaces":      [{{"point": "", "source": ""}}]
  }},
  "risques": [
    {{"type": "reglementaire|macro|concurrentiel", "description": "", "source": ""}}
  ],
  "recommandations": [
    {{"priorite": 1, "action": "recommandation actionnable", "source": ""}}
  ]
}}

Règles :
- overview : synthèse des 3 agents — pas d'invention
- swot : 2-3 points par quadrant max — chaque point référence sa source
- risques : basés sur regulatory_barriers + macro + competitor
- recommandations : exactement 3 actions concrètes et actionnables
- Retourne UNIQUEMENT le JSON"""