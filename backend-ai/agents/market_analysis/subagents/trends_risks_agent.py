from agents.base_agent import BaseAgent
from prompts.market_analysis.prompt_trends_risks import PROMPT_TRENDS_RISKS
from tools.market_analysis.tavily_tool import tavily_search
from utils.text_cleaner import clean_text


class TrendsRisksAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            agent_name="trends_risks",
            temperature=0.2
        )

    # ─────────────────────────
    # BUILD CONTEXT
    # ─────────────────────────
    def build_context(self, results):
        texts = []

        for r in results:
            title = clean_text(r.get("title", ""))[:100]
            content = clean_text(r.get("content", ""))[:300]
            url = r.get("url", "")

            source = "web"
            if "report" in url:
                source = "report"
            elif "news" in url:
                source = "news"

            block = f"""
SOURCE: {source}
TITLE: {title}
CONTENT: {content}
"""
            texts.append(block)

        context = "\n\n".join(texts)
        return context[:4000]

    # ─────────────────────────
    # RUN
    # ─────────────────────────
    async def run(self, state):

        queries = (state.market_analysis or {}).get("trend_queries", [])

        if not queries:
            return {
                "agent": "trends_risks",
                "status": "error",
                "error": "No trend queries provided",
                "data": {}
            }

        all_results = []

        for q in queries:
            results = tavily_search(q)
            all_results.extend(results[:3])

        all_results = all_results[:8]

        print("[DEBUG TRENDS] total results:", len(all_results))

        context = self.build_context(all_results)

        print("[DEBUG TRENDS] context length:", len(context))
        print("[DEBUG TRENDS] approx tokens:", len(context) // 4)

        response = await self._call_llm(
            system_prompt=PROMPT_TRENDS_RISKS,
            user_prompt=context
        )

        if not response or response.strip() == "":
            return {
                "agent": "trends_risks",
                "status": "error",
                "error": "Empty LLM response",
                "data": {}
            }

        data = self._parse_json(response)

        if not data:
            return {
                "agent": "trends_risks",
                "status": "error",
                "error": "Invalid JSON",
                "data": {}
            }

        return {
            "agent": "trends_risks",
            "status": "success",
            "data": data
        }