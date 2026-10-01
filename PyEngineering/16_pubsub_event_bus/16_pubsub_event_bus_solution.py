"""
16 · Pub/sub event bus — solution.

See `16_pubsub_event_bus_explanation.py` for the full spec, rationale, and
acceptance criteria. This file is the complete, idiomatic implementation.

DESIGN DECISION: drop-oldest over block-with-timeout
-----------------------------------------------------
A bounded per-subscriber queue needs a policy for what happens when it's
full. Two real options:

1. **Drop-oldest** (chosen here): `publish()` never awaits. If a
   subscriber's queue is full, evict its oldest queued message to make room
   for the new one. The publisher's call always completes immediately.
2. **Block-with-timeout**: `publish()` awaits `queue.put()` with a timeout
   per subscriber; on timeout, evict the subscriber entirely (treat it as
   dead) or drop the new message.

Drop-oldest is the right default for an *event* bus (as opposed to a
*work-queue*): subscribers here care about the current state of the world,
not full history — think "price ticked to $42" or "connection count is now
17." For that kind of message, the newest value supersedes the old one, so
losing a stale queued update is free; losing the newest one (which
block-with-timeout risks, since eviction happens on the new message too if
you drop-new instead of evicting) would show subscribers stale data. It
also means one slow subscriber's queue filling up can *never* add latency
to publishing for every other subscriber, or to the publisher itself —
publish() is O(subscribers) synchronous work, full stop.

Block-with-timeout is the better choice for a work queue where every item
must eventually be processed exactly once (e.g. job dispatch) — that's
problem 13's territory (pipeline with backpressure), not this one.
"""

from __future__ import annotations

import asyncio
from typing import Any, Final, Self

# ---------------------------------------------------------------------------
# A private sentinel used to wake a subscriber blocked on queue.get() when
# the bus closes. Must be an object distinct from any real message (in
# particular distinct from `None`, which is a legal message payload).
# ---------------------------------------------------------------------------
_CLOSE_SENTINEL: Final[object] = object()


class BusClosedError(RuntimeError):
    """Raised by publish()/subscribe() once the bus has been closed."""


class Subscription:
    """A single subscriber's handle: an async-iterable queue + unsubscribe.

    Not constructed directly by callers — returned by `EventBus.subscribe`.
    """

    def __init__(self, bus: EventBus, topic: str, maxsize: int) -> None:
        self._bus = bus
        self._topic = topic
        # Step 1: a bounded queue is the entire backpressure mechanism.
        # maxsize > 0 makes put_nowait() raise QueueFull once full, which
        # is exactly the signal _offer() needs to apply drop-oldest.
        self._queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=maxsize)
        self._dropped = 0
        self._active = True

    @property
    def dropped(self) -> int:
        """Count of messages dropped for this subscriber (queue was full)."""
        return self._dropped

    @property
    def active(self) -> bool:
        return self._active

    def unsubscribe(self) -> None:
        """Remove this subscription from the bus; stop its iterator.

        Idempotent: safe to call more than once (e.g. once explicitly and
        once more via `__aexit__` on a `with`/`async with` block).
        """
        if not self._active:
            return
        self._active = False
        self._bus._unsubscribe(self._topic, self)
        # Wake any pending __anext__() so it observes `_active is False`
        # promptly rather than waiting for the next real publish.
        self._push_wakeup()

    def _push_wakeup(self) -> None:
        """Best-effort: ensure a blocked get() returns soon after we go inactive."""
        try:
            self._queue.put_nowait(_CLOSE_SENTINEL)
        except asyncio.QueueFull:
            # Evict the oldest item to guarantee room for the wakeup —
            # the subscriber is going away regardless, so losing one more
            # stale queued message is irrelevant.
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(_CLOSE_SENTINEL)
            except asyncio.QueueEmpty:  # pragma: no cover - race, harmless
                pass

    def _offer(self, message: Any) -> bool:
        """Bus-internal: enqueue a message, applying drop-oldest if full.

        Returns True if queued, False if this subscription is inactive.
        """
        if not self._active:
            return False
        try:
            self._queue.put_nowait(message)
        except asyncio.QueueFull:
            # Drop-oldest: evict one item, then the new message always fits
            # (single-producer-per-call invariant: nothing else consumes
            # queue.put concurrently since publish() runs to completion
            # without awaiting).
            self._dropped += 1
            self._queue.get_nowait()
            self._queue.put_nowait(message)
        return True

    def __aiter__(self) -> Subscription:
        return self

    async def __anext__(self) -> Any:
        item = await self._queue.get()
        if item is _CLOSE_SENTINEL or not self._active:
            raise StopAsyncIteration
        return item

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        self.unsubscribe()


