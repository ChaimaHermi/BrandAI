import asyncio
import base64
import json
import logging
import os
import re
import sys
import io
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from langsmith import traceable
from langsmith.run_helpers import get_current_run_tree

from agents.base_agent import BaseAgent, PipelineState
from config.branding_config import (
    LOGO_AGENT_RECURSION_LIMIT,
    LOGO_AGENT_VERBOSE_REACT,
    LOGO_HF_IMAGE_MODEL,
    LOGO_IMAGE_PROVIDER,
    LOGO_LLM_CONFIG,
    LOGO_ORIGINALITY_CHECK_ENABLED,
    LOGO_ORIGINALITY_MAX_RETRIES,
    LOGO_ORIGINALITY_MAX_SIMILAR,
)
from llm.llm_factory import create_azure_openai_client
from prompts.branding.logo_prompt import (
    LOGO_IMAGE_PROMPT_SYSTEM_WITH_NAME,
    LOGO_REACT_SYSTEM_PROMPT,
    build_logo_react_user_message,
    build_logo_user_message_with_name,
)
from shared.branding.validators import parse_llm_json_object
from tools.branding.logo_image_client import fetch_logo_image_hf_with_pollinations_fallback
from tools.branding.logo_originality_checker import verifier_originalite_logo_bytes
from tools.branding.logo_tools import (
    make_draft_logo_prompt_tool,
    make_render_logo_image_tool,
)

logger = logging.getLogger("brandai.logo_agent")


def _trunc_log(text: str, max_len: int = 2500) -> str:
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[:max_len] + f"... [tronqué, {len(t)} caractères au total]"


def _print_prompt_to_terminal(image_prompt: str, negative_prompt: str) -> None:
    v = (os.getenv("LOGO_PRINT_IMAGE_PROMPT") or "1").strip().lower()
    if v in ("0", "false", "no", "off"):
        return
    lines = [
        "",
        "======== [logo_agent] PROMPT IMAGE (LLM) ========",
        (image_prompt or "").strip(),
    ]
    if (negative_prompt or "").strip():
        lines.extend(["-------- negative_prompt --------", negative_prompt.strip()])
    lines.append("======== fin prompt image ========\n")
    print("\n".join(lines), file=sys.stderr, flush=True)


def _flood_fill_background(data: bytearray, width: int, height: int, threshold: int = 230) -> None:
    """
    Flood-fill depuis les 4 bords de l'image pour supprimer le fond connecté.
    Seuls les pixels clairs (min RGB >= threshold) reliés au bord deviennent
    transparents — les zones claires à l'intérieur du logo restent intactes.
    """
    from collections import deque

    visited = bytearray(width * height)  # 0 = non visité
    queue: deque[int] = deque()

    def enqueue(x: int, y: int) -> None:
        idx_px = y * width + x
        if visited[idx_px]:
            return
        idx = idx_px * 4
        if min(data[idx], data[idx + 1], data[idx + 2]) >= threshold:
            visited[idx_px] = 1
            queue.append(idx_px)

    for x in range(width):
        enqueue(x, 0)
        enqueue(x, height - 1)
    for y in range(height):
        enqueue(0, y)
        enqueue(width - 1, y)

    while queue:
        idx_px = queue.popleft()
        idx = idx_px * 4
        r, g, b = data[idx], data[idx + 1], data[idx + 2]
        # Transition douce sur 20 niveaux pour éviter les bords crénelés.
        brightness = min(r, g, b)
        feather_range = 20
        alpha = max(0, int((threshold - brightness) / feather_range * 255))
        data[idx + 3] = min(data[idx + 3], alpha)

        x, y = idx_px % width, idx_px // width
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height:
                nidx_px = ny * width + nx
                if not visited[nidx_px]:
                    nidx = nidx_px * 4
                    if min(data[nidx], data[nidx + 1], data[nidx + 2]) >= threshold:
                        visited[nidx_px] = 1
                        queue.append(nidx_px)


