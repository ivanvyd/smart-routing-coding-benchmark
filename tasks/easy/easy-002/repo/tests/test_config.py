"""Deterministic tests for src.config."""

from __future__ import annotations

import pytest

from src.config import get_or_raise, load_settings


def test_get_or_raise_happy_path() -> None:
    assert get_or_raise({"a": "5"}, "a", int) == 5


def test_get_or_raise_missing_key() -> None:
    with pytest.raises(ValueError, match="missing required key: a"):
        get_or_raise({}, "a", int)


def test_get_or_raise_null_value() -> None:
    with pytest.raises(ValueError, match="required key has null value: a"):
        get_or_raise({"a": "null"}, "a", int)


def test_load_settings_defaults() -> None:
    out = load_settings({"region": "us-west-2"})
    assert out["region"] == "us-west-2"
    assert out["max_workers"] == 4
    assert out["timeout_seconds"] == 30.0
    assert out["retries"] == 3


def test_load_settings_null_string_for_optional() -> None:
    out = load_settings({"region": "us-west-2", "retries": "null"})
    assert out["retries"] == 3


def test_load_settings_rejects_missing_region() -> None:
    with pytest.raises(ValueError, match="region"):
        load_settings({})


def test_load_settings_rejects_negative_retries() -> None:
    with pytest.raises(ValueError, match="retries"):
        load_settings({"region": "us-west-2", "retries": -1})
