from benchmark.analysis.metrics import per_arm_metrics


def test_latency_uses_each_invocation_instead_of_run_means() -> None:
    runs = [
        {"task_passed": True, "task_difficulty": "easy", "duration_seconds": 1},
        {"task_passed": True, "task_difficulty": "easy", "duration_seconds": 1},
    ]
    attributed = [
        {
            "invocation_count": 2,
            "invocations": [{"latency_ms": 10}, {"latency_ms": 20}],
            "estimated_cost": 1.0,
        },
        {
            "invocation_count": 1,
            "invocations": [{"latency_ms": 300}],
            "estimated_cost": 1.0,
        },
    ]

    metrics = per_arm_metrics("FIXED_CHEAP", runs, attributed)

    assert metrics["mean_latency_ms"] == 110
    assert metrics["p95_latency_ms"] == 272


def test_cost_is_not_measured_when_any_run_lacks_a_price() -> None:
    runs = [
        {"task_passed": True, "task_difficulty": "easy", "duration_seconds": 1},
        {"task_passed": True, "task_difficulty": "easy", "duration_seconds": 1},
    ]
    attributed = [
        {"invocation_count": 1, "invocations": [], "estimated_cost": 1.0},
        {"invocation_count": 1, "invocations": [], "estimated_cost": None},
    ]

    metrics = per_arm_metrics("CLIENT_ROUTING", runs, attributed)

    assert metrics["total_estimated_cost"] == "NOT_MEASURED"
    assert metrics["cost_per_successful_task"] == "NOT_MEASURED"
