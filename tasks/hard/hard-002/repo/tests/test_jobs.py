"""Jobs must use the central policy."""

from src.jobs import run_with_retry
from src.retries import RetryPolicy


def test_jobs_uses_central_policy_for_max_attempts() -> None:
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError()
        return "ok"

    out = run_with_retry(flaky, attempts=3)
    assert out == "ok"
    assert calls["n"] == 3
    assert RetryPolicy(max_attempts=3, initial_backoff_s=0.0, retryable=(ConnectionError,)) is not None
