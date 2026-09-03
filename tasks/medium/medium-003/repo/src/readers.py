"""Read raw rows and translate to canonical schema."""

from __future__ import annotations

from .schema import AMOUNT, CREATED_AT, CUSTOMER_ID, ORDER_ID


def normalize_row(raw: dict) -> dict:
    return {
        "customer_id": raw.get(CUSTOMER_ID),
        "order_id":    raw.get(ORDER_ID),
        "amount":      raw.get(AMOUNT),
        "created_at":  raw.get(CREATED_AT),
    }


def enrich_with_region(rows: list[dict], region_lookup: dict[int, str]) -> list[dict]:
    """Add a `region` field by customer_id."""
    out = []
    for r in rows:
        rr = dict(r)
        rr["region"] = region_lookup.get(int(r["customer_id"]), "unknown")
        out.append(rr)
    return out
