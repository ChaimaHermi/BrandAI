"""
agents/market_analysis/orchestrator/keyword_extractor.py
=========================================================
Responsabilité unique : extraire les mots-clés depuis l'IDEA via 1 appel LLM.

Le LLM génère des keywords CONTEXTUELS basés sur l'idée réelle.
Pas de templates — chaque idée produit des keywords différents.

Flow :
  IDEA → KeywordExtractor.extract() → KeywordBundle → [4 sous-agents]
"""

import json
import logging
import os
import re
from dataclasses import asdict, dataclass, field

import httpx
from agents.base_agent import BaseAgent, PipelineState
from config.market_analysis_config import LLM_CONFIG

logger = logging.getLogger("brandai.keyword_extractor")


# ═══════════════════════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════════════════════
_SYSTEM = """\
You are a senior market intelligence analyst specialized in competitor discovery.

Your task: generate HIGHLY RELEVANT, CONTEXTUAL, and GEO-AWARE search queries to find competitors.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORE OBJECTIVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate search queries that help discover:

- platforms
- applications
- services
- products

related to the given startup idea.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
SOLUTION TYPE ADAPTATION (CRITICAL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before generating queries, identify the nature of the solution:

- digital product → apps, platforms, software, tools
- physical product → products, brands, manufacturers, suppliers
- service → services, providers, companies, agencies
- hybrid → combine appropriately

Queries MUST match the actual type of solution.

DO NOT force "apps" or "platforms" if not relevant.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Queries MUST be adapted to the idea dynamically
- Queries MUST reflect real user search behavior
- Queries MUST be specific (not generic)
- Return ONLY valid JSON

━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMAT RULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 2–5 words per query
- No full sentences
- No unnecessary words

━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRICT PROHIBITIONS (CRITICAL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

DO NOT generate queries related to:

- strategy
- marketing
- monetization
- pricing models
- trends
- statistics
- "how to" queries

These are NOT competitor discovery queries.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPETITOR DISCOVERY RULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━

All queries MUST aim to:

- find existing solutions
- identify similar products or services
- discover competitors

Queries should naturally match how users search for alternatives.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUALITY SIGNAL (CRITICAL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Queries should naturally lead to discovering:

- popular solutions
- widely used products or services
- well-known brands or companies

Use natural user search patterns such as:
- best
- top
- popular
- alternatives
- similar

DO NOT explicitly use "top competitors"

Queries must implicitly target high-quality, real-world solutions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
GEO STRUCTURE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate EXACTLY 10 queries:

1–4 → LOCAL (specific to the target country)
5–10 → GLOBAL (no geographic reference)

━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOCAL RULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Local queries MUST:

- explicitly include the target country
- reflect real usage patterns
- explore different angles:
  → product type
  → user intent
  → ecosystem / startups
  → usage context

━━━━━━━━━━━━━━━━━━━━━━━━━━━
GLOBAL RULE (CRITICAL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Global queries MUST:

- NOT include any country, region, or continent
- be fully geography-neutral
- focus on discovering similar solutions worldwide

If a global query contains a location → it is INVALID

━━━━━━━━━━━━━━━━━━━━━━━━━━━
DIVERSITY RULE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Each query MUST:

- be unique
- use different wording
- represent a different search intent

Avoid paraphrasing.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
SELF VALIDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before returning:

- Ensure EXACTLY 10 queries
- Ensure correct order (4 local + 6 global)
- Ensure no geography in global queries
- Ensure no forbidden query types
- Ensure all queries are discovery-oriented

━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL RULE
━━━━━━━━━━━━━━━━━━━━━━━━━━━

The system must adapt to ANY startup idea without relying on predefined examples.
"""

