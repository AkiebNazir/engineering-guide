"""Tests for 16 · Pub/sub event bus."""

from __future__ import annotations

import asyncio
from importlib import import_module

import pytest

_solution = import_module("16_pubsub_event_bus_solution")
EventBus = _solution.EventBus
BusClosedError = _solution.BusClosedError


@pytest.mark.asyncio
async def test_fan_out_to_multiple_subscribers() -> None:
    bus = EventBus()
    sub_a = bus.subscribe("orders")
    sub_b = bus.subscribe("orders")

    delivered = await bus.publish("orders", {"id": 1})
    assert delivered == 2

    assert await sub_a.__anext__() == {"id": 1}
    assert await sub_b.__anext__() == {"id": 1}

    sub_a.unsubscribe()
    sub_b.unsubscribe()
    await bus.close()


@pytest.mark.asyncio
async def test_independent_subscribers_do_not_compete() -> None:
    """Each subscriber gets its own copy — this is fan-out, not a work queue."""
    bus = EventBus()
    subs = [bus.subscribe("t") for _ in range(3)]
    await bus.publish("t", "hello")

    for sub in subs:
        assert await sub.__anext__() == "hello"
        sub.unsubscribe()
    await bus.close()


@pytest.mark.asyncio
async def test_slow_consumer_drops_oldest_not_newest() -> None:
    """A full queue evicts the oldest message; publish() never blocks/raises."""
    bus = EventBus(maxsize=2)
    sub = bus.subscribe("t")

    # Fill the queue beyond capacity without ever reading it.
    for i in range(5):
        n = await bus.publish("t", i)
        assert n == 1  # always "delivered" to the queue, even if it evicts

    assert sub.dropped == 3  # 5 published, capacity 2 -> 3 evictions

    # The two messages remaining are the newest ones (3, 4), not the oldest.
    first = await sub.__anext__()
    second = await sub.__anext__()
    assert (first, second) == (3, 4)

    sub.unsubscribe()
    await bus.close()


@pytest.mark.asyncio
async def test_publish_never_blocks_regardless_of_consumer_speed() -> None:
    bus = EventBus(maxsize=1)
    sub = bus.subscribe("t")

    async def publish_many() -> None:
        for i in range(1000):
            await bus.publish("t", i)

    # If publish() ever awaited on a full queue, this would hang forever
    # since nothing is reading `sub`. wait_for gives it a generous bound.
    await asyncio.wait_for(publish_many(), timeout=2.0)
    assert sub.dropped == 999

    sub.unsubscribe()
    await bus.close()


@pytest.mark.asyncio
async def test_unsubscribe_stops_async_for_cleanly() -> None:
    bus = EventBus()
    sub = bus.subscribe("t")
    received: list[object] = []

    async def consume() -> None:
        async for msg in sub:
            received.append(msg)

    task = asyncio.create_task(consume())
    await asyncio.sleep(0)  # let the task reach queue.get()

    await bus.publish("t", "one")
    await asyncio.sleep(0)

    sub.unsubscribe()
    # The consumer task must exit on its own (clean StopAsyncIteration),
    # not hang and not raise.
    await asyncio.wait_for(task, timeout=1.0)
    assert task.exception() is None
    assert received == ["one"]

    await bus.close()


@pytest.mark.asyncio
async def test_unsubscribe_is_idempotent() -> None:
    bus = EventBus()
    sub = bus.subscribe("t")
    sub.unsubscribe()
    sub.unsubscribe()  # must not raise
    await bus.close()


@pytest.mark.asyncio
async def test_subscription_as_async_context_manager() -> None:
    bus = EventBus()
    async with bus.subscribe("t") as sub:
        await bus.publish("t", "x")
        assert await sub.__anext__() == "x"
    # Exiting the `async with` block must have unsubscribed automatically.
    assert bus._subs == {}
    await bus.close()


@pytest.mark.asyncio
async def test_close_wakes_subscribers_and_ends_iteration() -> None:
    bus = EventBus()
    sub = bus.subscribe("t")
    received: list[object] = []

    async def consume() -> None:
        async for msg in sub:
            received.append(msg)

    task = asyncio.create_task(consume())
    await asyncio.sleep(0)

    await bus.close()
    await asyncio.wait_for(task, timeout=1.0)
    assert task.exception() is None
    assert received == []


@pytest.mark.asyncio
async def test_close_is_idempotent() -> None:
    bus = EventBus()
    await bus.close()
    await bus.close()  # must not raise


@pytest.mark.asyncio
async def test_publish_and_subscribe_after_close_raise() -> None:
    bus = EventBus()
    await bus.close()
    with pytest.raises(BusClosedError):
        bus.subscribe("t")
    with pytest.raises(BusClosedError):
        await bus.publish("t", "x")


@pytest.mark.asyncio
async def test_no_leaked_tasks_after_full_lifecycle() -> None:
    """The bus spawns zero internal tasks; only caller-owned tasks exist,
    and those must all be finished (and awaited) after cleanup."""
    current = asyncio.current_task()
    assert current is not None
    baseline = asyncio.all_tasks() - {current}

    bus = EventBus()
    subs = [bus.subscribe(f"topic-{i}") for i in range(5)]

    async def consume(sub: object) -> None:
        async for _ in sub:  # type: ignore[attr-defined]
            pass

    tasks = [asyncio.create_task(consume(sub)) for sub in subs]
    await asyncio.sleep(0)  # let every consumer reach queue.get()

    for i, sub in enumerate(subs):
        await bus.publish(f"topic-{i}", i)
    await asyncio.sleep(0)

    for sub in subs:
        sub.unsubscribe()
    await asyncio.wait_for(asyncio.gather(*tasks), timeout=1.0)
    await bus.close()

    after = asyncio.all_tasks() - {current}
    assert after == baseline, f"leaked tasks: {after - baseline}"
