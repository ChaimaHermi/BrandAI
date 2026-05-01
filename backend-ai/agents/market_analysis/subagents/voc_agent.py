from agents.base_agent import BaseAgent
from prompts.market_analysis.prompt_voc import PROMPT_VOC
from tools.market_analysis.tavily_tool import tavily_search
from utils.text_cleaner import clean_text
from config.market_analysis_config import MARKET_ANALYSIS_CONFIG


class VOCAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            agent_name="voc",
            temperature=0.1
        )

    # ─────────────────────────
    # BUILD CONTEXT
    # ─────────────────────────
    def build_context(self, results):
        texts = []

        for r in results:
            title = clean_text(r.get("title", ""))[:300]
            content = clean_text(r.get("content", ""))[:2_000]
            url = r.get("url", "")

            source = "web"
            if "reddit" in url.lower():
                source = "reddit"
            elif "youtube" in url.lower():
                source = "youtube"

            block = f"""
SOURCE: {source}
URL: {url}
TITLE: {title}
CONTENT: {content}
"""
            texts.append(block)

        context = "\n\n".join(texts)

        return context  # pas de limite — NVIDIA 128K context window

    def _normalize_sources(self, all_results, llm_sources):
        out = []
        seen = set()

        def _push(source, url):
            src = (source or "web").strip().lower()
            if src not in {"reddit", "youtube", "web"}:
                src = "web"
            u = (url or "").strip()
            if not u or u in seen:
                return
            seen.add(u)
            out.append({"source": src, "url": u})

        # Trust LLM extraction first if present
        if isinstance(llm_sources, list):
            for item in llm_sources:
                if not isinstance(item, dict):
                    continue
                _push(item.get("source"), item.get("url"))

        # Fallback/merge with retrieved search results
        for r in all_results:
            url = (r or {}).get("url", "")
            source = "web"
            if "reddit" in url.lower():
                source = "reddit"
            elif "youtube" in url.lower():
                source = "youtube"
            _push(source, url)

        return out[:8]

    # ─────────────────────────
    # RUN
    # ─────────────────────────
    async def run(self, state):

        # GET QUERIES FROM STATE (IMPORTANT)
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

            # LIMIT PER QUERY
            all_results.extend(results[:8])

        # GLOBAL LIMIT
        all_results = all_results[:40]

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

        data["sources"] = self._normalize_sources(
            all_results=all_results,
            llm_sources=data.get("sources", [])
        )

        return {
            "agent": "voc",
            "status": "success",
            "data": data
        }