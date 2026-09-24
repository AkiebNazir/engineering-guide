"""
13 · Pipeline (fan-out / fan-in) — solution.

See `13_pipeline_explanation.py` for the full spec, rationale, and
acceptance criteria. This file is the complete, idiomatic implementation.

DESIGN DECISION: sentinels over queue.join()/task_done()
-----------------------------------------------------------
`asyncio.Queue` offers a built-in "am I drained" primitive:
`await queue.join()` blocks until every item `put()` has had a matching
`task_done()` called. That looks tailor-made for fan-in completion, but it
composes badly with `TaskGroup` cancellation: if a worker is cancelled (or
raises) mid-item, it never calls `task_done()` for the item it was holding,
and `join()` then waits forever — exactly the leak this problem is designed
to prevent. A sentinel per worker has no such failure mode: either the
worker task completes (having consumed its sentinel or having been
cancelled first, in which case the TaskGroup itself is what's waited on,
not the queue), and there is nothing that can silently "forget" to signal.
`TaskGroup.__aexit__` is the actual completion gate in both `run_pipeline`
and `Pipeline`; the sentinel is only how *workers* learn to stop pulling,
not how the caller learns the pipeline is done.

DESIGN DECISION: TaskGroup for run_pipeline, manual tasks for Pipeline
-----------------------------------------------------------------------
`run_pipeline` is one call, one lifetime: producer + workers + collection
all happen inside a single `async with asyncio.TaskGroup() as tg:` block,
so structured concurrency (auto-cancel siblings on error, auto-await
everyone before returning) is free.

`Pipeline` is long-lived: `submit()` and `results()` are called
independently, potentially many times, between `__aenter__` and
`__aexit__`. A `TaskGroup`'s `async with` body defines its children's
entire lifetime — you cannot open one in `__aenter__` and close it in a
*different* call to `__aexit__` later, because the group object itself
must stay inside one `async with` statement. So `Pipeline` falls back to
plain `asyncio.create_task` plus explicit bookkeeping (`self._tasks`) that
`close()` awaits — the same guarantee (no orphaned tasks), achieved
manually because the use case doesn't fit TaskGroup's shape.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from typing import Final, Self

# ---------------------------------------------------------------------------
# Private sentinel: one is pushed per worker so each worker's `get()` loop
# knows precisely when to stop, without needing to pre-know the input size.
# ---------------------------------------------------------------------------
_DONE: Final[object] = object()


async def run_pipeline(
    items: Iterable[int],
    *,
    transform: Callable[[int], Awaitable[int]],
    num_workers: int = 4,
    queue_maxsize: int = 8,
) -> list[int]:
    """Run `items` through `transform` with bounded fan-out concurrency."""
    # Step 1: a single bounded queue is the whole backpressure story for
    # the producer -> workers edge. maxsize caps how far the producer can
    # run ahead of the slowest worker.
    in_q: asyncio.Queue[int | object] = asyncio.Queue(maxsize=queue_maxsize)
    results: list[int] = []

    async def producer() -> None:
        # Step 2: feed every real item, then exactly one stop sentinel per
        # worker so each worker's loop terminates independently.
        for item in items:
            await in_q.put(item)
        for _ in range(num_workers):
            await in_q.put(_DONE)

    async def worker() -> None:
        while True:
            item = await in_q.get()
            if item is _DONE:
                return
            # `transform` runs concurrently across up to num_workers items
            # at once; raising here propagates through the TaskGroup, which
            # cancels the producer and every sibling worker automatically.
            value = await transform(item)  # type: ignore[arg-type]
            # Single-threaded event loop: list.append() never yields mid-
            # operation, so concurrent workers appending here is race-free
            # without any lock — there is no thread-level interleaving to
            # protect against (contrast problem 14's real OS threads).
            results.append(value)

    # Step 3: TaskGroup is the whole leak-free guarantee. On success it
    # awaits every child before returning; on any child's exception it
    # cancels every sibling first, then awaits them, then re-raises
    # (wrapped in an ExceptionGroup) — zero manual cleanup required.
    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer())
        for _ in range(num_workers):
            tg.create_task(worker())

    return results


class Pipeline:
    """Long-lived pipeline: external submit() + results() over its lifetime.

    Not usable outside `async with Pipeline(...) as p:` — worker tasks are
    started in `__aenter__` and guaranteed-awaited in `__aexit__`/`close()`.
    """

    def __init__(
        self,
        *,
        transform: Callable[[int], Awaitable[int]],
        num_workers: int = 4,
        queue_maxsize: int = 8,
    ) -> None:
        self._transform = transform
        self._num_workers = num_workers
        self._in_q: asyncio.Queue[int | object] = asyncio.Queue(maxsize=queue_maxsize)
        # Unbounded by design: only the *input* side needs backpressure
        # (there's unbounded external demand behind it). Completed results
        # are cheap to hold and have exactly one designated drain path
        # (results()) that the caller controls — bounding this queue too
        # would mean close() (which awaits every worker) can deadlock
        # against a caller who hasn't started draining results() yet.
        self._out_q: asyncio.Queue[int | object] = asyncio.Queue()
        self._closed = False
        self._tasks: list[asyncio.Task[None]] = []

    async def __aenter__(self) -> Self:
        # Plain create_task, not TaskGroup: __aenter__ must return while
        # workers are still running (they run for this Pipeline's whole
        # lifetime, spanning many submit()/results() calls) — a TaskGroup's
        # `async with` block can't be entered here and exited elsewhere.
        self._tasks = [
            asyncio.create_task(self._worker()) for _ in range(self._num_workers)
        ]
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def _worker(self) -> None:
        while True:
            item = await self._in_q.get()
            if item is _DONE:
                # Tell the fan-in side (results()) this worker is finished,
                # then this task itself ends -- one _DONE per worker on each
                # queue, so both edges of the pipeline know precisely when
                # every worker has stopped.
                await self._out_q.put(_DONE)
                return
            value = await self._transform(item)  # type: ignore[arg-type]
            await self._out_q.put(value)

    async def submit(self, item: int) -> None:
        """Enqueue one item; blocks if the bounded input queue is full."""
        if self._closed:
            raise RuntimeError("cannot submit: pipeline is closed")
        await self._in_q.put(item)

    async def results(self) -> AsyncIterator[int]:
        """Async-iterate results as workers produce them.

        Ends (StopAsyncIteration) once every worker has signaled done —
        i.e. once `close()` has been called and every in-flight item has
        drained through. Safe to consume concurrently with `submit()`.
        """
        live_workers = self._num_workers
        while live_workers > 0:
            item = await self._out_q.get()
            if item is _DONE:
                live_workers -= 1
                continue
            yield item  # type: ignore[misc]

    async def close(self) -> None:
        """Signal no more input, then wait for all in-flight work to finish.

        Idempotent: safe to call more than once (e.g. explicitly and again
        via `__aexit__`).
        """
        if self._closed:
            return
        self._closed = True
        # Blocking put is correct here: whatever real backlog is still in
        # `_in_q` must drain in FIFO order before a worker sees its stop
        # sentinel, so results already submitted are never abandoned.
        for _ in range(self._num_workers):
            await self._in_q.put(_DONE)
        await asyncio.gather(*self._tasks)


# ---------------------------------------------------------------------------
# Best practices demonstrated here
# ---------------------------------------------------------------------------
# - Prefer `asyncio.TaskGroup` whenever the concurrent work's lifetime maps
#   onto one `async with` block — it is strictly harder to leak a task or
#   swallow an exception with it than with manual `create_task` +
#   `gather`.
# - When a TaskGroup doesn't fit (a lifetime spanning multiple calls, as in
#   `Pipeline`), keep the *same* guarantee manually: track every task you
#   create, and make the shutdown path (`close()`) unconditionally await
#   all of them, idempotently.
# - Bound every queue in the chain. Backpressure through a multi-stage
#   pipeline is only real if every stage's queue is bounded — one
#   unbounded queue anywhere in the chain breaks backpressure for every
#   stage upstream of it.
# - One sentinel per consumer for "N consumers, unknown-in-advance total
#   work" fan-in signaling; a shared counter/event invites races that a
#   per-consumer sentinel structurally avoids.
#
# Alternative approaches
# -----------------------
# - `queue.join()` + `task_done()` (see the module docstring) — simpler to
#   read, but silently hangs forever if a worker is cancelled or raises
#   mid-item without a `finally: queue.task_done()`, which is easy to
#   forget and hard to notice in testing (it only manifests under real
#   failure, exactly when you need shutdown to be reliable).
# - `asyncio.as_completed` / a semaphore-bounded `gather` instead of an
#   explicit worker pool — works for a one-shot batch, but doesn't
#   naturally extend to `Pipeline`'s streaming submit/consume shape, and
#   loses the clean "exactly num_workers concurrent" guarantee once you
#   start adding items after the batch has started.
#
# Testing/benchmarking notes
# ----------------------------
# - Prove real concurrency, not just correctness: N items each sleeping a
#   fixed duration through num_workers workers should take roughly
#   `ceil(N/num_workers) * duration`, not `N * duration` — see the test
#   file's timing assertion.
# - Prove backpressure directly: a slow consumer must cause `submit()` (or
#   the internal producer) to block once `queue_maxsize` is reached, not
#   silently buffer past it — measurable via `asyncio.wait_for` on a
#   `submit()` call racing a delayed drain.
# - Prove leak-freedom on the failure path deliberately, not just the
#   happy path — a pipeline that leaks tasks only when `transform` raises
#   is the version that actually ships a memory leak to production.
