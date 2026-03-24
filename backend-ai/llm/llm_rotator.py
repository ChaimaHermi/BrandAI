# ══════════════════════════════════════════════════════════════
#  llm/llm_rotator.py
# ══════════════════════════════════════════════════════════════

import logging

from llm.llm_factory import (
    create_openrouter_clients,
    create_gemini_clients,
    create_groq_clients,
)

logger = logging.getLogger("brandai.llm_rotator")

PROVIDER_ORDER = ["openrouter", "gemini", "groq"]


class LLMRotator:

    def __init__(self):
        self._clients = {
            "openrouter": create_openrouter_clients(),
            "gemini": create_gemini_clients(),
            "groq": create_groq_clients(),  # default llama
        }

        self._provider = self._first_available_provider()
        self._index = 0

        logger.info(
            f"[rotator] Init — provider={self._provider} | "
            f"openrouter={len(self._clients['openrouter'])} clés | "
            f"gemini={len(self._clients['gemini'])} clés | "
            f"groq={len(self._clients['groq'])} clés"
        )

    # ─────────────────────────────────────────────
    # 🔥 GROQ ONLY (LLAMA)
    # ─────────────────────────────────────────────
    @classmethod
    def groq_only(cls):
        instance = cls.__new__(cls)

        instance._clients = {
            "openrouter": [],
            "gemini": [],
            "groq": create_groq_clients(),  # llama
        }

        instance._provider = "groq"
        instance._index = 0

        if not instance._clients["groq"]:
            raise RuntimeError("Aucune clé Groq trouvée")

        return instance

    # ─────────────────────────────────────────────
    # 🔥 GROQ GPT ONLY (TON CAS EXACT)
    # ─────────────────────────────────────────────
    @classmethod
    def groq_gpt_only(cls):
        instance = cls.__new__(cls)

        instance._clients = {
            "openrouter": [],
            "gemini": [],
            "groq": create_groq_clients(model="openai/gpt-oss-120b"),  # 🔥 GPT OSS
        }

        instance._provider = "groq"
        instance._index = 0

        if not instance._clients["groq"]:
            raise RuntimeError("Aucune clé Groq trouvée")

        return instance

    # ─────────────────────────────────────────────
    # OPENROUTER ONLY
    # ─────────────────────────────────────────────
    @classmethod
    def openrouter_only(cls):
        instance = cls.__new__(cls)

        instance._clients = {
            "openrouter": create_openrouter_clients(),
            "gemini": [],
            "groq": [],
        }

        instance._provider = "openrouter"
        instance._index = 0

        if not instance._clients["openrouter"]:
            raise RuntimeError("Aucune clé OpenRouter trouvée")

        return instance

    # ─────────────────────────────────────────────
    # GET CLIENT
    # ─────────────────────────────────────────────
    def get_client(self, temperature: float = 0.7):
        clients = self._clients[self._provider]

        if not clients:
            raise RuntimeError(f"Aucun client {self._provider}")

        client = clients[self._index]

        if self._provider == "groq":
            client.temperature = 0.3
        else:
            client.temperature = temperature

        return client

    # ─────────────────────────────────────────────
    # ROTATION
    # ─────────────────────────────────────────────
    def rotate(self) -> bool:
        clients = self._clients[self._provider]
        next_idx = self._index + 1

        if next_idx < len(clients):
            self._index = next_idx
            return True

        next_provider = self._next_provider()

        if next_provider:
            self._provider = next_provider
            self._index = 0
            return True

        return False

    # ─────────────────────────────────────────────
    def current_info(self):
        clients = self._clients[self._provider]
        return f"{self._provider} clé {self._index + 1}/{len(clients)}"

    # ─────────────────────────────────────────────
    def _first_available_provider(self):
        for p in PROVIDER_ORDER:
            if self._clients[p]:
                return p
        raise RuntimeError("Aucun provider configuré")

    def _next_provider(self):
        current_idx = PROVIDER_ORDER.index(self._provider)

        for p in PROVIDER_ORDER[current_idx + 1:]:
            if self._clients[p]:
                return p

        return None