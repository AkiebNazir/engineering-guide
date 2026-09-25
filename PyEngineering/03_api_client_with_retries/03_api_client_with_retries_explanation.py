"""
03 — API Client With Retries
=============================

WHAT
----
An async HTTP client wrapper that calls a flaky upstream service
resiliently, built on `httpx`:

    - `RetryingClient` retries transient failures (transport errors, 429,
      5xx) with capped exponential backoff and *full jitter*, honours
      `Retry-After`, refuses to retry client errors (4xx) and refuses to
      auto-retry non-idempotent requests unless the caller opted in with an
      `Idempotency-Key` header.
    - `CircuitBreaker` wraps any sender and trips to OPEN after N
      consecutive failures, so a dead dependency gets zero traffic (not
      "every caller's full retry loop") until a cooldown passes and a
      single HALF_OPEN trial call proves it has recovered.
    - Both speak the same tiny `Sender` protocol (`async send(request) ->
      response`) as `httpx.AsyncClient`, so they compose like decorators:
      `RetryingClient(CircuitBreaker(httpx.AsyncClient()))`.

WHY THIS MATTERS
-----------------
Every service that calls another service over the network needs exactly
this logic, and getting it wrong is one of the most common causes of
cascading outages:

    1. **Retries without backoff** turn a two-second blip into a retry
       storm that keeps the downstream dead. With 3 layers of services each
       retrying 3 times, one user request can become 3^3 = 27 calls at the
       bottom of the stack.
    2. **Backoff without jitter** synchronises every client: they all fail
       at t=0, all retry at t=100ms, all retry at t=300ms -- thundering-herd
       waves instead of a smooth trickle. "Full jitter"
       (`sleep = uniform(0, min(cap, base * 2**attempt))`, from the AWS
       Architecture Blog post "Exponential Backoff and Jitter") spreads
       retries across the whole window.
    3. **Retries without a circuit breaker** mean a fully-down dependency
       still gets 100% of traffic times the retry multiplier, burning
       connections and latency budget on calls that are certain to fail.
    4. **Retries that ignore the caller's deadline** keep working after the
       caller has given up. In asyncio the deadline is an
       `asyncio.timeout(...)` block around the *whole* call (all attempts
       and sleeps), and cancellation arrives as `CancelledError` -- which
       must never be caught and retried.
    5. **Retrying non-idempotent calls** double-charges customers: the POST
       succeeded, the response was lost on the way back, the retry charges
       again. Only idempotent methods (GET, HEAD, PUT, DELETE, OPTIONS) or
       requests carrying an idempotency key are safe to replay.

CONCEPTS EXERCISED
-------------------
    - Retry classification: `httpx.TransportError` (connect/read errors,
      timeouts) and 429/5xx are retryable; other 4xx are not; cancellation
      is never retried.
    - Capped exponential backoff with full jitter, with the RNG and the
      sleep function injected so tests are exact and take no wall time.
    - `Retry-After` in both forms (delta-seconds and HTTP-date, parsed with
      `email.utils.parsedate_to_datetime`), capped so a broken server
      can't make you sleep for a day.
    - Closing discarded responses (`await response.aclose()`) so the
      connection returns to the pool.
    - A circuit breaker state machine CLOSED -> OPEN -> HALF_OPEN -> CLOSED
      with an injected monotonic clock, and why asyncio's single-threaded
      model means no lock is needed as long as state changes happen between
      `await`s.
    - `typing.Protocol` for structural typing: `httpx.AsyncClient`, the
      breaker and the retrying client are all interchangeable `Sender`s.
    - Faking HTTP with `httpx.MockTransport` -- the real client stack, no
      sockets.

SPEC
----
    class Sender(Protocol):
        async def send(self, request: httpx.Request) -> httpx.Response: ...

    @dataclass(frozen=True)
    class RetryPolicy:
        max_attempts: int = 3         # total attempts incl. the first, >= 1
        base_delay: float = 0.1       # seconds
        max_delay: float = 5.0        # cap on any single computed sleep
        max_retry_after: float = 30.0 # cap on a server-supplied Retry-After

    def is_retryable_status(status: int) -> bool
        "429 or 500-599."

    def is_idempotent(request: httpx.Request) -> bool
        "GET/HEAD/OPTIONS/PUT/DELETE/TRACE, or any request that carries an
         Idempotency-Key header."

    def backoff_delay(policy, attempts_made: int, rng: Callable[[], float]) -> float
        "Delay before the next attempt after `attempts_made` (>= 1) attempts:
         rng() * min(max_delay, base_delay * 2 ** (attempts_made - 1))."

    def parse_retry_after(value: str | None, now: datetime | None = None) -> float | None
        "Seconds to wait, from delta-seconds ('120') or an HTTP-date
         ('Wed, 21 Oct 2015 07:28:00 GMT'). None if absent or unparseable.
         A date in the past means 0."

    class RetriesExhaustedError(Exception):
        attempts: int                 # raised `from` the last transport error

    class RetryingClient:
        def __init__(self, sender, policy=RetryPolicy(), *,
                     sleep=asyncio.sleep, rng=random.random) -> None
        async def send(self, request: httpx.Request) -> httpx.Response

    Retry rules for `RetryingClient.send`:
      - At most `max_attempts` attempts in total.
      - Non-idempotent requests get exactly one attempt.
      - Transport error: retry if attempts remain, else raise
        `RetriesExhaustedError(attempts)` chained `from` the last error.
      - Retryable status: close the response, retry if attempts remain,
        else *return* the last response (the caller sees the real 503 and
        its body/headers, not a generic error).
      - Anything else (2xx/3xx/other 4xx): return immediately.
      - Sleep between attempts = parsed Retry-After (capped at
        `max_retry_after`) if the response had one, else `backoff_delay`.
      - `CircuitOpenError` and `asyncio.CancelledError` propagate at once.

    class CircuitState(Enum): CLOSED, OPEN, HALF_OPEN

    class CircuitOpenError(Exception): ...

    class CircuitBreaker:
        def __init__(self, sender, *, failure_threshold: int = 5,
                     cooldown: float = 30.0, clock=time.monotonic) -> None
        @property
        def state(self) -> CircuitState   # reports HALF_OPEN once cooldown passed
        async def send(self, request: httpx.Request) -> httpx.Response

    Breaker rules:
      - A "failure" is a transport error or a 5xx response. A 4xx is the
        *caller's* fault and does not move the breaker.
      - CLOSED: pass through; `failure_threshold` consecutive failures trip
        it to OPEN. Any success resets the consecutive-failure count.
      - OPEN: raise `CircuitOpenError` without touching the wrapped sender,
        until `cooldown` seconds have passed, then become HALF_OPEN.
      - HALF_OPEN: exactly one trial request is let through; concurrent
        callers get `CircuitOpenError`. Success -> CLOSED; failure (or the
        trial being cancelled) -> OPEN with a fresh cooldown.

ACCEPTANCE CRITERIA
--------------------
    - A fake upstream that fails N times then succeeds is called exactly
      N + 1 times, and a 400 is never retried.
    - A POST without an Idempotency-Key is attempted once even on 503; the
      same POST with the header is retried.
    - Backoff grows exponentially and is capped (asserted exactly with an
      injected rng, not with range checks).
    - Retry-After overrides the computed backoff and is capped.
    - Cancelling the caller during a backoff sleep stops further attempts.
    - The breaker trips after the threshold, fails fast without calling the
      sender, lets exactly one trial through after the cooldown, and a
      failed trial reopens it.
    - The whole test file runs in well under a second (no real sleeping).

Everything below is a stub. Fill in the `# TODO:` markers. Full type hints
are already in place -- match them.
"""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol

