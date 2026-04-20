import json
import logging
import time
from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.base_agent import PipelineState
from agents.clarifier.idea_clarifier_agent import IdeaClarifierAgent


router = APIRouter(tags=["Idea Clarifier"])
logger = logging.getLogger("brandai.clarifier.route")


def sse_event(event: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    data_lines = "\n".join(f"data: {line}" for line in payload.splitlines())
    return f"event: {event}\n{data_lines}\n\n"


def _xai_safety_block(result: dict) -> dict:
    safety = result.get("safety") or {}
    return {
        "safety_enabled": bool(safety),
        "safety_status": safety.get("status", "unknown"),
        "safety_provider": safety.get("provider", ""),
        "safety_model": safety.get("model", ""),
        "safety_fallback_used": bool(safety.get("fallback_used", False)),
    }


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
    answer_geography: Optional[str] = ""


# ══════════════════════════════════════════════════════════════
# STREAM — Appel initial (description seule)
# ══════════════════════════════════════════════════════════════

async def _stream_clarifier_start(body: ClarifierStartRequest):
    start_time = time.time()
    logger.info(
        "[clarifier/stream-start] request idea_id=%s name_len=%s desc_len=%s sector=%s target_len=%s",
        body.idea_id,
        len((body.name or "").strip()),
        len((body.description or "").strip()),
        (body.sector or "").strip(),
        len((body.target_audience or "").strip()),
    )

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
        logger.info("[clarifier/stream-start] idea_id=%s agent.run_start begin", body.idea_id)

        # 1 seul appel — sécurité + axes + réponse
        result = await agent.run_start(state)
        logger.info(
            "[clarifier/stream-start] idea_id=%s agent.run_start done type=%s",
            body.idea_id,
            result.get("type"),
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        result_type = result.get("type")

        # ── Étape XAI selon le résultat ──────────────────────
        if result_type == "refused":
            yield sse_event("step", {
                "status":  "error",
                "message": f"Projet refusé — {result.get('reason_category', 'non conforme')}",
                "elapsed_ms": elapsed_ms,
                **_xai_safety_block(result),
            })

        elif result_type == "questions":
            questions_count = len(result.get("questions") or [])
            yield sse_event("step", {
                "status":     "success",
                "message":    f"{questions_count} question(s) générée(s)",
                "sector":     result.get("detected_sector") or result.get("sector") or "",
                "elapsed_ms": elapsed_ms,
                "model":      agent.llm_rotator.current_info(),
                **_xai_safety_block(result),
            })

        elif result_type == "clarified":
            yield sse_event("step", {
                "status":     "success",
                "message":    "Idée claire — prêt pour le pipeline",
                "sector":     result.get("sector") or "",
                "elapsed_ms": elapsed_ms,
                "model":      agent.llm_rotator.current_info(),
                **_xai_safety_block(result),
            })

        yield sse_event("result", result)
        yield sse_event("done", {"success": True})
        logger.info(
            "[clarifier/stream-start] idea_id=%s stream done success elapsed_ms=%s",
            body.idea_id,
            elapsed_ms,
        )

    except Exception as e:
        logger.exception("[clarifier/stream-start] idea_id=%s stream error: %s", body.idea_id, e)
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
    logger.info(
        "[clarifier/stream-answer] request idea_id=%s desc_len=%s answers_len={problem:%s,target:%s,solution:%s,geo:%s}",
        body.idea_id,
        len((body.description or "").strip()),
        len((body.answer_problem or "").strip()),
        len((body.answer_target or "").strip()),
        len((body.answer_solution or "").strip()),
        len((body.answer_geography or "").strip()),
    )

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
        logger.info("[clarifier/stream-answer] idea_id=%s agent.run_answer begin", body.idea_id)

        answers = {
            "problem":  (body.answer_problem  or "").strip(),
            "target":   (body.answer_target   or "").strip(),
            "solution": (body.answer_solution or "").strip(),
            "geography": (body.answer_geography or "").strip(),
        }

        # 1 seul appel — sécurité sur réponses + structuration
        result = await agent.run_answer(state, answers)
        logger.info(
            "[clarifier/stream-answer] idea_id=%s agent.run_answer done type=%s",
            body.idea_id,
            result.get("type"),
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        result_type = result.get("type")

        if result_type == "refused":
            yield sse_event("step", {
                "status":  "error",
                "message": f"Projet refusé — {result.get('reason_category', 'non conforme')}",
                "elapsed_ms": elapsed_ms,
                **_xai_safety_block(result),
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
                    "geography": bool(result.get("country")) and result.get("country") != "Non précisé",
                },
                "sector":     result.get("sector", ""),
                "model":      agent.llm_rotator.current_info(),
                "elapsed_ms": elapsed_ms,
                **_xai_safety_block(result),
            })

        yield sse_event("result", result)
        yield sse_event("done", {"success": True})
        logger.info(
            "[clarifier/stream-answer] idea_id=%s stream done success elapsed_ms=%s",
            body.idea_id,
            elapsed_ms,
        )

    except Exception as e:
        logger.exception("[clarifier/stream-answer] idea_id=%s stream error: %s", body.idea_id, e)
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
        "geography": (body.answer_geography or "").strip(),
    }
    agent = IdeaClarifierAgent()
    return await agent.run_answer(state, answers)