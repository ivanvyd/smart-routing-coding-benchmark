"""API client with ad-hoc retry logic. BUG: disagrees with src/jobs.py."""

from __future__ import annotations

import time

DEFAULT_POLICY = None  # TODO: use src.retries.RetryPolicy


def call_with_retries(fn, *, max_attempts: int = 3) -> object:
    delay = 0.1
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except (ConnectionError, TimeoutError):
            if attempt == max_attempts:
                raise
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("unreachable")
