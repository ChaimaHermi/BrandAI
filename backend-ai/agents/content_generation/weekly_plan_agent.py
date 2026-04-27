from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from agents.base_agent import BaseAgent, PipelineState
from agents.content_generation.content_llm_runner import ContentLLMRunner
from prompts.content_generation.prompt_weekly_plan import (
    WEEKLY_REGEN_SYSTEM,
    build_weekly_intent_system,
)
from tools.content_generation.cloudinary_upload import (
    cloudinary_configured,
    upload_image_bytes,
)
from tools.content_generation.content_image_client import fetch_content_image_hf_then_pollinations
from tools.content_generation.idea_fetch import fetch_idea_row, idea_to_content_context
from tools.content_generation.platform_specs import get_spec_for_platform

logger = logging.getLogger("brandai.weekly_plan_agent")
INTENT_LLM_TIMEOUT_SECONDS = 20

DAY_WORDS = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
    "dimanche": 6,
}

WEEKDAY_FR = {
    0: "lundi",
    1: "mardi",
    2: "mercredi",
    3: "jeudi",
    4: "vendredi",
    5: "samedi",
    6: "dimanche",
}

PLATFORM_HOURS = {
    "linkedin": (9, 30),
    "facebook": (13, 0),
    "instagram": (18, 30),
}

FR_MONTHS = {
    "janvier": 1,
    "fevrier": 2,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "aout": 8,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "decembre": 12,
    "décembre": 12,
}


class WeeklyIntentLLM(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            "weekly_intent_llm",
            temperature=0.2,
            llm_model="openai/gpt-oss-120b",
            llm_max_tokens=2048,
        )

    async def run(self, state: PipelineState) -> dict[str, Any]:
        return {}

    async def parse_intent(
        self,
        prompt: str,
        *,
        today_iso: str,
        today_weekday_fr: str,
        timezone: str,
    ) -> dict[str, Any]:
        system = build_weekly_intent_system(
            today_iso=today_iso,
            today_weekday_fr=today_weekday_fr,
            timezone=timezone,
        )
        raw = await self._call_llm(system, prompt.strip())
        return _parse_json_object(raw)

    async def regenerate_caption(
        self,
        *,
        current_caption: str,
        feedback: str,
        platform: str,
    ) -> str:
        user = (
            f"Plateforme: {platform}\n"
            f"Texte actuel:\n{current_caption}\n\n"
            f"Feedback utilisateur:\n{feedback}\n"
        )
        raw = await self._call_llm(WEEKLY_REGEN_SYSTEM, user)
        data = _parse_json_object(raw)
        caption = str(data.get("caption") or "").strip()
        if not caption:
            raise RuntimeError("Réponse de régénération invalide (caption vide).")
        return caption


@dataclass
class WeeklyGenerateInput:
    idea_id: int
    user_prompt: str
    platforms: list[str]
    timezone: str
    align_with_project: bool
    include_images: bool
    requested_post_count: int | None
    access_token: str | None
    distribution_mode: str | None = None


def _parse_json_object(raw: str) -> dict[str, Any]:
    s = (raw or "").strip()
    s = re.sub(r"```(?:json)?\s*|\s*```", "", s, flags=re.IGNORECASE).strip()
    try:
        data = json.loads(s)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start = s.find("{")
    end = s.rfind("}")
    if start >= 0 and end > start:
        data = json.loads(s[start : end + 1])
        if isinstance(data, dict):
            return data
    raise RuntimeError("Réponse JSON invalide du modèle.")


def _extract_post_count_fallback(prompt: str) -> int:
    text = (prompt or "").lower()
    m = re.search(r"\b([1-7])\s*post", text)
    if m:
        return int(m.group(1))
    if "une seule" in text or "un seul" in text:
        return 1
    if "deux" in text:
        return 2
    if "trois" in text:
        return 3
    return 3


def _next_monday(now: datetime) -> datetime:
    day_idx = now.weekday()
    delta = (7 - day_idx) % 7
    return (now + timedelta(days=delta)).replace(hour=0, minute=0, second=0, microsecond=0)


