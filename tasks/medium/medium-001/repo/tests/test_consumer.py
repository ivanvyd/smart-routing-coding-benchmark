"""Tests for src.consumer. Confirms the consumer reads what the cache wrote."""

from src.cache import cache_set
from src.consumer import get_user_via_cache, save_user_via_cache


def test_save_then_get_via_consumer() -> None:
    save_user_via_cache(42, {"name": "Bob"})
    assert get_user_via_cache(42) == {"name": "Bob"}


def test_cache_set_then_consumer_get() -> None:
    cache_set(7, {"name": "Eve"})
    assert get_user_via_cache(7) == {"name": "Eve"}
