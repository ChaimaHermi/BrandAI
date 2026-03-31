# ══════════════════════════════════════════════════════════════
# agents/market_analysis/subagents/competitor_agent.py
# Robuste : multi-query Tavily + fallback déterministe + enrichissement
# ══════════════════════════════════════════════════════════════

import asyncio
import json
import re
from pathlib import Path

from agents.base_agent import BaseAgent, PipelineState
from config.market_analysis_config import LLM_CONFIG, LLM_LIMITS
from tools.market_analysis.subagents_tools.competitor_tools import (
    fetch_serp_competitors,
    fetch_serp_maps,
    fetch_tavily_competitor_insights,
)
from utils.simple_filter import simple_filter

BASE_DIR = Path(__file__).resolve().parents[3]
PROMPTS_DIR = BASE_DIR / "prompts" / "market_analysis"


class CompetitorAgent(BaseAgent):
    _NEGATIVE_KW = [
        "bug", "buggy", "crash", "crashes", "issue", "issues", "problem", "problems",
        "complaint", "complaints", "bad", "worst", "slow", "lag", "broken", "error",
        "expensive", "limited", "missing", "refund", "delay", "late", "spam",
        "lent", "bugue", "buguee", "probleme", "problemes", "plainte", "plaintes",
        "mauvais", "instable", "cher", "limite", "limitee", "manque", "retard",
    ]
    _POSITIVE_KW = [
        "simple", "easy", "fast", "reliable", "popular", "trusted", "intuitive",
        "complet", "fiable", "rapide", "officiel", "best", "top", "excellent",
    ]
    _NOISY_PATTERNS = (
        "###", "| |", "rated 1 out of 5", "how is the trustscore",
        "troubleshoot", "site:reddit.com", "raw but fast",
    )
    _WEAKNESS_HINTS = (
        "absence", "faible", "faibles", "peu", "difficile", "complexe", "probleme", "problème",
        "retard", "lente", "lent", "instable", "manque", "limite", "limité", "limitee",
        "cher", "coût", "cout", "erreur", "frustration", "support lent", "support faible",
    )
    _BOILERPLATE_PATTERNS = (
        "page d'accueil", "mentions legales", "politique de confidentialite", "politique de confidentialité",
        "cookies", "tous droits reserves", "copyright", "applications sur google play", "app store",
        "plateforme", "est une plateforme", "leader", "solution complete", "solution complète",
    )

    def __init__(self):
        super().__init__(
            agent_name="competitor_agent",
            llm_model=LLM_CONFIG["model"],
            llm_max_tokens=LLM_CONFIG["max_tokens"],
            temperature=LLM_CONFIG["temperature"],
        )

    async def run(self, state: PipelineState, queries: dict) -> dict:
        self._log_start(state)
        country = queries.get("country", "TN")
        base_query = (queries.get("tavily") or "").strip()

        try:
            tavily_queries = self._build_tavily_queries(base_query, queries.get("tavily_multi"))
            tasks = [
                fetch_serp_competitors(queries.get("competitors", ""), country),
                fetch_serp_maps(queries.get("maps", ""), country),
                *[fetch_tavily_competitor_insights(q) for q in tavily_queries],
            ]
            all_results = await asyncio.gather(*tasks)
            serp_search = all_results[0]
            serp_maps = all_results[1]
            tavily_batches = all_results[2:]

            tavily_merged = {
                "source": "tavily_merged",
                "queries": tavily_queries,
                "results": self._merge_tavily_results(tavily_batches),
            }
            raw_data = {
                "serp_search": serp_search,
                "serp_maps": serp_maps,
                "tavily_batches": tavily_batches,
                "tavily_merged": tavily_merged,
            }

            llm_data = await self._call_llm_safely(state, raw_data)
            final_data = self._post_process(llm_data, raw_data)
            self._log_success(final_data)
            return final_data
        except Exception as e:
            self._log_error(e)
            # Fallback dur sans LLM
            fallback_raw = {
                "serp_search": await fetch_serp_competitors(queries.get("competitors", ""), country),
                "serp_maps": await fetch_serp_maps(queries.get("maps", ""), country),
                "tavily_merged": {"results": []},
            }
            return self._post_process({}, fallback_raw)

    async def _call_llm_safely(self, state: PipelineState, raw_data: dict) -> dict:
        try:
            prompt = self._load_prompt("competitor_agent.txt", state)
            raw_data_filtered = {
                "serp_search": simple_filter(raw_data.get("serp_search", {}).get("results", []), LLM_LIMITS["max_items"], LLM_LIMITS["snippet_max_chars"]),
                "serp_maps": simple_filter(
                    [
                        {
                            "title": r.get("name", ""),
                            "snippet": f"rating={r.get('rating')} reviews={r.get('reviews')} {r.get('address', '')}",
                            "url": r.get("website", ""),
                        }
                        for r in raw_data.get("serp_maps", {}).get("results", [])
                    ],
                    LLM_LIMITS["max_items"],
                    LLM_LIMITS["snippet_max_chars"],
                ),
                "tavily": simple_filter(raw_data.get("tavily_merged", {}).get("results", []), LLM_LIMITS["max_items"], LLM_LIMITS["snippet_max_chars"]),
            }
            payload = json.dumps(raw_data_filtered, ensure_ascii=False, default=str)
            if len(payload) > LLM_LIMITS["max_payload_chars"]:
                payload = payload[:LLM_LIMITS["max_payload_chars"]]
            llm_response = await self._call_llm(
                system_prompt=prompt,
                user_prompt=payload,
            )
            return self._parse_json(llm_response)
        except Exception:
            return {}

    def _build_tavily_queries(self, base_query: str, multi) -> list[str]:
        queries = []
        if base_query:
            queries.append(base_query)
            queries.append(f"site:reddit.com {base_query} complaints problems bad reviews")
            queries.append(f"{base_query} vs alternatives comparison")
            queries.append(f"{base_query} user frustrations")
        if isinstance(multi, list):
            queries.extend([str(q).strip() for q in multi if str(q).strip()])
        elif isinstance(multi, str) and multi.strip():
            queries.extend([q.strip() for q in multi.split("||") if q.strip()])
        return self._dedup_keep_order(queries)[:8]

    def _merge_tavily_results(self, batches: list[dict]) -> list[dict]:
        seen = set()
        merged = []
        for b in batches:
            for r in b.get("results", []):
                title = (r.get("title") or "").strip()
                snippet = (r.get("snippet") or "").strip()
                key = (title.lower(), snippet.lower())
                if key in seen or not (title or snippet):
                    continue
                seen.add(key)
                merged.append({"title": title, "snippet": snippet})
        return merged

    def _post_process(self, llm_data: dict, raw_data: dict) -> dict:
        serp_results = raw_data.get("serp_search", {}).get("results", [])
        maps_results = raw_data.get("serp_maps", {}).get("results", [])
        tavily_results = raw_data.get("tavily_merged", {}).get("results", [])

        serp_index = self._build_serp_index(serp_results)
        maps_index = self._build_maps_index(maps_results)

        llm_competitors = llm_data.get("top_competitors", []) if isinstance(llm_data, dict) else []
        competitors = []
        for c in llm_competitors:
            enriched = self._enrich_competitor(c, serp_index, maps_index, tavily_results)
            if enriched:
                competitors.append(enriched)

        # Fallback déterministe si LLM insuffisant
        if len(competitors) < 3:
            competitors = self._merge_with_fallback_competitors(competitors, serp_results, maps_index, tavily_results)

        competitors = self._dedup_competitors(competitors)[:5]
        if len(competitors) < 3:
            competitors.extend(self._build_minimum_competitors(serp_results, maps_index)[: 3 - len(competitors)])

        with_weak = sum(1 for c in competitors if c.get("weaknesses"))
        opportunite_niveau = "fenetre_ouverte" if with_weak >= 2 else "partielle" if with_weak == 1 else "saturee"
        opportunite_summary = (
            "Plusieurs faiblesses concurrentes exploitables ont ete detectees."
            if with_weak >= 2 else
            "Quelques signaux de faiblesse existent mais la differenciation reste partielle."
            if with_weak == 1 else
            "Faiblesses publiques limitees; valider par interviews utilisateurs."
        )

        return {
            "top_competitors": competitors,
            "opportunite_niveau": llm_data.get("opportunite_niveau", opportunite_niveau),
            "opportunite_summary": llm_data.get("opportunite_summary", opportunite_summary),
        }

    def _enrich_competitor(self, c: dict, serp_index: dict, maps_index: dict, tavily_results: list[dict]) -> dict | None:
        name = self._clean_name(c.get("nom", ""))
        if not name:
            return None
        k = name.lower()
        serp = serp_index.get(k, {})
        maps = maps_index.get(k, {})

        weaknesses = c.get("weaknesses") or self._extract_weaknesses(name, tavily_results)
        weaknesses = self._clean_weaknesses(weaknesses)[:4]
        strengths = c.get("key_strengths") or self._extract_strengths(name, tavily_results)
        strengths = self._dedup_keep_order([s for s in (self._sanitize_issue_text(x) for x in strengths) if s])[:4]

        website = c.get("website") or serp.get("website", "")
        desc = c.get("description") or serp.get("description", "") or c.get("positioning", "")
        source = c.get("source") or ("serp+tavily" if website else "tavily")
        rating = maps.get("rating")

        return {
            "nom": name,
            "type": c.get("type") or ("digital" if website else "local"),
            "website": website,
            "description": desc[:220],
            "source": source,
            "rating": rating,
            "faiblesse_principale": c.get("faiblesse_principale") or (
                weaknesses[0] if weaknesses else "Non documente dans les sources disponibles"
            ),
            "weaknesses": weaknesses,
            "key_strengths": strengths,
            "positioning": c.get("positioning") or desc[:180],
        }

    def _build_serp_index(self, serp_results: list[dict]) -> dict:
        out = {}
        for r in serp_results:
            name = self._clean_name(r.get("title", ""))
            if not name:
                continue
            out[name.lower()] = {
                "website": r.get("url", ""),
                "description": (r.get("snippet") or "")[:220],
            }
        return out

    def _build_maps_index(self, maps_results: list[dict]) -> dict:
        out = {}
        for m in maps_results:
            name = self._clean_name(m.get("name", ""))
            if not name:
                continue
            out[name.lower()] = {"rating": m.get("rating"), "reviews": m.get("reviews")}
        return out

    def _extract_weaknesses(self, name: str, snippets: list[dict]) -> list[str]:
        name_tokens = [t for t in re.split(r"\W+", name.lower()) if len(t) > 2]
        scored = []
        for r in snippets:
            text = f"{r.get('title','')} {r.get('snippet','')}".lower()
            if name_tokens and not any(t in text for t in name_tokens):
                continue
            hit_count = sum(1 for kw in self._NEGATIVE_KW if kw in text)
            if hit_count == 0:
                continue
            extract = self._extract_fragment(text, self._NEGATIVE_KW, 150)
            extract = self._sanitize_issue_text(extract)
            if extract:
                scored.append((hit_count, extract))
        scored.sort(key=lambda x: x[0], reverse=True)
        return self._clean_weaknesses([x[1] for x in scored[:4]])

    def _extract_strengths(self, name: str, snippets: list[dict]) -> list[str]:
        name_tokens = [t for t in re.split(r"\W+", name.lower()) if len(t) > 2]
        out = []
        for r in snippets:
            text = f"{r.get('title','')} {r.get('snippet','')}".lower()
            if name_tokens and not any(t in text for t in name_tokens):
                continue
            if not any(kw in text for kw in self._POSITIVE_KW):
                continue
            frag = self._extract_fragment(text, self._POSITIVE_KW, 130)
            frag = self._sanitize_issue_text(frag)
            if frag and frag not in out:
                out.append(frag)
            if len(out) >= 4:
                break
        return out

    def _merge_with_fallback_competitors(self, current: list[dict], serp_results: list[dict], maps_index: dict, tavily_results: list[dict]) -> list[dict]:
        out = list(current)
        existing = {self._clean_name(c.get("nom", "")).lower() for c in out}
        for r in serp_results:
            name = self._clean_name(r.get("title", ""))
            if not name or name.lower() in existing:
                continue
            base = {
                "nom": name,
                "type": "digital" if r.get("url") else "local",
                "website": r.get("url", ""),
                "description": (r.get("snippet") or "")[:220],
                "source": "serp",
                "rating": maps_index.get(name.lower(), {}).get("rating"),
                "weaknesses": self._extract_weaknesses(name, tavily_results)[:4],
                "key_strengths": self._extract_strengths(name, tavily_results)[:4],
                "positioning": (r.get("snippet") or "")[:180],
            }
            base["faiblesse_principale"] = (
                base["weaknesses"][0] if base["weaknesses"] else "Non documente dans les sources disponibles"
            )
            out.append(base)
            existing.add(name.lower())
            if len(out) >= 5:
                break
        return out

    def _build_minimum_competitors(self, serp_results: list[dict], maps_index: dict) -> list[dict]:
        out = []
        for r in serp_results[:5]:
            name = self._clean_name(r.get("title", ""))
            if not name:
                continue
            out.append({
                "nom": name,
                "type": "digital" if r.get("url") else "local",
                "website": r.get("url", ""),
                "description": (r.get("snippet") or "")[:220],
                "source": "serp",
                "rating": maps_index.get(name.lower(), {}).get("rating"),
                "faiblesse_principale": "Non documente dans les sources disponibles",
                "weaknesses": [],
                "key_strengths": [],
                "positioning": (r.get("snippet") or "")[:180],
            })
        return out

    def _dedup_competitors(self, competitors: list[dict]) -> list[dict]:
        seen = set()
        out = []
        for c in competitors:
            name = self._clean_name(c.get("nom", ""))
            k = name.lower()
            if not name or k in seen:
                continue
            c["nom"] = name
            seen.add(k)
            out.append(c)
        return out

    def _clean_name(self, raw: str) -> str:
        s = (raw or "").strip()
        if not s:
            return ""
        s = re.sub(r"\s+", " ", s)
        s = re.split(r"\s[-|–:]\s", s)[0].strip()
        s = s.replace("Applications sur Google Play", "").strip(" -|:")
        return s[:90]

    def _extract_fragment(self, text: str, kws: list[str], width: int) -> str:
        idx = -1
        for kw in kws:
            i = text.find(kw)
            if i != -1:
                idx = i
                break
        if idx == -1:
            return ""
        frag = text[max(0, idx - 45): idx + width].strip()
        return re.sub(r"\s+", " ", frag)[:150]

    def _sanitize_issue_text(self, text: str) -> str:
        s = re.sub(r"\s+", " ", str(text or "")).strip()
        if not s:
            return ""
        s = re.sub(r"^[#>\-\*\|\s]+", "", s).strip()
        s = re.sub(r"\s*[|#]{1,}\s*", " ", s).strip()
        low = s.lower()
        if any(p in low for p in self._NOISY_PATTERNS):
            return ""
        if self._looks_like_boilerplate(low):
            return ""
        # Remove heavily polluted fragments with too many separators.
        if s.count("|") >= 2 or s.count("...") >= 2 or s.count("#") >= 1:
            return ""
        if re.search(r"https?://|www\.", low):
            return ""
        # Keep concise readable sentences only.
        tokens = [t for t in re.split(r"\s+", s) if t]
        if len(tokens) < 5:
            return ""
        if self._is_repetitive(tokens):
            return ""
        if len(tokens) > 30:
            s = " ".join(tokens[:30]).rstrip(" ,;:-") + "..."
        return s

    def _clean_weaknesses(self, weaknesses: list[str]) -> list[str]:
        cleaned = []
        for w in weaknesses or []:
            s = self._sanitize_issue_text(w)
            if not s:
                continue
            if self._is_actionable_weakness(s):
                cleaned.append(s)
        return self._dedup_keep_order(cleaned)

    def _is_actionable_weakness(self, text: str) -> bool:
        low = text.lower()
        if any(kw in low for kw in self._NEGATIVE_KW):
            return True
        return any(hint in low for hint in self._WEAKNESS_HINTS)

    def _looks_like_boilerplate(self, low: str) -> bool:
        if any(p in low for p in self._BOILERPLATE_PATTERNS):
            # Accept only if there is a clear negative signal too.
            return not any(kw in low for kw in self._NEGATIVE_KW) and not any(h in low for h in self._WEAKNESS_HINTS)
        return False

    def _is_repetitive(self, tokens: list[str]) -> bool:
        if not tokens:
            return True
        norm = [re.sub(r"[^\wàâçéèêëîïôûùüÿñæœ-]", "", t.lower()) for t in tokens]
        norm = [t for t in norm if t]
        if not norm:
            return True
        uniq_ratio = len(set(norm)) / len(norm)
        return uniq_ratio < 0.45

    def _dedup_keep_order(self, items: list[str]) -> list[str]:
        seen = set()
        out = []
        for x in items:
            k = x.lower().strip()
            if not k or k in seen:
                continue
            seen.add(k)
            out.append(x.strip())
        return out

    def _load_prompt(self, filename: str, state: PipelineState) -> str:
        try:
            with open(PROMPTS_DIR / filename, encoding="utf-8") as f:
                content = f.read()
            if "website" not in content:
                raise ValueError("Prompt incomplet")
            return content
        except (FileNotFoundError, ValueError):
            return f"""Tu es un expert en intelligence concurrentielle pour : {state.sector}.
Tu recois serp_search, serp_maps, tavily_batches, tavily_merged.
Priorite: extraire nom, website, description, faiblesses et forces reelles.
Retourne UNIQUEMENT un JSON valide:
{{
  "top_competitors": [{{
    "nom": "",
    "type": "digital|local|regional|international",
    "website": "",
    "description": "",
    "source": "serp|tavily|serp+tavily",
    "rating": null,
    "faiblesse_principale": "snippet negatif ou 'Non documente dans les sources disponibles'",
    "weaknesses": [],
    "key_strengths": [],
    "positioning": ""
  }}],
  "opportunite_niveau": "fenetre_ouverte|partielle|saturee",
  "opportunite_summary": ""
}}"""