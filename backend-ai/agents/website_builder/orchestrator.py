from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from typing import Any

from config.website_builder_config import GENERATION_MODEL

from langsmith import traceable
from agents.base_agent import BaseAgent, PipelineState
from tools.website_builder.infra.langsmith_traces import (
    TAGS_LLM,
    TAGS_ORCH,
    TAGS_QA,
    TAGS_STREAM,
    process_context_dict_outputs,
    process_ensure_html_inputs,
    process_ensure_html_outputs,
    process_generate_full_description_inputs,
    process_llm_inputs,
    process_llm_outputs,
    process_merge_description_outputs,
    process_route_inputs_idea_token,
    process_save_html_outputs,
    process_save_html_route_inputs,
    process_stream_description_inputs,
    process_stream_generate_inputs,
    process_stream_refine_inputs,
    process_stream_revise_inputs,
)
from tools.website_builder.concept.architecture_tool import generate_website_architecture
from tools.website_builder.generation.coder_tool import build_website_html
from tools.website_builder.concept.content_tool import generate_website_content
from tools.website_builder.context.context_tool import WebsiteContextTool
from tools.website_builder.infra.description_renderer import (
    render_context_summary,
    render_description_summary,
)
from tools.website_builder.concept.refinement_tool import refine_website_description
from tools.website_builder.revision.revision_tool import revise_website_html
from tools.website_builder.infra.step_streamer import (
    DESCRIPTION_TICKS,
    GENERATION_TICKS,
    REFINEMENT_TICKS,
    REVISION_TICKS,
    StepEmitter,
    run_with_progress,
)
from tools.website_builder.qa.validator_tool import sanitize_navigation_html
from tools.website_builder.deployment.vercel_deploy import delete_vercel_deployment, deploy_html_to_vercel
from tools.website_builder.infra.website_project_persistence import (
    append_website_message,
    build_message,
    patch_website_project,
)
from tools.website_builder.generation.website_renderer import html_stats, validate_html_document

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
        super().__init__(agent_name="website_builder", llm_model="z-ai/glm-5.1")
        self.context_tool = WebsiteContextTool()

    async def run(self, state: PipelineState) -> Any:
        raise NotImplementedError("Use orchestrator methods directly.")

    @traceable(
        name="website_builder.invoke_llm",
        run_type="llm",
        tags=TAGS_LLM,
        metadata={"component": "website_builder"},
        process_inputs=process_llm_inputs,
        process_outputs=process_llm_outputs,
    )
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
        """
        Appel LLM non-streaming.
        Pour GLM-5.1 : stream en interne (NVIDIA → SiliconFlow) et accumule les chunks.
        """
        if "glm" in self.llm_model.lower():
            chunks: list[str] = []
            async for chunk in self.stream_llm(
                system_prompt,
                user_prompt,
                model=self.llm_model,
                max_tokens=min(max_tokens, 16384),
                phase=phase,
            ):
                piece = chunk.get("content") or chunk.get("reasoning") or ""
                if piece:
                    chunks.append(piece)
            result = "".join(chunks).strip()
            if not result:
                raise RuntimeError(
                    f"GLM-5.1 n'a produit aucun contenu (phase={phase}). "
                    "Vérifiez NVIDIA_API_KEY_* et GLM-5.1_silicon dans .env."
                )
            return result

        old_temp, old_tokens, old_timeout = self.temperature, self.llm_max_tokens, getattr(self, '_override_timeout', None)
        self.temperature, self.llm_max_tokens = temperature, max_tokens
        if timeout_seconds > 0:
            self._override_timeout = timeout_seconds
        try:
            return await self._call_azure_direct(system_prompt, user_prompt)
        finally:
            self.temperature, self.llm_max_tokens = old_temp, old_tokens
            if old_timeout is None and hasattr(self, '_override_timeout'):
                delattr(self, '_override_timeout')
            elif old_timeout is not None:
                self._override_timeout = old_timeout

    # ── Constantes SiliconFlow ────────────────────────────────────────────────
    _SILICON_BASE = "https://api.siliconflow.com/v1/chat/completions"
    _SILICON_MODEL = "zai-org/GLM-4.7"   # GLM-5.1 indisponible sur SiliconFlow

    def _silicon_api_key(self) -> str | None:
        # Essaie plusieurs noms possibles dans .env
        for var in ("SILICONFLOW_API_KEY", "GLM_SILICON_API_KEY", "GLM-5.1_silicon", "GLM_5_1_silicon"):
            val = (os.getenv(var) or "").strip()
            if val:
                return val
        return None

    async def _stream_siliconflow(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        max_tokens: int = 16384,
    ) -> AsyncIterator[dict[str, str]]:
        """Streaming GLM via SiliconFlow (fallback NVIDIA)."""
        import httpx, json as _json
        key = self._silicon_api_key()
        if not key:
            raise RuntimeError("GLM-5.1_silicon absent du .env — fallback SiliconFlow impossible.")
        payload = {
            "model": self._SILICON_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "temperature": 1.0,
            "max_tokens": min(max_tokens, 16384),
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
            async with client.stream(
                "POST", self._SILICON_BASE,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "Accept": "text/event-stream"},
                json=payload,
            ) as resp:
                if resp.status_code >= 400:
                    body = (await resp.aread()).decode("utf-8", errors="ignore")
                    raise RuntimeError(f"SiliconFlow HTTP {resp.status_code}: {body[:200]}")
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        obj = _json.loads(data_str)
                        delta = obj["choices"][0].get("delta") or {}
                        content = delta.get("content") or ""
                        if content:
                            yield {"content": content}
                    except Exception:
                        continue

    async def stream_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 16384,
        phase: str = "unknown",
    ) -> AsyncIterator[dict[str, str]]:
        """
        Phase 3 — Streaming GLM-5.1.
        Ordre : SiliconFlow (primaire) → NVIDIA NIM (fallback).
        """
        used_model = (model or GENERATION_MODEL).strip()
        max_tokens = min(max_tokens, 16384)
        temperature = 1.0  # GLM exige temperature=1.0

        old_temp, old_tokens = self.temperature, self.llm_max_tokens
        self.temperature, self.llm_max_tokens = temperature, max_tokens
        try:
            # ── Tentative 1 : SiliconFlow (primaire) ──────────────────────
            if self._silicon_api_key():
                try:
                    async for chunk in self._stream_siliconflow(
                        system_prompt, user_prompt, max_tokens=max_tokens,
                    ):
                        yield chunk
                    return
                except Exception as sf_exc:
                    logger.warning(
                        "[website_builder] SiliconFlow échoué → fallback NVIDIA | err=%s",
                        str(sf_exc)[:120],
                    )

            # ── Tentative 2 : NVIDIA NIM (fallback) ───────────────────────
            api_key_override = (os.getenv("GLM_NVIDIA_API_KEY") or "").strip() or None
            extra_body: dict[str, Any] = {"top_p": 1.0}
            try:
                async for chunk in self._stream_nvidia_direct(
                    system_prompt, user_prompt,
                    model=used_model, max_tokens=max_tokens,
                    temperature=temperature, extra_body=extra_body,
                    api_key_override=api_key_override,
                ):
                    yield chunk
            except Exception as nv_exc:
                raise RuntimeError(
                    f"SiliconFlow et NVIDIA indisponibles. "
                    f"NVIDIA: {str(nv_exc)[:120]}"
                ) from nv_exc
        finally:
            self.temperature, self.llm_max_tokens = old_temp, old_tokens

    def parse_json_output(self, raw: str) -> dict[str, Any]:
        return self._parse_json(raw)

    @traceable(
        name="website_builder.merge_description",
        run_type="chain",
        tags=TAGS_ORCH,
        metadata={"phase": "2", "step": "architecture_plus_content"},
        process_inputs=process_generate_full_description_inputs,
        process_outputs=process_merge_description_outputs,
    )
    async def _generate_full_description(self, ctx) -> dict[str, Any]:
        """Phase 2 : architecture (2A) → contenu (2B) → description fusionnée."""
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

    @traceable(
        name="website_builder.ensure_valid_html",
        run_type="chain",
        tags=TAGS_QA,
        metadata={"component": "website_builder"},
        process_inputs=process_ensure_html_inputs,
        process_outputs=process_ensure_html_outputs,
    )
    async def _ensure_valid_html(self, *, ctx, html: str, phase: str) -> tuple[str, dict[str, int]]:
        """
        QA en deux passes :

        Passe 1 — Corrections automatiques sans LLM (instantané) :
          · sanitize_navigation_html : corrige href="#" → href="#hero"
          · repair_html_document     : ajoute </body></html> si tronqué

        Passe 2 — Correction LLM si problèmes détectés :
          · Détecte les problèmes restants (structure, brand name, responsive)
          · Appelle revise_website_html pour corriger en une passe
          · Si la correction LLM échoue → retourne le HTML de la passe 1 (jamais bloquant)
        """
        from tools.website_builder.generation.website_renderer import repair_html_document

        # ── Passe 1 : corrections Python instantanées ──────────────────────
        normalized_html = sanitize_navigation_html(html)
        normalized_html = repair_html_document(normalized_html)

        if not normalized_html.strip():
            raise RuntimeError(
                "Le modèle n'a produit aucun HTML. "
                "Vérifiez la clé GLM_NVIDIA_API_KEY ou NVIDIA_API_KEY_* dans .env."
            )

        # ── Détection des problèmes restants ───────────────────────────────
        issues: list[str] = []
        lower = normalized_html.lower()

        if "<html" not in lower or "</html>" not in lower:
            issues.append("structure HTML incomplète (balises <html> manquantes)")

        brand = (ctx.brand_name or "").strip()
        if brand and brand.lower() not in lower:
            issues.append(f"nom de marque '{brand}' absent du HTML")

        if "sm:" not in normalized_html and "md:" not in normalized_html:
            issues.append("aucune classe responsive Tailwind (sm:/md:) détectée")

        # ── Passe 2 : correction LLM si nécessaire ─────────────────────────
        if issues:
            fix_instruction = (
                "Corrige ces problèmes dans le HTML sans modifier le contenu visible : "
                + " | ".join(issues)
            )
            logger.info(
                "[qa] Problèmes détectés idea_id=%s → correction LLM : %s",
                ctx.idea_id, fix_instruction
            )
            try:
                fixed_html = await revise_website_html(
                    ctx=ctx,
                    current_html=normalized_html,
                    instruction=fix_instruction,
                    invoke_llm=self.invoke_llm,
                )
                fixed_html = sanitize_navigation_html(fixed_html)
                fixed_html = repair_html_document(fixed_html)
                if fixed_html.strip():
                    normalized_html = fixed_html
                    logger.info("[qa] Correction LLM appliquée idea_id=%s", ctx.idea_id)
            except Exception as exc:  # noqa: BLE001
                # Correction échouée → on garde le HTML de la passe 1, jamais bloquant.
                logger.warning(
                    "[qa] Correction LLM échouée (non bloquant) idea_id=%s err=%s",
                    ctx.idea_id, str(exc)[:150]
                )

        return normalized_html, html_stats(normalized_html)

    @traceable(
        name="website_builder.fetch_context",
        run_type="chain",
        tags=[*TAGS_ORCH, "context"],
        metadata={"route": "GET /website/context"},
        process_inputs=process_route_inputs_idea_token,
        process_outputs=process_context_dict_outputs,
    )
    async def fetch_context(self, *, idea_id: int, token: str) -> dict[str, Any]:
        ctx = await self.context_tool.fetch(idea_id=idea_id, access_token=token)
        return {
            **ctx.as_dict(),
            "summary_md": render_context_summary(ctx),
        }

    @traceable(
        name="website_builder.approve_description",
        run_type="chain",
        tags=[*TAGS_ORCH, "approval"],
        metadata={"route": "POST /website/description/approve"},
        process_inputs=process_route_inputs_idea_token,
    )
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

    @traceable(
        name="website_builder.save_html_manual",
        run_type="chain",
        tags=[*TAGS_ORCH, "edit", "manual_save"],
        metadata={"route": "POST /website/save", "llm": False},
        process_inputs=process_save_html_route_inputs,
        process_outputs=process_save_html_outputs,
    )
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
        from tools.website_builder.generation.website_renderer import html_stats

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

    @traceable(
        name="website_builder.stream.description",
        run_type="chain",
        tags=TAGS_STREAM,
        metadata={"sse_route": "/website/description/stream", "phase": "2"},
        process_inputs=process_stream_description_inputs,
    )
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

    @traceable(
        name="website_builder.stream.refine_description",
        run_type="chain",
        tags=TAGS_STREAM,
        metadata={"sse_route": "/website/description/refine/stream", "phase": "2.5"},
        process_inputs=process_stream_refine_inputs,
    )
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

    @traceable(
        name="website_builder.stream.generate_website",
        run_type="chain",
        tags=TAGS_STREAM,
        metadata={"sse_route": "/website/generate/stream", "phase": "3"},
        process_inputs=process_stream_generate_inputs,
    )
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
                f"Phase 3 - Generation du site vitrine via GLM ({GENERATION_MODEL})...",
                meta={"model": GENERATION_MODEL, "provider": "NVIDIA NIM"},
            )

            async def _on_glm_chunk(kind: str, text: str) -> None:
                if kind == "content":
                    await emitter.emit_code_chunk(
                        "build",
                        content=text,
                        model=GENERATION_MODEL,
                    )
                elif kind == "reasoning":
                    await emitter.emit_code_chunk(
                        "build",
                        reasoning=text,
                        model=GENERATION_MODEL,
                    )

            html = await run_with_progress(
                emitter,
                step_id="build",
                coro_factory=lambda: build_website_html(
                    ctx=ctx,
                    architecture=used_description.get("architecture") or used_description,  # type: ignore[union-attr]
                    content=used_description.get("content") or {},  # type: ignore[union-attr]
                    invoke_llm=self.invoke_llm,
                    stream_llm=self.stream_llm,
                    on_chunk=_on_glm_chunk,
                ),
                tick_messages=GENERATION_TICKS,
                tick_interval=3.0,
            )
            await emitter.emit_step(
                "build",
                f"HTML genere par GLM ({GENERATION_MODEL}).",
                status="done",
                meta={"model": GENERATION_MODEL},
            )

            await emitter.emit_step("qa", "Validation structure HTML...")
            html, stats = await self._ensure_valid_html(ctx=ctx, html=html, phase="generation")
            await emitter.emit_step("qa", "Structure HTML valide.", status="done", meta=stats)

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

    @traceable(
        name="website_builder.stream.revise_website",
        run_type="chain",
        tags=TAGS_STREAM,
        metadata={"sse_route": "/website/revise/stream", "phase": "4"},
        process_inputs=process_stream_revise_inputs,
    )
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

    @traceable(
        name="website_builder.deploy_website",
        run_type="chain",
        tags=[*TAGS_ORCH, "deployment"],
        metadata={"route": "POST /website/deploy"},
        process_inputs=process_save_html_route_inputs,
    )
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

    @traceable(
        name="website_builder.delete_deployment",
        run_type="chain",
        tags=[*TAGS_ORCH, "deployment"],
        metadata={"route": "POST /website/deploy/delete"},
        process_inputs=process_route_inputs_idea_token,
    )
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

