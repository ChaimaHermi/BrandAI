# ══════════════════════════════════════════════════════════════
# agents/market_analysis/subagents/market_voc_agent.py
# Robuste : multi-query + fallbacks + Reddit priority
# ══════════════════════════════════════════════════════════════

import asyncio
import json
from typing import Any, Callable, Awaitable

from agents.base_agent import BaseAgent, PipelineState
from config.market_analysis_config import LLM_CONFIG, LLM_LIMITS
from schemas.market_analysis_schemas import MarketVoc
from tools.market_analysis.subagents_tools.market_voc_tools import (
    fetch_newsapi,
    fetch_reddit_voc,
    fetch_tavily_insights,
    fetch_worldbank,
    fetch_youtube_voc,
)
from utils.simple_filter import simple_filter


class MarketVocAgent(BaseAgent):
    _NEG_KW = [
        "problem", "problems", "complaint", "complaints", "bad", "worst",
        "issue", "issues", "slow", "bug", "buggy", "crash", "refund",
        "expensive", "delay", "late", "difficult", "confusing",
        "probleme", "problemes", "plainte", "plaintes", "mauvais", "lent",
        "bugue", "retard", "cher", "difficile", "frustration",
    ]

    def __init__(self):
        super().__init__(
            agent_name="market_voc_agent",
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=LLM_CONFIG["max_tokens"],
            temperature=LLM_CONFIG["temperature"],
        )

    async def run(self, state: PipelineState, queries: dict) -> dict:
        self._log_start(state)
        idea = (state.clarified_idea or {}).get("short_pitch", state.name)
        sector = (state.clarified_idea or {}).get("sector", state.sector)
        validated = self._validate_queries(queries, idea, sector)
        country = validated.get("country", "TN")
        language = validated.get("language", "en")

        try:
            tavily_task = self._run_multi_queries(
                fetch_tavily_insights,
                [validated["tavily"], *validated.get("tavily_multi", [])],
                result_key="results",
                source_name="tavily_multi",
            )
            reddit_task = self._run_multi_queries(
                fetch_reddit_voc,
                [validated["reddit"], *validated.get("reddit_multi", [])],
                result_key="results",
                source_name="reddit_multi",
            )
            youtube_task = self._run_multi_queries(
                fetch_youtube_voc,
                [validated["youtube"], *validated.get("youtube_multi", [])],
                result_key="videos",
                source_name="youtube_multi",
            )
            news_task = fetch_newsapi(validated["news"], language)
            wb_task = fetch_worldbank(country)

            tavily, reddit, youtube, news, worldbank = await asyncio.gather(
                tavily_task, reddit_task, youtube_task, news_task, wb_task
            )

            if not reddit.get("results"):
                reddit = await self._run_multi_queries(
                    fetch_reddit_voc,
                    [f"{sector} problems reddit", f"{idea} complaints reddit"],
                    result_key="results",
                    source_name="reddit_fallback",
                )
            if not tavily.get("results"):
                tavily = await self._run_multi_queries(
                    fetch_tavily_insights,
                    [f"{idea} user problems", f"{sector} bad reviews"],
                    result_key="results",
                    source_name="tavily_fallback",
                )

            raw_data = {
                "reddit_priority": reddit,
                "reddit": reddit,
                "tavily": tavily,
                "youtube": youtube,
                "news": news,
                "worldbank": worldbank,
            }

            raw_data_filtered = {
                "reddit_priority": simple_filter(reddit.get("results", []), LLM_LIMITS["max_items"], LLM_LIMITS["snippet_max_chars"]),
                "reddit": simple_filter(reddit.get("results", []), LLM_LIMITS["max_items"], LLM_LIMITS["snippet_max_chars"]),
                "tavily": simple_filter(tavily.get("results", []), LLM_LIMITS["max_items"], LLM_LIMITS["snippet_max_chars"]),
                "youtube": simple_filter(
                    [{"title": v.get("title", ""), "snippet": v.get("description", ""), "url": ""} for v in youtube.get("videos", [])],
                    LLM_LIMITS["max_items"],
                    LLM_LIMITS["snippet_max_chars"],
                ),
                "news": simple_filter(
                    [{"title": a.get("title", ""), "snippet": a.get("description", ""), "url": ""} for a in news.get("articles", [])],
                    LLM_LIMITS["max_items"],
                    LLM_LIMITS["snippet_max_chars"],
                ),
                "worldbank": worldbank,
            }

            payload = json.dumps(raw_data_filtered, ensure_ascii=False, default=str)
            if len(payload) > LLM_LIMITS["max_payload_chars"]:
                payload = payload[:LLM_LIMITS["max_payload_chars"]]

            llm_response = await self._call_llm(
                system_prompt=self._load_prompt("market_voc_agent.txt", state),
                user_prompt=payload,
            )
            data = self._parse_json(llm_response)
            if not data.get("top_voc"):
                data["top_voc"] = self._fallback_voc(raw_data)

            data = self._ensure_output_shape(data, worldbank)
            output = MarketVoc(**data)
            self._log_success(output)
            return output.dict()
        except Exception as e:
            self._log_error(e)
            fallback_worldbank = await fetch_worldbank(country)
            fallback_raw = {
                "reddit_priority": {"results": []},
                "reddit": {"results": []},
                "tavily": {"results": []},
                "youtube": {"videos": []},
                "news": {"articles": []},
                "worldbank": fallback_worldbank,
            }
            data = self._ensure_output_shape(
                {
                    "demand_level": "faible",
                    "demand_summary": "Donnees limitees, fallback local active.",
                    "top_voc": self._fallback_voc(fallback_raw),
                    "personas": [],
                    "macro": fallback_worldbank.get("indicators", {}),
                    "news_signals": [],
                },
                fallback_worldbank,
            )
            return MarketVoc(**data).dict()

    def _validate_queries(self, queries, idea, sector):
        q = dict(queries or {})
        idea = (idea or "").strip() or "user idea"
        sector = (sector or "").strip() or "market"

        q["reddit"] = (q.get("reddit") or f"{idea} problems reddit").strip()
        q["tavily"] = (q.get("tavily") or f"{idea} complaints").strip()
        q["youtube"] = (q.get("youtube") or f"{idea} user review").strip()
        q["news"] = (q.get("news") or f"{sector} bad reviews").strip()
        q["country"] = (q.get("country") or "TN").strip().upper()
        q["language"] = (q.get("language") or "en").strip().lower()

        def _listify(v):
            if isinstance(v, list):
                return [str(x).strip() for x in v if str(x).strip()]
            if isinstance(v, str) and v.strip():
                return [v.strip()]
            return []

        q["reddit_multi"] = _listify(q.get("reddit_multi"))
        q["tavily_multi"] = _listify(q.get("tavily_multi"))
        q["youtube_multi"] = _listify(q.get("youtube_multi"))

        for extra in [f"{idea} problems reddit", f"{idea} complaints", f"{sector} bad reviews"]:
            if extra not in q["reddit_multi"]:
                q["reddit_multi"].append(extra)
            if extra not in q["tavily_multi"]:
                q["tavily_multi"].append(extra)
        return q

    async def _run_multi_queries(
        self,
        fetch_fn: Callable[[str], Awaitable[dict]],
        queries_list: list[str],
        result_key: str = "results",
        source_name: str = "multi",
    ) -> dict:
        clean = []
        seen = set()
        for q in queries_list or []:
            s = str(q).strip()
            if not s:
                continue
            k = s.lower()
            if k in seen:
                continue
            seen.add(k)
            clean.append(s)
        if not clean:
            return {"source": source_name, "queries": [], result_key: []}

        batches = await asyncio.gather(*[fetch_fn(q) for q in clean])
        merged = []
        seen_rows = set()
        for b in batches:
            for row in b.get(result_key, []):
                if result_key == "videos":
                    sig = (
                        str(row.get("title", "")).strip().lower(),
                        str(row.get("channel", "")).strip().lower(),
                    )
                else:
                    sig = (
                        str(row.get("title", "")).strip().lower(),
                        str(row.get("snippet", "")).strip().lower(),
                    )
                if not any(sig) or sig in seen_rows:
                    continue
                seen_rows.add(sig)
                merged.append(row)
        return {"source": source_name, "queries": clean, result_key: merged}

    def _fallback_voc(self, raw_data):
        candidates = []
        for src_name in ("reddit_priority", "reddit", "tavily"):
            for r in raw_data.get(src_name, {}).get("results", []):
                txt = (r.get("snippet") or r.get("title") or "").strip()
                if txt:
                    candidates.append((src_name, txt))

        out = []
        seen = set()
        for src_name, txt in candidates:
            low = txt.lower()
            if not any(kw in low for kw in self._NEG_KW):
                continue
            citation = " ".join(txt.split())[:220]
            key = citation.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(
                {
                    "theme": "User complaints and friction",
                    "recurrence": "faible",
                    "citation": citation,
                    "source": "reddit" if "reddit" in src_name else "tavily",
                }
            )
            if len(out) >= 5:
                break
        return out

    def _ensure_output_shape(self, data: dict, worldbank: dict) -> dict:
        indicators = worldbank.get("indicators", {}) if isinstance(worldbank, dict) else {}
        data.setdefault("demand_level", "faible")
        data.setdefault("demand_summary", "Signals VOC limites; analyse basee sur les donnees disponibles.")
        data.setdefault("top_voc", [])
        data.setdefault("personas", [])
        data.setdefault("macro", indicators or {})
        data.setdefault("news_signals", [])
        return data

    def _load_prompt(self, filename: str, state: PipelineState) -> str:
        try:
            with open(f"prompts/market_analysis/{filename}", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"""Tu es un expert VOC pour : {state.sector}.
Tu recois reddit_priority, reddit, tavily, youtube, news, worldbank.
Priorise reddit_priority pour extraire les pain points utilisateurs.
Retourne UNIQUEMENT un JSON valide :
{{
  "demand_level": "fort|modere|faible|inexistant",
  "demand_summary": "",
  "top_voc": [{{"theme":"","recurrence":"","citation":"","source":""}}],
  "personas": [{{"segment":"","tranche_age":"","comportement":"","pain_points":[],"motivations":[],"signal_niveau":""}}],
  "macro": {{"population":null,"gdp_per_capita":null,"internet_pct":null,"mobile_per100":null,"urban_pct":null,"youth_pct":null}},
  "news_signals": []
}}
Règle absolue : citations reelles extraites des donnees, jamais inventees."""
 