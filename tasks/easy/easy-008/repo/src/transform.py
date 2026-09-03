"""Small data-transform helpers."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Iterable


def flatten(record: dict, prefix: str = "") -> dict[str, Any]:
    """Flatten nested dicts/lists with dotted keys.

    Lists of primitives are joined with '|'.
    Lists of dicts are flattened with index suffixes (foo.0.bar).
    """
    out: dict[str, Any] = {}
    for k, v in record.items():
        key = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
        if isinstance(v, dict):
            out.update(flatten(v, key))
        elif isinstance(v, list):
            if all(not isinstance(x, (dict, list)) for x in v):
                out[key] = "|".join(str(x) for x in v)
            else:
                for i, x in enumerate(v):
                    if isinstance(x, dict):
                        out.update(flatten(x, f"{key}.{i}"))
                    else:
                        out[f"{key}.{i}"] = x
        else:
            out[key] = v
    return out


def records_to_csv(records: Iterable[dict]) -> str:
    """Render flattened records as a CSV string with a stable header."""
    flat = [flatten(r) for r in records]
    if not flat:
        return ""
    fieldnames = sorted({k for r in flat for k in r})
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fieldnames)
    w.writeheader()
    for r in flat:
        w.writerow({k: r.get(k, "") for k in fieldnames})
    return buf.getvalue()


def flatten_and_to_csv(data: str | list[dict]) -> str:
    """Accept either a JSON string or a list of dicts. Return CSV text."""
    if isinstance(data, str):
        data = json.loads(data)
    return records_to_csv(data)
