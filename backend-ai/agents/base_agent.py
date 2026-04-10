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

import httpx
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

# Modèles routés vers NVIDIA NIM en priorité (pas de limite TPM)
NVIDIA_MODELS = {
    "openai/gpt-oss-120b",
}

NVIDIA_API_BASE = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MAX_TOKENS_CAP = 65_536  # limite max output NVIDIA gpt-oss-120b

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
        temperature: float = 0.2,
        max_retries: int = 3,
        llm_model: str = "openai/gpt-oss-120b",
        llm_max_tokens: int | None = None,
    ):
        self.agent_name = agent_name
        self.temperature = temperature
        self.max_retries = max_retries
        self.llm_model = llm_model
        self.llm_max_tokens = llm_max_tokens or 65_536  # max output NVIDIA gpt-oss-120b

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

        # Clés NVIDIA NIM (rotation)
        self._nvidia_keys = [
            k for k in [
                os.getenv("NVIDIA_API_KEY_1", ""),
                os.getenv("NVIDIA_API_KEY_2", ""),
                os.getenv("NVIDIA_API_KEY_3", ""),
                os.getenv("NVIDIA_API_KEY_4", ""),
            ] if k
        ]
        self._nvidia_key_idx = 0

    def _next_groq_key(self) -> str:
        if not self._groq_keys:
            raise RuntimeError("Aucune clé GROQ_API_KEY définie")
        key = self._groq_keys[self._groq_key_idx % len(self._groq_keys)]
        self._groq_key_idx += 1
        return key

    def _next_nvidia_key(self) -> str:
        if not self._nvidia_keys:
            raise RuntimeError("Aucune clé NVIDIA_API_KEY définie")
        key = self._nvidia_keys[self._nvidia_key_idx % len(self._nvidia_keys)]
        self._nvidia_key_idx += 1
        return key

    # ─────────────────────────────────────────
    # LLM CALL
    # ─────────────────────────────────────────

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        # ── Priorité 1 : NVIDIA NIM (pas de limite TPM, 40 RPM) ──
        if self.llm_model in NVIDIA_MODELS and self._nvidia_keys:
            try:
                return await self._call_nvidia_direct(system_prompt, user_prompt)
            except Exception as e:
                self.logger.warning(
                    f"[{self.agent_name}] NVIDIA échoué → fallback Groq | {str(e)[:160]}"
                )
                # ── Fallback Groq si clés disponibles ──
                if self.llm_model in GROQ_DIRECT_MODELS and self._groq_keys:
                    try:
                        return await self._call_groq_direct(system_prompt, user_prompt)
                    except Exception as e2:
                        self.logger.warning(
                            f"[{self.agent_name}] Groq échoué → fallback LangChain | {str(e2)[:160]}"
                        )
                return await self._call_langchain(system_prompt, user_prompt)

        # ── Priorité 2 : Groq direct (si pas de clés NVIDIA) ──
        if self.llm_model in GROQ_DIRECT_MODELS and self._groq_keys:
            try:
                return await self._call_groq_direct(system_prompt, user_prompt)
            except Exception as e:
                self.logger.warning(
                    f"[{self.agent_name}] Groq échoué → fallback LangChain | {str(e)[:160]}"
                )
                return await self._call_langchain(system_prompt, user_prompt)

        # ── Priorité 3 : LangChain ──
        return await self._call_langchain(system_prompt, user_prompt)

    async def _call_nvidia_direct(self, system_prompt: str, user_prompt: str) -> str:
        """
        Appel NVIDIA NIM (OpenAI-compatible).
        Pas de limite TPM — limite RPM : 40 requêtes/minute par clé.
        Context window : 128 000 tokens | Max output : 65 536 tokens.

        Stratégie sur 429 :
          1. Essayer la clé suivante immédiatement (rotation)
          2. Si toutes les clés épuisées → attendre 60 sec → recommencer
          3. Après 3 cycles complets → lever une erreur
        """
        max_tokens = min(self.llm_max_tokens, NVIDIA_MAX_TOKENS_CAP)
        effort = REASONING_EFFORT_MAP.get(self.llm_model)
        n_keys = len(self._nvidia_keys)
        last_error = None

        async def _do_request(key: str) -> str:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    NVIDIA_API_BASE,
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.llm_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": self.temperature,
                        "max_tokens": max_tokens,
                        **({"reasoning_effort": effort} if effort else {}),
                    },
                )
                resp.raise_for_status()
                message = resp.json()["choices"][0]["message"]
                content = (message.get("content") or "").strip()
                if not content:
                    content = (message.get("reasoning_content") or "").strip()
                if not content:
                    raise RuntimeError("Réponse NVIDIA vide")
                return content

        # 3 cycles : chaque cycle essaie toutes les clés, puis attend 60 sec
        for cycle in range(self.max_retries):
            for _ in range(n_keys):
                key = self._next_nvidia_key()
                try:
                    content = await _do_request(key)
                    self.logger.info(
                        f"[{self.agent_name}] NVIDIA OK | cycle={cycle} | "
                        f"tokens ≈ {len(content)//4}"
                    )
                    return content
                except httpx.HTTPStatusError as e:
                    last_error = e
                    if e.response.status_code == 429:
                        # Rate limit → essayer la clé suivante immédiatement
                        self.logger.warning(
                            f"[{self.agent_name}] NVIDIA 429 → rotation clé suivante"
                        )
                        continue
                    # Autre erreur HTTP → pas de rotation, on sort du cycle
                    raise
                except Exception as e:
                    last_error = e
                    self.logger.warning(
                        f"[{self.agent_name}] NVIDIA erreur → {str(e)[:120]}"
                    )
                    continue

            # Toutes les clés épuisées → attendre 60 sec avant le prochain cycle
            if cycle < self.max_retries - 1:
                self.logger.warning(
                    f"[{self.agent_name}] Toutes les clés NVIDIA en limite "
                    f"→ attente 60 sec (cycle {cycle+1}/{self.max_retries})"
                )
                await asyncio.sleep(60)

        raise RuntimeError(
            f"NVIDIA failed après {self.max_retries} cycles × {n_keys} clés : {last_error}"
        )

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

        if not self.llm_rotator or not self.llm_rotator._clients.get("groq"):
            raise RuntimeError(
                "LangChain fallback indisponible : aucune clé Groq configurée. "
                "Ajoutez GROQ_API_KEY dans .env ou utilisez NVIDIA."
            )

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