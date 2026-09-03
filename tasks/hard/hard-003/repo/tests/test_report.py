"""Tests for src.report.build_csv."""

from __future__ import annotations

import time

from src.report import build_csv


def test_empty() -> None:
    assert build_csv(["a", "b"], []) == "a,b\n"


def test_one_row() -> None:
    assert build_csv(["a", "b"], [(1, 2)]) == "a,b\n1,2\n"


def test_unicode_values() -> None:
    assert build_csv(["name"], [("café",)]) == "name\ncafé\n"


def test_large_input_runs_in_reasonable_time() -> None:
    headers = ["id", "value", "tag"]
    rows = [(i, i * 2, f"row-{i}") for i in range(2000)]
    t0 = time.monotonic()
    out = build_csv(headers, rows)
    elapsed = time.monotonic() - t0
    assert elapsed < 1.0, f"build_csv too slow: {elapsed:.3f}s for 2000 rows"
    # Sanity: header line is present and the last row is correct.
    assert out.startswith("id,value,tag\n")
    assert out.rstrip().endswith("1999,3998,row-1999")
