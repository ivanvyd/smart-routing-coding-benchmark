from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from benchmark.runner.router import POLICY_SHA256, RoutingError, select_model


def test_select_model_returns_strong_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    response = {
        "content": [
            {
                "type": "text",
                "text": json.dumps(
                    {"choice": "strong", "reason": "The task changes concurrent state."}
                ),
            }
        ],
        "usage": {"input_tokens": 41, "output_tokens": 12},
    }

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=json.dumps(response), stderr="")

    monkeypatch.setattr("benchmark.runner.router.subprocess.run", fake_run)

    decision = select_model(
        title="Fix queue",
        task_prompt="Make queue updates thread safe.",
        profile="trial",
        router_model="system.ai.claude-haiku-4-5",
        cheap_model="system.ai.claude-haiku-4-5",
        strong_model="system.ai.claude-sonnet-5",
    )

    assert decision.selected_model == "system.ai.claude-sonnet-5"
    assert decision.reason == "The task changes concurrent state."
    assert decision.input_tokens == 41
    assert decision.output_tokens == 12
    assert decision.policy_sha256 == POLICY_SHA256


def test_select_model_accepts_fenced_json(monkeypatch: pytest.MonkeyPatch) -> None:
    response = {
        "content": [
            {
                "type": "text",
                "text": '```json\n{"choice":"cheap","reason":"One local edit."}\n```',
            }
        ]
    }
    monkeypatch.setattr(
        "benchmark.runner.router.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0, stdout=json.dumps(response), stderr=""
        ),
    )

    decision = select_model(
        title="Rename value",
        task_prompt="Rename one value.",
        profile="trial",
        router_model="router",
        cheap_model="cheap",
        strong_model="strong",
    )

    assert decision.selected_model == "cheap"


def test_select_model_rejects_invalid_choice(monkeypatch: pytest.MonkeyPatch) -> None:
    response = {
        "content": [
            {"type": "text", "text": '{"choice":"medium","reason":"Unsure."}'}
        ]
    }
    monkeypatch.setattr(
        "benchmark.runner.router.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0, stdout=json.dumps(response), stderr=""
        ),
    )

    with pytest.raises(RoutingError, match="invalid choice"):
        select_model(
            title="Task",
            task_prompt="Do work.",
            profile="trial",
            router_model="router",
            cheap_model="cheap",
            strong_model="strong",
        )
