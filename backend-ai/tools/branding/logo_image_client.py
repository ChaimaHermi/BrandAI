"""
Génération d'image logo : Hugging Face InferenceClient (Replicate) → NVIDIA NIM flux.2-klein-4b.
"""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import os
from typing import Any

_log = logging.getLogger("brandai.logo_image_client")


def _hf_call_timeout_s() -> float:
    return float(os.getenv("LOGO_HF_CALL_TIMEOUT_S", "480"))


def _hf_keys_ordered() -> list[str]:
    from config.settings import HF_KEYS
    if HF_KEYS:
        return list(HF_KEYS)
    raise RuntimeError(
        "Aucune clé Hugging Face : définissez HF_TOKEN_1 dans .env"
    )


def _image_to_png_bytes(image: Any) -> tuple[bytes, str]:
    try:
        from PIL import Image
    except ModuleNotFoundError as e:
        raise RuntimeError("Package Pillow manquant. pip install Pillow") from e

    if isinstance(image, Image.Image):
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue(), "image/png"
    if isinstance(image, (bytes, bytearray)):
        return bytes(image), "image/png"
    raise TypeError(f"Type image inattendu : {type(image)}")


def _hf_fatal_model_error(err: Exception) -> bool:
    msg = str(err).lower()
    return "model" in msg and any(
        x in msg for x in ("not found", "unknown", "does not exist", "invalid model", "no inference")
    )


def _nvidia_image_keys() -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for raw in (os.getenv("NVIDIA_IMAGE_API") or os.getenv("NVIDEA_IMAGE_API"),):
        v = (raw or "").strip()
        if v and v not in seen:
            seen.add(v)
            keys.append(v)
    return keys


def _nvidia_image_model(default: str = "flux.2-klein-4b") -> str:
    return (
        os.getenv("LOGO_NVIDIA_IMAGE_MODEL")
        or os.getenv("NVIDIA_IMAGE_MODEL")
        or default
    ).strip()


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


def _walk_image_strings(node: Any) -> Any:
    """
    Parcourt recursivement un payload JSON et yield toute string qui ressemble
    a une image (base64 PNG/JPEG/WebP, data: URI, ou URL http/https vers image).
    Permet de decoder les reponses NVIDIA dont la cle exacte varie (image,
    images, generated_images, output, result, ...).
    """
    if isinstance(node, str):
        s = node.strip()
        if not s:
            return
        # data URI image
        if s.startswith("data:image"):
            yield ("b64", s)
            return
        # base64 brut (au moins 200 chars, charset valide)
        if len(s) > 200 and all(c.isalnum() or c in "+/=\n\r" for c in s[:60]):
            yield ("b64", s)
            return
        # URL directe
        low = s.lower()
        if low.startswith(("http://", "https://")) and any(
            low.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif")
        ):
            yield ("url", s)
            return
        # URL signee (sans extension explicite) — heuristique large
        if low.startswith(("http://", "https://")) and ("image" in low or "cdn" in low):
            yield ("url", s)
            return
        return
    if isinstance(node, dict):
        # Priorise les cles connues pour decoder en premier
        priority_keys = (
            "b64_json", "base64", "image", "imageBase64", "imageBytes",
            "url", "image_url",
        )
        for k in priority_keys:
            if k in node:
                yield from _walk_image_strings(node[k])
        for k, v in node.items():
            if k in priority_keys:
                continue
            yield from _walk_image_strings(v)
        return
    if isinstance(node, list):
        for item in node:
            yield from _walk_image_strings(item)
        return


def _text_to_image_sync(api_key: str, prompt: str, model: str) -> Any:
    try:
        from huggingface_hub import InferenceClient
    except ModuleNotFoundError as e:
        raise RuntimeError("Package huggingface_hub manquant. pip install huggingface_hub") from e

    client = InferenceClient(provider="replicate", token=api_key)
    return client.text_to_image(prompt=prompt, model=model)


