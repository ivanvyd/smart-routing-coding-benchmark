"""Tests for src.dispatcher."""

from src.dispatcher import UnknownKey, dispatch
from src.registry import register, registry


def test_dispatch_uses_registry() -> None:
    r = registry()
    register(r, "greet", lambda name: f"hi {name}")
    assert dispatch(r, "greet", "Ada") == "hi Ada"


def test_dispatch_raises_for_unknown_key() -> None:
    r = registry()
    try:
        dispatch(r, "missing")
    except UnknownKey:
        return
    raise AssertionError("expected UnknownKey")
