import asyncio
import json

from agents.base_agent import PipelineState
from agents.branding.name_agent import NameAgent


async def test_name_agent():
    # ─────────────────────────────────────────
    # INPUT (simule idea clarifier)
    # ─────────────────────────────────────────
    state = PipelineState(
        idea_id=1,
        name="App gestion budget étudiant",
        sector="fintech",
        description="Application mobile pour aider les étudiants à gérer leurs dépenses",
        target_audience="étudiants en Tunisie",
    )

    # simuler clarified idea (important)
    state.clarified_idea = {
        "problem": "Les étudiants ont du mal à gérer leur budget",
        "solution": "Application simple pour suivre dépenses et revenus",
        "target_users": "Étudiants universitaires",
        "value_proposition": "Gestion financière simple et rapide",
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
    print(json.dumps(result_state.brand_identity, indent=2, ensure_ascii=False))


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(test_name_agent())