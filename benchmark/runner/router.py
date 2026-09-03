"""Prompt-only model selection for the client-routed benchmark arm."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from dataclasses import dataclass
from typing import Any

POLICY_ID = "prompt-only-v1"
POLICY_PROMPT = """You route coding tasks between two Claude models.

Choose the cheap model for a localized change with explicit requirements and low risk.
Choose the strong model for ambiguous debugging, concurrency, state transitions, schema or SQL
work, security-sensitive behavior, or changes that span several components.

Use only the task title and task request. Do not infer a hidden difficulty label.
Return one JSON object with exactly two fields:
{"choice":"cheap|strong","reason":"one short factual sentence"}
"""
POLICY_SHA256 = hashlib.sha256(POLICY_PROMPT.encode()).hexdigest()


class RoutingError(RuntimeError):
    """Raised when the selector cannot produce a valid routing decision."""


@dataclass(frozen=True)
class RoutingDecision:
    selected_model: str
    reason: str
    router_model: str
    policy_id: str
    policy_sha256: str
    duration_seconds: float
    input_tokens: int
    output_tokens: int


def select_model(
    *,
    title: str,
    task_prompt: str,
    profile: str,
    router_model: str,
    cheap_model: str,
    strong_model: str,
    timeout_seconds: int = 60,
) -> RoutingDecision:
    """Ask the cheap model to choose a candidate using task text only."""
    body = {
        "model": router_model,
        "max_tokens": 128,
        "system": POLICY_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": f"Task title: {title}\n\nTask request:\n{task_prompt.strip()}",
            }
        ],
    }
    started = time.monotonic()
    try:
        result = subprocess.run(
            [
                "databricks",
                "api",
                "post",
                "/ai-gateway/anthropic/v1/messages",
                "--json",
                json.dumps(body, separators=(",", ":")),
                "--profile",
                profile,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise RoutingError(f"router request exceeded {timeout_seconds}s") from exc
    duration = round(time.monotonic() - started, 3)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown Databricks CLI error"
        raise RoutingError(f"router request failed: {message}")

    response = _load_json(result.stdout, "router response")
    content = response.get("content")
    if not isinstance(content, list) or not content:
        raise RoutingError("router response has no content")
    first = content[0]
    if not isinstance(first, dict) or not isinstance(first.get("text"), str):
        raise RoutingError("router response has no text block")
    payload = _load_json(_strip_code_fence(first["text"]), "router decision")
    choice = payload.get("choice")
    reason = payload.get("reason")
    if choice not in {"cheap", "strong"}:
        raise RoutingError(f"router returned invalid choice: {choice!r}")
    if not isinstance(reason, str) or not reason.strip():
        raise RoutingError("router returned no reason")

    usage = response.get("usage")
    usage = usage if isinstance(usage, dict) else {}
    return RoutingDecision(
        selected_model=cheap_model if choice == "cheap" else strong_model,
        reason=reason.strip(),
        router_model=router_model,
        policy_id=POLICY_ID,
        policy_sha256=POLICY_SHA256,
        duration_seconds=duration,
        input_tokens=_int_field(usage, "input_tokens"),
        output_tokens=_int_field(usage, "output_tokens"),
    )


def _load_json(value: str, label: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise RoutingError(f"{label} is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise RoutingError(f"{label} must be a JSON object")
    return parsed


def _strip_code_fence(value: str) -> str:
    stripped = value.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        return "\n".join(lines[1:-1]).strip()
    return stripped


def _int_field(value: dict[str, Any], key: str) -> int:
    field = value.get(key)
    return field if isinstance(field, int) else 0
