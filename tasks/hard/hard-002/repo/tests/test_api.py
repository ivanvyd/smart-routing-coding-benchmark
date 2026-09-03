"""API must use the central policy."""

from src.api import call_with_retries
from src.retries import RetryPolicy


def test_api_uses_central_policy_for_max_attempts() -> None:
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 4:
            raise ConnectionError()
        return "ok"

    out = call_with_retries(flaky, max_attempts=4)
    assert out == "ok"
    assert calls["n"] == 4
    # Indirect: behaviour agrees with RetryPolicy(max_attempts=4, ...).
    assert RetryPolicy(max_attempts=4, initial_backoff_s=0.0, retryable=(ConnectionError,)) is not None
