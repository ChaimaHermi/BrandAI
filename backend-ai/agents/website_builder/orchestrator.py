from __future__ import annotations

import logging
from typing import Any

from langsmith import traceable
from agents.base_agent import BaseAgent, PipelineState
from tools.website_builder.architecture_tool import generate_website_architecture
from tools.website_builder.coder_tool import build_website_html
from tools.website_builder.content_tool import generate_website_content
from tools.website_builder.context_tool import WebsiteContextTool
from tools.website_builder.description_renderer import (
    render_context_summary,
    render_description_summary,
)
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
from tools.website_builder.validator_tool import (
    sanitize_navigation_html,
    validate_brand_identity,
    validate_html_output,
)
from tools.website_builder.vercel_deploy import delete_vercel_deployment, deploy_html_to_vercel
from tools.website_builder.website_project_persistence import (
    append_website_message,
    build_message,
    patch_website_project,
)
from tools.website_builder.website_renderer import validate_html_document

logger = logging.getLogger("brandai.website_builder.orchestrator")


def _section_title_from_content(section_content: Any, fallback_id: str) -> str:
    """Extrait un titre lisible depuis le contenu d'une section pour l'affichage."""
    if isinstance(section_content, dict):
        for key in ("title", "headline", "name", "tagline"):
            value = str(section_content.get(key) or "").strip()
            if value:
                return value
    return fallback_id.replace("-", " ").replace("_", " ").title()


def _merge_architecture_and_content(
    architecture: dict[str, Any],
    content: dict[str, Any],
) -> dict[str, Any]:
    """
    Fusionne les sorties Phase 2A (architecture) et 2B (contenu) en une
    description compatible avec le frontend (renderer) et le refinement.
    """
    arch_sections = architecture.get("sections") or []
    content_sections = (content.get("sections") or {}) if isinstance(content, dict) else {}

    merged_sections: list[dict[str, Any]] = []
    for arch_sec in arch_sections:
        if not isinstance(arch_sec, dict):
            continue
        sid = str(arch_sec.get("id") or "").strip()
        if not sid:
            continue
        sec_content = content_sections.get(sid) or {}
        title = _section_title_from_content(sec_content, sid)
        purpose = str(arch_sec.get("purpose") or "").strip()
        merged_sections.append({
            "id": sid,
            "type": str(arch_sec.get("type") or "").strip(),
            "title": title,
            "purpose": purpose,
            "has_cta": bool(arch_sec.get("has_cta") or False),
            "cta_target": arch_sec.get("cta_target") or None,
            "creative_touch": purpose,
        })

    hero_content = content_sections.get("hero") or {}
    hero_concept = str(
        (hero_content.get("headline") or "")
        if isinstance(hero_content, dict)
        else ""
    ).strip()

    user_summary_lines = [
        f"Voici ce que je vais te créer : un site vitrine en {len(merged_sections)} sections.",
    ]
    if hero_concept:
        user_summary_lines.append(f"Hero : « {hero_concept} ».")
    user_summary = " ".join(user_summary_lines)

    return {
        "language": architecture.get("language") or "fr",
        "visual_style": architecture.get("visual_style") or "",
        "tone_of_voice": architecture.get("tone") or "",
        "hero_concept": hero_concept,
        "user_summary": user_summary,
        "nav_links": architecture.get("nav_links") or [],
        "sections": merged_sections,
        "animations": architecture.get("animations") or [],
        "meta": (content.get("meta") or {}) if isinstance(content, dict) else {},
        "architecture": architecture,
        "content": content,
    }


