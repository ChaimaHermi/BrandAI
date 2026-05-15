from __future__ import annotations

import asyncio
import logging
import os

logger = logging.getLogger("brandai.logo_originality")

_SERPAPI_URL = "https://serpapi.com/search.json"

# Cache session : si quota SerpApi épuisé ou erreur fatale, on arrête les appels
_api_disabled: bool = False

# Distance pHash en dessous de laquelle deux images sont considérées copies exactes.
# 0 = pixel-perfect identique
# 1-3 = identique (légère compression/resize)  ← seuil "kifkif"
# 4-8 = très similaire (même image retouchée)
# >8  = similaire en concept seulement → ignoré
_PHASH_EXACT_THRESHOLD = int(os.getenv("LOGO_PHASH_THRESHOLD", "3"))

# Nombre max de thumbnails à télécharger pour la comparaison pHash (limite le temps)
_MAX_THUMBNAILS_TO_CHECK = int(os.getenv("LOGO_PHASH_MAX_THUMBNAILS", "15"))


def _phash_distance(img_bytes_a: bytes, img_bytes_b: bytes) -> int | None:
    """Retourne la distance pHash entre deux images (0 = identiques). None si erreur."""
    try:
        import io
        import imagehash
        from PIL import Image
        img_a = Image.open(io.BytesIO(img_bytes_a)).convert("RGB")
        img_b = Image.open(io.BytesIO(img_bytes_b)).convert("RGB")
        return imagehash.phash(img_a) - imagehash.phash(img_b)
    except Exception as e:
        logger.debug("[originality] pHash erreur : %s", e)
        return None


async def _download_thumbnail(client, url: str) -> bytes | None:
    """Télécharge un thumbnail avec timeout court. Retourne None si échec."""
    try:
        r = await client.get(url, timeout=5.0, follow_redirects=True)
        if r.status_code == 200 and len(r.content) > 500:
            return r.content
    except Exception:
        pass
    return None


async def verifier_originalite_logo_bytes(
    image_bytes: bytes,
    *,
    max_similar: int = 2,
) -> tuple[bool, list[str]]:
    """
    Vérifie l'originalité du logo via SerpApi Google Lens + comparaison pHash.

    Flow :
      1. Upload image bytes sur Cloudinary → URL publique
      2. SerpApi Google Lens → visual_matches
      3. Pour chaque match, télécharge le thumbnail et compare le pHash
      4. is_original = True si moins de max_similar copies exactes (pHash < seuil)

    Seules les copies EXACTES (kifkif) sont comptées — pas les logos similaires en concept.
    """
    global _api_disabled

    if _api_disabled:
        logger.debug("[originality] SerpApi désactivé — vérification ignorée")
        return True, []

    api_key = (os.getenv("SERPAPI_KEY") or "").strip()
    if not api_key:
        logger.warning("[originality] SERPAPI_KEY absent — vérification ignorée")
        return True, []

    if not image_bytes:
        return True, []

    try:
        import httpx
    except ImportError:
        logger.warning("[originality] httpx non installé — vérification ignorée")
        return True, []

    # ── 1. Upload sur Cloudinary ─────────────────────────────────────────────
    try:
        from tools.content_generation.cloudinary_upload import upload_image_bytes
        image_url = await asyncio.to_thread(
            upload_image_bytes,
            image_bytes,
            mime="image/png",
            folder="brandai/logo-originality",
        )
        logger.info("[originality] Image uploadée → %s", image_url[:80])
    except Exception as exc:
        logger.warning("[originality] Upload Cloudinary échoué : %s — vérification ignorée", exc)
        return True, []

    # ── 2. SerpApi Google Lens ───────────────────────────────────────────────
    params = {
        "engine": "google_lens",
        "url": image_url,
        "api_key": api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(_SERPAPI_URL, params=params)

            if resp.status_code == 401:
                _api_disabled = True
                logger.error("[originality] SerpApi clé invalide (401) — désactivé.")
                return True, []

            if resp.status_code == 429:
                _api_disabled = True
                logger.error("[originality] SerpApi quota épuisé (429) — désactivé.")
                return True, []

            if not resp.is_success:
                logger.warning("[originality] SerpApi HTTP %d — ignoré", resp.status_code)
                return True, []

            data = resp.json()

            if "error" in data:
                err_msg = data["error"]
                if any(k in err_msg.lower() for k in ("credit", "plan", "quota")):
                    _api_disabled = True
                    logger.error("[originality] SerpApi quota : %s — désactivé.", err_msg)
                else:
                    logger.warning("[originality] SerpApi erreur : %s", err_msg)
                return True, []

            visual_matches = data.get("visual_matches") or []
            logger.info(
                "[originality] Google Lens — %d résultats visuels trouvés (seuil pHash=%d)",
                len(visual_matches), _PHASH_EXACT_THRESHOLD,
            )

            if not visual_matches:
                return True, []

            # ── 3. Comparaison pHash — copies exactes seulement ──────────────
            thumbnail_urls: list[str] = []
            for m in visual_matches:
                if not isinstance(m, dict):
                    continue
                thumb = m.get("thumbnail") or m.get("image_url") or ""
                if thumb and thumb.startswith("http"):
                    thumbnail_urls.append(thumb)
                if len(thumbnail_urls) >= _MAX_THUMBNAILS_TO_CHECK:
                    break

            exact_copy_urls: list[str] = []

            if thumbnail_urls:
                # Téléchargement concurrent des thumbnails
                tasks = [_download_thumbnail(client, u) for u in thumbnail_urls]
                results = await asyncio.gather(*tasks)

                for thumb_bytes, match_url in zip(results, thumbnail_urls):
                    if not thumb_bytes:
                        continue
                    dist = await asyncio.to_thread(_phash_distance, image_bytes, thumb_bytes)
                    if dist is not None and dist <= _PHASH_EXACT_THRESHOLD:
                        exact_copy_urls.append(match_url)
                        logger.info(
                            "[originality] Copie exacte détectée (pHash dist=%d) : %s",
                            dist, match_url[:80],
                        )
            else:
                # Pas de thumbnails → impossible de vérifier → considère original
                logger.info("[originality] Aucun thumbnail disponible — logo considéré original")
                return True, []

            is_original = len(exact_copy_urls) <= max_similar
            logger.info(
                "[originality] Copies exactes=%d  seuil=%d  →  original=%s",
                len(exact_copy_urls), max_similar, is_original,
            )
            return is_original, exact_copy_urls

    except Exception as exc:
        logger.warning("[originality] Erreur inattendue : %s — ignoré", exc)
        return True, []
