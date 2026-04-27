import asyncio
import base64
import json
import logging
import os
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
    LOGO_POLLINATIONS_IMAGE_MODEL,
)
from llm.llm_factory import create_azure_openai_client
from prompts.branding.logo_prompt import LOGO_REACT_SYSTEM_PROMPT, build_logo_react_user_message
from tools.branding.logo_image_client import fetch_logo_image_hf_with_pollinations_fallback
from tools.branding.logo_tools import (
    make_draft_logo_prompt_tool,
    make_render_logo_image_tool,
    make_validate_logo_prompt_tool,
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


def _remove_light_background_to_transparent(
    image_bytes: bytes,
) -> tuple[bytes | None, str | None]:
    """
    Convert near-white background to transparency.
    Returns PNG bytes with alpha channel when successful.
    """
    try:
        from PIL import Image
    except Exception as e:
        return None, f"Pillow indisponible pour remove background: {e}"

    # 1) Best effort with rembg (robust segmentation), if available.
    try:
        from rembg import remove as rembg_remove

        out_bytes = rembg_remove(image_bytes)
        if isinstance(out_bytes, (bytes, bytearray)) and out_bytes:
            return bytes(out_bytes), None
    except Exception:
        # fallback below
        pass

    # 2) Fallback: near-white threshold transparency.
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            rgba = img.convert("RGBA")
            data = bytearray(rgba.tobytes())

            # Since logo prompt enforces white/light background, make near-white pixels transparent.
            # Keep non-white pixels opaque to preserve logo details.
            threshold = 245
            feather = 25
            for i in range(0, len(data), 4):
                r, g, b = data[i], data[i + 1], data[i + 2]
                min_rgb = min(r, g, b)

                if min_rgb >= threshold:
                    alpha = 0
                else:
                    # Soft transition near threshold to avoid jagged edges.
                    distance = threshold - min_rgb
                    alpha = min(255, int((distance / feather) * 255)) if distance < feather else 255

                data[i + 3] = alpha

            out = Image.frombytes("RGBA", rgba.size, bytes(data))
            buf = io.BytesIO()
            out.save(buf, format="PNG")
            return buf.getvalue(), None
    except Exception as e:
        return None, f"Remove background échoué (rembg indisponible + fallback Pillow): {e}"


class LogoAgent(BaseAgent):
    """Prompt image via ReAct (draft → validate → render) puis kit logo (HF / Pollinations)."""

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
    def _extract_validated_logo_prompts(messages: list) -> tuple[str, str] | None:
        for msg in reversed(messages or []):
            if not isinstance(msg, ToolMessage):
                continue
            if getattr(msg, "name", None) != "validate_logo_prompt":
                continue
            raw = msg.content
            if not isinstance(raw, str) or not raw.strip():
                continue
            try:
                data = json.loads(raw)
            except Exception:
                continue
            if not isinstance(data, dict) or not data.get("ok"):
                continue
            ip = str(data.get("image_prompt") or "").strip()
            if not ip:
                continue
            np = str(data.get("negative_prompt") or "").strip()
            return ip, np
        return None

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
        if tool_name == "validate_logo_prompt":
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    if data.get("ok"):
                        return "ok=true (image_prompt présent)"
                    return f"ok=false: {cls._truncate(str(data.get('error') or raw), 400)}"
            except Exception:
                pass
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
        validate_tool = make_validate_logo_prompt_tool(brand_name=brand_name)
        render_tool = make_render_logo_image_tool(holder)
        tools = [draft_tool, validate_tool, render_tool]

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
        from config.branding_config import LOGO_POLLINATIONS_FALLBACK

        provider = (LOGO_IMAGE_PROVIDER or "huggingface").strip().lower()
        if provider == "none":
            return None, None, None
        data, mime, src = await fetch_logo_image_hf_with_pollinations_fallback(
            image_prompt,
            negative_prompt,
            model=LOGO_HF_IMAGE_MODEL,
            pollinations_fallback=LOGO_POLLINATIONS_FALLBACK,
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
            if image_source == "pollinations":
                concept["image_provider"] = "pollinations"
                concept["image_model"] = LOGO_POLLINATIONS_IMAGE_MODEL
                pm = LOGO_POLLINATIONS_IMAGE_MODEL
                qwen_lbl = f"Qwen Image ({pm})" if "qwen" in pm.lower() else pm
                concept["image_attribution"] = (
                    f"Image générée avec Pollinations.AI — modèle {qwen_lbl} — "
                    "service tiers (fallback lorsque Hugging Face n’est pas disponible)."
                )
            elif image_source == "azure":
                concept["image_provider"] = "azure"
                concept["image_model"] = str(os.getenv("AZURE_OPENAI_LOGO_IMAGE_DEPLOYMENT") or "").strip() or "azure-image"
                concept["image_attribution"] = (
                    "Image générée via Azure OpenAI (fallback après Hugging Face)."
                )
            elif image_source == "huggingface":
                m = LOGO_HF_IMAGE_MODEL
                if "qwen" in m.lower():
                    concept["image_attribution"] = (
                        f"Image générée avec le modèle Qwen Image ({m}) via Hugging Face Inference."
                    )
                else:
                    concept["image_attribution"] = (
                        f"Image générée avec le modèle {m} via Hugging Face Inference."
                    )
        return concept

    @traceable(name="logo_agent.run", tags=["branding", "logo_agent"])
    async def run(self, state: PipelineState) -> PipelineState:
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
        slogan_hint = str(getattr(state, "palette_slogan_hint", "") or "").strip()
        palette_hint = str(getattr(state, "logo_palette_hint", "") or "").strip()

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

        holder: dict[str, Any] = {}
        messages: list | None = None
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                llm = self._make_llm_for_logo()

                rt = get_current_run_tree()
                if rt:
                    rt.metadata.update({
                        "provider": self._provider,
                        "brand": brand_name,
                    })

                self.logger.info(
                    "[logo_agent] ReAct attempt %s/%s (marque=%r)",
                    attempt + 1,
                    self.max_retries,
                    brand_name,
                )

                messages = await self._run_react_logo_agent(
                    llm,
                    idea,
                    brand_name,
                    slogan_hint,
                    palette_hint,
                    holder,
                    recursion_limit=LOGO_AGENT_RECURSION_LIMIT,
                )
                pair = self._extract_validated_logo_prompts(messages or [])
                if pair:
                    break
                last_error = RuntimeError(
                    "Validation du prompt logo non confirmée (validate_logo_prompt ok: true introuvable)."
                )
            except Exception as e:
                last_error = e
                if self._provider == "groq":
                    if _is_tpd_error(e):
                        self.logger.error("[logo_agent] TPD quota | %s", str(e)[:200])
                        msg = (
                            "Quota journalier Groq (TPD) épuisé. "
                            "Réessaie dans quelques heures ou change de modèle."
                        )
                        state.errors.append(f"logo_agent: {msg}")
                        state.brand_identity["logo_error"] = msg
                        state.brand_identity["branding_status"] = "logo_failed"
                        state.status = "logo_failed"
                        return state
                    if _is_quota_error(e):
                        rotated = self.llm_rotator.rotate()
                        self.logger.warning(
                            "[logo_agent] quota | rotated=%s | %s",
                            rotated,
                            str(e)[:180],
                        )
                        if rotated:
                            continue
                self._log_error(e)
                msg = f"logo ReAct: {e}"
                state.errors.append(f"logo_agent: {msg}")
                state.brand_identity["logo_error"] = msg
                state.brand_identity["branding_status"] = "logo_failed"
                state.status = "logo_failed"
                return state

        if not messages:
            err_detail = str(last_error) if last_error else "aucun message ReAct"
            msg = f"Échec génération prompt logo : {err_detail}"
            self._log_error(msg)
            state.brand_identity["logo_error"] = msg
            state.brand_identity["branding_status"] = "logo_failed"
            state.status = "logo_failed"
            return state

        pair = self._extract_validated_logo_prompts(messages)
        if not pair:
            msg = "Impossible d'extraire un prompt image validé (validate_logo_prompt)."
            self._log_error(msg)
            state.brand_identity["logo_error"] = msg
            state.brand_identity["branding_status"] = "logo_failed"
            state.status = "logo_failed"
            return state

        image_prompt, negative_prompt = pair
        logger.info(
            "[logo_agent] Prompt image validé — image_prompt:\n%s",
            _trunc_log(image_prompt),
        )
        if negative_prompt:
            logger.info(
                "[logo_agent] negative_prompt:\n%s",
                _trunc_log(negative_prompt, max_len=1200),
            )
        _print_prompt_to_terminal(image_prompt, negative_prompt)

        provider = (LOGO_IMAGE_PROVIDER or "huggingface").strip().lower()
        if (
            provider != "none"
            and not holder.get("skipped")
            and holder.get("image_bytes") is None
        ):
            try:
                logger.info("[logo_agent] Fallback image — render non présent ou incomplet")
                data, mime, src = await self._maybe_fetch_image(image_prompt, negative_prompt)
                if data:
                    holder["image_bytes"] = data
                    holder["mime"] = mime
                    holder["image_source"] = src
            except Exception as e:
                logger.error("logo image fetch (fallback): %s", e)
                state.brand_identity["logo_image_error"] = str(e)

        if holder.get("render_error") and not state.brand_identity.get("logo_image_error"):
            state.brand_identity["logo_image_error"] = str(holder["render_error"])

        image_bytes: bytes | None = holder.get("image_bytes")
        mime = holder.get("mime")
        image_source = holder.get("image_source")

        b64: str | None = None
        transparent_b64: str | None = None
        if image_bytes:
            b64 = base64.standard_b64encode(image_bytes).decode("ascii")
            logger.info(
                "[logo_agent] Image générée — source=%s, %s, %d octets",
                image_source or "?",
                mime or "image",
                len(image_bytes),
            )
            transparent_bytes, transparent_err = _remove_light_background_to_transparent(image_bytes)
            if transparent_bytes:
                transparent_b64 = base64.standard_b64encode(transparent_bytes).decode("ascii")
            elif transparent_err:
                logger.warning("[logo_agent] remove background non disponible: %s", transparent_err)
        elif not state.brand_identity.get("logo_image_error"):
            if provider == "none":
                pass
            elif holder.get("skipped"):
                pass
            else:
                logger.warning(
                    "[logo_agent] Aucun octet image — voir logo_image_error si défini",
                )

        concept = self._build_concept_dict(
            image_prompt,
            negative_prompt,
            b64=b64,
            mime=mime,
            transparent_b64=transparent_b64,
            image_source=image_source,
        )

        state.brand_identity["logo_concepts"] = [concept]
        state.brand_identity["branding_status"] = "logo_generated"
        state.brand_identity.pop("logo_error", None)
        state.status = "logo_generated"
        return state
