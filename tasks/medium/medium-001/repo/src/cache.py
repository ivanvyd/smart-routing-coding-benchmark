"""In-memory cache for user data.

The public API is cache_get / cache_set; the key format is an internal
implementation detail. Pick one and document it here.
"""

from __future__ import annotations

_KEY_FORMAT_DOC = ""  # TODO: document

# Format A: 'user:<id>'  (chosen here)
# Format B: 'user_<id>'  (used by consumer)
_KEY_PREFIX = "user:"


def _key(user_id: int) -> str:
    return f"{_KEY_PREFIX}{user_id}"


_STORE: dict[str, dict] = {}


def cache_set(user_id: int, payload: dict) -> None:
    _STORE[_key(user_id)] = payload


def cache_get(user_id: int) -> dict | None:
    return _STORE.get(_key(user_id))
