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
    idea_id:              int
    name:                 Optional[str] = ""
    sector:               Optional[str] = ""
    description:          str
    target_audience:      Optional[str] = ""
    answers:              List[str]
    conversation_history: Optional[List[dict]] = []


# ══════════════════════════════════════════════════════════════
#  /clarifier/start/stream
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
        # ── Étape 1 : sécurité ───────────────────────────────
        yield sse_event("step", {
            "status":  "loading",
            "message": "Vérification de sécurité en cours...",
        })

        safety = await agent.check_safety(state)

        # Mettre à jour le secteur détecté dans le state
        if safety.get("sector") and not state.sector:
            state.sector = safety["sector"]

        if not safety["safe"]:
            yield sse_event("step", {
                "status":  "error",
                "message": f"Projet refusé — {safety.get('reason_category', 'sécurité')}",
            })
            result = {
                "type":            "refused",
                "safe":            False,
                "reason_category": safety.get("reason_category"),
                "refusal_message": safety.get("refusal_message"),
                "message":         safety.get("refusal_message", ""),
                "score":           0,
            }
            print(f"[ROUTE] SSE result : {json.dumps(result, ensure_ascii=False)[:300]}")
            yield sse_event("result", result)
            yield sse_event("done", {"success": True})
            return

        yield sse_event("step", {
            "status":     "success",
            "message":    "Sécurité — projet conforme",
            "sector":     safety.get("sector") or "",
            "confidence": safety.get("confidence", 0),
        })

        # ── Étape 2 : richesse ───────────────────────────────
        yield sse_event("step", {
            "status":  "loading",
            "message": "Analyse de la description...",
        })

        richness = await agent._evaluate_richness(state)
        missing  = [
            k for k in ["problem", "target", "solution"]
            if not richness.get("has_" + k)
        ]

        yield sse_event("step", {
            "status":     "info",
            "message":    f"Analyse — {len(missing)} dimension(s) manquante(s)",
            "dimensions": {
                "problem":  richness["has_problem"],
                "target":   richness["has_target"],
                "solution": richness["has_solution"],
            },
        })

        questions = agent.build_questions(richness)
        yield sse_event("step", {
            "status":  "info",
            "message": f"{len(questions)} question(s) nécessaire(s)",
        })

        # ── Étape 3 : générer via LLM ────────────────────────
        yield sse_event("step", {
            "status":  "loading",
            "message": "Génération de la réponse...",
        })

        result = await agent.generate_clarified_idea(state)

        elapsed_ms = int((time.time() - start_time) * 1000)
        result_type = result.get("type", "questions")

        if result_type == "clarified":
            yield sse_event("step", {
                "status":     "success",
                "message":    f"Idée clarifiée — score {result.get('score', 0)}/100",
                "score":      result.get("score", 0),
                "model":      agent.llm_rotator.current_info(),
                "elapsed_ms": elapsed_ms,
            })
        else:
            yield sse_event("step", {
                "status":  "success",
                "message": "Analyse terminée",
            })

        print(f"[ROUTE] SSE result : {json.dumps(result, ensure_ascii=False)[:300]}")
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
#  /clarifier/answer/stream
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
            "message": "Analyse de votre réponse...",
        })

        result = await agent.generate_clarified_idea(
            state,
            user_answers=body.answers,
            conversation_history=body.conversation_history or [],
        )

        elapsed_ms  = int((time.time() - start_time) * 1000)
        result_type = result.get("type", "questions")

        if result_type == "off_topic":
            yield sse_event("step", {
                "status":  "info",
                "message": "Réponse hors sujet détectée",
            })

        elif result_type == "questions":
            score = result.get("score", 0)
            yield sse_event("step", {
                "status":     "info",
                "message":    f"Score {score}/100 — précisions nécessaires",
                "score":      score,
                "elapsed_ms": elapsed_ms,
            })

        elif result_type == "clarified":
            score = result.get("score", 0)
            yield sse_event("step", {
                "status":     "success",
                "message":    f"Idée clarifiée — score {score}/100",
                "score":      score,
                "model":      agent.llm_rotator.current_info(),
                "elapsed_ms": elapsed_ms,
            })

        print(f"[ROUTE] SSE result : {json.dumps(result, ensure_ascii=False)[:300]}")
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
#  Endpoints sync (non-SSE) — gardés pour compatibilité
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
    agent  = IdeaClarifierAgent()
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
    agent  = IdeaClarifierAgent()
    result = await agent.run_interactive(
        state,
        user_answers=body.answers,
        conversation_history=body.conversation_history or [],
    )
    return result