from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone as dt_timezone
from typing import Any

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore[no-redef]

import httpx

from agents.base_agent import PipelineState
from agents.content_generation.content_azure_llm import ContentTextLLMBase
from agents.content_generation.content_llm_runner import ContentLLMRunner
from observability.langsmith_tracing import agent_trace
from prompts.content_generation.prompt_weekly_plan import (
    WEEKLY_REGEN_SYSTEM,
    build_weekly_intent_system,
)
from tools.content_generation.cloudinary_upload import (
    cloudinary_configured,
    upload_image_bytes,
)
from tools.content_generation.content_image_client import fetch_content_image
from tools.content_generation.idea_fetch import (
    fetch_idea_row,
    idea_to_content_context,
    idea_to_planning_context,
)
from config.content_generation_config import content_http_timeout
from tools.content_generation.platform_specs import get_spec_for_platform

logger = logging.getLogger("brandai.weekly_plan_agent")

WEEKDAY_FR = {
    0: "lundi",
    1: "mardi",
    2: "mercredi",
    3: "jeudi",
    4: "vendredi",
    5: "samedi",
    6: "dimanche",
}

class WeeklyIntentLLM(ContentTextLLMBase):
    def __init__(self) -> None:
        max_retries = 3
        raw = (os.getenv("CONTENT_AZURE_MAX_RETRIES") or os.getenv("AZURE_MAX_RETRIES") or "").strip()
        if raw.isdigit():
            max_retries = max(1, int(raw))
        super().__init__(
            "weekly_intent_llm",
            temperature=0.2,
            llm_max_tokens=2048,
            max_retries=max_retries,
        )

    async def parse_intent(
        self,
        user_message: str,
        *,
        today_iso: str,
        today_weekday_fr: str,
        timezone: str,
        now_local_hhmm: str,
        allowed_platforms: list[str],
    ) -> dict[str, Any]:
        allowed = ", ".join(allowed_platforms) if allowed_platforms else "linkedin, facebook, instagram"
        system = build_weekly_intent_system(
            today_iso=today_iso,
            today_weekday_fr=today_weekday_fr,
            timezone=timezone,
            now_local_hhmm=now_local_hhmm,
            allowed_platforms=allowed,
        )
        raw = await self._call_llm(system, user_message.strip())
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


_TZ_OFFSET_FALLBACKS: dict[str, timedelta] = {
    "Africa/Tunis": timedelta(hours=1),
    "Europe/Paris": timedelta(hours=1),
    "Europe/Brussels": timedelta(hours=1),
    "Europe/Berlin": timedelta(hours=1),
}


def _resolve_tz(timezone_name: str):
    """Retourne ZoneInfo ou datetime.timezone (fallback Windows sans tzdata)."""
    name = (timezone_name or "UTC").strip()
    if name in ("UTC", "Etc/UTC", "GMT", "Zulu"):
        return dt_timezone.utc
    try:
        return ZoneInfo(name)
    except Exception:
        offset = _TZ_OFFSET_FALLBACKS.get(name)
        if offset is not None:
            logger.warning(
                "[weekly_plan] fuseau %s via offset fixe %s (installez tzdata pour l'heure d'ete)",
                name,
                offset,
            )
            return dt_timezone(offset)
        logger.warning("[weekly_plan] fuseau %s inconnu, fallback UTC", name)
        return dt_timezone.utc


def _user_now(timezone_name: str) -> datetime:
    return datetime.now(_resolve_tz(timezone_name))


def _utc_from_local_date_time(
    year: int,
    month: int,
    day: int,
    hh: int,
    mm: int,
    timezone_name: str,
) -> datetime:
    """Interprète date+heure dans le fuseau utilisateur, retourne UTC."""
    tz = _resolve_tz(timezone_name)
    local = datetime(year, month, day, hh, mm, 0, 0, tzinfo=tz)
    return local.astimezone(UTC)


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


