from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseCollector(ABC):
    @abstractmethod
    async def fetch_recent_posts(
        self,
        account_ref: dict[str, Any],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_post_metrics(
        self,
        account_ref: dict[str, Any],
        post_id: str,
    ) -> dict[str, Any]:
        raise NotImplementedError

