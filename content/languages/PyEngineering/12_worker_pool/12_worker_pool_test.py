from __future__ import annotations

import asyncio
import time
from functools import partial
from importlib import import_module
from typing import Any

import pytest

# The directory (and thus module) name starts with a digit, so it can't be
# named in a real `import` statement; pytest puts this file's directory on
# sys.path so the dynamic import below resolves at runtime. mypy has no
# static visibility into a dynamically-named module, so these are typed
# `Any` rather than faked into precise types.
_solution = import_module("12_worker_pool_solution")
run_pool: Any = _solution.run_pool
run_pool_collect_errors: Any = _solution.run_pool_collect_errors
run_cpu_bound_pool: Any = _solution.run_cpu_bound_pool


async def _sleep_and_return(value: int, delay: float = 0.01) -> int:
    await asyncio.sleep(delay)
    return value


async def _boom() -> int:
    raise RuntimeError("job failed")


# --- module-level, picklable CPU-bound jobs for ProcessPoolExecutor ---


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


def _count_primes_below(n: int) -> int:
    return sum(1 for i in range(2, n) if _is_prime(i))


@pytest.mark.asyncio
async def test_run_pool_preserves_input_order_despite_varied_delays() -> None:
    # Earlier jobs sleep longer, so completion order is reversed relative
    # to submission order -- results must still come back in submission
    # order.
    jobs = [
        (lambda: _sleep_and_return(0, delay=0.05)),
        (lambda: _sleep_and_return(1, delay=0.03)),
        (lambda: _sleep_and_return(2, delay=0.01)),
    ]

    results = await run_pool(jobs, max_concurrency=3)

    assert results == [0, 1, 2]


@pytest.mark.asyncio
async def test_run_pool_never_exceeds_max_concurrency() -> None:
    max_concurrency = 4
    active = 0
    peak = 0
    lock = asyncio.Lock()

    async def job() -> None:
        nonlocal active, peak
        async with lock:
            active += 1
            peak = max(peak, active)
        await asyncio.sleep(0.02)
        async with lock:
            active -= 1

    jobs = [job for _ in range(20)]

    await run_pool(jobs, max_concurrency=max_concurrency)

    assert peak <= max_concurrency
    assert peak == max_concurrency  # sanity: concurrency was actually used


@pytest.mark.asyncio
async def test_run_pool_propagates_and_cancels_siblings_on_failure() -> None:
    started = 0
    completed = 0
    lock = asyncio.Lock()

    async def slow_job(index: int) -> int:
        nonlocal started, completed
        async with lock:
            started += 1
        await asyncio.sleep(0.2)
        async with lock:
            completed += 1
        return index

    async def failing_job() -> int:
        await asyncio.sleep(0.01)
        raise RuntimeError("boom")

    jobs = [(lambda i=i: slow_job(i)) for i in range(5)] + [failing_job]

    with pytest.raises(ExceptionGroup) as exc_info:
        await run_pool(jobs, max_concurrency=6)

    assert any(isinstance(exc, RuntimeError) for exc in exc_info.value.exceptions)
    # The slow jobs should have started (all fit under max_concurrency=6)
    # but been cancelled before their 0.2s sleep completed.
    assert started == 5
    assert completed == 0


@pytest.mark.asyncio
async def test_run_pool_collect_errors_returns_full_length_with_exceptions() -> None:
    jobs = [
        (lambda: _sleep_and_return(1)),
        _boom,
        (lambda: _sleep_and_return(3)),
    ]

    results = await run_pool_collect_errors(jobs, max_concurrency=3)

    assert len(results) == 3
    assert results[0] == 1
    assert isinstance(results[1], RuntimeError)
    assert results[2] == 3


@pytest.mark.asyncio
async def test_run_pool_collect_errors_does_not_cancel_siblings() -> None:
    completed = []

    async def job(index: int) -> int:
        if index == 1:
            raise RuntimeError("boom")
        await asyncio.sleep(0.02)
        completed.append(index)
        return index

    jobs = [(lambda i=i: job(i)) for i in range(4)]

    results = await run_pool_collect_errors(jobs, max_concurrency=4)

    assert sorted(completed) == [0, 2, 3]
    assert isinstance(results[1], RuntimeError)


def test_run_cpu_bound_pool_computes_correct_results() -> None:
    # functools.partial of a module-level function is picklable (a lambda
    # is not), which is what ProcessPoolExecutor requires to ship the job
    # to a worker process.
    jobs = [partial(_count_primes_below, n) for n in (100, 200, 300)]

    start = time.monotonic()
    results = run_cpu_bound_pool(jobs, max_workers=3)
    elapsed = time.monotonic() - start

    expected = [_count_primes_below(n) for n in (100, 200, 300)]
    assert results == expected
    # Not a strict perf assertion (CI machines vary), just a sanity bound
    # that it actually ran rather than hanging.
    assert elapsed < 30
