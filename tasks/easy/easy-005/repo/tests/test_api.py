"""Tests for src.api.validate_user."""

from __future__ import annotations

import pytest

from src.api import ValidationError, validate_user


def test_valid_user() -> None:
    out = validate_user({"id": 1, "email": "a@b.c", "name": "Ada"})
    assert out == {"id": 1, "email": "a@b.c", "name": "Ada"}


def test_missing_id() -> None:
    with pytest.raises(ValidationError, match="id"):
        validate_user({"email": "a@b.c", "name": "Ada"})


def test_missing_email() -> None:
    with pytest.raises(ValidationError, match="email"):
        validate_user({"id": 1, "name": "Ada"})


def test_wrong_type_for_id() -> None:
    with pytest.raises(ValidationError, match="id"):
        validate_user({"id": "1", "email": "a@b.c", "name": "Ada"})


def test_email_without_at_sign() -> None:
    with pytest.raises(ValidationError, match="email"):
        validate_user({"id": 1, "email": "nope", "name": "Ada"})


def test_empty_name() -> None:
    with pytest.raises(ValidationError, match="name"):
        validate_user({"id": 1, "email": "a@b.c", "name": ""})
