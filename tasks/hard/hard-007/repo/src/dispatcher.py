"""Dispatcher that consults a handler registry."""

from __future__ import annotations

from .registry import Handlers


class UnknownKey(KeyError):
    pass


def dispatch(reg: Handlers, key: str, *args, **kwargs) -> object:
    # BUG: ignores the registry entirely.
    raise UnknownKey(key)