def _normalize_platform_rationale(raw: Any, platforms: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    if not isinstance(raw, dict):
        return out
    for plat in platforms:
        v = raw.get(plat)
        if isinstance(v, str) and v.strip():
            out[plat] = v.strip()
    return out


def _build_planning_user_message(
    *,
    user_prompt: str,
    project_context: dict[str, Any] | None,
    align_with_project: bool,
) -> str:
    parts = []
    if align_with_project and project_context:
        parts.append(
            "Contexte projet (données réelles API — ne rien inventer hors de ce bloc) :\n"
            + json.dumps(project_context, ensure_ascii=False, indent=2)
        )
    elif align_with_project:
        parts.append(
            "Contexte projet : indisponible (token ou API). Raisonne uniquement sur l'intention ci-dessous."
        )
    parts.append("Intention utilisateur (planification) :\n" + user_prompt.strip())
    return "\n\n".join(parts)


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
    platform: str,
    platform_time: str,
    user_specified_time: bool,
    scheduled_date_iso: str | None,
    timezone_name: str = "UTC",
    post_objective: str = "",
) -> tuple[datetime, str]:
    """Convertit la date/heure proposées par le LLM (fuseau utilisateur) en UTC."""
    if not scheduled_date_iso:
        raise RuntimeError(
            f"Le planificateur n'a pas fourni scheduled_date pour le post « {post_objective[:60]} »."
        )
    hhmm = _parse_hhmm(platform_time)
    if not hhmm:
        raise RuntimeError(
            f"Heure invalide pour {platform} sur « {post_objective[:60]} » : '{platform_time}'"
        )
    hh, mm = hhmm
    try:
        parts = scheduled_date_iso.strip().split("-")
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    except (ValueError, TypeError, IndexError) as exc:
        raise RuntimeError(
            f"scheduled_date invalide pour « {post_objective[:60]} » : {scheduled_date_iso!r}"
        ) from exc
    dt_utc = _utc_from_local_date_time(y, m, d, hh, mm, timezone_name)
    label = "user_time" if user_specified_time else "llm_time"
    return dt_utc, f"llm_schedule+{label}"


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


async def _build_merged_for_image(
    *,
    idea_id: int,
    platform: str,
    objective: str,
    align_with_project: bool,
    access_token: str | None,
) -> dict[str, Any]:
    brief = {
        "subject": objective,
        "tone": "professional",
        "content_type": "feed_post",
        "hashtags": platform == "instagram",
        "include_image": True,
        "call_to_action": "learn_more" if platform in ("facebook", "linkedin") else None,
        "align_with_project": align_with_project,
    }
    idea_block: dict[str, Any] = {}
    if align_with_project and access_token:
        try:
            row = await fetch_idea_row(idea_id, access_token)
            idea_block = idea_to_content_context(row)
        except Exception as exc:
            logger.warning("[weekly_plan] contexte idée image indisponible: %s", exc)
    return {
        "idea_id": idea_id,
        "platform": platform,
        "brief": brief,
        "align_with_project": align_with_project,
        "idea": idea_block,
    }


def _image_gen_max_attempts() -> int:
    raw = (os.getenv("CONTENT_IMAGE_GEN_ATTEMPTS") or "3").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 3


def _image_gen_retry_delay_s(attempt: int) -> float:
    base = float(os.getenv("CONTENT_IMAGE_GEN_RETRY_DELAY_S") or "30")
    return base * max(1, attempt + 1)


