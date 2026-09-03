"""Background worker that fans out work to a pool of coroutines."""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


async def run_many(
    items: list[T],
    fn: Callable[[T], Awaitable[R]],
    *,
    concurrency: int = 8,
) -> list[R]:
    """Run `fn` over `items` with bounded concurrency, preserving input order.

    On cancellation, partial results (so far completed) MUST be returned,
    and asyncio.CancelledError MUST be re-raised.
    """
    sem = asyncio.Semaphore(concurrency)
    results: list[R | None] = [None] * len(items)

    async def _one(i: int, item: T) -> None:
        async with sem:
            results[i] = await fn(item)

    tasks = [asyncio.create_task(_one(i, it)) for i, it in enumerate(items)]
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        # BUG: re-raise without returning what we already have.
        raise
    return [r for r in results if r is not None]
