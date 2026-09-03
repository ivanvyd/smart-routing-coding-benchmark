"""Tests for src.client.call using the new API error shape."""

from __future__ import annotations

import json

import pytest

from src.client import APIError, call


class _FakeResp:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):  # noqa: D401, ANN001
        return self

    def __exit__(self, *args):  # noqa: ANN001
        return False


def test_returns_parsed_body(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_open(url: str) -> _FakeResp:
        return _FakeResp(json.dumps({"hello": "world"}).encode("utf-8"))

    monkeypatch.setattr("urllib.request.urlopen", fake_open)
    assert call("http://x") == {"hello": "world"}


def test_raises_api_error_from_new_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_open(url: str) -> _FakeResp:
        return _FakeResp(json.dumps({
            "error": {"code": "rate_limited", "message": "try again later"},
            "request_id": "abc-123",
        }).encode("utf-8"))

    monkeypatch.setattr("urllib.request.urlopen", fake_open)
    with pytest.raises(APIError) as ei:
        call("http://x")
    assert ei.value.code == "rate_limited"
    assert "try again" in str(ei.value)
