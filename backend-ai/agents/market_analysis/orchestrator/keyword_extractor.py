"""
Orchestrateur mots-clés : LLM (config + BaseAgent) → KeywordBundle pour les sous-agents.
Prompts : prompts/market_analysis/. Parsing listes : tools/market_analysis/keyword_json.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from agents.base_agent import BaseAgent, PipelineState
from config.market_analysis_config import LLM_CONFIG
from prompts.market_analysis.keyword_extractor_prompt import (
    KEYWORD_EXTRACTOR_SYSTEM_PROMPT,
    build_keyword_extraction_user_prompt,
)
from tools.market_analysis.keyword_json import norm_str_list, parse_keyword_json_response


@dataclass
class KeywordBundle:
    primary_keywords: list[str] = field(default_factory=list)
    market_keywords: list[str] = field(default_factory=list)
    competitor_search_queries: list[str] = field(default_factory=list)
    voc_keywords: list[str] = field(default_factory=list)
    trend_keywords: list[str] = field(default_factory=list)
    sector_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def for_agent_market(self) -> list[str]:
        return self.primary_keywords

    def for_agent_competitors(self) -> list[str]:
        return self.competitor_search_queries

    def for_agent_voc(self) -> dict:
        return {"voc_keywords": self.voc_keywords, "trend_keywords": self.trend_keywords}

    def for_agent_trends(self) -> list[str]:
        return self.trend_keywords


class KeywordExtractorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="keyword_extractor",
            temperature=LLM_CONFIG["temperature"],
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=min(LLM_CONFIG.get("max_tokens") or 4096, 8000),
        )

    async def run(self, state: PipelineState) -> PipelineState:
        return state

    async def extract_from_idea(self, idea: dict) -> KeywordBundle:
        self.logger.info(
            "[keyword_extractor] pitch=%r | model=%s",
            (idea.get("short_pitch") or "")[:120],
            LLM_CONFIG["model"],
        )
        user = build_keyword_extraction_user_prompt(idea)
        raw_text = await self._call_llm(KEYWORD_EXTRACTOR_SYSTEM_PROMPT, user)
        try:
            data = parse_keyword_json_response(raw_text)
        except json.JSONDecodeError as e:
            self.logger.error("[keyword_extractor] JSON invalide: %r", raw_text[:400])
            raise RuntimeError(f"Réponse LLM non JSON: {e}") from e

        bundle = KeywordBundle(
            primary_keywords=norm_str_list(data.get("primary_keywords"), max_len=5),
            market_keywords=norm_str_list(data.get("market_keywords"), max_len=4),
            competitor_search_queries=norm_str_list(data.get("competitor_search_queries"), max_len=4),
            voc_keywords=norm_str_list(data.get("voc_keywords"), max_len=5),
            trend_keywords=norm_str_list(data.get("trend_keywords"), max_len=4),
            sector_tags=norm_str_list(data.get("sector_tags"), max_len=3),
        )
        self.logger.info(
            "[keyword_extractor] ok | n_primary=%s n_voc=%s",
            len(bundle.primary_keywords),
            len(bundle.voc_keywords),
        )
        return bundle


async def extract_keywords(idea: dict) -> KeywordBundle:
    return await KeywordExtractorAgent().extract_from_idea(idea)
