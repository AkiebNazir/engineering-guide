from __future__ import annotations

import asyncio
import time
from importlib import import_module
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# The module name starts with a digit, so it can't appear in an `import`
# statement; pytest puts this directory on sys.path, so import it by string.
_solution = import_module("15_rate_limiter_solution")
KeyedRateLimiter: Any = _solution.KeyedRateLimiter
FixedWindowLimiter: Any = _solution.FixedWindowLimiter


class FakeClock:
    """Manually advanced clock. Tests use binary-exact steps (0.25, 0.125)."""

    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


# --- construction -------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"rate": 0, "burst": 1},
        {"rate": -1, "burst": 1},
        {"rate": float("nan"), "burst": 1},
        {"rate": 1, "burst": 0},
        {"rate": 1, "burst": 1, "idle_ttl": 0},
    ],
)
def test_invalid_arguments(kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        KeyedRateLimiter(**kwargs)


# --- allow ----------------------------------------------------------------


def test_fresh_key_allows_exactly_burst(clock: FakeClock) -> None:
    lim = KeyedRateLimiter(rate=1, burst=3, clock=clock)
    assert [lim.allow("k") for _ in range(4)] == [True, True, True, False]


def test_refill_is_continuous_and_keeps_fractions(clock: FakeClock) -> None:
    lim = KeyedRateLimiter(rate=4, burst=1, clock=clock)  # one token / 0.25 s
    assert lim.allow("k")
    clock.advance(0.125)  # half a token: not enough...
    assert not lim.allow("k")
    clock.advance(0.125)  # ...but the half is kept, so now it's a whole one
    assert lim.allow("k")
    assert not lim.allow("k")


def test_tokens_capped_at_burst_after_long_idle(clock: FakeClock) -> None:
    lim = KeyedRateLimiter(rate=10, burst=2, idle_ttl=10**9, clock=clock)
    lim.allow("k")
    clock.advance(3600)
    assert [lim.allow("k") for _ in range(3)] == [True, True, False]


def test_allow_n_is_all_or_nothing(clock: FakeClock) -> None:
    lim = KeyedRateLimiter(rate=1, burst=5, clock=clock)
    assert lim.allow("k", 3)
    assert not lim.allow("k", 3)  # only 2 left: refuse and consume nothing
    assert lim.allow("k", 2)
    assert not lim.allow("k")


def test_n_larger_than_burst_never_allowed(clock: FakeClock) -> None:
    lim = KeyedRateLimiter(rate=1, burst=2, clock=clock)
    assert not lim.allow("k", 3)
    with pytest.raises(ValueError):
        lim.allow("k", 0)


def test_keys_are_independent(clock: FakeClock) -> None:
    lim = KeyedRateLimiter(rate=1, burst=1, clock=clock)
    assert lim.allow("a")
    assert not lim.allow("a")
    assert lim.allow("b")
    assert lim.allow(("tenant", 7))  # any hashable key


def test_retry_after(clock: FakeClock) -> None:
    lim = KeyedRateLimiter(rate=4, burst=2, clock=clock)
    assert lim.retry_after("k") == 0.0
    lim.allow("k", 2)
    assert lim.retry_after("k") == 0.25
    assert lim.retry_after("k", 2) == 0.5
    clock.advance(0.25)
    assert lim.retry_after("k") == 0.0
    assert lim.allow("k")  # retry_after itself consumed nothing


def test_clock_going_backwards_never_removes_tokens(clock: FakeClock) -> None:
    lim = KeyedRateLimiter(rate=1, burst=2, clock=clock)
    lim.allow("k")
    clock.advance(-100)
    assert lim.allow("k")


@settings(max_examples=200, deadline=None)
@given(
    rate=st.sampled_from([0.5, 1.0, 4.0, 16.0]),
    burst=st.integers(min_value=1, max_value=8),
    ops=st.lists(
        st.tuples(st.sampled_from([0.0, 0.03125, 0.125, 0.5, 2.0]), st.integers(1, 4)),
        max_size=60,
    ),
)
def test_property_never_exceeds_burst_plus_rate_times_elapsed(
    rate: float, burst: int, ops: list[tuple[float, int]]
) -> None:
    clock = FakeClock(0.0)
    lim = KeyedRateLimiter(rate=rate, burst=burst, clock=clock)
    granted = 0
    for dt, n in ops:
        clock.advance(dt)
        if lim.allow("k", n):
            granted += n
        assert granted <= burst + rate * clock.t + 1e-9


# --- eviction -------------------------------------------------------------


def test_sweep_evicts_only_idle_full_buckets(clock: FakeClock) -> None:
    lim = KeyedRateLimiter(rate=1, burst=4, idle_ttl=10, clock=clock)
    lim.allow("idle")
    clock.advance(5)
    lim.allow("recent")
    clock.advance(7)
    # "idle": unused for 12 s and refilled to full -> evicted.
    # "recent": unused for only 7 s -> kept.
    assert lim.sweep() == 1
    assert len(lim) == 1
    # Eviction was invisible: the evicted key comes back with a full bucket,
    # exactly what it would have had anyway.
    assert [lim.allow("idle") for _ in range(5)] == [True] * 4 + [False]


def test_sweep_keeps_bucket_that_is_not_yet_full(clock: FakeClock) -> None:
    lim = KeyedRateLimiter(rate=0.5, burst=10, idle_ttl=5, clock=clock)
    lim.allow("slow", 10)  # needs 20 s to refill
    clock.advance(5)
    assert lim.sweep() == 0  # idle long enough, but evicting would gift tokens
    clock.advance(15)
    assert lim.sweep() == 1


def test_sweep_runs_automatically_and_bounds_memory(clock: FakeClock) -> None:
    lim = KeyedRateLimiter(rate=100, burst=1, idle_ttl=1, clock=clock)
    for i in range(10_000):
        lim.allow(f"ip-{i}")
        clock.advance(0.001)
    # Without eviction this would be 10,000 keys; with amortised sweeping it
    # stays around rate-of-new-keys * idle_ttl.
    assert len(lim) < 2_500


# --- wait -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_wait_returns_immediately_when_tokens_available() -> None:
    lim = KeyedRateLimiter(rate=1, burst=2)
    t0 = time.monotonic()
    await lim.wait("k")
    await lim.wait("k")
    assert time.monotonic() - t0 < 0.05


@pytest.mark.asyncio
async def test_wait_sleeps_once_for_the_computed_duration(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = FakeClock()
    lim = KeyedRateLimiter(rate=4, burst=1, clock=clock)
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(_solution.asyncio, "sleep", fake_sleep)
    await lim.wait("k")  # bucket full: no sleep
    await lim.wait("k")  # debt 1 token -> 0.25 s
    await lim.wait("k")  # debt 2 tokens -> 0.5 s (queued behind the previous)
    assert sleeps == [0.25, 0.5]


@pytest.mark.asyncio
async def test_concurrent_waiters_are_paced_in_arrival_order() -> None:
    rate = 50.0  # one token every 20 ms
    lim = KeyedRateLimiter(rate=rate, burst=1)
    finished: list[tuple[int, float]] = []
    t0 = time.monotonic()

    async def worker(i: int) -> None:
        await lim.wait("k")
        finished.append((i, time.monotonic() - t0))

    async with asyncio.TaskGroup() as tg:
        for i in range(5):
            tg.create_task(worker(i))

    assert [i for i, _ in finished] == [0, 1, 2, 3, 4]
    # The 5th call needs 4 refills: ~80 ms. Generous upper bound for CI.
    assert 0.07 <= finished[-1][1] < 0.5


@pytest.mark.asyncio
async def test_cancelled_wait_refunds_tokens() -> None:
    clock = FakeClock()
    lim = KeyedRateLimiter(rate=1, burst=1, clock=clock)
    assert lim.allow("k")  # empty the bucket
    with pytest.raises(TimeoutError):
        async with asyncio.timeout(0.02):
            await lim.wait("k")  # would sleep 1 s (fake clock never moves)
    # The reservation was returned: exactly one refill later, one token.
    clock.advance(1)
    assert lim.allow("k")
    assert not lim.allow("k")


@pytest.mark.asyncio
async def test_wait_rejects_n_above_burst() -> None:
    lim = KeyedRateLimiter(rate=1, burst=2)
    with pytest.raises(ValueError):
        await lim.wait("k", 3)


@pytest.mark.asyncio
async def test_allow_refused_while_waiters_hold_debt(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = FakeClock()
    lim = KeyedRateLimiter(rate=1, burst=1, clock=clock)
    gate = asyncio.Event()

    async def blocked_sleep(delay: float) -> None:
        await gate.wait()

    real_sleep = asyncio.sleep
    monkeypatch.setattr(_solution.asyncio, "sleep", blocked_sleep)
    lim.allow("k")
    task = asyncio.create_task(lim.wait("k"))
    await real_sleep(0)  # let the waiter run up to its (blocked) sleep
    clock.advance(0.5)
    assert not lim.allow("k")  # half a token of a whole-token debt: still negative
    gate.set()
    await task


# --- fixed window contrast ------------------------------------------------


def test_fixed_window_boundary_burst_vs_token_bucket() -> None:
    clock = FakeClock(0.0)
    fixed = FixedWindowLimiter(limit=10, window=60, clock=clock)
    bucket = KeyedRateLimiter(rate=10 / 60, burst=10, clock=clock)

    clock.t = 59.875  # just before the minute boundary
    fixed_ok = sum(fixed.allow("k") for _ in range(10))
    bucket_ok = sum(bucket.allow("k") for _ in range(10))
    clock.t = 60.0  # 125 ms later: new window
    fixed_ok += sum(fixed.allow("k") for _ in range(10))
    bucket_ok += sum(bucket.allow("k") for _ in range(10))

    assert fixed_ok == 20  # 2x the limit in 125 ms
    assert bucket_ok == 10  # burst, plus ~0.02 tokens of refill


def test_fixed_window_resets_each_window() -> None:
    clock = FakeClock(0.0)
    fixed = FixedWindowLimiter(limit=2, window=1, clock=clock)
    assert [fixed.allow("k") for _ in range(3)] == [True, True, False]
    clock.advance(1)
    assert fixed.allow("k")
