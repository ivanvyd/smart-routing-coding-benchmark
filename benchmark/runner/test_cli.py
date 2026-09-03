from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import yaml

from benchmark.runner import cli


def test_gate_accepts_passing_fixed_arms_and_selected_client_model() -> None:
    fixed = SimpleNamespace(
        task_passed=True,
        routing_blocker=None,
        selected_model="model",
    )
    routing = SimpleNamespace(
        task_passed=True,
        routing_blocker=None,
        selected_model="system.ai.claude-haiku-4-5",
    )

    assert (
        cli._gate_failure(
            {
                "FIXED_STRONG": [fixed],
                "FIXED_CHEAP": [fixed],
                "CLIENT_ROUTING": [routing],
            }
        )
        is None
    )


def test_full_run_stops_after_failed_client_routing_smoke(
    monkeypatch, tmp_path: Path
) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "execution": {"randomize_order": False},
                "arms": [
                    {"id": "FIXED_STRONG"},
                    {"id": "FIXED_CHEAP"},
                    {"id": "CLIENT_ROUTING"},
                ],
                "tasks": [
                    {"id": "easy-001"},
                    {"id": "easy-002"},
                ],
            }
        ),
        encoding="utf-8",
    )
    calls: list[tuple[str, list[str]]] = []

    class FakeRunner:
        def __init__(self, workspace_root: Path, manifest_path: Path) -> None:
            pass

        def run_all(self, *, arm, tasks, results_dir, profile, dry_run):
            calls.append((arm, [task["id"] for task in tasks]))
            blocker = "router request failed" if arm == "CLIENT_ROUTING" else None
            return [
                SimpleNamespace(
                    task_passed=arm != "CLIENT_ROUTING",
                    routing_blocker=blocker,
                    selected_model=None if blocker else "model",
                )
            ]

        @staticmethod
        def dump_results(results, out_path: Path) -> None:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text("smoke\n", encoding="utf-8")

    monkeypatch.setattr(cli, "Runner", FakeRunner)
    args = Namespace(
        manifest=str(manifest_path),
        workspace=str(tmp_path),
        task=None,
        arm=None,
        results_dir=str(tmp_path / "results"),
        profile="test",
        dry_run=False,
    )

    assert cli.cmd_run(args) == 2
    assert calls == [
        ("FIXED_STRONG", ["easy-001"]),
        ("FIXED_CHEAP", ["easy-001"]),
        ("CLIENT_ROUTING", ["easy-001"]),
    ]
