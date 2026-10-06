"""
13 · Pipeline (fan-out / fan-in)
================================

WHAT WE'RE BUILDING
--------------------
A multi-stage async processing pipeline: a producer feeds items into stage
1, stage 1 fans out to N worker coroutines that transform each item and
feed stage 2, and stage 2 fans everything back in to a single collector.
This is the canonical "fan-out/fan-in" shape behind an ETL job, a batch
image-resize service, a log-processing pipeline, or any system that reads
records from one place, does bounded-concurrency work on each, and writes
results somewhere else.

Same shape as `../GoEngineering/13_pipeline` (channels + goroutines); here
the channel is `asyncio.Queue` and the goroutine is a `asyncio.Task` inside
an `asyncio.TaskGroup`.

WHY THIS MATTERS IN REAL SYSTEMS
---------------------------------
- **Fan-out gives you bounded concurrency for free.** A fixed pool of N
  worker tasks pulling from one queue is a natural concurrency limiter —
  you never have more than N transforms in flight, unlike
  `asyncio.gather(*(transform(x) for x in items))` which launches all of
  them at once.
- **Fan-in needs a completion signal, not a fixed count.** The collector
  doesn't know in advance how many results N workers will produce combined
  (workers finish at different times) — it needs a reliable "every worker
  is done and the queue is drained" signal. Two idiomatic options: sentinel
  values (one per worker) or `queue.join()` paired with `task_done()`. This
  problem uses sentinels because they compose cleanly with `TaskGroup`
  cancellation — `queue.join()` alone can hang forever if a worker dies
  without calling `task_done()`, whereas a sentinel-starved queue.get()
  is trivially visible and a `TaskGroup` propagates a worker's exception
  immediately, cancelling siblings instead of hanging.
- **Leak-free shutdown is the actual bar.** Every task spawned must either
  run to completion or be cancelled and awaited before the pipeline
  function returns. `asyncio.TaskGroup` (3.11+) gives you this for free:
  if any task raises, every other task in the group is cancelled and the
  group `__aexit__` awaits all of them before re-raising (as an
  `ExceptionGroup`). This is directly testable: `asyncio.all_tasks()`
  must return to baseline after the pipeline finishes or fails.
- **Backpressure is not optional.** Every `asyncio.Queue` here is bounded.
  An unbounded queue between a fast producer and slow workers is just
  deferred unbounded memory growth — the same lesson as problem 16's
  bounded subscriber queues, applied to a work queue instead of an event
  stream (contrast problem 16's drop-oldest policy, which is wrong for
  work that must be processed exactly once — here we block instead).

CONCEPTS COVERED
-----------------
- `asyncio.Queue` as a bounded, backpressured channel between stages
- Fan-out: N worker tasks reading from one queue
- Fan-in: multiple producers feeding one downstream queue/collector
- Sentinel-based "N workers done" signaling vs. `queue.join()`
- `asyncio.TaskGroup` for structured concurrency: exceptions propagate,
  siblings get cancelled, everything is awaited before the group exits
- Verifying zero leaked tasks via `asyncio.all_tasks()` before/after

THE SPEC
--------
Build a two-stage pipeline:

    async def run_pipeline(
        items: Iterable[int],
        *,
        transform: Callable[[int], Awaitable[int]],
        num_workers: int = 4,
        queue_maxsize: int = 8,
    ) -> list[int]:
        '''Run `items` through `transform` with `num_workers` concurrent
        workers (stage 1: fan-out) and collect every result into a list,
        order not guaranteed (stage 2: fan-in). Returns once every item has
        been transformed and collected, with zero leaked tasks.

        If `transform` raises for any item, the whole pipeline stops:
        remaining input stops being fed, in-flight workers finish or are
        cancelled, and the exception propagates to the caller (wrapped in
        an ExceptionGroup, since asyncio.TaskGroup raises one on any child
        failure — see problem 17 for the taxonomy of unwrapping this).
        '''

    class Pipeline:
        '''A reusable, explicitly-lifecycled version of the same pipeline,
        for callers that want to keep it running across multiple batches
        instead of a one-shot function call.'''
        def __init__(
            self,
            *,
            transform: Callable[[int], Awaitable[int]],
            num_workers: int = 4,
            queue_maxsize: int = 8,
        ) -> None: ...
        async def __aenter__(self) -> "Pipeline": ...
        async def __aexit__(self, *exc: object) -> None: ...
        async def submit(self, item: int) -> None: ...
            # blocks (backpressure) if the input queue is full
        async def results(self) -> AsyncIterator[int]:
            # async-iterate results as they complete; ends when the
            # pipeline is closed and drained
        async def close(self) -> None: ...
            # signal no more input; wait for in-flight work to finish

Behavior:
    - `run_pipeline` is the simple one-shot entry point: feed a fixed
      iterable, get a fixed list back. Internally it wires a producer task,
      `num_workers` worker tasks, and the current coroutine as collector,
      all under one `asyncio.TaskGroup`.
    - `Pipeline` is the long-lived version: an external caller `submit()`s
      items over time (e.g. from a web handler) and separately consumes
      `results()` as an async iterator, until `close()` is called and
      drains.
    - Both must guarantee: no orphaned tasks after normal completion, no
      orphaned tasks after an exception, and correct backpressure (a
      full input queue blocks `submit`/the producer, it never drops or
      grows unbounded).

ACCEPTANCE CRITERIA
--------------------
1. `run_pipeline` processes every input item exactly once and returns all
   results (order-independent), with `num_workers` transforms genuinely
   running concurrently (provable via a timing test: N items each
   sleeping `t` seconds with `num_workers` workers takes ~`(N/num_workers)*t`,
   not `N*t`).
2. A `transform` exception cancels sibling workers and the producer, and
   propagates to the caller — no swallowed errors, no hang.
3. `asyncio.all_tasks()` (minus the current task) returns to its exact
   pre-pipeline membership after both a successful run and a failed run.
4. `Pipeline.submit()` blocks once the bounded input queue is full
   (backpressure), provably via a test that a slow consumer stalls a fast
   producer rather than letting the queue grow past `queue_maxsize`.
5. `Pipeline.close()` lets in-flight items finish, then ends `results()`'s
   async iteration cleanly (no exception, no hang).
6. mypy-clean, black-formatted, ruff-clean.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterable
from typing import Self

# A private sentinel pushed onto the results queue by each worker once it
# has permanently stopped, so the fan-in side knows when every worker is
# done without needing a pre-known item count.
# TODO: define `_DONE: Final[object] = object()`


async def run_pipeline(
    items: Iterable[int],
    *,
    transform: Callable[[int], Awaitable[int]],
    num_workers: int = 4,
    queue_maxsize: int = 8,
) -> list[int]:
    """Run `items` through `transform` with bounded fan-out concurrency."""
    # TODO:
    # 1. Create `in_q: asyncio.Queue[int | object]` bounded by queue_maxsize
    #    (or split sentinel type cleanly with a wrapper — your call).
    # 2. Inside `async with asyncio.TaskGroup() as tg:`
    #    - spawn a producer task that puts every item then, per worker,
    #      puts one sentinel (so each worker gets exactly one stop signal)
    #    - spawn num_workers worker tasks: loop `get()`, break on sentinel,
    #      else call `await transform(item)` and append to a shared list
    #      (a plain list append is fine — no other task interleaves on a
    #      single-threaded event loop between the append itself and the
    #      next `await`, so no lock is needed here)
    # 3. Return the collected results after the TaskGroup exits.
    raise NotImplementedError("TODO: implement run_pipeline")


class Pipeline:
    """Long-lived pipeline: external submit() + results() over its lifetime."""

    def __init__(
        self,
        *,
        transform: Callable[[int], Awaitable[int]],
        num_workers: int = 4,
        queue_maxsize: int = 8,
    ) -> None:
        # TODO: store config, create self._in_q (bounded by queue_maxsize —
        # this is the backpressure surface submit() blocks on) and
        # self._out_q (leave UNBOUNDED: `asyncio.Queue()`, no maxsize — a
        # bounded out_q can deadlock close() against a caller who hasn't
        # started draining results() yet), self._closed, and placeholders
        # for the worker tasks started in __aenter__.
        raise NotImplementedError("TODO: implement Pipeline.__init__")

    async def __aenter__(self) -> Self:
        # TODO: start num_workers worker tasks (store them; do NOT use a
        # TaskGroup here since __aenter__ must return before workers
        # finish — a TaskGroup's `async with` block wouldn't exit until
        # all workers do). Track tasks so __aexit__/close() can await them.
        raise NotImplementedError("TODO: implement Pipeline.__aenter__")

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def submit(self, item: int) -> None:
        """Enqueue one item; blocks if the bounded input queue is full."""
        # TODO: raise RuntimeError if closed; else `await self._in_q.put(item)`.
        raise NotImplementedError("TODO: implement Pipeline.submit")

    async def results(self) -> AsyncIterator[int]:
        """Async-iterate results as workers produce them."""
        # TODO: loop `await self._out_q.get()`; stop once every worker has
        # signaled done (track a countdown of live workers, decremented on
        # each `_DONE` sentinel received) — do not stop on the first
        # sentinel, since num_workers workers each emit one.
        raise NotImplementedError("TODO: implement Pipeline.results")
        yield 0  # pragma: no cover - makes this an async generator for mypy

    async def close(self) -> None:
        """Signal no more input, then wait for all in-flight work to finish."""
        # TODO: idempotent. Put one sentinel per worker into self._in_q
        # (blocking put is fine/expected here — draining the real backlog
        # first is the point), then `await asyncio.gather(*self._tasks)`.
        raise NotImplementedError("TODO: implement Pipeline.close")


# ---------------------------------------------------------------------------
# HINTS
# -----
# - `asyncio.TaskGroup` (3.11+) is the structured-concurrency primitive for
#   `run_pipeline`: it blocks at `__aexit__` until every child task is
#   done, and if any child raises, it cancels all siblings first. This is
#   exactly "leak-free on both success and failure" for free.
# - For `Pipeline` (long-lived, spans multiple `submit`/`results` calls
#   outside any single `async with tg:` block), plain `asyncio.create_task`
#   + manually tracking/awaiting the tasks in `close()` is correct — a
#   `TaskGroup` can't span an `__aenter__`/`__aexit__` pair the way you'd
#   need here, since its own `async with` body IS the task lifetime.
# - One sentinel *per worker*, not one sentinel total — if you put a single
#   sentinel into a multi-consumer queue, whichever worker happens to
#   `get()` it first exits, leaving the rest blocked on `get()` forever.
# - Use `asyncio.Queue(maxsize=...)` (never 0/unbounded) for both stages —
#   backpressure is a hard requirement, not a nice-to-have.
#
# COMMON PITFALLS
# ---------------
# - Using `asyncio.gather(*(transform(x) for x in items))` instead of a
#   worker pool — that launches unbounded concurrency, defeating the whole
#   point of "fan-out with N workers."
# - Forgetting per-worker sentinels and instead trying to signal "done" via
#   a shared counter/event without care for the exact moment every worker
#   has actually seen its own sentinel — races are easy to introduce here.
# - Calling `close()` a second time and re-sending sentinels /
#   double-awaiting already-finished tasks — must be idempotent, same
#   lesson as problem 16.
# - Appending to a shared results list from multiple worker coroutines
#   without realizing this is *fine* on a single-threaded event loop
#   (list.append doesn't await mid-operation) — don't over-engineer with a
#   `threading.Lock` that adds nothing here and would be actively wrong to
#   reach for in a coroutine (there's no OS thread contention to protect
#   against; that's problem 14's territory, on a real thread pool).
#
# STRETCH GOALS
# --------------
# - Add a third stage (fan-out -> fan-out -> fan-in) and confirm the
#   backpressure chain: a slow stage-2 stalls stage-1 workers once the
#   inter-stage queue fills, which in turn stalls the producer.
# - Add per-item timeout via `asyncio.timeout()` (3.11+) around each
#   `transform` call, routing timed-out items to a separate "failed" list
#   instead of aborting the whole pipeline.
# - Compare `queue.join()` + `task_done()` as an alternative fan-in
#   completion signal to the sentinel approach used here, and explain in
#   comments why it's a worse fit under `TaskGroup` cancellation (a
#   cancelled worker task that dies mid-item without calling `task_done()`
#   leaves `join()` waiting forever, whereas sentinel-starvation is visible
#   immediately as "the results queue.get() never returns").
