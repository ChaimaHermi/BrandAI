"""
Génération d’image logo : Hugging Face InferenceClient (Replicate) + Qwen Image.
Fallback : Pollinations GET public (image.pollinations.ai), modèle par défaut zimage (Z-Image Turbo).
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
from typing import Any
from urllib.parse import quote, urlencode

_log = logging.getLogger("brandai.logo_image_client")


def _hf_call_timeout_s() -> float:
    return float(os.getenv("LOGO_HF_CALL_TIMEOUT_S", "480"))


def _hf_keys_ordered() -> list[str]:
    from config.settings import HF_KEYS

    if HF_KEYS:
        return list(HF_KEYS)
    raise RuntimeError(
        "Aucune clé Hugging Face : définissez HF_TOKEN_1 et HF_TOKEN_2 "
        "(ou HF_TOKEN / HUGGINGFACE_HUB_TOKEN) dans .env"
    )


def _image_to_png_bytes(image: Any) -> tuple[bytes, str]:
    try:
        from PIL import Image
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "Package Pillow (PIL) manquant. pip install Pillow (ou pip install -r requirements.txt)."
        ) from e

    if isinstance(image, Image.Image):
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue(), "image/png"
    if isinstance(image, (bytes, bytearray)):
        return bytes(image), "image/png"
    raise TypeError(f"Type image inattendu : {type(image)}")


def _hf_fatal_model_error(err: Exception) -> bool:
    msg = str(err).lower()
    if "model" in msg and any(
        x in msg for x in ("not found", "unknown", "does not exist", "invalid model", "no inference")
    ):
        return True
    return False


def _text_to_image_sync(api_key: str, prompt: str, model: str) -> Any:
    try:
        from huggingface_hub import InferenceClient
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "Package huggingface_hub manquant dans l’environnement backend-ai. "
            "pip install huggingface_hub Pillow (ou requirements.txt)."
        ) from e

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
                m,
                i + 1,
                len(keys),
                len(full),
            )
            tmo = _hf_call_timeout_s()
            try:
                image = await asyncio.wait_for(
                    asyncio.to_thread(_text_to_image_sync, api_key, full, m),
                    timeout=tmo,
                )
            except asyncio.TimeoutError as te:
                raise RuntimeError(
                    f"Délai Hugging Face dépassé ({tmo:.0f}s). "
                    "Augmentez LOGO_HF_CALL_TIMEOUT_S dans .env si besoin."
                ) from te
            raw, mime = _image_to_png_bytes(image)
            _log.info("[logo_image_client] HF — image reçue %s, %d octets", mime, len(raw))
            return raw, mime
        except Exception as e:
            _log.warning(
                "[logo_image_client] HF clé #%d échouée : %s",
                i + 1,
                str(e)[:240],
            )
            if _hf_fatal_model_error(e):
                raise RuntimeError(
                    f"Génération image Hugging Face échouée (modèle={m}) : {e}"
                ) from e
            if i + 1 < len(keys):
                continue
            raise RuntimeError(
                f"Génération image Hugging Face échouée (modèle={m}) : {e}"
            ) from e


def _pollinations_norm_key(name: str) -> str:
    return " ".join(name.strip().lower().replace("-", " ").split())


# Libellés catalogue → slug ?model= sur image.pollinations.ai
_POLLINATIONS_SLUG_BY_ALIAS: dict[str, str] = {
    _pollinations_norm_key("Z-Image Turbo"): "zimage",
    _pollinations_norm_key("z-image-turbo"): "zimage",
    _pollinations_norm_key("Qwen Image Plus"): "qwen-image",
    _pollinations_norm_key("Qwen Image"): "qwen-image",
    _pollinations_norm_key("Flux Schnell"): "flux",
    _pollinations_norm_key("Flux"): "flux",
}


def _pollinations_resolve_model_slug(raw: str, default: str) -> str:
    s = (raw or "").strip() or default
    k = _pollinations_norm_key(s)
    if k in _POLLINATIONS_SLUG_BY_ALIAS:
        out = _POLLINATIONS_SLUG_BY_ALIAS[k]
        if k != _pollinations_norm_key(out):
            _log.info(
                "[logo_image_client] Pollinations — LOGO_POLLINATIONS_MODEL %r → slug %r",
                s,
                out,
            )
        return out
    if " " in s:
        _log.warning(
            "[logo_image_client] Pollinations — modèle %r : utilisez un slug (zimage, qwen-image, flux).",
            s,
        )
    return s.lower()


def _pollinations_public_get_url(full_prompt: str) -> str:
    from config.branding_config import LOGO_POLLINATIONS_MODEL_DEFAULT

    max_len = int(os.getenv("LOGO_POLLINATIONS_MAX_PROMPT_CHARS", "2400"))
    p = (full_prompt or "").strip()
    if len(p) > max_len:
        p = p[:max_len].rstrip()
        _log.warning(
            "[logo_image_client] Pollinations GET — prompt tronqué à %d car.",
            max_len,
        )
    encoded = quote(p, safe="")
    raw = (os.getenv("LOGO_POLLINATIONS_MODEL") or "").strip()
    model = _pollinations_resolve_model_slug(
        raw if raw else LOGO_POLLINATIONS_MODEL_DEFAULT,
        LOGO_POLLINATIONS_MODEL_DEFAULT,
    )
    w = int(os.getenv("LOGO_POLLINATIONS_WIDTH", "1024"))
    h = int(os.getenv("LOGO_POLLINATIONS_HEIGHT", "1024"))
    q: dict[str, str] = {"width": str(w), "height": str(h), "model": model}
    base = (os.getenv("LOGO_POLLINATIONS_BASE_URL") or "https://image.pollinations.ai/prompt").rstrip("/")
    return f"{base}/{encoded}?{urlencode(q)}"


async def fetch_logo_image_pollinations(
    image_prompt: str,
    negative_prompt: str = "",
) -> tuple[bytes, str]:
    try:
        import httpx
    except ModuleNotFoundError as e:
        raise RuntimeError("Package httpx manquant. pip install httpx.") from e

    full = (image_prompt or "").strip()
    if not full:
        raise ValueError("image_prompt vide")
    if negative_prompt:
        full = f"{full}. Avoid: {negative_prompt.strip()}"

    url = _pollinations_public_get_url(full)
    timeout = float(os.getenv("LOGO_POLLINATIONS_TIMEOUT_S", "120"))
    _log.info(
        "[logo_image_client] Pollinations — GET public (prompt %d car., timeout=%.0fs)",
        len(full),
        timeout,
    )
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        r = await client.get(url)
        r.raise_for_status()
        body = r.content
        ct = (r.headers.get("content-type") or "").split(";")[0].strip().lower()

    if not body:
        raise RuntimeError("Réponse Pollinations vide")

    if "application/json" in ct or (body[:1] == b"{" and b'"error"' in body[:400]):
        try:
            err = json.loads(body.decode("utf-8", errors="replace"))
            eo = err.get("error") if isinstance(err, dict) else err
            msg = eo if isinstance(eo, str) else str(eo or err)
            raise RuntimeError(f"Pollinations (erreur JSON) : {msg!s}")
        except json.JSONDecodeError:
            raise RuntimeError("Pollinations a renvoyé du JSON au lieu d’une image.")

    if "jpeg" in ct or "jpg" in ct:
        mime = "image/jpeg"
    elif "webp" in ct:
        mime = "image/webp"
    else:
        mime = "image/png"

    _log.info("[logo_image_client] Pollinations — image %s, %d octets", mime, len(body))
    return body, mime


async def fetch_logo_image_hf_with_pollinations_fallback(
    image_prompt: str,
    negative_prompt: str = "",
    *,
    model: str | None = None,
    pollinations_fallback: bool = True,
) -> tuple[bytes, str, str]:
    from config.settings import HF_KEYS

    if not HF_KEYS:
        if not pollinations_fallback:
            raise RuntimeError(
                "Aucune clé Hugging Face et fallback Pollinations désactivé (LOGO_POLLINATIONS_FALLBACK=0)."
            )
        _log.info("[logo_image_client] Pas de clé HF — Pollinations uniquement (défaut zimage / Z-Image Turbo).")
        data, mime = await fetch_logo_image_pollinations(image_prompt, negative_prompt)
        return data, mime, "pollinations"

    try:
        data, mime = await fetch_logo_image_huggingface(
            image_prompt,
            negative_prompt,
            model=model,
        )
        return data, mime, "huggingface"
    except Exception as hf_err:
        if _hf_fatal_model_error(hf_err):
            raise RuntimeError(
                f"Génération Hugging Face échouée (pas de fallback Pollinations) : {hf_err}"
            ) from hf_err
        if not pollinations_fallback:
            raise RuntimeError(
                f"Hugging Face échoué (fallback Pollinations désactivé) : {hf_err}"
            ) from hf_err
        _log.warning("[logo_image_client] HF indisponible → Pollinations : %s", str(hf_err)[:280])
        try:
            data, mime = await fetch_logo_image_pollinations(image_prompt, negative_prompt)
            return data, mime, "pollinations"
        except Exception as pol_err:
            raise RuntimeError(
                f"Hugging Face : {hf_err} ; Pollinations : {pol_err}"
            ) from pol_err