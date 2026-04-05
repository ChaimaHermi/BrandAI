import asyncio
import json
import sys
from pathlib import Path

# Fix path
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agents.base_agent import PipelineState
from agents.market_analysis.subagents.competitor_agent import CompetitorAgent


# ─────────────────────────────────────────
# IDEA TEST
# ─────────────────────────────────────────

IDEA = {
    "short_pitch": "Online second-hand clothing marketplace",
    "solution_description": "Platform where users can buy and sell second-hand clothing",
    "target_users": "Consumers interested in affordable fashion",
    "problem": "Hard to resell clothes easily",
    "sector": "E-commerce / Marketplace",
    "country": "United States",
    "country_code": "US",
}

# ─────────────────────────────────────────
# QUERIES (IMPORTANT)
# ─────────────────────────────────────────

COMPETITOR_QUERIES = [
    "best second hand clothing apps",
    "Vinted vs Depop",
    "top resale fashion platforms",
    "second hand marketplace competitors"
]

# ─────────────────────────────────────────
# TEST FUNCTION
# ─────────────────────────────────────────

async def test_competitor_agent():

    print("\nRunning CompetitorAgent...\n")

    state = PipelineState(idea_id="TEST-COMP-001")
    state.clarified_idea = IDEA

    state.market_analysis = {
        "competitor_queries": COMPETITOR_QUERIES
    }

    agent = CompetitorAgent()

    try:
        result = await agent.run(state)

        print(json.dumps(result, indent=2, ensure_ascii=False))

        # ─────────────────────────
        # VALIDATIONS
        # ─────────────────────────

        assert result["status"] == "success"

        data = result.get("data", {})
        assert "competitors" in data

        competitors = data["competitors"]
        assert isinstance(competitors, list)
        assert len(competitors) > 0

        # check structure
        first = competitors[0]

        assert "name" in first
        assert "type" in first
        assert first["type"] in ["direct", "indirect"]

        print("\nTEST PASSED ✅")

    except Exception as e:
        print("\nTEST FAILED ❌")
        print(str(e))


# ─────────────────────────────────────────
# RUN
# ─────────────────────────────────────────

if __name__ == "__main__":
    asyncio.run(test_competitor_agent())