def _is_retryable_image_error(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code if exc.response is not None else 0
        return status in (429, 502, 503, 504)
    msg = str(exc).lower()
    return any(
        token in msg
        for token in ("504", "502", "503", "429", "gateway timeout", "gateway time-out")
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

    max_attempts = _image_gen_max_attempts()
    last_err: str | None = None
    for attempt in range(max_attempts):
        try:
            spec = get_spec_for_platform(platform)
            ip, np = await runner.build_image_prompt(
                json.dumps(merged, ensure_ascii=False, indent=2),
                json.dumps(spec, ensure_ascii=False, indent=2),
                caption,
            )
            data, mime, _ = await fetch_content_image(ip, np)
            url = upload_image_bytes(data, mime=mime)
            if attempt > 0:
                logger.info(
                    "[weekly_plan] image OK apres %d tentative(s) | platform=%s",
                    attempt + 1,
                    platform,
                )
            return url, None
        except Exception as exc:
            last_err = str(exc)[:220]
            if _is_retryable_image_error(exc) and attempt < max_attempts - 1:
                delay = _image_gen_retry_delay_s(attempt)
                logger.warning(
                    "[weekly_plan] image retry %d/%d dans %.0fs | platform=%s | %s",
                    attempt + 1,
                    max_attempts,
                    delay,
                    platform,
                    last_err[:120],
                )
                await asyncio.sleep(delay)
                continue
            return None, last_err
    return None, last_err or "image_generation_failed"


@agent_trace("weekly_plan.generate", tags=["content_generation", "weekly_plan"])
async def generate_weekly_plan(payload: WeeklyGenerateInput) -> dict[str, Any]:
    intent_llm = WeeklyIntentLLM()

    tz_name = (payload.timezone or "UTC").strip()
    user_now = _user_now(tz_name)
    today_iso = user_now.date().isoformat()
    today_weekday_fr = WEEKDAY_FR.get(user_now.weekday(), "")
    now_local_hhmm = user_now.strftime("%H:%M")
    allowed = [p for p in (payload.platforms or []) if p in ("linkedin", "facebook", "instagram")]
    if not allowed:
        allowed = ["linkedin", "facebook", "instagram"]

    project_context: dict[str, Any] | None = None
    if payload.align_with_project and payload.access_token:
        try:
            row = await fetch_idea_row(payload.idea_id, payload.access_token)
            project_context = idea_to_planning_context(row)
        except Exception as exc:
            logger.warning("[weekly_plan] contexte projet indisponible: %s", exc)

    user_message = _build_planning_user_message(
        user_prompt=payload.user_prompt,
        project_context=project_context,
        align_with_project=payload.align_with_project,
    )

    try:
        intent = await intent_llm.parse_intent(
            user_message,
            today_iso=today_iso,
            today_weekday_fr=today_weekday_fr,
            timezone=tz_name,
            now_local_hhmm=now_local_hhmm,
            allowed_platforms=allowed,
        )
    except Exception as exc:
        raise RuntimeError(f"Le planificateur LLM a échoué : {exc}") from exc

    if not isinstance(intent, dict):
        raise RuntimeError("Le planificateur LLM a renvoyé une réponse invalide.")

    plan_notes: list[str] = []
    if isinstance(intent.get("notes"), list):
        plan_notes.extend(str(n) for n in intent["notes"] if n)

    parsed_posts = intent.get("posts") if isinstance(intent.get("posts"), list) else []
    normalized_posts: list[dict[str, Any]] = []
    for p in parsed_posts:
        if not isinstance(p, dict):
            continue
        objective = str(p.get("objective") or "").strip()
        if not objective:
            continue

        content_type = str(p.get("content_type") or "other").strip() or "other"
        rec = [x for x in (p.get("recommended_platforms") or []) if x in allowed]
        if not rec:
            raise RuntimeError(
                f"Le planificateur n'a proposé aucune plateforme valide pour « {objective[:60]} »."
            )
        rec = rec[:3]
        rationale = _normalize_platform_rationale(p.get("platform_rationale"), rec)

        post_user_time = (
            p.get("user_time_specified") is True
            if isinstance(p.get("user_time_specified"), bool)
            else False
        )
        scheduled_date = str(p.get("scheduled_date") or "").strip()
        if not scheduled_date:
            raise RuntimeError(
                f"Le planificateur n'a pas fourni scheduled_date pour « {objective[:60]} »."
            )

        plat_times_raw = p.get("platform_times")
        if not isinstance(plat_times_raw, dict):
            raise RuntimeError(
                f"Le planificateur LLM n'a pas proposé `platform_times` pour le post « {objective[:60]} »."
            )
        plat_times: dict[str, str] = {}
        fallback_time = None
        for _plat, _t in plat_times_raw.items():
            if isinstance(_t, str) and _parse_hhmm(_t):
                fallback_time = _t
                break
        for plat in rec:
            t = plat_times_raw.get(plat) or fallback_time
            if not isinstance(t, str) or not _parse_hhmm(t):
                raise RuntimeError(
                    f"Le planificateur LLM n'a pas proposé d'heure valide pour {plat} sur le post « {objective[:60]} »."
                )
            plat_times[plat] = t

        plat_images_raw = p.get("platform_images")
        if not isinstance(plat_images_raw, dict):
            raise RuntimeError(
                f"Le planificateur LLM n'a pas proposé `platform_images` pour le post « {objective[:60]} »."
            )
        plat_images: dict[str, bool] = {}
        for plat in rec:
            v = plat_images_raw.get(plat)
            if not isinstance(v, bool):
                raise RuntimeError(
                    f"Le planificateur LLM n'a pas proposé d'image (bool) pour {plat} sur le post « {objective[:60]} »."
                )
            plat_images[plat] = v
        # Master kill switch : si l'utilisateur a globalement désactivé les images,
        # on force false sur LinkedIn et Facebook. Instagram reste à true (règle
        # non négociable : Instagram sans image n'a aucun sens).
        if not payload.include_images:
            plat_images = {k: False for k in plat_images}

        normalized_posts.append(
            {
                "objective": objective,
                "content_type": content_type,
                "recommended_platforms": rec,
                "platform_rationale": rationale,
                "user_time_specified": post_user_time,
                "scheduled_date": scheduled_date,
                "platform_times": plat_times,
                "platform_images": plat_images,
                "date_hint": str(p.get("date_hint") or "").strip() or None,
                "day_hint": str(p.get("day_hint") or "").strip() or None,
            }
        )

    if not normalized_posts:
        raise RuntimeError(
            "Le planificateur LLM n'a proposé aucun post exploitable. Reformule l'intention."
        )

    # Le nombre de posts effectif suit l'intention du LLM (qui suit l'utilisateur).
    # Si l'utilisateur force `requested_post_count`, on tronque ou complète,
    # sinon on garde TOUT ce que le LLM a proposé.
    requested = payload.requested_post_count
    if isinstance(requested, int) and requested > 0:
        target = max(1, min(7, requested))
        while len(normalized_posts) < target:
            normalized_posts.append(dict(normalized_posts[-1]))
        normalized_posts = normalized_posts[:target]
    count = len(normalized_posts)

    items = []
    for idx, post in enumerate(normalized_posts):
        objective = post["objective"]
        rec_platforms = post["recommended_platforms"]
        plat_times = post["platform_times"]
        plat_images = post["platform_images"]

        variants = []
        for platform in rec_platforms:
            slot_dt, timing_source = _slot_for_post(
                platform=platform,
                platform_time=plat_times[platform],
                user_specified_time=bool(post.get("user_time_specified")),
                scheduled_date_iso=post.get("scheduled_date"),
                timezone_name=tz_name,
                post_objective=objective,
            )
            want_image = bool(plat_images.get(platform, False))
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
                    "image_mode": "required" if want_image else "none",
                    "image_status": "pending" if want_image else "skipped",
                    "image_url": None,
                    "image_error": None,
                    "content_generated": False,
                }
            )
        items.append(
            {
                "item_id": f"wp-{idx+1}",
                "objective": objective,
                "content_type": post.get("content_type"),
                "recommended_platforms": rec_platforms,
                "platform_rationale": post.get("platform_rationale") or {},
                "status": "proposed",
                "scheduled_date": post.get("scheduled_date"),
                "platform_times": post.get("platform_times"),
                "platform_images": post.get("platform_images"),
                "date_hint": post.get("date_hint"),
                "day_hint": post.get("day_hint"),
                "user_time_specified": post.get("user_time_specified"),
                "variants": variants,
            }
        )

    return {
        "plan_id": f"plan-{payload.idea_id}-{int(datetime.now(UTC).timestamp())}",
        "detected_post_count": count,
        "timezone": payload.timezone,
        "align_with_project": payload.align_with_project,
        "project_context_used": bool(project_context),
        "notes": plan_notes,
        "items": items,
    }


