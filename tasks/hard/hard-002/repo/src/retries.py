"""Centralised retry policy + helper."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int
    initial_backoff_s: float
    backoff_factor: float = 2.0
    max_backoff_s: float = 30.0
    retryable: tuple[type[BaseException], ...] = (Exception,)

    def backoffs(self) -> Iterable[float]:
        delay = self.initial_backoff_s
        for _ in range(self.max_attempts - 1):
            yield min(delay, self.max_backoff_s)
            delay *= self.backoff_factor


def run_with_retry(policy: RetryPolicy, fn: Callable[[], T], *, sleep: Callable[[float], None] = time.sleep) -> T:
    last: BaseException | None = None
    for attempt, delay in enumerate([0.0, *policy.backoffs()], start=1):
        if delay:
            sleep(delay)
        try:
            return fn()
        except policy.retryable as e:  # type: ignore[misc]
            last = e
            if attempt >= policy.max_attempts:
                raise
    if last is not None:
        raise last
    raise RuntimeError("unreachable")