def _remove_light_background_to_transparent(
    image_bytes: bytes,
) -> tuple[bytes | None, str | None]:
    """
    Supprime le fond clair/blanc du logo et retourne un PNG avec canal alpha.

    Stratégie en 2 passes :
    1. rembg (segmentation IA) si disponible — meilleure qualité.
    2. Flood-fill depuis les bords (fallback PIL) — supprime le fond connecté
       aux bords sans toucher les zones claires à l'intérieur du logo
       (icône, texte clair, etc.).
    """
    try:
        from PIL import Image
    except Exception as e:
        return None, f"Pillow indisponible pour remove background: {e}"

    # 1) rembg — segmentation IA (meilleure qualité, préserve les détails fins).
    try:
        from rembg import remove as rembg_remove
        out_bytes = rembg_remove(image_bytes)
        if isinstance(out_bytes, (bytes, bytearray)) and out_bytes:
            return bytes(out_bytes), None
    except Exception:
        pass

    # 2) Fallback flood-fill depuis les bords : supprime le fond connecté
    #    aux bords de l'image (cadre/sticker/fond blanc/off-white) sans
    #    altérer les parties claires à l'intérieur du logo.
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            rgba = img.convert("RGBA")
            w, h = rgba.size
            data = bytearray(rgba.tobytes())

            _flood_fill_background(data, w, h, threshold=230)

            out = Image.frombytes("RGBA", (w, h), bytes(data))
            buf = io.BytesIO()
            out.save(buf, format="PNG")
            return buf.getvalue(), None
    except Exception as e:
        return None, f"Remove background échoué: {e}"


