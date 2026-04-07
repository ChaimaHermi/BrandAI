import asyncio
import json
import sys
from pathlib import Path

# ─────────────────────────────────────────
# SETUP PATH
# ─────────────────────────────────────────
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ─────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────
from agents.base_agent import PipelineState
from agents.market_analysis.subagents.voc_agent import VOCAgent


# ─────────────────────────────────────────
# IDEA TEST (vide dressing)
# ─────────────────────────────────────────
IDEA = {
    "short_pitch": "Online second-hand clothing marketplace",
    "solution_description": "Platform where users can sell and buy second-hand clothes easily",
    "target_users": "Consumers interested in affordable fashion",
    "problem": "Users struggle to sell clothes and find buyers",
    "sector": "E-commerce / Marketplace",
    "country": "United States",
    "country_code": "US"
}


# ─────────────────────────────────────────
# VOC QUERIES (IMPORTANT)
# ─────────────────────────────────────────
VOC_QUERIES = [
     "slow seller response times",
    "poor item quality descriptions",
    "payment security concerns",
    "high shipping fees",
    "limited size options",
    "fake product listings"
]


# ─────────────────────────────────────────
# TEST FUNCTION
# ─────────────────────────────────────────
async def test_voc_agent():

    print("\nRunning VOCAgent...\n")

    # Init state
    state = PipelineState(idea_id="TEST-VOC-001")
    state.clarified_idea = IDEA

    # 🔥 Inject queries (CRITICAL)
    state.market_analysis = {
        "voc_queries": VOC_QUERIES
    }

    # Init agent
    agent = VOCAgent()

    try:
        result = await agent.run(state)

        print("\nRESULT:\n")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # ─────────────────────
        # BASIC VALIDATIONS
        # ─────────────────────
        assert result["status"] == "success"
        assert "data" in result

        data = result["data"]

        assert "pain_points" in data
        assert "desired_features" in data
        assert "user_quotes" in data

        print("\nTEST PASSED ✅")

    except Exception as e:
        print("\nTEST FAILED ❌")
        print(str(e))


# ─────────────────────────────────────────
# RUN
# ─────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(test_voc_agent())