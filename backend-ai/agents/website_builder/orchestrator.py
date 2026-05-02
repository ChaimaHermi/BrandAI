from __future__ import annotations

import logging
from typing import Any

from langsmith import traceable
from agents.base_agent import PipelineState
from tools.website_builder.build_tool import build_website_html
from tools.website_builder.context_tool import WebsiteContextTool
from tools.website_builder.description_renderer import (
    render_context_summary,
    render_description_summary,
)
from tools.website_builder.llm_gateway import WebsiteBuilderLlmGateway
from tools.website_builder.planning_tool import generate_website_plan
from tools.website_builder.refinement_tool import refine_website_description
from tools.website_builder.revision_tool import revise_website_html
from tools.website_builder.step_streamer import (
    DESCRIPTION_TICKS,
    GENERATION_TICKS,
    REFINEMENT_TICKS,
    REVISION_TICKS,
    StepEmitter,
    run_with_progress,
)
from tools.website_builder.validator_tool import sanitize_navigation_html
from tools.website_builder.vercel_deploy import delete_vercel_deployment, deploy_html_to_vercel
from tools.website_builder.website_project_persistence import (
    append_website_message,
    build_message,
    patch_website_project,
)
from tools.website_builder.website_renderer import html_stats, validate_html_document

logger = logging.getLogger("brandai.website_builder.orchestrator")


def _qa(html: str) -> tuple[str, dict[str, int]]:
    """Nettoyage navigation + validation basique. Pas de LLM."""
    html = sanitize_navigation_html(html)
    validate_html_document(html)
    return html, html_stats(html)


