import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Racine backend-ai (fonctionne depuis Brand AI ou backend-ai)
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from agents.base_agent import PipelineState
from agents.market_analysis import MarketAnalysisAgent

# ══════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════

IDEA = {
    "short_pitch": "AI meeting assistant",
    "solution_description": "AI tool that records, summarizes, and extracts action items from meetings automatically",
    "target_users": "Remote teams, startups, managers",
    "problem": "People waste time in meetings and forget key decisions and tasks",
    "sector": "SaaS / Productivity",
    "country_code": "US",
    "language": "en",
}

# ══════════════════════════════════════════════════════
# BUILD STATE
# ══════════════════════════════════════════════════════


def build_state_from_idea(idea: dict) -> PipelineState:
    state = PipelineState(
        idea_id="test-market-1",
        name=idea["short_pitch"],
        sector=idea.get("sector", "Unknown"),
        description=f"{idea['solution_description']} Problem: {idea['problem']}",
        target_audience=idea["target_users"],
    )
    state.country = idea["country_code"]
    state.clarified_idea = idea
    return state


# ══════════════════════════════════════════════════════
# SAFE FILE NAME
# ══════════════════════════════════════════════════════


def safe_filename(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", text)


# ══════════════════════════════════════════════════════
# MAIN TEST
# ══════════════════════════════════════════════════════


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # Groq live uniquement si RUN_LIVE_MARKET_ANALYSIS=1 et clé présente (évite 429 en boucle de tests).
    have_key = bool(os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY_2"))
    use_live_groq = (
        os.getenv("RUN_LIVE_MARKET_ANALYSIS", "").strip() in ("1", "true", "yes")
        and have_key
    )

    agent = MarketAnalysisAgent()
    state = build_state_from_idea(IDEA)

    print("\n>> Lancement analyse de marche (phase mots-cles)")
    print(f"Idee    : {IDEA['short_pitch']}")
    print(f"Secteur : {IDEA['sector']}")
    print(f"Pays    : {IDEA['country_code']}")
    print(
        f"Mode    : {'Groq live (RUN_LIVE_MARKET_ANALYSIS=1)' if use_live_groq else 'mock LLM'}"
    )
    print()

    try:
        if use_live_groq:
            state = await agent.run(state)
        else:
            fake_json = json.dumps(
                {
                    "primary_keywords": ["meeting assistant AI"],
                    "market_keywords": ["productivity software market"],
                    "competitor_search_queries": ["best meeting assistant software"],
                    "voc_keywords": ["meeting notes frustration"],
                    "trend_keywords": ["AI workplace trends"],
                    "sector_tags": ["SaaS", "Productivity"],
                }
            )
            with patch(
                "agents.market_analysis.orchestrator.keyword_extractor.KeywordExtractorAgent._call_llm",
                new_callable=AsyncMock,
                return_value=fake_json,
            ):
                state = await agent.run(state)
    except Exception as e:
        print("Erreur pendant l'analyse :", e)
        return

    report = state.market_analysis

    if not report:
        print("Aucun resultat genere")
        return

    assert "keyword_bundle" in report
    assert "keyword_routing" in report

    print("\n-- Phase mots-cles")
    print("keyword_bundle OK :", bool(report.get("keyword_bundle")))
    rb = report.get("keyword_routing") or {}
    print("  -> agent_market      :", rb.get("agent_market"))
    print("  -> agent_competitors :", rb.get("agent_competitors"))

    filename = f"market_analysis_{safe_filename(IDEA['sector'])}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\nRESULTAT (phase mots-cles) :\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    print(f"\nOK Rapport sauvegarde : {filename}")

    if report.get("data_quality", {}).get("warnings"):
        print("\nWARNINGS :")
        for w in report["data_quality"]["warnings"]:
            print("-", w)

    if state.errors:
        print("\nErreurs pipeline :", state.errors)


if __name__ == "__main__":
    asyncio.run(main())
