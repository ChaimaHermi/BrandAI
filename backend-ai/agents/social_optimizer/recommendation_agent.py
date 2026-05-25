"""Social Optimizer recommendation agent."""

from __future__ import annotations

import json
from datetime import datetime

import httpx
from langsmith import traceable

from agents.base_agent import BaseAgent
from prompts.social_media_optimizer.prompt_optimizer_system import SOCIAL_OPTIMIZER_SYSTEM_PROMPT
from prompts.social_media_optimizer.prompt_optimizer_user import build_optimizer_user_prompt
from tools.social_optimizer.recommendation_tools import (
    get_current_kpis,
    get_latest_recommendation,
    get_project_context,
    save_recommendation,
)


class SocialOptimizerRecommendationAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_name="social_optimizer_recommendation_agent",
            temperature=0.35,
            llm_model="openai/gpt-oss-120b",
            llm_max_tokens=1600,
        )

    @staticmethod
    def _normalize_priority(value: str | None) -> str:
        p = (value or "medium").strip().lower()
        return p if p in {"high", "medium", "low"} else "medium"

    def _normalize_payload(self, payload: dict, *, platform: str) -> dict:
        recs = payload.get("recommendations")
        if not isinstance(recs, list):
            recs = []
        normalized = []
        for idx, item in enumerate(recs[:5], start=1):
            if not isinstance(item, dict):
                continue
            actions = item.get("actions")
            if not isinstance(actions, list):
                actions = []
            normalized.append(
                {
                    "id": int(item.get("id") or idx),
                    "title": str(item.get("title") or "").strip(),
                    "description": str(item.get("description") or "").strip(),
                    "actions": [str(a).strip() for a in actions if str(a).strip()],
                    "priority": self._normalize_priority(str(item.get("priority") or "medium")),
                }
            )
        return {
            "platform": str(payload.get("platform") or platform).strip().lower(),
            "summary": str(payload.get("summary") or "").strip(),
            "recommendations": normalized,
        }

    @traceable(
        name="social_optimizer.llm_json",
        run_type="llm",
        tags=["social_optimizer", "llm"],
    )
    async def _call_llm_json_object(self, system_prompt: str, user_prompt: str) -> dict:
        max_tokens = min(self.llm_max_tokens, 4096)
        key, lock = await self._acquire_free_key()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as client:
                resp = await client.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
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
                        "response_format": {"type": "json_object"},
                    },
                )
                resp.raise_for_status()
                message = resp.json()["choices"][0]["message"]
                content = (message.get("content") or "").strip()
                return json.loads(content)
        finally:
            lock.release()

    @traceable(name="social_optimizer.agent.generate_recommendation", run_type="chain", tags=["social_optimizer", "agent"])
    async def generate_recommendation(
        self,
        *,
        idea_id: int,
        platform: str,
        access_token: str,
        force: bool = False,
    ) -> dict:
        if not force:
            cached = await get_latest_recommendation(idea_id, platform)
            if cached:
                try:
                    payload = json.loads(str(cached.get("content") or "{}"))
                except Exception:
                    payload = {}
                normalized = self._normalize_payload(payload, platform=platform)
                normalized["generated_at"] = (
                    cached["generated_at"].isoformat()
                    if hasattr(cached.get("generated_at"), "isoformat")
                    else str(cached.get("generated_at") or datetime.utcnow().isoformat())
                )
                return normalized

        project_context = await get_project_context(idea_id, access_token)
        stats = await get_current_kpis(idea_id, platform, access_token)
        user_prompt = build_optimizer_user_prompt(
            platform=platform,
            project_context=project_context,
            stats=stats,
        )
        payload = await self._call_llm_json_object(SOCIAL_OPTIMIZER_SYSTEM_PROMPT, user_prompt)
        normalized = self._normalize_payload(payload, platform=platform)
        content = json.dumps(normalized, ensure_ascii=False)
        saved = await save_recommendation(idea_id, platform, content)
        normalized["generated_at"] = (
            saved["generated_at"].isoformat()
            if hasattr(saved.get("generated_at"), "isoformat")
            else str(saved.get("generated_at") or datetime.utcnow().isoformat())
        )
        return normalized

    async def run(self, state):
        """
        Compatibility with BaseAgent abstract contract.
        Social optimizer uses explicit params in generate_recommendation.
        """
        return state

