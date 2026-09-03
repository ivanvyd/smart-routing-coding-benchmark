"""Tests for src.cache."""

from src.cache import cache_get, cache_set


def test_round_trip() -> None:
    cache_set(1, {"name": "Ada"})
    assert cache_get(1) == {"name": "Ada"}


def test_missing_returns_none() -> None:
    assert cache_get(999) is None
