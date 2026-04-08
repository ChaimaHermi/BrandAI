# ══════════════════════════════════════════════════════════════
#  agents/base_agent.py
# ══════════════════════════════════════════════════════════════

import asyncio
import json
import logging
import os
import re
import time
from abc import ABC, abstractmethod

from groq import AsyncGroq
from langchain_core.messages import HumanMessage, SystemMessage
from llm.llm_rotator import LLMRotator


# ══════════════════════════════════════════════════════════════
# Pipeline State (✅ CORRIGÉ)
# ══════════════════════════════════════════════════════════════

class PipelineState:

    def __init__(
        self,
        idea_id,
        name=None,
        sector=None,
        description=None,
        target_audience=""
    ):
        self.idea_id = idea_id

        # legacy (optionnel maintenant)
        self.name = name
        self.sector = sector
        self.description = description
        self.target_audience = target_audience

        # ✅ source principale
        self.clarified_idea = {}

        self.market_analysis = {}
        self.brand_identity = {}
        self.content = {}

        self.status = "running"
        self.errors = []

        self.started_at = time.time()

        # Branding (optionnel, renseigné par les routes / orchestrateur)
        self.brand_name_chosen = ""
        self.slogan_preferences: dict = {}
        self.palette_preferences: dict = {}
        self.palette_slogan_hint = ""
        self.logo_palette_hint: str = ""

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
# Modèles Groq direct
# ══════════════════════════════════════════════════════════════

GROQ_DIRECT_MODELS = {
    "openai/gpt-oss-120b",
}

REASONING_EFFORT_MAP = {
    "openai/gpt-oss-120b": "medium",
}


# ══════════════════════════════════════════════════════════════
# Base Agent
# ══════════════════════════════════════════════════════════════

class BaseAgent(ABC):

    def __init__(
        self,
        agent_name: str,
        temperature: float = 0.7,
        max_retries: int = 3,
        llm_model: str = "openai/gpt-oss-120b",
        llm_max_tokens: int | None = None,
    ):
        self.agent_name = agent_name
        self.temperature = temperature
        self.max_retries = max_retries
        self.llm_model = llm_model
        self.llm_max_tokens = llm_max_tokens or 4096

        self.logger = logging.getLogger(f"brandai.{agent_name}")
        self.llm_rotator = LLMRotator.groq_model(llm_model, max_tokens=llm_max_tokens)

        self._groq_keys = [
            k for k in [
                os.getenv("GROQ_API_KEY", ""),
                os.getenv("GROQ_API_KEY_2", ""),
                os.getenv("GROQ_API_KEY_3", ""),
            ] if k
        ]
        self._groq_key_idx = 0

    def _next_groq_key(self) -> str:
        if not self._groq_keys:
            raise RuntimeError("Aucune clé GROQ_API_KEY définie")
        key = self._groq_keys[self._groq_key_idx % len(self._groq_keys)]
        self._groq_key_idx += 1
        return key

    # ─────────────────────────────────────────
    # LLM CALL
    # ─────────────────────────────────────────

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        if self.llm_model in GROQ_DIRECT_MODELS:
            try:
                return await self._call_groq_direct(system_prompt, user_prompt)
            except Exception as e:
                self.logger.warning(
                    f"[{self.agent_name}] fallback LangChain | {str(e)[:160]}"
                )
                return await self._call_langchain(system_prompt, user_prompt)

        return await self._call_langchain(system_prompt, user_prompt)

    async def _call_groq_direct(self, system_prompt: str, user_prompt: str) -> str:
        attempt = 0
        last_error = None

        tpm_budget = 7600
        min_completion_tokens = 256
        chars_per_token = 4

        total_chars = len(system_prompt) + len(user_prompt)
        est_tokens = max(1, total_chars // chars_per_token)

        max_input_tokens = max(1, tpm_budget - min_completion_tokens)
        if est_tokens > max_input_tokens:
            allowed = max_input_tokens * chars_per_token - len(system_prompt)
            user_prompt = user_prompt[:allowed]

        dynamic_max_tokens = min(
            self.llm_max_tokens,
            max(min_completion_tokens, tpm_budget - est_tokens),
        )

        while attempt < self.max_retries:
            try:
                key = self._next_groq_key()
                client = AsyncGroq(api_key=key)

                params = {
                    "model": self.llm_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": self.temperature,
                    "max_tokens": dynamic_max_tokens,
                }

                effort = REASONING_EFFORT_MAP.get(self.llm_model)
                if effort:
                    params["reasoning_effort"] = effort

                response = await client.chat.completions.create(**params)
                message = response.choices[0].message
                # gpt-oss often puts JSON in reasoning_content while content is empty
                content = (message.content or "").strip()
                if not content:
                    reasoning = getattr(message, "reasoning_content", None) or ""
                    if isinstance(reasoning, str) and reasoning.strip():
                        content = reasoning.strip()
                if not content:
                    raise RuntimeError("Empty response (no content or reasoning)")

                return content

            except Exception as e:
                last_error = e
                attempt += 1
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError(f"Groq failed: {last_error}")

    async def _call_langchain(self, system_prompt: str, user_prompt: str) -> str:

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            try:
                client = self.llm_rotator.get_client(self.temperature)
                response = await client.ainvoke(messages)
                return response.content

            except Exception as e:
                last_error = e
                attempt += 1
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError(f"LangChain failed: {last_error}")

    # ─────────────────────────────────────────
    # ABSTRACT
    # ─────────────────────────────────────────

    @abstractmethod
    async def run(self, state: PipelineState):
        pass

    # ─────────────────────────────────────────
    # JSON PARSER
    # ─────────────────────────────────────────

    def _parse_json(self, raw: str) -> dict:
        """Parse LLM output; tolerates markdown fences and leading prose."""
        if raw is None:
            raise json.JSONDecodeError("Invalid JSON (empty response)", "", 0)

        s = str(raw).strip()
        if not s:
            raise json.JSONDecodeError("Invalid JSON (empty response)", raw or "", 0)

        cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", s, flags=re.IGNORECASE).strip()

        # Direct JSON
        try:
            out = json.loads(cleaned)
            if isinstance(out, dict):
                return out
        except json.JSONDecodeError:
            pass

        # First balanced { ... } block (non-greedy depth scan)
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
                            out = json.loads(cleaned[brace_start : i + 1])
                            if isinstance(out, dict):
                                return out
                        except json.JSONDecodeError:
                            break

        preview = (s[:120] + "…") if len(s) > 120 else s
        raise json.JSONDecodeError(f"Invalid JSON (no parseable object): {preview!r}", s, 0)

    # ─────────────────────────────────────────
    # LOGGING
    # ─────────────────────────────────────────

    def _log_start(self, state: PipelineState):
        self.logger.info(f"[{self.agent_name}] START {state.idea_id}")

    def _log_success(self):
        self.logger.info(f"[{self.agent_name}] SUCCESS")

    def _log_error(self, error):
        self.logger.error(f"[{self.agent_name}] ERROR: {error}")