@agent_trace("weekly_plan.regenerate_item", tags=["content_generation", "weekly_plan"])
async def regenerate_weekly_item(
    *,
    item: dict[str, Any],
    feedback: str,
    idea_id: int,
    access_token: str | None = None,
    align_with_project: bool = True,
) -> dict[str, Any]:
    """Régénère la légende puis l'image si le variant est en mode visuel."""
    llm = WeeklyIntentLLM()
    runner = ContentLLMRunner()
    platform = str(item.get("platform") or "linkedin")
    objective = str(item.get("objective") or "Post semaine").strip()

    caption = await llm.regenerate_caption(
        current_caption=str(item.get("caption") or ""),
        feedback=feedback,
        platform=platform,
    )
    next_item = dict(item)
    next_item["caption"] = caption

    image_mode = str(item.get("image_mode") or "none")
    if platform == "instagram":
        image_mode = "required"

    if image_mode != "none":
        logger.info(
            "[weekly_plan] regenerate image | variant=%s platform=%s",
            item.get("variant_id"),
            platform,
        )
        merged = await _build_merged_for_image(
            idea_id=idea_id,
            platform=platform,
            objective=objective,
            align_with_project=align_with_project,
            access_token=access_token,
        )
        img_url, img_err = await _generate_item_image(
            runner=runner,
            merged=merged,
            platform=platform,
            caption=caption,
        )
        next_item["image_url"] = img_url
        next_item["image_error"] = img_err
        if img_url:
            next_item["image_status"] = "generated"
        elif img_err:
            next_item["image_status"] = "failed"
    else:
        next_item["image_status"] = "skipped"

    next_item["status"] = "regenerated"
    next_item["content_generated"] = True
    return next_item


