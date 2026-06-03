"""
Generation d'image pour posts : NVIDIA flux.2-klein-4b uniquement.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
from typing import Any

import httpx

from config.content_generation_config import content_http_timeout
from observability.langsmith_tracing import agent_trace

_log = logging.getLogger("brandai.content_image_client")


def _nvidia_image_keys() -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for raw in (os.getenv("NVIDEA_IMAGE_API"),):
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


def _nvidia_image_http_timeout() -> httpx.Timeout:
    """
    Images Flux : illimité par défaut (comme le reste du pipeline contenu).
    Plafond optionnel : CONTENT_NVIDIA_IMAGE_TIMEOUT_S=90
    Sinon CONTENT_HTTP_TIMEOUT_S s'applique via content_http_timeout().
    """
    raw = (os.getenv("CONTENT_NVIDIA_IMAGE_TIMEOUT_S") or "").strip()
    if raw in ("0", "none", "off", ""):
        return content_http_timeout()
    try:
        return httpx.Timeout(float(raw))
    except ValueError:
        return content_http_timeout()


def _nvidia_image_model_path(model: str) -> str:
    m = (model or "").strip()
    if not m:
        return "black-forest-labs/flux.2-klein-4b"
    if "/" in m:
        return m
    return f"black-forest-labs/{m}"


def _retryable_image_http_status(status: int) -> bool:
    return status in (429, 502, 503, 504)


def _decode_b64_payload(value: str) -> bytes:
    v = (value or "").strip()
    if not v:
        return b""
    encoded = v.split(",", 1)[-1]
    try:
        return base64.b64decode(encoded)
    except Exception:
        return b""


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
    httpx_timeout = _nvidia_image_http_timeout()
    size = (os.getenv("CONTENT_NVIDIA_IMAGE_SIZE") or "1024x1024").strip()
    model_path = _nvidia_image_model_path(m)
    endpoint = f"{_nvidia_image_base_url()}/genai/{model_path}"
    last_err: Exception | None = None
    per_key_attempts = max(1, int(os.getenv("CONTENT_NVIDIA_IMAGE_ATTEMPTS", "3")))

    for i, key in enumerate(keys):
        for attempt in range(per_key_attempts):
            try:
                _log.info(
                    "[content_image_client] NVIDIA — model=%s cle %d/%d timeout=%s attempt=%d/%d",
                    m,
                    i + 1,
                    len(keys),
                    "illimite",
                    attempt + 1,
                    per_key_attempts,
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
                async with httpx.AsyncClient(timeout=httpx_timeout, follow_redirects=True) as client:
                    r = await client.post(endpoint, headers=headers, json=body)
                    if r.status_code >= 400:
                        if _retryable_image_http_status(r.status_code) and attempt < per_key_attempts - 1:
                            delay = 45.0 * (attempt + 1)
                            _log.warning(
                                "[content_image_client] HTTP %s → retry dans %.0fs",
                                r.status_code,
                                delay,
                            )
                            await asyncio.sleep(delay)
                            continue
                        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:240]}")
                    payload = r.json()

                    image_field = payload.get("image") if isinstance(payload, dict) else None
                    if isinstance(image_field, str) and image_field.strip():
                        raw = _decode_b64_payload(image_field)
                        if raw:
                            _log.info("[content_image_client] NVIDIA OK | %d octets", len(raw))
                            return raw, "image/png"

                    artifacts = payload.get("artifacts") if isinstance(payload, dict) else None
                    if isinstance(artifacts, list):
                        for item in artifacts:
                            if not isinstance(item, dict):
                                continue
                            raw = _decode_b64_payload(str(item.get("base64") or ""))
                            if raw:
                                _log.info("[content_image_client] NVIDIA OK | %d octets", len(raw))
                                return raw, "image/png"
                            raw = _decode_b64_payload(str(item.get("b64_json") or ""))
                            if raw:
                                _log.info("[content_image_client] NVIDIA OK | %d octets", len(raw))
                                return raw, "image/png"

                    data = payload.get("data") if isinstance(payload, dict) else None
                    first = data[0] if isinstance(data, list) and data and isinstance(data[0], dict) else {}
                    b64 = first.get("b64_json")
                    if isinstance(b64, str) and b64.strip():
                        raw = _decode_b64_payload(b64)
                        if raw:
                            _log.info("[content_image_client] NVIDIA OK | %d octets", len(raw))
                            return raw, "image/png"

                    url_img = first.get("url")
                    if isinstance(url_img, str) and url_img.strip():
                        rr = await client.get(url_img)
                        rr.raise_for_status()
                        ct = (rr.headers.get("content-type") or "").lower()
                        _log.info("[content_image_client] NVIDIA OK (url) | %d octets", len(rr.content))
                        if "jpeg" in ct or "jpg" in ct:
                            return rr.content, "image/jpeg"
                        if "webp" in ct:
                            return rr.content, "image/webp"
                        return rr.content, "image/png"

                    if isinstance(payload, dict):
                        _log.warning(
                            "[content_image_client] NVIDIA reponse sans image | keys=%s",
                            ",".join(sorted(payload.keys()))[:180],
                        )
                    raise RuntimeError("NVIDIA image: aucune image decodable")
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                retryable = _retryable_image_http_status(
                    getattr(getattr(e, "response", None), "status_code", 0) or 0
                ) or any(t in msg for t in ("504", "502", "503", "429", "gateway timeout"))
                if retryable and attempt < per_key_attempts - 1:
                    delay = 45.0 * (attempt + 1)
                    _log.warning(
                        "[content_image_client] erreur retryable → retry dans %.0fs | %s",
                        delay,
                        str(e)[:120],
                    )
                    await asyncio.sleep(delay)
                    continue
                _log.warning("[content_image_client] NVIDIA erreur: %s", str(e)[:220])
                break
    raise RuntimeError(f"NVIDIA image indisponible: {last_err}")


@agent_trace("content.fetch_image", tags=["content_generation", "image"])
async def fetch_content_image(
    image_prompt: str,
    negative_prompt: str = "",
) -> tuple[bytes, str, str]:
    """Retourne (octets, mime, source='nvidia') via NVIDIA flux.2-klein-4b."""
    data, mime = await fetch_content_image_nvidia(image_prompt, negative_prompt)
    return data, mime, "nvidia"
