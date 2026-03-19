import json
import time
from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.base_agent import PipelineState
from agents.idea_clarifier import IdeaClarifierAgent


router = APIRouter(tags=["Idea Clarifier"])


def sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class ClarifierStartRequest(BaseModel):
    idea_id:         int
    name:            Optional[str] = ""
    sector:          Optional[str] = ""
    description:     str
    target_audience: Optional[str] = ""


class ClarifierAnswerRequest(BaseModel):
    idea_id:         int
    name:            Optional[str] = ""
    sector:          Optional[str] = ""
    description:     str
    target_audience: Optional[str] = ""
    answer_problem:  Optional[str] = ""
    answer_target:   Optional[str] = ""
    answer_solution: Optional[str] = ""


# ══════════════════════════════════════════════════════════════
# STREAM — Appel initial (description seule)
# ══════════════════════════════════════════════════════════════

async def _stream_clarifier_start(body: ClarifierStartRequest):
    start_time = time.time()

    state = PipelineState(
        idea_id=body.idea_id,
        name=body.name or "",
        sector=body.sector or "",
        description=body.description,
        target_audience=body.target_audience or "",
    )
    agent = IdeaClarifierAgent()

    try:
        yield sse_event("step", {
            "status":  "loading",
            "message": "Analyse de votre idée...",
        })

        # 1 seul appel — sécurité + axes + réponse
        result = await agent.run_start(state)

        elapsed_ms = int((time.time() - start_time) * 1000)
        result_type = result.get("type")

        # ── Étape XAI selon le résultat ──────────────────────
        if result_type == "refused":
            yield sse_event("step", {
                "status":  "error",
                "message": f"Projet refusé — {result.get('reason_category', 'non conforme')}",
                "elapsed_ms": elapsed_ms,
            })

        elif result_type == "questions":
            questions_count = len(result.get("questions") or [])
            yield sse_event("step", {
                "status":     "success",
                "message":    f"{questions_count} question(s) générée(s)",
                "sector":     result.get("detected_sector") or result.get("sector") or "",
                "elapsed_ms": elapsed_ms,
                "model":      agent.llm_rotator.current_info(),
            })

        elif result_type == "clarified":
            yield sse_event("step", {
                "status":     "success",
                "message":    "Idée claire — prêt pour le pipeline",
                "sector":     result.get("sector") or "",
                "elapsed_ms": elapsed_ms,
                "model":      agent.llm_rotator.current_info(),
            })

        yield sse_event("result", result)
        yield sse_event("done", {"success": True})

    except Exception as e:
        yield sse_event("step", {
            "status":  "error",
            "message": f"Erreur : {str(e)}",
        })
        yield sse_event("error", {"message": str(e)})
        yield sse_event("done", {"success": False})


@router.post("/clarifier/start/stream")
async def clarifier_start_stream(body: ClarifierStartRequest):
    return StreamingResponse(
        _stream_clarifier_start(body),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ══════════════════════════════════════════════════════════════
# STREAM — Appel après réponses utilisateur
# ══════════════════════════════════════════════════════════════

async def _stream_clarifier_answer(body: ClarifierAnswerRequest):
    start_time = time.time()

    state = PipelineState(
        idea_id=body.idea_id,
        name=body.name or "",
        sector=body.sector or "",
        description=body.description,
        target_audience=body.target_audience or "",
    )
    agent = IdeaClarifierAgent()

    try:
        yield sse_event("step", {
            "status":  "loading",
            "message": "Analyse de vos réponses...",
        })

        answers = {
            "problem":  (body.answer_problem  or "").strip(),
            "target":   (body.answer_target   or "").strip(),
            "solution": (body.answer_solution or "").strip(),
        }

        # 1 seul appel — sécurité sur réponses + structuration
        result = await agent.run_answer(state, answers)

        elapsed_ms = int((time.time() - start_time) * 1000)
        result_type = result.get("type")

        if result_type == "refused":
            yield sse_event("step", {
                "status":  "error",
                "message": f"Projet refusé — {result.get('reason_category', 'non conforme')}",
                "elapsed_ms": elapsed_ms,
            })

        elif result_type == "clarified":
            score = result.get("score", 0)
            yield sse_event("step", {
                "status":     "success",
                "message":    f"Idée clarifiée — score {score}/100",
                "score":      score,
                "dimensions": {
                    "problem":  bool(result.get("problem")),
                    "target":   bool(result.get("target_users")),
                    "solution": bool(result.get("solution_description")),
                },
                "sector":     result.get("sector", ""),
                "model":      agent.llm_rotator.current_info(),
                "elapsed_ms": elapsed_ms,
            })

        yield sse_event("result", result)
        yield sse_event("done", {"success": True})

    except Exception as e:
        yield sse_event("step", {
            "status":  "error",
            "message": f"Erreur : {str(e)}",
        })
        yield sse_event("error", {"message": str(e)})
        yield sse_event("done", {"success": False})


@router.post("/clarifier/answer/stream")
async def clarifier_answer_stream(body: ClarifierAnswerRequest):
    return StreamingResponse(
        _stream_clarifier_answer(body),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ══════════════════════════════════════════════════════════════
# ENDPOINTS JSON (sans stream) — conservés
# ══════════════════════════════════════════════════════════════

@router.post("/clarifier/start")
async def clarifier_start(body: ClarifierStartRequest):
    state = PipelineState(
        idea_id=body.idea_id,
        name=body.name or "",
        sector=body.sector or "",
        description=body.description,
        target_audience=body.target_audience or "",
    )
    agent = IdeaClarifierAgent()
    return await agent.run_start(state)


@router.post("/clarifier/answer")
async def clarifier_answer(body: ClarifierAnswerRequest):
    state = PipelineState(
        idea_id=body.idea_id,
        name=body.name or "",
        sector=body.sector or "",
        description=body.description,
        target_audience=body.target_audience or "",
    )
    answers = {
        "problem":  (body.answer_problem  or "").strip(),
        "target":   (body.answer_target   or "").strip(),
        "solution": (body.answer_solution or "").strip(),
    }
    agent = IdeaClarifierAgent()
    return await agent.run_answer(state, answers)