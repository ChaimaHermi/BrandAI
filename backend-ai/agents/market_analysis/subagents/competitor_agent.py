import asyncio

from agents.base_agent import BaseAgent
from prompts.market_analysis.prompt_competitor import PROMPT_COMPETITOR
from tools.market_analysis.serpapi_tool import serpapi_search
from tools.market_analysis.tavily_tool import tavily_search
from utils.text_cleaner import clean_text


_TAVILY_PER_QUERY  = 10
_SERP_PER_QUERY    = 5
_TOTAL_RESULTS_MAX = 30
_CONTENT_MAX       = 2_000
_CONTEXT_MAX       = 500_000
_CONCURRENCY       = 5   # requêtes API simultanées max (évite rate limit)


class CompetitorAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            agent_name="competitor",
            temperature=0.1
        )

    def build_context(self, results):
        blocks = []
        for r in results:
            src      = (r.get("source") or "").strip()
            url      = (r.get("url") or "").strip()
            title_s  = clean_text(r.get("title") or "")[:200]
            content_s = clean_text(r.get("content") or "")[:_CONTENT_MAX]
            blocks.append(
                f"SOURCE: {src}\n"
                f"URL: {url}\n"
                f"Title: {title_s}\n"
                f"Content: {content_s}"
            )
        context = "\n\n".join(blocks)
        return context[:_CONTEXT_MAX] if len(context) > _CONTEXT_MAX else context

    async def _fetch_tavily(self, semaphore: asyncio.Semaphore, q: str) -> list:
        async with semaphore:
            results = await asyncio.to_thread(tavily_search, q)
            return [
                {
                    "source":  "Tavily",
                    "title":   r.get("title") or "",
                    "content": r.get("content") or "",
                    "url":     r.get("url") or "",
                }
                for r in results[:_TAVILY_PER_QUERY]
            ]

    async def _fetch_serp(self, semaphore: asyncio.Semaphore, q: str) -> list:
        async with semaphore:
            results = await asyncio.to_thread(serpapi_search, q)
            return [
                {
                    "source":  "SerpAPI",
                    "title":   r.get("title") or "",
                    "content": r.get("snippet") or "",
                    "url":     r.get("link") or "",
                }
                for r in results[:_SERP_PER_QUERY]
            ]

    async def run(self, state):
        queries = (state.market_analysis or {}).get("competitor_queries", [])

        semaphore = asyncio.Semaphore(_CONCURRENCY)
        tasks = (
            [self._fetch_tavily(semaphore, q) for q in queries] +
            [self._fetch_serp(semaphore, q)   for q in queries]
        )
        batches = await asyncio.gather(*tasks)

        all_rows = []
        for batch in batches:
            all_rows.extend(batch)
        final_results = all_rows[:_TOTAL_RESULTS_MAX]

        context = self.build_context(final_results)

        response = await self._call_llm(
            system_prompt=PROMPT_COMPETITOR,
            user_prompt=context
        )

        if not response:
            return {"agent": "competitor", "status": "error",
                    "error": "Empty LLM response", "data": {}}

        try:
            data = self._parse_json(response)
        except Exception as e:
            preview = (response[:220] + "...") if len(response) > 220 else response
            return {"agent": "competitor", "status": "error",
                    "error": f"Invalid competitor JSON: {e}; preview={preview!r}", "data": {}}

        competitors = data.get("competitors")
        if isinstance(competitors, list):
            fallback_url = next(
                (x.get("url") for x in final_results if (x.get("url") or "").strip()), ""
            )
            for comp in competitors:
                if not isinstance(comp, dict):
                    continue
                if not (comp.get("website") or "").strip() and fallback_url:
                    comp["website"] = fallback_url
                if comp.get("strengths") is None:
                    comp["strengths"] = []
                if comp.get("weaknesses") is None:
                    comp["weaknesses"] = []

        return {"agent": "competitor", "status": "success", "data": data}
