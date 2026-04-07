import json
import os
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.persistence.market_marketing_persistence_service import (
    persist_market_result,
    persist_marketing_result,
)
from workflows.pipeline_graph import build_graph


router = APIRouter(tags=["Pipeline"])
pipeline_graph = build_graph()


def sse_event(event: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    data_lines = "\n".join(f"data: {line}" for line in payload.splitlines())
    return f"event: {event}\n{data_lines}\n\n"


class PipelineStreamRequest(BaseModel):
    idea_id: int
    access_token: str


_MIN_CLARITY_SCORE = 80


async def _fetch_idea_context(idea_id: int, access_token: str) -> dict[str, Any]:
    base = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")
    url = f"{base}/ideas/{idea_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


def _validation_done_payload(idea_row: dict[str, Any]) -> dict[str, Any] | None:
    clarity_status = (idea_row.get("clarity_status") or "").strip().lower()
    clarity_score = int(idea_row.get("clarity_score") or 0)

    if clarity_status == "refused":
        return {
            "success": False,
            "reason": "clarifier_refused",
            "message": "Idée refusée par le Clarifier.",
        }

    if clarity_status == "questions":
        return {
            "success": False,
            "reason": "clarifier_questions",
            "message": "Répondez aux questions du Clarifier avant de lancer le pipeline.",
        }

    if clarity_status != "clarified":
        return {
            "success": False,
            "reason": "clarifier_not_ready",
            "message": "L'idée n'est pas encore clarifiée.",
        }

    if clarity_score < _MIN_CLARITY_SCORE:
        return {
            "success": False,
            "reason": "clarity_score_too_low",
            "message": f"Score de clarté insuffisant ({clarity_score}/{_MIN_CLARITY_SCORE}).",
        }

    return None


async def _stream_pipeline(body: PipelineStreamRequest):
    started_at = datetime.now(timezone.utc)
    t0 = time.time()

    try:
        yield sse_event("step", {"status": "loading", "stage": "build_state", "message": "Préparation du pipeline..."})
        yield sse_event(
            "step",
            {
                "status": "loading",
                "stage": "fetch_idea_context",
                "message": "Chargement de l'idée depuis la base...",
            },
        )
        idea_row = await _fetch_idea_context(body.idea_id, body.access_token)

        invalid = _validation_done_payload(idea_row)
        if invalid is not None:
            yield sse_event(
                "done",
                {
                    "idea_id": body.idea_id,
                    **invalid,
                },
            )
            return

        clarified_idea = {
            "short_pitch": idea_row.get("clarity_short_pitch") or idea_row.get("name") or "",
            "solution_description": (
                idea_row.get("clarity_solution") or idea_row.get("description") or ""
            ),
            "target_users": (
                idea_row.get("clarity_target_users") or idea_row.get("target_audience") or ""
            ),
            "problem": idea_row.get("clarity_problem") or idea_row.get("description") or "",
            "sector": idea_row.get("clarity_sector") or idea_row.get("sector") or "",
            "country": (idea_row.get("clarity_country") or "").strip() or "Non précisé",
            "country_code": idea_row.get("clarity_country_code") or "TN",
            "language": idea_row.get("clarity_language") or "fr",
        }
        yield sse_event(
            "step",
            {
                "status": "success",
                "stage": "clarifier",
                "message": "Clarifier validé en base — passage à Market Analysis",
            },
        )

        graph_input = {
            "idea_id": body.idea_id,
            "name": idea_row.get("name") or clarified_idea["short_pitch"] or "",
            "sector": idea_row.get("sector") or clarified_idea["sector"] or "",
            "description": idea_row.get("description") or clarified_idea["solution_description"] or "",
            "target_audience": idea_row.get("target_audience") or clarified_idea["target_users"] or "",
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
        marketing_plan = graph_result.get("marketing_plan") or {}

        if not market_analysis:
            # Clarifier may have stopped with questions/refused.
            if status in {"questions", "refused"}:
                yield sse_event(
                    "done",
                    {
                        "success": True,
                        "stopped_at": "clarifier",
                        "status": status,
                        "errors": errors,
                    },
                )
                return
            raise RuntimeError("Pipeline terminé sans résultat market_analysis")

        yield sse_event("step", {"status": "loading", "stage": "persist_result", "message": "Sauvegarde du résultat..."})
        completed_at = datetime.now(timezone.utc)
        persisted = await persist_market_result(
            idea_id=body.idea_id,
            result_json=market_analysis,
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
            persisted_marketing = await persist_marketing_result(
                idea_id=body.idea_id,
                result_json=marketing_plan,
                access_token=body.access_token,
            )

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

