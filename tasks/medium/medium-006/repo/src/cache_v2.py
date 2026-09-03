"""A small KV cache that tracks a logical timestamp per key."""

from __future__ import annotations

import threading

# Logical clock that the verify-then-update pattern uses.
_now = [0]
_lock = threading.Lock()


def _tick() -> int:
    with _lock:
        _now[0] += 1
        return _now[0]


def reset_for_tests() -> None:
    with _lock:
        _now[0] = 0
    _store.clear()


_store: dict[str, tuple[int, object]] = {}
_store_lock = threading.Lock()


def get_if_fresh(key: str, min_ts: int) -> object | None:
    """Return value if its ts >= min_ts, else None."""
    with _store_lock:
        entry = _store.get(key)
        if entry is None:
            return None
        ts, val = entry
        return val if ts >= min_ts else None


def set_if_newer(key: str, value: object) -> int:
    """Set value only if there is no newer entry already. Return ts used."""
    ts = _tick()
    with _store_lock:
        existing = _store.get(key)
        if existing is not None and existing[0] > ts:
            return existing[0]
        _store[key] = (ts, value)
    return ts


def verify_then_update(key: str, value: object, min_ts: int) -> tuple[object, int]:
    """Verify that no newer value exists since `min_ts`, then update.

    Return (value, ts) on success. If a fresher value already exists,
    return that fresher value with its ts WITHOUT overwriting it.
    """
    # BUG: re-reads and overwrites even when something newer is now stored.
    current = get_if_fresh(key, min_ts)
    ts = _tick()
    with _store_lock:
        _store[key] = (ts, value)
    return value, ts
