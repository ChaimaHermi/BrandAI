import json
import os
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.base_agent import PipelineState
from agents.marketing.marketing_agent import MarketingAgent
from app.services.persistence.market_marketing_persistence_service import (
    persist_market_result,
    persist_marketing_result,
)
from pipeline.market_graph import build_market_graph


router = APIRouter(tags=["Pipeline"])
market_graph = build_market_graph()
marketing_agent = MarketingAgent()


def sse_event(event: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    data_lines = "\n".join(f"data: {line}" for line in payload.splitlines())
    return f"event: {event}\n{data_lines}\n\n"


class PipelineStreamRequest(BaseModel):
    idea_id: int
    access_token: str


_MIN_CLARITY_SCORE = 80

# ── Market graph node sequence (matches LangGraph edge order) ─────────────────
# (stage_id, loading_message, done_message)
MARKET_NODE_SEQUENCE = [
    ("keyword_extractor",       "Extraction des mots-clés…",    "Mots-clés extraits"),
    ("market_sizing",           "Dimensionnement du marché…",   "Dimensionnement terminé"),
    ("competitor",              "Analyse des concurrents…",     "Concurrents analysés"),
    ("voc",                     "Voice of Customer…",           "VOC terminé"),
    ("trends_risks",            "Tendances et risques…",        "Tendances et risques analysés"),
    ("strategy_analysis_agent", "Stratégie SWOT / PESTEL…",    "Stratégie terminée"),
    ("save_results",            "Finalisation du rapport…",     "Rapport de marché finalisé"),
]

_NODE_IDX  = {name: i   for i, (name, _, _) in enumerate(MARKET_NODE_SEQUENCE)}
_NODE_LOAD = {name: msg for name, msg, _   in MARKET_NODE_SEQUENCE}
_NODE_DONE = {name: msg for name, _, msg   in MARKET_NODE_SEQUENCE}


async def _fetch_idea_context(idea_id: int, access_token: str) -> dict[str, Any]:
    base = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")
    url = f"{base}/ideas/{idea_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


def _validation_error(idea_row: dict[str, Any]) -> dict[str, Any] | None:
    clarity_status = (idea_row.get("clarity_status") or "").strip().lower()
    clarity_score  = int(idea_row.get("clarity_score") or 0)

    if clarity_status == "refused":
        return {"success": False, "reason": "clarifier_refused",    "message": "Idée refusée par le Clarifier."}
    if clarity_status == "questions":
        return {"success": False, "reason": "clarifier_questions",  "message": "Répondez aux questions du Clarifier avant de lancer le pipeline."}
    if clarity_status != "clarified":
        return {"success": False, "reason": "clarifier_not_ready",  "message": "L'idée n'est pas encore clarifiée."}
    if clarity_score < _MIN_CLARITY_SCORE:
        return {"success": False, "reason": "clarity_score_too_low","message": f"Score de clarté insuffisant ({clarity_score}/{_MIN_CLARITY_SCORE})."}
    return None


async def _stream_pipeline(body: PipelineStreamRequest):
    started_at = datetime.now(timezone.utc)
    t0 = time.time()

    try:
        # ── 1. Initialisation ─────────────────────────────────────────────
        yield sse_event("step", {
            "status": "loading",
            "stage":  "build_state",
            "message": "Préparation du pipeline…",
        })

        # ── 2. Chargement + validation de l'idée ─────────────────────────
        yield sse_event("step", {
            "status": "loading",
            "stage":  "fetch_idea_context",
            "message": "Chargement de l'idée depuis la base…",
        })
        idea_row = await _fetch_idea_context(body.idea_id, body.access_token)

        error_payload = _validation_error(idea_row)
        if error_payload is not None:
            yield sse_event("done", {"idea_id": body.idea_id, **error_payload})
            return

        clarified_idea = {
            "short_pitch":          idea_row.get("clarity_short_pitch") or idea_row.get("name") or "",
            "solution_description": idea_row.get("clarity_solution")    or idea_row.get("description") or "",
            "target_users":         idea_row.get("clarity_target_users")or idea_row.get("target_audience") or "",
            "problem":              idea_row.get("clarity_problem")     or idea_row.get("description") or "",
            "sector":               idea_row.get("clarity_sector")      or idea_row.get("sector") or "",
            "country":              (idea_row.get("clarity_country") or "").strip() or "Non précisé",
            "country_code":         idea_row.get("clarity_country_code") or "TN",
            "language":             idea_row.get("clarity_language") or "fr",
        }

        yield sse_event("step", {
            "status": "done",
            "stage":  "fetch_idea_context",
            "message": "Clarifier validé — démarrage de l'analyse de marché",
        })

        # ── 3. Analyse de marché — streaming nœud par nœud ───────────────
        first_name, first_msg, _ = MARKET_NODE_SEQUENCE[0]
        yield sse_event("step", {
            "status": "loading",
            "stage":  first_name,
            "message": first_msg,
        })

        market_input = {
            "idea_id":         body.idea_id,
            "clarified_idea":  clarified_idea,
            "market_analysis": {},
        }

        market_analysis: dict = {}

        async for chunk in market_graph.astream(market_input, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                if node_name not in _NODE_IDX:
                    continue

                idx = _NODE_IDX[node_name]

                # Nœud terminé → done
                yield sse_event("step", {
                    "status": "done",
                    "stage":  node_name,
                    "message": _NODE_DONE[node_name],
                })

                # Prochain nœud → loading (sauf après save_results)
                if idx + 1 < len(MARKET_NODE_SEQUENCE):
                    next_name, next_msg, _ = MARKET_NODE_SEQUENCE[idx + 1]
                    yield sse_event("step", {
                        "status": "loading",
                        "stage":  next_name,
                        "message": next_msg,
                    })

                if isinstance(node_output, dict) and "market_analysis" in node_output:
                    market_analysis = node_output["market_analysis"]

        if not market_analysis:
            raise RuntimeError("Le graph market n'a produit aucun résultat.")

        # ── 4. Plan marketing ─────────────────────────────────────────────
        yield sse_event("step", {
            "status": "loading",
            "stage":  "marketing_plan",
            "message": "Génération du plan marketing…",
        })

        ps = PipelineState(
            idea_id=body.idea_id,
            name=idea_row.get("name") or clarified_idea["short_pitch"],
            sector=idea_row.get("sector") or clarified_idea["sector"],
            description=idea_row.get("description") or clarified_idea["solution_description"],
            target_audience=idea_row.get("target_audience") or clarified_idea["target_users"],
        )
        ps.clarified_idea  = clarified_idea
        ps.market_analysis = market_analysis

        marketing_plan: dict = {}
        try:
            marketing_plan = await marketing_agent.run(ps) or {}
        except Exception as e:
            # Marketing is non-blocking — log but don't fail the pipeline
            marketing_plan = {}
            yield sse_event("step", {
                "status": "error",
                "stage":  "marketing_plan",
                "message": f"Plan marketing non généré : {e}",
            })

        if marketing_plan:
            yield sse_event("step", {
                "status": "done",
                "stage":  "marketing_plan",
                "message": "Plan marketing généré",
            })

        # ── 5. Sauvegarde ─────────────────────────────────────────────────
        yield sse_event("step", {
            "status": "loading",
            "stage":  "persist_result",
            "message": "Sauvegarde des résultats en base…",
        })

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
            persisted_marketing = await persist_marketing_result(
                idea_id=body.idea_id,
                result_json=marketing_plan,
                access_token=body.access_token,
            )

        yield sse_event("step", {
            "status": "done",
            "stage":  "persist_result",
            "message": "Résultats sauvegardés avec succès",
        })

        elapsed_ms = int((time.time() - t0) * 1000)
        yield sse_event("done", {
            "success":                True,
            "idea_id":                body.idea_id,
            "status":                 "done",
            "persisted_id":           persisted.get("id"),
            "persisted_marketing_id": persisted_marketing.get("id") if persisted_marketing else None,
            "elapsed_ms":             elapsed_ms,
        })

    except Exception as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        yield sse_event("error", {"success": False, "message": str(e), "elapsed_ms": elapsed_ms})
        yield sse_event("done",  {"success": False})


@router.post("/pipeline/stream")
async def pipeline_stream(body: PipelineStreamRequest):
    return StreamingResponse(
        _stream_pipeline(body),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
