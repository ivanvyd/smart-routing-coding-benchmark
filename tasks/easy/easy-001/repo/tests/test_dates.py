"""Deterministic tests for src.dates.days_between."""

from datetime import date

import pytest

from src.dates import days_between


def test_same_day_returns_zero() -> None:
    assert days_between(date(2026, 1, 1), date(2026, 1, 1)) == 0


def test_one_day_apart_returns_one() -> None:
    assert days_between(date(2026, 1, 1), date(2026, 1, 2)) == 1


def test_seven_day_range() -> None:
    assert days_between(date(2026, 1, 1), date(2026, 1, 8)) == 7


def test_month_boundary() -> None:
    assert days_between(date(2026, 1, 28), date(2026, 2, 4)) == 7


def test_rejects_reversed_range() -> None:
    with pytest.raises(ValueError):
        days_between(date(2026, 1, 5), date(2026, 1, 4))
