import json
import time
from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.base_agent import PipelineState
from agents.idea_clarifier import IdeaClarifierAgent
from tools.idea_tools import validate_idea_input


router = APIRouter(tags=["Idea Clarifier"])


def sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class ClarifierStartRequest(BaseModel):
    idea_id: int
    name: str
    sector: str
    description: str
    target_audience: Optional[str] = ""


class ClarifierAnswerRequest(BaseModel):
    idea_id: int
    name: str
    sector: str
    description: str
    target_audience: Optional[str] = ""
    answers: List[str]


@router.post("/clarifier/start")
async def clarifier_start(body: ClarifierStartRequest):
    state = PipelineState(
        idea_id=body.idea_id,
        name=body.name,
        sector=body.sector,
        description=body.description,
        target_audience=body.target_audience or "",
    )
    agent = IdeaClarifierAgent()
    result = await agent.run_interactive(state, user_answers=None)
    return result


@router.post("/clarifier/answer")
async def clarifier_answer(body: ClarifierAnswerRequest):
    state = PipelineState(
        idea_id=body.idea_id,
        name=body.name,
        sector=body.sector,
        description=body.description,
        target_audience=body.target_audience or "",
    )
    agent = IdeaClarifierAgent()
    result = await agent.run_interactive(state, user_answers=body.answers)
    return result


async def _stream_clarifier_start(body: ClarifierStartRequest):
    start_time = time.time()
    state = PipelineState(
        idea_id=body.idea_id,
        name=body.name,
        sector=body.sector,
        description=body.description,
        target_audience=body.target_audience or "",
    )
    agent = IdeaClarifierAgent()

    errors = validate_idea_input(state.name, state.description, state.sector)
    if errors:
        yield sse_event("result", {
            "safe": True,
            "questions": [],
            "clarified_idea": {},
            "clarity_score": 0,
            "ready": False,
            "error": "; ".join(errors),
        })
        return

    yield sse_event("step", {
        "status": "loading",
        "message": "Vérification de sécurité en cours...",
    })
    safety = await agent.check_safety(state)

    if not safety["safe"]:
        yield sse_event("step", {
            "status": "error",
            "message": f"Projet refusé — {safety.get('reason_category', 'sécurité')}",
        })
        yield sse_event("result", {
            "safe": False,
            "reason_category": safety.get("reason_category"),
            "refusal_message": safety.get("refusal_message"),
            "questions": [],
            "clarified_idea": {},
            "clarity_score": 0,
            "ready": False,
        })
        return

    yield sse_event("step", {
        "status": "success",
        "message": "Sécurité — projet conforme",
        "sector": safety.get("sector") or "",
        "confidence": safety.get("confidence", 0),
    })

    yield sse_event("step", {
        "status": "loading",
        "message": "Analyse de la description...",
    })
    richness = await agent._evaluate_richness(state)
    missing = [k for k in ["problem", "target", "solution"] if not richness.get("has_" + k)]
    yield sse_event("step", {
        "status": "info",
        "message": f"Analyse — {len(missing)} dimension(s) manquante(s)",
        "dimensions": {
            "problem": richness["has_problem"],
            "target": richness["has_target"],
            "solution": richness["has_solution"],
        },
    })
    questions = agent.build_questions(richness)
    yield sse_event("step", {
        "status": "info",
        "message": f"{len(questions)} question(s) nécessaire(s)",
    })
    yield sse_event("result", {
        "safe": True,
        "questions": questions,
        "clarified_idea": {},
        "clarity_score": 0,
        "ready": False,
    })


@router.post("/clarifier/start/stream")
async def clarifier_start_stream(body: ClarifierStartRequest):
    return StreamingResponse(
        _stream_clarifier_start(body),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _stream_clarifier_answer(body: ClarifierAnswerRequest):
    start_time = time.time()
    state = PipelineState(
        idea_id=body.idea_id,
        name=body.name,
        sector=body.sector,
        description=body.description,
        target_audience=body.target_audience or "",
    )
    agent = IdeaClarifierAgent()

    yield sse_event("step", {
        "status": "loading",
        "message": "Génération du JSON structuré...",
    })
    clarified = await agent.generate_clarified_idea(state, body.answers)
    score = clarified.get("clarity_score", 0)
    model_info = agent.llm_rotator.current_info()
    elapsed_ms = int((time.time() - start_time) * 1000)
    yield sse_event("step", {
        "status": "success",
        "message": "JSON généré",
        "score": score,
        "model": model_info,
        "elapsed_ms": elapsed_ms,
    })
    yield sse_event("result", {
        "safe": True,
        "questions": [],
        "clarified_idea": clarified,
        "clarity_score": score,
        "ready": True,
    })


@router.post("/clarifier/answer/stream")
async def clarifier_answer_stream(body: ClarifierAnswerRequest):
    return StreamingResponse(
        _stream_clarifier_answer(body),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

