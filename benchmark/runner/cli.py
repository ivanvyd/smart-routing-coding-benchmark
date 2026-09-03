"""Top-level CLI for the benchmark runner.

Examples:
  # Capture environment and run the full benchmark across all three arms.
  src-bench run --manifest benchmark/manifest.yaml

  # Dry-run (does not invoke ucode or the client router).
  src-bench run --manifest benchmark/manifest.yaml --dry-run --arm FIXED_STRONG

  # Capture environment only.
  src-bench capture-env --manifest benchmark/manifest.yaml
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

import yaml

from .env import capture_env
from .runner import Runner, RunResult


class _GateResult(Protocol):
    task_passed: bool
    routing_blocker: str | None
    selected_model: str | None


def _load_tasks(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return list(manifest["tasks"])


def _maybe_shuffle(tasks: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    shuffled = list(tasks)
    rng.shuffle(shuffled)
    return shuffled


def _gate_failure(results_by_arm: Mapping[str, Sequence[_GateResult]]) -> str | None:
    """Return the reason a full run must stop, or None when its smoke gate passed."""
    routing = results_by_arm.get("CLIENT_ROUTING")
    if routing:
        result = routing[0]
        if result.routing_blocker:
            return f"CLIENT_ROUTING blocked: {result.routing_blocker}"
        if not result.selected_model:
            return "CLIENT_ROUTING did not record a selected model"

    for arm, results in results_by_arm.items():
        if len(results) != 1 or not results[0].task_passed:
            return f"{arm} smoke verifier did not pass"
    return None


def cmd_capture_env(args: argparse.Namespace) -> int:
    capture_env(Path(args.manifest), profile=args.profile)
    # Auto-commit the manifest change so `src-bench run`'s clean-tree guard
    # is not tripped by capture-env's own output. capture-env is config,
    # not agent work; committing it is the right contract.
    #
    # We invoke git from the manifest's parent directory with just the
    # basename as the pathspec, so this works regardless of the cwd the
    # user is in when they ran the CLI.
    manifest_path = Path(args.manifest).resolve()
    git_cwd = manifest_path.parent
    manifest_name = manifest_path.name
    if subprocess.run(
        ["git", "-C", str(git_cwd), "diff", "--quiet", "--", manifest_name],
        check=False,
    ).returncode != 0:
        subprocess.run(
            ["git", "-C", str(git_cwd), "add", "--", manifest_name],
            check=True,
        )
        subprocess.run(
            [
                "git", "-C", str(git_cwd), "commit", "-q",
                "-m", "chore(manifest): capture-env",
                "--", manifest_name,
            ],
            check=True,
        )
    print(json.dumps({"captured": True, "manifest": args.manifest}, indent=2))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest)
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    runner = Runner(workspace_root=Path(args.workspace), manifest_path=manifest_path)

    tasks = _load_tasks(manifest)
    if args.task:
        wanted = {t for t in args.task}
        tasks = [t for t in tasks if t["id"] in wanted]
    if manifest["execution"].get("randomize_order", True):
        tasks = _maybe_shuffle(tasks, manifest["execution"].get("random_seed", 42))

    arms = [a["id"] for a in manifest["arms"]]
    if args.arm:
        arms = [a for a in arms if a == args.arm]

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    # The canonical smoke task prevents an unavailable model or selector from
    # becoming 24 invalid rows.
    gate_results: dict[str, list[RunResult]] = {}
    if not args.dry_run and args.task is None and "CLIENT_ROUTING" in arms:
        smoke_task = next((task for task in tasks if task["id"] == "easy-001"), None)
        if smoke_task is None:
            raise ValueError("full runs require the easy-001 smoke task")
        for arm in arms:
            arm_results = runner.run_all(
                arm=arm,
                tasks=[smoke_task],
                results_dir=results_dir,
                profile=args.profile,
                dry_run=False,
            )
            gate_results[arm] = arm_results
            Runner.dump_results(
                arm_results, results_dir / "normalized" / f"{arm}.jsonl"
            )
            print(f"[src-bench] {arm}: smoke gate -> easy-001")

        failure = _gate_failure(gate_results)
        if failure:
            print(f"[src-bench] full matrix stopped: {failure}", file=sys.stderr)
            return 2
        tasks = [task for task in tasks if task["id"] != "easy-001"]

    for arm in arms:
        arm_results = runner.run_all(
            arm=arm,
            tasks=tasks,
            results_dir=results_dir,
            profile=args.profile,
            dry_run=args.dry_run,
        )
        if arm in gate_results:
            arm_results = [*gate_results[arm], *arm_results]
        out = results_dir / "normalized" / f"{arm}.jsonl"
        Runner.dump_results(arm_results, out)
        print(f"[src-bench] {arm}: {len(arm_results)} runs -> {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="src-bench")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_cap = sub.add_parser("capture-env", help="update manifest with current env")
    p_cap.add_argument("--manifest", required=True)
    p_cap.add_argument("--profile", default="DEFAULT")
    p_cap.set_defaults(func=cmd_capture_env)

    p_run = sub.add_parser("run", help="run the benchmark")
    p_run.add_argument("--manifest", required=True)
    p_run.add_argument("--workspace", default=".")
    p_run.add_argument("--results-dir", default="results")
    p_run.add_argument("--profile", default="DEFAULT")
    p_run.add_argument(
        "--arm",
        default=None,
        help="FIXED_STRONG | FIXED_CHEAP | CLIENT_ROUTING",
    )
    p_run.add_argument("--task", action="append", default=None, help="restrict to task ids")
    p_run.add_argument("--dry-run", action="store_true")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