def _build_slots(
    *,
    count: int,
    platforms: list[str],
    user_prompt: str,
) -> list[tuple[str, datetime, str]]:
    now = datetime.now(UTC)
    base = _next_monday(now)
    mention_day = None
    lower = user_prompt.lower()
    for dword, idx in DAY_WORDS.items():
        if dword in lower:
            mention_day = idx
            break

    out: list[tuple[str, datetime, str]] = []
    for i in range(count):
        plat = platforms[i % len(platforms)]
        day_offset = i if mention_day is None else ((mention_day + i) % 7)
        hh, mm = PLATFORM_HOURS.get(plat, (10, 0))
        dt = base + timedelta(days=day_offset)
        dt = dt.replace(hour=hh, minute=mm)
        source = "ai_suggested"
        out.append((plat, dt, source))
    return out


def _next_weekday_from(now: datetime, weekday: int) -> datetime:
    delta = (weekday - now.weekday()) % 7
    if delta == 0:
        delta = 7
    return (now + timedelta(days=delta)).replace(hour=0, minute=0, second=0, microsecond=0)


def _extract_explicit_date(text: str, *, now: datetime | None = None) -> datetime | None:
    """Extrait une date explicite ou relative depuis du texte libre.

    Supporte :
    - ISO `YYYY-MM-DD`
    - `aujourd'hui`, `aujourd hui`, `today`
    - `demain`, `tomorrow`
    - `après-demain`, `apres-demain`, `apres demain`
    - `1er mai`, `1 mai`, `1 mai 2026`
    - `dd/mm`, `dd/mm/yyyy`, `dd-mm`, `dd-mm-yyyy`
    """
    if not text:
        return None
    base_now = (now or datetime.now(UTC)).replace(hour=0, minute=0, second=0, microsecond=0)
    lower = text.lower().strip()

    iso = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", lower)
    if iso:
        try:
            return datetime(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)), tzinfo=UTC)
        except ValueError:
            return None

    if re.search(r"\baujourd['\s]?hui\b|\btoday\b", lower):
        return base_now
    if re.search(r"\bapr[eè]s[\s-]demain\b", lower):
        return base_now + timedelta(days=2)
    if re.search(r"\bdemain\b|\btomorrow\b", lower):
        return base_now + timedelta(days=1)

    m = re.search(
        r"\b(\d{1,2})(?:er)?\s+(janvier|fevrier|février|mars|avril|mai|juin|juillet|aout|août|septembre|octobre|novembre|decembre|décembre)(?:\s+(\d{4}))?\b",
        lower,
    )
    if m:
        day = int(m.group(1))
        month = FR_MONTHS.get(m.group(2), 0)
        year = int(m.group(3)) if m.group(3) else base_now.year
        if month:
            try:
                dt = datetime(year, month, day, tzinfo=UTC)
                if not m.group(3) and dt.date() < base_now.date():
                    dt = dt.replace(year=year + 1)
                return dt
            except ValueError:
                return None

    m2 = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{4}))?\b", lower)
    if m2:
        day = int(m2.group(1))
        month = int(m2.group(2))
        year = int(m2.group(3)) if m2.group(3) else base_now.year
        try:
            dt = datetime(year, month, day, tzinfo=UTC)
            if not m2.group(3) and dt.date() < base_now.date():
                dt = dt.replace(year=year + 1)
            return dt
        except ValueError:
            return None
    return None


def _parse_hhmm(text: str | None) -> tuple[int, int] | None:
    if not text:
        return None
    m = re.search(r"\b(\d{1,2})\s*[:hH]\s*(\d{2})?\b", text)
    if not m:
        return None
    try:
        hh = int(m.group(1))
        mm = int(m.group(2)) if m.group(2) else 0
    except ValueError:
        return None
    if 0 <= hh <= 23 and 0 <= mm <= 59:
        return hh, mm
    return None


