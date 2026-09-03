"""Billing impact per state."""

from .orders import OrderState


def is_refundable(state: OrderState) -> bool:
    # BUG: still references the old 'refunded' name.
    return state in {OrderState.refunded, OrderState.cancelled}
