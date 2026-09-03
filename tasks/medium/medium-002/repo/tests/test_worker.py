"""Tests for src.worker.run_many."""

from __future__ import annotations

import asyncio

import pytest

from src.worker import run_many


async def slow_double(x: int) -> int:
    await asyncio.sleep(0.01)
    return x * 2


def test_preserves_order() -> None:
    out = asyncio.run(run_many([1, 2, 3, 4], slow_double))
    assert out == [2, 4, 6, 8]


def test_empty_input() -> None:
    out = asyncio.run(run_many([], slow_double))
    assert out == []


def test_cancellation_returns_partial_results() -> None:
    """When the outer task is cancelled mid-flight, the worker should
    return the results it already has, and then re-raise CancelledError."""
    results: list[int] = []
    error: list[BaseException] = []

    async def driver() -> None:
        try:
            out = await run_many(
                list(range(50)),
                slow_double,
                concurrency=4,
            )
            results.extend(out)
        except BaseException as e:  # noqa: BLE001
            error.append(e)

    loop = asyncio.new_event_loop()
    try:
        task = loop.create_task(driver())
        loop.run_until_complete(asyncio.sleep(0.02))  # let some finish
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            loop.run_until_complete(task)
    finally:
        loop.close()

    assert results, "expected partial results to be returned before re-raise"
    assert all(v % 2 == 0 for v in results)
