"""Upload image générée vers Cloudinary → secure_url."""

from __future__ import annotations

import asyncio
import io
import logging
import mimetypes
from urllib.parse import urlparse

import httpx

from config.content_generation_config import (
    CONTENT_CLOUDINARY_API_KEY,
    CONTENT_CLOUDINARY_API_SECRET,
    CONTENT_CLOUDINARY_CLOUD_NAME,
    CONTENT_CLOUDINARY_UPLOAD_FOLDER,
)

logger = logging.getLogger("brandai.content_cloudinary")

_MAX_IMPORT_BYTES = 8 * 1024 * 1024


def is_brandai_cloudinary_url(url: str) -> bool:
    """True si l’URL pointe déjà vers notre compte res.cloudinary.com/<cloud_name>/…"""
    name = (CONTENT_CLOUDINARY_CLOUD_NAME or "").strip().lower()
    if not name:
        return False
    try:
        p = urlparse((url or "").strip())
    except Exception:
        return False
    if (p.scheme or "").lower() != "https" or (p.hostname or "").lower() != "res.cloudinary.com":
        return False
    parts = [x for x in p.path.split("/") if x]
    return bool(parts) and parts[0].lower() == name


async def ensure_cloudinary_public_url(image_url: str) -> str:
    """
    Garantit une URL **HTTPS** hébergée sur le compte Cloudinary du projet.

    - Si l’URL est déjà `res.cloudinary.com/<notre cloud>/…`, la retourne telle quelle.
    - Sinon : téléchargement → `upload_image_bytes` → `secure_url` (URL publique stable pour LinkedIn / Meta).
    """
    u = (image_url or "").strip()
    if not u.startswith("https://"):
        raise RuntimeError("URL d’image invalide : HTTPS requis.")
    if is_brandai_cloudinary_url(u):
        return u
    if not cloudinary_configured():
        raise RuntimeError(
            "Cloudinary non configuré : impossible d’obtenir une URL publique pour cette image. "
            "Définissez CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET."
        )
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        r = await client.get(u)
        if r.status_code != 200:
            raise RuntimeError(f"Téléchargement image impossible : HTTP {r.status_code}")
        data = r.content
        if len(data) > _MAX_IMPORT_BYTES:
            raise RuntimeError("Image trop volumineuse (max ~8 Mo).")
        ct = (r.headers.get("content-type") or "").split(";")[0].strip().lower()
        if not ct or ct == "application/octet-stream":
            path = u.split("?", 1)[0].lower()
            guess, _ = mimetypes.guess_type(path)
            ct = guess or "image/jpeg"
        if not ct.startswith("image/"):
            raise RuntimeError("L’URL ne renvoie pas une image (Content-Type attendu : image/*).")

    secure = await asyncio.to_thread(upload_image_bytes, data, mime=ct)
    logger.info("[cloudinary_upload] URL externe → Cloudinary | %s", secure[:80])
    return secure


def cloudinary_configured() -> bool:
    return bool(
        CONTENT_CLOUDINARY_CLOUD_NAME
        and CONTENT_CLOUDINARY_API_KEY
        and CONTENT_CLOUDINARY_API_SECRET
    )


def upload_image_bytes(
    data: bytes,
    *,
    mime: str = "image/png",
    folder: str | None = None,
) -> str:
    """Retourne secure_url. Lève si Cloudinary non configuré."""
    upload_folder = (folder or CONTENT_CLOUDINARY_UPLOAD_FOLDER).strip() or "brandai/content"
    if not cloudinary_configured():
        raise RuntimeError(
            "Cloudinary non configuré : définissez CONTENT_CLOUDINARY_* ou "
            "CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET"
        )

    try:
        import cloudinary
        import cloudinary.uploader
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "Package cloudinary manquant. pip install cloudinary"
        ) from e

    cloudinary.config(
        cloud_name=CONTENT_CLOUDINARY_CLOUD_NAME,
        api_key=CONTENT_CLOUDINARY_API_KEY,
        api_secret=CONTENT_CLOUDINARY_API_SECRET,
    )

    resource_type = "image"
    upload_kwargs: dict = {
        "folder": upload_folder,
        "resource_type": resource_type,
    }

    buf = io.BytesIO(data)
    buf.seek(0)
    result = cloudinary.uploader.upload(buf, **upload_kwargs)
    url = (result or {}).get("secure_url")
    if not url:
        raise RuntimeError("Cloudinary : pas de secure_url dans la réponse.")
    logger.info("[cloudinary_upload] ok | %s", url[:80])
    return str(url)