def _slot_for_post(
    *,
    idx: int,
    platform: str,
    user_prompt: str,
    post_day_hint: str | None,
    post_date_hint: str | None,
    scheduled_date_iso: str | None = None,
    scheduled_time: str | None = None,
) -> tuple[datetime, str]:
    """Détermine la date+heure proposée pour une variante.

    Priorité :
    1. `scheduled_date_iso` (déjà résolu par le LLM) + `scheduled_time` éventuel.
    2. Détection explicite dans `post_date_hint` puis `user_prompt`.
    3. Détection d'un jour de la semaine (`post_day_hint` ou prompt).
    4. Lundi prochain par défaut.
    """
    now = datetime.now(UTC)
    default_hh, default_mm = PLATFORM_HOURS.get(platform, (10, 0))
    hhmm = _parse_hhmm(scheduled_time)
    hh = hhmm[0] if hhmm else default_hh
    mm = hhmm[1] if hhmm else default_mm
    time_source_user = bool(hhmm)

    if scheduled_date_iso:
        try:
            base = datetime.fromisoformat(scheduled_date_iso)
            if base.tzinfo is None:
                base = base.replace(tzinfo=UTC)
            dt = base.replace(hour=hh, minute=mm, second=0, microsecond=0)
            if dt < now.replace(second=0, microsecond=0):
                dt = dt + timedelta(days=7)
            return dt, ("user_date+user_time" if time_source_user else "user_date+ai_time")
        except (ValueError, TypeError):
            pass

    explicit = _extract_explicit_date(post_date_hint or "", now=now) or _extract_explicit_date(
        user_prompt, now=now
    )
    if explicit:
        dt = (explicit + timedelta(days=idx)).replace(hour=hh, minute=mm)
        if dt < now:
            dt = dt.replace(year=now.year + 1)
        return dt, ("user_date+user_time" if time_source_user else "user_date+ai_time")

    hint = (post_day_hint or "").strip().lower()
    if not hint:
        lower = user_prompt.lower()
        for dword in DAY_WORDS:
            if dword in lower:
                hint = dword
                break
    if hint in DAY_WORDS:
        base = _next_weekday_from(now, DAY_WORDS[hint])
        dt = (base + timedelta(days=idx)).replace(hour=hh, minute=mm)
        return dt, ("user_day+user_time" if time_source_user else "user_day+ai_time")

    base = _next_monday(now)
    dt = (base + timedelta(days=idx)).replace(hour=hh, minute=mm)
    return dt, ("ai_suggested+user_time" if time_source_user else "ai_suggested")


async def _generate_item_caption(
    *,
    runner: ContentLLMRunner,
    idea_id: int,
    platform: str,
    goal: str,
    user_prompt: str,
    align_with_project: bool,
    access_token: str | None,
) -> str:
    brief = {
        "subject": goal,
        "tone": "professional",
        "content_type": "feed_post",
        "hashtags": platform == "instagram",
        "include_image": True,
        "call_to_action": "learn_more" if platform in ("facebook", "linkedin") else None,
        "align_with_project": align_with_project,
        "weekly_user_prompt": user_prompt,
    }
    idea_block: dict[str, Any] = {}
    if align_with_project and access_token:
        try:
            row = await fetch_idea_row(idea_id, access_token)
            idea_block = idea_to_content_context(row)
        except Exception as exc:
            logger.warning("[weekly_plan] contexte idée indisponible: %s", exc)

    merged = {
        "idea_id": idea_id,
        "platform": platform,
        "brief": brief,
        "align_with_project": align_with_project,
        "idea": idea_block,
    }
    spec = get_spec_for_platform(platform)
    return await runner.draft_post(
        json.dumps(merged, ensure_ascii=False, indent=2),
        json.dumps(spec, ensure_ascii=False, indent=2),
    )


async def _generate_item_image(
    *,
    runner: ContentLLMRunner,
    merged: dict[str, Any],
    platform: str,
    caption: str,
) -> tuple[str | None, str | None]:
    if not cloudinary_configured():
        return None, "cloudinary_not_configured"
    try:
        spec = get_spec_for_platform(platform)
        ip, np = await runner.build_image_prompt(
            json.dumps(merged, ensure_ascii=False, indent=2),
            json.dumps(spec, ensure_ascii=False, indent=2),
            caption,
        )
        data, mime, _ = await fetch_content_image_hf_then_pollinations(ip, np)
        url = upload_image_bytes(data, mime=mime)
        return url, None
    except Exception as exc:
        return None, str(exc)[:220]


