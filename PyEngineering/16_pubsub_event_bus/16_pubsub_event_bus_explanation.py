"""
16 · Pub/sub event bus
======================

WHAT WE'RE BUILDING
--------------------
An in-process, `asyncio`-native publish/subscribe event bus: multiple
subscribers register interest in a topic, publishers fan a message out to
every current subscriber of that topic, and the bus can be closed cleanly
without leaking background tasks or leaving subscribers blocked forever.

This is the same shape as an in-memory Redis Pub/Sub client, a WebSocket
broadcast hub, or the internal event bus inside a monolith before it grows
into a real message broker (Kafka/NATS/RabbitMQ). The engineering problems
are identical at every scale: what happens when a consumer is slower than
the producer, and how do you guarantee that unsubscribing/closing doesn't
leave dangling resources (tasks, sockets, threads) running forever.

WHY THIS MATTERS IN REAL SYSTEMS
---------------------------------
- **Slow-consumer handling is the whole game.** A publisher must never be
  allowed to block indefinitely because one subscriber stopped reading
  (imagine a browser tab that went to sleep holding a WebSocket open, or a
  worker that's stuck on a slow downstream call). Every real pub/sub system
  makes an explicit choice here: drop messages, block with a timeout and
  then evict the subscriber, or apply true backpressure to the publisher.
  There's no free lunch — you pick which failure mode you can tolerate.
- **No hidden tasks.** A naive pub/sub implementation spawns one
  `asyncio.Task` per subscriber to "pump" messages into it. Every task you
  spawn is a task you must guarantee gets cancelled and awaited — miss one
  unsubscribe path and you leak a task per churned subscriber, which shows
  up as a slow, silent memory leak in a long-running service. This
  implementation deliberately spawns **zero** internal tasks: `publish` is
  a plain synchronous fan-out over subscriber queues, and each subscriber
  drives its own consumption loop (or task, in the caller's code) — so the
  bus itself has nothing to leak.
- **Graceful close.** Closing the bus must wake every subscriber currently
  blocked on `queue.get()` (via a sentinel), reject new publishes/
  subscribes, and leave `asyncio.all_tasks()` exactly as it was before —
  this is directly testable and is exactly what you'd check in a real
  service's shutdown-path test.

CONCEPTS COVERED
-----------------
- `asyncio.Queue` with a bounded `maxsize` per subscriber
- Drop-oldest vs. block-with-timeout backpressure policies (we implement
  drop-oldest; the trade-off is explained inline)
- Subscriber lifecycle: `subscribe()` / `unsubscribe()` with an
  async-context-manager `Subscription` so callers can't forget to clean up
- Verifying "no leaked tasks" directly via `asyncio.all_tasks()`
- Graceful `close()`: sentinel-based wakeup, rejecting further use

THE SPEC
--------
Build `EventBus`:

    class EventBus:
        def __init__(self, *, maxsize: int = 16) -> None: ...
        def subscribe(self, topic: str) -> Subscription: ...
        async def publish(self, topic: str, message: object) -> int: ...
            # returns the number of subscribers the message was delivered
            # or queued to (not counting drops)
        async def close(self) -> None: ...
        @property
        def is_closed(self) -> bool: ...

    class Subscription:
        # async-iterable: `async for message in sub: ...` yields messages
        # until the bus closes or the subscription is cancelled.
        def unsubscribe(self) -> None: ...
        @property
        def dropped(self) -> int: ...   # count of messages dropped for
                                          # this subscriber (queue was full)
        async def __aenter__(self) -> "Subscription": ...
        async def __aexit__(self, *exc: object) -> None: ...

Behavior:
    - `subscribe(topic)` registers a new `Subscription` with its own
      bounded `asyncio.Queue(maxsize=...)`. Multiple subscriptions to the
      same topic are independent — each gets every message published to
      that topic (fan-out, not load-balancing).
    - `publish(topic, message)` is fan-out only: it never awaits on a full
      subscriber queue. If a subscriber's queue is full, the **oldest**
      queued message for that subscriber is dropped to make room for the
      new one (drop-oldest policy — see rationale in the solution file).
    - `unsubscribe()` removes the subscription from the bus and causes its
      async iterator to stop (a clean `StopAsyncIteration`, not an
      exception) — anyone doing `async for msg in sub:` exits its loop
      normally.
    - `close()` marks the bus closed, wakes every live subscription with a
      sentinel so their iterators end, and rejects further
      `publish`/`subscribe` calls with `BusClosedError`. `close()` is
      idempotent (safe to call twice).
    - The bus itself never calls `asyncio.create_task` — zero internal
      tasks, by construction.

ACCEPTANCE CRITERIA
--------------------
1. Two subscribers to the same topic both receive every published message
   (fan-out, not competing consumers).
2. A subscriber that stops reading and whose queue fills up causes new
   publishes to drop that subscriber's *oldest* queued message, not block
   the publisher and not raise.
3. `unsubscribe()` (directly, or via the `Subscription` async context
   manager) removes the subscriber; a background task consuming via
   `async for` exits cleanly with no exception.
4. After `close()`, `asyncio.all_tasks()` (minus the current test task) has
   the same membership as before any subscriber tasks were created — no
   leaked/pending tasks, asserted directly in a test.
5. `publish`/`subscribe` after `close()` raise `BusClosedError`.
6. mypy-clean, black-formatted, ruff-clean.
"""

from __future__ import annotations

from typing import Any, Self


class BusClosedError(RuntimeError):
    """Raised by publish()/subscribe() once the bus has been closed."""


# A private sentinel object used to wake a subscriber's queue on close.
# TODO: define `_CLOSE_SENTINEL: Final[object] = object()`


