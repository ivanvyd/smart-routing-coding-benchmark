"""Two-stage pipeline."""

from __future__ import annotations


def _parse_amount(value: str) -> float:
    # BUG: silently drops the currency sign; treats "$12.50" as 0.
    return float(value.replace("$", "").replace(",", "") or "0")


def process(record: dict) -> dict:
    return {
        "id": record["id"],
        "amount": _parse_amount(str(record["amount"])),
    }


def from_csv_row(row: dict) -> dict:
    # BUG: forgets to normalise the key naming convention from CSV.
    return process({"id": row["id"], "amount": row["Amount"]})
