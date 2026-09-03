"""Configuration helpers for the pipeline.

The current implementation is incomplete:
  - Missing keys crash with KeyError.
  - String values of "null" are silently passed through.
Implement the functions described in the docstrings.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

T = TypeVar("T")


def get_or_raise(mapping: dict[str, Any], key: str, caster: Callable[[Any], T]) -> T:
    """Return mapping[key] cast with `caster`, or raise ValueError with a useful message.

    - If `key` is missing, raise ValueError("missing required key: <key>").
    - If `caster` raises, propagate a ValueError that includes the key.
    - If the value is the string "null", raise ValueError("required key has null value: <key>").
    """
    # TODO: implement
    raise NotImplementedError


def load_settings(payload: dict[str, Any]) -> dict[str, Any]:
    """Load the canonical settings dict from a raw parsed YAML/JSON payload.

    Recognized keys and types:
      - "max_workers": int (default 4)
      - "timeout_seconds": float (default 30.0)
      - "retries": int (default 3, must be >= 0)
      - "region": str (required)

    For optional keys, fall back to the documented default when the key is
    absent OR the value is the string "null". Raise ValueError for invalid
    types or out-of-range values.
    """
    # TODO: implement
    raise NotImplementedError
