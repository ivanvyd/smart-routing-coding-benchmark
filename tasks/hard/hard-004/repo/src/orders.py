"""Order state enum and helpers."""

from __future__ import annotations

from enum import Enum


class OrderState(str, Enum):
    pending = "pending"
    paid = "paid"
    shipped = "shipped"
    delivered = "delivered"
    refunded = "refunded"      # BUG: should be 'returned'
    # New variant: cancelled = "cancelled"


def is_terminal(state: OrderState) -> bool:
    # BUG: uses the old name; tests use 'returned'.
    return state in {OrderState.delivered, OrderState.refunded}