class Subscription:
    """A single subscriber's handle: an async-iterable queue + unsubscribe."""

    def __init__(self, bus: EventBus, topic: str, maxsize: int) -> None:
        # TODO: store bus/topic, create `self._queue: asyncio.Queue[Any]`
        # bounded by maxsize, `self._dropped = 0`, `self._active = True`.
        raise NotImplementedError("TODO: implement Subscription.__init__")

    @property
    def dropped(self) -> int:
        """Count of messages dropped for this subscriber (queue was full)."""
        raise NotImplementedError("TODO: implement Subscription.dropped")

    def unsubscribe(self) -> None:
        """Remove this subscription from the bus and stop its iterator."""
        # TODO: idempotent — safe to call more than once. Must ask the bus
        # to forget this subscription and mark self inactive so __anext__
        # returns/raises StopAsyncIteration on the next call.
        raise NotImplementedError("TODO: implement Subscription.unsubscribe")

    def _offer(self, message: Any) -> bool:
        """Bus-internal: enqueue a message, applying drop-oldest if full.

        Returns True if the message was queued (even if something else had
        to be dropped to make room), False if this subscription is inactive.
        """
        # TODO: if not active, return False. Try `put_nowait`; on
        # `asyncio.QueueFull`, `get_nowait()` once to evict the oldest item
        # (increment self._dropped), then `put_nowait` the new message.
        raise NotImplementedError("TODO: implement Subscription._offer")

    def __aiter__(self) -> Subscription:
        return self

    async def __anext__(self) -> Any:
        # TODO: await self._queue.get(). If the item is the close sentinel
        # or self is no longer active, raise StopAsyncIteration. Otherwise
        # return it.
        raise NotImplementedError("TODO: implement Subscription.__anext__")

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        self.unsubscribe()


class EventBus:
    """Zero-task pub/sub bus: publish() is a synchronous fan-out."""

    def __init__(self, *, maxsize: int = 16) -> None:
        # TODO: self._maxsize = maxsize
        # TODO: self._subs: dict[str, set[Subscription]] = {}
        # TODO: self._closed = False
        raise NotImplementedError("TODO: implement EventBus.__init__")

    @property
    def is_closed(self) -> bool:
        raise NotImplementedError("TODO: implement EventBus.is_closed")

    def subscribe(self, topic: str) -> Subscription:
        """Register and return a new Subscription for `topic`."""
        # TODO: raise BusClosedError if closed. Otherwise create a
        # Subscription, add it to self._subs[topic], return it.
        raise NotImplementedError("TODO: implement EventBus.subscribe")

    def _unsubscribe(self, topic: str, sub: Subscription) -> None:
        """Bus-internal: called by Subscription.unsubscribe()."""
        raise NotImplementedError("TODO: implement EventBus._unsubscribe")

    async def publish(self, topic: str, message: object) -> int:
        """Fan `message` out to every live subscriber of `topic`.

        Never awaits on a full queue (drop-oldest instead). Returns the
        number of subscribers the message was queued to.
        """
        # TODO: raise BusClosedError if closed. Look up self._subs.get(topic,
        # ()), call sub._offer(message) on each, count Trues. Note this
        # method is `async def` for API symmetry with a real broker client
        # (network I/O in a real implementation) even though this in-memory
        # version does no actual awaiting on the hot path.
        raise NotImplementedError("TODO: implement EventBus.publish")

    async def close(self) -> None:
        """Idempotently close the bus: wake every subscriber, reject reuse."""
        # TODO: if already closed, return. Set closed=True. For every
        # subscription across every topic: mark inactive and push the
        # sentinel via put_nowait (queue may be full — that's fine, evict
        # oldest first, same drop-oldest logic, since we just need *a*
        # wakeup, not delivery). Clear self._subs.
        raise NotImplementedError("TODO: implement EventBus.close")


# ---------------------------------------------------------------------------
# HINTS
# -----
# - `asyncio.Queue.put_nowait` / `get_nowait` never await — that's exactly
#   what you need inside `publish`, which must not block on a slow
#   consumer. Reach for `QueueFull`/`QueueEmpty`, not `try/except Exception`.
# - Iterate over a *copy* of the subscriber set inside `publish` and
#   `close` (`list(self._subs.get(topic, ()))`) — a subscriber unsubscribing
#   itself mid-iteration (e.g. from inside its own consumer callback) must
#   not raise `RuntimeError: set changed size during iteration`.
# - The sentinel must be a private, unique object (`object()`), not `None`
#   — `None` is a perfectly legal message a publisher might send.
#
# COMMON PITFALLS
# ---------------
# - Spawning `asyncio.create_task` inside `subscribe`/`publish` "to pump
#   messages" — this is the exact leak this problem is designed to catch.
#   Keep the bus task-free; let callers drive consumption themselves.
# - Blocking on `await queue.put(message)` in `publish` — this makes one
#   slow subscriber stall delivery to every *other* subscriber of the same
#   topic, and can deadlock a publisher that is itself a subscriber.
# - Forgetting `close()` must be idempotent — a shutdown path that calls
#   `close()` from two places (e.g. a signal handler and a `finally` block)
#   is common and must not raise on the second call.
# - Comparing `asyncio.all_tasks()` without excluding the current task —
#   the coroutine running the assertion is itself a task.
#
# STRETCH GOALS
# --------------
# - Add a `block-with-timeout` alternative policy behind a constructor flag
#   (`policy: Literal["drop_oldest", "block"]`) and measure how a single
#   frozen subscriber affects publish latency to *other* subscribers under
#   each policy.
# - Add wildcard topic subscriptions (`subscribe("orders.*")`).
# - Add a `stats()` method summarizing per-topic subscriber counts and
#   total dropped messages, the kind of thing you'd export to Prometheus
#   (problem 25's `/metrics`) for a real bus.
