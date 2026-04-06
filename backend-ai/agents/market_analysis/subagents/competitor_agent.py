from agents.base_agent import BaseAgent
from prompts.market_analysis.prompt_competitor import PROMPT_COMPETITOR

from tools.market_analysis.serpapi_tool import serpapi_search
from tools.market_analysis.tavily_tool import tavily_search

from utils.text_cleaner import clean_text


_TAVILY_PER_QUERY = 5
_SERP_PER_QUERY = 2
_TOTAL_RESULTS_MAX = 20
_CONTENT_MAX = 300
_CONTEXT_MAX = 5000


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
            title_raw = clean_text(r.get("title") or "")
            body_raw = clean_text(r.get("content") or "")
            title_s = title_raw[:200] if len(title_raw) > 200 else title_raw
            content_s = body_raw[:_CONTENT_MAX] if len(body_raw) > _CONTENT_MAX else body_raw
            block = (
                f"SOURCE: {src}\n"
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
                })

        serp_rows = []
        for q in queries:
            for r in serpapi_search(q)[:_SERP_PER_QUERY]:
                serp_rows.append({
                    "source": "SerpAPI",
                    "title": r.get("title") or "",
                    "content": r.get("snippet") or "",
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

        data = self._parse_json(response)

        return {
            "agent": "competitor",
            "status": "success",
            "data": data
        }
