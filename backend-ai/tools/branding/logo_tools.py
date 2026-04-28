"""
Outils LangChain pour LogoAgent (ReAct) : brouillon prompt LLM, validation, rendu image.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

from config.branding_config import (
    LOGO_HF_IMAGE_MODEL,
    LOGO_IMAGE_PROVIDER,
    LOGO_POLLINATIONS_FALLBACK,
)
from prompts.branding.logo_prompt import LOGO_IMAGE_PROMPT_SYSTEM, build_logo_user_message
from shared.branding.validators import parse_llm_json_object
from tools.branding.logo_image_client import fetch_logo_image_hf_with_pollinations_fallback

LOGO_IMAGE_PROMPT_MIN_LEN = 32
LOGO_IMAGE_PROMPT_MAX_LEN = 520
LOGO_NEGATIVE_PROMPT_MAX_LEN = 220


def normalize_logo_prompt_dict(data: dict[str, Any]) -> tuple[str, str]:
    ip = str(data.get("image_prompt") or "").strip()
    np = str(data.get("negative_prompt") or "").strip()
    return ip, np


def make_draft_logo_prompt_tool(
    llm,
    clarified_idea: dict[str, Any],
    brand_name: str,
    slogan_hint: str,
    palette_hint: str,
):
    @traceable(name="tool.draft_logo_prompt", tags=["branding", "tool", "logo_draft"])
    def _draft(validation_feedback: str) -> str:
        user_prompt = build_logo_user_message(
            clarified_idea,
            brand_name,
            slogan_hint,
            palette_hint,
        )
        fb = (validation_feedback or "").strip()
        if fb:
            user_prompt += (
                "\n\n--- VALIDATOR FEEDBACK (fix and return a single valid JSON object) ---\n"
                + fb
            )
        messages = [
            SystemMessage(content=LOGO_IMAGE_PROMPT_SYSTEM),
            HumanMessage(content=user_prompt),
        ]
        response = llm.invoke(messages)
        content = response.content if response and getattr(response, "content", None) else ""
        return content if isinstance(content, str) else str(content)

    @tool
    def draft_logo_prompt(validation_feedback: str = "") -> str:
        """
        Produces a JSON object with keys image_prompt and negative_prompt (English) for text-to-image.
        First call: empty validation_feedback. If validate_logo_prompt fails, call again with the error text.
        """
        return _draft(validation_feedback)

    return draft_logo_prompt


def make_validate_logo_prompt_tool(*, brand_name: str):

    brand_key = (brand_name or "").strip().lower()

    @traceable(name="tool.validate_logo_prompt", tags=["branding", "tool", "logo_validate"])
    def _validate(prompts_json: str) -> str:
        try:
            data = parse_llm_json_object(prompts_json)
        except Exception as e:
            return json.dumps(
                {
                    "ok": False,
                    "error": f"Invalid JSON: {e}",
                    "validation_hints": "Return a single JSON object with image_prompt and negative_prompt.",
                },
                ensure_ascii=False,
                indent=2,
            )

        if not isinstance(data, dict):
            return json.dumps(
                {
                    "ok": False,
                    "error": "Root JSON must be an object.",
                    "validation_hints": "Use keys image_prompt and negative_prompt.",
                },
                ensure_ascii=False,
                indent=2,
            )

        image_prompt, negative_prompt = normalize_logo_prompt_dict(data)
        if not image_prompt:
            return json.dumps(
                {
                    "ok": False,
                    "error": "image_prompt is empty or missing.",
                    "validation_hints": "Provide a non-empty English image_prompt.",
                },
                ensure_ascii=False,
                indent=2,
            )

        if len(image_prompt) < LOGO_IMAGE_PROMPT_MIN_LEN:
            return json.dumps(
                {
                    "ok": False,
                    "error": f"image_prompt too short (min {LOGO_IMAGE_PROMPT_MIN_LEN} characters).",
                    "validation_hints": "Add concrete layout, style, and brand name usage.",
                },
                ensure_ascii=False,
                indent=2,
            )

        if len(image_prompt) > LOGO_IMAGE_PROMPT_MAX_LEN:
            return json.dumps(
                {
                    "ok": False,
                    "error": f"image_prompt too long (max {LOGO_IMAGE_PROMPT_MAX_LEN} characters).",
                    "validation_hints": "Shorten while keeping brand and style constraints.",
                },
                ensure_ascii=False,
                indent=2,
            )

        if len(negative_prompt) > LOGO_NEGATIVE_PROMPT_MAX_LEN:
            return json.dumps(
                {
                    "ok": False,
                    "error": f"negative_prompt too long (max {LOGO_NEGATIVE_PROMPT_MAX_LEN} characters).",
                    "validation_hints": "Keep negative prompt concise.",
                },
                ensure_ascii=False,
                indent=2,
            )

        if brand_key and brand_key not in image_prompt.lower():
            return json.dumps(
                {
                    "ok": False,
                    "error": f"The brand name « {brand_name} » must appear in image_prompt (readable text in the logo).",
                    "validation_hints": "Include the exact brand name in the prompt as visible typography.",
                },
                ensure_ascii=False,
                indent=2,
            )

        # Prevent prompts that instruct rendering palette color codes in the logo text.
        if re.search(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b", image_prompt):
            return json.dumps(
                {
                    "ok": False,
                    "error": "image_prompt must not contain hexadecimal color codes.",
                    "validation_hints": "Keep palette for visual style only; never display #RRGGBB as text in the logo.",
                },
                ensure_ascii=False,
                indent=2,
            )

        if re.search(r"\b(hex(?:adecimal)?|rgb|rgba|cmyk|color\s*code|palette\s*code)\b", image_prompt, re.IGNORECASE):
            return json.dumps(
                {
                    "ok": False,
                    "error": "image_prompt must not request visible color codes in the logo text.",
                    "validation_hints": "Use colors visually, but allow only the brand name as text.",
                },
                ensure_ascii=False,
                indent=2,
            )

        # Prevent prompts that request plate/badge/container backgrounds behind logo.
        if re.search(
            r"\b(badge|label|plate|sticker|rounded\s*rectangle|capsule|pill|card\s*background|panel\s*behind|container\s*behind)\b",
            image_prompt,
            re.IGNORECASE,
        ):
            return json.dumps(
                {
                    "ok": False,
                    "error": "image_prompt must not request a badge/container background behind the logo.",
                    "validation_hints": "Keep icon + brand name only on transparent/empty background, without plate/card/capsule.",
                },
                ensure_ascii=False,
                indent=2,
            )

        return json.dumps(
            {
                "ok": True,
                "image_prompt": image_prompt,
                "negative_prompt": negative_prompt,
            },
            ensure_ascii=False,
            indent=2,
        )

    @tool
    def validate_logo_prompt(prompts_json: str) -> str:
        """
        Validates JSON from draft_logo_prompt: required keys, lengths, brand name in image_prompt.
        """
        return _validate(prompts_json)

    return validate_logo_prompt


def make_render_logo_image_tool(holder: dict[str, Any]):
    """
    holder: mutated by the tool with image_bytes, mime, image_source, skipped, render_error.
    """

    @traceable(name="tool.render_logo_image", tags=["branding", "tool", "logo_render"])
    async def _render(image_prompt: str, negative_prompt: str = "") -> str:
        holder.pop("image_bytes", None)
        holder.pop("mime", None)
        holder.pop("image_source", None)
        holder.pop("skipped", None)
        holder.pop("render_error", None)

        provider = (LOGO_IMAGE_PROVIDER or "huggingface").strip().lower()
        if provider == "none":
            holder["skipped"] = True
            return json.dumps(
                {
                    "ok": True,
                    "skipped": True,
                    "reason": "LOGO_IMAGE_PROVIDER=none (no image API call).",
                },
                ensure_ascii=False,
                indent=2,
            )

        ip = (image_prompt or "").strip()
        np = (negative_prompt or "").strip()
        if not ip:
            return json.dumps(
                {"ok": False, "error": "image_prompt is empty for render."},
                ensure_ascii=False,
                indent=2,
            )

        try:
            data, mime, src = await fetch_logo_image_hf_with_pollinations_fallback(
                ip,
                np,
                model=LOGO_HF_IMAGE_MODEL,
                pollinations_fallback=LOGO_POLLINATIONS_FALLBACK,
            )
            holder["image_bytes"] = data
            holder["mime"] = mime
            holder["image_source"] = src
            return json.dumps(
                {
                    "ok": True,
                    "byte_count": len(data) if data else 0,
                    "source": src,
                    "mime": mime,
                },
                ensure_ascii=False,
                indent=2,
            )
        except Exception as e:
            err = str(e)
            holder["render_error"] = err
            return json.dumps(
                {"ok": False, "error": err},
                ensure_ascii=False,
                indent=2,
            )

    @tool
    async def render_logo_image(image_prompt: str, negative_prompt: str = "") -> str:
        """
        Runs text-to-image after validate_logo_prompt succeeded. Pass the same image_prompt and negative_prompt
        that were validated. Do not call before validation returns ok: true.
        """
        return await _render(image_prompt, negative_prompt)

    return render_logo_image
