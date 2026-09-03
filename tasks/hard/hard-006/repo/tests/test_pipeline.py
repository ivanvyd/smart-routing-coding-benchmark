"""Unit test: passes today."""

from src.pipeline import process


def test_process_parses_amount() -> None:
    assert process({"id": 1, "amount": "12.50"}) == {"id": 1, "amount": 12.5}
