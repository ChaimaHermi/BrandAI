import asyncio
from urllib.parse import urlparse

from agents.base_agent import BaseAgent, PipelineState
from config.market_analysis_config import MARKET_ANALYSIS_CONFIG, MARKET_SIZING_LLM_CONFIG

from prompts.market_analysis.prompt_market_sizing import PROMPT_MARKET_SIZING
from tools.market_analysis.news_tool import news_search
from tools.market_analysis.serpapi_tool import serpapi_search
from tools.market_analysis.tavily_tool import tavily_search


class MarketSizingAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            agent_name="market_sizing",
            temperature=MARKET_SIZING_LLM_CONFIG["temperature"],
            llm_model=MARKET_SIZING_LLM_CONFIG["model"],
            llm_max_tokens=MARKET_SIZING_LLM_CONFIG["max_tokens"],
        )

    def build_context(self, results):
        texts = []

        for r in results:
            text = (
                "URL: " + (r.get("url", "") or r.get("link", "") or "") + "\n"
                + r.get("title", "") + "\n"
                + r.get("snippet", "") + "\n"
                + r.get("content", "") + "\n"
                + r.get("description", "") + "\n"
            )
            texts.append(text)

        return "\n\n".join(texts[:20])

    def _extract_sources(self, results, max_items=8):
        out = []
        seen = set()
        for r in results:
            raw = (r.get("url") or r.get("link") or "").strip()
            if not raw:
                continue
            if raw in seen:
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

    def _attach_sources(self, data, sources):
        if not isinstance(data, dict):
            return data
        first_source = sources[0]["url"] if sources else ""
        metric_keys = [
            "market_size",
            "market_revenue",
            "CAGR",
            "growth_rate",
            "number_of_users",
            "adoption_rate",
        ]
        for key in metric_keys:
            metric = data.get(key)
            if isinstance(metric, dict):
                src = (metric.get("source") or "").strip()
                if not src and first_source:
                    metric["source"] = first_source
        data["sources"] = sources
        return data

    def _market_keywords_from_state(self, state: PipelineState) -> list[str]:
        ma = state.market_analysis or {}
        if not isinstance(ma, dict):
            return []
        kws = ma.get("market_keywords")
        if isinstance(kws, list) and kws:
            return [str(x) for x in kws if x]
        bundle = ma.get("keyword_bundle") or {}
        if isinstance(bundle, dict):
            mk = bundle.get("market_keywords") or bundle.get("trend_keywords")
            if isinstance(mk, list):
                return [str(x) for x in mk if x]
        return []

    async def run(self, state: PipelineState) -> dict:
        self._log_start(state)

        market_keywords = self._market_keywords_from_state(state)
        cap = int(
            MARKET_ANALYSIS_CONFIG.get("agents", {})
            .get("market_sizing", {})
            .get("max_keywords", 5)
        )
        market_keywords = market_keywords[:cap]

        if not market_keywords:
            self._log_error("no market_keywords in state.market_analysis")
            return {
                "agent": "market_sizing",
                "status": "error",
                "error": "missing market_keywords",
                "data": None,
            }

        all_results = []
        for kw in market_keywords:
            serp, tavily, news = await asyncio.gather(
                asyncio.to_thread(serpapi_search, kw),
                asyncio.to_thread(tavily_search, kw),
                asyncio.to_thread(news_search, kw),
            )
            all_results.extend(serp + tavily + news)

        context = self.build_context(all_results)
        user_prompt = f"Web search results (aggregated):\n{context}"

        try:
            raw = await self._call_llm(PROMPT_MARKET_SIZING.strip(), user_prompt)
            data = self._parse_json(raw)
            data = self._attach_sources(data, self._extract_sources(all_results))
        except Exception as e:
            self._log_error(e)
            return {
                "agent": "market_sizing",
                "status": "error",
                "error": str(e),
                "data": None,
            }

        self._log_success()
        return {
            "agent": "market_sizing",
            "status": "success",
            "data": data,
        }
