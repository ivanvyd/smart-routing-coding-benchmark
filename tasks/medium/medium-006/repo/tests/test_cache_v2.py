"""Tests for src.cache_v2.verify_then_update."""

from __future__ import annotations

from src.cache_v2 import reset_for_tests, set_if_newer, verify_then_update


def setup_function(_fn) -> None:  # noqa: D401, ANN001
    reset_for_tests()


def test_first_write_succeeds() -> None:
    v, ts = verify_then_update("k", "v1", min_ts=0)
    assert v == "v1"
    assert ts >= 1


def test_does_not_overwrite_newer() -> None:
    ts1 = set_if_newer("k", "v1")
    # A verify_then_update with min_ts BEFORE the current ts must not stomp.
    v, ts = verify_then_update("k", "v0", min_ts=0)
    assert v == "v1"
    assert ts == ts1
