"""
03 — API Client With Retries — solution.

See `03_api_client_with_retries_explanation.py` for the full spec, rationale
and acceptance criteria. This file is the complete reference: a retrying
`httpx` client with capped exponential backoff + full jitter, Retry-After
support and an idempotency guard, plus a circuit breaker that composes with
it because both implement the same one-method `Sender` protocol.
"""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from enum import Enum
from typing import Protocol

import httpx

SleepFunc = Callable[[float], Awaitable[None]]

# RFC 9110 §9.2.2: methods whose intended effect is the same whether sent
# once or many times. POST and PATCH are deliberately absent.
IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE", "TRACE"})


class Sender(Protocol):
    """Anything that can send a prepared request. `httpx.AsyncClient`
    satisfies this structurally, and so do the two wrappers below, which is
    what lets them stack like decorators."""

    async def send(self, request: httpx.Request) -> httpx.Response: ...


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay: float = 0.1
    max_delay: float = 5.0
    max_retry_after: float = 30.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if min(self.base_delay, self.max_delay, self.max_retry_after) < 0:
            raise ValueError("delays must be >= 0")


class RetriesExhaustedError(Exception):
    """Every attempt failed at the transport level. Raised `from` the last
    underlying `httpx.TransportError`, so the real cause stays in the
    traceback (Python's equivalent of Go's `%w` wrapping)."""

    def __init__(self, attempts: int) -> None:
        super().__init__(f"request failed after {attempts} attempt(s)")
        self.attempts = attempts


class CircuitOpenError(Exception):
    """The breaker refused the call without touching the network."""


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


def is_retryable_status(status: int) -> bool:
    # 429 = "slow down", 5xx = "my fault, maybe transient". Every other 4xx
    # means the request itself is wrong; sending it again gets the same
    # answer and just adds load.
    return status == 429 or 500 <= status <= 599


def is_idempotent(request: httpx.Request) -> bool:
    # An Idempotency-Key (the Stripe-popularised convention, now an IETF
    # draft) means the server deduplicates replays, which makes even a POST
    # safe to retry.
    return request.method in IDEMPOTENT_METHODS or "idempotency-key" in request.headers


def backoff_delay(
    policy: RetryPolicy, attempts_made: int, rng: Callable[[], float]
) -> float:
    # Exponent is clamped before exponentiation: 2.0 ** 2000 raises
    # OverflowError, and anything past ~2**60 is past any sane cap anyway.
    exponent = min(max(attempts_made - 1, 0), 60)
    ceiling = min(policy.max_delay, policy.base_delay * 2.0**exponent)
    # Full jitter: uniform over [0, ceiling]. Compared with "equal jitter"
    # (ceiling/2 + uniform(0, ceiling/2)) it does slightly more total
    # waiting but spreads clients out best, which is the point.
    return rng() * ceiling


def parse_retry_after(value: str | None, now: datetime | None = None) -> float | None:
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:  # RFC 9110 dates are always GMT
        when = when.replace(tzinfo=UTC)
    now = now or datetime.now(UTC)
    return max(0.0, (when - now).total_seconds())


class RetryingClient:
    def __init__(
        self,
        sender: Sender,
        policy: RetryPolicy | None = None,
        *,
        sleep: SleepFunc = asyncio.sleep,
        rng: Callable[[], float] = random.random,
    ) -> None:
        self._sender = sender
        self._policy = policy or RetryPolicy()
        # Both injected so tests can assert exact delays without waiting.
        self._sleep = sleep
        self._rng = rng

    async def send(self, request: httpx.Request) -> httpx.Response:
        policy = self._policy
        max_attempts = policy.max_attempts if is_idempotent(request) else 1

        # A streaming body can only be consumed once. Buffer it up front so
        # every attempt sends the same bytes. For multi-GB uploads you would
        # instead refuse to retry (or use a resumable upload protocol).
        if max_attempts > 1:
            await request.aread()

        last_error: httpx.TransportError | None = None
        for attempt in range(1, max_attempts + 1):
            retry_after: float | None = None
            try:
                response = await self._sender.send(request)
            except httpx.TransportError as exc:
                # ConnectError, ReadTimeout, RemoteProtocolError, ... all
                # subclass TransportError. CancelledError and CircuitOpenError
                # are not caught here, so they propagate immediately.
                last_error = exc
            else:
                if not is_retryable_status(response.status_code) or attempt == max_attempts:
                    # Success, a non-retryable error, or the final retryable
                    # one: hand the real response back to the caller.
                    return response
                retry_after = parse_retry_after(response.headers.get("retry-after"))
                # Release the connection back to the pool before sleeping.
                await response.aclose()

            if attempt == max_attempts:
                break
            if retry_after is not None:
                delay = min(retry_after, policy.max_retry_after)
            else:
                delay = backoff_delay(policy, attempt, self._rng)
            # asyncio.sleep is cancellation-aware: if the caller's
            # asyncio.timeout() fires or the task is cancelled, this raises
            # CancelledError and no further attempt happens.
            await self._sleep(delay)

        assert last_error is not None  # only transport errors reach here
        raise RetriesExhaustedError(max_attempts) from last_error