_USER = """\
Startup idea to analyze:

- Name/Pitch      : {short_pitch}
- Description     : {solution_description}
- Problem solved  : {problem}
- Target users    : {target_users}
- Sector          : {sector}
- Country         : {country}
- Country/Market  : {country_code}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate HIGH-QUALITY, CONTEXTUAL search keywords.

Focus on identifying REAL existing solutions similar to this idea.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTEXT UNDERSTANDING (IMPORTANT)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

First, understand:

- what type of solution this is (product, service, platform, etc.)
- how users would search for similar existing solutions
- what real competitors or alternatives might exist

Then generate queries aligned with that understanding.
━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATA QUALITY REQUIREMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATA QUALITY REQUIREMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Keywords must resemble real-world search queries used to retrieve actionable market data.

They should prioritize:

- concrete and commonly searched phrases
- measurable signals (market size, demand, growth, user behavior)
- terminology used by analysts, researchers, and real users

Keywords must be directly usable in search engines, APIs, or data sources.

They should closely match phrases that would realistically return results,
not abstract or artificial wording.

Prefer explicit, complete, and natural search queries
over shortened or conceptual expressions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRENDS & RISKS COVERAGE (CRITICAL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Keywords must enable discovery of:

- market trends and growth signals
- industry challenges and barriers
- risks and threats affecting the market
- regulatory or legal constraints

Keywords must explicitly cover BOTH:

- positive signals (growth, trends, demand)
- negative signals (risks, challenges, problems, barriers)

Ensure that:

- at least one keyword clearly targets risks or negative outcomes
- multiple keywords reflect trends and growth dynamics
- keywords remain natural, search-oriented, and realistic

Avoid generating keywords focused only on positive or descriptive aspects.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
VOC-SPECIFIC REQUIREMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━

VOC keywords must focus on:

- user problems
- frustrations
- complaints
- reviews
- real user experiences

They should reflect how users express issues in forums, reviews, or discussions.

Avoid:

- generic or marketing-style terms
- product features without user context
- abstract or descriptive wording without real user signal
━━━━━━━━━━━━━━━━━━━━━━━━━━━
VOC-SPECIFIC REQUIREMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━

VOC keywords must focus on:

- user problems
- frustrations
- complaints
- reviews
- real user experiences

They should reflect how users express issues in forums, reviews, or discussions.

Avoid:

- generic, descriptive, or marketing-style terms
- product features without user context
- abstract concepts that do not lead to real user feedback

━━━━━━━━━━━━━━━━━━━━━━━━━━━
GENERAL AVOIDANCE RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Avoid:

- vague, abstract, or conceptual wording
- product feature descriptions without market context
- terms that do not lead to quantifiable or actionable insights

━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT (STRICT JSON)
━━━━━━━━━━━━━━━━━━━━━━━━━━━

{{
  "primary_keywords": ["<keyword>", "<keyword>", "<keyword>", "<keyword>", "<keyword>"],

  "market_keywords": ["<keyword>", "<keyword>", "<keyword>", "<keyword>", "<keyword>"],

  "pricing_keywords": ["<keyword>", "<keyword>", "<keyword>", "<keyword>", "<keyword>"],

  "adoption_keywords": ["<keyword>", "<keyword>", "<keyword>", "<keyword>", "<keyword>"],

  "competitor_queries": [
    "<local query 1>",
    "<local query 2>",
    "<local query 3>",
    "<local query 4>",
    "<global query 1>",
    "<global query 2>",
    "<global query 3>",
    "<global query 4>",
    "<global query 5>",
    "<global query 6>"
  ],

  "voc_keywords": ["<keyword>", "<keyword>", "<keyword>", "<keyword>", "<keyword>", "<keyword>"],

  "trend_keywords": ["<keyword>", "<keyword>", "<keyword>", "<keyword>", "<keyword>"],

  "sector_tags": ["<tag>", "<tag>", "<tag>"]
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPORTANT
━━━━━━━━━━━━━━━━━━━━━━━━━━━

- EXACTLY 10 competitor_queries required
- order MUST be:
  → 4 local
  → 6 global

- queries MUST be adapted to the idea dynamically
- queries MUST be diverse and non-repetitive
- queries MUST reflect real user search behavior
- output must be valid JSON only
- no explanation
"""
# ═══════════════════════════════════════════════════════════════
# KEYWORD BUNDLE — conteneur distribué aux sous-agents
# ═══════════════════════════════════════════════════════════════

