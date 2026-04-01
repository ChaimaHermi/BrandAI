# ══════════════════════════════════════════════════════════════
# agents/market_analysis/market_analysis_agent.py  [FIXED]
# ══════════════════════════════════════════════════════════════

import json, logging, time
from datetime import datetime
from pathlib import Path

from agents.base_agent import BaseAgent, PipelineState
from agents.market_analysis.subagents.signal_agent import SignalAgent
from agents.market_analysis.subagents.market_voc_agent import MarketVocAgent
from agents.market_analysis.subagents.competitor_agent import CompetitorAgent
from config.market_analysis_config import LLM_CONFIG, LLM_LIMITS
from schemas.market_analysis_schemas import MarketReport

logger = logging.getLogger("brandai.market_analysis_agent")
BASE_DIR = Path(__file__).resolve().parents[2]
PROMPTS_DIR = BASE_DIR / "prompts" / "market_analysis"


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
            idea = state.clarified_idea or {}

            # ── Helper troncature ──────────────────────────────
            def _trunc(val, n=120):
                """Tronque un string à n chars, retourne '' si None."""
                return str(val or "")[:n]

            # ── LLM 1 : génère toutes les queries ─────────────
            # FIX : chaque champ tronqué pour éviter 413 Groq
            logger.info("[market_analysis_agent] LLM 1 — génération queries")
            queries_raw = await self._call_llm(
                system_prompt=self._queries_system_prompt(),
                user_prompt=json.dumps({
                    "short_pitch":          _trunc(idea.get("short_pitch")          or state.name,            80),
                    "solution_description": _trunc(idea.get("solution_description") or state.description,    120),
                    "target_users":         _trunc(idea.get("target_users")         or state.target_audience, 80),
                    "problem":              _trunc(idea.get("problem")              or state.description,     80),
                    "secteur":              _trunc(idea.get("sector")               or state.sector,          40),
                    "country_code":         idea.get("country_code", "TN"),
                    "language":             idea.get("language",     "fr"),
                }, ensure_ascii=False),
            )
            queries = self._safe_parse_json(
                raw=queries_raw,
                fallback=self._fallback_queries(state),
                stage="queries_generation",
            )

            # ── 3 sous-agents en séquentiel (quota-safe) ──────
            logger.info("[market_analysis_agent] Exécution sous-agents (séquentiel)")
            tendances  = await self.signal_agent.run(state, queries["signal"])
            market_voc = await self.market_voc_agent.run(state, queries["market_voc"])
            competitor = await self.competitor_agent.run(state, queries["competitor"])

            # ── LLM 2 : synthèse finale ───────────────────────
            logger.info("[market_analysis_agent] LLM 2 — synthèse finale")
            synthesis_payload = json.dumps({
                "tendances":  tendances,
                "market_voc": market_voc,
                "competitor": competitor,
            }, ensure_ascii=False)
            if len(synthesis_payload) > LLM_LIMITS["max_payload_chars"]:
                synthesis_payload = synthesis_payload[: LLM_LIMITS["max_payload_chars"]]

            synthesis_raw = await self._call_llm(
                system_prompt=self._synthesis_system_prompt(state),
                user_prompt=synthesis_payload,
            )
            synthesis = self._safe_parse_json(
                raw=synthesis_raw,
                fallback={},
                stage="final_synthesis",
            )
            synthesis = self._normalize_synthesis_payload(synthesis)

            # ── Data quality ───────────────────────────────────
            data_quality = self._build_data_quality(tendances, market_voc, competitor)

            # ── Rapport final ──────────────────────────────────
            final_output = {
                "executive_summary": synthesis.get("executive_summary", ""),
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
                        "tavily", "tavily_weakness", "tavily_compare",
                        "reddit_via_tavily",
                        "youtube", "gnews",
                        "worldbank", "serpapi_search", "serpapi_maps",
                    ],
                    "appels_llm": 2,
                    "appels_api": 13,
                },
            }
            validated = MarketReport(**final_output)
            state.market_analysis = validated.dict()

            self._log_success()
            return state

        except Exception as e:
            self._log_error(e)
            state.errors.append(f"market_analysis_agent: {str(e)}")
            raise

    # ──────────────────────────────────────────────────────────
    # PROMPT LLM 1 — génération des queries
    # ──────────────────────────────────────────────────────────

    def _queries_system_prompt(self) -> str:
        try:
            with open(PROMPTS_DIR / "market_analysis_agent.txt", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return """Tu es un expert en analyse de marché.
Tu reçois une idée clarifiée et tu génères des queries PRÉCISES pour 3 agents.

RÈGLE CRITIQUE pour competitor.tavily :
→ Nommer 2-3 concurrents probables du secteur + cibler avis négatifs
→ Format : "[Concurrent1] [Concurrent2] [problème] avis négatifs bugs [pays]"
→ Ex EdTech TN : "MyStudyLife EduPage ADE Campus emploi du temps bugs problèmes Tunisie"
→ Ex FoodTech TN : "Jumia Food Glovo livraison repas lent annulé problèmes Tunisie"
→ JAMAIS une query générique sans noms de concurrents

RÈGLE pour market_voc.news : 2-3 mots anglais, secteur SANS pays.

Retourne UNIQUEMENT un JSON valide :
{
  "signal": {
    "trends_1":   "mot-clé court max 5 mots",
    "trends_2":   "variante anglais court",
    "tiktok":     "query courte TikTok",
    "regulatory": "réglementation secteur pays en clair",
    "country":    "code ISO2"
  },
  "market_voc": {
    "tavily":   "problème secteur pays insights croissance",
    "reddit":   "solution type app problème complaints site:reddit.com",
    "youtube":  "secteur problème pays avis test",
    "news":     "2-3 mots secteur en anglais sans pays",
    "country":  "code ISO2",
    "language": "fr|en|ar"
  },
  "competitor": {
    "competitors": "solution concrète + problème + pays",
    "maps":        "service principal ville principale",
    "tavily":      "Concurrent1 Concurrent2 problèmes avis négatifs bugs pays",
    "country":     "code ISO2"
  }
}"""

    # ──────────────────────────────────────────────────────────
    # PROMPT LLM 2 — synthèse finale
    # ──────────────────────────────────────────────────────────

    def _synthesis_system_prompt(self, state: PipelineState) -> str:
        try:
            with open(PROMPTS_DIR / "synthesis_agent.txt", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"""Tu es un expert senior en stratégie pour : {state.sector}.
Tu reçois les outputs de 3 agents (tendances, market_voc, competitor).
Retourne UNIQUEMENT un JSON valide :

{{
  "executive_summary": "3 phrases factuelles : marché. problème+opportunité. condition prioritaire.",
  "overview": {{
    "demande":     {{"niveau": "fort|modere|faible|inexistant", "label": "phrase courte"}},
    "probleme":    {{"niveau": "tres_discute|discute|peu|absent",  "label": "phrase courte"}},
    "concurrence": {{"niveau": "vulnerable|forte|saturee|absente", "label": "phrase courte"}},
    "tendance":    {{"niveau": "hausse|stable|baisse", "label": "phrase courte"}}
  }},
  "swot": {{
    "forces":       [{{"point": "...", "source": "champ.exact"}}],
    "faiblesses":   [{{"point": "...", "source": "champ.exact"}}],
    "opportunites": [{{"point": "...", "source": "champ.exact"}}],
    "menaces":      [{{"point": "...", "source": "champ.exact"}}]
  }},
  "risques": [
    {{
      "type": "reglementaire|macro|concurrentiel",
      "cause": "...",
      "impact": "...",
      "probabilite": "elevee|moyenne|faible",
      "mitigation": "action concrète"
    }}
  ],
  "recommandations": [
    {{
      "action": "verbe + quoi + comment + critère mesurable",
      "horizon": "court_terme|moyen_terme|long_terme",
      "impact_attendu": "résultat concret"
    }}
  ]
}}

Règles : ton neutre, jamais de GO/NO-GO, 3 risques, 3 recommandations une par horizon."""

    # ──────────────────────────────────────────────────────────
    # DATA QUALITY
    # ──────────────────────────────────────────────────────────

    def _build_data_quality(self, tendances, market_voc, competitor) -> dict:

        def _has(val) -> bool:
            if val is None: return False
            if isinstance(val, (list, dict, str)): return bool(val)
            return True

        direction_ok  = tendances.get("direction") in ("RISING", "STABLE", "FALLING")
        trends_ok     = _has(tendances.get("rising_queries"))
        sector_ctx_ok = _has(tendances.get("sector_context"))
        reg_ok        = _has(tendances.get("regulatory_barriers"))

        voc_ok     = _has(market_voc.get("top_voc"))
        macro_ok   = _has(market_voc.get("macro", {}).get("population"))
        persona_ok = _has(market_voc.get("personas"))
        news_ok    = _has(market_voc.get("news_signals"))

        comp_ok   = _has(competitor.get("top_competitors"))
        n_comp    = len(competitor.get("top_competitors", []))
        with_weak = sum(
            1 for c in competitor.get("top_competitors", [])
            if _has(c.get("weaknesses"))
        )
        with_str  = sum(
            1 for c in competitor.get("top_competitors", [])
            if _has(c.get("key_strengths"))
        )

        checks = [
            direction_ok, trends_ok, sector_ctx_ok, reg_ok,
            voc_ok, macro_ok, persona_ok, comp_ok, news_ok,
        ]
        base_score = round(sum(checks) / len(checks) * 100)

        penalties = 0
        if not trends_ok:  penalties += 10
        if with_weak == 0: penalties += 15
        if with_str  == 0: penalties += 5

        score = max(0, base_score - penalties)

        warnings = []
        if with_weak == 0:
            warnings.append(
                "⚠ Aucune faiblesse concurrente extraite — "
                "tavily_weakness trop générique ou concurrents non documentés en ligne"
            )
        if not trends_ok:
            warnings.append(
                "⚠ rising_queries vide — "
                "Google Trends n'a pas retourné de requêtes montantes"
            )
        if not news_ok:
            warnings.append("⚠ news_signals vide — GNews sans résultats pour cette période")

        return {
            "score_global":   score,
            "interpretation": (
                "élevée" if score >= 75
                else "moyenne" if score >= 50
                else "faible"
            ),
            "warnings": warnings,
            "sections": {
                "tendances": {
                    "direction":           {"status": "api" if direction_ok   else "llm_inference", "ok": direction_ok},
                    "rising_queries":      {"status": "api" if trends_ok      else "absent",        "ok": trends_ok},
                    "sector_context":      {"status": "api" if sector_ctx_ok  else "absent",        "ok": sector_ctx_ok},
                    "regulatory_barriers": {"status": "api" if reg_ok         else "absent",        "ok": reg_ok},
                    "tiktok":              {"status": "desactive", "ok": False},
                },
                "market_voc": {
                    "top_voc":  {"status": "api" if voc_ok    else "absent", "ok": voc_ok},
                    "personas": {
                        "status": "llm_inference" if persona_ok else "absent",
                        "ok":     persona_ok,
                        "note":   "inférés par LLM depuis les données VOC",
                    },
                    "macro":    {"status": "api" if macro_ok  else "absent", "ok": macro_ok},
                    "news":     {"status": "api" if news_ok   else "absent", "ok": news_ok},
                },
                "competitor": {
                    "top_competitors": {
                        "status": "api" if comp_ok else "absent",
                        "ok":     comp_ok,
                        "count":  n_comp,
                    },
                    "avec_weaknesses": {
                        "status": "llm_inference",
                        "ok":     with_weak > 0,
                        "count":  with_weak,
                        "note":   "extraites depuis snippets Tavily",
                    },
                    "avec_strengths": {
                        "status": "llm_inference",
                        "ok":     with_str > 0,
                        "count":  with_str,
                        "note":   "extraites depuis snippets Tavily",
                    },
                },
            },
            "legende": {
                "api":           "valeur extraite directement depuis une API — vérifiable",
                "llm_inference": "valeur inférée par le LLM à partir des données brutes",
                "absent":        "donnée non disponible — API n'a pas retourné de résultat",
                "desactive":     "source désactivée dans cette version",
            },
        }

    def _normalize_synthesis_payload(self, synthesis: dict) -> dict:
        if not isinstance(synthesis, dict):
            return {}

        ov = synthesis.get("overview")
        if isinstance(ov, dict):
            for key in ("demande", "probleme", "concurrence", "tendance"):
                val = ov.get(key)
                if isinstance(val, str):
                    ov[key] = {"niveau": "modere", "label": val}
                elif isinstance(val, dict):
                    ov[key] = {
                        "niveau": val.get("niveau") or "modere",
                        "label": val.get("label") or val.get("description") or "",
                    }
                else:
                    ov[key] = {"niveau": "modere", "label": ""}
            synthesis["overview"] = ov

        swot = synthesis.get("swot")
        if isinstance(swot, dict):
            for bucket in ("forces", "faiblesses", "opportunites", "menaces"):
                items = swot.get(bucket) or []
                norm_items = []
                if isinstance(items, list):
                    for it in items[:3]:
                        if isinstance(it, str):
                            norm_items.append({"point": it, "source": "inference"})
                        elif isinstance(it, dict):
                            point = it.get("point") or it.get("description") or ""
                            source = it.get("source") or "inference"
                            norm_items.append({"point": point, "source": source})
                swot[bucket] = norm_items
            synthesis["swot"] = swot

        recs = synthesis.get("recommandations")
        if isinstance(recs, list):
            norm_recs = []
            horizon_default = ["court", "moyen", "long"]
            for i, r in enumerate(recs[:3]):
                if isinstance(r, str):
                    norm_recs.append({
                        "action": r,
                        "horizon": horizon_default[i] if i < len(horizon_default) else None,
                        "impact_attendu": "",
                    })
                elif isinstance(r, dict):
                    norm_recs.append({
                        "action": r.get("action") or r.get("description") or "",
                        "horizon": r.get("horizon"),
                        "impact_attendu": r.get("impact_attendu") or "",
                        "priorite": r.get("priorite"),
                        "source": r.get("source"),
                    })
            synthesis["recommandations"] = norm_recs

        return synthesis

    def _safe_parse_json(self, raw: str, fallback: dict, stage: str) -> dict:
        try:
            return self._parse_json(raw or "")
        except Exception as e:
            logger.warning(
                "[market_analysis_agent] fallback JSON used at stage=%s | reason=%s",
                stage,
                str(e)[:180],
            )
            return fallback

    def _fallback_queries(self, state: PipelineState) -> dict:
        secteur = (state.sector or "secteur").strip()
        country = "TN"
        return {
            "signal": {
                "trends_1": f"{secteur} Tunisie",
                "trends_2": f"{secteur} app",
                "tiktok": f"{secteur} avis",
                "regulatory": f"reglementation {secteur} Tunisie",
                "country": country,
            },
            "market_voc": {
                "tavily": f"problemes {secteur} Tunisie",
                "reddit": f"{secteur} complaints site:reddit.com",
                "youtube": f"{secteur} Tunisie avis",
                "news": f"{secteur} market",
                "country": country,
                "language": "fr",
            },
            "competitor": {
                "competitors": f"solutions {secteur} Tunisie",
                "maps": f"{secteur} tunis",
                "tavily": f"concurrents {secteur} avis negatifs Tunisie",
                "country": country,
            },
        }