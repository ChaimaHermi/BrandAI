# ══════════════════════════════════════════════════════════════
# agents/market_analysis/subagents/competitor_agent.py  [v2]
# Fix principal : construction correcte des queries Tavily weakness
# ══════════════════════════════════════════════════════════════

import asyncio
import json

from agents.base_agent import BaseAgent, PipelineState
from config.market_analysis_config import LLM_CONFIG
from schemas.market_analysis_schemas import CompetitorSection
from tools.market_analysis.subagents_tools.competitor_tools import (
    fetch_serp_competitors,
    fetch_serp_maps,
    fetch_tavily_competitor_insights,
)


class CompetitorAgent(BaseAgent):

    # Mots négatifs pour post-processing si LLM rate les weaknesses
    _NEGATIVE_KW = [
        "slow", "crash", "bug", "buggy", "broken", "issue", "problem", "bad",
        "missing", "lacking", "limited", "expensive", "complicated", "confusing",
        "lent", "bugué", "problème", "erreur", "manque", "instable", "limité",
        "cher", "compliqué", "difficile", "mauvais", "absent", "dépassé",
        "horrible", "worst", "useless", "annoying", "ugly", "outdated",
    ]

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
            "competitors": "application emploi du temps étudiant université Tunisie",
            "maps":        "application éducative planning Tunis",
            "tavily":      "MyStudyLife EduPage bugs problèmes Tunisie",
            "country":     "TN"
        }
        """
        self._log_start(state)
        country    = queries.get("country", "TN")
        base_query = queries.get("tavily", "")

        try:
            # ── Construire 2 queries Tavily complémentaires ──────────────
            #
            # weakness_q : cibler Reddit + mots négatifs explicites
            #   → On ne retire PAS "site:reddit.com" car il n'est pas forcément là
            #   → On AJOUTE site:reddit.com + mots négatifs
            weakness_q = (
                f"site:reddit.com {base_query} "
                "bugs problems slow crash bad review worst complaints"
            )

            # compare_q : comparaisons utilisateurs = meilleure source de faiblesses
            compare_q = f"{base_query} vs alternative better switch problems"

            # ── 5 appels en parallèle ────────────────────────────────────
            (
                serp_search,
                serp_maps,
                tavily_main,
                tavily_weakness,
                tavily_compare,
            ) = await asyncio.gather(
                fetch_serp_competitors(queries["competitors"], country),
                fetch_serp_maps(queries.get("maps", ""), country),
                fetch_tavily_competitor_insights(base_query),
                fetch_tavily_competitor_insights(weakness_q),
                fetch_tavily_competitor_insights(compare_q),
            )

            raw_data = {
                "serp_search":     serp_search,
                "serp_maps":       serp_maps,
                "tavily_main":     tavily_main,      # positionnement général
                "tavily_weakness": tavily_weakness,  # plaintes Reddit
                "tavily_compare":  tavily_compare,   # comparaisons utilisateurs
            }

            llm_response = await self._call_llm(
                system_prompt=self._load_prompt("competitor_agent.txt", state),
                user_prompt=json.dumps(raw_data, ensure_ascii=False, default=str),
            )

            data = self._parse_json(llm_response)

            # ── Post-processing : récupérer weaknesses si LLM a raté ─────
            data = self._fill_missing_weaknesses(data, raw_data)

            output = CompetitorSection(**data)
            self._log_success(output)
            return output.dict()

        except Exception as e:
            self._log_error(e)
            raise

    # ──────────────────────────────────────────────────────────────────
    # Post-processing : scan de mots négatifs dans les snippets bruts
    # Déclenché UNIQUEMENT si weaknesses=[] après le LLM
    # ──────────────────────────────────────────────────────────────────

    def _fill_missing_weaknesses(self, data: dict, raw_data: dict) -> dict:
        # Collecter tous les snippets de toutes les sources Tavily
        all_snippets: list[tuple[str, str]] = []  # (title, snippet)
        for src in ("tavily_weakness", "tavily_compare", "tavily_main"):
            for r in raw_data.get(src, {}).get("results", []):
                title   = r.get("title", "").lower()
                snippet = r.get("snippet", "").lower()
                all_snippets.append((title, snippet))

        for competitor in data.get("top_competitors", []):
            if competitor.get("weaknesses"):
                continue  # déjà rempli par le LLM — ne pas toucher

            comp_name  = competitor.get("nom", "").lower()
            # Mots clés du nom (filtre les mots trop courts comme "app")
            name_words = [w for w in comp_name.split() if len(w) > 3]

            found = []
            for title, snippet in all_snippets:
                full_text = title + " " + snippet

                # Vérifier si le concurrent est mentionné dans ce snippet
                name_present = any(w in full_text for w in name_words) if name_words else True

                if not name_present:
                    continue

                # Chercher des mots négatifs
                for kw in self._NEGATIVE_KW:
                    if kw not in full_text:
                        continue
                    idx     = full_text.find(kw)
                    extract = full_text[max(0, idx - 50): idx + 100].strip()
                    extract = extract[:130]
                    if extract and extract not in found:
                        found.append(extract)
                    if len(found) >= 2:
                        break
                if len(found) >= 2:
                    break

            if found:
                competitor["weaknesses"]         = found
                competitor["faiblesse_principale"] = found[0]

        return data

    # ──────────────────────────────────────────────────────────────────
    # CHARGEMENT DU PROMPT
    # ──────────────────────────────────────────────────────────────────

    def _load_prompt(self, filename: str, state: PipelineState) -> str:
        try:
            with open(f"prompts/market_analysis/{filename}", encoding="utf-8") as f:
                content = f.read()
            # Vérification minimale de validité
            if "faiblesse_principale" not in content:
                raise ValueError("Prompt incomplet")
            return content
        except (FileNotFoundError, ValueError):
            # Fallback inline minimal (le fichier txt est la vraie source)
            return f"""Tu es un expert en intelligence concurrentielle pour : {state.sector}.
Tu reçois serp_search, serp_maps, tavily_main, tavily_weakness, tavily_compare.
Extrais les concurrents depuis serp_search et leurs faiblesses depuis tavily_weakness/tavily_compare.
Retourne UNIQUEMENT un JSON :
{{
  "top_competitors": [{{
    "nom": "...", "type": "digital|local|regional|international",
    "faiblesse_principale": "extrait snippet ou 'Non documenté dans les sources disponibles'",
    "weaknesses": [], "key_strengths": [], "positioning": "..."
  }}],
  "opportunite_niveau": "fenetre_ouverte|partielle|saturee",
  "opportunite_summary": "..."
}}"""