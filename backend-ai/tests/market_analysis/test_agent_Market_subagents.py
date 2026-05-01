import asyncio
import json
import logging
import re
import sys
from pathlib import Path

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

    agent = MarketAnalysisAgent()
    state = build_state_from_idea(IDEA)

    print("\nLancement analyse de marché")
    print(f"Idée    : {IDEA['short_pitch']}")
    print(f"Secteur : {IDEA['sector']}")
    print(f"Pays    : {IDEA['country_code']}\n")

    try:
        state = await agent.run(state)
    except Exception as e:
        print("Erreur pendant l'analyse :", e)
        return

    report = state.market_analysis

    if not report:
        print("Aucun résultat généré")
        return

    assert "executive_summary" in report
    assert "market_voc" in report
    assert "competitor" in report
    assert "tendances" in report

    print("\nDEBUG CHECK")
    print("Tendances OK :", bool(report.get("tendances")))
    print("VOC OK       :", bool(report.get("market_voc")))
    print("Competitor OK:", bool(report.get("competitor")))

    filename = f"market_analysis_{safe_filename(IDEA['sector'])}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\nRESULTAT COMPLET :\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    print(f"\nRapport sauvegardé : {filename}")

    if report.get("data_quality", {}).get("warnings"):
        print("\n⚠ WARNINGS :")
        for w in report["data_quality"]["warnings"]:
            print("-", w)

    if state.errors:
        print("\n❌ Erreurs pipeline :", state.errors)


if __name__ == "__main__":
    asyncio.run(main())