import httpx

SleepFunc = Callable[[float], Awaitable[None]]


class Sender(Protocol):
    async def send(self, request: httpx.Request) -> httpx.Response: ...


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay: float = 0.1
    max_delay: float = 5.0
    max_retry_after: float = 30.0

    # TODO: validate in __post_init__ (max_attempts >= 1, delays >= 0).


class RetriesExhaustedError(Exception):
    def __init__(self, attempts: int) -> None:
        super().__init__(f"request failed after {attempts} attempt(s)")
        self.attempts = attempts


class CircuitOpenError(Exception):
    pass


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


def is_retryable_status(status: int) -> bool:
    # TODO: 429 or any 5xx.
    raise NotImplementedError


def is_idempotent(request: httpx.Request) -> bool:
    # TODO: idempotent HTTP method, or an Idempotency-Key header present.
    raise NotImplementedError


def backoff_delay(
    policy: RetryPolicy, attempts_made: int, rng: Callable[[], float]
) -> float:
    # TODO: rng() * min(max_delay, base_delay * 2 ** (attempts_made - 1)).
    #  Guard against float overflow for huge attempt counts (2 ** 2000).
    raise NotImplementedError


def parse_retry_after(value: str | None, now: datetime | None = None) -> float | None:
    # TODO:
    #  - None/empty -> None
    #  - all digits -> float(value)
    #  - otherwise try email.utils.parsedate_to_datetime; seconds until that
    #    moment (clamped at 0); unparseable -> None
    raise NotImplementedError


