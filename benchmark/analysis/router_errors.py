"""Identify candidate over-routing / under-routing cases.

These are not claimed as proof the router is wrong. They are surfaced for
manual inspection, with a short case study per finding.
"""

from __future__ import annotations

from typing import Any


def find_candidates(
    runs_by_arm: dict[str, list[dict[str, Any]]],
    attributed_by_arm: dict[str, list[dict[str, Any]]],
    cost_metric: str = "total_estimated_cost",
) -> dict[str, list[dict[str, Any]]]:
    """Return candidate over-routing and under-routing cases.

    Over-routing candidate: the client router chose a substantially more
    expensive model than the cheap baseline while the cheap baseline
    succeeded. We compare total cost per task, not model list price, so
    the candidate set naturally reflects token usage patterns too.

    Under-routing candidate: the client router chose the cheaper model and the
    task failed, while the strong baseline succeeded.
    """
    tasks = {r["task_id"] for rs in runs_by_arm.values() for r in rs}
    out: dict[str, list[dict[str, Any]]] = {"over_routing": [], "under_routing": []}

    for tid in sorted(tasks):
        sm = _first(runs_by_arm, "CLIENT_ROUTING", tid)
        weak = _first(runs_by_arm, "FIXED_CHEAP", tid)
        strong = _first(runs_by_arm, "FIXED_STRONG", tid)
        if not sm or not weak or not strong:
            continue
        sm_attr = _first(attributed_by_arm, "CLIENT_ROUTING", tid)
        weak_attr = _first(attributed_by_arm, "FIXED_CHEAP", tid)
        strong_attr = _first(attributed_by_arm, "FIXED_STRONG", tid)

        sm_cost = (sm_attr or {}).get(cost_metric)
        weak_cost = (weak_attr or {}).get(cost_metric)
        strong_cost = (strong_attr or {}).get(cost_metric)
        sm_passed = sm.get("task_passed")
        weak_passed = weak.get("task_passed")
        strong_passed = strong.get("task_passed")
        selected_cheap = sm.get("selected_model") == weak.get("selected_model")
        selected_strong = sm.get("selected_model") == strong.get("selected_model")

        # Candidate over-routing: cheap baseline succeeded, client routing
        # spent >= 2x cheap baseline cost.
        if (
            weak_passed
            and selected_strong
            and isinstance(sm_cost, int | float)
            and isinstance(weak_cost, int | float)
            and weak_cost > 0
            and sm_cost >= 2 * weak_cost
        ):
            out["over_routing"].append(
                {
                    "task_id": tid,
                    "selected_model": sm.get("selected_model"),
                    "cheap_model": (weak_attr or {}).get("models_used", []),
                    "result": "passed" if sm_passed else "failed",
                    "cheap_result": "passed" if weak_passed else "failed",
                    "routed_cost": sm_cost,
                    "cheap_cost": weak_cost,
                    "strong_cost": strong_cost,
                    "routed_tokens": (sm_attr or {}).get("total_tokens"),
                    "cheap_tokens": (weak_attr or {}).get("total_tokens"),
                    "note": (
                        "The client router selected a more expensive model on a "
                        "task the cheap baseline passed. Manual inspection "
                        "required to determine whether the router was right."
                    ),
                }
            )

        # Candidate under-routing: strong baseline passed, client routing failed.
        if strong_passed and selected_cheap and not sm_passed:
            out["under_routing"].append(
                {
                    "task_id": tid,
                    "selected_model": sm.get("selected_model"),
                    "strong_model": (strong_attr or {}).get("models_used", []),
                    "result": "failed",
                    "strong_result": "passed",
                    "routed_cost": sm_cost,
                    "strong_cost": strong_cost,
                    "note": (
                        "The client-routed arm failed a task the strong baseline passed. "
                        "Manual inspection required."
                    ),
                }
            )
    return out


def _first(
    by_arm: dict[str, list[dict[str, Any]]], arm: str, task_id: str
) -> dict[str, Any] | None:
    for r in by_arm.get(arm, []):
        if r["task_id"] == task_id:
            return r
    return None
