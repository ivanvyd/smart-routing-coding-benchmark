"""Compute the benchmark's headline metrics per arm.

All functions return a dict with the metric name as key. If the input is
empty or `NOT_MEASURED` is requested, the returned value is the literal
string "NOT_MEASURED" so the chart code can show a placeholder.
"""

from __future__ import annotations

import math
import statistics
from collections import Counter
from typing import Any

NOT_MEASURED = "NOT_MEASURED"


def _safe(v: Any) -> Any:
    if v is None:
        return NOT_MEASURED
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return NOT_MEASURED
    return v


def per_arm_metrics(
    arm: str,
    runs: list[dict[str, Any]],
    attributed: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return the headline metrics for one arm.

    `runs` are the raw runner outputs.
    `attributed` are the per-run attributed invocations (may be empty).
    """
    if not runs:
        return {"arm": arm, "status": NOT_MEASURED}

    n = len(runs)
    passes = sum(1 for r in runs if r.get("task_passed"))
    by_diff: Counter[str] = Counter()
    pass_by_diff: Counter[str] = Counter()
    for r in runs:
        d = r.get("task_difficulty", "unknown")
        by_diff[d] += 1
        if r.get("task_passed"):
            pass_by_diff[d] += 1

    durations = [r.get("duration_seconds", 0.0) for r in runs]

    metrics: dict[str, Any] = {
        "arm": arm,
        "n_runs": n,
        "task_success_rate": _safe(passes / n if n else None),
        "passes_easy": pass_by_diff.get("easy", 0),
        "passes_medium": pass_by_diff.get("medium", 0),
        "passes_hard": pass_by_diff.get("hard", 0),
        "n_easy": by_diff.get("easy", 0),
        "n_medium": by_diff.get("medium", 0),
        "n_hard": by_diff.get("hard", 0),
        "mean_duration_seconds": _safe(statistics.fmean(durations) if durations else None),
        "median_duration_seconds": _safe(statistics.median(durations) if durations else None),
    }

    if attributed is None:
        metrics.update(
            {
                "total_input_tokens": NOT_MEASURED,
                "total_output_tokens": NOT_MEASURED,
                "total_tokens": NOT_MEASURED,
                "mean_latency_ms": NOT_MEASURED,
                "p95_latency_ms": NOT_MEASURED,
                "error_rate": NOT_MEASURED,
                "invocations_per_run": NOT_MEASURED,
                "cost_per_attempted_task": NOT_MEASURED,
                "cost_per_successful_task": NOT_MEASURED,
                "total_estimated_cost": NOT_MEASURED,
            }
        )
        return metrics

    invs = sum(a.get("invocation_count", 0) for a in attributed)
    total_in = sum(a.get("total_input_tokens", 0) for a in attributed)
    total_out = sum(a.get("total_output_tokens", 0) for a in attributed)
    errs = sum(a.get("error_count", 0) for a in attributed)
    latencies = [
        float(invocation.get("latency_ms", 0.0))
        for a in attributed
        for invocation in a.get("invocations", [])
        if float(invocation.get("latency_ms", 0.0)) > 0
    ]
    p95 = _percentile(latencies, 95) if latencies else None

    # Cost stays separate from token totals because the conversion depends on
    # the dated price snapshot supplied during attribution.
    costs = [a.get("estimated_cost") for a in attributed]
    numeric_costs = [float(cost) for cost in costs if isinstance(cost, int | float)]
    total_cost: float | str
    cps: float | str
    cpa: float | str
    if not costs or len(numeric_costs) != len(costs):
        total_cost = NOT_MEASURED
        cps = NOT_MEASURED
        cpa = NOT_MEASURED
    else:
        measured_cost = sum(numeric_costs)
        total_cost = measured_cost
        cpa = measured_cost / n
        cps = measured_cost / passes if passes else NOT_MEASURED

    metrics.update(
        {
            "total_input_tokens": _safe(total_in),
            "total_output_tokens": _safe(total_out),
            "total_tokens": _safe(total_in + total_out),
            "mean_latency_ms": _safe(statistics.fmean(latencies) if latencies else None),
            "p95_latency_ms": _safe(p95),
            "error_rate": _safe((errs / invs) if invs else None),
            "invocations_per_run": _safe(invs / n if n else None),
            "total_estimated_cost": _safe(total_cost),
            "cost_per_attempted_task": _safe(cpa),
            "cost_per_successful_task": cps,
        }
    )
    return metrics


def _percentile(values: list[float], p: int) -> float:
    """Linear-interpolated percentile, matching `statistics.quantiles` style."""
    if not values:
        return 0.0
    s = sorted(values)
    k = (p / 100) * (len(s) - 1)
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    frac = k - lo
    return s[lo] * (1 - frac) + s[hi] * frac
