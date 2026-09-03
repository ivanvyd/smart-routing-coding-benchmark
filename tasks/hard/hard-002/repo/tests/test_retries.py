"""Test the central RetryPolicy behaves correctly."""

from __future__ import annotations

import pytest

from src.retries import RetryPolicy, run_with_retry


def test_eventual_success() -> None:
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("nope")
        return "ok"

    policy = RetryPolicy(max_attempts=5, initial_backoff_s=0.0, retryable=(ConnectionError,))
    sleeps: list[float] = []
    out = run_with_retry(policy, flaky, sleep=sleeps.append)
    assert out == "ok"
    assert calls["n"] == 3


def test_exhausts_attempts() -> None:
    def always_fail() -> None:
        raise ConnectionError("nope")

    policy = RetryPolicy(max_attempts=3, initial_backoff_s=0.0, retryable=(ConnectionError,))
    with pytest.raises(ConnectionError):
        run_with_retry(policy, always_fail, sleep=lambda _: None)