class RetryingClient:
    def __init__(
        self,
        sender: Sender,
        policy: RetryPolicy | None = None,
        *,
        sleep: SleepFunc = asyncio.sleep,
        rng: Callable[[], float] = random.random,
    ) -> None:
        # TODO: store collaborators; default policy = RetryPolicy().
        raise NotImplementedError

    async def send(self, request: httpx.Request) -> httpx.Response:
        # TODO: the retry loop described in the SPEC.
        #  - attempts allowed = policy.max_attempts if idempotent else 1
        #  - catch httpx.TransportError only (never bare Exception: that
        #    would swallow CircuitOpenError and programming errors)
        #  - on a retryable status with attempts left: read Retry-After,
        #    `await response.aclose()`, then sleep
        #  - on exhaustion: return last response, or raise
        #    RetriesExhaustedError(n) from the last transport error
        raise NotImplementedError


class CircuitBreaker:
    def __init__(
        self,
        sender: Sender,
        *,
        failure_threshold: int = 5,
        cooldown: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        # TODO: fields: sender, threshold, cooldown, clock, current state,
        #  consecutive failures, opened_at, trial_in_flight flag.
        raise NotImplementedError

    @property
    def state(self) -> CircuitState:
        # TODO: OPEN whose cooldown has elapsed reports HALF_OPEN.
        raise NotImplementedError

    async def send(self, request: httpx.Request) -> httpx.Response:
        # TODO: the state machine in the SPEC. Decide "may I call?" before
        #  the await, record the outcome after it. Use try/finally so a
        #  cancelled HALF_OPEN trial doesn't leave the breaker stuck with
        #  trial_in_flight=True forever.
        raise NotImplementedError


if __name__ == "__main__":
    # TODO: build an httpx.MockTransport that returns 503 twice then 200,
    #  wrap it as RetryingClient(CircuitBreaker(httpx.AsyncClient(...))),
    #  send one GET and print the status and the attempt count.
    print("Implement the TODOs, then run the tests: pytest 03_api_client_with_retries/")


# ---------------------------------------------------------------------------
# Hints
# ---------------------------------------------------------------------------
# - `httpx.AsyncClient(transport=httpx.MockTransport(handler))` runs the
#   real client stack (headers, response parsing, closing) against a plain
#   function `handler(request) -> httpx.Response`. That's the idiomatic way
#   to fake HTTP in httpx tests -- no monkeypatching, no sockets.
# - Build requests with `client.build_request(...)` or `httpx.Request(...)`
#   and pass them to `send`. A request built with `content=b"..."` can be
#   sent many times; one built from an async generator body can't -- call
#   `await request.aread()` once before the loop to buffer it (and note the
#   memory trade-off for huge uploads).
# - Cancellation needs no special code in asyncio: `await sleep(d)` raises
#   `CancelledError` when the task is cancelled. Your only job is not to
#   swallow it -- `except httpx.TransportError` doesn't catch it, while a
#   careless `except BaseException` would.
# - The breaker needs no lock: asyncio runs one coroutine at a time on a
#   loop, and nothing can interleave between two lines that contain no
#   `await`. Do the check-and-mark ("I am the trial") in one await-free
#   block. If the breaker had to be shared across *threads*, you would need
#   a `threading.Lock` around the same blocks.
#
# Pitfalls
# --------
# - Treating `httpx.TimeoutException` on a POST as safe to retry: the server
#   may have processed it. Idempotency is decided by the request, not by
#   the error type.
# - Retrying inside the breaker instead of outside it. Order matters:
#   RetryingClient(CircuitBreaker(client)) lets the breaker see each
#   attempt and stop the loop with CircuitOpenError; the reverse order
#   counts a whole retry loop as one breaker outcome.
# - Sleeping with `time.sleep` in async code -- it blocks the whole event
#   loop, not just this request.
# - Not resetting the failure counter on success: sporadic failures spread
#   over hours would eventually trip the breaker.
#
# Stretch goals
# -------------
# - A retry *budget* (e.g. retries may be at most 10% of requests over a
#   sliding window), which is what gRPC and Envoy use to cap amplification.
# - One breaker per host (a dict of breakers keyed by `request.url.host`).
# - Emit metrics hooks (attempts, sleeps, state transitions) via a callback.
# - Put the 15_rate_limiter token bucket in front to cap outbound QPS.
