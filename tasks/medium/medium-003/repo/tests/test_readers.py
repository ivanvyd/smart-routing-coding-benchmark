"""Readers must use the central schema, not the old hard-coded strings."""

from src.readers import enrich_with_region, normalize_row


def test_normalize_row_uses_new_field() -> None:
    raw = {"cust_id": 1, "order_id": "o-1", "amount": 9.99, "created_at": "2026-01-01"}
    out = normalize_row(raw)
    assert out["customer_id"] == 1
    assert out["order_id"] == "o-1"


def test_enrich_with_region() -> None:
    rows = [
        {"customer_id": 1, "order_id": "a"},
        {"customer_id": 2, "order_id": "b"},
    ]
    out = enrich_with_region(rows, {1: "us", 2: "eu"})
    assert [r["region"] for r in out] == ["us", "eu"]


def test_enrich_unknown_region() -> None:
    rows = [{"customer_id": 99, "order_id": "x"}]
    out = enrich_with_region(rows, {})
    assert out[0]["region"] == "unknown"
