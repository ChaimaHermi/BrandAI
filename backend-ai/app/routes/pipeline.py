import json
import os
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from workflows.pipeline_graph import build_graph


router = APIRouter(tags=["Pipeline"])
pipeline_graph = build_graph()


def sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class PipelineStreamRequest(BaseModel):
    idea_id: int
    name: str
    sector: Optional[str] = ""
    description: str
    target_audience: Optional[str] = ""

    # Optional pre-clarified payload. If present, graph skips clarifier.
    short_pitch: Optional[str] = None
    solution_description: Optional[str] = None
    target_users: Optional[str] = None
    problem: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = "TN"
    language: Optional[str] = "fr"

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


async def _persist_brand_identity_row(
    *,
    idea_id: int,
    brand_identity: dict,
    started_at: datetime,
    completed_at: datetime,
    access_token: str,
) -> dict:
    base = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")
    url = f"{base}/brand-identity/{idea_id}"
    payload = {
        "status": "done",
        "result_json": brand_identity,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def _persist_marketing_result(
    *,
    idea_id: int,
    result_json: dict,
    access_token: str,
) -> dict:
    base = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")
    url = f"{base}/marketing-plans/{idea_id}"
    payload = {
        "status": "done",
        "result_json": result_json,
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def _stream_pipeline(body: PipelineStreamRequest):
    started_at = datetime.now(timezone.utc)
    t0 = time.time()

    try:
        yield sse_event("step", {"status": "loading", "stage": "build_state", "message": "Préparation du pipeline..."})
        clarified_idea = {}

        if any([body.short_pitch, body.solution_description, body.target_users, body.problem]):
            clarified_idea = {
                "short_pitch": body.short_pitch or body.name,
                "solution_description": body.solution_description or body.description,
                "target_users": body.target_users or body.target_audience or "",
                "problem": body.problem or body.description,
                "sector": body.sector or "",
                "country": (body.country or "").strip() or "Non précisé",
                "country_code": body.country_code or "TN",
                "language": body.language or "fr",
            }
            yield sse_event("step", {
                "status": "success",
                "stage": "clarifier",
                "message": "Clarifier déjà validé — passage direct à Market Analysis",
            })
        else:
            yield sse_event("step", {
                "status": "loading",
                "stage": "clarifier",
                "message": "Exécution Clarifier...",
            })

        graph_input = {
            "idea_id": body.idea_id,
            "name": body.name or "",
            "sector": body.sector or "",
            "description": body.description,
            "target_audience": body.target_audience or "",
            "clarified_idea": clarified_idea,
            "market_analysis": {},
            "brand_identity": {},
            "marketing_plan": {},
            "status": "running",
            "errors": [],
        }

        yield sse_event("step", {
            "status": "loading",
            "stage": "run_pipeline_graph",
            "message": "Orchestration LangGraph en cours...",
        })
        yield sse_event("step", {
            "status": "loading",
            "stage": "run_market_analysis",
            "message": "Analyse de marché en cours...",
        })
        graph_result = await pipeline_graph.ainvoke(graph_input)
        status = graph_result.get("status", "error")
        errors = graph_result.get("errors", []) or []
        market_analysis = graph_result.get("market_analysis") or {}
        brand_identity = graph_result.get("brand_identity") or {}
        marketing_plan = graph_result.get("marketing_plan") or {}

        if not market_analysis:
            # Clarifier may have stopped with questions/refused.
            if status in {"questions", "refused"}:
                yield sse_event("result", {
                    "type": status,
                    "errors": errors,
                })
                yield sse_event("done", {"success": True, "stopped_at": "clarifier", "status": status})
                return
            raise RuntimeError("Pipeline terminé sans résultat market_analysis")

        if not body.access_token:
            raise RuntimeError("access_token requis pour persister le résultat")

        yield sse_event("step", {"status": "loading", "stage": "persist_result", "message": "Sauvegarde du résultat..."})
        completed_at = datetime.now(timezone.utc)
        persisted = await _persist_market_result(
            idea_id=body.idea_id,
            result_json=market_analysis,
            started_at=started_at,
            completed_at=completed_at,
            access_token=body.access_token,
        )

        if brand_identity:
            yield sse_event("step", {
                "status": "loading",
                "stage": "persist_brand_identity",
                "message": "Sauvegarde de l'identité de marque...",
            })
            await _persist_brand_identity_row(
                idea_id=body.idea_id,
                brand_identity=brand_identity,
                started_at=started_at,
                completed_at=completed_at,
                access_token=body.access_token,
            )

        persisted_marketing = None
        if marketing_plan:
            yield sse_event("step", {
                "status": "loading",
                "stage": "persist_marketing_result",
                "message": "Sauvegarde du plan marketing...",
            })
            persisted_marketing = await _persist_marketing_result(
                idea_id=body.idea_id,
                result_json=marketing_plan,
                access_token=body.access_token,
            )

        yield sse_event("result", {
            "market_analysis": market_analysis,
            "brand_identity": brand_identity,
            "marketing_plan": marketing_plan,
        })
        elapsed_ms = int((time.time() - t0) * 1000)
        yield sse_event("done", {
            "success": True,
            "idea_id": body.idea_id,
            "status": status,
            "persisted_id": persisted.get("id"),
            "persisted_marketing_id": (
                persisted_marketing.get("id") if persisted_marketing else None
            ),
            "elapsed_ms": elapsed_ms,
        })
    except Exception as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        yield sse_event("error", {"success": False, "message": str(e), "elapsed_ms": elapsed_ms})
        yield sse_event("done", {"success": False})


@router.post("/pipeline/stream")
async def pipeline_stream(body: PipelineStreamRequest):
    return StreamingResponse(
        _stream_pipeline(body),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

