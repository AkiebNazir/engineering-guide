"""
12 — Worker Pool
=================

WHAT
----
A bounded-concurrency worker pool over an arbitrary list of async jobs:

    - Concurrency is capped with `asyncio.Semaphore`, so N jobs can be
      in-flight regardless of how many total jobs there are.
    - `asyncio.TaskGroup` (3.11+) supervises the workers: if any job raises,
      the group cancels every other still-running task and re-raises via an
      `ExceptionGroup` -- this file demonstrates that propagation explicitly
      rather than just asserting it happens.
    - Results are collected in the *original submission order*, not
      completion order, because most callers want `results[i]` to correspond
      to `jobs[i]`.
    - A CPU-bound variant note covers why `asyncio` alone doesn't help for
      CPU-bound work (the GIL) and how `concurrent.futures.ProcessPoolExecutor`
      genuinely parallelizes it, with `loop.run_in_executor` as the bridge.

WHY THIS MATTERS
-----------------
"Run N things at once, but not everything at once" is one of the most common
real shapes of concurrent work: batch API calls, fan-out DB queries, parallel
file processing. Getting it right means:

    1. **Bounding concurrency** -- unbounded `asyncio.gather` over 10,000
       jobs will happily open 10,000 sockets/file handles at once and fall
       over. A semaphore (or a fixed pool of worker coroutines pulling from
       a queue) caps the blast radius.
    2. **Fail-fast cancellation** -- if job 3 of 100 raises an unrecoverable
       error, do the other 97 keep running to completion for no reason
       (wasting time/money on doomed work), or does the pool cancel them?
       `TaskGroup` gives you fail-fast by default; you have to explicitly
       opt out (e.g. wrap each job to catch-and-return errors) if you want
       "run everything regardless."
    3. **CPU-bound vs I/O-bound** -- `asyncio` concurrency is cooperative
       and single-threaded per event loop; it multiplexes I/O waits, but a
       CPU-bound job blocks the *entire* event loop for its duration (the
       GIL prevents true parallel Python bytecode execution across OS
       threads too). Only separate processes get you real parallel CPU
       throughput in stock CPython.

CONCEPTS EXERCISED
-------------------
    - `asyncio.Semaphore` for bounded concurrency.
    - `asyncio.TaskGroup` (structured concurrency, PEP-recommended over
      raw `asyncio.gather` since 3.11): automatic cancellation of siblings
      on first exception, and `ExceptionGroup`/`except*` handling.
    - Preserving submission order in results despite out-of-order
      completion.
    - `concurrent.futures.ProcessPoolExecutor` + `loop.run_in_executor` for
      genuinely parallel CPU-bound work, and why threads don't help there.

SPEC
----
    async def run_pool(
        jobs: Sequence[Callable[[], Awaitable[T]]],
        max_concurrency: int,
    ) -> list[T]:
        "Run all `jobs` with at most `max_concurrency` concurrently in
         flight. Returns results in the same order as `jobs`. If any job
         raises, cancel all other in-flight/pending jobs and propagate
         (see `run_pool_fail_fast` for the exact exception shape)."

    async def run_pool_collect_errors(
        jobs: Sequence[Callable[[], Awaitable[T]]],
        max_concurrency: int,
    ) -> list[T | BaseException]:
        "Like run_pool, but never cancels siblings on error -- every job
         runs to completion, and its slot in the result list holds either
         its return value or the exception it raised."

    def run_cpu_bound_pool(
        jobs: Sequence[Callable[[], T]],
        max_workers: int,
    ) -> list[T]:
        "Synchronous-callable variant for CPU-bound work: run `jobs` across
         a ProcessPoolExecutor with `max_workers` worker processes, return
         results in submission order. Callables and their arguments must be
         picklable (ProcessPoolExecutor constraint)."

ACCEPTANCE CRITERIA
--------------------
    - `run_pool` never has more than `max_concurrency` jobs actually
      in-flight at once (demonstrated with an active-count assertion in the
      solution/tests, not just a docstring claim).
    - `run_pool`'s results list is ordered by input position regardless of
      which job finishes first.
    - A job raising in `run_pool` causes the function to raise, and no job
      submitted after the pool starts unwinding is allowed to *start* fresh
      work (already-running jobs may observe cancellation).
    - `run_pool_collect_errors` always returns a full-length list; a failed
      job's slot contains the exception instance, not a raised exception
      propagating out of the function.
    - `run_cpu_bound_pool` returns correct results for CPU-heavy pure
      functions (e.g. computing primality) using multiple worker processes.

Everything below is a stub. Fill in the `# TODO:` markers. Full type hints
are already in place -- match them.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import TypeVar

T = TypeVar("T")


async def run_pool(
    jobs: Sequence[Callable[[], Awaitable[T]]],
    max_concurrency: int,
) -> list[T]:
    # TODO:
    #  - asyncio.Semaphore(max_concurrency) to bound in-flight jobs
    #  - asyncio.TaskGroup() to supervise: on first exception, remaining
    #    tasks are cancelled automatically and an ExceptionGroup propagates
    #    once the `async with` block exits
    #  - write each job's result into a pre-sized list at its own index so
    #    order matches `jobs` regardless of completion order
    raise NotImplementedError


async def run_pool_collect_errors(
    jobs: Sequence[Callable[[], Awaitable[T]]],
    max_concurrency: int,
) -> list[T | BaseException]:
    # TODO:
    #  - same bounded concurrency, but each job's coroutine wrapper must
    #    catch BaseException and return it rather than let it propagate,
    #    so no single failure cancels the rest via TaskGroup semantics
    raise NotImplementedError


def run_cpu_bound_pool(
    jobs: Sequence[Callable[[], T]],
    max_workers: int,
) -> list[T]:
    # TODO:
    #  - concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)
    #  - submit all jobs, gather results in submission order
    #  - remember: the callables (and any closures) must be picklable --
    #    module-level functions work, local closures/lambdas typically don't
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Hints
# ---------------------------------------------------------------------------
# - A common bug: creating all `len(jobs)` tasks immediately inside the
#   TaskGroup and relying only on the semaphore to gate *execution* still
#   means all tasks exist (and are scheduled) up front -- that's fine for
#   correctness (the semaphore still bounds concurrent *work*), but if you
#   want to bound outstanding task *objects* too (e.g. jobs is huge), use a
#   fixed number of worker coroutines pulling from an `asyncio.Queue`
#   instead. Both are legitimate designs; the semaphore-per-task version is
#   simpler and is what the acceptance criteria test against.
# - `asyncio.TaskGroup` requires Python 3.11+; on exception it raises an
#   `ExceptionGroup` (or `BaseExceptionGroup`) wrapping the underlying
#   exception(s), not the original exception directly -- callers need
#   `except*` or to inspect `.exceptions` to get at it.
# - For `run_pool_collect_errors`, catching `BaseException` (not just
#   `Exception`) inside each job wrapper is deliberate: you don't want a
#   `CancelledError` from an *external* cancellation to look like "the pool
#   finished normally," but you also don't want one job's `KeyboardInterrupt`
#   analog to silently vanish -- consider re-raising `CancelledError` after
#   recording it, since task cancellation has special semantics.
# - `ProcessPoolExecutor` pickles the callable and its arguments to send to
#   worker processes -- a `lambda` or local closure will raise
#   `PicklingError`. Use module-level functions (or `functools.partial` of
#   one) for CPU-bound jobs.
#
# Pitfalls
# --------
# - Forgetting the semaphore is *per-job-acquisition*, not per-call to
#   run_pool -- reusing one Semaphore instance across concurrent run_pool()
#   calls would incorrectly share the concurrency budget between them.
# - Using `asyncio.gather(return_exceptions=True)` when you actually wanted
#   fail-fast cancellation (or vice versa) -- gather's return_exceptions
#   flag is the "collect errors" behavior, not TaskGroup's default.
# - Assuming ProcessPoolExecutor workers share memory with the parent --
#   they don't; only picklable arguments and return values cross the
#   boundary.
#
# Stretch goals
# -------------
# - Add a per-job timeout using `asyncio.timeout()` (3.11+) that cancels
#   just that job without failing the whole pool.
# - Add progress reporting (a callback invoked as each job completes).
# - Benchmark `run_cpu_bound_pool` against a naive sequential loop for a
#   genuinely CPU-bound function and report the speedup vs. `max_workers`.
