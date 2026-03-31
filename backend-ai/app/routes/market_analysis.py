import json
import os
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.base_agent import PipelineState
from agents.market_analysis.market_analysis_agent import MarketAnalysisAgent


router = APIRouter(tags=["Market Analysis"])


def sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


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


async def _persist_market_result(
    *,
    idea_id: int,
    result_json: dict,
    started_at: datetime,
    completed_at: datetime,
    access_token: str,
) -> dict:
    base = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")
    url = f"{base}/market-analysis/{idea_id}"
    payload = {
        "status": "done",
        "result_json": result_json,
        "data_quality_json": result_json.get("data_quality"),
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
    }
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def _stream_market_analysis(body: MarketAnalysisStreamRequest):
    started_at = datetime.now(timezone.utc)
    t0 = time.time()

    try:
        yield sse_event("step", {"status": "loading", "stage": "build_state", "message": "Préparation de l'analyse..."})

        state = PipelineState(
            idea_id=body.idea_id,
            name=body.name,
            sector=body.sector,
            description=body.description,
            target_audience=body.target_audience or "",
        )
        state.clarified_idea = {
            "short_pitch": body.short_pitch or body.name,
            "solution_description": body.solution_description or body.description,
            "target_users": body.target_users or body.target_audience or "",
            "problem": body.problem or body.description,
            "sector": body.sector,
            "country_code": body.country_code or "TN",
            "language": body.language or "fr",
        }

        yield sse_event("step", {"status": "loading", "stage": "run_market_analysis", "message": "Analyse de marché en cours..."})
        agent = MarketAnalysisAgent()
        state = await agent.run(state)

        if not state.market_analysis:
            raise RuntimeError("Aucun résultat market_analysis produit")

        if not body.access_token:
            raise RuntimeError("access_token requis pour persister le résultat dans backend-api")

        yield sse_event("step", {"status": "loading", "stage": "persist_result", "message": "Sauvegarde du résultat..."})
        completed_at = datetime.now(timezone.utc)
        persisted = await _persist_market_result(
            idea_id=body.idea_id,
            result_json=state.market_analysis,
            started_at=started_at,
            completed_at=completed_at,
            access_token=body.access_token,
        )

        elapsed_ms = int((time.time() - t0) * 1000)
        yield sse_event(
            "done",
            {
                "success": True,
                "idea_id": body.idea_id,
                "elapsed_ms": elapsed_ms,
                "persisted_id": persisted.get("id"),
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
