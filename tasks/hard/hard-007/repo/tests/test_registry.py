"""Tests for src.registry."""

from src.registry import register, registry


def test_empty_registry() -> None:
    assert registry() == {}


def test_register_and_read_back() -> None:
    r = registry()
    register(r, "k", lambda: "v")
    assert r["k"]() == "v"


def test_register_overwrites() -> None:
    r = registry()
    register(r, "k", lambda: "first")
    register(r, "k", lambda: "second")
    assert r["k"]() == "second"
