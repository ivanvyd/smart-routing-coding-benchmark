"""Simple in-memory delivery queue."""

from __future__ import annotations

import threading
from contextlib import contextmanager

_QUEUE: list[str] = []
_DELIVERED: set[str] = set()
_LOCK = threading.Lock()


@contextmanager
def _critical():
    with _LOCK:
        yield


def enqueue(item: str) -> None:
    with _LOCK:
        _QUEUE.append(item)


def deliver_next() -> str | None:
    """Atomically: pick the next undelivered item, mark it delivered."""
    # BUG: marks delivered BEFORE removing; a second caller can pick the
    # same item between mark and remove.
    with _critical():
        if not _QUEUE:
            return None
        item = _QUEUE[0]
        _DELIVERED.add(item)
    _QUEUE.pop(0)
    return item


def was_delivered(item: str) -> bool:
    return item in _DELIVERED


def pending() -> list[str]:
    return list(_QUEUE)


def reset_for_tests() -> None:
    with _LOCK:
        _QUEUE.clear()
        _DELIVERED.clear()
