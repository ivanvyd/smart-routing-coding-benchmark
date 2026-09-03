"""Top-level analysis CLI.

Usage:
  src-analyze --results-dir results --out-dir results
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from ..io import load_jsonl_by_arm
from .charts import render_all
from .metrics import NOT_MEASURED, per_arm_metrics
from .router_errors import find_candidates


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="src-analyze")
    p.add_argument("--results-dir", default="results")
    p.add_argument("--manifest", default="benchmark/manifest.yaml")
    p.add_argument("--exclusions", default="benchmark/exclusions.yaml")
    args = p.parse_args(argv)

    results_dir = Path(args.results_dir)
    manifest_arms = _manifest_arms(args.manifest)
    allowed_arms = {arm["id"] for arm in manifest_arms}
    runs_by_arm = {
        arm: runs
        for arm, runs in load_jsonl_by_arm(results_dir / "normalized").items()
        if arm in allowed_arms
    }
    attributed_by_arm = {
        arm: runs
        for arm, runs in load_jsonl_by_arm(results_dir / "attributed").items()
        if arm in allowed_arms
    }
    exclusion_commit, configured_exclusions = _load_exclusions(args.exclusions)
    run_commits: set[str | None] = set()
    for runs in runs_by_arm.values():
        for run in runs:
            commit = run.get("git_base_commit")
            run_commits.add(str(commit) if commit is not None else None)
    exclusions = _applicable_exclusions(
        exclusion_commit,
        configured_exclusions,
        run_commits,
    )
    if exclusions:
        runs_by_arm = {
            arm: [run for run in runs if run.get("task_id") not in exclusions]
            for arm, runs in runs_by_arm.items()
        }
        attributed_by_arm = {
            arm: [run for run in runs if run.get("task_id") not in exclusions]
            for arm, runs in attributed_by_arm.items()
        }

    if not runs_by_arm:
        print("[src-analyze] no normalized runs found, emitting NOT_MEASURED charts")
        metrics_by_arm = {arm["id"]: {"task_success_rate": NOT_MEASURED} for arm in manifest_arms}
    else:
        metrics_by_arm = {}
        for arm_config in manifest_arms:
            arm_id = arm_config["id"]
            if arm_id not in runs_by_arm:
                continue
            metrics_by_arm[arm_id] = per_arm_metrics(
                arm_id,
                runs_by_arm[arm_id],
                attributed_by_arm.get(arm_id),
            )

    cases = find_candidates(runs_by_arm, attributed_by_arm)
    render_all(
        metrics_by_arm=metrics_by_arm,
        routing_runs=runs_by_arm.get("CLIENT_ROUTING", []),
        cases=cases,
        out_dir=results_dir / "figures",
    )
    tables_dir = results_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    (tables_dir / "summary.json").write_text(
        json.dumps(
            {
                "excluded_tasks": exclusions,
                "metrics": metrics_by_arm,
                "router_error_cases": cases,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    print(f"[src-analyze] wrote figures to {results_dir / 'figures'}")
    print(f"[src-analyze] wrote summary to {tables_dir / 'summary.json'}")
    return 0


def _manifest_arms(path: str) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    return list(yaml.safe_load(p.read_text(encoding="utf-8")).get("arms", []))


def _load_exclusions(path: str) -> tuple[str | None, dict[str, str]]:
    exclusion_path = Path(path)
    if not exclusion_path.exists():
        return None, {}
    payload = yaml.safe_load(exclusion_path.read_text(encoding="utf-8")) or {}
    tasks = payload.get("tasks", {})
    return (
        payload.get("applies_to_base_commit"),
        {
            str(task_id): str(details.get("reason", "excluded"))
            for task_id, details in tasks.items()
        },
    )


def _applicable_exclusions(
    exclusion_commit: str | None,
    exclusions: dict[str, str],
    run_commits: set[str | None],
) -> dict[str, str]:
    if len(run_commits) > 1:
        raise ValueError(f"normalized results span multiple base commits: {run_commits}")
    if exclusion_commit is None:
        return exclusions
    return exclusions if run_commits == {exclusion_commit} else {}


if __name__ == "__main__":
    sys.exit(main())
