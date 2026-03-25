# ══════════════════════════════════════════════════════════════
#  agents/market_analysis.py  —  BrandAI  (version finale)
#  _build_raw_summary() optimisée — ~3000 tokens, plus de 413
# ══════════════════════════════════════════════════════════════

import asyncio
import json

from agents.base_agent import BaseAgent, PipelineState
from tools.market_tools import (
    fetch_serpapi, fetch_tavily_competitor, fetch_youtube,
    fetch_news, fetch_reddit, fetch_trends,
    fetch_worldbank, fetch_regulatory,
)
from utils.market_utils import build_queries
from utils.market_output_normalize import normalize_market_analysis
from prompts.market_prompts import SYSTEM_PROMPT, build_user_prompt


class MarketAnalysisAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            agent_name="market_analysis",
            temperature=0.3,
            max_retries=3,
            llm_model="openai/gpt-oss-120b",
            llm_max_tokens=8192,
        )

    async def run(self, state: PipelineState):
        self._log_start(state)
        try:
            idea         = state.clarified_idea or {}
            problem      = idea.get("problem",      "")
            target       = idea.get("target",       "")
            sector       = idea.get("sector",       "")
            solution     = idea.get("solution",     "")
            country      = idea.get("country",      "Tunisie")
            country_code = idea.get("country_code", "TN")
            language     = idea.get("language",     "fr")

            self.logger.info(f"[market_analysis] sector={sector} | country={country}")

            queries = await build_queries(
                problem=problem, target=target, sector=sector,
                solution=solution, country=country,
                country_code=country_code, language=language,
            )
            self.logger.info(
                f"[market_analysis] Queries — "
                f"serpapi:{len(queries.get('serpapi_local',[]))} "
                f"tavily:{len(queries.get('tavily_competitor',[]))} "
                f"voc:{len(queries.get('tavily_voc',[]))}"
            )

            (serp, tavily_comp, youtube, news,
             reddit, trends, worldbank, regulatory,
            ) = await asyncio.gather(
                fetch_serpapi(queries), fetch_tavily_competitor(queries),
                fetch_youtube(queries), fetch_news(queries),
                fetch_reddit(queries), fetch_trends(queries),
                fetch_worldbank(country_code),
                fetch_regulatory(queries),
                return_exceptions=True,
            )

            def safe(v, d): return v if isinstance(v, dict) else d
            serp        = safe(serp,       {"competitors":[],"organic_signals":[],"local_ratings":[]})
            tavily_comp = safe(tavily_comp, {"competitor_summaries":[]})
            youtube     = safe(youtube,    {"trending_videos":[]})
            news        = safe(news,       {"articles":[],"funding_signals":[],"regulatory_signals":[]})
            reddit      = safe(reddit,     {"posts":[],"pain_points":[],"competitor_mentions":[]})
            trends      = safe(trends,     {"trends":[],"tiktok_signals":[]})
            worldbank   = safe(worldbank,  {})
            regulatory  = safe(regulatory, {"regulatory_data":[]})

            self.logger.info("[market_analysis] All tools done")

            raw_data = self._build_raw_summary(
                idea, serp, tavily_comp, youtube,
                news, reddit, trends, worldbank, regulatory,
            )

            est = len(json.dumps(raw_data, ensure_ascii=False)) // 4
            self.logger.info(
                f"[market_analysis] raw_data ~{est} tokens | "
                f"marge TPM: {8000 - est - 1300} tokens disponibles"
            )

            try:
                with open("market_raw_data.json", "w", encoding="utf-8") as f:
                    json.dump(raw_data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

            self.logger.info("[market_analysis] Calling gpt-oss-120b (reasoning=medium)...")
            response = await self._call_llm(SYSTEM_PROMPT, build_user_prompt(raw_data))
            parsed   = normalize_market_analysis(self._parse_json(response))
            state.market_analysis = parsed

            try:
                with open("market_analysis.json", "w", encoding="utf-8") as f:
                    json.dump(parsed, f, ensure_ascii=False, indent=2)
                self.logger.info("[market_analysis] Saved → market_analysis.json")
            except Exception:
                pass

            self._log_success()
            return state

        except Exception as e:
            self._log_error(e)
            state.errors.append(str(e))
            state.status = "error"
            return state

    def _build_raw_summary(
        self, idea, serp, tavily_comp, youtube,
        news, reddit, trends, worldbank, regulatory,
    ) -> dict:
        """
        VERSION OPTIMISÉE — ~3000 tokens (était ~11500)
        Garde uniquement les données décisionnelles pour l'analyse.
        """

        # 1. Trends — direction calculée en Python (économie: -608 tokens)
        optimized_trends = []
        for t in trends.get("trends", []):
            values = [
                v["extracted_value"]
                for week in t.get("timeline", [])
                for v in week.get("values", [])
                if isinstance(v.get("extracted_value"), (int, float))
            ]
            if values:
                avg, last, first = sum(values)/len(values), values[-1], values[0]
                if last > avg * 1.2 or (last - first) > 15:   direction = "RISING"
                elif last < avg * 0.8 or (first - last) > 15: direction = "DECLINING"
                else:                                          direction = "STABLE"
            else:
                avg, last, direction = 0, 0, "STABLE"
            optimized_trends.append({
                "keyword":        t.get("keyword", ""),
                "avg_volume":     round(avg),
                "last_volume":    round(last),
                "direction":      direction,
                "rising_queries": t.get("rising_queries", [])[:3],
            })

        # 2. Reddit — title 80 + body 150, sans URL (économie: -552 tokens)
        optimized_reddit = [
            {"title": p.get("title","")[:80], "body": (p.get("body","") or "")[:150]}
            for p in reddit.get("posts", [])[:8]
            if p.get("title","").strip()
        ]

        # 3. Tavily — sans score/raw_content (économie: -573 tokens)
        optimized_tavily = [
            {"title": t.get("title","")[:60], "content": (t.get("content","") or "")[:250]}
            for t in tavily_comp.get("competitor_summaries", [])[:5]
        ]

        # 4. Competitors — snippet 120 chars (économie: -489 tokens)
        optimized_competitors = [
            {"title": c.get("title","")[:60], "link": c.get("link",""),
             "snippet": (c.get("snippet","") or "")[:120]}
            for c in serp.get("competitors", [])[:8]
        ]

        # 5. News — title + description courte
        optimized_news = [
            {"title": a.get("title","")[:80],
             "description": (a.get("description","") or "")[:150],
             "source": a.get("source","")}
            for a in news.get("articles", [])[:5]
            if a.get("title","").strip()
        ]

        # 6. Regulatory — content tronqué
        optimized_regulatory = [
            {"title": r.get("title","")[:60], "content": (r.get("content","") or "")[:200]}
            for r in regulatory.get("regulatory_data", [])[:3]
        ]

        # 7. YouTube — description tronquée
        optimized_youtube = [
            {"title": v.get("title","")[:70], "description": (v.get("description","") or "")[:100]}
            for v in youtube.get("trending_videos", [])[:4]
        ]

        return {
            "idea":                        idea,
            "raw_competitors":             optimized_competitors,
            "organic_signals":             serp.get("organic_signals",    [])[:6],
            "local_ratings":               serp.get("local_ratings",      [])[:3],
            "tavily_competitor_summaries": optimized_tavily,
            "top_youtube_signals":         optimized_youtube,
            "news_articles":               optimized_news,
            "funding_signals":             news.get("funding_signals",    [])[:3],
            "regulatory_signals":          news.get("regulatory_signals", [])[:2],
            "reddit_posts":                optimized_reddit,
            "reddit_pain_points":          reddit.get("pain_points",        [])[:5],
            "competitor_mentions":         reddit.get("competitor_mentions", [])[:3],
            "growth_trends":               optimized_trends,
            "tiktok_signals":              trends.get("tiktok_signals",   [])[:3],
            "macro_context":               worldbank,
            "regulatory_data":             optimized_regulatory,
        }