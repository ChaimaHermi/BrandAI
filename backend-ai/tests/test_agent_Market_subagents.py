import asyncio
import json
import sys

sys.path.insert(0, ".")

from agents.base_agent import PipelineState
from agents.market_analysis import MarketAnalysisAgent

IDEA = {
    "short_pitch": "Chips de légumes locaux healthy et vegan",
    "solution_description": (
        "Production et vente de chips à base de légumes tunisiens "
        "(betterave, carotte, patate douce), sans additifs et adaptées aux régimes healthy"
    ),
    "target_users": "Jeunes actifs, étudiants et sportifs en Tunisie",
    "problem": (
        "Les snacks disponibles sont souvent gras, industriels et peu adaptés "
        "aux personnes cherchant une alimentation saine"
    ),
    "sector": "Healthy Food",
    "country_code": "TN",
    "language": "fr",
}

def build_state_from_idea(idea: dict) -> PipelineState:
    name = idea["short_pitch"]
    sector = idea.get("sector", "Secteur non défini")
    description = (
        f"{idea['solution_description']} "
        f"Problème : {idea['problem']}"
    )
    state = PipelineState(
        idea_id="test-market-1",
        name=name,
        sector=sector,
        description=description,
        target_audience=idea["target_users"],
    )
    # Pas dans __init__ de PipelineState — utilisé par _build_report / prompts
    state.country = idea["country_code"]
    state.clarified_idea = {
        "short_pitch":          idea["short_pitch"],
        "solution_description": idea["solution_description"],
        "target_users":         idea["target_users"],
        "problem":              idea["problem"],
        "sector":               idea["sector"],
        "country_code":         idea["country_code"],
        "language":             idea["language"],
    }
    return state


async def main():
    agent = MarketAnalysisAgent()
    state = build_state_from_idea(IDEA)

    print("Lancement analyse de marché (orchestrateur + 3 sous-agents)...")
    print(f"Idée : {IDEA['short_pitch']}\n")

    state = await agent.run(state)

    report = state.market_analysis
    out_path = "market_analysis_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if state.errors:
        print("Erreurs pipeline :", state.errors)


if __name__ == "__main__":
    asyncio.run(main())

