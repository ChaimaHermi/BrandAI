# ══════════════════════════════════════════════════════════════
#  agents/base_agent.py
#  Classe mère de tous les agents du pipeline
# ══════════════════════════════════════════════════════════════

import asyncio
import json
import logging
import re
import time
from abc import ABC, abstractmethod

from langchain_core.messages import HumanMessage, SystemMessage
from llm.llm_rotator import LLMRotator


# ══════════════════════════════════════════════════════════════
# Pipeline State
# ══════════════════════════════════════════════════════════════

class PipelineState:

    def __init__(self, idea_id, name, sector, description, target_audience=""):

        self.idea_id         = idea_id
        self.name            = name
        self.sector          = sector
        self.description     = description
        self.target_audience = target_audience

        self.clarified_idea  = {}
        self.market_analysis = {}
        self.brand_identity  = {}
        self.content         = {}

        self.status  = "running"
        self.errors  = []

        self.started_at = time.time()

    def to_dict(self):
        return {
            "idea_id":         self.idea_id,
            "name":            self.name,
            "sector":          self.sector,
            "description":     self.description,
            "target_audience": self.target_audience,
            "clarified_idea":  self.clarified_idea,
            "market_analysis": self.market_analysis,
            "brand_identity":  self.brand_identity,
            "content":         self.content,
            "status":          self.status,
            "errors":          self.errors,
        }


# ══════════════════════════════════════════════════════════════
# Base Agent
# ══════════════════════════════════════════════════════════════

class BaseAgent(ABC):

    def __init__(self, agent_name: str, temperature: float = 0.7, max_retries: int = 3):

        self.agent_name  = agent_name
        self.temperature = temperature
        self.max_retries = max_retries

        self.logger      = logging.getLogger(f"brandai.{agent_name}")
        self.llm_rotator = LLMRotator()

    # ──────────────────────────────────────────────────────────

    @abstractmethod
    async def run(self, state: PipelineState):
        pass

    def _build_system_prompt(self, state: PipelineState) -> str:
        return ""

    def _build_user_prompt(self, state: PipelineState) -> str:
        return ""

    # ──────────────────────────────────────────────────────────
    # Appel LLM — 3 tentatives par clé, rotation si quota/erreur
    # ──────────────────────────────────────────────────────────

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        Appelle le LLM avec retry + rotation automatique.

        Logique :
          - MAX_RETRIES tentatives au total (pas par clé)
          - Si erreur quota/429/model_not_found → rotate() puis retry immédiat
          - Si autre erreur → backoff exponentiel puis retry
          - Si rotate() retourne False → plus aucun provider dispo → exception
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        attempt    = 0
        last_error = None

        while attempt < self.max_retries:

            try:
                client = self.llm_rotator.get_client(self.temperature)

                self.logger.info(
                    f"[{self.agent_name}] LLM call — "
                    f"attempt {attempt + 1}/{self.max_retries} — "
                    f"{self.llm_rotator.current_info()}"
                )

                start    = time.time()
                response = await client.ainvoke(messages)
                elapsed  = round(time.time() - start, 2)

                self.logger.info(
                    f"[{self.agent_name}] LLM response in {elapsed}s — "
                    f"{self.llm_rotator.current_info()}"
                )

                return response.content

            except Exception as e:

                last_error = e
                error_str  = str(e).lower()
                attempt   += 1   # ← FIX : toujours incrémenter

                is_quota_error = any(kw in error_str for kw in [
                    "429", "quota", "rate_limit", "model_not_found",
                    "insufficient_quota", "overloaded",
                ])

                if is_quota_error:
                    self.logger.warning(
                        f"[{self.agent_name}] Quota/rate error — "
                        f"rotating from {self.llm_rotator.current_info()}"
                    )
                    rotated = self.llm_rotator.rotate()
                    if not rotated:
                        # Plus aucun provider → inutile de continuer
                        break
                    # Retry immédiat après rotation (pas de sleep)
                    continue

                # Erreur non-quota → backoff exponentiel
                if attempt < self.max_retries:
                    wait = 2 ** attempt
                    self.logger.warning(
                        f"[{self.agent_name}] Error (attempt {attempt}) — "
                        f"retry in {wait}s — {e}"
                    )
                    await asyncio.sleep(wait)

        raise RuntimeError(
            f"[{self.agent_name}] LLM failed after {attempt} attempts. "
            f"Last error: {last_error}"
        )

    # ──────────────────────────────────────────────────────────
    # JSON parsing robuste
    # ──────────────────────────────────────────────────────────

    def _parse_json(self, raw: str) -> dict:
        """Parse la réponse LLM en JSON, tolère les backticks markdown."""

        cleaned = re.sub(r"```json\s*", "", raw)
        cleaned = re.sub(r"```\s*",     "", cleaned)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            self.logger.error(
                f"[{self.agent_name}] JSON parse error: {e} | "
                f"raw[:300]={raw[:300]}"
            )
            raise

    # ──────────────────────────────────────────────────────────
    # Logging helpers
    # ──────────────────────────────────────────────────────────

    def _log_start(self, state: PipelineState):
        self.logger.info(
            f"[{self.agent_name}] ▶ START | idea_id={state.idea_id}"
        )

    def _log_success(self, payload=None):
        self.logger.info(f"[{self.agent_name}] ✅ SUCCESS")

    def _log_error(self, error):
        self.logger.error(f"[{self.agent_name}] ❌ ERROR : {error}")