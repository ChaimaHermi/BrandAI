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
        self.palette_slogan_hint = ""
        self.logo_palette_hint: str = ""
        self.logo_previous_prompt: str = ""
        self.logo_user_remarks: str = ""

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
# Modèles servis exclusivement par NVIDIA NIM (openai/gpt-oss-120b) — pas de Groq
# ══════════════════════════════════════════════════════════════
NVIDIA_MODELS = {
    "openai/gpt-oss-120b",
}

NVIDIA_API_BASE = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MAX_TOKENS_CAP = 65_536  # limite max output NVIDIA gpt-oss-120b

# Timeout HTTP NVIDIA (génération longue). Défaut 600 s ; 0 / none / off = pas de limite.
def _nvidia_http_timeout() -> float | None:
    raw = (os.getenv("NVIDIA_HTTP_TIMEOUT_S") or "").strip()
    if raw in ("0", "none", "off"):
        return None
    if not raw:
        return 600.0
    try:
        return float(raw)
    except ValueError:
        return 600.0

def _nvidia_reasoning_effort() -> str | None:
    """
    Hosted NVIDIA NIM may reject unknown fields; only send reasoning_effort when explicitly set.
    Env NVIDIA_REASONING_EFFORT: low | medium | high (see NVIDIA GPT-OSS docs).
    """
    raw = (os.getenv("NVIDIA_REASONING_EFFORT") or "").strip().lower()
    if raw in ("low", "medium", "high"):
        return raw
    return None


# ══════════════════════════════════════════════════════════════
# Pool global de clés NVIDIA — partagé entre tous les agents
# ══════════════════════════════════════════════════════════════

# Verrou asyncio par clé — créé à la première utilisation depuis l'event loop
_NVIDIA_KEY_LOCKS: dict[str, asyncio.Lock] = {}
_KEY_POOL_RR_IDX: int = 0   # index round-robin global


def _get_key_lock(key: str) -> asyncio.Lock:
    """Retourne le verrou asyncio associé à cette clé (créé si absent).
    Sûr en asyncio : pas d'await entre le test et l'assignation."""
    return _NVIDIA_KEY_LOCKS.setdefault(key, asyncio.Lock())


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

        # Clés NVIDIA NIM (rotation) — seul fournisseur pour openai/gpt-oss-120b
        self._nvidia_keys = [
            k for k in [
                os.getenv("NVIDIA_API_KEY_1", ""),
                os.getenv("NVIDIA_API_KEY_2", ""),
                os.getenv("NVIDIA_API_KEY_3", ""),
                os.getenv("NVIDIA_API_KEY_4", ""),
            ] if k
        ]

    async def _acquire_free_key(self) -> tuple[str, asyncio.Lock]:
        """
        Cherche une clé NVIDIA libre (verrou non acquis).
        Si toutes occupées → attend sur la prochaine en round-robin global.
        Retourne (key, lock) avec le verrou déjà acquis.
        """
        global _KEY_POOL_RR_IDX
        keys = self._nvidia_keys
        n = len(keys)
        if not n:
            raise RuntimeError("Aucune clé NVIDIA_API_KEY définie")

        # Passe 1 : cherche une clé libre (non bloquante)
        for i in range(n):
            idx = (_KEY_POOL_RR_IDX + i) % n
            key  = keys[idx]
            lock = _get_key_lock(key)
            if not lock.locked():
                _KEY_POOL_RR_IDX = (idx + 1) % n
                await lock.acquire()
                return key, lock

        # Passe 2 : toutes occupées → attend sur la suivante en round-robin
        idx  = _KEY_POOL_RR_IDX % n
        _KEY_POOL_RR_IDX = (idx + 1) % n
        key  = keys[idx]
        lock = _get_key_lock(key)
        await lock.acquire()
        return key, lock

    # ─────────────────────────────────────────
    # LLM CALL
    # ─────────────────────────────────────────

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        # openai/gpt-oss-120b : NVIDIA NIM uniquement (contexte ~128k tokens, sortie max 65 536).
        if self.llm_model in NVIDIA_MODELS:
            if not self._nvidia_keys:
                raise RuntimeError(
                    "Modèle openai/gpt-oss-120b : définissez au moins une variable "
                    "d'environnement NVIDIA_API_KEY_1 … NVIDIA_API_KEY_4. "
                    "Le routage Groq n'est pas utilisé pour ce modèle."
                )
            return await self._call_nvidia_direct(system_prompt, user_prompt)

        # Autres modèles (ex. hors gpt-oss) : LangChain + rotator Groq si configuré
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
        effort     = _nvidia_reasoning_effort()
        last_error = None

        nv_timeout    = _nvidia_http_timeout()
        httpx_timeout = httpx.Timeout(None) if nv_timeout is None else httpx.Timeout(nv_timeout)

        async def _do_request(key: str) -> str:
            async with httpx.AsyncClient(timeout=httpx_timeout) as client:
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

        for cycle in range(self.max_retries):
            # Acquiert une clé libre — attend si toutes occupées
            key, lock = await self._acquire_free_key()
            try:
                self.logger.info(f"[{self.agent_name}] NVIDIA → clé …{key[-6:]}")
                content = await _do_request(key)
                self.logger.info(
                    f"[{self.agent_name}] NVIDIA OK | cycle={cycle} | "
                    f"tokens ≈ {len(content)//4}"
                )
                return content

            except httpx.HTTPStatusError as e:
                last_error = e
                status = e.response.status_code if e.response is not None else "?"
                self.logger.error(
                    f"[API_KO] provider=NVIDIA status={status} "
                    f"agent={self.agent_name} err={str(e)[:200]}"
                )
                if status == 429:
                    self.logger.warning(
                        f"[{self.agent_name}] NVIDIA 429 sur clé …{key[-6:]} "
                        f"→ retry cycle {cycle+1}"
                    )
                    # libère immédiatement et attend avant de réessayer
                    if cycle < self.max_retries - 1:
                        await asyncio.sleep(60)
                    continue
                raise

            except Exception as e:
                last_error = e
                self.logger.warning(f"[{self.agent_name}] NVIDIA erreur → {str(e)[:120]}")
                continue

            finally:
                lock.release()   # libère toujours la clé, même en cas d'erreur

        raise RuntimeError(
            f"NVIDIA failed après {self.max_retries} tentatives : {last_error}"
        )

    async def _call_langchain(self, system_prompt: str, user_prompt: str) -> str:

        if not self.llm_rotator or not self.llm_rotator._clients.get("groq"):
            raise RuntimeError(
                "LangChain indisponible : aucune clé GROQ_API_KEY configurée "
                "(rotator Groq requis pour ce modèle hors openai/gpt-oss-120b)."
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