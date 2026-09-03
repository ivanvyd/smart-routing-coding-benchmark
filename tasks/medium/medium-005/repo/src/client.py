"""Tiny API client wrapper. Implements only what the tests need."""

from __future__ import annotations

import urllib.error
import urllib.request


class APIError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def call(url: str) -> dict:
    """GET a JSON object from `url` and return the parsed body.

    On a 4xx/5xx response, parse the new error envelope
    ({error: {code, message}, request_id}) and raise APIError.
    """
    # BUG: still parses the old envelope {errors: [{code, message}]}.
    with urllib.request.urlopen(url) as r:
        return r.read()  # type: ignore[return-value]
