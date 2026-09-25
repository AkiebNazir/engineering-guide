from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime
from importlib import import_module
from typing import Any

import httpx
import pytest

# The module name starts with a digit, so it can't appear in an `import`
# statement; pytest puts this directory on sys.path, so import it by string.
_solution = import_module("03_api_client_with_retries_solution")
RetryPolicy: Any = _solution.RetryPolicy
RetryingClient: Any = _solution.RetryingClient
RetriesExhaustedError: Any = _solution.RetriesExhaustedError
CircuitBreaker: Any = _solution.CircuitBreaker
CircuitOpenError: Any = _solution.CircuitOpenError
CircuitState: Any = _solution.CircuitState
backoff_delay: Any = _solution.backoff_delay
is_retryable_status: Any = _solution.is_retryable_status
is_idempotent: Any = _solution.is_idempotent
parse_retry_after: Any = _solution.parse_retry_after

URL = "https://upstream.test/items"


class FakeUpstream:
    """A scripted upstream: each call pops the next outcome (a status code or
    an exception instance). Counts calls so tests can assert exact attempts."""

    def __init__(self, *outcomes: int | Exception, headers: dict[str, str] | None = None):
        self.outcomes = list(outcomes)
        self.headers = headers or {}
        self.calls = 0
        self.bodies: list[bytes] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls += 1
        self.bodies.append(request.content)
        outcome = self.outcomes.pop(0) if len(self.outcomes) > 1 else self.outcomes[0]
        if isinstance(outcome, Exception):
            raise outcome
        return httpx.Response(outcome, headers=self.headers)

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(self))


class RecordingSleep:
    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, delay: float) -> None:
        self.delays.append(delay)


def _policy(**overrides: Any) -> Any:
    return RetryPolicy(**{"max_attempts": 3, "base_delay": 0.1, "max_delay": 1.0, **overrides})


# ----------------------------------------------------------------- pure helpers


@pytest.mark.parametrize(
    ("status", "expected"),
    [(200, False), (302, False), (400, False), (404, False), (429, True),
     (500, True), (503, True), (599, True)],
)
def test_is_retryable_status(status: int, expected: bool) -> None:
    assert is_retryable_status(status) is expected


@pytest.mark.parametrize(
    ("method", "headers", "expected"),
    [("GET", {}, True), ("PUT", {}, True), ("DELETE", {}, True),
     ("POST", {}, False), ("PATCH", {}, False),
     ("POST", {"Idempotency-Key": "abc"}, True)],
)
def test_is_idempotent(method: str, headers: dict[str, str], expected: bool) -> None:
    assert is_idempotent(httpx.Request(method, URL, headers=headers)) is expected


def test_backoff_is_exponential_and_capped() -> None:
    policy = _policy(base_delay=0.1, max_delay=1.0)
    full = lambda: 1.0  # noqa: E731 - rng pinned to the top of the jitter range
    assert [backoff_delay(policy, n, full) for n in range(1, 7)] == pytest.approx(
        [0.1, 0.2, 0.4, 0.8, 1.0, 1.0]
    )
    assert backoff_delay(policy, 3, lambda: 0.5) == pytest.approx(0.2)
    assert backoff_delay(policy, 3, lambda: 0.0) == 0.0
    assert backoff_delay(policy, 5000, full) == pytest.approx(1.0)  # no OverflowError


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, None), ("", None), ("120", 120.0), ("0", 0.0), ("soon", None),
     ("Thu, 01 Jan 2026 00:00:30 GMT", 30.0),
     ("Wed, 31 Dec 2025 23:59:00 GMT", 0.0)],  # a date in the past -> 0
)
def test_parse_retry_after(value: str | None, expected: float | None) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    assert parse_retry_after(value, now=now) == expected


def test_policy_validation() -> None:
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)


# --------------------------------------------------------------- RetryingClient


