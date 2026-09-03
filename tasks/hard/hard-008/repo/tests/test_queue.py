"""Tests for src.queue."""

from src.queue import deliver_next, enqueue, pending, reset_for_tests, was_delivered


def setup_function(_fn) -> None:  # noqa: D401, ANN001
    reset_for_tests()


def test_each_item_delivered_at_most_once() -> None:
    enqueue("a")
    enqueue("b")
    seen: list[str] = []
    while True:
        item = deliver_next()
        if item is None:
            break
        seen.append(item)
    assert sorted(seen) == ["a", "b"]
    # A second pass finds nothing.
    assert deliver_next() is None


def test_was_delivered_truthful() -> None:
    enqueue("x")
    deliver_next()
    assert was_delivered("x") is True
    assert pending() == []
