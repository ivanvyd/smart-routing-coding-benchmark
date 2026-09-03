"""Notifications that listen to state changes."""

from .orders import OrderState


def template_for(state: OrderState) -> str:
    if state == OrderState.refunded:        # BUG: old name
        return "Your refund has been processed."
    if state == OrderState.delivered:
        return "Your order has arrived."
    return f"Order is now {state.value}."
