"""État OAuth éphémère (CSRF) — mémoire process."""

from __future__ import annotations

import time
from typing import Any

_state_meta: dict[str, dict[str, Any]] = {}
_state_li: dict[str, dict[str, Any]] = {}
TTL_S = 600.0


def _prune(store: dict[str, dict[str, Any]]) -> None:
    now = time.monotonic()
    dead = [k for k, v in store.items() if now - v.get("ts", 0) > TTL_S]
    for k in dead:
        del store[k]


def save_meta_state(state: str) -> None:
    _prune(_state_meta)
    _state_meta[state] = {"ts": time.monotonic()}


def verify_meta_state(state: str) -> bool:
    _prune(_state_meta)
    if state not in _state_meta:
        return False
    del _state_meta[state]
    return True


def save_linkedin_state(state: str) -> None:
    _prune(_state_li)
    _state_li[state] = {"ts": time.monotonic()}


def verify_linkedin_state(state: str) -> bool:
    _prune(_state_li)
    if state not in _state_li:
        return False
    del _state_li[state]
    return True
