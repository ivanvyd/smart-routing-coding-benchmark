from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmark.runner.runner import (
    Runner,
    _read_current_ucode_profile,
    _TaskContext,
)


class _CompletedProcess:
    def wait(self, timeout: int) -> int:
        return 0


def test_reads_profile_from_ucode_current_workspace(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "current_workspace": "https://trial.example",
                "workspaces": {
                    "https://trial.example": {"profile": "benchmark-trial-work"},
                    "https://client.example": {"profile": "client"},
                },
            }
        ),
        encoding="utf-8",
    )

    assert _read_current_ucode_profile(state_path) == "benchmark-trial-work"


def test_rejects_profile_that_does_not_match_ucode_state(
    monkeypatch, tmp_path: Path
) -> None:
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "current_workspace": "https://client.example",
                "workspaces": {"https://client.example": {"profile": "client"}},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("benchmark.runner.runner._ucode_state_path", lambda: state_path)
    runner = Runner(Path("."), Path("benchmark/manifest.yaml"))

    with pytest.raises(RuntimeError, match="not bound to the requested"):
        runner._ensure_ucode_profile("benchmark-trial-work")


def test_exec_forces_utf8_for_redirected_windows_cli_output(
    monkeypatch, tmp_path: Path
) -> None:
    captured_env: dict[str, str] = {}

    def fake_popen(*args, **kwargs):
        captured_env.update(kwargs["env"])
        return _CompletedProcess()

    monkeypatch.setattr("benchmark.runner.runner.subprocess.Popen", fake_popen)
    runner = Runner(Path("."), Path("benchmark/manifest.yaml"))

    exit_code = runner._exec(
        ["ucode", "--version"],
        tmp_path / "stdout.txt",
        tmp_path / "stderr.txt",
        Path("."),
    )

    assert exit_code == 0
    assert captured_env["PYTHONUTF8"] == "1"
    assert captured_env["PYTHONIOENCODING"] == "utf-8"


def test_fixed_arms_use_current_system_ai_model_ids() -> None:
    runner = Runner(Path("."), Path("benchmark/manifest.yaml"))

    strong = runner._build_invocation(
        "prompt",
        runner._arm_model("FIXED_STRONG"),
    )
    cheap = runner._build_invocation(
        "prompt",
        runner._arm_model("FIXED_CHEAP"),
    )

    assert strong[:3] == ["ucode", "claude", "--dangerously-skip-permissions"]
    assert cheap[:3] == ["ucode", "claude", "--dangerously-skip-permissions"]
    assert strong[3:5] == ["--model", "system.ai.claude-sonnet-5"]
    assert cheap[3:5] == ["--model", "system.ai.claude-haiku-4-5"]


def test_client_routing_dry_run_selects_cheap_model() -> None:
    runner = Runner(Path("."), Path("benchmark/manifest.yaml"))

    decision = runner._route_task(
        {"title": "Task", "prompt": "Fix one value."},
        "benchmark-work",
        dry_run=True,
    )
    invocation = runner._build_invocation(
        "prompt",
        decision.selected_model,
    )

    assert invocation[:5] == [
        "ucode",
        "claude",
        "--dangerously-skip-permissions",
        "--model",
        "system.ai.claude-haiku-4-5",
    ]


def test_run_one_executes_and_evaluates_inside_task_repo(
    monkeypatch, tmp_path: Path
) -> None:
    worktree = tmp_path / "worktree"
    task_repo = worktree / "tasks" / "easy" / "easy-001" / "repo"
    task_repo.mkdir(parents=True)
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        "execution:\n  wall_clock_timeout_seconds: 30\n"
        "arms:\n- id: FIXED_STRONG\n  model: strong\n",
        encoding="utf-8",
    )
    runner = Runner(tmp_path, manifest_path)
    observed: dict[str, Path] = {}

    monkeypatch.setattr(runner, "_create_worktree", lambda ctx, run_id: worktree)
    monkeypatch.setattr(
        runner,
        "_load_task",
        lambda ctx: {
            "title": "Task",
            "prompt": "Fix it.",
            "verifier": "python -m pytest -q tests/",
        },
    )
    monkeypatch.setattr(runner, "_build_invocation", lambda *args: ["agent"])

    def fake_run_agent(invocation, paths, profile, dry_run):
        observed["agent"] = paths.worktree
        paths.stdout.write_text("done", encoding="utf-8")
        paths.stderr.write_text("", encoding="utf-8")
        return 0

    monkeypatch.setattr(runner, "_run_agent", fake_run_agent)
    monkeypatch.setattr(
        runner,
        "_record_diff",
        lambda root, base, path: path.write_text("(no changes)\n", encoding="utf-8"),
    )
    monkeypatch.setattr(runner, "_destroy_worktree", lambda path: None)

    def fake_verifier(*, task, worktree):
        observed["verifier"] = worktree
        return {"passed": True, "message": "ok"}

    monkeypatch.setattr("benchmark.runner.runner.run_verifier", fake_verifier)
    context = _TaskContext(
        arm="FIXED_STRONG",
        task={"id": "easy-001", "difficulty": "easy", "path": "tasks/easy/easy-001"},
        base_commit="base",
        results_dir=tmp_path / "results",
        profile="benchmark-work",
        dry_run=False,
    )

    result = runner._run_one(context)

    assert result.task_passed is True
    assert observed == {"agent": task_repo, "verifier": task_repo}
