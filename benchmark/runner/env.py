"""Capture the environment at run time.

Records the exact versions of every tool the benchmark depends on, plus the
benchmark's own git commit. The manifest is updated in place before any
runs begin. This is what makes a run reproducible *and* falsifiable — every
result can be matched against the exact versions that produced it.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml


def _safe_run(cmd: list[str], timeout: float = 10.0) -> str:
    """Run a command, return trimmed stdout. Empty string on failure."""
    try:
        out = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return (out.stdout or "").strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""


def _ucode_version() -> str:
    out = _safe_run(["ucode", "--version"])
    return out


def _claude_version() -> str:
    out = _safe_run(["claude", "--version"])
    return out


def _databricks_cli_version() -> str:
    out = _safe_run(["databricks", "--version"])
    # The CLI prints "Databricks CLI vX.Y.Z"
    return out.replace("Databricks CLI", "").strip()


def _benchmark_git_commit(repo: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return (out.stdout or "").strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return ""


def _is_workspace_reachable(profile: str) -> bool:
    """Return whether the configured Databricks workspace accepts CLI auth."""
    out = _safe_run(
        [
            "databricks",
            "--profile",
            profile,
            "current-user",
            "me",
            "--output",
            "json",
        ],
        timeout=15,
    )
    if not out:
        return False
    try:
        json.loads(out)
    except json.JSONDecodeError:
        return False
    return True


def capture_env(manifest_path: Path, profile: str = "DEFAULT") -> dict[str, str]:
    """Update the manifest with the current environment and return it."""
    repo = manifest_path.parent
    env_block: dict[str, str] = {
        "python": platform.python_version(),
        "databricks_cli": _databricks_cli_version(),
        "ucode": _ucode_version(),
        "claude_code": _claude_version(),
        "os": platform.system(),
        "os_release": platform.release(),
        "benchmark_git_commit": _benchmark_git_commit(repo),
        "workspace_region": "",  # filled by caller when known
        "workspace_cloud": "",   # filled by caller when known
        "captured_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }

    workspace_reachable = _is_workspace_reachable(profile)

    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    data["environment"] = env_block
    data.setdefault("workspace", {})
    data["workspace"]["workspace_reachable"] = workspace_reachable

    # Atomic write to avoid corrupting the manifest on crash.
    tmp = manifest_path.with_suffix(".yaml.tmp")
    tmp.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    tmp.replace(manifest_path)
    return env_block


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: env.py <manifest.yaml> [profile]", file=sys.stderr)
        sys.exit(2)
    profile = sys.argv[2] if len(sys.argv) > 2 else "DEFAULT"
    captured = capture_env(Path(sys.argv[1]), profile=profile)
    print(json.dumps(captured, indent=2))
