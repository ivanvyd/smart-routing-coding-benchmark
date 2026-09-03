"""Job helpers. BUG: ad-hoc retry policy that disagrees with src/api.py."""

from __future__ import annotations

import time


def run_with_retry(fn, *, attempts: int = 5) -> object:
    delay = 0.5
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except (ConnectionError,):
            if attempt == attempts:
                raise
            time.sleep(delay)
            delay *= 3
    raise RuntimeError("unreachable")
