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
You are a market research expert specialized in keyword extraction for APIs.

Your task: analyze the startup idea and generate SPECIFIC, CONTEXTUAL, and SEARCH-OPTIMIZED keywords.

LANGUAGE RULE:
- The input idea will ALWAYS be in French
- First, internally translate it to English
- Generate ALL keywords in English only

CRITICAL RULES:
- Keywords must be specific to the idea, sector, and country
- Use realistic search patterns (what users actually type)
- Avoid overly generic OR overly complex queries
- Return ONLY valid JSON

QUERY FORMAT RULE:
- All keywords must be 2–5 words maximum
- Do NOT generate full sentences
- Prefer noun-based expressions (avoid verbs when possible)
- Avoid unnecessary words
- Avoid hardcoded years

SEARCH LOGIC RULE:
- Prefer structure: [concept] + [metric]

BALANCE RULE:
- Include a mix of:
  - user intent keywords
  - market/analysis keywords
  - local keywords (country)
  - global keywords

DEDUPLICATION RULE:
- Avoid redundant or very similar keywords
- Each keyword must be distinct and useful

KEYWORD RULES:
  primary_keywords    : core product + user intent
  market_keywords     : market size, revenue, growth
  pricing_keywords    : pricing, cost, fees
  adoption_keywords   : usage, statistics, demand
  competitor_queries  : competitor data extraction queries
  voc_keywords        : short pain points (2–4 words)
  trend_keywords      : trends and industry evolution
  sector_tags         : industry labels

COMPETITOR RULES:
- Generate queries to EXTRACT INFORMATION about competitors (not comparison)
- Focus on retrieving:
  - features
  - pricing
  - user reviews
  - strengths and weaknesses
  - platform descriptions

- Include BOTH:
  1. Global competitors (international platforms)
  2. Local or country-specific competitors

- At least one query must include the country
- Use the country input to localize queries
- Do NOT generate comparison queries (no "vs")
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

Based on this SPECIFIC idea, generate contextual search keywords.

Return this EXACT JSON structure:

{{
  "primary_keywords": [
    "<specific keyword 1>",
    "<specific keyword 2>",
    "<specific keyword 3>",
    "<specific keyword 4>",
    "<specific keyword 5>"
  ],

  "market_keywords": [
    "<market size keyword>",
    "<industry revenue keyword>",
    "<growth keyword>",
    "<CAGR keyword>",
    "<market value keyword>"
  ],

  "pricing_keywords": [
    "<pricing keyword>",
    "<cost keyword>",
    "<fee keyword>",
    "<pricing model keyword>"
  ],

  "adoption_keywords": [
    "<user statistics keyword>",
    "<adoption rate keyword>",
    "<usage keyword>",
    "<demand keyword>"
  ],

  "competitor_queries": [
    "<competitor features>",
    "<competitor pricing>",
    "<competitor reviews>",
    "<solution category country>"
  ],

  "voc_keywords": [
    "<pain point>",
    "<complaint>",
    "<problem>",
    "<frustration>",
    "<issue>"
  ],

  "trend_keywords": [
    "<trend keyword>",
    "<growth keyword>",
    "<adoption trend>",
    "<industry evolution>"
  ],

  "sector_tags": [
    "<industry tag 1>",
    "<industry tag 2>",
    "<industry tag 3>"
  ]
}}

Return ONLY the JSON. No explanation.
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
            for x in raw[:n]:
                if not isinstance(x, str):
                    continue
                x = re.sub(r"\s+", " ", x).strip()
                if x:
                    result.append(x)
            return result

        return KeywordBundle(
            primary_keywords   = _clean(data.get("primary_keywords"),   5),
            market_keywords    = _clean(data.get("market_keywords"),    5),
            pricing_keywords   = _clean(data.get("pricing_keywords"),   4),
            adoption_keywords  = _clean(data.get("adoption_keywords"),  4),
            competitor_queries = _clean(data.get("competitor_queries"), 4),
            voc_keywords       = _clean(data.get("voc_keywords"),       5),
            trend_keywords     = _clean(data.get("trend_keywords"),     4),
            sector_tags        = _clean(data.get("sector_tags"),        3),
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