@agent_trace("weekly_plan.retry_image", tags=["content_generation", "weekly_plan"])
async def retry_weekly_variant_image(
    *,
    variant: dict[str, Any],
    objective: str,
    idea_id: int,
    access_token: str | None = None,
    align_with_project: bool = True,
) -> dict[str, Any]:
    """Regenere uniquement l'image (caption conservee)."""
    runner = ContentLLMRunner()
    platform = str(variant.get("platform") or "linkedin")
    caption = str(variant.get("caption") or "").strip()
    if not caption:
        raise ValueError("Caption manquante : impossible de regenerer l'image.")

    image_mode = str(variant.get("image_mode") or "none")
    if platform == "instagram":
        image_mode = "required"
    if image_mode == "none":
        raise ValueError("Ce variant est configure sans image.")

    logger.info(
        "[weekly_plan] retry image | variant=%s platform=%s",
        variant.get("variant_id"),
        platform,
    )
    merged = await _build_merged_for_image(
        idea_id=idea_id,
        platform=platform,
        objective=objective.strip() or "Post semaine",
        align_with_project=align_with_project,
        access_token=access_token,
    )
    next_variant = dict(variant)
    next_variant["image_error"] = None
    next_variant["image_status"] = "pending"
    img_url, img_err = await _generate_item_image(
        runner=runner,
        merged=merged,
        platform=platform,
        caption=caption,
    )
    next_variant["image_url"] = img_url
    next_variant["image_error"] = img_err
    if img_url:
        next_variant["image_status"] = "generated"
    elif img_err:
        next_variant["image_status"] = "failed"
    return next_variant


@agent_trace("weekly_plan.generate_content", tags=["content_generation", "weekly_plan"])
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
    logger.info(
        "[weekly_content] start | include_images=%s | items=%d",
        include_images,
        len(items),
    )

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
            # Garde-fou serveur : Instagram doit TOUJOURS avoir une image.
            # Si le frontend a envoyé image_mode="none" pour une variante Instagram,
            # on force "required" — Instagram sans image n'a aucun sens.
            if platform == "instagram":
                image_mode = "required"
            image_status = variant.get("image_status")
            image_error = variant.get("image_error")
            should_generate_image = (
                include_images
                and image_mode != "none"
                and (not image_url or bool(image_error))
            )
            logger.info(
                "[weekly_content] variant=%s platform=%s image_mode=%s existing_url=%s → generate_image=%s",
                variant.get("variant_id"),
                platform,
                image_mode,
                bool(image_url),
                should_generate_image,
            )
            if should_generate_image:
                merged_for_img = await _build_merged_for_image(
                    idea_id=idea_id,
                    platform=platform,
                    objective=objective,
                    align_with_project=align_with_project,
                    access_token=access_token,
                )
                img_url, img_err = await _generate_item_image(
                    runner=runner,
                    merged=merged_for_img,
                    platform=platform,
                    caption=caption,
                )
                image_url = img_url
                image_error = img_err
                image_status = "generated" if img_url else ("failed" if img_err else image_status)
                if img_err:
                    logger.warning(
                        "[weekly_content] image gen failed | variant=%s | err=%s",
                        variant.get("variant_id"),
                        img_err,
                    )
                else:
                    logger.info(
                        "[weekly_content] image ok | variant=%s | url=%s",
                        variant.get("variant_id"),
                        (image_url or "")[:80],
                    )

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


@agent_trace("weekly_plan.approve", tags=["content_generation", "weekly_plan"])
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
    async with httpx.AsyncClient(timeout=content_http_timeout()) as client:
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
                # Garde-fou Instagram : toujours une image.
                if platform == "instagram":
                    image_mode = "required"
                if image_mode != "none" and not image_url:
                    merged_for_img = await _build_merged_for_image(
                        idea_id=idea_id,
                        platform=platform,
                        objective=objective,
                        align_with_project=align_with_project,
                        access_token=access_token,
                    )
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
