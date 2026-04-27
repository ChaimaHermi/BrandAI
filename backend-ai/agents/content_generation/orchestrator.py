from __future__ import annotations

from typing import Any

from agents.content_generation.content_react_agent import run_content_generation
from agents.content_generation.weekly_plan_agent import (
    WeeklyGenerateInput,
    approve_weekly_plan,
    generate_weekly_plan,
    regenerate_weekly_item,
)


async def run_content_flow(mode: str, payload: dict[str, Any]) -> dict[str, Any]:
    if mode == "single_post":
        return await run_content_generation(**payload)
    if mode == "weekly_plan_generate":
        return await generate_weekly_plan(WeeklyGenerateInput(**payload))
    if mode == "weekly_plan_regenerate_item":
        return {"item": await regenerate_weekly_item(**payload)}
    if mode == "weekly_plan_approve":
        return await approve_weekly_plan(**payload)
    raise ValueError(f"Unsupported content flow mode: {mode}")
