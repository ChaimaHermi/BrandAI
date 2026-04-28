"""
Generation d'image pour posts :
Hugging Face (Qwen) -> NVIDIA Image API (flux.2-klein-4b) -> Pollinations.
"""

from __future__ import annotations

import asyncio
import base64
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


def _nvidia_image_keys() -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for raw in (
        os.getenv("NVIDEA_IMAGE_API"),
    ):
        val = (raw or "").strip()
        if val and val not in seen:
            seen.add(val)
            keys.append(val)
    return keys


def _nvidia_image_model(default: str = "flux.2-klein-4b") -> str:
    return (
        os.getenv("CONTENT_NVIDIA_IMAGE_MODEL")
        or os.getenv("NVIDIA_IMAGE_MODEL")
        or default
    ).strip()


def _nvidia_image_base_url() -> str:
    return (
        os.getenv("NVIDIA_IMAGE_BASE_URL") or "https://ai.api.nvidia.com/v1"
    ).rstrip("/")


def _nvidia_image_model_path(model: str) -> str:
    m = (model or "").strip()
    if not m:
        return "black-forest-labs/flux.2-klein-4b"
    if "/" in m:
        return m
    return f"black-forest-labs/{m}"


def _decode_b64_payload(value: str) -> bytes:
    v = (value or "").strip()
    if not v:
        return b""
    encoded = v.split(",", 1)[-1]
    try:
        return base64.b64decode(encoded)
    except Exception:
        return b""


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


async def fetch_content_image_nvidia(
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

    keys = _nvidia_image_keys()
    if not keys:
        raise RuntimeError("Aucune cle NVIDIA (NVIDEA_IMAGE_API)")

    m = (model or _nvidia_image_model()).strip()
    timeout = float(os.getenv("CONTENT_NVIDIA_IMAGE_TIMEOUT_S", "90"))
    size = (os.getenv("CONTENT_NVIDIA_IMAGE_SIZE") or "1024x1024").strip()
    model_path = _nvidia_image_model_path(m)
    endpoint = f"{_nvidia_image_base_url()}/genai/{model_path}"
    last_err: Exception | None = None

    for i, key in enumerate(keys):
        try:
            _log.info(
                "[content_image_client] NVIDIA image — model=%s cle %d/%d timeout=%.0fs",
                m,
                i + 1,
                len(keys),
                timeout,
            )
            headers = {
                "Authorization": f"Bearer {key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            body: dict[str, Any] = {
                "prompt": full,
                "seed": 0,
                "steps": int(os.getenv("CONTENT_NVIDIA_IMAGE_STEPS", "4")),
            }
            if "x" in size:
                sw, sh = size.lower().split("x", 1)
                if sw.strip().isdigit() and sh.strip().isdigit():
                    body["width"] = int(sw.strip())
                    body["height"] = int(sh.strip())
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                r = await client.post(endpoint, headers=headers, json=body)
                if r.status_code >= 400:
                    raise RuntimeError(f"HTTP {r.status_code}: {r.text[:240]}")
                payload = r.json()

                image_field = payload.get("image") if isinstance(payload, dict) else None
                if isinstance(image_field, str) and image_field.strip():
                    raw = _decode_b64_payload(image_field)
                    if raw:
                        return raw, "image/png"

                artifacts = payload.get("artifacts") if isinstance(payload, dict) else None
                if isinstance(artifacts, list):
                    for item in artifacts:
                        if not isinstance(item, dict):
                            continue
                        raw = _decode_b64_payload(str(item.get("base64") or ""))
                        if raw:
                            return raw, "image/png"
                        raw = _decode_b64_payload(str(item.get("b64_json") or ""))
                        if raw:
                            return raw, "image/png"

                data = payload.get("data") if isinstance(payload, dict) else None
                first = data[0] if isinstance(data, list) and data and isinstance(data[0], dict) else {}
                b64 = first.get("b64_json")
                if isinstance(b64, str) and b64.strip():
                    raw = _decode_b64_payload(b64)
                    if raw:
                        return raw, "image/png"

                url_img = first.get("url")
                if isinstance(url_img, str) and url_img.strip():
                    rr = await client.get(url_img)
                    rr.raise_for_status()
                    ct = (rr.headers.get("content-type") or "").lower()
                    if "jpeg" in ct or "jpg" in ct:
                        return rr.content, "image/jpeg"
                    if "webp" in ct:
                        return rr.content, "image/webp"
                    return rr.content, "image/png"

                if isinstance(payload, dict):
                    _log.warning(
                        "[content_image_client] NVIDIA reponse sans image decodable | keys=%s",
                        ",".join(sorted(payload.keys()))[:180],
                    )
                raise RuntimeError("NVIDIA image: aucune image decodable (image/artifacts/data/url)")
        except Exception as e:
            last_err = e
            _log.warning("[content_image_client] NVIDIA erreur: %s", str(e)[:220])
            if i + 1 < len(keys):
                continue
    raise RuntimeError(f"NVIDIA image indisponible: {last_err}")


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
    retries = int(os.getenv("CONTENT_POLLINATIONS_RETRIES", "2"))
    last_err: Exception | None = None
    body = b""
    ct = ""
    for attempt in range(1, retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                r = await client.get(url)
                r.raise_for_status()
                body = r.content
                ct = (r.headers.get("content-type") or "").split(";")[0].strip().lower()
            break
        except (httpx.ReadTimeout, httpx.TimeoutException) as e:
            last_err = e
            _log.warning(
                "[content_image_client] Pollinations timeout (attempt %d/%d, timeout=%.0fs)",
                attempt,
                retries,
                timeout,
            )
            if attempt < retries:
                await asyncio.sleep(1.2 * attempt)
        except Exception as e:
            last_err = e
            _log.warning(
                "[content_image_client] Pollinations erreur (attempt %d/%d): %s",
                attempt,
                retries,
                str(e)[:180],
            )
            if attempt < retries:
                await asyncio.sleep(1.2 * attempt)
    if not body and last_err is not None:
        raise RuntimeError(f"Pollinations indisponible: {last_err}") from last_err

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
    """Retourne (octets, mime, source) avec source huggingface | nvidia | pollinations."""
    if not HF_KEYS:
        _log.info("[content_image_client] Aucune cle HF, tentative NVIDIA en fallback primaire.")
    else:
        try:
            data, mime = await fetch_content_image_huggingface(image_prompt, negative_prompt)
            return data, mime, "huggingface"
        except Exception as hf_err:
            _log.warning("[content_image_client] HF indisponible -> NVIDIA fallback | %s", str(hf_err)[:200])

    try:
        data, mime = await fetch_content_image_nvidia(image_prompt, negative_prompt)
        return data, mime, "nvidia"
    except Exception as nv_err:
        if not CONTENT_POLLINATIONS_FALLBACK:
            raise RuntimeError(f"NVIDIA image : {nv_err}") from nv_err
        _log.warning("[content_image_client] NVIDIA -> Pollinations | %s", str(nv_err)[:200])
        data, mime = await fetch_content_image_pollinations(image_prompt, negative_prompt)
        return data, mime, "pollinations"
