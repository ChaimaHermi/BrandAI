"""DB-first step runner for market and marketing pipeline stages."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, AsyncIterator

import httpx

from agents.base_agent import PipelineState
from agents.marketing.marketing_agent import MarketingAgent
from app.services.persistence.market_marketing_persistence_service import (
    persist_market_result,
    persist_marketing_result,
)
from pipeline.market_graph import build_market_graph
from pipeline.market_strategy_graph import build_market_strategy_graph

_MIN_CLARITY_SCORE = 80

# (stage_id, loading_message, done_message)
MARKET_NODE_SEQUENCE = [
    ("keyword_extractor", "Extraction des mots-clés…", "Mots-clés extraits"),
    ("market_sizing", "Dimensionnement du marché…", "Dimensionnement terminé"),
    ("competitor", "Analyse des concurrents…", "Concurrents analysés"),
    ("voc", "Voice of Customer…", "VOC terminé"),
    ("trends_risks", "Tendances et risques…", "Tendances et risques analysés"),
    ("strategy_analysis_agent", "Stratégie SWOT / PESTEL…", "Stratégie terminée"),
    ("save_results", "Finalisation du rapport…", "Rapport de marché finalisé"),
]

_NODE_IDX = {name: i for i, (name, _, _) in enumerate(MARKET_NODE_SEQUENCE)}
_NODE_DONE = {name: msg for name, _, msg in MARKET_NODE_SEQUENCE}


class StepRunnerService:
    """Run pipeline steps by reloading context from backend-api."""

    def __init__(self) -> None:
        self.market_graph = build_market_graph()
        self.market_strategy_graph = build_market_strategy_graph()
        self.marketing_agent = MarketingAgent()

    @staticmethod
    def sse_event(event: str, data: dict) -> str:
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        data_lines = "\n".join(f"data: {line}" for line in payload.splitlines())
        return f"event: {event}\n{data_lines}\n\n"

    @staticmethod
    async def _fetch_idea_row(idea_id: int, access_token: str) -> dict[str, Any]:
        base = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")
        url = f"{base}/ideas/{idea_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def _validate_clarifier_state(idea_row: dict[str, Any]) -> dict[str, Any] | None:
        clarity_status = (idea_row.get("clarity_status") or "").strip().lower()
        clarity_score = int(idea_row.get("clarity_score") or 0)

        if clarity_status == "refused":
            return {"success": False, "reason": "clarifier_refused", "message": "Idée refusée par le Clarifier."}
        if clarity_status == "questions":
            return {
                "success": False,
                "reason": "clarifier_questions",
                "message": "Répondez aux questions du Clarifier avant de lancer le pipeline.",
            }
        if clarity_status != "clarified":
            return {"success": False, "reason": "clarifier_not_ready", "message": "L'idée n'est pas encore clarifiée."}
        if clarity_score < _MIN_CLARITY_SCORE:
            return {
                "success": False,
                "reason": "clarity_score_too_low",
                "message": f"Score de clarté insuffisant ({clarity_score}/{_MIN_CLARITY_SCORE}).",
            }
        return None

    @staticmethod
    def _build_clarified_context(idea_row: dict[str, Any]) -> dict[str, Any]:
        clarity_answers = idea_row.get("clarity_answers") or {}
        return {
            "short_pitch": idea_row.get("clarity_short_pitch") or idea_row.get("name") or "",
            "solution_description": idea_row.get("clarity_solution") or idea_row.get("description") or "",
            "target_users": idea_row.get("clarity_target_users") or idea_row.get("target_audience") or "",
            "problem": idea_row.get("clarity_problem") or idea_row.get("description") or "",
            "sector": idea_row.get("clarity_sector") or idea_row.get("sector") or "",
            "country": (idea_row.get("clarity_country") or "").strip() or "Non précisé",
            "country_code": idea_row.get("clarity_country_code") or "TN",
            "language": idea_row.get("clarity_language") or "fr",
            "budget_min": clarity_answers.get("budget_min"),
            "budget_max": clarity_answers.get("budget_max"),
            "budget_currency": (clarity_answers.get("budget_currency") or "").strip().upper(),
        }

    async def run_market_step(
        self,
        *,
        idea_id: int,
        clarified_idea: dict[str, Any],
    ) -> AsyncIterator[tuple[str, dict[str, Any] | None]]:
        """Yield progress events while running market graph."""
        first_name, first_msg, _ = MARKET_NODE_SEQUENCE[0]
        yield "step", {"status": "loading", "stage": first_name, "message": first_msg}

        market_input = {
            "idea_id": idea_id,
            "clarified_idea": clarified_idea,
            "market_analysis": {},
        }
        market_analysis: dict[str, Any] = {}
        async for chunk in self.market_graph.astream(market_input, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                if node_name not in _NODE_IDX:
                    continue
                idx = _NODE_IDX[node_name]
                yield "step", {"status": "done", "stage": node_name, "message": _NODE_DONE[node_name]}
                if idx + 1 < len(MARKET_NODE_SEQUENCE):
                    next_name, next_msg, _ = MARKET_NODE_SEQUENCE[idx + 1]
                    yield "step", {"status": "loading", "stage": next_name, "message": next_msg}
                if isinstance(node_output, dict) and "market_analysis" in node_output:
                    market_analysis = node_output["market_analysis"]
        yield "result", market_analysis

    async def run_marketing_step(
        self,
        *,
        idea_id: int,
        idea_row: dict[str, Any],
        clarified_idea: dict[str, Any],
        market_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        ps = PipelineState(
            idea_id=idea_id,
            name=idea_row.get("name") or clarified_idea.get("short_pitch") or "",
            sector=idea_row.get("sector") or clarified_idea.get("sector") or "",
            description=idea_row.get("description") or clarified_idea.get("solution_description") or "",
            target_audience=idea_row.get("target_audience") or clarified_idea.get("target_users") or "",
        )
        ps.clarified_idea = clarified_idea
        ps.market_analysis = market_analysis
        return await self.marketing_agent.run(ps) or {}

    async def stream_pipeline(self, *, idea_id: int, access_token: str) -> AsyncIterator[str]:
        started_at = datetime.now(timezone.utc)
        t0 = time.time()

        yield self.sse_event("step", {"status": "loading", "stage": "fetch_idea_context", "message": "Chargement de l'idée depuis la base…"})
        idea_row = await self._fetch_idea_row(idea_id, access_token)
        error_payload = self._validate_clarifier_state(idea_row)
        if error_payload is not None:
            yield self.sse_event("done", {"idea_id": idea_id, **error_payload})
            return
        clarified_idea = self._build_clarified_context(idea_row)
        yield self.sse_event("step", {"status": "done", "stage": "fetch_idea_context", "message": "Clarifier validé — démarrage de l'analyse de marché"})

        market_analysis: dict[str, Any] = {}
        async for event, data in self.run_market_step(idea_id=idea_id, clarified_idea=clarified_idea):
            if event == "result":
                market_analysis = data or {}
            else:
                yield self.sse_event(event, data or {})

        if not market_analysis:
            raise RuntimeError("Le graph market n'a produit aucun résultat.")

        yield self.sse_event("step", {"status": "loading", "stage": "persist_result", "message": "Sauvegarde de l'analyse de marché en base…"})
        completed_at = datetime.now(timezone.utc)
        persisted_market = await persist_market_result(
            idea_id=idea_id,
            result_json=market_analysis,
            started_at=started_at,
            completed_at=completed_at,
            access_token=access_token,
        )
        yield self.sse_event("step", {"status": "done", "stage": "persist_result", "message": "Analyse de marché sauvegardée"})

        yield self.sse_event("step", {"status": "loading", "stage": "marketing_plan", "message": "Génération du plan marketing…"})
        marketing_plan: dict[str, Any] = {}
        try:
            marketing_plan = await self.run_marketing_step(
                idea_id=idea_id,
                idea_row=idea_row,
                clarified_idea=clarified_idea,
                market_analysis=market_analysis,
            )
        except Exception as e:
            yield self.sse_event("step", {"status": "error", "stage": "marketing_plan", "message": f"Plan marketing non généré : {e}"})

        persisted_marketing = None
        if marketing_plan and not marketing_plan.get("error"):
            yield self.sse_event("step", {"status": "done", "stage": "marketing_plan", "message": "Plan marketing généré"})
            yield self.sse_event("step", {"status": "loading", "stage": "persist_marketing_result", "message": "Sauvegarde du plan marketing en base…"})
            persisted_marketing = await persist_marketing_result(
                idea_id=idea_id,
                result_json=marketing_plan,
                access_token=access_token,
            )
            yield self.sse_event("step", {"status": "done", "stage": "persist_marketing_result", "message": "Plan marketing sauvegardé"})
        elif marketing_plan and marketing_plan.get("error"):
            yield self.sse_event(
                "step",
                {
                    "status": "error",
                    "stage": "marketing_plan",
                    "message": "Plan marketing invalide (JSON/schema). Non sauvegardé.",
                },
            )

        yield self.sse_event(
            "done",
            {
                "success": True,
                "idea_id": idea_id,
                "status": "done",
                "persisted_id": persisted_market.get("id"),
                "persisted_marketing_id": persisted_marketing.get("id") if persisted_marketing else None,
                "elapsed_ms": int((time.time() - t0) * 1000),
            },
        )

    async def stream_market_strategy(self, *, idea_id: int, access_token: str) -> AsyncIterator[str]:
        started_at = datetime.now(timezone.utc)
        t0 = time.time()

        yield self.sse_event("step", {"status": "loading", "stage": "fetch_idea_context", "message": "Chargement de l'idée depuis la base…"})
        idea_row = await self._fetch_idea_row(idea_id, access_token)
        error_payload = self._validate_clarifier_state(idea_row)
        if error_payload is not None:
            yield self.sse_event("done", {"idea_id": idea_id, **error_payload})
            return
        clarified_idea = self._build_clarified_context(idea_row)
        yield self.sse_event("step", {"status": "done", "stage": "fetch_idea_context", "message": "Clarifier validé — démarrage de l'analyse de marché"})

        graph_input = {
            "idea_id": idea_id,
            "clarified_idea": clarified_idea,
            "market_analysis": {},
            "marketing_plan": {},
        }
        market_analysis: dict[str, Any] = {}
        marketing_plan: dict[str, Any] = {}

        # same market phase progress messages, then marketing phase.
        first_name, first_msg, _ = MARKET_NODE_SEQUENCE[0]
        yield self.sse_event("step", {"status": "loading", "stage": first_name, "message": first_msg})

        async for chunk in self.market_strategy_graph.astream(graph_input, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                if node_name in _NODE_IDX:
                    idx = _NODE_IDX[node_name]
                    yield self.sse_event("step", {"status": "done", "stage": node_name, "message": _NODE_DONE[node_name]})
                    if idx + 1 < len(MARKET_NODE_SEQUENCE):
                        next_name, next_msg, _ = MARKET_NODE_SEQUENCE[idx + 1]
                        yield self.sse_event("step", {"status": "loading", "stage": next_name, "message": next_msg})
                elif node_name == "marketing_plan":
                    yield self.sse_event("step", {"status": "loading", "stage": "marketing_plan", "message": "Génération du plan marketing…"})
                    yield self.sse_event("step", {"status": "done", "stage": "marketing_plan", "message": "Plan marketing généré"})

                if isinstance(node_output, dict):
                    if "market_analysis" in node_output:
                        market_analysis = node_output.get("market_analysis") or market_analysis
                    if "marketing_plan" in node_output:
                        marketing_plan = node_output.get("marketing_plan") or marketing_plan

        if not market_analysis:
            raise RuntimeError("Le graph market strategy n'a produit aucun résultat market.")

        yield self.sse_event("step", {"status": "loading", "stage": "persist_result", "message": "Sauvegarde de l'analyse de marché en base…"})
        completed_at = datetime.now(timezone.utc)
        persisted_market = await persist_market_result(
            idea_id=idea_id,
            result_json=market_analysis,
            started_at=started_at,
            completed_at=completed_at,
            access_token=access_token,
        )
        yield self.sse_event("step", {"status": "done", "stage": "persist_result", "message": "Analyse de marché sauvegardée"})

        persisted_marketing = None
        if marketing_plan and not marketing_plan.get("error"):
            yield self.sse_event("step", {"status": "loading", "stage": "persist_marketing_result", "message": "Sauvegarde du plan marketing en base…"})
            persisted_marketing = await persist_marketing_result(
                idea_id=idea_id,
                result_json=marketing_plan,
                access_token=access_token,
            )
            yield self.sse_event("step", {"status": "done", "stage": "persist_marketing_result", "message": "Plan marketing sauvegardé"})
        elif marketing_plan and marketing_plan.get("error"):
            yield self.sse_event(
                "step",
                {
                    "status": "error",
                    "stage": "marketing_plan",
                    "message": "Plan marketing invalide (JSON/schema). Non sauvegardé.",
                },
            )

        yield self.sse_event(
            "done",
            {
                "success": True,
                "idea_id": idea_id,
                "status": "done",
                "persisted_id": persisted_market.get("id"),
                "persisted_marketing_id": persisted_marketing.get("id") if persisted_marketing else None,
                "elapsed_ms": int((time.time() - t0) * 1000),
            },
        )