@dataclass
class KeywordBundle:
    """
    Conteneur créé une seule fois depuis l'IDEA.
    Chaque sous-agent reçoit uniquement les keywords qui le concernent.

      primary_keywords   → market_sizing_agent  (Google Trends)
      market_keywords    → market_sizing_agent  (Tavily market research)
      pricing_keywords   → market_sizing_agent  (TAM bottom-up)
      adoption_keywords  → market_sizing_agent  (World Bank enrichi)
      competitor_queries → competitor_agent     (Serper / Tavily)
      voc_keywords       → voc_agent            (Reddit / YouTube / G2)
      trend_keywords     → trends_agent         (GNews / NewsAPI)
      sector_tags        → tous les agents      (contexte)
    """

    primary_keywords:   list[str] = field(default_factory=list)
    market_keywords:    list[str] = field(default_factory=list)
    pricing_keywords:   list[str] = field(default_factory=list)
    adoption_keywords:  list[str] = field(default_factory=list)
    competitor_queries: list[str] = field(default_factory=list)
    voc_keywords:       list[str] = field(default_factory=list)
    trend_keywords:     list[str] = field(default_factory=list)
    sector_tags:        list[str] = field(default_factory=list)

    # ── Accesseurs par agent ──────────────────────────────────

    def for_market_sizing(self) -> dict:
        """Envoyé à market_sizing_agent."""
        return {
            "primary_keywords":  self.primary_keywords,
            "market_keywords":   self.market_keywords,
            "pricing_keywords":  self.pricing_keywords,
            "adoption_keywords": self.adoption_keywords,
            "trend_keywords":    self.trend_keywords,
            "sector_tags":       self.sector_tags,
        }

    def for_competitor(self) -> list[str]:
        """Envoyé à competitor_agent."""
        return self.competitor_queries

    def for_voc(self) -> dict:
        """Envoyé à voc_agent."""
        return {
            "voc_keywords":   self.voc_keywords,
            "trend_keywords": self.trend_keywords,
        }

    def for_trends(self) -> dict:
        """Envoyé à trends_agent."""
        return {
            "primary_keywords": self.primary_keywords,
            "trend_keywords":   self.trend_keywords,
        }

    def to_dict(self) -> dict:
        return asdict(self)

    def is_empty(self) -> bool:
        return not any([
            self.primary_keywords,
            self.market_keywords,
            self.voc_keywords,
            self.trend_keywords,
        ])


# ═══════════════════════════════════════════════════════════════
# KEYWORD EXTRACTOR
# ═══════════════════════════════════════════════════════════════

