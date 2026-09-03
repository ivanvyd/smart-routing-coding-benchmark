"""Tests for src.fetcher.fetch."""

from __future__ import annotations

import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from src.fetcher import fetch


def _start_hanging_server() -> ThreadingHTTPServer:
    """An HTTP handler that never sends a response."""
    class _H(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            time.sleep(1)
        def log_message(self, *args, **kwargs):  # noqa: ANN001
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), _H)
    server.daemon_threads = True
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


def test_fetch_respects_timeout() -> None:
    server = _start_hanging_server()
    try:
        host, port = server.server_address
        url = f"http://{host}:{port}/"
        t0 = time.monotonic()
        with pytest.raises((TimeoutError, socket.timeout)):
            fetch(url, timeout=0.1)
        elapsed = time.monotonic() - t0
        assert elapsed < 0.5, f"fetch should have returned, took {elapsed:.1f}s"
    finally:
        server.shutdown()
        server.server_close()
