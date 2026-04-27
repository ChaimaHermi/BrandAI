from urllib.parse import urlparse

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
            title = clean_text(r.get("title", ""))[:300]
            content = clean_text(r.get("content", ""))[:2_000]
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
        return context  # pas de limite — NVIDIA 128K context window

    def _extract_sources(self, results, max_items=12):
        """Deduplicated Tavily URLs for UI (same shape as market_sizing: url + domain)."""
        out = []
        seen = set()
        for r in results:
            raw = (r.get("url") or r.get("link") or "").strip()
            if not raw or raw in seen:
                continue
            seen.add(raw)
            domain = ""
            try:
                domain = urlparse(raw).netloc or ""
            except Exception:
                domain = ""
            out.append({"url": raw, "domain": domain})
            if len(out) >= max_items:
                break
        return out

    def _attach_sources(self, data, all_results):
        if not isinstance(data, dict):
            return data
        data["sources"] = self._extract_sources(all_results)
        return data

    # ─────────────────────────
    # RUN
    # ─────────────────────────
    async def run(self, state):

        ma = (state.market_analysis or {})
        trend_queries = ma.get("trend_queries", []) if isinstance(ma, dict) else []
        risk_queries = ma.get("risk_queries", []) if isinstance(ma, dict) else []
        trend_q = []
        risk_q = []
        seen = set()
        for q in (trend_queries if isinstance(trend_queries, list) else []):
            s = str(q).strip()
            if not s:
                continue
            k = s.lower()
            if k in seen:
                continue
            seen.add(k)
            trend_q.append(s)
        for q in (risk_queries if isinstance(risk_queries, list) else []):
            s = str(q).strip()
            if not s:
                continue
            k = s.lower()
            if k in seen:
                continue
            seen.add(k)
            risk_q.append(s)

        queries = trend_q + risk_q

        if not queries:
            return {
                "agent": "trends_risks",
                "status": "error",
                "error": "No trend queries provided",
                "data": {}
            }

        all_results = []

        # Balanced retrieval: reserve room for both trend and risk evidence.
        # This prevents risk queries from being dropped by the global cap.
        per_query_cap = 4
        trend_budget = 20
        risk_budget = 20

        trend_results = []
        for q in trend_q:
            results = tavily_search(q)
            trend_results.extend(results[:per_query_cap])
            if len(trend_results) >= trend_budget:
                break
        trend_results = trend_results[:trend_budget]

        risk_results = []
        for q in risk_q:
            results = tavily_search(q)
            risk_results.extend(results[:per_query_cap])
            if len(risk_results) >= risk_budget:
                break
        risk_results = risk_results[:risk_budget]

        # Interleave trend/risk chunks to keep both signal types in context.
        i = j = 0
        while len(all_results) < 40 and (i < len(trend_results) or j < len(risk_results)):
            if i < len(trend_results):
                all_results.append(trend_results[i])
                i += 1
            if len(all_results) >= 40:
                break
            if j < len(risk_results):
                all_results.append(risk_results[j])
                j += 1

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

        data = self._attach_sources(data, all_results)

        return {
            "agent": "trends_risks",
            "status": "success",
            "data": data
        }