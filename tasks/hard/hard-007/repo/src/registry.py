"""A tiny plugin registry."""

from __future__ import annotations

from typing import Callable

Handlers = dict[str, Callable[..., object]]


def registry() -> Handlers:
    """Return a fresh, empty handler map."""
    return {}


def register(reg: Handlers, key: str, fn: Callable[..., object]) -> None:
    """Register fn under key. Last write wins; overwrites previous entry."""
    reg[key] = fn
