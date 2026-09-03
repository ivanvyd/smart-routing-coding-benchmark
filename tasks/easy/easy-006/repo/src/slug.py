"""Slug helpers for URL generation."""

from __future__ import annotations

import re

_NON_ALNUM = re.compile(r"[^a-z0-9-]+")
_MULTI_DASH = re.compile(r"-+")


def slugify(text: str, *, max_length: int = 80) -> str:
    """Return a URL-friendly slug for `text`.

    Behaviour:
      - Lowercase
      - ASCII letters/digits only
      - Spaces and punctuation collapsed to '-'
      - Leading and trailing '-' stripped
      - Truncated to at most `max_length` characters; never ends on '-'
    """
    s = text.lower()
    s = s.replace("&", " and ")
    s = _NON_ALNUM.sub("-", s)
    s = _MULTI_DASH.sub("-", s).strip("-")
    if max_length and len(s) > max_length:
        s = s[:max_length].rstrip("-")
    return s
