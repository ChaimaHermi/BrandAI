import asyncio
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agents.base_agent import PipelineState
from agents.market_analysis.subagents.trends_risks_agent import TrendsRisksAgent


IDEA = {
    "short_pitch": "Online second-hand clothing marketplace",
    "sector": "E-commerce",
    "country": "US",
}


TREND_QUERIES = [
    "second hand fashion trends",
    "resale market growth",
    "ecommerce marketplace regulations",
    "consumer behavior thrift shopping",
    "online marketplace risks",
]


async def test_trends_agent():

    print("\nRunning TrendsRisksAgent...\n")

    state = PipelineState(idea_id="TEST-TRENDS-001")
    state.clarified_idea = IDEA

    state.market_analysis = {
        "trend_queries": TREND_QUERIES,
    }

    agent = TrendsRisksAgent()

    result = await agent.run(state)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    assert result["status"] == "success"

    print("\nTEST PASSED")


if __name__ == "__main__":
    asyncio.run(test_trends_agent())