async def fetch_logo_image_huggingface(
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

    m = (model or os.getenv("LOGO_HF_IMAGE_MODEL") or "Qwen/Qwen-Image").strip()
    keys = _hf_keys_ordered()

    for i, api_key in enumerate(keys):
        try:
            _log.info(
                "[logo_image_client] HF Replicate — model=%s clé #%d/%d (prompt %d car.)",
                m, i + 1, len(keys), len(full),
            )
            tmo = _hf_call_timeout_s()
            try:
                image = await asyncio.wait_for(
                    asyncio.to_thread(_text_to_image_sync, api_key, full, m),
                    timeout=tmo,
                )
            except asyncio.TimeoutError as te:
                raise RuntimeError(
                    f"Délai Hugging Face dépassé ({tmo:.0f}s). Augmentez LOGO_HF_CALL_TIMEOUT_S si besoin."
                ) from te
            raw, mime = _image_to_png_bytes(image)
            _log.info("[logo_image_client] HF — image reçue %s, %d octets", mime, len(raw))
            return raw, mime
        except Exception as e:
            _log.warning("[logo_image_client] HF clé #%d échouée : %s", i + 1, str(e)[:240])
            if _hf_fatal_model_error(e):
                raise RuntimeError(f"HF échoué (modèle={m}) : {e}") from e
            if i + 1 < len(keys):
                continue
            raise RuntimeError(f"HF échoué (modèle={m}) : {e}") from e


async def fetch_logo_image_nvidia(
    image_prompt: str,
    *,
    model: str | None = None,
) -> tuple[bytes, str]:
    try:
        import httpx
    except ModuleNotFoundError as e:
        raise RuntimeError("Package httpx manquant. pip install httpx") from e

    img_p = (image_prompt or "").strip()
    if not img_p:
        raise ValueError("image_prompt vide")

    keys = _nvidia_image_keys()
    if not keys:
        raise RuntimeError("Aucune clé NVIDIA — définissez NVIDEA_IMAGE_API dans .env")

    timeout = float(os.getenv("LOGO_NVIDIA_IMAGE_TIMEOUT_S", "90"))
    size = (os.getenv("LOGO_NVIDIA_IMAGE_SIZE") or "1024x1024").strip()
    m = (model or _nvidia_image_model()).strip()
    model_path = _nvidia_image_model_path(m)
    endpoint = f"{(os.getenv('NVIDIA_IMAGE_BASE_URL') or 'https://ai.api.nvidia.com/v1').rstrip('/')}/genai/{model_path}"
    last_err: Exception | None = None

    for i, key in enumerate(keys):
        try:
            _log.info(
                "[logo_image_client] NVIDIA — model=%s clé %d/%d prompt=%d chars",
                m, i + 1, len(keys), len(img_p),
            )
            headers = {
                "Authorization": f"Bearer {key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            # flux.2-klein-4b : negative_prompt non supporté
            body: dict[str, Any] = {
                "prompt": img_p,
                "seed": 0,
                "steps": int(os.getenv("LOGO_NVIDIA_IMAGE_STEPS", "4")),
            }
            if "x" in size:
                sw, sh = size.lower().split("x", 1)
                if sw.strip().isdigit() and sh.strip().isdigit():
                    body["width"] = int(sw.strip())
                    body["height"] = int(sh.strip())

            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                r = await client.post(endpoint, headers=headers, json=body)
                if r.status_code >= 400:
                    raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")

                # Parfois NVIDIA renvoie directement les bytes (image/png) au lieu d'un JSON.
                ctype = (r.headers.get("content-type") or "").lower()
                if ctype.startswith("image/"):
                    mime = "image/png"
                    if "jpeg" in ctype or "jpg" in ctype:
                        mime = "image/jpeg"
                    elif "webp" in ctype:
                        mime = "image/webp"
                    return r.content, mime

                try:
                    payload = r.json()
                except Exception as je:
                    raise RuntimeError(
                        f"NVIDIA : reponse non-JSON ({ctype}, {len(r.content)} octets) : {je}"
                    )

                # Decodeur generique : explore toutes les chaines base64/URL du payload.
                for kind, value in _walk_image_strings(payload):
                    if kind == "b64":
                        raw = _decode_b64_payload(value)
                        if raw and len(raw) > 256:
                            _log.info(
                                "[logo_image_client] NVIDIA — image decodee (base64, %d octets)",
                                len(raw),
                            )
                            return raw, "image/png"
                    elif kind == "url":
                        try:
                            rr = await client.get(value)
                            rr.raise_for_status()
                        except Exception as ue:
                            _log.warning(
                                "[logo_image_client] NVIDIA — URL image inaccessible (%s) : %s",
                                value[:80],
                                str(ue)[:120],
                            )
                            continue
                        ct = (rr.headers.get("content-type") or "").lower()
                        if "jpeg" in ct or "jpg" in ct:
                            return rr.content, "image/jpeg"
                        if "webp" in ct:
                            return rr.content, "image/webp"
                        return rr.content, "image/png"

                # Diagnostic : on log les cles racine du payload pour aider le debug.
                top_keys = list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__
                preview = str(payload)[:300] if not isinstance(payload, dict) else str({k: type(v).__name__ for k, v in payload.items()})[:300]
                raise RuntimeError(
                    f"NVIDIA : aucune image decodable dans la reponse "
                    f"(keys={top_keys}, preview={preview})"
                )
        except Exception as e:
            last_err = e
            _log.warning("[logo_image_client] NVIDIA clé #%d échouée : %s", i + 1, str(e)[:240])
            if i + 1 < len(keys):
                continue

    raise RuntimeError(f"NVIDIA échoué : {last_err}")


async def fetch_logo_image_hf_with_pollinations_fallback(
    image_prompt: str,
    negative_prompt: str = "",
    *,
    model: str | None = None,
    pollinations_fallback: bool = False,
) -> tuple[bytes, str, str]:
    """Chaîne : Hugging Face → NVIDIA. Pollinations désactivé."""
    from config.settings import HF_KEYS

    hf_err: Exception | None = None

    _log.info("[logo_image_client] ── Chaîne image : HF → NVIDIA ──")

    # 1) Hugging Face
    if HF_KEYS:
        _log.info("[logo_image_client] [1/2] Tentative Hugging Face (model=%s)…", model or "Qwen/Qwen-Image")
        try:
            data, mime = await fetch_logo_image_huggingface(image_prompt, negative_prompt, model=model)
            _log.info("[logo_image_client] ✓ [1/2] Hugging Face → %s %d octets", mime, len(data))
            return data, mime, "huggingface"
        except Exception as e:
            hf_err = e
            _log.warning("[logo_image_client] ✗ [1/2] Hugging Face échoué : %s → NVIDIA…", str(e)[:280])
    else:
        _log.warning("[logo_image_client] ✗ [1/2] Hugging Face ignoré : aucune clé HF_TOKEN dans .env")

    # 2) NVIDIA — toujours son propre modèle (flux.2-klein-4b), pas le modèle HF
    _log.info("[logo_image_client] [2/2] Tentative NVIDIA NIM (model=%s)…", _nvidia_image_model())
    try:
        data, mime = await fetch_logo_image_nvidia(image_prompt)
        _log.info("[logo_image_client] ✓ [2/2] NVIDIA → %s %d octets", mime, len(data))
        return data, mime, "nvidia"
    except Exception as e:
        details = []
        if hf_err:
            details.append(f"HF: {hf_err}")
        details.append(f"NVIDIA: {e}")
        _log.error("[logo_image_client] ✗ Tous les providers ont échoué : %s", " ; ".join(details))
        raise RuntimeError(" ; ".join(details)) from e