class EventBus:
    """Zero-task pub/sub bus: `publish()` is a synchronous fan-out.

    No method here ever calls `asyncio.create_task` — there is nothing for
    the bus itself to leak. Consumption (draining a `Subscription`) is
    entirely the caller's responsibility, typically via `async for` inside
    a task the caller owns and is responsible for cancelling.
    """

    def __init__(self, *, maxsize: int = 16) -> None:
        self._maxsize = maxsize
        self._subs: dict[str, set[Subscription]] = {}
        self._closed = False

    @property
    def is_closed(self) -> bool:
        return self._closed

    def subscribe(self, topic: str) -> Subscription:
        """Register and return a new Subscription for `topic`."""
        if self._closed:
            raise BusClosedError("cannot subscribe: bus is closed")
        sub = Subscription(self, topic, self._maxsize)
        self._subs.setdefault(topic, set()).add(sub)
        return sub

    def _unsubscribe(self, topic: str, sub: Subscription) -> None:
        """Bus-internal: called by Subscription.unsubscribe()."""
        topic_subs = self._subs.get(topic)
        if topic_subs is not None:
            topic_subs.discard(sub)
            if not topic_subs:
                del self._subs[topic]

    async def publish(self, topic: str, message: object) -> int:
        """Fan `message` out to every live subscriber of `topic`.

        Never awaits on a full queue (drop-oldest instead). Returns the
        number of subscribers the message was queued to.
        """
        if self._closed:
            raise BusClosedError("cannot publish: bus is closed")
        # Iterate a *copy* of the subscriber set: a subscriber's own
        # consumer callback could call unsubscribe() synchronously as a
        # side effect of _offer() in exotic setups, and mutating a set
        # while iterating it raises RuntimeError.
        delivered = 0
        for sub in list(self._subs.get(topic, ())):
            if sub._offer(message):
                delivered += 1
        return delivered

    async def close(self) -> None:
        """Idempotently close the bus: wake every subscriber, reject reuse."""
        if self._closed:
            return
        self._closed = True
        for topic_subs in list(self._subs.values()):
            for sub in list(topic_subs):
                sub._active = False
                sub._push_wakeup()
        self._subs.clear()


# ---------------------------------------------------------------------------
# Best practices demonstrated here
# ---------------------------------------------------------------------------
# - Keep the bus itself task-free. Every task the *caller* spawns to drain
#   a Subscription is a task the caller owns and can cancel deterministically
#   — the bus never hides concurrency behind an innocuous-looking method call.
# - Bound every queue. An unbounded `asyncio.Queue()` under a slow consumer
#   is just a slower, deferred version of unbounded memory growth.
# - Make `close()` idempotent and `unsubscribe()` idempotent — shutdown
#   paths are frequently invoked from more than one place (signal handler +
#   `finally`), and a non-idempotent cleanup method is a footgun.
# - Use a private sentinel object, not `None`, to signal "the stream is
#   done" over a queue that also carries real application messages.
#
# Alternative approaches
# -----------------------
# - Block-with-timeout backpressure (see the module docstring) — better for
#   at-least-once work queues, worse for live/"latest value" event streams.
# - A single asyncio.Condition broadcast instead of per-subscriber queues —
#   simpler, but couples every subscriber's read speed to the others' (a
#   slow subscriber can miss messages emitted between wakeups instead of
#   having its own buffer), and cannot express per-subscriber drop policy.
# - `weakref.WeakSet` for `self._subs[topic]` to auto-forget subscribers
#   whose owner was garbage collected without calling unsubscribe() — a
#   defense-in-depth measure real long-running buses often add; omitted
#   here to keep the lifecycle contract explicit (always unsubscribe).
