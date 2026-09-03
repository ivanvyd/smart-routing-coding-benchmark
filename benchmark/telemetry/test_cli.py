from benchmark.telemetry.cli import Invocation, ModelPrice, attribute_runs


def _invocation(event_time: str, model: str = "claude-haiku-4-5") -> Invocation:
    return Invocation(
        request_id="request",
        invocation_id="invocation",
        event_time=event_time,
        endpoint_name="system.ai.claude-haiku-4-5",
        endpoint_id="endpoint",
        destination_type="PAY_PER_TOKEN_FOUNDATION_MODEL",
        destination_name="databricks-claude-haiku-4-5",
        destination_model=model,
        latency_ms=100,
        time_to_first_byte_ms=25,
        input_tokens=1_000_000,
        output_tokens=100_000,
        total_tokens=1_100_000,
        cache_read_input_tokens=200_000,
        cache_creation_input_tokens=100_000,
        output_reasoning_tokens=0,
        status_code=200,
        user_agent="ucode",
        requester="tester",
    )


def test_attribute_uses_exact_non_overlapping_windows() -> None:
    runs = [
        {
            "run_id": "first",
            "arm": "FIXED_CHEAP",
            "task_id": "easy-001",
            "started_at": "2026-09-03T10:00:00+00:00",
            "finished_at": "2026-09-03T10:00:06+00:00",
        },
        {
            "run_id": "second",
            "arm": "FIXED_CHEAP",
            "task_id": "easy-002",
            "started_at": "2026-09-03T10:00:06+00:00",
            "finished_at": "2026-09-03T10:00:10+00:00",
        },
    ]
    invocations = [_invocation("2026-09-03T10:00:06+00:00")]

    attributed = attribute_runs(runs, invocations)

    assert attributed[0]["invocation_count"] == 0
    assert attributed[1]["invocation_count"] == 1


def test_attribute_estimates_cache_aware_cost() -> None:
    runs = [
        {
            "run_id": "run",
            "arm": "FIXED_CHEAP",
            "task_id": "easy-001",
            "started_at": "2026-09-03T10:00:00+00:00",
            "finished_at": "2026-09-03T10:00:10+00:00",
        }
    ]
    prices = {
        "claude-haiku-4-5": ModelPrice(
            input=1.0,
            output=5.0,
            cache_read=0.1,
            cache_write=1.25,
        )
    }

    attributed = attribute_runs(
        runs,
        [_invocation("2026-09-03T10:00:05+00:00")],
        prices,
    )

    assert attributed[0]["estimated_cost"] == 1.345


def test_attribute_does_not_report_partial_cost() -> None:
    runs = [
        {
            "run_id": "run",
            "arm": "CLIENT_ROUTING",
            "task_id": "easy-001",
            "started_at": "2026-09-03T10:00:00+00:00",
            "finished_at": "2026-09-03T10:00:10+00:00",
        }
    ]
    prices = {
        "claude-haiku-4-5": ModelPrice(
            input=1.0,
            output=5.0,
            cache_read=0.1,
            cache_write=1.25,
        )
    }

    attributed = attribute_runs(
        runs,
        [_invocation("2026-09-03T10:00:05+00:00", model="unpriced-model")],
        prices,
    )

    assert attributed[0]["estimated_cost"] is None