class KeywordExtractor(BaseAgent):
    """
    1 appel LLM → KeywordBundle contextuel.

    Utilise _call_groq_reasoning car gpt-oss-120b retourne
    content="" avec le JSON dans reasoning_content.
    """

    def __init__(self):
        # Sortie JSON longue (8 listes) : 800 tokens coupait la réponse → JSON invalide
        _cap = min(LLM_CONFIG.get("max_tokens") or 4096, 4096)
        super().__init__(
            agent_name     = "keyword_extractor",
            llm_model      = LLM_CONFIG["model"],
            llm_max_tokens = max(1500, _cap),
            temperature    = 0.1,
        )
        self._groq_keys = [
            k for k in [
                os.getenv("GROQ_API_KEY",   ""),
                os.getenv("GROQ_API_KEY_2", ""),
                os.getenv("GROQ_API_KEY_3", ""),
            ] if k
        ]

    async def run(self, state: PipelineState) -> PipelineState:
        raise NotImplementedError("Utiliser extract(idea).")

    async def extract(self, idea: dict) -> KeywordBundle:
        """
        Point d'entrée principal.
        3 tentatives avant fallback bundle vide.
        """
        logger.info(f"[keyword_extractor] '{idea.get('short_pitch', '?')}'")

        country = (idea.get("country") or "").strip() or (idea.get("country_code") or "US")

        user_prompt = _USER.format(
            short_pitch          = idea.get("short_pitch",          "")[:100],
            solution_description = idea.get("solution_description", "")[:150],
            problem              = idea.get("problem",              "")[:100],
            target_users         = idea.get("target_users",         "")[:80],
            sector               = idea.get("sector",               "")[:50],
            country              = country[:80],
            country_code         = idea.get("country_code",         "US"),
        )

        for attempt in range(3):
            try:
                raw    = await self._call_groq_reasoning(_SYSTEM, user_prompt)
                data   = self._parse_json_robust(raw)
                bundle = self._build_bundle(data)
                self._log_bundle(bundle)
                return bundle

            except Exception as e:
                logger.warning(f"[keyword_extractor] tentative {attempt+1}/3 échouée : {e}")

        # Fallback : bundle vide — jamais de valeurs inventées
        logger.error("[keyword_extractor] toutes les tentatives échouées → bundle vide")
        return KeywordBundle()

    # ── Appel Groq compatible reasoning ──────────────────────

    async def _call_groq_reasoning(self, system: str, user: str) -> str:
        """
        Appel HTTP direct à Groq.
        Lit content en priorité, puis reasoning_content.
        """
        if not self._groq_keys:
            raise RuntimeError("Aucune GROQ_API_KEY dans .env")

        last_err = None
        for key in self._groq_keys:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {key}",
                            "Content-Type":  "application/json",
                        },
                        json={
                            "model":            self.llm_model,
                            "max_tokens":       self.llm_max_tokens,
                            "temperature":      self.temperature,
                            "reasoning_effort": "medium",
                            "messages": [
                                {"role": "system", "content": system},
                                {"role": "user",   "content": user},
                            ],
                        },
                    )
                    resp.raise_for_status()
                    message = resp.json()["choices"][0]["message"]

                # Priorité 1 : content (réponse normale)
                content = (message.get("content") or "").strip()
                if content:
                    return content

                # Priorité 2 : reasoning_content (gpt-oss-120b)
                reasoning = (message.get("reasoning_content") or "").strip()
                if reasoning:
                    return reasoning

                raise RuntimeError(f"Réponse Groq vide — message: {message}")

            except Exception as e:
                last_err = e
                continue

        raise RuntimeError(f"Toutes les clés Groq ont échoué : {last_err}")

    # ── JSON parser — 3 stratégies ────────────────────────────

    def _parse_json_robust(self, raw: str) -> dict:
        if not raw or not raw.strip():
            raise ValueError("Réponse LLM vide")

        # 1. Direct
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            pass

        # 2. Strip backticks markdown
        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # 3. Premier objet JSON (non greedy sur la profondeur : du premier { au dernier } équilibré)
        brace_start = cleaned.find("{")
        if brace_start >= 0:
            depth = 0
            for i, ch in enumerate(cleaned[brace_start:], start=brace_start):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(cleaned[brace_start : i + 1])
                        except json.JSONDecodeError:
                            break

        logger.error(f"[keyword_extractor] JSON introuvable dans : {repr(raw[:300])}")
        raise ValueError("JSON introuvable dans la réponse LLM")

    # ── Bundle builder ────────────────────────────────────────

    def _build_bundle(self, data: dict) -> KeywordBundle:
        def _clean(raw, n: int) -> list[str]:
            if not isinstance(raw, list):
                return []

            result = []
            seen = set()

            for x in raw:
                if not isinstance(x, str):
                    continue

                x = re.sub(r"\s+", " ", x).strip()

                if not x:
                    continue

                key = x.lower()
                if key in seen:
                    continue

                seen.add(key)
                result.append(x)

                if len(result) >= n:
                    break

            return result

        return KeywordBundle(
            primary_keywords   = _clean(data.get("primary_keywords"),   6),
            market_keywords    = _clean(data.get("market_keywords"),    6),
            pricing_keywords   = _clean(data.get("pricing_keywords"),   5),
            adoption_keywords  = _clean(data.get("adoption_keywords"),  5),
            competitor_queries = _clean(data.get("competitor_queries"), 10),
            voc_keywords       = _clean(data.get("voc_keywords"),       6),
            trend_keywords     = _clean(data.get("trend_keywords"),     5),
            sector_tags        = _clean(data.get("sector_tags"),        4),
        )

    def _log_bundle(self, b: KeywordBundle) -> None:
        logger.info(f"  primary_keywords   → {b.primary_keywords}")
        logger.info(f"  market_keywords    → {b.market_keywords}")
        logger.info(f"  pricing_keywords   → {b.pricing_keywords}")
        logger.info(f"  adoption_keywords  → {b.adoption_keywords}")
        logger.info(f"  competitor_queries → {b.competitor_queries}")
        logger.info(f"  voc_keywords       → {b.voc_keywords}")
        logger.info(f"  trend_keywords     → {b.trend_keywords}")
        logger.info(f"  sector_tags        → {b.sector_tags}")