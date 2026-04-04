"""
Génération d’image logo : OpenRouter + FLUX.2 Pro (modalités image), comme le script de test local.
Optionnel : Pollinations (URL) si `LOGO_IMAGE_PROVIDER=pollinations`.
"""

from __future__ import annotations

import base64
import logging
import os
from urllib.parse import quote

import httpx

_log = logging.getLogger("brandai.logo_image_client")

DEFAULT_POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"
DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_FLUX_MODEL = "black-forest-labs/flux.2-pro"


def _openrouter_bearer() -> str:
    """OPENROUTER_API_KEY ou OPENROUTER_API_KEY_1 / _2 / _3 (settings)."""
    single = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    if single:
        return single
    from config.settings import OPENROUTER_KEYS

    if OPENROUTER_KEYS:
        return OPENROUTER_KEYS[0]
    raise RuntimeError(
        "Clé OpenRouter manquante : définissez OPENROUTER_API_KEY ou OPENROUTER_API_KEY_1 dans .env"
    )


def _decode_data_url(data_url: str) -> tuple[bytes, str]:
    if not data_url.startswith("data:image"):
        raise ValueError("Réponse image OpenRouter : data URL attendue (data:image/...;base64,...)")
    meta, b64 = data_url.split(",", 1)
    mime = "image/png"
    if "image/jpeg" in meta or "image/jpg" in meta:
        mime = "image/jpeg"
    elif "image/webp" in meta:
        mime = "image/webp"
    raw = base64.b64decode(b64)
    return raw, mime


async def fetch_logo_image_openrouter_flux(
    image_prompt: str,
    negative_prompt: str = "",
    *,
    model: str | None = None,
    timeout_s: float = 180.0,
) -> tuple[bytes, str]:
    """
    POST /chat/completions avec `modalities: ["image"]` — aligné sur le flux FLUX.2 Pro OpenRouter.
    """
    full = (image_prompt or "").strip()
    if not full:
        raise ValueError("image_prompt vide")
    if negative_prompt:
        full = f"{full}. Avoid: {negative_prompt.strip()}"

    url = (os.getenv("OPENROUTER_API_URL") or DEFAULT_OPENROUTER_URL).strip()
    m = (model or os.getenv("LOGO_OPENROUTER_MODEL") or DEFAULT_FLUX_MODEL).strip()
    payload = {
        "model": m,
        "messages": [{"role": "user", "content": full}],
        "modalities": ["image"],
        "image_config": {"aspect_ratio": "1:1"},
    }
    headers = {
        "Authorization": f"Bearer {_openrouter_bearer()}",
        "Content-Type": "application/json",
    }
    t = httpx.Timeout(timeout_s, connect=20.0)
    _log.info(
        "[logo_image_client] OpenRouter FLUX — POST %s model=%s (prompt %d car.)",
        url,
        m,
        len(full),
    )
    async with httpx.AsyncClient(timeout=t) as client:
        r = await client.post(url, headers=headers, json=payload)

    if r.status_code != 200:
        detail = ""
        try:
            err = r.json()
            if isinstance(err, dict):
                raw = err.get("error")
                if isinstance(raw, dict):
                    detail = raw.get("message") or str(raw)[:400]
                elif isinstance(raw, str):
                    detail = raw[:400]
                else:
                    detail = err.get("message") or str(raw or "")[:400]
        except Exception:
            detail = (r.text or "")[:500]
        detail = (detail or "").strip() or f"HTTP {r.status_code}"

        if r.status_code == 402:
            raise RuntimeError(
                "OpenRouter : crédits ou facturation requis (HTTP 402). "
                "Ajoutez des crédits sur https://openrouter.ai/settings/credits ou utilisez un autre modèle / fournisseur. "
                f"Détail : {detail}"
            )
        if r.status_code == 401:
            raise RuntimeError(
                f"OpenRouter : clé API invalide ou expirée (HTTP 401). {detail}"
            )
        if r.status_code == 429:
            raise RuntimeError(
                f"OpenRouter : limite de débit ou quota (HTTP 429). {detail}"
            )
        raise RuntimeError(f"OpenRouter image HTTP {r.status_code}: {detail}")

    data = r.json()

    msg = (data.get("choices") or [{}])[0].get("message") or {}
    images = msg.get("images") or []
    if not images:
        raise RuntimeError("OpenRouter n’a renvoyé aucune image (choices[0].message.images vide).")

    img0 = images[0]
    data_url = (img0.get("image_url") or {}).get("url") or ""
    if not isinstance(data_url, str) or not data_url.startswith("data:image"):
        raise RuntimeError(f"Format d’image OpenRouter inattendu : {str(data_url)[:160]}")

    raw_bytes, mime = _decode_data_url(data_url)
    _log.info(
        "[logo_image_client] OpenRouter FLUX — image reçue HTTP 200, %s, %d octets",
        mime,
        len(raw_bytes),
    )
    return raw_bytes, mime


async def fetch_logo_image_pollinations(
    image_prompt: str,
    *,
    width: int = 512,
    height: int = 512,
    timeout_s: float = 120.0,
) -> bytes:
    encoded = quote((image_prompt or "").strip(), safe="")
    if not encoded:
        raise ValueError("image_prompt vide")
    base = os.getenv("POLLINATIONS_IMAGE_BASE", DEFAULT_POLLINATIONS_BASE).rstrip("/")
    url = f"{base}/{encoded}?width={width}&height={height}&nologo=true"
    t = httpx.Timeout(timeout_s, connect=15.0)
    async with httpx.AsyncClient(timeout=t, follow_redirects=True) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.content
