"""Tests for src.jobs.schedule."""

from __future__ import annotations

from src.jobs import schedule


def test_first_call() -> None:
    assert schedule(["a", "b"]) == ["a", "b"]


def test_second_call_does_not_leak() -> None:
    # If the default list is shared, this would also see ['a', 'b'].
    assert schedule(["c"]) == ["c"]
