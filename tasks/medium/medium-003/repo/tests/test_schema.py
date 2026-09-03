"""Schema is the single source of truth."""

from src.schema import AMOUNT, CREATED_AT, CUSTOMER_ID, ORDER_ID


def test_renamed_constant() -> None:
    # Upstream renamed customer_id -> cust_id. The central constant must match.
    assert CUSTOMER_ID == "cust_id"


def test_other_constants_unchanged() -> None:
    assert ORDER_ID == "order_id"
    assert AMOUNT == "amount"
    assert CREATED_AT == "created_at"
