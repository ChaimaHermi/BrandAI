from llm.llm_factory import create_gemini_clients, create_groq_clients
import logging

logger = logging.getLogger("brandai.llm_rotator")

class LLMRotator:

    def __init__(self):
        self.gemini = create_gemini_clients()
        self.groq   = create_groq_clients()
        self.provider = "gemini"
        self.index    = 0

    def get_client(self, temperature: float = 0.7):
        clients = self.gemini if self.provider == "gemini" else self.groq
        if not clients:
            raise RuntimeError(f"Aucun client {self.provider} disponible.")
        client = clients[self.index]
        client.temperature = temperature
        return client

    def rotate(self) -> bool:
        clients = self.gemini if self.provider == "gemini" else self.groq
        next_index = self.index + 1

        if next_index < len(clients):
            logger.warning(
                f"[rotator] Rotation {self.provider} "
                f"clé {self.index + 1} → clé {next_index + 1}"
            )
            self.index = next_index
            return True

        # Toutes les clés Gemini épuisées → fallback Groq
        if self.provider == "gemini" and self.groq:
            logger.warning("[rotator] Gemini épuisé → fallback Groq")
            self.provider = "groq"
            self.index = 0
            return True

        logger.error("[rotator] Toutes les clés épuisées.")
        return False

    def current_info(self) -> str:
        clients = self.gemini if self.provider == "gemini" else self.groq
        return f"{self.provider} clé {self.index + 1}/{len(clients)}"