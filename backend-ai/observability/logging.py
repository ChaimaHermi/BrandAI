import os
import logging
from langsmith import Client as LangSmithClient

# ─────────────────────────────────────────
# LANGSMITH CLIENT (singleton)
# ─────────────────────────────────────────
_client: LangSmithClient | None = None


def get_langsmith_client() -> LangSmithClient | None:
    """Returns a singleton LangSmith client if tracing is enabled."""
    global _client
    if _client is None and os.getenv("LANGCHAIN_API_KEY"):
        _client = LangSmithClient()
    return _client


def is_tracing_enabled() -> bool:
    return os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"


# ─────────────────────────────────────────
# STRUCTURED LOGGING
# ─────────────────────────────────────────
def setup_logging(name: str = "brand_ai", level: int = logging.INFO) -> logging.Logger:
    """Configures structured logging and returns a named logger."""
    logging.basicConfig(
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        level=level,
    )
    return logging.getLogger(name)
