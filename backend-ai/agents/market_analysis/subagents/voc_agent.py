from agents.base_agent import BaseAgent
from prompts.market_analysis.prompt_voc import PROMPT_VOC
from tools.market_analysis.tavily_tool import tavily_search
from utils.text_cleaner import clean_text
from config.market_analysis_config import MARKET_ANALYSIS_CONFIG


class VOCAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            agent_name="voc",
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
            if "reddit" in url.lower():
                source = "reddit"
            elif "youtube" in url.lower():
                source = "youtube"

            block = f"""
SOURCE: {source}
TITLE: {title}
CONTENT: {content}
"""
            texts.append(block)

        context = "\n\n".join(texts)

        # 🔥 LIMIT CONTEXT (CRITICAL)
        return context[:4000]

    # ─────────────────────────
    # RUN
    # ─────────────────────────
    async def run(self, state):

        # 🔥 GET QUERIES FROM STATE (IMPORTANT)
        queries = state.market_analysis.get("voc_queries", [])

        if not queries:
            return {
                "agent": "voc",
                "status": "error",
                "error": "No VOC queries provided",
                "data": {}
            }

        all_results = []

        # ─────────────────────────
        # SEARCH VIA TAVILY
        # ─────────────────────────
        for q in queries:
            results = tavily_search(q)

            # 🔥 LIMIT PER QUERY
            all_results.extend(results[:3])

        # 🔥 GLOBAL LIMIT
        all_results = all_results[:8]

        print("[DEBUG VOC] total results:", len(all_results))

        # ─────────────────────────
        # BUILD CONTEXT
        # ─────────────────────────
        context = self.build_context(all_results)

        print("[DEBUG VOC] context length:", len(context))
        print("[DEBUG VOC] approx tokens:", len(context) // 4)

        # ─────────────────────────
        # CALL LLM
        # ─────────────────────────
        response = await self._call_llm(
            system_prompt=PROMPT_VOC,
            user_prompt=context
        )

        if not response or response.strip() == "":
            return {
                "agent": "voc",
                "status": "error",
                "error": "Empty LLM response",
                "data": {}
            }

        # ─────────────────────────
        # PARSE JSON
        # ─────────────────────────
        data = self._parse_json(response)

        if not data:
            return {
                "agent": "voc",
                "status": "error",
                "error": "Invalid JSON from LLM",
                "data": {}
            }

        return {
            "agent": "voc",
            "status": "success",
            "data": data
        }