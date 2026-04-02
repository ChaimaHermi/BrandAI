# ══════════════════════════════════════════════════════════════
#  agents/base_agent.py
#  Classe mère de tous les agents du pipeline
#
#  CORRECTION vs version précédente :
#  + reasoning_effort pour gpt-oss-120b (medium par défaut)
#  + appel direct Groq SDK pour les modèles qui le nécessitent
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
# Modèles qui nécessitent un appel direct Groq SDK
# (pas via LangChain — pour supporter reasoning_effort)
# ══════════════════════════════════════════════════════════════

GROQ_DIRECT_MODELS = {
    "openai/gpt-oss-120b",
}

# reasoning_effort par modèle
# low    → rapide, analyse simple
# medium → équilibré — recommandé pour market analysis
# high   → raisonnement profond, +tokens output
REASONING_EFFORT_MAP = {
    "openai/gpt-oss-120b": "medium",
}


# ══════════════════════════════════════════════════════════════
# Base Agent
# ══════════════════════════════════════════════════════════════

class BaseAgent(ABC):

    def __init__(
        self,
        agent_name:     str,
        temperature:    float = 0.7,
        max_retries:    int   = 3,
        llm_model:      str   = "openai/gpt-oss-120b",
        llm_max_tokens: int | None = None,
    ):
        self.agent_name     = agent_name
        self.temperature    = temperature
        self.max_retries    = max_retries
        self.llm_model      = llm_model
        self.llm_max_tokens = llm_max_tokens or 4096

        self.logger      = logging.getLogger(f"brandai.{agent_name}")
        self.llm_rotator = LLMRotator.groq_model(llm_model, max_tokens=llm_max_tokens)

        # Clés Groq pour appel direct SDK
        self._groq_keys = [
            k for k in [
                os.getenv("GROQ_API_KEY",   ""),
                os.getenv("GROQ_API_KEY_2", ""),
                os.getenv("GROQ_API_KEY_3", ""),
            ] if k
        ]
        self._groq_key_idx = 0

    def _next_groq_key(self) -> str:
        """Rotation simple des clés Groq."""
        if not self._groq_keys:
            raise RuntimeError("Aucune clé GROQ_API_KEY définie")
        key = self._groq_keys[self._groq_key_idx % len(self._groq_keys)]
        self._groq_key_idx += 1
        return key

    # ──────────────────────────────────────────────────────────
    # Appel LLM unifié — LangChain OU Groq direct selon modèle
    # ──────────────────────────────────────────────────────────

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        Appelle le LLM avec retry + rotation automatique.

        - Si modèle dans GROQ_DIRECT_MODELS → appel direct Groq SDK
          (supporte reasoning_effort, JSON mode, etc.)
        - Sinon → LangChain via LLMRotator (comportement inchangé)
        """
        if self.llm_model in GROQ_DIRECT_MODELS:
            try:
                return await self._call_groq_direct(system_prompt, user_prompt)
            except Exception as e:
                # Some Groq direct responses are transiently empty or fail in ways that
                # the LangChain client path can recover from. Fallback once.
                self.logger.warning(
                    f"[{self.agent_name}] Groq direct failed — fallback to LangChain | {str(e)[:160]}"
                )
                return await self._call_langchain(system_prompt, user_prompt)

        return await self._call_langchain(system_prompt, user_prompt)

    # ──────────────────────────────────────────────────────────
    # Appel direct Groq SDK (gpt-oss-120b avec reasoning_effort)
    # ──────────────────────────────────────────────────────────

    async def _call_groq_direct(self, system_prompt: str, user_prompt: str) -> str:
        """
        Appel direct via Groq AsyncClient.
        Supporte reasoning_effort pour gpt-oss-120b.
        Rotation des clés en cas de 413/429.
        """
        attempt    = 0
        last_error = None

        # Keep requests under Groq on_demand TPM limit (8000).
        # Use safety margin to avoid borderline 413 errors.
        tpm_budget = 7600
        min_completion_tokens = 256
        chars_per_token = 4

        system_prompt = system_prompt or ""
        user_prompt = user_prompt or ""

        total_chars = len(system_prompt) + len(user_prompt)
        est_tokens = max(1, total_chars // chars_per_token)

        max_input_tokens = max(1, tpm_budget - min_completion_tokens)
        if est_tokens > max_input_tokens:
            allowed_user_chars = max(200, max_input_tokens * chars_per_token - len(system_prompt))
            user_prompt = user_prompt[:allowed_user_chars]
            total_chars = len(system_prompt) + len(user_prompt)
            est_tokens = max(1, total_chars // chars_per_token)
            self.logger.warning(
                f"[{self.agent_name}] prompt truncated for TPM safety — input~{est_tokens} tokens"
            )

        dynamic_max_tokens = min(
            self.llm_max_tokens,
            max(min_completion_tokens, tpm_budget - est_tokens),
        )
        requested_tokens = est_tokens + dynamic_max_tokens
        self.logger.info(
            f"[{self.agent_name}] Groq direct call — input~{est_tokens} | "
            f"max_out={dynamic_max_tokens} | requested~{requested_tokens} | model={self.llm_model}"
        )

        while attempt < self.max_retries:
            try:
                key    = self._next_groq_key()
                client = AsyncGroq(api_key=key)

                # Paramètres de base
                params = {
                    "model":      self.llm_model,
                    "messages":   [
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt},
                    ],
                    "temperature":  self.temperature,
                    "max_tokens":   dynamic_max_tokens,
                }

                # reasoning_effort si supporté par ce modèle
                effort = REASONING_EFFORT_MAP.get(self.llm_model)
                if effort:
                    params["reasoning_effort"] = effort

                self.logger.info(
                    f"[{self.agent_name}] attempt {attempt+1}/{self.max_retries} — "
                    f"key ...{key[-6:]} | reasoning={effort}"
                )

                start    = time.time()
                response = await client.chat.completions.create(**params)
                elapsed  = round(time.time() - start, 2)

                content = response.choices[0].message.content or ""
                out_tokens = response.usage.completion_tokens if response.usage else "?"
                self.logger.info(
                    f"[{self.agent_name}] done in {elapsed}s — "
                    f"~{out_tokens} output tokens"
                )

                # Some transient Groq responses can return an empty body.
                # Treat this as retryable to avoid downstream JSON parse crashes.
                if not str(content).strip():
                    raise RuntimeError("Empty LLM response content")

                return content

            except Exception as e:
                last_error = e
                error_str  = str(e).lower()
                attempt   += 1

                is_quota = any(kw in error_str for kw in [
                    "429", "413", "quota", "rate_limit",
                    "payload too large", "tokens per minute",
                    "overloaded", "insufficient_quota",
                ])

                if is_quota:
                    self.logger.warning(
                        f"[{self.agent_name}] Quota/rate error (attempt {attempt}) — "
                        f"rotating key | error: {str(e)[:120]}"
                    )
                    # Pas de sleep sur quota — on change juste de clé
                    continue

                # Erreur non-quota → backoff exponentiel
                if attempt < self.max_retries:
                    wait = 2 ** attempt
                    self.logger.warning(
                        f"[{self.agent_name}] Error (attempt {attempt}) — "
                        f"retry in {wait}s | {str(e)[:120]}"
                    )
                    await asyncio.sleep(wait)

        raise RuntimeError(
            f"[{self.agent_name}] Groq direct failed after {attempt} attempts. "
            f"Last error: {last_error}"
        )

    # ──────────────────────────────────────────────────────────
    # Appel LangChain (modèles autres que gpt-oss-120b)
    # ──────────────────────────────────────────────────────────

    async def _call_langchain(self, system_prompt: str, user_prompt: str) -> str:
        """Appel LangChain via LLMRotator — comportement original inchangé."""

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
                    f"[{self.agent_name}] LangChain call — "
                    f"attempt {attempt+1}/{self.max_retries} — "
                    f"{self.llm_rotator.current_info()}"
                )

                start    = time.time()
                response = await client.ainvoke(messages)
                elapsed  = round(time.time() - start, 2)

                self.logger.info(
                    f"[{self.agent_name}] LangChain done in {elapsed}s"
                )

                return response.content

            except Exception as e:
                last_error = e
                error_str  = str(e).lower()
                attempt   += 1

                is_quota = any(kw in error_str for kw in [
                    "429", "quota", "rate_limit", "model_not_found",
                    "insufficient_quota", "overloaded",
                ])

                if is_quota:
                    self.logger.warning(
                        f"[{self.agent_name}] Quota error — rotating"
                    )
                    rotated = self.llm_rotator.rotate()
                    if not rotated:
                        break
                    continue

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
    # Abstract
    # ──────────────────────────────────────────────────────────

    @abstractmethod
    async def run(self, state: PipelineState):
        pass

    def _build_system_prompt(self, state: PipelineState) -> str:
        return ""

    def _build_user_prompt(self, state: PipelineState) -> str:
        return ""

    # ──────────────────────────────────────────────────────────
    # JSON parsing robuste
    # ──────────────────────────────────────────────────────────

    def _repair_json_text(self, s: str) -> str:
        for bad, good in (
            ("\u201c", '"'), ("\u201d", '"'),
            ("\u00ab", '"'), ("\u00bb", '"'),
            ("\u2018", "'"), ("\u2019", "'"),
            ("\u2011", "-"), ("\u2013", "-"), ("\u2014", "-"),
        ):
            s = s.replace(bad, good)
        s = re.sub(r",\s*([}\]])", r"\1", s)
        return s

    def _extract_outer_json_object(self, s: str) -> str | None:
        start = s.find("{")
        if start < 0:
            return None
        depth = 0
        for i, c in enumerate(s[start:], start):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return s[start : i + 1]
        return None

    def _parse_json(self, raw: str) -> dict:
        cleaned = re.sub(r"```json\s*", "", raw)
        cleaned = re.sub(r"```\s*", "", cleaned)
        cleaned = cleaned.strip()

        candidates = [cleaned]
        blob = self._extract_outer_json_object(cleaned)
        if blob and blob != cleaned:
            candidates.append(blob)

        last_err = None
        for cand in candidates:
            for variant in (cand, self._repair_json_text(cand)):
                try:
                    data = json.loads(variant)
                    if isinstance(data, dict):
                        return data
                except json.JSONDecodeError as e:
                    last_err = e
                    continue

        self.logger.error(
            f"[{self.agent_name}] JSON parse error: {last_err} | "
            f"raw[:300]={raw[:300]}"
        )
        if last_err:
            raise last_err
        raise json.JSONDecodeError("empty", raw, 0)

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