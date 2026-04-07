import json
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.pipeline_persistence_service import persist_market_result
from pipeline.market_graph import build_market_graph


router = APIRouter(tags=["Market Analysis"])
market_graph = build_market_graph()


def sse_event(event: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    data_lines = "\n".join(f"data: {line}" for line in payload.splitlines())
    return f"event: {event}\n{data_lines}\n\n"


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
        yield sse_event("step", {"status": "loading", "stage": "build_state", "message": "Préparation de l'analyse..."})

        yield sse_event("step", {"status": "loading", "stage": "run_market_analysis", "message": "Analyse de marché en cours..."})
        graph_input = {
            "idea_id": body.idea_id,
            "clarified_idea": {
                "short_pitch": body.short_pitch or body.name,
                "solution_description": body.solution_description or body.description,
                "target_users": body.target_users or body.target_audience or "",
                "problem": body.problem or body.description,
                "sector": body.sector,
                "country_code": body.country_code or "TN",
                "language": body.language or "fr",
            },
            "market_analysis": {},
        }
        graph_result = await market_graph.ainvoke(graph_input)
        market_analysis = graph_result.get("market_analysis") or {}

        if not market_analysis:
            raise RuntimeError("Aucun résultat market_analysis produit")

        if not body.access_token:
            raise RuntimeError("access_token requis pour persister le résultat dans backend-api")

        yield sse_event("step", {"status": "loading", "stage": "persist_result", "message": "Sauvegarde du résultat..."})
        completed_at = datetime.now(timezone.utc)
        persisted = await persist_market_result(
            idea_id=body.idea_id,
            result_json=market_analysis,
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