class WebsiteBuilderOrchestrator(WebsiteBuilderLlmGateway):
    """
    Orchestrateur principal du Website Builder.
    Hérite de WebsiteBuilderLlmGateway pour les appels LLM (Azure OpenAI).
    Pipeline : contexte → description → refinement → génération HTML → QA → révision → déploiement.
    """

    def __init__(self) -> None:
        super().__init__()
        self.context_tool = WebsiteContextTool()

    async def run(self, state: PipelineState) -> Any:
        raise NotImplementedError("Use orchestrator methods directly.")

    # ── Phase 1 ───────────────────────────────────────────────────────────────

    @traceable(name="website_builder.orchestrator.fetch_context", tags=["website_builder", "context"])
    async def fetch_context(self, *, idea_id: int, token: str) -> dict[str, Any]:
        ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
        return {**ctx.as_dict(), "summary_md": render_context_summary(ctx)}

    # ── Phase 2 : Description ─────────────────────────────────────────────────

    @traceable(name="website_builder.orchestrator.generate_description", tags=["website_builder", "description"])
    async def generate_description(self, *, idea_id: int, token: str) -> dict[str, Any]:
        ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
        description = await generate_website_plan(
            ctx=ctx,
            invoke_llm=self.invoke_llm,
            parse_json=self.parse_json_output,
        )
        await patch_website_project(
            idea_id=idea_id, access_token=token,
            patch={"status": "draft", "description_json": description},
        )
        await append_website_message(
            idea_id=idea_id, access_token=token,
            message=build_message(
                role="assistant", msg_type="description_result",
                content="Description du site generee.",
                meta={"sections": len(description.get("sections") or [])},
            ),
        )
        return {
            "context": {**ctx.as_dict(), "summary_md": render_context_summary(ctx)},
            "description": description,
            "description_summary_md": render_description_summary(description),
        }

    # ── Phase 2.5 : Refinement ────────────────────────────────────────────────

    @traceable(name="website_builder.orchestrator.refine_description", tags=["website_builder", "refinement"])
    async def refine_description(
        self, *, idea_id: int, token: str,
        current_description: dict[str, Any], user_feedback: str,
    ) -> dict[str, Any]:
        ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
        new_description = await refine_website_description(
            ctx=ctx,
            current_description=current_description,
            user_feedback=user_feedback,
            invoke_llm=self.invoke_llm,
            parse_json=self.parse_json_output,
        )
        await patch_website_project(
            idea_id=idea_id, access_token=token,
            patch={"status": "draft", "description_json": new_description},
        )
        await append_website_message(
            idea_id=idea_id, access_token=token,
            message=build_message(role="user", msg_type="description_refine_request", content=user_feedback.strip()),
        )
        await append_website_message(
            idea_id=idea_id, access_token=token,
            message=build_message(
                role="assistant", msg_type="description_refine_result",
                content="Description mise a jour.",
                meta={"sections": len(new_description.get("sections") or [])},
            ),
        )
        return {
            "context": {**ctx.as_dict(), "summary_md": render_context_summary(ctx)},
            "description": new_description,
            "description_summary_md": render_description_summary(new_description),
        }

    # ── Approbation ───────────────────────────────────────────────────────────

    @traceable(name="website_builder.orchestrator.approve_description", tags=["website_builder", "approval"])
    async def approve_description(self, *, idea_id: int, token: str) -> dict[str, Any]:
        await patch_website_project(
            idea_id=idea_id, access_token=token,
            patch={"status": "description_approved"},
        )
        await append_website_message(
            idea_id=idea_id, access_token=token,
            message=build_message(role="user", msg_type="description_approved", content="Concept approuve."),
        )
        return {"idea_id": idea_id, "approved": True}

    # ── Phase 3 : Génération HTML ─────────────────────────────────────────────

    @traceable(name="website_builder.orchestrator.generate_website", tags=["website_builder", "generation"])
    async def generate_website(
        self, *, idea_id: int, token: str,
        description: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
        used_description = description or await generate_website_plan(
            ctx=ctx, invoke_llm=self.invoke_llm, parse_json=self.parse_json_output,
        )
        html = await build_website_html(
            ctx=ctx, description=used_description, invoke_llm=self.invoke_llm,
        )
        html, stats = _qa(html)

        await patch_website_project(
            idea_id=idea_id, access_token=token,
            patch={"status": "generated", "description_json": used_description, "current_html": html, "current_version": 1},
        )
        await append_website_message(
            idea_id=idea_id, access_token=token,
            message=build_message(role="assistant", msg_type="generation_result", content="Site HTML genere.", meta=stats),
        )
        return {
            "context": {**ctx.as_dict(), "summary_md": render_context_summary(ctx)},
            "description": used_description,
            "description_summary_md": render_description_summary(used_description),
            "html": html,
            "html_stats": stats,
        }

    # ── Phase 4 : Révision (chat + édition manuelle) ──────────────────────────

    @traceable(name="website_builder.orchestrator.revise_website", tags=["website_builder", "revision"])
    async def revise_website(
        self, *, idea_id: int, token: str,
        current_html: str, instruction: str,
    ) -> dict[str, Any]:
        ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
        html = await revise_website_html(
            ctx=ctx, current_html=current_html,
            instruction=instruction, invoke_llm=self.invoke_llm,
        )
        html, stats = _qa(html)

        await patch_website_project(
            idea_id=idea_id, access_token=token,
            patch={"status": "generated", "current_html": html},
        )
        await append_website_message(
            idea_id=idea_id, access_token=token,
            message=build_message(role="user", msg_type="revision_instruction", content=instruction.strip()),
        )
        await append_website_message(
            idea_id=idea_id, access_token=token,
            message=build_message(role="assistant", msg_type="revision_result", content="Modification appliquee.", meta=stats),
        )
        return {
            "idea_id": idea_id,
            "instruction": instruction.strip(),
            "html": html,
            "html_stats": stats,
        }

    # ── Phase 5 : Déploiement ─────────────────────────────────────────────────

    @traceable(name="website_builder.orchestrator.deploy_website", tags=["website_builder", "deployment"])
    async def deploy_website(self, *, idea_id: int, token: str, html: str) -> dict[str, Any]:
        ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
        validate_html_document(html)
        deployment = await deploy_html_to_vercel(html=html, idea_id=ctx.idea_id, brand_name=ctx.brand_name)

        summary_md = (
            "**Ton site est en ligne !**\n\n"
            f"[{deployment.full_url}]({deployment.full_url})\n\n"
            f"_Projet Vercel : `{deployment.project_name}` · "
            f"deploiement `{deployment.deployment_id}` · {deployment.elapsed_seconds:.1f}s_"
        )
        await patch_website_project(
            idea_id=idea_id, access_token=token,
            patch={
                "status": "deployed", "current_html": html,
                "last_deployment_id": deployment.deployment_id,
                "last_deployment_url": deployment.full_url,
                "last_deployment_state": deployment.state,
            },
        )
        await append_website_message(
            idea_id=idea_id, access_token=token,
            message=build_message(
                role="assistant", msg_type="deploy_result",
                content=f"Site deploye: {deployment.full_url}",
                meta=deployment.as_dict(),
            ),
        )
        return {"idea_id": idea_id, "deployment": deployment.as_dict(), "summary_md": summary_md}

    @traceable(name="website_builder.orchestrator.delete_deployment", tags=["website_builder", "deployment"])
    async def delete_deployment(self, *, idea_id: int, token: str, deployment_id: str) -> dict[str, Any]:
        dep_id = str(deployment_id or "").strip()
        if not dep_id:
            raise ValueError("deployment_id manquant.")
        await delete_vercel_deployment(deployment_id=dep_id)
        await patch_website_project(
            idea_id=idea_id, access_token=token,
            patch={"status": "generated", "last_deployment_id": None, "last_deployment_url": None, "last_deployment_state": None},
        )
        await append_website_message(
            idea_id=idea_id, access_token=token,
            message=build_message(role="assistant", msg_type="deploy_deleted", content=f"Deploiement supprime: {dep_id}"),
        )
        return {"idea_id": idea_id, "deployment_id": dep_id, "deleted": True}

    # ── Streaming (SSE) ───────────────────────────────────────────────────────

    async def stream_description(self, *, idea_id: int, token: str, emitter: StepEmitter) -> None:
        try:
            await emitter.emit_step("context", "Chargement du contexte projet et du brand kit...")
            ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
            await emitter.emit_step("context", "Contexte chargé.", status="done", meta={"brand_name": ctx.brand_name})

            await emitter.emit_step("design", "Phase 2 — Conception du concept créatif...")
            description = await run_with_progress(
                emitter, step_id="design",
                coro_factory=lambda: generate_website_plan(
                    ctx=ctx, invoke_llm=self.invoke_llm, parse_json=self.parse_json_output,
                ),
                tick_messages=DESCRIPTION_TICKS,
            )
            await emitter.emit_step("design", "Concept rédigé.", status="done",
                                    meta={"sections": len(description.get("sections") or [])})

            await emitter.emit_step("persist", "Enregistrement...")
            await patch_website_project(
                idea_id=idea_id, access_token=token,
                patch={"status": "draft", "description_json": description},
            )
            await append_website_message(
                idea_id=idea_id, access_token=token,
                message=build_message(role="assistant", msg_type="description_result", content="Description generee.",
                                      meta={"sections": len(description.get("sections") or [])}),
            )
            await emitter.emit_step("persist", "Description enregistrée.", status="done")

            await emitter.emit_result({
                "context": {**ctx.as_dict(), "summary_md": render_context_summary(ctx)},
                "description": description,
                "description_summary_md": render_description_summary(description),
            })
        except Exception as exc:  # noqa: BLE001
            logger.exception("[orchestrator] stream_description failed")
            await emitter.emit_error(str(exc))
        finally:
            await emitter.close()

    async def stream_refine_description(
        self, *, idea_id: int, token: str,
        current_description: dict[str, Any], user_feedback: str,
        emitter: StepEmitter,
    ) -> None:
        try:
            await emitter.emit_step("context", "Chargement du contexte...")
            ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
            await emitter.emit_step("context", "Contexte chargé.", status="done")

            await emitter.emit_step("refine", "Phase 2.5 — Affinage du concept selon tes retours...")
            new_description = await run_with_progress(
                emitter, step_id="refine",
                coro_factory=lambda: refine_website_description(
                    ctx=ctx, current_description=current_description,
                    user_feedback=user_feedback,
                    invoke_llm=self.invoke_llm, parse_json=self.parse_json_output,
                ),
                tick_messages=REFINEMENT_TICKS,
            )
            await emitter.emit_step("refine", "Concept mis à jour.", status="done",
                                    meta={"sections": len(new_description.get("sections") or [])})

            await emitter.emit_step("persist", "Enregistrement...")
            await patch_website_project(
                idea_id=idea_id, access_token=token,
                patch={"status": "draft", "description_json": new_description},
            )
            await append_website_message(
                idea_id=idea_id, access_token=token,
                message=build_message(role="user", msg_type="description_refine_request", content=(user_feedback or "").strip()),
            )
            await append_website_message(
                idea_id=idea_id, access_token=token,
                message=build_message(role="assistant", msg_type="description_refine_result", content="Description mise a jour.",
                                      meta={"sections": len(new_description.get("sections") or [])}),
            )
            await emitter.emit_step("persist", "Concept enregistré.", status="done")

            await emitter.emit_result({
                "context": {**ctx.as_dict(), "summary_md": render_context_summary(ctx)},
                "description": new_description,
                "description_summary_md": render_description_summary(new_description),
            })
        except Exception as exc:  # noqa: BLE001
            logger.exception("[orchestrator] stream_refine_description failed")
            await emitter.emit_error(str(exc))
        finally:
            await emitter.close()

    async def stream_generate_website(
        self, *, idea_id: int, token: str,
        description: dict[str, Any] | None,
        emitter: StepEmitter,
    ) -> None:
        try:
            await emitter.emit_step("context", "Chargement du contexte projet et du brand kit...")
            ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
            await emitter.emit_step("context", "Contexte chargé.", status="done")

            used_description = description
            if not used_description:
                await emitter.emit_step("design", "Concept manquant, génération à la volée...")
                used_description = await run_with_progress(
                    emitter, step_id="design",
                    coro_factory=lambda: generate_website_plan(
                        ctx=ctx, invoke_llm=self.invoke_llm, parse_json=self.parse_json_output,
                    ),
                    tick_messages=DESCRIPTION_TICKS,
                )
                await emitter.emit_step("design", "Concept prêt.", status="done")

            await emitter.emit_step("build", "Phase 3 — Écriture du HTML/Tailwind/JS complet...")
            html = await run_with_progress(
                emitter, step_id="build",
                coro_factory=lambda: build_website_html(
                    ctx=ctx, description=used_description, invoke_llm=self.invoke_llm,
                ),
                tick_messages=GENERATION_TICKS,
                tick_interval=3.0,
            )
            await emitter.emit_step("build", "HTML généré.", status="done")

            await emitter.emit_step("qa", "Nettoyage navigation et validation...")
            html, stats = _qa(html)
            await emitter.emit_step("qa", "Site validé.", status="done", meta=stats)

            await emitter.emit_step("persist", "Enregistrement du site...")
            await patch_website_project(
                idea_id=idea_id, access_token=token,
                patch={"status": "generated", "description_json": used_description, "current_html": html, "current_version": 1},
            )
            await append_website_message(
                idea_id=idea_id, access_token=token,
                message=build_message(role="assistant", msg_type="generation_result", content="Site HTML genere.", meta=stats),
            )
            await emitter.emit_step("persist", "Site enregistré.", status="done")

            await emitter.emit_result({
                "context": {**ctx.as_dict(), "summary_md": render_context_summary(ctx)},
                "description": used_description,
                "description_summary_md": render_description_summary(used_description),
                "html": html,
                "html_stats": stats,
            })
        except Exception as exc:  # noqa: BLE001
            logger.exception("[orchestrator] stream_generate_website failed")
            await emitter.emit_error(str(exc))
        finally:
            await emitter.close()

    async def stream_revise_website(
        self, *, idea_id: int, token: str,
        current_html: str, instruction: str,
        emitter: StepEmitter,
    ) -> None:
        try:
            await emitter.emit_step("context", "Lecture de ta consigne et du contexte projet...")
            ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
            await emitter.emit_step("context", "Contexte chargé.", status="done")

            await emitter.emit_step("patch", "Phase 4 — Application de la modification...")
            html = await run_with_progress(
                emitter, step_id="patch",
                coro_factory=lambda: revise_website_html(
                    ctx=ctx, current_html=current_html,
                    instruction=instruction, invoke_llm=self.invoke_llm,
                ),
                tick_messages=REVISION_TICKS,
            )
            await emitter.emit_step("patch", "Modification appliquée.", status="done")

            await emitter.emit_step("qa", "Nettoyage navigation et validation...")
            html, stats = _qa(html)
            await emitter.emit_step("qa", "Site validé.", status="done", meta=stats)

            await emitter.emit_step("persist", "Enregistrement du site...")
            await patch_website_project(
                idea_id=idea_id, access_token=token,
                patch={"status": "generated", "current_html": html},
            )
            await append_website_message(
                idea_id=idea_id, access_token=token,
                message=build_message(role="user", msg_type="revision_instruction", content=instruction.strip()),
            )
            await append_website_message(
                idea_id=idea_id, access_token=token,
                message=build_message(role="assistant", msg_type="revision_result", content="Modification appliquee.", meta=stats),
            )
            await emitter.emit_step("persist", "Site enregistré.", status="done")

            await emitter.emit_result({
                "idea_id": idea_id,
                "instruction": instruction.strip(),
                "html": html,
                "html_stats": stats,
            })
        except Exception as exc:  # noqa: BLE001
            logger.exception("[orchestrator] stream_revise_website failed")
            await emitter.emit_error(str(exc))
        finally:
            await emitter.close()
