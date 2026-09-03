"""Billing helpers."""

from __future__ import annotations

from decimal import Decimal


def compute_total(items: list[dict]) -> Decimal:
    """Sum the 'amount' field of every item, treating missing as 0."""
    return sum((Decimal(str(it.get("amount", 0))) for it in items), Decimal("0"))


def total_with_tax(items: list[dict], tax_rate: Decimal) -> Decimal:
    """Total + tax. Uses compute_total internally."""
    return compute_total(items) * (Decimal("1") + tax_rate)
