from __future__ import annotations

from pathlib import Path

import yaml

from benchmark.runner import env


def test_capture_env_preserves_workspace_metadata(monkeypatch, tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "environment": {},
                "workspace": {"access_mode": "test"},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(env, "_safe_run", lambda *args, **kwargs: '{"id": "user"}')
    monkeypatch.setattr(env, "_benchmark_git_commit", lambda repo: "commit")

    env.capture_env(manifest_path, profile="benchmark-work")

    captured = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert captured["workspace"]["workspace_reachable"] is True
    assert captured["workspace"]["access_mode"] == "test"