async def generate_weekly_plan(payload: WeeklyGenerateInput) -> dict[str, Any]:
    intent_llm = WeeklyIntentLLM()

    now = datetime.now(UTC)
    today_iso = now.date().isoformat()
    today_weekday_fr = WEEKDAY_FR.get(now.weekday(), "")

    intent: dict[str, Any] = {}
    try:
        intent = await asyncio.wait_for(
            intent_llm.parse_intent(
                payload.user_prompt,
                today_iso=today_iso,
                today_weekday_fr=today_weekday_fr,
                timezone=payload.timezone or "UTC",
            ),
            timeout=INTENT_LLM_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        logger.warning(
            "[weekly_plan] parse_intent timeout after %ss, fallback parsing used",
            INTENT_LLM_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        logger.warning("[weekly_plan] fallback parsing used: %s", exc)

    requested = payload.requested_post_count
    count = requested if requested is not None else int(intent.get("post_count") or 0)
    if count < 1:
        count = _extract_post_count_fallback(payload.user_prompt)
    count = max(1, min(7, count))

    parsed_posts = intent.get("posts") if isinstance(intent.get("posts"), list) else []
    normalized_posts: list[dict[str, Any]] = []
    for p in parsed_posts:
        if not isinstance(p, dict):
            continue
        objective = str(p.get("objective") or "").strip()
        if not objective:
            continue
        rec = p.get("recommended_platforms") or []
        rec = [x for x in rec if x in payload.platforms]
        if not rec:
            rec = payload.platforms[:]
        normalized_posts.append(
            {
                "objective": objective,
                "recommended_platforms": rec[:3],
                "scheduled_date": str(p.get("scheduled_date") or "").strip() or None,
                "scheduled_time": str(p.get("scheduled_time") or "").strip() or None,
                "date_hint": str(p.get("date_hint") or "").strip() or None,
                "day_hint": str(p.get("day_hint") or "").strip() or None,
            }
        )
    if not normalized_posts:
        normalized_posts = [
            {
                "objective": f"Post {i + 1}: {payload.user_prompt.strip()}",
                "recommended_platforms": payload.platforms[:],
                "scheduled_date": None,
                "scheduled_time": None,
                "date_hint": None,
                "day_hint": None,
            }
            for i in range(count)
        ]
    while len(normalized_posts) < count:
        normalized_posts.append(dict(normalized_posts[-1]))
    normalized_posts = normalized_posts[:count]

    items = []
    for idx, post in enumerate(normalized_posts):
        objective = post["objective"]
        rec_platforms = post["recommended_platforms"]

        variants = []
        for platform in rec_platforms:
            slot_dt, timing_source = _slot_for_post(
                idx=idx,
                platform=platform,
                user_prompt=payload.user_prompt,
                post_day_hint=post.get("day_hint"),
                post_date_hint=post.get("date_hint"),
                scheduled_date_iso=post.get("scheduled_date"),
                scheduled_time=post.get("scheduled_time"),
            )
            # Cost-aware UX: weekly generate returns only scheduling proposals.
            # Caption/image generation is deferred to approval time.
            variants.append(
                {
                    "variant_id": f"wp-{idx+1}-{platform}",
                    "platform": platform,
                    "caption": "",
                    "scheduled_at_utc": slot_dt.isoformat(),
                    "timing_source": timing_source,
                    "status": "suggested",
                    "image_mode": "required" if payload.include_images else "none",
                    "image_status": "pending" if payload.include_images else "skipped",
                    "image_url": None,
                    "image_error": None,
                    "content_generated": False,
                }
            )
        items.append(
            {
                "item_id": f"wp-{idx+1}",
                "objective": objective,
                "recommended_platforms": rec_platforms,
                "status": "proposed",
                "scheduled_date": post.get("scheduled_date"),
                "scheduled_time": post.get("scheduled_time"),
                "date_hint": post.get("date_hint"),
                "day_hint": post.get("day_hint"),
                "variants": variants,
            }
        )

    return {
        "plan_id": f"plan-{payload.idea_id}-{int(datetime.now(UTC).timestamp())}",
        "detected_post_count": count,
        "timezone": payload.timezone,
        "align_with_project": payload.align_with_project,
        "notes": intent.get("notes") or [],
        "items": items,
    }


async def regenerate_weekly_item(
    *,
    item: dict[str, Any],
    feedback: str,
) -> dict[str, Any]:
    llm = WeeklyIntentLLM()
    caption = await llm.regenerate_caption(
        current_caption=str(item.get("caption") or ""),
        feedback=feedback,
        platform=str(item.get("platform") or "linkedin"),
    )
    next_item = dict(item)
    next_item["caption"] = caption
    next_item["status"] = "regenerated"
    next_item["content_generated"] = True
    return next_item


async def generate_weekly_content_for_items(
    *,
    idea_id: int,
    access_token: str | None,
    align_with_project: bool,
    include_images: bool,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    runner = ContentLLMRunner()
    updated_items: list[dict[str, Any]] = []

    for item in items:
        objective = str(item.get("objective") or "Post semaine").strip()
        variants = item.get("variants") if isinstance(item.get("variants"), list) else []
        new_variants = []
        for variant in variants:
            if variant.get("status") == "removed_by_user":
                new_variants.append(dict(variant))
                continue
            platform = str(variant.get("platform") or "linkedin")
            caption = str(variant.get("caption") or "").strip()
            if not caption:
                caption = await _generate_item_caption(
                    runner=runner,
                    idea_id=idea_id,
                    platform=platform,
                    goal=objective,
                    user_prompt=objective,
                    align_with_project=align_with_project,
                    access_token=access_token,
                )

            image_url = variant.get("image_url")
            image_mode = str(variant.get("image_mode") or "none")
            image_status = variant.get("image_status")
            image_error = variant.get("image_error")
            if include_images and image_mode != "none" and not image_url:
                merged_for_img = {
                    "idea_id": idea_id,
                    "platform": platform,
                    "brief": {"subject": objective, "include_image": True},
                    "idea": {},
                }
                img_url, img_err = await _generate_item_image(
                    runner=runner,
                    merged=merged_for_img,
                    platform=platform,
                    caption=caption,
                )
                image_url = img_url
                image_error = img_err
                image_status = "generated" if img_url else ("failed" if img_err else image_status)

            next_variant = dict(variant)
            next_variant["caption"] = caption
            next_variant["image_url"] = image_url
            next_variant["image_error"] = image_error
            next_variant["image_status"] = image_status or ("generated" if image_url else "skipped")
            next_variant["content_generated"] = True
            if next_variant.get("status") == "suggested":
                next_variant["status"] = "generated"
            new_variants.append(next_variant)

        next_item = dict(item)
        next_item["variants"] = new_variants
        if next_item.get("status") == "proposed":
            next_item["status"] = "content_generated"
        updated_items.append(next_item)

    return {"items": updated_items}


async def approve_weekly_plan(
    *,
    idea_id: int,
    access_token: str,
    timezone_name: str,
    items: list[dict[str, Any]],
    align_with_project: bool = True,
) -> dict[str, Any]:
    base = "http://localhost:8000/api"
    base = __import__("os").getenv("BACKEND_API_BASE_URL", base).rstrip("/")
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    created = []
    runner = ContentLLMRunner()
    async with httpx.AsyncClient(timeout=httpx.Timeout(40.0, connect=5.0)) as client:
        for item in items:
            variants = item.get("variants")
            if isinstance(variants, list) and variants:
                source_rows = variants
                objective = item.get("objective")
            else:
                source_rows = [item]
                objective = item.get("objective")

            for row in source_rows:
                if row.get("status") == "removed_by_user":
                    continue
                platform = str(row.get("platform") or "")
                objective = str(item.get("objective") or "Post semaine").strip()
                caption = str(row.get("caption") or "").strip()

                # Generate content lazily on approval (cost control)
                if not caption:
                    caption = await _generate_item_caption(
                        runner=runner,
                        idea_id=idea_id,
                        platform=platform,
                        goal=objective,
                        user_prompt=objective,
                        align_with_project=align_with_project,
                        access_token=access_token,
                    )

                image_url = row.get("image_url")
                image_mode = str(row.get("image_mode") or "none")
                if image_mode != "none" and not image_url:
                    merged_for_img = {
                        "idea_id": idea_id,
                        "platform": platform,
                        "brief": {"subject": objective, "include_image": True},
                        "idea": {},
                    }
                    img_url, _img_err = await _generate_item_image(
                        runner=runner,
                        merged=merged_for_img,
                        platform=platform,
                        caption=caption,
                    )
                    image_url = img_url

                gc_payload = {
                    "platform": platform,
                    "caption": caption,
                    "image_url": image_url,
                    "char_count": len(caption or ""),
                }
                gc_resp = await client.post(
                    f"{base}/ideas/{idea_id}/generated-contents",
                    headers=headers,
                    json=gc_payload,
                )
                gc_resp.raise_for_status()
                gc = gc_resp.json()

                sp_payload = {
                    "generated_content_id": gc["id"],
                    "scheduled_at": row["scheduled_at_utc"],
                    "timezone": timezone_name or "UTC",
                    "title": (objective or "")[:255] or None,
                }
                sp_resp = await client.post(
                    f"{base}/ideas/{idea_id}/scheduled-publications",
                    headers=headers,
                    json=sp_payload,
                )
                sp_resp.raise_for_status()
                sp = sp_resp.json()
                created.append({"generated_content_id": gc["id"], "schedule_id": sp["id"]})

    return {"created_count": len(created), "items": created}
