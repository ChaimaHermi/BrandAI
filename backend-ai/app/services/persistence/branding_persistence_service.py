from __future__ import annotations

import os
from datetime import datetime

import httpx

from app.branding_payload import split_brand_identity_payload


async def fetch_branding_merged_generated(
    idea_id: int,
    access_token: str,
) -> dict:
    """Merge generated fields from naming/slogan/palette/logo rows."""
    base = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")
    headers = {"Authorization": f"Bearer {access_token}"}
    merged: dict = {}
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        for path in ("naming", "slogan", "palette", "logo"):
            r = await client.get(
                f"{base}/branding/ideas/{idea_id}/{path}",
                headers=headers,
            )
            if r.status_code != 200:
                continue
            row = r.json()
            g = row.get("generated")
            if isinstance(g, dict):
                merged.update(g)
    return merged


async def persist_brand_identity_row(
    *,
    idea_id: int,
    brand_identity: dict,
    access_token: str,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
) -> dict:
    """
    Compatibility helper for branding service.
    started_at/completed_at are accepted for API compatibility with old callers.
    """
    await persist_branding_results_tables(
        idea_id=idea_id,
        brand_identity=brand_identity,
        access_token=access_token,
    )
    return {"ok": True, "idea_id": idea_id}


async def persist_branding_results_tables(
    *,
    idea_id: int,
    brand_identity: dict,
    access_token: str,
) -> None:
    """PATCH backend-api /branding/ideas/{id}/... per table."""
    meta, names, slogans, logo = split_brand_identity_payload(brand_identity)
    base = os.getenv("BACKEND_API_BASE_URL", "http://localhost:8000/api").rstrip("/")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    naming_generated: dict = {**(meta or {}), **(names or {})}
    slogan_generated: dict = dict(slogans or {})
    palette_generated: dict = {}
    logo_generated: dict = {}
    if logo:
        for k in ("palette_options", "color_palette", "palette_error"):
            if k in logo:
                palette_generated[k] = logo[k]
        if "logo_concepts" in logo:
            logo_generated["logo_concepts"] = logo["logo_concepts"]

    timeout = httpx.Timeout(45.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        if naming_generated:
            r = await client.patch(
                f"{base}/branding/ideas/{idea_id}/naming",
                json={"status": "completed", "generated": naming_generated},
                headers=headers,
            )
            r.raise_for_status()
        if slogan_generated:
            r = await client.patch(
                f"{base}/branding/ideas/{idea_id}/slogan",
                json={"status": "completed", "generated": slogan_generated},
                headers=headers,
            )
            r.raise_for_status()
        if palette_generated:
            r = await client.patch(
                f"{base}/branding/ideas/{idea_id}/palette",
                json={"status": "completed", "generated": palette_generated},
                headers=headers,
            )
            r.raise_for_status()
        if logo_generated:
            r = await client.patch(
                f"{base}/branding/ideas/{idea_id}/logo",
                json={"status": "completed", "generated": logo_generated},
                headers=headers,
            )
            r.raise_for_status()
