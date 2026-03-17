# ══════════════════════════════════════════════════════════════
# BrandAI Base Agent
# Classe mère de tous les agents du pipeline
#
# RESPONSABILITÉS :
# - construire les prompts
# - appeler le LLM
# - parser la réponse
# - gérer les retries
#
# NOTE :
# La configuration LLM (Gemini / Groq / clés API) est gérée
# dans le module llm_rotator.
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
# Objet partagé entre les agents
# ══════════════════════════════════════════════════════════════

class PipelineState:

    def __init__(self, idea_id, name, sector, description, target_audience=""):

        self.idea_id = idea_id
        self.name = name
        self.sector = sector
        self.description = description
        self.target_audience = target_audience

        self.clarified_idea = {}
        self.market_analysis = {}
        self.brand_identity = {}
        self.content = {}

        self.status = "running"
        self.errors = []

        self.started_at = time.time()

    def to_dict(self):

        return {
            "idea_id": self.idea_id,
            "name": self.name,
            "sector": self.sector,
            "description": self.description,
            "target_audience": self.target_audience,
            "clarified_idea": self.clarified_idea,
            "market_analysis": self.market_analysis,
            "brand_identity": self.brand_identity,
            "content": self.content,
            "status": self.status,
            "errors": self.errors,
        }


# ══════════════════════════════════════════════════════════════
# Base Agent
# ══════════════════════════════════════════════════════════════

class BaseAgent(ABC):

    def __init__(self, agent_name, temperature=0.7, max_retries=3):

        self.agent_name = agent_name
        self.temperature = temperature
        self.max_retries = max_retries

        self.logger = logging.getLogger(f"brandai.{agent_name}")

        # rotator gère Gemini + Groq + rotation
        self.llm_rotator = LLMRotator()

    # ─────────────────────────────────────────

    @abstractmethod
    async def run(self, state: PipelineState):
        """Méthode principale exécutée par l'agent"""
        pass

    @abstractmethod
    def _build_system_prompt(self, state: PipelineState):
        """Construit le system prompt"""
        pass

    @abstractmethod
    def _build_user_prompt(self, state: PipelineState):
        """Construit le user prompt"""
        pass

    # ─────────────────────────────────────────
    # Appel LLM
    # ─────────────────────────────────────────

    async def _call_llm(self, system_prompt, user_prompt):

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        retry = 0
        last_error = None

        while retry < self.max_retries:

            try:

                client = self.llm_rotator.get_client(self.temperature)

                self.logger.info(
                    f"[{self.agent_name}] LLM call"
                )

                start = time.time()

                response = await client.ainvoke(messages)

                elapsed = round(time.time() - start, 2)

                self.logger.info(
                    f"[{self.agent_name}] response received in {elapsed}s"
                )

                return response.content

            except Exception as e:

                last_error = e
                error_str = str(e)

                is_llm_error = (
                    "429" in error_str
                    or "quota" in error_str.lower()
                    or "model_not_found" in error_str
                )

                if is_llm_error:

                    self.logger.warning(
                        f"[{self.agent_name}] LLM error → rotating key/provider"
                    )

                    self.llm_rotator.rotate()
                    continue

                retry += 1

                if retry < self.max_retries:

                    wait = 2 ** retry
                    await asyncio.sleep(wait)

        raise RuntimeError(
            f"[{self.agent_name}] LLM failed after {self.max_retries} attempts: {last_error}"
        )

    # ─────────────────────────────────────────
    # JSON parsing robuste
    # ─────────────────────────────────────────

    def _parse_json(self, raw):

        cleaned = re.sub(r"```json", "", raw)
        cleaned = re.sub(r"```", "", cleaned)

        try:

            return json.loads(cleaned.strip())

        except Exception:

            self.logger.error(
                f"[{self.agent_name}] JSON parsing error: {raw[:300]}"
            )

            raise

    # ─────────────────────────────────────────
    # Logging helpers
    # ─────────────────────────────────────────

    def _log_start(self, state):

        self.logger.info(
            f"[{self.agent_name}] START | idea_id={state.idea_id}"
        )

    def _log_success(self, payload=None):

        self.logger.info(f"[{self.agent_name}] SUCCESS")

    def _log_error(self, error):

        self.logger.error(
            f"[{self.agent_name}] ERROR : {error}"
        )