class CircuitBreaker:
    def __init__(
        self,
        sender: Sender,
        *,
        failure_threshold: int = 5,
        cooldown: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        self._sender = sender
        self._threshold = failure_threshold
        self._cooldown = cooldown
        # Monotonic, never wall-clock: an NTP step backwards must not make
        # a cooldown last forever.
        self._clock = clock
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._opened_at = 0.0
        self._trial_in_flight = False

    @property
    def state(self) -> CircuitState:
        if (
            self._state is CircuitState.OPEN
            and self._clock() - self._opened_at >= self._cooldown
        ):
            return CircuitState.HALF_OPEN
        return self._state

    def _trip(self) -> None:
        self._state = CircuitState.OPEN
        self._opened_at = self._clock()
        self._failures = 0

    async def send(self, request: httpx.Request) -> httpx.Response:
        # --- admission: no await in this block, so it is atomic on the loop
        state = self.state
        if state is CircuitState.OPEN:
            raise CircuitOpenError("circuit open; failing fast")
        is_trial = state is CircuitState.HALF_OPEN
        if is_trial:
            if self._trial_in_flight:
                raise CircuitOpenError("circuit half-open; trial already in flight")
            self._state = CircuitState.HALF_OPEN
            self._trial_in_flight = True

        # --- the call itself
        failed = True  # pessimistic: covers cancellation and unexpected errors
        try:
            response = await self._sender.send(request)
            # 5xx = dependency unhealthy. 4xx = caller's bug; it says nothing
            # about the dependency's health, so it counts as a success here.
            failed = response.status_code >= 500
            return response
        finally:
            # --- outcome: again await-free
            if is_trial:
                self._trial_in_flight = False
                if failed:
                    self._trip()  # fresh cooldown
                else:
                    self._state = CircuitState.CLOSED
                    self._failures = 0
            elif self._state is CircuitState.CLOSED:
                if failed:
                    self._failures += 1
                    if self._failures >= self._threshold:
                        self._trip()
                else:
                    self._failures = 0


async def _demo() -> None:
    calls = 0

    def upstream(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls <= 2:
            return httpx.Response(503, headers={"Retry-After": "0"})
        return httpx.Response(200, json={"ok": True})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(upstream), base_url="https://upstream.test"
    ) as http:
        client = RetryingClient(CircuitBreaker(http, failure_threshold=5))
        response = await client.send(http.build_request("GET", "/items"))
        print(f"status={response.status_code} body={response.json()} attempts={calls}")


if __name__ == "__main__":
    asyncio.run(_demo())


# ---------------------------------------------------------------------------
# Best practices
# ---------------------------------------------------------------------------
# - The deadline belongs to the caller, around the whole operation:
#       async with asyncio.timeout(2.0):
#           resp = await client.send(req)
#   That budget covers every attempt and every sleep. Per-attempt timeouts
#   live in `httpx.Timeout(connect=..., read=...)` on the AsyncClient; the
#   two are complementary, not substitutes.
# - Returning the final 503 (rather than raising) keeps the server's body and
#   headers visible to the caller; raising a chained exception for transport
#   failures keeps the root cause in the traceback. Both beat a bare
#   "retries exhausted".
# - Composition order RetryingClient(CircuitBreaker(client)): the breaker
#   counts individual attempts, and when it opens mid-loop the
#   CircuitOpenError ends the retry loop at once instead of sleeping and
#   trying again against a known-dead dependency.
# - The breaker's `finally` block marks the outcome even when the trial call
#   is cancelled; without it a cancelled HALF_OPEN trial would leave
#   `_trial_in_flight=True` and the circuit could never close again.
#
# Alternative approaches
# -----------------------
# - `tenacity` is the widely used Python retry library (decorators with
#   stop/wait/retry predicates, async support). In a real codebase it saves
#   code; writing the loop by hand once is how you learn which predicates to
#   configure.
# - `httpx.AsyncHTTPTransport(retries=n)` only retries *connection*
#   failures (ConnectError/ConnectTimeout), never status codes, which is a
#   safe but narrow default.
# - For service meshes, retries and breaking often move into the sidecar
#   (Envoy retry policies, outlier detection). Then application-level retries
#   must be turned off or they multiply with the mesh's.
# - A count-based breaker (N consecutive failures) is simple; production
#   breakers such as resilience4j use a failure *rate* over a sliding window
#   with a minimum call count, which behaves better under mixed traffic.
