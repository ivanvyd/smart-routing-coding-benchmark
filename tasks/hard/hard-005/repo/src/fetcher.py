"""HTTP fetcher with a timeout parameter that is not yet forwarded."""

from __future__ import annotations

import urllib.request


def fetch(url: str, *, timeout: float = 5.0) -> bytes:
    """GET `url` and return the body. Raise on timeout, cancellation, or HTTP error."""
    with urllib.request.urlopen(url) as r:
        return r.read()  # type: ignore[return-value]
