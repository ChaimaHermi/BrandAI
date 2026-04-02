import asyncio
import json

from agents.base_agent import PipelineState
from agents.branding.name_agent import NameAgent


async def test_name_agent():
    # ─────────────────────────────────────────
    # INPUT MINIMAL (ONLY clarified_idea)
    # ─────────────────────────────────────────
    state = PipelineState(
        idea_id=1
    )

    state.clarified_idea = {
        "idea_name": "Coach sport a domicile",
        "sector": "health",
        "target_users": "jeunes adultes debutants en fitness",

        "problem": (
            "Les utilisateurs manquent de motivation et ne savent pas "
            "comment structurer leurs seances de sport a domicile"
        ),

        "solution_description": (
            "Une application mobile qui propose des programmes de fitness personnalises, "
            "avec des seances guidees en video, un suivi des progres et des rappels quotidiens "
            "pour maintenir la motivation"
        ),

        "country": "Tunisie",
        "country_code": "TN",
        "language": "fr",
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
        print(json.dumps({
            "name_error": brand["name_error"],
            "name_options": []
        }, indent=2, ensure_ascii=False))
        return

    print(json.dumps(brand, indent=2, ensure_ascii=False))


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(test_name_agent())