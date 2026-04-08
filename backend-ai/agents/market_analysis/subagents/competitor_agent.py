from agents.base_agent import BaseAgent
from prompts.market_analysis.prompt_competitor import PROMPT_COMPETITOR

from tools.market_analysis.serpapi_tool import serpapi_search
from tools.market_analysis.tavily_tool import tavily_search

from utils.text_cleaner import clean_text


_TAVILY_PER_QUERY = 5
_SERP_PER_QUERY = 2
_TOTAL_RESULTS_MAX = 20
_CONTENT_MAX = 700
_CONTEXT_MAX = 7000


class CompetitorAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            agent_name="competitor",
            temperature=0.1
        )

    def build_context(self, results):
        blocks = []

        for r in results:
            src = (r.get("source") or "").strip()
            url = (r.get("url") or "").strip()
            title_raw = clean_text(r.get("title") or "")
            body_raw = clean_text(r.get("content") or "")
            title_s = title_raw[:200] if len(title_raw) > 200 else title_raw
            content_s = body_raw[:_CONTENT_MAX] if len(body_raw) > _CONTENT_MAX else body_raw
            block = (
                f"SOURCE: {src}\n"
                f"URL: {url}\n"
                f"Title: {title_s}\n"
                f"Content: {content_s}"
            )
            blocks.append(block)

        context = "\n\n".join(blocks)
        if len(context) > _CONTEXT_MAX:
            context = context[:_CONTEXT_MAX]
        return context

    async def run(self, state):

        queries = (state.market_analysis or {}).get("competitor_queries", [])

        tavily_rows = []
        for q in queries:
            for r in tavily_search(q)[:_TAVILY_PER_QUERY]:
                tavily_rows.append({
                    "source": "Tavily",
                    "title": r.get("title") or "",
                    "content": r.get("content") or "",
                    "url": r.get("url") or "",
                })

        serp_rows = []
        for q in queries:
            for r in serpapi_search(q)[:_SERP_PER_QUERY]:
                serp_rows.append({
                    "source": "SerpAPI",
                    "title": r.get("title") or "",
                    "content": r.get("snippet") or "",
                    "url": r.get("link") or "",
                })

        final_results = (tavily_rows + serp_rows)[:_TOTAL_RESULTS_MAX]

        print("[DEBUG] total results:", len(final_results))

        context = self.build_context(final_results)

        print("[DEBUG] CONTEXT LENGTH:", len(context))
        print("[DEBUG] APPROX TOKENS:", len(context) // 4)

        response = await self._call_llm(
            system_prompt=PROMPT_COMPETITOR,
            user_prompt=context
        )

        if not response:
            return {
                "agent": "competitor",
                "status": "error",
                "error": "Empty LLM response",
                "data": {}
            }

        try:
            data = self._parse_json(response)
        except Exception as e:
            preview = (response[:220] + "...") if len(response) > 220 else response
            return {
                "agent": "competitor",
                "status": "error",
                "error": f"Invalid competitor JSON: {e}; preview={preview!r}",
                "data": {},
            }

        competitors = data.get("competitors")
        if isinstance(competitors, list):
            fallback_urls = [x.get("url") for x in final_results if (x.get("url") or "").strip()]
            fallback_url = fallback_urls[0] if fallback_urls else ""
            for comp in competitors:
                if not isinstance(comp, dict):
                    continue
                website = (comp.get("website") or "").strip()
                if not website and fallback_url:
                    comp["website"] = fallback_url
                # Keep schema stable for frontend rendering.
                if comp.get("strengths") is None:
                    comp["strengths"] = []
                if comp.get("weaknesses") is None:
                    comp["weaknesses"] = []

        return {
            "agent": "competitor",
            "status": "success",
            "data": data
        }
