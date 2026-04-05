"""Tests extraction mots-clés — exemples d'idée ici uniquement."""
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from agents.base_agent import PipelineState
from agents.market_analysis import MarketAnalysisAgent
from agents.market_analysis.orchestrator.keyword_extractor import KeywordBundle, extract_keywords
from tools.market_analysis.keyword_json import parse_keyword_json_response

# Idée de test (comme un clarifier output minimal)
SAMPLE_IDEA = {
    "short_pitch": "AI Meeting Assistant",
    "solution_description": "Records and summarizes meetings",
    "target_users": "Teams",
    "problem": "Lost notes",
    "sector": "SaaS / Productivity",
    "country_code": "US",
    "language": "en",
}


def _print_json_block(title: str, data: dict) -> None:
    """Affiche un bloc JSON dans le terminal (stderr + flush = ordre lisible avec unittest)."""
    lines = [
        "\n" + "=" * 60,
        title,
        "=" * 60,
        json.dumps(data, indent=2, ensure_ascii=False),
    ]
    print(*lines, sep="\n", file=sys.stderr, flush=True)


class TestKeywordExtractor(unittest.TestCase):
    def test_parse_json_tool(self):
        raw = '{"primary_keywords": ["a"], "market_keywords": [], "competitor_search_queries": [], "voc_keywords": [], "trend_keywords": [], "sector_tags": []}'
        self.assertEqual(parse_keyword_json_response(raw)["primary_keywords"], ["a"])

    def test_keyword_bundle_helpers(self):
        b = KeywordBundle(primary_keywords=["x"], competitor_search_queries=["q"])
        self.assertEqual(b.for_agent_market(), ["x"])
        self.assertEqual(b.for_agent_competitors(), ["q"])


class TestKeywordExtractorAsync(unittest.IsolatedAsyncioTestCase):
    async def test_extract_keywords_mocked(self):
        fake = json.dumps(
            {
                "primary_keywords": ["a"],
                "market_keywords": ["m"],
                "competitor_search_queries": ["q"],
                "voc_keywords": ["v"],
                "trend_keywords": ["t"],
                "sector_tags": ["SaaS"],
            }
        )
        with patch(
            "agents.market_analysis.orchestrator.keyword_extractor.KeywordExtractorAgent._call_llm",
            new_callable=AsyncMock,
            return_value=fake,
        ):
            b = await extract_keywords(SAMPLE_IDEA)
            self.assertEqual(b.primary_keywords, ["a"])
            _print_json_block("Resultat: KeywordBundle (LLM mock)", b.to_dict())

    async def test_market_agent_puts_bundle_in_state(self):
        fake = json.dumps(
            {
                "primary_keywords": ["kw"],
                "market_keywords": [],
                "competitor_search_queries": [],
                "voc_keywords": [],
                "trend_keywords": [],
                "sector_tags": [],
            }
        )
        with patch(
            "agents.market_analysis.orchestrator.keyword_extractor.KeywordExtractorAgent._call_llm",
            new_callable=AsyncMock,
            return_value=fake,
        ):
            st = PipelineState(idea_id=1)
            st.clarified_idea = SAMPLE_IDEA
            out = await MarketAnalysisAgent().run(st)
            self.assertEqual(out.market_analysis["keyword_bundle"]["primary_keywords"], ["kw"])
            _print_json_block(
                "Resultat: state.market_analysis (LLM mock)",
                out.market_analysis,
            )


class TestGroqLiveOptional(unittest.IsolatedAsyncioTestCase):
    async def test_live_groq(self):
        if os.getenv("RUN_GROQ_INTEGRATION", "").strip() not in ("1", "true", "yes"):
            self.skipTest("RUN_GROQ_INTEGRATION=1")
        if not (os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY_2")):
            self.skipTest("GROQ_API_KEY")
        b = await extract_keywords(SAMPLE_IDEA)
        self.assertGreaterEqual(len(b.primary_keywords), 1)
        _print_json_block("Resultat: KeywordBundle (Groq live)", b.to_dict())


if __name__ == "__main__":
    # buffer=False : affiche les print (JSON) au fil des tests, pas a la fin
    unittest.main(verbosity=2, buffer=False)
