import subprocess
from pathlib import Path

import pytest

from benchmark.evaluators import runner as evaluator
from benchmark.evaluators.runner import _check_forbidden


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_forbidden_paths_are_relative_to_nested_task_repo(tmp_path: Path) -> None:
    repo = tmp_path / "workspace"
    task_repo = repo / "tasks" / "medium" / "sample" / "repo"
    tests = task_repo / "tests"
    tests.mkdir(parents=True)
    source = task_repo / "src.py"
    fixture = tests / "fixture.txt"
    source.write_text("before\n", encoding="utf-8")
    fixture.write_text("before\n", encoding="utf-8")
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    base = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    source.write_text("after\n", encoding="utf-8")
    fixture.write_text("after\n", encoding="utf-8")

    assert _check_forbidden(task_repo, base, ["tests/**"]) == ["tests/fixture.txt"]


def test_verifier_timeout_is_a_recorded_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_timeout(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired("pytest", 600, output="partial output")

    monkeypatch.setattr(evaluator, "_run_in_bash", raise_timeout)

    report = evaluator.run_verifier(
        {"verifier": "python -m pytest -q", "required_files": []},
        tmp_path,
    )

    assert report["passed"] is False
    assert report["verifier_exit_code"] == 124
    assert report["message"] == "verifier timed out after 600s"
    assert report["verifier_stdout_tail"] == "partial output"
