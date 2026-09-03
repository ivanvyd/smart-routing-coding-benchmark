"""Thread-safe counter. Currently NOT thread-safe."""

from __future__ import annotations

import threading


class Counter:
    def __init__(self, initial: int = 0) -> None:
        self._value = initial
        # BUG: the lock is created but never used.
        self._lock = threading.Lock()

    @property
    def value(self) -> int:
        return self._value

    def increment(self, by: int = 1) -> int:
        current = self._value
        # Simulate a tiny window where another thread can sneak in.
        # (We do not actually sleep; the read-then-write is the bug.)
        new = current + by
        self._value = new
        return new
