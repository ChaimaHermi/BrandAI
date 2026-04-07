import asyncio
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agents.base_agent import PipelineState
from agents.market_analysis.subagents.market_sizing_agent import MarketSizingAgent


IDEA = {
    "short_pitch": "Online second-hand clothing marketplace",
    "solution_description": "Platform where users can buy and sell second-hand clothing easily with integrated payments and shipping",
    "target_users": "Consumers interested in affordable and sustainable fashion",
    "problem": "Users struggle to resell clothes easily and find trusted resale platforms",
    "sector": "E-commerce / Marketplace",
    "country": "United States",
    "country_code": "US",
}


MARKET_KEYWORDS = [
    "second hand clothing market size",
    "resale fashion market size",
    "used clothing market growth rate",
    "online resale clothing statistics",
    "fashion resale industry revenue"
]


async def test_market_sizing_agent():

    print("\n" + "="*60)
    print("TEST — MarketSizingAgent")
    print("="*60)

    state = PipelineState(idea_id="TEST-001")
    state.clarified_idea = IDEA

    state.market_analysis = {
        "market_keywords": MARKET_KEYWORDS
    }

    agent = MarketSizingAgent()

    print("\nRunning agent...\n")
    print("Keywords used:", MARKET_KEYWORDS, "\n")

    try:
        result = await agent.run(state)

        print("="*60)
        print("RESULT")
        print("="*60)

        print(json.dumps(result, indent=2, ensure_ascii=False))

        # validations avancées
        assert result["status"] == "success"

        data = result.get("data", {})
        assert isinstance(data, dict)

        assert "market_size" in data
        assert "CAGR" in data

        print("\nTEST PASSED")

    except Exception as e:
        print("\nTEST FAILED")
        print(str(e))


if __name__ == "__main__":
    asyncio.run(test_market_sizing_agent())