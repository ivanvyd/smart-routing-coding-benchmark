from benchmark.analysis.router_errors import find_candidates


def _run(arm: str, passed: bool, model: str) -> dict[str, object]:
    return {
        "arm": arm,
        "task_id": "task",
        "task_passed": passed,
        "selected_model": model,
    }


def _attribution(arm: str, cost: float) -> dict[str, object]:
    return {"arm": arm, "task_id": "task", "total_estimated_cost": cost}


def test_under_routing_requires_the_cheap_model_to_have_been_selected() -> None:
    runs = {
        "FIXED_CHEAP": [_run("FIXED_CHEAP", False, "cheap")],
        "FIXED_STRONG": [_run("FIXED_STRONG", True, "strong")],
        "CLIENT_ROUTING": [_run("CLIENT_ROUTING", False, "strong")],
    }

    assert find_candidates(runs, {})["under_routing"] == []

    runs["CLIENT_ROUTING"] = [_run("CLIENT_ROUTING", False, "cheap")]
    assert len(find_candidates(runs, {})["under_routing"]) == 1


def test_over_routing_requires_the_strong_model_to_have_been_selected() -> None:
    runs = {
        "FIXED_CHEAP": [_run("FIXED_CHEAP", True, "cheap")],
        "FIXED_STRONG": [_run("FIXED_STRONG", True, "strong")],
        "CLIENT_ROUTING": [_run("CLIENT_ROUTING", True, "cheap")],
    }
    attributed = {
        "FIXED_CHEAP": [_attribution("FIXED_CHEAP", 1.0)],
        "FIXED_STRONG": [_attribution("FIXED_STRONG", 3.0)],
        "CLIENT_ROUTING": [_attribution("CLIENT_ROUTING", 2.0)],
    }

    assert find_candidates(runs, attributed)["over_routing"] == []

    runs["CLIENT_ROUTING"] = [_run("CLIENT_ROUTING", True, "strong")]
    assert len(find_candidates(runs, attributed)["over_routing"]) == 1