class WebsiteBuilderOrchestrator(BaseAgent):
    """Application orchestrator for website builder phases."""

    def __init__(self) -> None:
        super().__init__(agent_name="website_builder", llm_model="openai/gpt-oss-120b")
        self.context_tool = WebsiteContextTool()

    async def run(self, state: PipelineState) -> Any:
        raise NotImplementedError("Use orchestrator methods directly.")

    async def invoke_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float,
        max_tokens: int,
        phase: str = "unknown",
        timeout_seconds: float = 0.0,
    ) -> str:
        old_temp, old_tokens, old_timeout = self.temperature, self.llm_max_tokens, getattr(self, '_override_timeout', None)
        self.temperature, self.llm_max_tokens = temperature, max_tokens
        if timeout_seconds > 0:
            self._override_timeout = timeout_seconds
        try:
            return await self._call_nvidia_direct(system_prompt, user_prompt)
        finally:
            self.temperature, self.llm_max_tokens = old_temp, old_tokens
            if old_timeout is None and hasattr(self, '_override_timeout'):
                delattr(self, '_override_timeout')
            elif old_timeout is not None:
                self._override_timeout = old_timeout

    def parse_json_output(self, raw: str) -> dict[str, Any]:
        return self._parse_json(raw)

    async def _generate_full_description(self, ctx) -> dict[str, Any]:
        """Pipeline Phase 2 : architecture → contenu → description fusionnée."""
        architecture = await generate_website_architecture(
            ctx=ctx,
            invoke_llm=self.invoke_llm,
            parse_json=self.parse_json_output,
        )
        content = await generate_website_content(
            ctx=ctx,
            architecture=architecture,
            invoke_llm=self.invoke_llm,
            parse_json=self.parse_json_output,
        )
        return _merge_architecture_and_content(architecture, content)

    async def _ensure_valid_html(self, *, ctx, html: str, phase: str) -> tuple[str, dict[str, int]]:
        """
        Validate generated/revised HTML and attempt one automatic correction pass
        if QA fails.
        """
        normalized_html = sanitize_navigation_html(html)
        try:
            validate_brand_identity(
                normalized_html,
                brand_name=ctx.brand_name,
                slogan=ctx.slogan,
            )
            stats = validate_html_output(normalized_html)
            return normalized_html, stats
        except RuntimeError as exc:
            auto_fix_instruction = (
                "Corrige automatiquement ce HTML pour qu'il passe la QA sans changer "
                "l'identité de marque: "
                "1) slogan du contexte présent tel quel, "
                "2) navigation interne uniquement avec ancres #id valides, "
                "2.1) interdit absolu: href=\"#\" et ancres orphelines (ex: #cgu sans section), "
                "3) images robustes (src http/https/data, alt, fallback), "
                "4) responsive complet (meta viewport, breakpoints sm/md/lg, nav mobile). "
                f"Phase: {phase}. Erreur QA détectée: {exc}"
            )
            healed_html = await revise_website_html(
                ctx=ctx,
                current_html=normalized_html,
                instruction=auto_fix_instruction,
                invoke_llm=self.invoke_llm,
            )
            healed_html = sanitize_navigation_html(healed_html)
            validate_brand_identity(
                healed_html,
                brand_name=ctx.brand_name,
                slogan=ctx.slogan,
            )
            stats = validate_html_output(healed_html)
            return healed_html, stats

    @traceable(name="website_builder.orchestrator.fetch_context", tags=["website_builder", "orchestrator", "context"])
    async def fetch_context(self, *, idea_id: int, token: str) -> dict[str, Any]:
        ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
        return {
            **ctx.as_dict(),
            "summary_md": render_context_summary(ctx),
        }

    @traceable(name="website_builder.orchestrator.generate_description", tags=["website_builder", "orchestrator", "description"])
    async def generate_description(self, *, idea_id: int, token: str) -> dict[str, Any]:
        ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
        description = await self._generate_full_description(ctx)

        await patch_website_project(
            idea_id=idea_id,
            access_token=token,
            patch={"status": "draft", "description_json": description},
        )
        await append_website_message(
            idea_id=idea_id,
            access_token=token,
            message=build_message(
                role="assistant",
                msg_type="description_result",
                content="Description du site generee.",
                meta={
                    "sections": len(description.get("sections") or []),
                    "animations": len(description.get("animations") or []),
                },
            ),
        )

        return {
            "context": {
                **ctx.as_dict(),
                "summary_md": render_context_summary(ctx),
            },
            "description": description,
            "description_summary_md": render_description_summary(description),
        }

    @traceable(name="website_builder.orchestrator.generate_website", tags=["website_builder", "orchestrator", "generation"])
    async def generate_website(
        self,
        *,
        idea_id: int,
        token: str,
        description: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
        used_description = description or await self._generate_full_description(ctx)
        html = await build_website_html(
            ctx=ctx,
            architecture=used_description.get("architecture") or used_description,
            content=used_description.get("content") or {},
            invoke_llm=self.invoke_llm,
        )
        html, stats = await self._ensure_valid_html(ctx=ctx, html=html, phase="generation")

        await patch_website_project(
            idea_id=idea_id,
            access_token=token,
            patch={
                "status": "generated",
                "description_json": used_description,
                "current_html": html,
                "current_version": 1,
            },
        )
        await append_website_message(
            idea_id=idea_id,
            access_token=token,
            message=build_message(
                role="assistant",
                msg_type="generation_result",
                content="Site HTML genere.",
                meta=stats,
            ),
        )

        return {
            "context": {
                **ctx.as_dict(),
                "summary_md": render_context_summary(ctx),
            },
            "description": used_description,
            "description_summary_md": render_description_summary(used_description),
            "html": html,
            "html_stats": stats,
        }

    @traceable(name="website_builder.orchestrator.revise_website", tags=["website_builder", "orchestrator", "revision"])
    async def revise_website(
        self,
        *,
        idea_id: int,
        token: str,
        current_html: str,
        instruction: str,
    ) -> dict[str, Any]:
        ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
        html = await revise_website_html(
            ctx=ctx,
            current_html=current_html,
            instruction=instruction,
            invoke_llm=self.invoke_llm,
        )
        html, stats = await self._ensure_valid_html(ctx=ctx, html=html, phase="revision")

        await patch_website_project(
            idea_id=idea_id,
            access_token=token,
            patch={"status": "generated", "current_html": html},
        )
        await append_website_message(
            idea_id=idea_id,
            access_token=token,
            message=build_message(
                role="user",
                msg_type="revision_instruction",
                content=instruction.strip(),
            ),
        )
        await append_website_message(
            idea_id=idea_id,
            access_token=token,
            message=build_message(
                role="assistant",
                msg_type="revision_result",
                content="Modification appliquee sur le site.",
                meta=stats,
            ),
        )
        return {
            "idea_id": idea_id,
            "instruction": instruction.strip(),
            "html": html,
            "html_stats": stats,
        }

    @traceable(name="website_builder.orchestrator.refine_description", tags=["website_builder", "orchestrator", "refinement"])
    async def refine_description(
        self,
        *,
        idea_id: int,
        token: str,
        current_description: dict[str, Any],
        user_feedback: str,
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
            idea_id=idea_id,
            access_token=token,
            patch={"status": "draft", "description_json": new_description},
        )
        await append_website_message(
            idea_id=idea_id,
            access_token=token,
            message=build_message(
                role="user",
                msg_type="description_refine_request",
                content=user_feedback.strip(),
            ),
        )
        await append_website_message(
            idea_id=idea_id,
            access_token=token,
            message=build_message(
                role="assistant",
                msg_type="description_refine_result",
                content="Description du site mise a jour selon tes retours.",
                meta={
                    "sections": len(new_description.get("sections") or []),
                    "animations": len(new_description.get("animations") or []),
                },
            ),
        )
        return {
            "context": {
                **ctx.as_dict(),
                "summary_md": render_context_summary(ctx),
            },
            "description": new_description,
            "description_summary_md": render_description_summary(new_description),
        }

    @traceable(name="website_builder.orchestrator.approve_description", tags=["website_builder", "orchestrator", "approval"])
    async def approve_description(self, *, idea_id: int, token: str) -> dict[str, Any]:
        await patch_website_project(
            idea_id=idea_id,
            access_token=token,
            patch={"status": "description_approved"},
        )
        await append_website_message(
            idea_id=idea_id,
            access_token=token,
            message=build_message(
                role="user",
                msg_type="description_approved",
                content="Concept approuve, lancer la generation.",
            ),
        )
        return {"idea_id": idea_id, "approved": True}

    @traceable(name="website_builder.orchestrator.save_html_directly", tags=["website_builder", "orchestrator", "edit"])
    async def save_html_directly(
        self,
        *,
        idea_id: int,
        token: str,
        html: str,
    ) -> dict[str, Any]:
        """Persiste un HTML edite manuellement (mode 'Modifier le site') sans
        passer par le LLM. Garde-fous QA legers : on accepte un HTML edite
        meme s'il rate certaines validations strictes (par ex. brand_identity)
        car l'utilisateur peut volontairement avoir change le slogan."""
        from tools.website_builder.website_renderer import html_stats

        validate_html_document(html)
        stats = html_stats(html)
        await patch_website_project(
            idea_id=idea_id,
            access_token=token,
            patch={"status": "generated", "current_html": html},
        )
        await append_website_message(
            idea_id=idea_id,
            access_token=token,
            message=build_message(
                role="user",
                msg_type="manual_edit",
                content="Modifications manuelles enregistrees depuis le mode edition.",
                meta=stats,
            ),
        )
        return {
            "idea_id": idea_id,
            "html": html,
            "html_stats": stats,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Streaming variants — emettent des etapes "XAI" en temps reel via
    # StepEmitter / SSE. Utilises par les routes /stream du Website Builder.
    # ─────────────────────────────────────────────────────────────────────────

    async def stream_description(
        self,
        *,
        idea_id: int,
        token: str,
        emitter: StepEmitter,
    ) -> None:
        try:
            await emitter.emit_step(
                "context",
                "Phase 1 - Chargement du contexte projet et du brand kit...",
            )
            ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
            await emitter.emit_step(
                "context",
                "Contexte projet et brand kit charges.",
                status="done",
                meta={"brand_name": ctx.brand_name, "language": ctx.language},
            )

            await emitter.emit_step(
                "design",
                "Phase 2 - Imagination du concept creatif (sections, animations, ton)...",
            )
            description = await run_with_progress(
                emitter,
                step_id="design",
                coro_factory=lambda: self._generate_full_description(ctx),
                tick_messages=DESCRIPTION_TICKS,
            )
            await emitter.emit_step(
                "design",
                "Concept creatif redige et valide.",
                status="done",
                meta={
                    "sections": len(description.get("sections") or []),
                    "animations": len(description.get("animations") or []),
                },
            )

            await emitter.emit_step("persist", "Enregistrement de la description...")
            await patch_website_project(
                idea_id=idea_id,
                access_token=token,
                patch={"status": "draft", "description_json": description},
            )
            await append_website_message(
                idea_id=idea_id,
                access_token=token,
                message=build_message(
                    role="assistant",
                    msg_type="description_result",
                    content="Description du site generee.",
                    meta={
                        "sections": len(description.get("sections") or []),
                        "animations": len(description.get("animations") or []),
                    },
                ),
            )
            await emitter.emit_step("persist", "Description enregistree.", status="done")

            await emitter.emit_result(
                {
                    "context": {
                        **ctx.as_dict(),
                        "summary_md": render_context_summary(ctx),
                    },
                    "description": description,
                    "description_summary_md": render_description_summary(description),
                }
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("[orchestrator] stream_description failed")
            await emitter.emit_error(str(exc))
        finally:
            await emitter.close()

    async def stream_refine_description(
        self,
        *,
        idea_id: int,
        token: str,
        current_description: dict[str, Any],
        user_feedback: str,
        emitter: StepEmitter,
    ) -> None:
        try:
            await emitter.emit_step(
                "context",
                "Chargement du contexte pour appliquer tes retours...",
            )
            ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
            await emitter.emit_step("context", "Contexte charge.", status="done")

            await emitter.emit_step(
                "refine",
                "Phase 2.5 - Affinage du concept selon tes retours...",
            )
            new_description = await run_with_progress(
                emitter,
                step_id="refine",
                coro_factory=lambda: refine_website_description(
                    ctx=ctx,
                    current_description=current_description,
                    user_feedback=user_feedback,
                    invoke_llm=self.invoke_llm,
                    parse_json=self.parse_json_output,
                ),
                tick_messages=REFINEMENT_TICKS,
            )
            await emitter.emit_step(
                "refine",
                "Concept mis a jour.",
                status="done",
                meta={
                    "sections": len(new_description.get("sections") or []),
                    "animations": len(new_description.get("animations") or []),
                },
            )

            await emitter.emit_step("persist", "Enregistrement du nouveau concept...")
            await patch_website_project(
                idea_id=idea_id,
                access_token=token,
                patch={"status": "draft", "description_json": new_description},
            )
            await append_website_message(
                idea_id=idea_id,
                access_token=token,
                message=build_message(
                    role="user",
                    msg_type="description_refine_request",
                    content=(user_feedback or "").strip(),
                ),
            )
            await append_website_message(
                idea_id=idea_id,
                access_token=token,
                message=build_message(
                    role="assistant",
                    msg_type="description_refine_result",
                    content="Description du site mise a jour selon tes retours.",
                    meta={
                        "sections": len(new_description.get("sections") or []),
                        "animations": len(new_description.get("animations") or []),
                    },
                ),
            )
            await emitter.emit_step("persist", "Concept enregistre.", status="done")

            await emitter.emit_result(
                {
                    "context": {
                        **ctx.as_dict(),
                        "summary_md": render_context_summary(ctx),
                    },
                    "description": new_description,
                    "description_summary_md": render_description_summary(new_description),
                }
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("[orchestrator] stream_refine_description failed")
            await emitter.emit_error(str(exc))
        finally:
            await emitter.close()

    async def stream_generate_website(
        self,
        *,
        idea_id: int,
        token: str,
        description: dict[str, Any] | None,
        emitter: StepEmitter,
    ) -> None:
        try:
            await emitter.emit_step(
                "context",
                "Chargement du contexte projet et du brand kit...",
            )
            ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
            await emitter.emit_step("context", "Contexte charge.", status="done")

            used_description = description
            if not used_description:
                await emitter.emit_step(
                    "design",
                    "Concept manquant, generation a la volee...",
                )
                used_description = await run_with_progress(
                    emitter,
                    step_id="design",
                    coro_factory=lambda: self._generate_full_description(ctx),
                    tick_messages=DESCRIPTION_TICKS,
                )
                await emitter.emit_step("design", "Concept pret.", status="done")

            await emitter.emit_step(
                "build",
                "Phase 3 - Ecriture du HTML/Tailwind/JS complet...",
            )
            html = await run_with_progress(
                emitter,
                step_id="build",
                coro_factory=lambda: build_website_html(
                    ctx=ctx,
                    architecture=used_description.get("architecture") or used_description,  # type: ignore[union-attr]
                    content=used_description.get("content") or {},  # type: ignore[union-attr]
                    invoke_llm=self.invoke_llm,
                ),
                tick_messages=GENERATION_TICKS,
                tick_interval=3.0,
            )
            await emitter.emit_step("build", "HTML genere.", status="done")

            await emitter.emit_step(
                "qa",
                "Validation qualite (brand kit, navigation, images, responsive)...",
            )
            html, stats = await self._ensure_valid_html(ctx=ctx, html=html, phase="generation")
            await emitter.emit_step(
                "qa",
                "Site valide.",
                status="done",
                meta=stats,
            )

            await emitter.emit_step("persist", "Enregistrement du site...")
            await patch_website_project(
                idea_id=idea_id,
                access_token=token,
                patch={
                    "status": "generated",
                    "description_json": used_description,
                    "current_html": html,
                    "current_version": 1,
                },
            )
            await append_website_message(
                idea_id=idea_id,
                access_token=token,
                message=build_message(
                    role="assistant",
                    msg_type="generation_result",
                    content="Site HTML genere.",
                    meta=stats,
                ),
            )
            await emitter.emit_step("persist", "Site enregistre.", status="done")

            await emitter.emit_result(
                {
                    "context": {
                        **ctx.as_dict(),
                        "summary_md": render_context_summary(ctx),
                    },
                    "description": used_description,
                    "description_summary_md": render_description_summary(used_description),
                    "html": html,
                    "html_stats": stats,
                }
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("[orchestrator] stream_generate_website failed")
            await emitter.emit_error(str(exc))
        finally:
            await emitter.close()

    async def stream_revise_website(
        self,
        *,
        idea_id: int,
        token: str,
        current_html: str,
        instruction: str,
        emitter: StepEmitter,
    ) -> None:
        try:
            await emitter.emit_step(
                "context",
                "Lecture de ta consigne et du contexte projet...",
            )
            ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
            await emitter.emit_step("context", "Contexte charge.", status="done")

            await emitter.emit_step(
                "patch",
                "Phase 4 - Application chirurgicale de la modification...",
            )
            html = await run_with_progress(
                emitter,
                step_id="patch",
                coro_factory=lambda: revise_website_html(
                    ctx=ctx,
                    current_html=current_html,
                    instruction=instruction,
                    invoke_llm=self.invoke_llm,
                ),
                tick_messages=REVISION_TICKS,
            )
            await emitter.emit_step("patch", "Modification appliquee.", status="done")

            await emitter.emit_step("qa", "Verification anti-regression...")
            html, stats = await self._ensure_valid_html(ctx=ctx, html=html, phase="revision")
            await emitter.emit_step("qa", "Aucune regression detectee.", status="done", meta=stats)

            await emitter.emit_step("persist", "Enregistrement du site...")
            await patch_website_project(
                idea_id=idea_id,
                access_token=token,
                patch={"status": "generated", "current_html": html},
            )
            await append_website_message(
                idea_id=idea_id,
                access_token=token,
                message=build_message(
                    role="user",
                    msg_type="revision_instruction",
                    content=instruction.strip(),
                ),
            )
            await append_website_message(
                idea_id=idea_id,
                access_token=token,
                message=build_message(
                    role="assistant",
                    msg_type="revision_result",
                    content="Modification appliquee sur le site.",
                    meta=stats,
                ),
            )
            await emitter.emit_step("persist", "Site enregistre.", status="done")

            await emitter.emit_result(
                {
                    "idea_id": idea_id,
                    "instruction": instruction.strip(),
                    "html": html,
                    "html_stats": stats,
                }
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("[orchestrator] stream_revise_website failed")
            await emitter.emit_error(str(exc))
        finally:
            await emitter.close()

    @traceable(name="website_builder.orchestrator.deploy_website", tags=["website_builder", "orchestrator", "deployment"])
    async def deploy_website(self, *, idea_id: int, token: str, html: str) -> dict[str, Any]:
        ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
        validate_html_document(html)
        deployment = await deploy_html_to_vercel(
            html=html,
            idea_id=ctx.idea_id,
            brand_name=ctx.brand_name,
        )

        summary_md = (
            "**Ton site est en ligne !**\n\n"
            f"[{deployment.full_url}]({deployment.full_url})\n\n"
            f"_Projet Vercel : `{deployment.project_name}` · "
            f"deploiement `{deployment.deployment_id}` · "
            f"{deployment.elapsed_seconds:.1f}s_"
        )

        await patch_website_project(
            idea_id=idea_id,
            access_token=token,
            patch={
                "status": "deployed",
                "current_html": html,
                "last_deployment_id": deployment.deployment_id,
                "last_deployment_url": deployment.full_url,
                "last_deployment_state": deployment.state,
            },
        )
        await append_website_message(
            idea_id=idea_id,
            access_token=token,
            message=build_message(
                role="assistant",
                msg_type="deploy_result",
                content=f"Site deploye: {deployment.full_url}",
                meta=deployment.as_dict(),
            ),
        )
        return {
            "idea_id": idea_id,
            "deployment": deployment.as_dict(),
            "summary_md": summary_md,
        }

    @traceable(name="website_builder.orchestrator.delete_deployment", tags=["website_builder", "orchestrator", "deployment"])
    async def delete_deployment(self, *, idea_id: int, token: str, deployment_id: str) -> dict[str, Any]:
        dep_id = str(deployment_id or "").strip()
        if not dep_id:
            raise ValueError("deployment_id manquant.")

        await delete_vercel_deployment(deployment_id=dep_id)
        await patch_website_project(
            idea_id=idea_id,
            access_token=token,
            patch={
                "status": "generated",
                "last_deployment_id": None,
                "last_deployment_url": None,
                "last_deployment_state": None,
            },
        )
        await append_website_message(
            idea_id=idea_id,
            access_token=token,
            message=build_message(
                role="assistant",
                msg_type="deploy_deleted",
                content=f"Deploiement supprime: {dep_id}",
            ),
        )
        return {"idea_id": idea_id, "deployment_id": dep_id, "deleted": True}

