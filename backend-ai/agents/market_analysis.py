# ══════════════════════════════════════════════════════════════
#  market_analysis.py
#  Market Analysis Agent
#  - Appels outils en parallèle (asyncio.gather)
#  - LLM via BaseAgent._call_llm
#  - Output JSON structuré
# ══════════════════════════════════════════════════════════════

import asyncio
import json

from agents.base_agent import BaseAgent, PipelineState

from tools.market_tools import (
    fetch_serpapi,
    fetch_youtube,
    fetch_news,
    fetch_reddit,
    fetch_trends,
    fetch_worldbank,
)

from utils.market_utils import build_queries
from prompts.market_prompts import SYSTEM_PROMPT, build_user_prompt

from llm.llm_rotator import LLMRotator

class MarketAnalysisAgent(BaseAgent):


    def __init__(self):
        super().__init__(
            agent_name="market_analysis",
            temperature=0.3,
            max_retries=3,
        )

        # 🔥 GROQ + GPT OSS
        self.llm_rotator = LLMRotator.groq_gpt_only()

    # ─────────────────────────────────────────────
    # MAIN RUN
    # ─────────────────────────────────────────────
    async def run(self, state: PipelineState):

        self._log_start(state)

        try:
            # ══════════════════════════════════
            # 1. EXTRACTION IDEA
            # ══════════════════════════════════

            idea = state.clarified_idea or {}

            problem  = idea.get("problem",  "")
            target   = idea.get("target",   "")
            sector   = idea.get("sector",   "")
            solution = idea.get("solution", "")

            self.logger.info(
                f"[market_analysis] Idea received | sector={sector} | target={target}"
            )

            # ══════════════════════════════════
            # 2. BUILD QUERIES
            # ══════════════════════════════════

            queries = build_queries(
                problem=problem,
                target=target,
                sector=sector,
                solution=solution,
            )

            self.logger.info(
                f"[market_analysis] Queries built — "
                f"{sum(len(v) for v in queries.values())} total queries"
            )

            # ══════════════════════════════════
            # 3. CALL TOOLS EN PARALLÈLE
            # ══════════════════════════════════

            self.logger.info("[market_analysis] Fetching all tools in parallel...")

            (
                serp,
                youtube,
                news,
                reddit,
                trends,
                worldbank,
            ) = await asyncio.gather(
                fetch_serpapi(queries),
                fetch_youtube(queries),
                fetch_news(queries),          # ← on passe queries maintenant
                fetch_reddit(queries),
                fetch_trends(queries),
                fetch_worldbank(),            # country par défaut = TN
                return_exceptions=True,       # ne pas planter si une API échoue
            )

            # Fallback si une tool a levé une exception
            serp      = serp      if isinstance(serp,      dict) else {}
            youtube   = youtube   if isinstance(youtube,   dict) else {}
            news      = news      if isinstance(news,      dict) else {}
            reddit    = reddit    if isinstance(reddit,    dict) else {}
            trends    = trends    if isinstance(trends,    dict) else {}
            worldbank = worldbank if isinstance(worldbank, dict) else {}

            self.logger.info("[market_analysis] All tools done")

            # ══════════════════════════════════
            # 4. BUILD RAW DATA
            # ══════════════════════════════════

            raw_data = self._build_raw_summary(
                idea, serp, youtube, news, reddit, trends, worldbank
            )

            # Sauvegarde debug
            try:
                with open("market_raw_data.json", "w", encoding="utf-8") as f:
                    json.dump(raw_data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

            # ══════════════════════════════════
            # 5. LLM ANALYSIS
            # ══════════════════════════════════

            self.logger.info("[market_analysis] Calling LLM...")

            user_prompt = build_user_prompt(raw_data)
            response    = await self._call_llm(SYSTEM_PROMPT, user_prompt)

            # ══════════════════════════════════
            # 6. PARSE JSON
            # ══════════════════════════════════

            parsed = self._parse_json(response)

            # ══════════════════════════════════
            # 7. SAVE RESULT
            # ══════════════════════════════════

            state.market_analysis = parsed

            try:
                with open("market_analysis.json", "w", encoding="utf-8") as f:
                    json.dump(parsed, f, ensure_ascii=False, indent=2)
                self.logger.info("[market_analysis] Output saved → market_analysis.json")
            except Exception:
                pass

            self._log_success()
            return state

        except Exception as e:
            self._log_error(e)
            state.errors.append(str(e))
            state.status = "error"
            return state

    # ──────────────────────────────────────────────────────────
    # BUILD RAW SUMMARY
    # ──────────────────────────────────────────────────────────

    def _build_raw_summary(
        self,
        idea:      dict,
        serp:      dict,
        youtube:   dict,
        news:      dict,
        reddit:    dict,
        trends:    dict,
        worldbank: dict,
    ) -> dict:

        return {
            "idea": idea,

            # SerpAPI
            "raw_competitors":  serp.get("competitors",     [])[:10],
            "organic_signals":  serp.get("organic_signals", [])[:10],

            # YouTube
            "top_youtube_signals": youtube.get("trending_videos", [])[:5],

            # News
            "news_articles":       news.get("articles",           [])[:8],
            "funding_signals":     news.get("funding_signals",    []),
            "regulatory_signals":  news.get("regulatory_signals", []),

            # Reddit
            "reddit_posts":         reddit.get("posts",                [])[:10],
            "reddit_pain_points":   reddit.get("pain_points",          [])[:5],
            "competitor_mentions":  reddit.get("competitor_mentions",  [])[:5],

            # Google Trends
            "growth_trends": trends.get("trends", []),

            # World Bank
            "macro_context": worldbank,
        }