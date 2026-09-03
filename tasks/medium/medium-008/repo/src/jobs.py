"""Job scheduling helpers."""

from __future__ import annotations


def schedule(jobs: list[str], seen: list[str] = []) -> list[str]:  # noqa: B006
    """Append each job in `jobs` to `seen` and return the new list."""
    for j in jobs:
        seen.append(j)
    return list(seen)
