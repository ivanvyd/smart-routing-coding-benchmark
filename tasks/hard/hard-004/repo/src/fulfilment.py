"""Fulfilment that checks state."""

from .orders import OrderState, is_terminal


def should_ship(state: OrderState) -> bool:
    return state == OrderState.paid and not is_terminal(state)
