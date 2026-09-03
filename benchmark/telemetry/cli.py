"""Telemetry CLI: pull invocations from Unity AI Gateway and attribute them
to (arm, task) runs.

Strategy:
  1. For each run, build a time window [start, end] from the captured
     start_iso / finish_iso in results/normalized/<arm>.jsonl.
  2. Query system.ai_gateway.usage for the benchmark requester and full run
     window.
  3. Aggregate token counts, latency, selected model.
  4. Match rows to exact, non-overlapping run windows from the serial matrix.

Cost uses a dated model-price snapshot and stays labelled as an estimate.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field, fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..io import load_jsonl


@dataclass
class Invocation:
    request_id: str
    invocation_id: str
    event_time: str
    endpoint_name: str
    endpoint_id: str
    destination_type: str
    destination_name: str
    destination_model: str
    latency_ms: int
    time_to_first_byte_ms: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cache_read_input_tokens: int
    cache_creation_input_tokens: int
    output_reasoning_tokens: int
    status_code: int
    user_agent: str
    requester: str
    routing_attempts: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class ModelPrice:
    input: float
    output: float
    cache_read: float
    cache_write: float


def _parse_iso(ts: str) -> datetime:
    parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed


def attribute_runs(
    runs: list[dict[str, Any]],
    invocations: list[Invocation],
    prices: dict[str, ModelPrice] | None = None,
) -> list[dict[str, Any]]:
    """Attach invocations to exact run windows.

    Exact windows prevent a boundary invocation from being counted in two
    consecutive runs. Runs with no matching invocations are returned with an
    empty list and a `telemetry_status` of "no_match".
    """
    by_run: list[dict[str, Any]] = []
    for r in runs:
        start = _parse_iso(r["started_at"])
        end = _parse_iso(r["finished_at"])
        matching: list[Invocation] = []
        for inv in invocations:
            t = _parse_iso(inv.event_time)
            if start <= t < end:
                matching.append(inv)
        by_run.append(
            {
                "run_id": r["run_id"],
                "arm": r["arm"],
                "task_id": r["task_id"],
                "started_at": r["started_at"],
                "finished_at": r["finished_at"],
                "invocation_count": len(matching),
                "models_used": sorted({i.destination_model for i in matching}),
                "total_input_tokens": sum(i.input_tokens for i in matching),
                "total_output_tokens": sum(i.output_tokens for i in matching),
                "total_cache_read_input_tokens": sum(i.cache_read_input_tokens for i in matching),
                "total_cache_creation_input_tokens": sum(
                    i.cache_creation_input_tokens for i in matching
                ),
                "total_output_reasoning_tokens": sum(i.output_reasoning_tokens for i in matching),
                "mean_latency_ms": (
                    round(sum(i.latency_ms for i in matching) / len(matching), 2) if matching else 0
                ),
                "p95_latency_ms": _percentile_latency(matching, 95),
                "error_count": sum(1 for i in matching if i.status_code >= 400),
                "estimated_cost": _estimate_cost(matching, prices),
                "invocations": [asdict(i) for i in matching],
                "telemetry_status": _status(matching),
            }
        )
    return by_run


def _model_key(value: str) -> str:
    key = value.strip().lower().replace("_", "-").replace(".", "-")
    for prefix in ("system-ai-", "databricks-", "anthropic-"):
        if key.startswith(prefix):
            key = key.removeprefix(prefix)
    return key


def _estimate_cost(
    invocations: list[Invocation],
    prices: dict[str, ModelPrice] | None,
) -> float | None:
    if not prices or not invocations:
        return None
    total = 0.0
    for invocation in invocations:
        price = prices.get(_model_key(invocation.destination_model))
        if price is None:
            return None
        cached = min(max(invocation.cache_read_input_tokens, 0), max(invocation.input_tokens, 0))
        created = min(
            max(invocation.cache_creation_input_tokens, 0),
            max(invocation.input_tokens - cached, 0),
        )
        uncached = max(invocation.input_tokens - cached - created, 0)
        total += (
            uncached * price.input
            + cached * price.cache_read
            + created * price.cache_write
            + max(invocation.output_tokens, 0) * price.output
        ) / 1_000_000
    return round(total, 8)


def load_prices(path: Path) -> dict[str, ModelPrice]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    models = payload.get("models", {})
    return {
        _model_key(name): ModelPrice(
            input=float(values["input"]),
            output=float(values["output"]),
            cache_read=float(values["cache_read"]),
            cache_write=float(values["cache_write"]),
        )
        for name, values in models.items()
    }


def _percentile_latency(invs: list[Invocation], p: float) -> float:
    if not invs:
        return 0.0
    s = sorted(i.latency_ms for i in invs)
    k = max(0, min(len(s) - 1, round((p / 100) * (len(s) - 1))))
    return float(s[k])


def _status(invs: list[Invocation]) -> str:
    if not invs:
        return "no_match"
    if any(i.status_code >= 400 for i in invs):
        return "errors"
    return "ok"


def load_runs(path: Path) -> list[dict[str, Any]]:
    return load_jsonl(path)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="src-telemetry")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_attr = sub.add_parser("attribute", help="attribute invocations to runs")
    p_attr.add_argument("--runs", required=True, help="path to results/normalized/<arm>.jsonl")
    p_attr.add_argument(
        "--invocations",
        required=True,
        help="path to a JSONL of invocations (from sql/usage.sql)",
    )
    p_attr.add_argument("--out", required=True)
    p_attr.add_argument(
        "--prices",
        help="JSON price snapshot; adds estimated USD cost to attributed runs",
    )
    p_attr.set_defaults(_handler=_handle_attribute)

    p_pull = sub.add_parser(
        "pull",
        help=(
            "Print a `databricks sql` invocation that fetches invocations for "
            "a given run window. This is a wrapper around sql/usage.sql."
        ),
    )
    p_pull.add_argument("--manifest", required=True)
    p_pull.add_argument("--start-utc", required=True)
    p_pull.add_argument("--end-utc", required=True)
    p_pull.add_argument("--requester", required=True)
    p_pull.set_defaults(_handler=_handle_pull)

    args = p.parse_args(argv)
    return int(args._handler(args) or 0)


def _handle_attribute(args: argparse.Namespace) -> int:
    runs = load_runs(Path(args.runs))
    invocations: list[Invocation] = []
    for line in Path(args.invocations).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        for key in (
            "latency_ms",
            "time_to_first_byte_ms",
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "cache_read_input_tokens",
            "cache_creation_input_tokens",
            "output_reasoning_tokens",
            "status_code",
        ):
            rec[key] = int(rec.get(key) or 0)
        rec["routing_attempts"] = rec.get("routing_attempts") or []
        allowed = {item.name for item in fields(Invocation)}
        invocations.append(
            Invocation(**{key: value for key, value in rec.items() if key in allowed})
        )
    prices = load_prices(Path(args.prices)) if args.prices else None
    out = attribute_runs(runs, invocations, prices)
    Path(args.out).write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in out) + "\n",
        encoding="utf-8",
    )
    print(f"[src-telemetry] wrote {len(out)} attributed runs to {args.out}")
    return 0


def _handle_pull(args: argparse.Namespace) -> int:
    sql_file = Path(__file__).resolve().parents[2] / "sql" / "usage.sql"
    print(
        f"databricks --profile DEFAULT sql query "
        f"--warehouse <warehouse_id> "
        f'"$(cat {sql_file}) | substitute '
        f"start='{args.start_utc}' end='{args.end_utc}' requester='{args.requester}'\""
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
