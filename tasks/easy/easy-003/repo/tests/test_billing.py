"""Tests for the renamed billing helpers."""

from __future__ import annotations

from decimal import Decimal

from src.billing import sum_amounts, total_with_tax


def test_sum_amounts_basic() -> None:
    assert sum_amounts([{"amount": "1.50"}, {"amount": "2.25"}]) == Decimal("3.75")


def test_sum_amounts_empty() -> None:
    assert sum_amounts([]) == Decimal("0")


def test_sum_amounts_missing_amount() -> None:
    assert sum_amounts([{"foo": "bar"}]) == Decimal("0")


def test_total_with_tax_uses_renamed() -> None:
    assert total_with_tax([{"amount": "100"}], Decimal("0.1")) == Decimal("110")
