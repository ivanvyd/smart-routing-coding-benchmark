"""Shared JSONL I/O for the benchmark.

Three of the four pipeline stages had their own near-identical copy of
"read a JSONL into a list of dicts" or "read every <arm>.jsonl under a
dir into a dict keyed by arm." They live here now.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def load_jsonl_by_arm(dir_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Read every <arm>.jsonl under `dir_path` into {arm: [rows]}."""
    out: dict[str, list[dict[str, Any]]] = {}
    if not dir_path.exists():
        return out
    for p in sorted(dir_path.glob("*.jsonl")):
        out[p.stem] = load_jsonl(p)
    return out
