"""Reporting aggregations."""

from .orders import OrderState


def count_by_state(orders: list) -> dict[str, int]:
    counts: dict[str, int] = {}
    for o in orders:
        key = o.state.value
        counts[key] = counts.get(key, 0) + 1
    return counts
