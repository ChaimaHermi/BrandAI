# ══════════════════════════════════════════════════════════════
#  llm/llm_rotator.py
# ══════════════════════════════════════════════════════════════

import logging

from llm.llm_factory import create_groq_clients

logger = logging.getLogger("brandai.llm_rotator")

class LLMRotator:

    def __init__(self, model: str = "llama3-70b-8192", max_tokens: int | None = None):
        self._provider = "groq"
        self._model = model
        self._clients = {"groq": create_groq_clients(model=model, max_tokens=max_tokens)}
        self._index = 0

        logger.info(
            f"[rotator] Init - provider=groq | model={self._model} | "
            f"groq={len(self._clients['groq'])} keys"
        )

        if not self._clients["groq"]:
            raise RuntimeError("Aucune clé Groq trouvée")

    # ─────────────────────────────────────────────
    # 🔥 GROQ ONLY (LLAMA)
    # ─────────────────────────────────────────────
    @classmethod
    def groq_only(cls):
        return cls(model="llama3-70b-8192")

    # ─────────────────────────────────────────────
    # 🔥 GROQ GPT ONLY (TON CAS EXACT)
    # ─────────────────────────────────────────────
    @classmethod
    def groq_gpt_only(cls):
        return cls(model="openai/gpt-oss-120b")

    # ─────────────────────────────────────────────
    # Generic model selector for future agents
    # ─────────────────────────────────────────────
    @classmethod
    def groq_model(cls, model: str, max_tokens: int | None = None):
        return cls(model=model, max_tokens=max_tokens)

    # ─────────────────────────────────────────────
    # GET CLIENT
    # ─────────────────────────────────────────────
    def get_client(self, temperature: float = 0.7):
        clients = self._clients[self._provider]

        if not clients:
            raise RuntimeError(f"Aucun client {self._provider}")

        client = clients[self._index]

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

        return False

    # ─────────────────────────────────────────────
    def current_info(self):
        clients = self._clients[self._provider]
        return f"{self._provider}:{self._model} key {self._index + 1}/{len(clients)}"