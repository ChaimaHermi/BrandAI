import asyncio
import json

from agents.base_agent import PipelineState
from agents.branding.name_agent import NameAgent


async def test_name_agent():
    # ─────────────────────────────────────────
    # INPUT MINIMAL (ONLY clarified_idea)
    # ─────────────────────────────────────────
    state = PipelineState(
        idea_id=1,
        name="Coach sport à domicile",
        sector="health",
        description="Application de coaching fitness personnalisé à domicile",
        target_audience="jeunes adultes débutants en fitness",
    )
    state.clarified_idea = {
        "sector": "health",
        "target_users": "jeunes adultes débutants en fitness",

        "problem": (
            "Les utilisateurs manquent de motivation et ne savent pas "
            "comment structurer leurs séances de sport à domicile"
        ),

        "solution_description": (
            "Une application mobile qui propose des programmes de fitness personnalisés, "
            "avec des séances guidées en vidéo, un suivi des progrès et des rappels quotidiens "
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

    # gestion erreur propre
    if brand.get("name_error"):
        print(json.dumps({
            "name_error": brand["name_error"],
            "name_options": []
        }, indent=2, ensure_ascii=False))
        return

    # affichage normal
    print(json.dumps(brand, indent=2, ensure_ascii=False))


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(test_name_agent())