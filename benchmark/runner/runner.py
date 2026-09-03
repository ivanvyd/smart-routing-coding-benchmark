"""Run a single (arm, task) pair in an isolated worktree."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import time
import uuid
from contextlib import suppress
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from benchmark.evaluators.runner import run_verifier
from benchmark.runner.router import (
    POLICY_ID,
    POLICY_SHA256,
    RoutingDecision,
    RoutingError,
    select_model,
)


@dataclass
class RunResult:
    """Everything we know about one (arm, task) execution."""

    run_id: str
    arm: str
    task_id: str
    task_difficulty: str
    started_at: str
    finished_at: str
    duration_seconds: float
    exit_code: int | None
    stdout_path: str
    stderr_path: str
    diff_path: str
    eval_report_path: str
    task_passed: bool
    eval_message: str
    ucode_invocation: list[str]
    git_base_commit: str
    git_head_commit: str
    dry_run: bool = False
    selected_model: str | None = None
    routing_policy: str | None = None
    routing_policy_sha256: str | None = None
    routing_reason: str | None = None
    router_model: str | None = None
    router_duration_seconds: float | None = None
    router_input_tokens: int | None = None
    router_output_tokens: int | None = None
    routing_blocker: str | None = None


@dataclass
class _TaskContext:
    """Everything _run_one needs to do its job, packed so the signature stays small."""

    arm: str
    task: dict[str, Any]
    base_commit: str
    results_dir: Path
    profile: str
    dry_run: bool


def _check_pinned_models(manifest: dict[str, Any]) -> None:
    """Refuse to run if a FIXED_* arm has no model pinned.

    An unpinned FIXED arm silently degenerates into the same default
    the gateway would choose, defeating the point of the arm.
    """
    for arm in manifest.get("arms", []):
        if arm.get("id") in {"FIXED_STRONG", "FIXED_CHEAP"}:
            m = arm.get("model")
            if not m or not isinstance(m, str) or not m.strip():
                raise ValueError(
                    f"arm {arm['id']!r} has no model pinned. "
                    f"Fill in `model:` in benchmark/manifest.yaml before running. "
                    f"See docs/reproduction.md for requirements."
                )


def _ucode_state_path() -> Path:
    return Path.home() / ".ucode" / "state.json"


def _read_current_ucode_profile(state_path: Path) -> str | None:
    """Return the CLI profile bound to ucode's current workspace.

    ``DATABRICKS_CONFIG_PROFILE`` controls the Databricks CLI, but ucode selects
    its workspace from its own state file. Treat the two as separate sources of
    truth so a benchmark cannot silently run against the wrong workspace.
    """
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    current_workspace = state.get("current_workspace")
    workspaces = state.get("workspaces")
    if not isinstance(current_workspace, str) or not isinstance(workspaces, dict):
        return None
    workspace_state = workspaces.get(current_workspace)
    if not isinstance(workspace_state, dict):
        return None
    profile = workspace_state.get("profile")
    return profile.strip() if isinstance(profile, str) and profile.strip() else None


class Runner:
    """Run tasks in isolated git worktrees.

    Usage:
        runner = Runner(workspace_root=Path("."), manifest_path=Path("benchmark/manifest.yaml"))
        results = runner.run_all(arm="FIXED_STRONG", tasks=tasks)
    """

    def __init__(self, workspace_root: Path, manifest_path: Path) -> None:
        self.workspace_root = workspace_root
        self.manifest_path = manifest_path
        self.manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(UTC).isoformat(timespec="seconds")

    def _git(self, *args: str, cwd: Path | None = None) -> str:
        full = ["git", *(["-C", str(cwd)] if cwd is not None else []), *args]
        out = subprocess.run(
            full,
            capture_output=True,
            text=True,
            check=False,
        )
        if out.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {out.stderr.strip()}")
        return out.stdout.strip()

    def _git_unchecked(self, *args: str, cwd: Path | None = None) -> int:
        """Like _git, but returns the exit code instead of raising."""
        full = ["git", *(["-C", str(cwd)] if cwd is not None else []), *args]
        return subprocess.run(full, capture_output=True, text=True, check=False).returncode

    def _base_commit(self) -> str:
        return self._git("rev-parse", "HEAD", cwd=self.workspace_root)

    def _ensure_clean(self) -> None:
        # `--untracked-files=no` excludes untracked files: a sidecar produced
        # by a prior arm's run (e.g. base_commit_<arm>.txt) is not an
        # agent-modified tracked file, so it should not block the next arm.
        # The contract is "no agent-modified tracked files before we begin."
        status = self._git(
            "status", "--porcelain", "--untracked-files=no", cwd=self.workspace_root
        )
        if status:
            raise RuntimeError(
                f"workspace {self.workspace_root} has uncommitted tracked changes:\n{status}\n"
                "Commit or stash before running the benchmark."
            )

    def _ensure_ucode_profile(self, profile: str) -> None:
        configured_profile = _read_current_ucode_profile(_ucode_state_path())
        if configured_profile != profile:
            raise RuntimeError(
                "ucode is not bound to the requested Databricks CLI profile "
                f"{profile!r}. Run `ucode configure --agents claude --profiles "
                f"{profile} --skip-validate` before starting the benchmark."
            )

    def run_all(
        self,
        arm: str,
        tasks: list[dict[str, Any]],
        results_dir: Path,
        profile: str = "DEFAULT",
        dry_run: bool = False,
    ) -> list[RunResult]:
        """Run every task under the given arm sequentially."""
        if arm not in {a["id"] for a in self.manifest["arms"]}:
            raise ValueError(f"unknown arm {arm!r}")
        if not dry_run:
            _check_pinned_models(self.manifest)
            self._ensure_ucode_profile(profile)
        self._ensure_clean()
        base_commit = self._base_commit()
        original_manifest = self.manifest_path.read_text(encoding="utf-8")
        self.manifest["execution"]["base_commit_at_run"] = base_commit
        self.manifest_path.write_text(
            yaml.safe_dump(self.manifest, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

        try:
            return [
                self._run_one(_TaskContext(arm, task, base_commit, results_dir, profile, dry_run))
                for task in tasks
            ]
        finally:
            # Restore the manifest so the workspace stays clean for the next
            # arm. The recorded commit is also written into results/tables
            # for reproducibility.
            self.manifest_path.write_text(original_manifest, encoding="utf-8")
            sidecar = results_dir / "tables" / f"base_commit_{arm}.txt"
            sidecar.parent.mkdir(parents=True, exist_ok=True)
            sidecar.write_text(base_commit + "\n", encoding="utf-8")

    def _run_one(self, ctx: _TaskContext) -> RunResult:
        run_id = uuid.uuid4().hex[:12]
        worktree = self._create_worktree(ctx, run_id)
        task_repo = worktree / ctx.task["path"] / "repo"
        run_dir = ctx.results_dir / "raw" / ctx.arm / ctx.task["id"] / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        paths = _RunPaths(worktree=task_repo, run_dir=run_dir)
        started_at = self._now_iso()
        t0 = time.monotonic()

        try:
            task_data = self._load_task(ctx)
            prompt = self._render_prompt(task_data)
            (task_repo / "TASK_PROMPT.md").write_text(prompt, encoding="utf-8")

            decision: RoutingDecision | None = None
            routing_blocker: str | None = None
            selected_model = self._arm_model(ctx.arm)
            if ctx.arm == "CLIENT_ROUTING":
                try:
                    decision = self._route_task(task_data, ctx.profile, ctx.dry_run)
                    selected_model = decision.selected_model
                except RoutingError as exc:
                    routing_blocker = str(exc)

            invocation: list[str] = []
            if routing_blocker:
                paths.stdout.write_text("", encoding="utf-8")
                paths.stderr.write_text(
                    f"[runner] client routing failed: {routing_blocker}\n",
                    encoding="utf-8",
                )
                exit_code = None
            else:
                invocation = self._build_invocation(prompt, selected_model)
                exit_code = self._run_agent(invocation, paths, ctx.profile, ctx.dry_run)

            self._record_diff(worktree, ctx.base_commit, paths.diff)
            eval_report = run_verifier(task=task_data, worktree=task_repo)
            paths.eval_report.write_text(
                json.dumps(eval_report, indent=2, sort_keys=True), encoding="utf-8"
            )

            return _make_run_result(
                ctx=ctx,
                run_id=run_id,
                paths=paths,
                started_at=started_at,
                t0=t0,
                exit_code=exit_code,
                invocation=invocation,
                eval_report=eval_report,
                selected_model=selected_model,
                decision=decision,
                routing_blocker=routing_blocker,
            )
        finally:
            self._destroy_worktree(worktree)

    def _create_worktree(self, ctx: _TaskContext, run_id: str) -> Path:
        worktree = self.workspace_root / ".worktrees" / f"{ctx.arm}-{ctx.task['id']}-{run_id}"
        self._git(
            "worktree",
            "add",
            "--detach",
            str(worktree),
            ctx.base_commit,
            cwd=self.workspace_root,
        )
        return worktree

    def _load_task(self, ctx: _TaskContext) -> dict[str, Any]:
        task_yaml = (self.workspace_root / ctx.task["path"] / "task.yaml").resolve()
        task = yaml.safe_load(task_yaml.read_text(encoding="utf-8"))
        if not isinstance(task, dict):
            raise ValueError(f"task file must contain a mapping: {task_yaml}")
        return task

    def _run_agent(
        self, invocation: list[str], paths: _RunPaths, profile: str, dry_run: bool
    ) -> int:
        if dry_run:
            paths.stdout.write_text(
                "[DRY-RUN] would invoke:\n  " + " ".join(shlex.quote(p) for p in invocation) + "\n",
                encoding="utf-8",
            )
            paths.stderr.write_text("[DRY-RUN] no agent executed\n", encoding="utf-8")
            return 0
        return self._exec(invocation, paths.stdout, paths.stderr, cwd=paths.worktree, profile=profile)

    def _render_prompt(self, task_data: dict[str, Any]) -> str:
        """Render the task prompt the agent receives.

        We send only the task prompt plus the verifier instruction. The agent
        has the worktree as its working directory; nothing else is included.
        """
        return (
            f"# Task: {task_data['title']}\n\n"
            f"{task_data['prompt'].strip()}\n\n"
            f"## Verification\n\n"
            f"You can verify your work locally with:\n\n"
            f"```\n{task_data['verifier'].strip()}\n```\n\n"
            f"When you are confident the task is complete, summarize what you "
            f"changed and stop.\n"
        )

    def _arm_model(self, arm: str) -> str | None:
        arm_cfg = next(a for a in self.manifest["arms"] if a["id"] == arm)
        model = arm_cfg.get("model")
        return model if isinstance(model, str) and model else None

    def _route_task(
        self, task_data: dict[str, Any], profile: str, dry_run: bool
    ) -> RoutingDecision:
        arm_cfg = next(
            a for a in self.manifest["arms"] if a["id"] == "CLIENT_ROUTING"
        )
        cheap_model = str(arm_cfg["candidate_models"]["cheap"])
        strong_model = str(arm_cfg["candidate_models"]["strong"])
        router_model = str(arm_cfg["router_model"])
        if dry_run:
            return RoutingDecision(
                selected_model=cheap_model,
                reason="dry-run selection",
                router_model=router_model,
                policy_id=POLICY_ID,
                policy_sha256=POLICY_SHA256,
                duration_seconds=0.0,
                input_tokens=0,
                output_tokens=0,
            )
        return select_model(
            title=str(task_data["title"]),
            task_prompt=str(task_data["prompt"]),
            profile=profile,
            router_model=router_model,
            cheap_model=cheap_model,
            strong_model=strong_model,
        )

    def _build_invocation(self, prompt: str, selected_model: str | None) -> list[str]:
        """Build one unattended Claude Code command pinned to a model."""
        cmd: list[str] = ["ucode", "claude", "--dangerously-skip-permissions"]
        if selected_model:
            cmd += ["--model", selected_model]
        cmd += ["--", prompt]
        return cmd

    def _exec(
        self,
        invocation: list[str],
        stdout_path: Path,
        stderr_path: Path,
        cwd: Path,
        profile: str = "DEFAULT",
        timeout: int | None = None,
    ) -> int:
        timeout = timeout or int(self.manifest["execution"]["wall_clock_timeout_seconds"])
        env = os.environ.copy()
        env["DATABRICKS_CONFIG_PROFILE"] = profile
        env["CI"] = "1"
        env["NO_COLOR"] = "1"
        env["PAGER"] = "cat"
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        with (
            stdout_path.open("w", encoding="utf-8", errors="replace") as out_f,
            stderr_path.open("w", encoding="utf-8", errors="replace") as err_f,
        ):
            proc = subprocess.Popen(
                invocation,
                cwd=str(cwd),
                env=env,
                stdout=out_f,
                stderr=err_f,
                stdin=subprocess.DEVNULL,
                text=True,
            )
            try:
                return proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                err_f.write(f"\n[runner] killed after {timeout}s timeout\n")
                return 124

    def _record_diff(self, worktree: Path, base_commit: str, diff_path: Path) -> None:
        diff = self._git("diff", "--binary", "--no-color", base_commit, cwd=worktree)
        if not diff:
            diff = "(no changes)\n"
        diff_path.write_text(diff, encoding="utf-8")

    def _destroy_worktree(self, worktree: Path) -> None:
        # Two passes: `worktree remove` is the proper path, `prune` is the
        # fallback for stale state. Either failing is non-fatal here, so we
        # check returncode rather than catching the RuntimeError.
        self._git_unchecked("worktree", "remove", "--force", str(worktree), cwd=self.workspace_root)
        self._git_unchecked("worktree", "prune", cwd=self.workspace_root)
        if worktree.exists():
            shutil.rmtree(worktree, ignore_errors=True)

    @staticmethod
    def dump_results(results: list[RunResult], out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(asdict(r), sort_keys=True) for r in results]
        out_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


@dataclass
class _RunPaths:
    """Where one run's artifacts go on disk."""

    worktree: Path
    run_dir: Path

    @property
    def stdout(self) -> Path:
        return self.run_dir / "stdout.txt"

    @property
    def stderr(self) -> Path:
        return self.run_dir / "stderr.txt"

    @property
    def diff(self) -> Path:
        return self.run_dir / "diff.patch"

    @property
    def eval_report(self) -> Path:
        return self.run_dir / "eval_report.json"


