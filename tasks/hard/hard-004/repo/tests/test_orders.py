"""Tests using the new enum names."""

from __future__ import annotations

from src.billing import is_refundable
from src.fulfilment import should_ship
from src.notifications import template_for
from src.orders import OrderState, is_terminal


def test_renamed_variant_exists() -> None:
    assert hasattr(OrderState, "returned")
    assert not hasattr(OrderState, "refunded")


def test_new_cancelled_variant_exists() -> None:
    assert hasattr(OrderState, "cancelled")


def test_is_terminal_uses_renamed() -> None:
    assert is_terminal(OrderState.returned) is True
    assert is_terminal(OrderState.delivered) is True
    assert is_terminal(OrderState.paid) is False


def test_should_ship() -> None:
    assert should_ship(OrderState.paid) is True
    assert should_ship(OrderState.returned) is False


def test_template_uses_renamed() -> None:
    assert "return" in template_for(OrderState.returned).lower()


def test_is_refundable_uses_renamed() -> None:
    assert is_refundable(OrderState.returned) is True
    assert is_refundable(OrderState.cancelled) is True
    assert is_refundable(OrderState.paid) is False
