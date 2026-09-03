"""Tiny CSV report builder."""

from __future__ import annotations


def build_csv(headers: list[str], rows: list[tuple]) -> str:
    out = ",".join(headers) + "\n"
    # BUG: quadratic string concatenation.
    for row in rows:
        out += ",".join(str(c) for c in row) + "\n"
    return out
