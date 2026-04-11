"""
Génération d’image logo : Hugging Face InferenceClient (provider replicate) + modèle Qwen Image.
Rotation entre plusieurs clés HF (HF_TOKEN_1, HF_TOKEN_2, …).
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
from typing import Any

_log = logging.getLogger("brandai.logo_image_client")

# Délai max pour un appel text_to_image (secondes). Dépassement → erreur côté API au lieu d’attendre indéfiniment.
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


def _fatal_do_not_rotate_keys(err: Exception) -> bool:
    """Erreur identique pour toute clé (ex. modèle inconnu) : ne pas essayer la suivante."""
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
            "Package huggingface_hub manquant dans l’environnement Python qui exécute backend-ai. "
            "Depuis le dossier backend-ai : pip install huggingface_hub Pillow "
            "(ou pip install -r requirements.txt). "
            "Utilisez le même interpréteur que pour lancer uvicorn."
        ) from e

    client = InferenceClient(provider="replicate", token=api_key)
    return client.text_to_image(prompt=prompt, model=model)


async def fetch_logo_image_huggingface(
    image_prompt: str,
    negative_prompt: str = "",
    *,
    model: str | None = None,
) -> tuple[bytes, str]:
    """
    Génère une image via l’API Inference (backend Replicate), ex. Qwen/Qwen-Image.
    """
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
                    "Réessayez ou augmentez LOGO_HF_CALL_TIMEOUT_S dans .env."
                ) from te
            raw, mime = _image_to_png_bytes(image)
            _log.info(
                "[logo_image_client] HF — image reçue %s, %d octets",
                mime,
                len(raw),
            )
            return raw, mime
        except Exception as e:
            _log.warning(
                "[logo_image_client] HF clé #%d échouée : %s",
                i + 1,
                str(e)[:240],
            )
            if _fatal_do_not_rotate_keys(e):
                raise RuntimeError(
                    f"Génération image Hugging Face échouée (modèle={m}) : {e}"
                ) from e
            if i + 1 < len(keys):
                continue
            raise RuntimeError(
                f"Génération image Hugging Face échouée (modèle={m}) : {e}"
            ) from e
