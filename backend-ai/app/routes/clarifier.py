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
    # Réponses aux 3 questions — champs séparés
    answer_problem:  Optional[str] = ""
    answer_target:   Optional[str] = ""
    answer_solution: Optional[str] = ""


async def _stream_clarifier_start(body: ClarifierStartRequest):
    import time
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
        # Étape 1 — sécurité
        yield sse_event("step", {
            "status":  "loading",
            "message": "Vérification de sécurité...",
        })

        safety = await agent.check_safety(state)
        if safety.get("sector") and not state.sector:
            state.sector = safety["sector"]

        if not safety["safe"]:
            refusal_msg = (safety.get("refusal_message") or "").strip()
            if not refusal_msg:
                # Fallback ultime (ne devrait pas arriver si l'agent fonctionne)
                refusal_msg = "BrandAI ne peut pas vous accompagner dans ce type de projet."
            yield sse_event("step", {
                "status":  "error",
                "message": f"Projet refusé — {safety.get('reason_category')}",
            })
            yield sse_event("result", {
                "type":            "refused",
                # Compat front: certains clients lisent `message`,
                # d'autres `refusal_message`.
                "message":         refusal_msg,
                "refusal_message": refusal_msg,
                "reason_category": safety.get("reason_category"),
                "score":           0,
            })
            yield sse_event("done", {"success": True})
            return

        yield sse_event("step", {
            "status":     "success",
            "message":    "Sécurité — projet conforme",
            "sector":     safety.get("sector") or "",
            "confidence": safety.get("confidence", 0),
        })

        # Étape 2 — générer les 3 questions
        yield sse_event("step", {
            "status":  "loading",
            "message": "Analyse de votre idée...",
        })

        result = await agent.generate_questions(state)
        # Ajouter le secteur détecté dans le result
        # pour que le frontend le renvoie au 2ème appel
        result["detected_sector"] = state.sector or ""

        elapsed_ms = int((time.time() - start_time) * 1000)
        yield sse_event("step", {
            "status":     "success",
            "message":    "3 questions générées",
            "sector":     state.sector or safety.get("sector") or "",
            "confidence": safety.get("confidence", 0),
            "model":      agent.llm_rotator.current_info(),
            "elapsed_ms": elapsed_ms,
        })

        print(
            f"[ROUTE] questions : "
            f"{json.dumps(result, ensure_ascii=False)[:300]}"
        )
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


async def _stream_clarifier_answer(body: ClarifierAnswerRequest):
    import time
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
            "problem":  body.answer_problem or "",
            "target":   body.answer_target or "",
            "solution": body.answer_solution or "",
        }

        result = await agent.run_interactive(
            state,
            answers=answers,
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
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

        print(
            f"[ROUTE] result : "
            f"{json.dumps(result, ensure_ascii=False)[:300]}"
        )
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
    result = await agent.run_interactive(state)
    return result


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
        "problem":  body.answer_problem or "",
        "target":   body.answer_target or "",
        "solution": body.answer_solution or "",
    }
    agent = IdeaClarifierAgent()
    result = await agent.run_interactive(state, answers=answers)
    return result