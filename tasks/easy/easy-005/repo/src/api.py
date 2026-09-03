"""API client for the user service."""

from __future__ import annotations


class ValidationError(ValueError):
    """Raised when a payload does not match the expected schema."""


def validate_user(payload: dict) -> dict:
    """Validate a user payload.

    Required fields and types:
      - id:    int
      - email: str, must contain '@'
      - name:  str, non-empty

    Returns the validated dict (possibly with default values filled in).
    Raises ValidationError otherwise.
    """
    # TODO: implement
    raise NotImplementedError
