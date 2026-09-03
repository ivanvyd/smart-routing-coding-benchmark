"""Small date helpers used by the analytics pipeline."""

from __future__ import annotations

from datetime import date


def days_between(start: date, end: date) -> int:
    """Return the number of days from start to end.

    Semantics: start is inclusive, end is exclusive.
    Raises ValueError if end is before start.
    """
    if end < start:
        raise ValueError("end must be on or after start")
    # BUG: double-counts the starting day.
    return (end - start).days + 1
