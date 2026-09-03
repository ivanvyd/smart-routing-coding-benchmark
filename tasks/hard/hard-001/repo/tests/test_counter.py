"""Thread-safety tests for src.counter.Counter."""

from __future__ import annotations

import threading

from src.counter import Counter


def test_basic_increment() -> None:
    c = Counter()
    c.increment()
    c.increment(2)
    assert c.value == 3


def test_concurrent_increments_do_not_lose_updates() -> None:
    c = Counter()
    n_threads = 8
    n_increments = 500
    threads = []

    def worker() -> None:
        for _ in range(n_increments):
            c.increment()

    for _ in range(n_threads):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    assert c.value == n_threads * n_increments
