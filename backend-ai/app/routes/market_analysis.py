import json
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.step_runner_service import StepRunnerService
from app.services.persistence.market_marketing_persistence_service import (
    persist_market_result,
)


router = APIRouter(tags=["Market Analysis"])
step_runner = StepRunnerService()


def sse_event(event: str, data: dict) -> str:
    return step_runner.sse_event(event, data)


class MarketAnalysisStreamRequest(BaseModel):
    idea_id: int
    name: str
    sector: str
    description: str
    target_audience: Optional[str] = ""

    # Clarifier output
    short_pitch: Optional[str] = None
    solution_description: Optional[str] = None
    target_users: Optional[str] = None
    problem: Optional[str] = None
    country_code: Optional[str] = "TN"
    language: Optional[str] = "fr"

    # JWT du user (backend-api protège la route persist)
    access_token: Optional[str] = None


async def _stream_market_analysis(body: MarketAnalysisStreamRequest):
    started_at = datetime.now(timezone.utc)
    t0 = time.time()

    try:
        clarified_idea = {
            "short_pitch": body.short_pitch or body.name,
            "solution_description": body.solution_description or body.description,
            "target_users": body.target_users or body.target_audience or "",
            "problem": body.problem or body.description,
            "sector": body.sector,
            "country_code": body.country_code or "TN",
            "language": body.language or "fr",
        }

        market_analysis: dict = {}
        async for event, data in step_runner.run_market_step(
            idea_id=body.idea_id,
            clarified_idea=clarified_idea,
        ):
            if event == "result":
                market_analysis = data or {}
            else:
                yield sse_event(event, data or {})

        if not market_analysis:
            raise RuntimeError("Aucun résultat market_analysis produit")

        if not body.access_token:
            raise RuntimeError("access_token requis pour persister le résultat dans backend-api")

        yield sse_event("step", {"status": "loading", "stage": "persist_result", "message": "Sauvegarde de l'analyse de marché en base…"})
        completed_at = datetime.now(timezone.utc)
        persisted = await persist_market_result(
            idea_id=body.idea_id,
            result_json=market_analysis,
            started_at=started_at,
            completed_at=completed_at,
            access_token=body.access_token,
        )
        yield sse_event("step", {"status": "done", "stage": "persist_result", "message": "Analyse de marché sauvegardée"})

        elapsed_ms = int((time.time() - t0) * 1000)
        yield sse_event(
            "done",
            {
                "success": True,
                "idea_id": body.idea_id,
                "status": "done",
                "elapsed_ms": elapsed_ms,
                "persisted_id": persisted.get("id"),
                "persisted_marketing_id": None,
            },
        )
    except Exception as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        yield sse_event("error", {"success": False, "message": str(e), "elapsed_ms": elapsed_ms})


@router.post("/market-analysis/stream")
async def market_analysis_stream(body: MarketAnalysisStreamRequest):
    return StreamingResponse(
        _stream_market_analysis(body),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
