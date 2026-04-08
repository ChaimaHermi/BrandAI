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
from prompts.market_analysis.prompt_keyword_extractor import (
    SYSTEM_PROMPT,
    USER_PROMPT,
)

logger = logging.getLogger("brandai.keyword_extractor")


# KEYWORD BUNDLE — conteneur distribué aux sous-agents
# ═══════════════════════════════════════════════════════════════

@dataclass
class KeywordBundle:
    """
    Conteneur créé une seule fois depuis l'IDEA.
    Chaque sous-agent reçoit uniquement les keywords qui le concernent.

      primary_keywords   → trend_queries (merge) / sizing contexte
      market_keywords    → market_sizing_agent
      competitor_queries → competitor_agent
      voc_keywords       → voc_agent
      trend_keywords     → trend_queries (merge) / trends_agent
    """

    primary_keywords:   list[str] = field(default_factory=list)
    market_keywords:    list[str] = field(default_factory=list)
    competitor_queries: list[str] = field(default_factory=list)
    voc_keywords:       list[str] = field(default_factory=list)
    trend_keywords:     list[str] = field(default_factory=list)

    # ── Accesseurs par agent ──────────────────────────────────

    def for_market_sizing(self) -> dict:
        """Envoyé à market_sizing_agent."""
        return {
            "primary_keywords": self.primary_keywords,
            "market_keywords":  self.market_keywords,
            "trend_keywords":   self.trend_keywords,
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

        user_prompt = USER_PROMPT.format(
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
                raw    = await self._call_groq_reasoning(SYSTEM_PROMPT, user_prompt)
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
            competitor_queries = _clean(data.get("competitor_queries"), 10),
            voc_keywords       = _clean(data.get("voc_keywords"),       6),
            trend_keywords     = _clean(data.get("trend_keywords"),     5),
        )

    def _log_bundle(self, b: KeywordBundle) -> None:
        logger.info(f"  primary_keywords   → {b.primary_keywords}")
        logger.info(f"  market_keywords    → {b.market_keywords}")
        logger.info(f"  competitor_queries → {b.competitor_queries}")
        logger.info(f"  voc_keywords       → {b.voc_keywords}")
        logger.info(f"  trend_keywords     → {b.trend_keywords}")