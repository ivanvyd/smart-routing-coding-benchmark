"""Consumer that uses the cache with the WRONG key format."""

from __future__ import annotations

from .cache import cache_get, cache_set


def get_user_via_cache(user_id: int) -> dict | None:
    # BUG: this format does not match src.cache._key().
    return cache_get(int(f"user_{user_id}"))


def save_user_via_cache(user_id: int, payload: dict) -> None:
    cache_set(int(f"user_{user_id}"), payload)
