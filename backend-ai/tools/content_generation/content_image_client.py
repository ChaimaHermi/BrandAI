"""
Génération d’image pour posts : HF Qwen (timeout CONTENT_HF_TIMEOUT_S) → Pollinations.
Ne modifie pas logo_image_client.
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
from typing import Any
from urllib.parse import quote, urlencode

import httpx

from config.content_generation_config import (
    CONTENT_HF_IMAGE_MODEL,
    CONTENT_HF_TIMEOUT_S,
    CONTENT_POLLINATIONS_FALLBACK,
    CONTENT_POLLINATIONS_MODEL_DEFAULT,
)
from config.settings import HF_KEYS

_log = logging.getLogger("brandai.content_image_client")


def _pollinations_slug() -> str:
    raw = (os.getenv("CONTENT_POLLINATIONS_MODEL") or "").strip()
    return raw if raw else CONTENT_POLLINATIONS_MODEL_DEFAULT


def _pollinations_url(full_prompt: str) -> str:
    max_len = int(os.getenv("CONTENT_POLLINATIONS_MAX_PROMPT_CHARS", "2400"))
    p = (full_prompt or "").strip()
    if len(p) > max_len:
        p = p[:max_len].rstrip()
    encoded = quote(p, safe="")
    model = _pollinations_slug()
    w = int(os.getenv("CONTENT_POLLINATIONS_WIDTH", "1024"))
    h = int(os.getenv("CONTENT_POLLINATIONS_HEIGHT", "1024"))
    q: dict[str, str] = {"width": str(w), "height": str(h), "model": model}
    base = (
        os.getenv("CONTENT_POLLINATIONS_BASE_URL") or "https://image.pollinations.ai/prompt"
    ).rstrip("/")
    return f"{base}/{encoded}?{urlencode(q)}"


def _image_to_png_bytes(image: Any) -> tuple[bytes, str]:
    try:
        from PIL import Image
    except ModuleNotFoundError as e:
        raise RuntimeError("Pillow requis pour la conversion image.") from e

    if isinstance(image, Image.Image):
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue(), "image/png"
    if isinstance(image, (bytes, bytearray)):
        return bytes(image), "image/png"
    raise TypeError(f"Type image inattendu : {type(image)}")


def _text_to_image_sync(api_key: str, prompt: str, model: str) -> Any:
    from huggingface_hub import InferenceClient

    client = InferenceClient(provider="replicate", token=api_key)
    return client.text_to_image(prompt=prompt, model=model)


async def fetch_content_image_huggingface(
    image_prompt: str,
    negative_prompt: str = "",
    *,
    model: str | None = None,
) -> tuple[bytes, str]:
    full = (image_prompt or "").strip()
    if not full:
        raise ValueError("image_prompt vide")
    if negative_prompt:
        full = f"{full}. Avoid: {negative_prompt.strip()}"

    m = (model or CONTENT_HF_IMAGE_MODEL).strip()
    if not HF_KEYS:
        raise RuntimeError("Aucune clé Hugging Face (HF_TOKEN_*)")

    for i, api_key in enumerate(HF_KEYS):
        try:
            tmo = CONTENT_HF_TIMEOUT_S
            _log.info(
                "[content_image_client] HF — model=%s clé %d/%d timeout=%.0fs",
                m,
                i + 1,
                len(HF_KEYS),
                tmo,
            )
            image = await asyncio.wait_for(
                asyncio.to_thread(_text_to_image_sync, api_key, full, m),
                timeout=tmo,
            )
            raw, mime = _image_to_png_bytes(image)
            _log.info("[content_image_client] HF OK | %d octets", len(raw))
            return raw, mime
        except asyncio.TimeoutError as te:
            _log.warning("[content_image_client] HF timeout %.0fs → fallback", tmo)
            raise RuntimeError(f"Hugging Face timeout ({tmo:.0f}s)") from te
        except Exception as e:
            _log.warning("[content_image_client] HF erreur : %s", str(e)[:200])
            if i + 1 < len(HF_KEYS):
                continue
            raise


async def fetch_content_image_pollinations(
    image_prompt: str,
    negative_prompt: str = "",
) -> tuple[bytes, str]:
    full = (image_prompt or "").strip()
    if not full:
        raise ValueError("image_prompt vide")
    if negative_prompt:
        full = f"{full}. Avoid: {negative_prompt.strip()}"

    url = _pollinations_url(full)
    timeout = float(os.getenv("CONTENT_POLLINATIONS_TIMEOUT_S", "120"))
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        r = await client.get(url)
        r.raise_for_status()
        body = r.content
        ct = (r.headers.get("content-type") or "").split(";")[0].strip().lower()

    if not body:
        raise RuntimeError("Pollinations réponse vide")
    if "application/json" in ct or (body[:1] == b"{" and b'"error"' in body[:400]):
        raise RuntimeError("Pollinations a renvoyé une erreur JSON.")

    mime = "image/jpeg" if "jpeg" in ct or "jpg" in ct else "image/png"
    _log.info("[content_image_client] Pollinations OK | %d octets", len(body))
    return body, mime


async def fetch_content_image_hf_then_pollinations(
    image_prompt: str,
    negative_prompt: str = "",
) -> tuple[bytes, str, str]:
    """Retourne (octets, mime, source) avec source huggingface | pollinations."""
    if not HF_KEYS:
        if not CONTENT_POLLINATIONS_FALLBACK:
            raise RuntimeError("Pas de clé HF et fallback Pollinations désactivé.")
        data, mime = await fetch_content_image_pollinations(image_prompt, negative_prompt)
        return data, mime, "pollinations"

    try:
        data, mime = await fetch_content_image_huggingface(image_prompt, negative_prompt)
        return data, mime, "huggingface"
    except Exception as hf_err:
        if not CONTENT_POLLINATIONS_FALLBACK:
            raise RuntimeError(f"Hugging Face : {hf_err}") from hf_err
        _log.warning("[content_image_client] HF → Pollinations | %s", str(hf_err)[:200])
        data, mime = await fetch_content_image_pollinations(image_prompt, negative_prompt)
        return data, mime, "pollinations"
