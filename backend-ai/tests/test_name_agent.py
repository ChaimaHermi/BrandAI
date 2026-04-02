import asyncio
import json

from agents.base_agent import PipelineState
from agents.branding.name_agent import NameAgent


async def test_name_agent():
    # ─────────────────────────────────────────
    # INPUT (simule idea clarifier)
    # ─────────────────────────────────────────
    state = PipelineState(
        idea_id=3,
        name="App fitness à domicile",
        sector="health",
        description="Application mobile pour faire du sport chez soi avec coaching personnalisé",
        target_audience="jeunes adultes",
    )

    state.clarified_idea = {
        "problem": "Manque de motivation pour faire du sport",
        "solution": "Coaching fitness personnalisé à domicile",
        "target_users": "Débutants et amateurs",
        "value_proposition": "Fitness simple sans salle de sport",
    }

    # ─────────────────────────────────────────
    # RUN AGENT
    # ─────────────────────────────────────────
    agent = NameAgent()

    result_state = await agent.run(state)

    # ─────────────────────────────────────────
    # OUTPUT
    # ─────────────────────────────────────────
    print("\n===== NAME AGENT RESULT =====\n")
    brand = result_state.brand_identity or {}
    if brand.get("name_error"):
        print(json.dumps({"name_error": brand["name_error"], "name_options": []}, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(brand, indent=2, ensure_ascii=False))


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(test_name_agent())