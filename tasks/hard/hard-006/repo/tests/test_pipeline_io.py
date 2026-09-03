"""Integration test: catches the boundary bug."""

from src.pipeline import from_csv_row


def test_from_csv_row_uses_correct_field_names() -> None:
    out = from_csv_row({"id": 1, "Amount": "12.50"})
    assert out == {"id": 1, "amount": 12.5}
