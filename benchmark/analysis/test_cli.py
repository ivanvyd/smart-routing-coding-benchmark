from pathlib import Path

import pytest

from benchmark.analysis.cli import _applicable_exclusions, _load_exclusions


def test_load_exclusions_returns_task_reasons(tmp_path: Path) -> None:
    path = tmp_path / "exclusions.yaml"
    path.write_text(
        "applies_to_base_commit: abc123\ntasks:\n  easy-004:\n    reason: broken verifier\n",
        encoding="utf-8",
    )

    assert _load_exclusions(str(path)) == (
        "abc123",
        {"easy-004": "broken verifier"},
    )


def test_exclusions_apply_only_to_the_exact_run_commit() -> None:
    exclusions = {"easy-004": "broken verifier"}

    assert _applicable_exclusions("abc123", exclusions, {"abc123"}) == exclusions
    assert _applicable_exclusions("abc123", exclusions, {"different"}) == {}


def test_analysis_rejects_mixed_base_commits() -> None:
    with pytest.raises(ValueError, match="multiple base commits"):
        _applicable_exclusions("abc123", {}, {"abc123", "different"})
