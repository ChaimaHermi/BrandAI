"""
Step streamer for the Website Builder.

Transforme un pipeline orchestrateur (description / generation / revision /
refinement) en flux d'evenements "etape par etape" consommable par le
frontend via Server-Sent Events. C'est notre couche XAI : l'utilisateur voit
en temps reel ou en est l'agent.

Format des evenements (JSON par ligne) :

  {"type": "step", "id": "context", "label": "...", "status": "running"}
  {"type": "step", "id": "context", "label": "...", "status": "done", "meta": {...}}
  {"type": "tick", "id": "design", "label": "Imagination du concept hero..."}
  {"type": "result", "payload": {...}}
  {"type": "error", "message": "..."}
  {"type": "done"}

Le client emet les events au fur et a mesure ; cote backend on utilise une
asyncio.Queue couplee a une StreamingResponse FastAPI.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from typing import Any

logger = logging.getLogger("brandai.website_builder.step_streamer")


# Messages "creatifs" affiches en boucle pendant que le LLM travaille,
# pour donner a l'utilisateur un sentiment de progression.
DESCRIPTION_TICKS: tuple[str, ...] = (
    "Analyse du brand kit et de la palette...",
    "Cadrage du positionnement et de la cible...",
    "Imagination du concept hero...",
    "Conception des sections principales...",
    "Choix des animations et interactions...",
    "Definition de la typographie premium...",
    "Strategie couleur, contrastes et accents...",
    "Reglage du ton de voix editorial...",
    "Ecriture du resume utilisateur final...",
)

REFINEMENT_TICKS: tuple[str, ...] = (
    "Lecture attentive de tes retours...",
    "Identification des sections impactees...",
    "Reecriture du concept hero si necessaire...",
    "Ajustement des sections / animations...",
    "Maintien de la coherence avec la marque...",
    "Validation du nouveau JSON...",
)

GENERATION_TICKS: tuple[str, ...] = (
    "Lecture du concept et du brand kit...",
    "Construction du squelette HTML5 + meta SEO...",
    "Configuration Tailwind CDN + tailwind.config...",
    "Integration des Google Fonts du brand kit...",
    "Ecriture du header sticky + navigation desktop/mobile...",
    "Ecriture du hero (slogan + CTA + visuel)...",
    "Generation des sections de contenu...",
    "Integration des animations IntersectionObserver...",
    "Ecriture du footer + reseaux sociaux...",
    "Stylisation responsive (sm/md/lg/xl)...",
    "Verification de la coherence des ancres internes...",
    "Polissage typographique et contraste...",
)

REVISION_TICKS: tuple[str, ...] = (
    "Lecture de ta consigne...",
    "Reperage des zones a modifier dans le HTML...",
    "Application chirurgicale de la modification...",
    "Maintien du brand kit et des invariants nav...",
    "Verification anti-regression sur les ancres...",
    "Polissage final du HTML modifie...",
)


def event_step(
    step_id: str,
    label: str,
    *,
    status: str = "running",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": "step",
        "id": step_id,
        "label": label,
        "status": status,
    }
    if meta:
        payload["meta"] = meta
    return payload


def event_tick(step_id: str, label: str) -> dict[str, Any]:
    return {"type": "tick", "id": step_id, "label": label}


def event_result(payload: dict[str, Any]) -> dict[str, Any]:
    return {"type": "result", "payload": payload}


def event_error(message: str) -> dict[str, Any]:
    return {"type": "error", "message": message}


def event_done() -> dict[str, Any]:
    return {"type": "done"}


def serialize_sse(event: dict[str, Any]) -> str:
    """Serialise un event au format SSE (`data: <json>\\n\\n`)."""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


class StepEmitter:
    """File de messages que le pipeline pousse et que la route SSE consomme."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()

    async def emit(self, event: dict[str, Any]) -> None:
        await self._queue.put(event)

    async def emit_step(
        self,
        step_id: str,
        label: str,
        *,
        status: str = "running",
        meta: dict[str, Any] | None = None,
    ) -> None:
        await self.emit(event_step(step_id, label, status=status, meta=meta))

    async def emit_result(self, payload: dict[str, Any]) -> None:
        await self.emit(event_result(payload))

    async def emit_error(self, message: str) -> None:
        await self.emit(event_error(message))

    async def close(self) -> None:
        await self._queue.put(None)

    async def stream(self) -> AsyncIterator[dict[str, Any]]:
        while True:
            item = await self._queue.get()
            if item is None:
                return
            yield item


async def run_with_progress(
    emitter: StepEmitter,
    *,
    step_id: str,
    coro_factory: Callable[[], Awaitable[Any]],
    tick_messages: Sequence[str],
    tick_interval: float = 2.5,
    emit_ticks: bool = False,
) -> Any:
    """
    Lance la coroutine `coro_factory()` en parallele d'un ticker qui emet
    des messages "tick" toutes les `tick_interval` secondes.

    Les ticks affichent ce que l'agent "pense" en boucle, jusqu'a ce que
    la coroutine renvoie son resultat.
    """
    if not emit_ticks or not tick_messages:
        return await coro_factory()

    stop = asyncio.Event()
    started_at = time.monotonic()

    async def _ticker() -> None:
        idx = 0
        while not stop.is_set():
            try:
                await asyncio.wait_for(stop.wait(), timeout=tick_interval)
                return
            except asyncio.TimeoutError:
                pass
            label = tick_messages[idx % len(tick_messages)]
            elapsed = time.monotonic() - started_at
            try:
                await emitter.emit(
                    {
                        "type": "tick",
                        "id": step_id,
                        "label": label,
                        "elapsed_seconds": round(elapsed, 1),
                    }
                )
            except Exception:
                logger.exception("[step_streamer] ticker emit failed")
                return
            idx += 1

    ticker_task = asyncio.create_task(_ticker())
    try:
        result = await coro_factory()
        return result
    finally:
        stop.set()
        try:
            await ticker_task
        except asyncio.CancelledError:
            pass


async def sse_response_stream(emitter: StepEmitter) -> AsyncIterator[bytes]:
    """Stream SSE pret a passer a `StreamingResponse`."""
    async for event in emitter.stream():
        yield serialize_sse(event).encode("utf-8")
    # Marqueur explicite de fin pour les clients qui en ont besoin.
    yield serialize_sse(event_done()).encode("utf-8")
