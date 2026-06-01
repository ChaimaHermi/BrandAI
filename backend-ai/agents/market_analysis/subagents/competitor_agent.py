import asyncio

from agents.base_agent import BaseAgent
from observability.langsmith_tracing import agent_trace
from prompts.market_analysis.prompt_competitor import PROMPT_COMPETITOR
from tools.market_analysis.serpapi_tool import serpapi_search
from tools.market_analysis.tavily_tool import tavily_search
from utils.text_cleaner import clean_text


_TAVILY_PER_QUERY  = 10
_SERP_PER_QUERY    = 5
_TOTAL_RESULTS_MAX = 30
_CONTENT_MAX       = 2_000
_CONTEXT_MAX       = 500_000
_CONCURRENCY       = 5
_MAX_COMPETITORS   = 8


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

    def _enrich_competitor_queries(self, queries: list, clarified: dict) -> list[str]:
        country = str(clarified.get("country") or clarified.get("country_code") or "").strip()
        out: list[str] = []
        seen: set[str] = set()
        for raw in queries:
            s = str(raw).strip()
            if not s:
                continue
            variants = [s]
            if country and country.lower() not in s.lower():
                variants.append(f"{s} {country}")
            if "competitor" not in s.lower():
                variants.append(f"{s} competitors market")
            for v in variants:
                k = v.lower()
                if k not in seen:
                    seen.add(k)
                    out.append(v)
        return out[:10]

    def _filter_competitors_by_corpus(self, data: dict, context: str, all_results: list) -> dict:
        if not isinstance(data, dict):
            return data
        ctx_lower = (context or "").lower()
        valid_urls = {
            (r.get("url") or "").strip()
            for r in (all_results or [])
            if (r.get("url") or "").strip()
        }

        items = data.get("competitors")
        if not isinstance(items, list):
            data["competitors"] = []
            return data

        kept = []
        seen_names: set[str] = set()
        for comp in items:
            if not isinstance(comp, dict):
                continue
            name = str(comp.get("name") or "").strip()
            snippet = str(comp.get("evidence_snippet") or "").strip()
            website = str(comp.get("website") or "").strip()

            if len(name) < 2:
                continue
            if len(snippet) < 10 or snippet.lower() not in ctx_lower:
                if name.lower() not in ctx_lower:
                    continue
            if website.startswith("http") and valid_urls and website not in valid_urls:
                comp["website"] = ""

            nk = name.lower()
            if nk in seen_names:
                continue
            seen_names.add(nk)

            if comp.get("strengths") is None:
                comp["strengths"] = []
            if comp.get("weaknesses") is None:
                comp["weaknesses"] = []
            kept.append(comp)

        data["competitors"] = kept[:_MAX_COMPETITORS]
        return data

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

    @agent_trace("competitor.run", tags=["market_analysis", "competitor"])
    async def run(self, state):
        queries = (state.market_analysis or {}).get("competitor_queries", [])
        clarified = getattr(state, "clarified_idea", None) or {}

        if not queries:
            return {"agent": "competitor", "status": "error",
                    "error": "No competitor queries provided", "data": {}}

        queries = self._enrich_competitor_queries(queries, clarified)

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

        data = self._filter_competitors_by_corpus(data, context, final_results)

        return {
            "agent": "competitor",
            "status": "success",
            "data": data,
            "collected_context": context,
        }
