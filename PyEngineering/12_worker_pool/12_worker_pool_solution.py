"""
12 — Worker Pool — solution.

Bounded-concurrency async worker pool built on asyncio.Semaphore +
asyncio.TaskGroup, plus a ProcessPoolExecutor-backed variant for CPU-bound
work.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from concurrent.futures import ProcessPoolExecutor
from typing import TypeVar

T = TypeVar("T")


async def run_pool(
    jobs: Sequence[Callable[[], Awaitable[T]]],
    max_concurrency: int,
) -> list[T]:
    if max_concurrency < 1:
        raise ValueError("max_concurrency must be >= 1")

    # A fresh Semaphore per call: sharing one across concurrent run_pool()
    # invocations would silently merge their concurrency budgets.
    semaphore = asyncio.Semaphore(max_concurrency)
    results: list[T | None] = [None] * len(jobs)

    async def _run_one(index: int, job: Callable[[], Awaitable[T]]) -> None:
        # The semaphore gates *execution*, not task creation -- all tasks
        # are scheduled up front inside the TaskGroup, but only
        # `max_concurrency` of them proceed past `acquire()` at a time.
        async with semaphore:
            results[index] = await job()

    # TaskGroup gives structured concurrency: if `_run_one` raises for any
    # index, the group cancels every other outstanding task automatically
    # and, once all tasks have settled, raises an ExceptionGroup wrapping
    # the failure(s) from the `async with` block. No manual gather/cancel
    # bookkeeping needed.
    async with asyncio.TaskGroup() as tg:
        for index, job in enumerate(jobs):
            tg.create_task(_run_one(index, job))

    # If we reach here, every task completed without raising, so every
    # slot in `results` was written -- safe to narrow the type.
    return [r for r in results]  # type: ignore[misc]


async def run_pool_collect_errors(
    jobs: Sequence[Callable[[], Awaitable[T]]],
    max_concurrency: int,
) -> list[T | BaseException]:
    if max_concurrency < 1:
        raise ValueError("max_concurrency must be >= 1")

    semaphore = asyncio.Semaphore(max_concurrency)
    results: list[T | BaseException | None] = [None] * len(jobs)

    async def _run_one(index: int, job: Callable[[], Awaitable[T]]) -> None:
        async with semaphore:
            try:
                results[index] = await job()
            except asyncio.CancelledError:
                # Cancellation is not "this job failed" in the same sense
                # as a raised business exception -- record it for
                # visibility, but re-raise so the task genuinely stops and
                # the enclosing TaskGroup/event loop sees the cancellation
                # rather than having it silently absorbed.
                results[index] = asyncio.CancelledError()
                raise
            except BaseException as exc:  # noqa: BLE001 - intentional: see spec
                # Every other exception is captured into its slot instead
                # of propagating, so one job's failure never cancels its
                # siblings -- this is the "run everything regardless" mode.
                results[index] = exc

    async with asyncio.TaskGroup() as tg:
        for index, job in enumerate(jobs):
            tg.create_task(_run_one(index, job))

    return [r for r in results]  # type: ignore[misc]


def run_cpu_bound_pool(
    jobs: Sequence[Callable[[], T]],
    max_workers: int,
) -> list[T]:
    # asyncio does not help here: CPython's GIL means only one thread runs
    # Python bytecode at a time, so a CPU-bound function occupies the
    # entire event loop (or a whole OS thread, if run via
    # run_in_executor(ThreadPoolExecutor, ...)) for its full duration --
    # no other coroutine progresses meanwhile. ProcessPoolExecutor sidesteps
    # the GIL by using separate OS processes, each with its own
    # interpreter and GIL, giving genuine parallelism for CPU-bound work at
    # the cost of pickling inputs/outputs across the process boundary and
    # losing shared in-memory state.
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(job) for job in jobs]
        return [future.result() for future in futures]


# ---------------------------------------------------------------------------
# Best practices
# ---------------------------------------------------------------------------
# - `asyncio.TaskGroup` over raw `asyncio.gather`: TaskGroup is structured
#   concurrency -- every task it creates is guaranteed to have completed
#   (successfully, cancelled, or raised) by the time the `async with` block
#   exits, and a single failure fails fast by cancelling siblings. Plain
#   `gather` without `return_exceptions=True` leaves already-created tasks
#   running in the background even after `gather` itself raises, which is
#   a common source of "leaked" fire-and-forget tasks.
# - Writing results into a pre-sized list by index (rather than appending
#   as jobs complete) is what keeps output order matching input order
#   despite jobs finishing in arbitrary completion order.
# - `run_pool_collect_errors` re-raising `CancelledError` after recording it
#   respects the asyncio contract that a task observing cancellation should
#   let it propagate rather than swallow it -- swallowing cancellation can
#   make `task.cancel()` calls elsewhere in the program appear to silently
#   fail.
# - `ProcessPoolExecutor` as a context manager ensures worker processes are
#   torn down (`shutdown(wait=True)`) even if a job raises during
#   `.result()`.
#
# Alternative approaches
# -----------------------
# - A fixed pool of N worker coroutines consuming from an `asyncio.Queue`
#   (see 13_pipeline for this shape) bounds the number of *task objects*
#   in flight too, not just concurrent execution -- worth it when `jobs`
#   is very large (millions) and creating that many Task objects up front
#   is itself a memory concern. For a bounded/moderate job list, the
#   semaphore-per-task approach here is simpler and equally correct.
# - `loop.run_in_executor(process_pool, job)` bridges a ProcessPoolExecutor
#   into async code, letting CPU-bound jobs run alongside I/O-bound
#   `asyncio` work in the same event loop rather than as a fully separate
#   synchronous call -- useful when a service does both kinds of work.
# - For CPU-bound jobs that release the GIL internally (e.g. NumPy/C
#   extensions doing the heavy lifting), a `ThreadPoolExecutor` can
#   actually parallelize despite the GIL, since the GIL is released during
#   the C-level computation. That's a property of the specific workload,
#   not something to assume for arbitrary "CPU-bound" Python code.
