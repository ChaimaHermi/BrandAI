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

    def _attach_sources(self, data, sources, sector_name=""):
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
        if sector_name and not str(data.get("sector_name") or "").strip():
            data["sector_name"] = sector_name
        data["sources"] = sources
        return data

    def _market_keywords_from_state(self, state: PipelineState, cap: int) -> list[str]:
        ma = state.market_analysis or {}
        if not isinstance(ma, dict):
            return []
        market_kws = ma.get("market_keywords")
        growth_kws = ma.get("sector_growth_keywords")
        market_list = market_kws if isinstance(market_kws, list) else []
        growth_list = growth_kws if isinstance(growth_kws, list) else []

        if cap <= 0:
            return []

        # Option 2: guaranteed mix for market sizing queries.
        # Keep a fixed split under the current cap (default 5): 3 market + 2 growth.
        target_market = min(3, cap)
        target_growth = min(2, max(cap - target_market, 0))

        out = []
        seen = set()

        def push(items, take):
            added = 0
            for raw in items:
                if added >= take or len(out) >= cap:
                    break
                s = str(raw).strip()
                if not s:
                    continue
                k = s.lower()
                if k in seen:
                    continue
                seen.add(k)
                out.append(s)
                added += 1

        # First pass: guaranteed split
        push(market_list, target_market)
        push(growth_list, target_growth)

        # Second pass: backfill remaining slots from both pools if needed
        if len(out) < cap:
            push(market_list, cap - len(out))
        if len(out) < cap:
            push(growth_list, cap - len(out))

        return out

    async def run(self, state: PipelineState) -> dict:
        self._log_start(state)

        cap = int(
            MARKET_ANALYSIS_CONFIG.get("agents", {})
            .get("market_sizing", {})
            .get("max_keywords", 5)
        )
        market_keywords = self._market_keywords_from_state(state, cap)

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
            sector_name = str((state.clarified_idea or {}).get("sector") or "").strip()
            data = self._attach_sources(data, self._extract_sources(all_results), sector_name)
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
