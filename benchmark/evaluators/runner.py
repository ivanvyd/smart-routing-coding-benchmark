"""Run the per-task verifier in an isolated worktree.

Each task declares a `verifier` command (e.g. `pytest -q tests/`) and a
`forbidden_modifications` list (paths the agent MUST NOT touch). The runner
executes the verifier, captures its output, and produces a structured report:

  {
    "passed": bool,
    "message": str,           # short reason
    "verifier_exit_code": int,
    "verifier_stdout_tail": str,
    "verifier_stderr_tail": str,
    "forbidden_modifications_detected": [str, ...],
    "required_files_missing": [str, ...],
    "duration_seconds": float,
  }

The agent is considered to have passed the task iff `passed` is true.
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

_TAIL_CHARS = 4000
_VERIFIER_TIMEOUT_SECONDS = 600


def _resolve_bash() -> tuple[str, str]:
    """Pick a bash binary and the path-mount style it uses.

    On Windows there are three bashes on PATH: Git-Bash, the WSL interop
    stub, and a WindowsApps stub. The bash subprocess on Windows actually
    picks up depends on Win32 PATH lookup, not the interactive shell, so
    we prefer Git-Bash explicitly when it exists. The mount style is
    decided by probing the resolved bash itself: Git-Bash sees /c/...,
    WSL bash sees /mnt/c/.... This is computed once at module import.
    """
    bash = shutil.which("bash") or "bash"
    for cand in (r"C:\Program Files\Git\usr\bin\bash.exe", r"C:\Program Files\Git\bin\bash.exe"):
        if Path(cand).exists():
            bash = cand
            break
    probe = subprocess.run(
        [
            bash,
            "-c",
            "if [ -e /c/Python314/python.exe ]; then echo G; "
            "elif [ -e /mnt/c/Python314/python.exe ]; then echo W; "
            "else echo N; fi",
        ],
        capture_output=True,
        text=True,
        timeout=5,
    )
    mount = "wsl" if probe.stdout.strip() == "W" else "git"
    return bash, mount


_BASH_BIN, _BASH_MOUNT = _resolve_bash()


def _to_bash_path(p: Path) -> str:
    s = str(p).replace("\\", "/")
    if len(s) >= 2 and s[1] == ":":
        drive = s[0].lower()
        rest = s[2:].lstrip("/")
        return f"/mnt/{drive}/{rest}" if _BASH_MOUNT == "wsl" else f"/{drive}/{rest}"
    return s


def _run_in_bash(
    command: str, cwd: Path, env: dict[str, str], timeout: int
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_BASH_BIN, "-c", f"cd {shlex.quote(_to_bash_path(cwd))} && {command}"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _rewrite_python_invocation(verifier: str, python_exe: str) -> str:
    """Replace a leading `python ` invocation with the absolute path.

    Task verifiers are simple commands like `python -m pytest -q tests/`.
    We rewrite the leading `python` to the absolute path so the bash
    subshell always finds the same interpreter that ran the runner.
    Does not touch mid-string occurrences.
    """
    pattern = re.compile(r"(^|\s|;|&&|\|\|)python(\s)")
    return pattern.sub(lambda m: f"{m.group(1)}{python_exe}{m.group(2)}", verifier, count=1)


def _truncate(s: str, n: int = _TAIL_CHARS) -> str:
    if len(s) <= n:
        return s
    return "...[truncated]...\n" + s[-n:]


def _check_forbidden(task_repo: Path, base_commit: str, forbidden: list[str]) -> list[str]:
    """Return any forbidden files the agent modified/created.

    Git's ``--relative`` option reports paths as the agent sees them inside
    the task repository, so patterns such as ``tests/**`` match correctly.
    """
    if not forbidden:
        return []
    out = subprocess.run(
        [
            "git",
            "-C",
            str(task_repo),
            "diff",
            "--name-only",
            "--relative",
            "--diff-filter=ACMRT",
            base_commit,
            "--",
            ".",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    changed = {line.strip() for line in out.stdout.splitlines() if line.strip()}
    return sorted(p for p in changed if any(_matches(p, f) for f in forbidden))


def _matches(path: str, pattern: str) -> bool:
    """Glob-style match: '**' matches any depth, '*' any segment chars."""
    regex = re.escape(pattern).replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
    return re.fullmatch(regex, path) is not None


def _check_required(task_repo_root: Path, required: list[str]) -> list[str]:
    return [p for p in required if not (task_repo_root / p).exists()]


def run_verifier(task: dict[str, Any], worktree: Path) -> dict[str, Any]:
    """Run the deterministic verifier inside the task repository.

    ``worktree`` is retained as the public parameter name for compatibility,
    but the runner passes the nested task repository as this path.
    """
    t0 = time.monotonic()
    base_commit = task.get("_base_commit", "HEAD")
    forbidden = task.get("forbidden_modifications", []) or []
    required = task.get("required_files", []) or []
    task_repo = worktree

    forbidden_hits = _check_forbidden(task_repo, base_commit, forbidden)
    missing_required = _check_required(task_repo, required)

    verifier = task.get("verifier", "").strip()
    if not verifier:
        return {
            "passed": False,
            "message": "task is missing a verifier",
            "verifier_exit_code": -1,
            "verifier_stdout_tail": "",
            "verifier_stderr_tail": "",
            "forbidden_modifications_detected": forbidden_hits,
            "required_files_missing": missing_required,
            "duration_seconds": round(time.monotonic() - t0, 3),
        }

    env = os.environ.copy()
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    env.setdefault("NO_COLOR", "1")
    # Rewrite a leading `python` in the verifier to the absolute path of
    # THIS interpreter so the bash subshell doesn't pick up a stale alias.
    python_abs = shlex.quote(_to_bash_path(Path(sys.executable).resolve()))
    rewritten = _rewrite_python_invocation(verifier, python_abs)
    try:
        proc = _run_in_bash(
            rewritten,
            cwd=task_repo,
            env=env,
            timeout=_VERIFIER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        duration = round(time.monotonic() - t0, 3)
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {
            "passed": False,
            "message": f"verifier timed out after {_VERIFIER_TIMEOUT_SECONDS}s",
            "verifier_exit_code": 124,
            "verifier_stdout_tail": _truncate(stdout),
            "verifier_stderr_tail": _truncate(stderr),
            "verifier_command": verifier,
            "verifier_invocation": shlex.quote(verifier),
            "forbidden_modifications_detected": forbidden_hits,
            "required_files_missing": missing_required,
            "duration_seconds": duration,
        }
    duration = round(time.monotonic() - t0, 3)

    if forbidden_hits or missing_required:
        passed = False
        msg_parts: list[str] = []
        if forbidden_hits:
            msg_parts.append(f"forbidden modifications: {forbidden_hits}")
        if missing_required:
            msg_parts.append(f"missing required files: {missing_required}")
        if proc.returncode != 0:
            msg_parts.append(f"verifier exit={proc.returncode}")
        message = "; ".join(msg_parts) or "verifier failed"
    else:
        passed = proc.returncode == 0
        message = "verifier passed" if passed else f"verifier exit={proc.returncode}"

    return {
        "passed": passed,
        "message": message,
        "verifier_exit_code": proc.returncode,
        "verifier_stdout_tail": _truncate(proc.stdout),
        "verifier_stderr_tail": _truncate(proc.stderr),
        "verifier_command": verifier,
        "verifier_invocation": shlex.quote(verifier),
        "forbidden_modifications_detected": forbidden_hits,
        "required_files_missing": missing_required,
        "duration_seconds": duration,
    }