@pytest.mark.asyncio
async def test_retries_until_success() -> None:
    upstream = FakeUpstream(503, 503, 200)
    sleep = RecordingSleep()
    async with upstream.client() as http:
        client = RetryingClient(http, _policy(), sleep=sleep, rng=lambda: 1.0)
        response = await client.send(httpx.Request("GET", URL))
    assert response.status_code == 200
    assert upstream.calls == 3
    assert sleep.delays == pytest.approx([0.1, 0.2])


@pytest.mark.asyncio
async def test_returns_last_response_when_attempts_exhausted() -> None:
    upstream = FakeUpstream(503)
    async with upstream.client() as http:
        client = RetryingClient(http, _policy(max_attempts=4), sleep=RecordingSleep())
        response = await client.send(httpx.Request("GET", URL))
    assert response.status_code == 503
    assert upstream.calls == 4


@pytest.mark.asyncio
async def test_client_error_is_not_retried() -> None:
    upstream = FakeUpstream(400)
    sleep = RecordingSleep()
    async with upstream.client() as http:
        response = await RetryingClient(http, _policy(), sleep=sleep).send(
            httpx.Request("GET", URL)
        )
    assert response.status_code == 400
    assert upstream.calls == 1
    assert sleep.delays == []


@pytest.mark.asyncio
async def test_transport_errors_retried_then_raised_with_cause() -> None:
    upstream = FakeUpstream(httpx.ConnectError("refused"))
    async with upstream.client() as http:
        client = RetryingClient(http, _policy(), sleep=RecordingSleep())
        with pytest.raises(RetriesExhaustedError) as exc_info:
            await client.send(httpx.Request("GET", URL))
    assert exc_info.value.attempts == 3
    assert isinstance(exc_info.value.__cause__, httpx.ConnectError)
    assert upstream.calls == 3


@pytest.mark.asyncio
async def test_transport_error_then_success() -> None:
    upstream = FakeUpstream(httpx.ReadTimeout("slow"), 200)
    async with upstream.client() as http:
        client = RetryingClient(http, _policy(), sleep=RecordingSleep())
        response = await client.send(httpx.Request("GET", URL))
    assert response.status_code == 200
    assert upstream.calls == 2


@pytest.mark.asyncio
async def test_non_idempotent_post_is_sent_once() -> None:
    upstream = FakeUpstream(503)
    async with upstream.client() as http:
        client = RetryingClient(http, _policy(), sleep=RecordingSleep())
        response = await client.send(httpx.Request("POST", URL, content=b"charge"))
    assert response.status_code == 503
    assert upstream.calls == 1


@pytest.mark.asyncio
async def test_post_with_idempotency_key_is_retried_and_body_replayed() -> None:
    upstream = FakeUpstream(503, 200)
    async with upstream.client() as http:
        client = RetryingClient(http, _policy(), sleep=RecordingSleep())
        request = httpx.Request(
            "POST", URL, content=b"charge", headers={"Idempotency-Key": "k1"}
        )
        response = await client.send(request)
    assert response.status_code == 200
    assert upstream.bodies == [b"charge", b"charge"]


@pytest.mark.asyncio
async def test_retry_after_overrides_backoff_and_is_capped() -> None:
    upstream = FakeUpstream(429, 429, 200, headers={"Retry-After": "7"})
    sleep = RecordingSleep()
    async with upstream.client() as http:
        client = RetryingClient(
            http, _policy(max_retry_after=5.0), sleep=sleep, rng=lambda: 1.0
        )
        await client.send(httpx.Request("GET", URL))
    assert sleep.delays == [5.0, 5.0]


@pytest.mark.asyncio
async def test_cancellation_during_backoff_stops_retrying() -> None:
    upstream = FakeUpstream(503)
    async with upstream.client() as http:
        # Real asyncio.sleep with a long backoff; the caller's deadline
        # cancels it long before the second attempt.
        client = RetryingClient(http, _policy(base_delay=10.0, max_delay=10.0), rng=lambda: 1.0)
        with pytest.raises(TimeoutError):
            async with asyncio.timeout(0.05):
                await client.send(httpx.Request("GET", URL))
    assert upstream.calls == 1