class LogoAgent(BaseAgent):
    """Prompt image via ReAct (draft -> render) puis kit logo (HF / NVIDIA / Pollinations)."""

    def __init__(self):
        super().__init__(
            agent_name="logo_agent",
            temperature=LOGO_LLM_CONFIG["temperature"],
            llm_model="gpt-4.1",
            llm_max_tokens=min(LOGO_LLM_CONFIG.get("max_tokens") or 900, 1200),
        )
        self._provider = LOGO_LLM_CONFIG.get("provider", "azure")
        self._logo_max_tokens = min(LOGO_LLM_CONFIG.get("max_tokens") or 900, 1200)

    @staticmethod
    def _extract_drafted_logo_prompts(messages: list, brand_name: str) -> tuple[str, str] | None:
        brand_key = (brand_name or "").strip().lower()
        for msg in reversed(messages or []):
            if not isinstance(msg, ToolMessage):
                continue
            if getattr(msg, "name", None) != "draft_logo_prompt":
                continue
            raw = msg.content
            if not isinstance(raw, str) or not raw.strip():
                continue
            try:
                data = json.loads(raw)
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            ip = str(data.get("image_prompt") or "").strip()
            if not ip:
                continue
            np = str(data.get("negative_prompt") or "").strip()
            if brand_key and brand_key not in ip.lower():
                continue
            if re.search(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b", ip):
                continue
            return ip, np
        return None

    @staticmethod
    def _parse_logo_prompt_json(raw: str, brand_name: str) -> tuple[str, str] | None:
        try:
            data = parse_llm_json_object(raw)
        except Exception:
            return None
        ip = str(data.get("image_prompt") or "").strip()
        np = str(data.get("negative_prompt") or "").strip()
        if not ip:
            return None
        if (brand_name or "").strip().lower() not in ip.lower():
            return None
        if re.search(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b", ip):
            return None
        return ip, np

    def _draft_logo_prompt_direct(
        self,
        *,
        llm,
        idea: dict,
        brand_name: str,
        palette_hint: str,
        validation_feedback: str,
    ) -> tuple[str, str] | None:
        user_prompt = build_logo_user_message_with_name(idea, brand_name, palette_hint)
        fb = (validation_feedback or "").strip()
        if fb:
            user_prompt += "\n\n--- FEEDBACK (produce a new JSON prompt) ---\n" + fb
        messages = [
            SystemMessage(content=LOGO_IMAGE_PROMPT_SYSTEM_WITH_NAME),
            HumanMessage(content=user_prompt),
        ]
        response = llm.invoke(messages)
        content = response.content if response and getattr(response, "content", None) else ""
        raw = content if isinstance(content, str) else str(content)

        result = self._parse_logo_prompt_json(raw, brand_name)
        if not result:
            self.logger.warning(
                "[logo_agent] Parse échoué | brand=%r | raw[:300]=%r",
                brand_name, raw[:300],
            )
        return result

    @staticmethod
    def _print(msg: str = "") -> None:
        print(msg, flush=True)

    @staticmethod
    def _header(title: str) -> None:
        bar = "=" * 56
        print(f"\n{bar}", flush=True)
        print(f"  {title}", flush=True)
        print(bar, flush=True)

    @staticmethod
    def _truncate(s: str, max_len: int = 480) -> str:
        s = (s or "").strip()
        if len(s) <= max_len:
            return s
        return s[: max_len - 3] + "..."

    @classmethod
    def _summarize_tool_observation(cls, tool_name: str, raw: str) -> str:
        if not raw or not isinstance(raw, str):
            return str(raw)[:400]
        if tool_name == "render_logo_image":
            try:
                data = json.loads(raw)
                if isinstance(data, dict) and data.get("ok"):
                    if data.get("skipped"):
                        return "render skipped (provider=none)"
                    return f"ok=true bytes≈{data.get('byte_count', '?')} source={data.get('source')}"
            except Exception:
                pass
        if tool_name == "draft_logo_prompt":
            return cls._truncate(raw, 520)
        return cls._truncate(raw, 520)

    @classmethod
    def _log_react_message(cls, msg, step: int) -> None:
        if isinstance(msg, HumanMessage):
            cls._print(f"\n--- [Message utilisateur] ---\n{cls._truncate(str(msg.content), 600)}")
            return
        if isinstance(msg, SystemMessage):
            cls._print(f"\n--- [System] (etape {step}) ---\n{cls._truncate(str(msg.content), 400)}")
            return
        if isinstance(msg, AIMessage):
            tcalls = getattr(msg, "tool_calls", None) or []
            text = (msg.content or "").strip() if isinstance(msg.content, str) else ""
            if text:
                cls._print(f"\n--- [Thought] (etape {step}) ---\n{cls._truncate(text, 700)}")
            if tcalls:
                cls._print(f"\n--- [Action] (etape {step}) ---")
                for tc in tcalls:
                    if isinstance(tc, dict):
                        name = tc.get("name", "?")
                        args = tc.get("args", {})
                    else:
                        name = getattr(tc, "name", "?")
                        args = getattr(tc, "args", {})
                    try:
                        arg_s = json.dumps(args, ensure_ascii=False, indent=2) if isinstance(args, dict) else str(args)
                    except Exception:
                        arg_s = str(args)
                    cls._print(f"  -> {name}({cls._truncate(arg_s, 400)})")
            if not text and not tcalls:
                cls._print(f"\n--- [AIMessage vide] (etape {step}) ---")
            return
        if isinstance(msg, ToolMessage):
            tname = getattr(msg, "name", None) or "tool"
            raw = msg.content if isinstance(msg.content, str) else str(msg.content)
            cls._print(f"\n--- [Observation] (etape {step}) tool={tname} ---")
            cls._print(cls._summarize_tool_observation(tname, raw))
            return
        cls._print(f"\n--- [{type(msg).__name__}] (etape {step}) ---\n{cls._truncate(str(getattr(msg, 'content', '')), 400)}")

    async def _invoke_react_with_optional_trace(
        self,
        agent,
        user_content: str,
        recursion_limit: int,
    ) -> dict:
        cfg = {"recursion_limit": recursion_limit}
        initial = {"messages": [HumanMessage(content=user_content)]}

        if not LOGO_AGENT_VERBOSE_REACT:
            return await agent.ainvoke(initial, config=cfg)

        self._print("\n>>> ReAct logo (stream_mode=values)\n")
        final_state: dict | None = None
        prev_len = 0
        step = 0
        async for state in agent.astream(initial, config=cfg, stream_mode="values"):
            final_state = state
            msgs = state.get("messages") or []
            for i in range(prev_len, len(msgs)):
                step += 1
                self._log_react_message(msgs[i], step)
            prev_len = len(msgs)

        if final_state is None:
            return await agent.ainvoke(initial, config=cfg)
        return final_state

    def _make_llm_for_logo(self):
        if self._provider == "azure":
            from config.settings import AZURE_OPENAI_LOGO_DEPLOYMENT

            deployment = (AZURE_OPENAI_LOGO_DEPLOYMENT or "").strip() or None
            return create_azure_openai_client(
                temperature=self.temperature,
                max_tokens=self._logo_max_tokens,
                azure_deployment=deployment,
            )
        return self.llm_rotator.get_client(self.temperature)

    @traceable(name="logo_agent.react_invoke", tags=["branding", "logo_agent", "react"])
    async def _run_react_logo_agent(
        self,
        llm,
        idea: dict,
        brand_name: str,
        slogan_hint: str,
        palette_hint: str,
        holder: dict[str, Any],
        *,
        recursion_limit: int = LOGO_AGENT_RECURSION_LIMIT,
    ) -> list | None:
        rt = get_current_run_tree()
        if rt:
            rt.metadata.update({
                "recursion_limit": recursion_limit,
                "agent": "langgraph_react_logo",
            })

        draft_tool = make_draft_logo_prompt_tool(
            llm,
            idea,
            brand_name,
            slogan_hint,
            palette_hint,
        )
        render_tool = make_render_logo_image_tool(holder)
        tools = [draft_tool, render_tool]

        agent = create_react_agent(
            llm,
            tools,
            prompt=LOGO_REACT_SYSTEM_PROMPT,
            name="logo_react",
        )

        user_content = build_logo_react_user_message(brand_name)

        self._header("LangGraph ReAct — logo")
        self.logger.info(
            "[logo_agent] ReAct | recursion_limit=%s verbose=%s",
            recursion_limit,
            LOGO_AGENT_VERBOSE_REACT,
        )

        result = await self._invoke_react_with_optional_trace(
            agent,
            user_content,
            recursion_limit,
        )
        return result.get("messages") or []

    @staticmethod
    async def _maybe_fetch_image(
        image_prompt: str,
        negative_prompt: str,
    ) -> tuple[bytes | None, str | None, str | None]:
        provider = (LOGO_IMAGE_PROVIDER or "huggingface").strip().lower()
        if provider == "none":
            return None, None, None
        # Chaîne : HF Qwen → NVIDIA flux.2-klein-4b (pas de Pollinations)
        data, mime, src = await fetch_logo_image_hf_with_pollinations_fallback(
            image_prompt,
            negative_prompt,
            model=LOGO_HF_IMAGE_MODEL,
            pollinations_fallback=False,
        )
        return data, mime, src

    @staticmethod
    def _build_concept_dict(
        image_prompt: str,
        negative_prompt: str,
        *,
        b64: str | None,
        mime: str | None,
        transparent_b64: str | None,
        image_source: str | None,
    ) -> dict[str, Any]:
        concept: dict[str, Any] = {
            "title": "Generated mark",
            "image_prompt": image_prompt,
            "negative_prompt": negative_prompt,
            "image_provider": "huggingface",
            "image_model": LOGO_HF_IMAGE_MODEL,
        }
        if b64 and mime:
            concept["image_base64"] = b64
            concept["image_mime"] = mime
            if transparent_b64:
                concept["image_base64_transparent"] = transparent_b64
                concept["image_mime_transparent"] = "image/png"
            if image_source == "nvidia":
                concept["image_provider"] = "nvidia"
                m = (os.getenv("LOGO_NVIDIA_IMAGE_MODEL") or os.getenv("NVIDIA_IMAGE_MODEL") or "flux.2-klein-4b").strip()
                concept["image_model"] = m
                concept["image_attribution"] = f"Image générée avec NVIDIA NIM — modèle {m}."
            elif image_source == "huggingface":
                m = LOGO_HF_IMAGE_MODEL
                concept["image_attribution"] = f"Image générée avec Hugging Face Inference — modèle {m}."
        return concept

    async def _generate_logo_concept(
        self,
        *,
        llm,
        idea: dict,
        brand_name: str,
        palette_hint: str,
        originality_feedback: str = "",
        emitter: Any = None,
    ) -> dict[str, Any] | None:
        """Génère un concept logo (avec nom de marque) via appel LLM direct."""
        if emitter:
            await emitter.emit_step("prompt", "Génération du prompt image (LLM)…", status="running")
        pair = self._draft_logo_prompt_direct(
            llm=llm,
            idea=idea,
            brand_name=brand_name,
            palette_hint=palette_hint,
            validation_feedback=originality_feedback,
        )
        if not pair:
            logger.warning("[logo_agent] Prompt logo : extraction échouée")
            if emitter:
                await emitter.emit_step("prompt", "Prompt image non généré", status="error")
            return None

        image_prompt, negative_prompt = pair
        _print_prompt_to_terminal(image_prompt, negative_prompt)
        if emitter:
            await emitter.emit_step("prompt", "Prompt image prêt", status="done",
                                    meta={"preview": image_prompt[:120]})

        if emitter:
            await emitter.emit_step("image", "Génération de l'image logo (NVIDIA)…", status="running")
        image_bytes: bytes | None = None
        mime: str | None = None
        image_source: str | None = None
        image_fetch_error: str | None = None
        try:
            data, m, src = await self._maybe_fetch_image(image_prompt, negative_prompt)
            if data:
                image_bytes, mime, image_source = data, m, src
        except Exception as exc:
            image_fetch_error = str(exc)
            logger.error("[logo_agent] image fetch failed: %s", exc)

        if emitter:
            if image_bytes:
                await emitter.emit_step("image", "Image générée", status="done")
            else:
                await emitter.emit_step(
                    "image",
                    f"Image non disponible : {(image_fetch_error or '')[:80]}",
                    status="error",
                )

        b64: str | None = None
        transparent_b64: str | None = None
        if image_bytes:
            b64 = base64.standard_b64encode(image_bytes).decode("ascii")
            transparent_bytes, _ = _remove_light_background_to_transparent(image_bytes)
            if transparent_bytes:
                transparent_b64 = base64.standard_b64encode(transparent_bytes).decode("ascii")

        concept = self._build_concept_dict(
            image_prompt, negative_prompt,
            b64=b64, mime=mime,
            transparent_b64=transparent_b64,
            image_source=image_source,
        )
        concept["title"] = "Generated mark"
        # Attacher l'erreur image au concept pour que run() puisse l'exposer
        if image_fetch_error and not b64:
            concept["_image_fetch_error"] = image_fetch_error
        logger.info("[logo_agent] Concept généré image=%s", "ok" if b64 else f"absent ({image_fetch_error or 'raison inconnue'})")
        return concept

    @traceable(name="logo_agent.run", tags=["branding", "logo_agent"])
    async def run(self, state: PipelineState, emitter: Any = None) -> PipelineState:
        self._log_start(state)

        if not hasattr(state, "brand_identity") or state.brand_identity is None:
            state.brand_identity = {}

        brand_name = str(getattr(state, "brand_name_chosen", "") or "").strip()
        if not brand_name:
            msg = "brand_name_chosen est requis pour générer un logo"
            state.brand_identity["logo_error"] = msg
            state.brand_identity["branding_status"] = "logo_failed"
            state.status = "logo_failed"
            state.errors.append(f"logo_agent: {msg}")
            self._log_error(msg)
            return state

        idea = state.clarified_idea or {}
        palette_hint = str(getattr(state, "logo_palette_hint", "") or "").strip()

        # Feedback de régénération : prompt précédent à éviter + remarques utilisateur
        previous_prompt = str(getattr(state, "logo_previous_prompt", "") or "").strip()
        user_remarks = str(getattr(state, "logo_user_remarks", "") or "").strip()
        regen_feedback = ""
        if previous_prompt:
            regen_feedback = (
                "REGENERATION REQUEST — the user did not like the previous logo.\n"
                f"Previous image_prompt to AVOID completely:\n\"\"\"{previous_prompt}\"\"\"\n"
                "You MUST produce a design that is clearly different: "
                "choose a different icon concept, different typography style, and different composition. "
                "Do NOT reuse any element from the previous prompt."
            )
            if user_remarks:
                regen_feedback += f"\n\nUser remarks: {user_remarks}"
        elif user_remarks:
            regen_feedback = f"User remarks for this generation: {user_remarks}"

        def _is_tpd_error(err: Exception) -> bool:
            s = str(err).lower()
            return "tokens per day" in s or "tpd" in s

        def _is_quota_error(err: Exception) -> bool:
            s = str(err).lower()
            return any(k in s for k in [
                "429", "413", "rate_limit", "rate_limit_exceeded",
                "tokens per minute", "tokens per day",
                "request too large", "tpm", "tpd",
            ])

        try:
            llm = self._make_llm_for_logo()
            rt = get_current_run_tree()
            if rt:
                rt.metadata.update({"provider": self._provider, "brand": brand_name})

            concept = await self._generate_logo_concept(
                llm=llm,
                idea=idea,
                brand_name=brand_name,
                palette_hint=palette_hint,
                originality_feedback=regen_feedback,
                emitter=emitter,
            )
        except Exception as e:
            self._log_error(e)
            state.brand_identity["logo_error"] = str(e)
            state.brand_identity["branding_status"] = "logo_failed"
            state.status = "logo_failed"
            state.errors.append(f"logo_agent: {e}")
            return state

        if not concept:
            msg = "Aucun concept logo généré (prompt image introuvable)."
            self._log_error(msg)
            state.brand_identity["logo_error"] = msg
            state.brand_identity["branding_status"] = "logo_failed"
            state.status = "logo_failed"
            return state

        # ── Vérification d'originalité + boucle retry ───────────────────────
        if LOGO_ORIGINALITY_CHECK_ENABLED and concept.get("image_base64"):
            logger.info("[logo_agent] Vérification originalité activée (max_retries=%d)", LOGO_ORIGINALITY_MAX_RETRIES)
            if emitter:
                await emitter.emit_step("originality", "Vérification d'originalité…", status="running")
            for attempt in range(LOGO_ORIGINALITY_MAX_RETRIES):
                raw_bytes = base64.b64decode(concept["image_base64"])
                is_original, similar_urls = await verifier_originalite_logo_bytes(
                    raw_bytes, max_similar=LOGO_ORIGINALITY_MAX_SIMILAR
                )
                if is_original:
                    logger.info("[logo_agent] Logo original ✓ (tentative %d)", attempt + 1)
                    if emitter:
                        await emitter.emit_step("originality", "Logo original ✓", status="done")
                    break

                logger.warning(
                    "[logo_agent] Logo non original (tentative %d/%d) — similaires: %s",
                    attempt + 1, LOGO_ORIGINALITY_MAX_RETRIES, similar_urls[:2],
                )
                if emitter:
                    await emitter.emit_step(
                        "originality",
                        f"Non original, régénération ({attempt + 1}/{LOGO_ORIGINALITY_MAX_RETRIES})…",
                        status="running",
                    )
                refs = "; ".join(similar_urls[:3]) if similar_urls else "images existantes en ligne"
                feedback = (
                    "ORIGINALITY ISSUE — the previous logo is visually too similar to existing logos "
                    f"found online ({refs}). "
                    "You MUST generate a completely different and unique logo: "
                    "change the icon concept entirely, use a different geometric metaphor, "
                    "alter the typography style, and rethink the overall composition. "
                    "The new logo must be distinct and unrecognisable compared to the previous one."
                )
                try:
                    new_concept = await self._generate_logo_concept(
                        llm=llm,
                        idea=idea,
                        brand_name=brand_name,
                        palette_hint=palette_hint,
                        originality_feedback=feedback,
                        emitter=emitter,
                    )
                    if new_concept:
                        concept = new_concept
                except Exception as exc:
                    logger.warning("[logo_agent] Erreur régénération originalité: %s", exc)
                    break
            else:
                if emitter:
                    await emitter.emit_step("originality", "Originalité non vérifiée (max retries)", status="done")
                logger.info("[logo_agent] Max retries originalité atteint — on garde le dernier concept")

        # ── Forcer la version transparente comme version principale ──────────
        if emitter:
            await emitter.emit_step("background", "Suppression du fond…", status="running")
        if concept.get("image_base64_transparent"):
            concept["image_base64"] = concept["image_base64_transparent"]
            concept["image_mime"] = concept.get("image_mime_transparent", "image/png")
            logger.info("[logo_agent] Version transparente utilisée comme image principale")
        elif concept.get("image_base64"):
            # Tentative supplémentaire de suppression du fond si la première a échoué
            try:
                raw = base64.b64decode(concept["image_base64"])
                transparent_bytes, err = _remove_light_background_to_transparent(raw)
                if transparent_bytes:
                    t_b64 = base64.standard_b64encode(transparent_bytes).decode("ascii")
                    concept["image_base64_transparent"] = t_b64
                    concept["image_mime_transparent"] = "image/png"
                    concept["image_base64"] = t_b64
                    concept["image_mime"] = "image/png"
                    logger.info("[logo_agent] Suppression fond (retry) réussie")
                elif err:
                    logger.warning("[logo_agent] Suppression fond échouée: %s", err)
            except Exception as exc:
                logger.warning("[logo_agent] Erreur suppression fond retry: %s", exc)

        if emitter:
            await emitter.emit_step("background", "Fond supprimé", status="done")

        # Extraire l'erreur image éventuelle et la nettoyer du concept
        image_fetch_error = concept.pop("_image_fetch_error", None)

        # ── Upload Cloudinary au moment de la génération ─────────────────────
        # Stocke image_url dans le concept pour éviter tout re-upload lors des
        # consultations futures (website builder, publications schedulées).
        has_image = bool(concept.get("image_base64"))
        if has_image:
            if emitter:
                await emitter.emit_step("upload", "Sauvegarde vers Cloudinary…", status="running")
            try:
                from tools.content_generation.cloudinary_upload import (
                    cloudinary_configured,
                    upload_image_bytes,
                )
                if cloudinary_configured():
                    raw = base64.b64decode(concept["image_base64"])
                    mime = concept.get("image_mime") or "image/png"
                    image_url = await asyncio.to_thread(
                        upload_image_bytes, raw, mime=mime, folder="brandai/logos"
                    )
                    concept["image_url"] = image_url
                    logger.info("[logo_agent] Logo uploadé Cloudinary → %s", image_url[:80])
                    if emitter:
                        await emitter.emit_step("upload", "Logo sauvegardé", status="done")
                else:
                    if emitter:
                        await emitter.emit_step("upload", "Cloudinary non configuré", status="done")
            except Exception as exc:
                logger.warning("[logo_agent] Upload Cloudinary échoué (non bloquant) : %s", exc)
                if emitter:
                    await emitter.emit_step("upload", "Upload ignoré (non bloquant)", status="done")

        state.brand_identity["logo_concepts"] = [concept]
        state.brand_identity.pop("logo_error", None)

        if has_image:
            state.brand_identity["branding_status"] = "logo_generated"
            state.status = "logo_generated"
            logger.info("[logo_agent] logo généré avec image pour brand=%r", brand_name)
        else:
            img_err = image_fetch_error or "Aucun octet image reçu (HF, NVIDIA et Pollinations ont tous échoué)."
            state.brand_identity["logo_image_error"] = img_err
            state.brand_identity["branding_status"] = "logo_generated"
            state.status = "logo_generated"
            logger.warning("[logo_agent] logo sans image pour brand=%r : %s", brand_name, img_err)

        return state
