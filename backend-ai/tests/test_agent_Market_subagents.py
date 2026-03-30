import asyncio
import json
import sys
import re

sys.path.insert(0, ".")

from agents.base_agent import PipelineState
from agents.market_analysis import MarketAnalysisAgent

# ══════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════

IDEA = {
    "short_pitch": "Healthy meal delivery platform",
    "solution_description": "Platform that delivers healthy meals prepared by local chefs with personalized nutrition plans",
    "target_users": "Busy professionals, fitness enthusiasts, and families",
    "problem": "People lack time to cook healthy meals and rely on unhealthy fast food",
    "sector": "FoodTech / Delivery",
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
    agent = MarketAnalysisAgent()
    state = build_state_from_idea(IDEA)

    print("\n🚀 Lancement analyse de marché")
    print(f"Idée    : {IDEA['short_pitch']}")
    print(f"Secteur : {IDEA['sector']}")
    print(f"Pays    : {IDEA['country_code']}\n")

    try:
        state = await agent.run(state)
    except Exception as e:
        print("❌ Erreur pendant l'analyse :", e)
        return

    report = state.market_analysis

    # ── VALIDATION OUTPUT ─────────────────────
    if not report:
        print("❌ Aucun résultat généré")
        return

    # Debug rapide
    print("\n🔍 DEBUG CHECK")
    print("Tendances OK :", bool(report.get("tendances")))
    print("VOC OK       :", bool(report.get("market_voc")))
    print("Competitor OK:", bool(report.get("competitor")))

    # ── SAVE ──────────────────────────────────
    filename = f"market_analysis_{safe_filename(IDEA['sector'])}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n📊 RESULTAT COMPLET :\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    print(f"\n✅ Rapport sauvegardé : {filename}")

    # ── WARNINGS ──────────────────────────────
    if report.get("data_quality", {}).get("warnings"):
        print("\n⚠ WARNINGS :")
        for w in report["data_quality"]["warnings"]:
            print("-", w)

    if state.errors:
        print("\n❌ Erreurs pipeline :", state.errors)


# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    asyncio.run(main())