# ---------------------------------------------------------------- CircuitBreaker


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def _breaker(upstream: FakeUpstream, clock: Callable[[], float], threshold: int = 3) -> Any:
    return CircuitBreaker(
        upstream.client(), failure_threshold=threshold, cooldown=10.0, clock=clock
    )


@pytest.mark.asyncio
async def test_breaker_trips_and_fails_fast() -> None:
    upstream = FakeUpstream(500)
    breaker = _breaker(upstream, FakeClock())
    for _ in range(3):
        assert (await breaker.send(httpx.Request("GET", URL))).status_code == 500
    assert breaker.state is CircuitState.OPEN
    with pytest.raises(CircuitOpenError):
        await breaker.send(httpx.Request("GET", URL))
    assert upstream.calls == 3  # the fail-fast call never reached upstream


@pytest.mark.asyncio
async def test_breaker_half_open_trial_success_closes() -> None:
    clock = FakeClock()
    upstream = FakeUpstream(500, 500, 500, 200)
    breaker = _breaker(upstream, clock)
    for _ in range(3):
        await breaker.send(httpx.Request("GET", URL))
    clock.now += 10.0
    assert breaker.state is CircuitState.HALF_OPEN
    assert (await breaker.send(httpx.Request("GET", URL))).status_code == 200
    assert breaker.state is CircuitState.CLOSED


@pytest.mark.asyncio
async def test_breaker_half_open_trial_failure_reopens_with_fresh_cooldown() -> None:
    clock = FakeClock()
    upstream = FakeUpstream(500)
    breaker = _breaker(upstream, clock, threshold=1)
    await breaker.send(httpx.Request("GET", URL))
    clock.now += 10.0
    await breaker.send(httpx.Request("GET", URL))  # the trial, fails
    assert breaker.state is CircuitState.OPEN
    clock.now += 9.0
    assert breaker.state is CircuitState.OPEN
    clock.now += 1.0
    assert breaker.state is CircuitState.HALF_OPEN


@pytest.mark.asyncio
async def test_breaker_allows_exactly_one_concurrent_trial() -> None:
    clock = FakeClock()
    release = asyncio.Event()
    calls = 0

    async def slow_handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        await release.wait()
        return httpx.Response(200)

    breaker = CircuitBreaker(
        httpx.AsyncClient(transport=httpx.MockTransport(slow_handler)),
        failure_threshold=1, cooldown=10.0, clock=clock,
    )
    breaker._trip()  # start OPEN without scripting failures
    clock.now += 10.0

    trial = asyncio.create_task(breaker.send(httpx.Request("GET", URL)))
    await asyncio.sleep(0)  # let the trial get admitted and block
    with pytest.raises(CircuitOpenError):
        await breaker.send(httpx.Request("GET", URL))
    release.set()
    assert (await trial).status_code == 200
    assert calls == 1
    assert breaker.state is CircuitState.CLOSED


@pytest.mark.asyncio
async def test_breaker_success_resets_failure_count_and_4xx_is_not_a_failure() -> None:
    upstream = FakeUpstream(500, 500, 200, 500, 500, 404, 404, 404, 500)
    breaker = _breaker(upstream, FakeClock(), threshold=3)
    for _ in range(9):
        await breaker.send(httpx.Request("GET", URL))
    assert breaker.state is CircuitState.CLOSED


@pytest.mark.asyncio
async def test_retrying_client_stops_when_breaker_opens() -> None:
    upstream = FakeUpstream(500)
    breaker = _breaker(upstream, FakeClock(), threshold=2)
    client = RetryingClient(breaker, _policy(max_attempts=5), sleep=RecordingSleep())
    with pytest.raises(CircuitOpenError):
        await client.send(httpx.Request("GET", URL))
    assert upstream.calls == 2
