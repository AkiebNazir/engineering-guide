"""Tests for 13 · Pipeline (fan-out / fan-in)."""

from __future__ import annotations

import asyncio
import time
from importlib import import_module

import pytest

_solution = import_module("13_pipeline_solution")
run_pipeline = _solution.run_pipeline
Pipeline = _solution.Pipeline


async def _double(x: int) -> int:
    return x * 2


@pytest.mark.asyncio
async def test_run_pipeline_processes_every_item_exactly_once() -> None:
    results = await run_pipeline(range(20), transform=_double, num_workers=4)
    assert sorted(results) == [x * 2 for x in range(20)]


@pytest.mark.asyncio
async def test_run_pipeline_workers_run_concurrently() -> None:
    """N items x fixed sleep through num_workers workers takes ~N/num_workers
    slices, not N slices -- proves real fan-out, not sequential processing."""
    delay = 0.05
    n_items = 8
    num_workers = 4

    async def slow_transform(x: int) -> int:
        await asyncio.sleep(delay)
        return x

    start = time.monotonic()
    results = await run_pipeline(
        range(n_items), transform=slow_transform, num_workers=num_workers
    )
    elapsed = time.monotonic() - start

    assert sorted(results) == list(range(n_items))
    expected_batches = n_items / num_workers  # 2 sequential batches of 4
    # Generous upper bound: well under fully-sequential (n_items * delay)
    # but comfortably above the ideal, to absorb scheduler jitter.
    assert elapsed < n_items * delay * 0.75
    assert elapsed >= expected_batches * delay * 0.5


@pytest.mark.asyncio
async def test_run_pipeline_propagates_transform_error_and_cancels_siblings() -> None:
    async def flaky(x: int) -> int:
        if x == 3:
            raise ValueError("boom")
        await asyncio.sleep(0.2)
        return x

    with pytest.raises(ExceptionGroup) as excinfo:
        await run_pipeline(range(10), transform=flaky, num_workers=4)
    assert any(isinstance(e, ValueError) for e in excinfo.value.exceptions)


@pytest.mark.asyncio
async def test_run_pipeline_leaves_no_leaked_tasks_on_success() -> None:
    current = asyncio.current_task()
    assert current is not None
    baseline = asyncio.all_tasks() - {current}

    await run_pipeline(range(12), transform=_double, num_workers=3)

    after = asyncio.all_tasks() - {current}
    assert after == baseline, f"leaked tasks: {after - baseline}"


@pytest.mark.asyncio
async def test_run_pipeline_leaves_no_leaked_tasks_on_failure() -> None:
    current = asyncio.current_task()
    assert current is not None
    baseline = asyncio.all_tasks() - {current}

    async def always_fails(x: int) -> int:
        if x == 0:
            raise RuntimeError("nope")
        await asyncio.sleep(0.1)
        return x

    with pytest.raises(ExceptionGroup):
        await run_pipeline(range(8), transform=always_fails, num_workers=4)

    after = asyncio.all_tasks() - {current}
    assert after == baseline, f"leaked tasks: {after - baseline}"


@pytest.mark.asyncio
async def test_pipeline_submit_and_results_roundtrip() -> None:
    async with Pipeline(transform=_double, num_workers=2, queue_maxsize=4) as p:
        for i in range(6):
            await p.submit(i)
        await p.close()

        collected = [x async for x in p.results()]

    assert sorted(collected) == [x * 2 for x in range(6)]


@pytest.mark.asyncio
async def test_pipeline_submit_blocks_when_input_queue_is_full() -> None:
    """Backpressure: a slow/absent consumer must stall submit(), never let
    the queue grow past queue_maxsize and never silently drop."""
    release = asyncio.Event()

    async def controllable(x: int) -> int:
        # Blocks until the test explicitly releases it, so the worker
        # holds exactly one item in flight without an arbitrary sleep.
        await release.wait()
        return x

    async with Pipeline(transform=controllable, num_workers=1, queue_maxsize=2) as p:
        # Fill the bounded input queue plus the one item the sole worker
        # pulls out to block on inside controllable().
        await asyncio.wait_for(p.submit(1), timeout=1.0)
        await asyncio.wait_for(p.submit(2), timeout=1.0)
        await asyncio.wait_for(p.submit(3), timeout=1.0)

        # The queue (maxsize=2) is now full; a 4th submit must block.
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(p.submit(4), timeout=0.2)

        release.set()  # let the worker drain everything before teardown


@pytest.mark.asyncio
async def test_pipeline_close_is_idempotent_and_ends_results_cleanly() -> None:
    async with Pipeline(transform=_double, num_workers=2) as p:
        await p.submit(1)
        await p.close()
        await p.close()  # must not raise / hang

        collected = [x async for x in p.results()]
    assert collected == [2]


@pytest.mark.asyncio
async def test_pipeline_submit_after_close_raises() -> None:
    async with Pipeline(transform=_double, num_workers=1) as p:
        await p.close()
        with pytest.raises(RuntimeError):
            await p.submit(1)


@pytest.mark.asyncio
async def test_pipeline_leaves_no_leaked_tasks_after_lifecycle() -> None:
    current = asyncio.current_task()
    assert current is not None
    baseline = asyncio.all_tasks() - {current}

    async with Pipeline(transform=_double, num_workers=4) as p:
        for i in range(10):
            await p.submit(i)
        await p.close()
        _ = [x async for x in p.results()]

    after = asyncio.all_tasks() - {current}
    assert after == baseline, f"leaked tasks: {after - baseline}"
