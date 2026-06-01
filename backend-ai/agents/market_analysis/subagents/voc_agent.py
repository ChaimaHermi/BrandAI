import asyncio

from agents.base_agent import BaseAgent
from observability.langsmith_tracing import agent_trace
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

    _INSIGHT_LIST_KEYS = (
        "pain_points",
        "frustrations",
        "desired_features",
        "market_insights",
    )

    def _enrich_voc_queries(self, queries: list) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for raw in queries:
            s = str(raw).strip()
            if not s:
                continue
            k = s.lower()
            if k not in seen:
                seen.add(k)
                out.append(s)
            if "reddit" not in k and "review" not in k and len(out) < 8:
                alt = f"{s} user reviews reddit"
                ak = alt.lower()
                if ak not in seen:
                    seen.add(ak)
                    out.append(alt)
        return out[:8]

    def _filter_insights_by_corpus(self, data: dict, context: str, all_results: list) -> dict:
        if not isinstance(data, dict):
            return data
        ctx_lower = (context or "").lower()
        valid_urls = {
            (r.get("url") or "").strip()
            for r in (all_results or [])
            if (r.get("url") or "").strip()
        }

        for key in self._INSIGHT_LIST_KEYS:
            items = data.get(key)
            if not isinstance(items, list):
                data[key] = []
                continue
            kept = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                snippet = str(item.get("evidence_snippet") or "").strip()
                src = str(item.get("source") or "").strip()
                if len(snippet) < 10:
                    continue
                if snippet.lower() not in ctx_lower:
                    continue
                if src.startswith("http") and valid_urls and src not in valid_urls:
                    continue
                kept.append(item)
            data[key] = kept[:3]

        quotes = data.get("user_quotes")
        if isinstance(quotes, list):
            kept_q = []
            for q in quotes:
                if not isinstance(q, dict):
                    continue
                quote = str(q.get("quote") or "").strip()
                if len(quote) < 5 or quote.lower() not in ctx_lower:
                    continue
                kept_q.append(q)
            data["user_quotes"] = kept_q[:3]

        return data

    # ─────────────────────────
    # RUN
    # ─────────────────────────
    @agent_trace("voc.run", tags=["market_analysis", "voc"])
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

        queries = self._enrich_voc_queries(queries)

        all_results = []

        # ─────────────────────────
        # SEARCH VIA TAVILY
        # ─────────────────────────
        for q in queries:
            results = await asyncio.to_thread(tavily_search, q)
            all_results.extend(results[:8])

        # GLOBAL LIMIT
        all_results = all_results[:40]

        context = self.build_context(all_results)

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

        data = self._filter_insights_by_corpus(data, context, all_results)

        data["sources"] = self._normalize_sources(
            all_results=all_results,
            llm_sources=data.get("sources", [])
        )

        return {
            "agent": "voc",
            "status": "success",
            "data": data,
            "collected_context": context,
        }