def _make_run_result(
    ctx: _TaskContext,
    run_id: str,
    paths: _RunPaths,
    started_at: str,
    t0: float,
    exit_code: int | None,
    invocation: list[str],
    eval_report: dict[str, Any],
    selected_model: str | None,
    decision: RoutingDecision | None,
    routing_blocker: str | None,
) -> RunResult:
    head_commit = "0" * 40
    if paths.worktree.exists():
        with suppress(Exception):
            head_commit = (
                subprocess.run(
                    ["git", "-C", str(paths.worktree), "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=False,
                ).stdout.strip()
                or head_commit
            )
    return RunResult(
        run_id=run_id,
        arm=ctx.arm,
        task_id=ctx.task["id"],
        task_difficulty=ctx.task.get("difficulty", "unknown"),
        started_at=started_at,
        finished_at=Runner._now_iso(),
        duration_seconds=round(time.monotonic() - t0, 3),
        exit_code=exit_code,
        stdout_path=str(paths.stdout),
        stderr_path=str(paths.stderr),
        diff_path=str(paths.diff),
        eval_report_path=str(paths.eval_report),
        task_passed=bool(eval_report.get("passed", False)),
        eval_message=str(eval_report.get("message", "")),
        ucode_invocation=invocation,
        git_base_commit=ctx.base_commit,
        git_head_commit=head_commit,
        dry_run=ctx.dry_run,
        selected_model=selected_model,
        routing_policy=decision.policy_id if decision else None,
        routing_policy_sha256=decision.policy_sha256 if decision else None,
        routing_reason=decision.reason if decision else None,
        router_model=decision.router_model if decision else None,
        router_duration_seconds=decision.duration_seconds if decision else None,
        router_input_tokens=decision.input_tokens if decision else None,
        router_output_tokens=decision.output_tokens if decision else None,
        routing_blocker=routing_blocker,
    )
