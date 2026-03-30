# ══════════════════════════════════════════════════════════════
# agents/market_analysis/subagents/signal_agent.py
# Robuste : multi-query trends + multi-source tavily + fallbacks
# ══════════════════════════════════════════════════════════════

import asyncio
import json
import logging

from agents.base_agent import BaseAgent, PipelineState
from config.market_analysis_config import LLM_CONFIG, LLM_LIMITS
from schemas.market_analysis_schemas import Tendances
from tools.market_analysis.subagents_tools.signal_tools import (
    fetch_google_autocomplete,
    fetch_google_trends,
    fetch_regulatory,
    fetch_tavily_trends,
    fetch_tiktok_signals,
)
from utils.simple_filter import simple_filter

logger = logging.getLogger("brandai.signal_agent")


class SignalAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="signal_agent",
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=LLM_CONFIG["max_tokens"],
            temperature=LLM_CONFIG["temperature"],
        )

    async def run(self, state: PipelineState, queries: dict) -> dict:
        self._log_start(state)
        idea = (state.clarified_idea or {}).get("short_pitch", state.name)
        sector = (state.clarified_idea or {}).get("sector", state.sector)
        q = self._validate_queries(queries, idea=idea, sector=sector)
        country = q.get("country", "TN")

        try:
            trends_queries = [q["trends_1"], q["trends_2"], *q.get("trends_multi", [])]
            trends_queries = self._dedup_keep_order([x for x in trends_queries if x])

            trends_results = await asyncio.gather(
                *[fetch_google_trends(tq, country) for tq in trends_queries]
            )
            autocomplete_results = await asyncio.gather(
                *[fetch_google_autocomplete(tq, country) for tq in trends_queries]
            )
            tavily_trends_results = await asyncio.gather(
                *[fetch_tavily_trends(tq, country) for tq in trends_queries]
            )
            tiktok, regulatory = await asyncio.gather(
                fetch_tiktok_signals(q["tiktok"]),
                fetch_regulatory(q["regulatory"], country),
            )

            trends_merged = self._merge_trends_sources(trends_results)
            autocomplete_merged = self._merge_autocomplete_sources(autocomplete_results)
            tavily_merged = self._merge_tavily_sources(tavily_trends_results)
            peak_period = self._compute_peak_period(trends_results)

            raw_data = {
                "trends_queries": trends_queries,
                "trends_multi": trends_results,
                "trends_merged": trends_merged,
                "autocomplete_multi": autocomplete_results,
                "autocomplete_merged": autocomplete_merged,
                "tavily_trends_multi": tavily_trends_results,
                "tavily_trends_merged": tavily_merged,
                "tiktok": tiktok,
                "regulatory": regulatory,
                "peak_period_detected": peak_period,
            }

            raw_data_filtered = {
                "trends_multi": [
                    {
                        "title": f"trends::{t.get('keyword', '')}"[:LLM_LIMITS["title_max_chars"]],
                        "snippet": json.dumps(
                            {
                                "rising_queries": t.get("rising_queries", []),
                                "rising_topics": t.get("rising_topics", []),
                                "peak_period": t.get("peak_period"),
                            },
                            ensure_ascii=False,
                        )[:LLM_LIMITS["snippet_max_chars"]],
                        "url": "",
                    }
                    for t in trends_results[: LLM_LIMITS["max_items"]]
                ],
                "autocomplete": [
                    {
                        "title": f"autocomplete::{a.get('keyword', '')}"[:LLM_LIMITS["title_max_chars"]],
                        "snippet": ", ".join(a.get("suggestions", [])[:6])[:LLM_LIMITS["snippet_max_chars"]],
                        "url": "",
                    }
                    for a in autocomplete_results[: LLM_LIMITS["max_items"]]
                ],
                "tavily_trends": simple_filter(
                    [
                        {"title": r.get("title", ""), "snippet": r.get("snippet", ""), "url": r.get("url", "")}
                        for src in tavily_trends_results
                        for r in src.get("results", [])
                    ],
                    LLM_LIMITS["max_items"],
                    LLM_LIMITS["snippet_max_chars"],
                ),
                "regulatory": simple_filter(regulatory.get("results", []), LLM_LIMITS["max_items"], LLM_LIMITS["snippet_max_chars"]),
            }

            payload = json.dumps(raw_data_filtered, ensure_ascii=False, default=str)
            if len(payload) > LLM_LIMITS["max_payload_chars"]:
                payload = payload[:LLM_LIMITS["max_payload_chars"]]

            llm_response = await self._call_llm(
                system_prompt=self._load_prompt("signal_agent.txt", state),
                user_prompt=payload,
            )
            data = self._parse_json(llm_response)
            data = self._validate_output(data, raw_data)
            data["rising_queries"] = self._clean_rising_queries(
                data.get("rising_queries", [])
            )

            output = Tendances(**data)
            self._log_success(output)
            return output.dict()
        except Exception as e:
            self._log_error(e)
            # Fallback complet sans LLM
            fallback_rising = self._clean_rising_queries(
                self._fallback_rising_queries(
                    {"trends_merged": {}, "autocomplete_merged": {}, "tavily_trends_merged": {}}
                )
            )
            fallback = {
                "direction": "STABLE",
                "signal_strength": "LOW",
                "peak_period": None,
                "rising_queries": fallback_rising,
                "hashtags": [],
                "hashtags_disponibles": False,
                "viral_score": "NONE",
                "viral_signals": [],
                "sector_context": "",
                "news_signals": [],
                "regulatory_barriers": [],
            }
            return Tendances(**fallback).dict()

    def _clean_rising_queries(self, queries):
        INVALID_TERMS = ["news", "market", "stock", "brand", "evaluation", "business"]

        cleaned = []

        for q in queries or []:
            if not q:
                continue

            q = str(q).strip()

            if len(q) < 5:
                continue

            if q.isdigit():
                continue

            if "|" in q:
                continue

            lower = q.lower()

            if any(term in lower for term in INVALID_TERMS):
                continue

            cleaned.append(q)

        return cleaned[:5]

    def _validate_queries(self, queries, idea, sector):
        q = dict(queries or {})
        idea = (idea or "").strip()
        sector = (sector or "").strip()
        default_1 = f"{idea} market trend".strip() if idea else f"{sector} market trend".strip()
        default_2 = f"{sector} growth".strip() if sector else "market growth"

        q["trends_1"] = (q.get("trends_1") or default_1 or "market trend").strip()
        q["trends_2"] = (q.get("trends_2") or default_2 or "industry growth").strip()

        multi = q.get("trends_multi") or []
        if isinstance(multi, str):
            multi = [multi]
        if not isinstance(multi, list):
            multi = []
        multi = [str(x).strip() for x in multi if str(x).strip()]
        for fallback_q in (default_1, default_2):
            if fallback_q and fallback_q.lower() not in {m.lower() for m in multi}:
                multi.append(fallback_q)
        q["trends_multi"] = multi

        q["tiktok"] = (q.get("tiktok") or q["trends_1"]).strip()
        q["regulatory"] = (q.get("regulatory") or f"regulation {sector or idea}").strip()
        q["country"] = (q.get("country") or "TN").strip().upper()
        return q

    def _merge_trends_sources(self, trends_results: list[dict]) -> dict:
        merged_timeline = []
        merged_rising = []
        merged_topics = []
        merged_signals = []

        for tr in trends_results:
            merged_timeline.extend(tr.get("timeline", []))
            merged_rising.extend(tr.get("rising_queries", []))
            merged_topics.extend(tr.get("rising_topics", []))
            merged_signals.extend(tr.get("top_queries", []))

        return {
            "timeline": merged_timeline,
            "rising_queries": self._dedup_keep_order(merged_rising)[:12],
            "rising_topics": self._dedup_keep_order(merged_topics)[:12],
            "top_queries": self._dedup_keep_order(merged_signals)[:12],
        }

    def _merge_autocomplete_sources(self, ac_results: list[dict]) -> dict:
        suggestions = []
        for ac in ac_results:
            suggestions.extend(ac.get("suggestions", []))
        return {"suggestions": self._dedup_keep_order(suggestions)[:12]}

    def _merge_tavily_sources(self, tavily_results: list[dict]) -> dict:
        signals = []
        snippets = []
        for tv in tavily_results:
            signals.extend(tv.get("signals", []))
            snippets.extend(tv.get("snippet_keywords", []))
        return {
            "signals": self._dedup_keep_order(signals)[:12],
            "snippet_keywords": self._dedup_keep_order(snippets)[:12],
        }

    def _fallback_rising_queries(self, raw_data: dict) -> list[str]:
        trends = raw_data.get("trends_merged", {})
        ac = raw_data.get("autocomplete_merged", {})
        tav = raw_data.get("tavily_trends_merged", {})
        candidates = []
        candidates.extend(trends.get("rising_queries", []))
        candidates.extend(trends.get("rising_topics", []))
        candidates.extend(ac.get("suggestions", []))
        candidates.extend(tav.get("signals", []))
        candidates.extend(tav.get("snippet_keywords", []))
        return self._dedup_keep_order(candidates)[:8]

    def _validate_output(self, data: dict, raw_data: dict) -> dict:
        direction = (data.get("direction") or "").upper()
        if direction not in {"RISING", "STABLE", "FALLING"}:
            # Heuristique simple depuis timeline
            timeline = raw_data.get("trends_merged", {}).get("timeline", [])
            if len(timeline) >= 2:
                first = timeline[0].get("value", 0) or 0
                last = timeline[-1].get("value", 0) or 0
                if last > first + 5:
                    direction = "RISING"
                elif last < first - 5:
                    direction = "FALLING"
                else:
                    direction = "STABLE"
            else:
                direction = "STABLE"
        data["direction"] = direction

        strength = (data.get("signal_strength") or "").upper()
        if strength not in {"HIGH", "MEDIUM", "LOW"}:
            rq_len = len(self._fallback_rising_queries(raw_data))
            strength = "HIGH" if rq_len >= 8 else "MEDIUM" if rq_len >= 4 else "LOW"
        data["signal_strength"] = strength

        if not data.get("rising_queries"):
            data["rising_queries"] = self._fallback_rising_queries(raw_data)

        if not data.get("peak_period"):
            data["peak_period"] = raw_data.get("peak_period_detected")

        # Champs minimums
        data.setdefault("hashtags", [])
        data.setdefault("hashtags_disponibles", False)
        data.setdefault("viral_score", "NONE")
        data.setdefault("viral_signals", [])
        data.setdefault("sector_context", "")
        data.setdefault("news_signals", [])
        data.setdefault("regulatory_barriers", [])
        return data

    def _compute_peak_period(self, trends_results: list[dict]):
        peak_date = None
        peak_value = -1
        for tr in trends_results:
            for point in tr.get("timeline", []):
                value = point.get("value", 0) or 0
                if value > peak_value:
                    peak_value = value
                    peak_date = point.get("date")
        return peak_date

    def _dedup_keep_order(self, items):
        seen = set()
        out = []
        for x in items:
            s = str(x).strip()
            if not s:
                continue
            k = s.lower()
            if k in seen:
                continue
            seen.add(k)
            out.append(s)
        return out

    def _load_prompt(self, filename: str, state: PipelineState) -> str:
        try:
            with open(f"prompts/market_analysis/{filename}", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"""Tu es un expert en signaux marché pour : {state.sector}.
Tu reçois trends_multi, autocomplete_multi, tavily_trends_multi, tiktok et regulatory.
Priorité rising_queries : trends_merged -> autocomplete_merged -> tavily_trends_merged.
Si rising_queries vide, remplir depuis fallback.
Retourne UNIQUEMENT un JSON valide :
{{
  "direction": "RISING|STABLE|FALLING",
  "signal_strength": "HIGH|MEDIUM|LOW",
  "peak_period": null,
  "rising_queries": ["q1", "q2", "q3"],
  "hashtags": [],
  "hashtags_disponibles": false,
  "viral_score": "NONE",
  "viral_signals": [],
  "sector_context": "",
  "news_signals": [],
  "regulatory_barriers": []
}}"""