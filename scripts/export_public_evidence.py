"""Export benchmark evidence without workspace or requester identifiers."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

ARMS = ("FIXED_STRONG", "FIXED_CHEAP", "CLIENT_ROUTING")
RUN_FIELDS = (
    "arm",
    "task_id",
    "task_difficulty",
    "task_passed",
    "duration_seconds",
    "exit_code",
    "selected_model",
    "router_model",
    "router_duration_seconds",
    "router_input_tokens",
    "router_output_tokens",
    "routing_policy",
    "routing_policy_sha256",
    "routing_reason",
    "routing_blocker",
    "git_base_commit",
    "run_id",
)
ATTRIBUTION_FIELDS = (
    "arm",
    "task_id",
    "run_id",
    "invocation_count",
    "models_used",
    "total_input_tokens",
    "total_output_tokens",
    "total_cache_read_input_tokens",
    "total_cache_creation_input_tokens",
    "total_output_reasoning_tokens",
    "mean_latency_ms",
    "p95_latency_ms",
    "error_count",
    "estimated_cost",
    "telemetry_status",
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _write_jsonl(
    path: Path,
    rows: list[dict[str, Any]],
    fields: tuple[str, ...],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps({field: row.get(field) for field in fields}, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def main() -> None:
    source = Path("results")
    destination = Path("evidence") / "results"
    for arm in ARMS:
        _write_jsonl(
            destination / "normalized" / f"{arm}.jsonl",
            _load_jsonl(source / "normalized" / f"{arm}.jsonl"),
            RUN_FIELDS,
        )
        _write_jsonl(
            destination / "attributed" / f"{arm}.jsonl",
            _load_jsonl(source / "attributed" / f"{arm}.jsonl"),
            ATTRIBUTION_FIELDS,
        )
    shutil.copy2(source / "tables" / "summary.json", destination / "summary.json")
    figures = destination / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    for path in (source / "figures").glob("*.png"):
        shutil.copy2(path, figures / path.name)


if __name__ == "__main__":
    main()
