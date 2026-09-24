"""
22 - Profiling & optimization - Reference Solution
=====================================================

See `22_profiling_optimization_explanation.py` for the full spec,
rationale, and acceptance criteria.
"""

from __future__ import annotations

import io
import pstats
import timeit
import tracemalloc
from collections.abc import Callable, Iterable
from cProfile import Profile
from typing import Any


# ---------------------------------------------------------------------------
# The workload: naive vs fast.
# ---------------------------------------------------------------------------
def _parse_line(line: str) -> tuple[str, float]:
    key, _, raw_value = line.partition(",")
    return key, float(raw_value)


def aggregate_naive(lines: list[str]) -> dict[str, float]:
    """Deliberately allocation-heavy: materializes a parsed-tuple list and
    a separate keys list before accumulating."""
    # Pass 1: parse everything into a list up front. For N lines this is
    # one full extra list of N tuples alive at once, for no benefit - the
    # accumulation loop below could have consumed each tuple as it was
    # produced instead.
    parsed = [_parse_line(line) for line in lines]

    # Pass 2: a second full-length list, thrown away after computing a
    # sorted key set nothing downstream strictly needs (the accumulation
    # dict below discovers keys on its own). This mirrors a common
    # real-world pattern: code that computes something "just in case" or
    # for a debug log line, then never removes it once fast-pathed.
    keys = [key for key, _ in parsed]
    _known_keys = sorted(set(keys))

    # Pass 3: accumulate. Three full passes over the data for a
    # computation that needs exactly one.
    totals: dict[str, float] = {}
    for key, value in parsed:
        totals[key] = totals.get(key, 0.0) + value
    return totals


def aggregate_fast(lines: Iterable[str]) -> dict[str, float]:
    """Single pass, no intermediate list materialization.

    `dict.get(key, 0.0)` over `collections.defaultdict(float)`: the two
    perform almost identically in practice, but a plain `dict` is chosen
    here so the return type has no `defaultdict` surprises for callers
    (e.g. accidental key creation on `totals[missing_key]` lookups after
    the fact).
    """
    totals: dict[str, float] = {}
    for line in lines:
        key, value = _parse_line(line)
        totals[key] = totals.get(key, 0.0) + value
    return totals


# ---------------------------------------------------------------------------
# __slots__ vs a plain class.
# ---------------------------------------------------------------------------
class Point:
    """A plain point - each instance carries a `__dict__`."""

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def distance_from_origin(self) -> float:
        return (self.x**2 + self.y**2) ** 0.5


class PointSlotted:
    """Same shape as `Point`, but with `__slots__` - no per-instance `__dict__`."""

    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def distance_from_origin(self) -> float:
        return (self.x**2 + self.y**2) ** 0.5


# ---------------------------------------------------------------------------
# Profiling / benchmarking toolkit.
# ---------------------------------------------------------------------------
def profile_call(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
    """Run `fn(*args, **kwargs)` under cProfile; return a cumulative-time
    sorted text report."""
    profiler = Profile()
    with profiler:
        fn(*args, **kwargs)

    buffer = io.StringIO()
    stats = pstats.Stats(profiler, stream=buffer)
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stats.print_stats()
    return buffer.getvalue()


def peak_memory_of(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> int:
    """Run `fn(*args, **kwargs)` under tracemalloc; return peak bytes traced."""
    tracemalloc.start()
    try:
        fn(*args, **kwargs)
        _current, peak = tracemalloc.get_traced_memory()
    finally:
        # try/finally so an exception from fn doesn't leave tracing (which
        # has real, process-wide overhead) permanently enabled.
        tracemalloc.stop()
    return peak


def _consume(result: Any) -> object:
    """Do real work with a call's return value instead of discarding it.

    A benchmark that computes a result and immediately drops it measures
    something subtly different from a real call site, which always does
    *something* with the answer. Reducing dict/list/scalar results to a
    single cheap value keeps the consumption cost itself negligible
    relative to `fn`, while still forcing the interpreter to fully
    materialize whatever `fn` returned.
    """
    if isinstance(result, dict):
        return sum(result.values())
    if isinstance(result, (list, tuple)):
        return len(result)
    return result


def time_it(
    fn: Callable[..., Any],
    *args: Any,
    number: int = 1000,
    repeat: int = 5,
    **kwargs: Any,
) -> float:
    """Return the minimum per-call time in seconds across `repeat` batches
    of `number` calls, after one untimed warm-up call."""
    # Warm-up: pays for import machinery / attribute-lookup caches / first
    # -call overhead once, outside the measured region.
    _consume(fn(*args, **kwargs))

    def _timed_call() -> None:
        _consume(fn(*args, **kwargs))

    # timeit.repeat returns `repeat` totals, each for `number` calls.
    # timeit disables the cyclic garbage collector for the duration of
    # each batch by default, which is itself the "honest" choice for a
    # microbenchmark: it isolates the function's own cost from whenever
    # the GC happens to run, without permanently changing process state
    # (it re-enables gc after each batch if it was on).
    totals = timeit.repeat(_timed_call, number=number, repeat=repeat)

    # min(), not mean(): measurement noise from OS scheduling, other
    # processes, and cache effects is one-sided (it can only slow a run
    # down, never speed one up below its true cost), so the minimum
    # across repeats is the closest approximation to the function's
    # actual per-call cost. This is the guidance the `timeit` module
    # docs themselves give.
    return min(totals) / number


# ---------------------------------------------------------------------------
# Best practices
# ---------------------------------------------------------------------------
# - Profile (cProfile) to find *where* time goes, measure (tracemalloc)
#   to find *how much* memory a call path costs, and only then optimize -
#   in that order, every time. Optimizing from intuition alone routinely
#   targets the wrong function.
# - Prefer a single-pass, generator-friendly pipeline over "parse
#   everything into a list, then transform the list, then transform
#   that" - each intermediate list is an allocation *and* a full extra
#   pass over the data, and the cost compounds with input size.
# - `__slots__` pays off specifically when you instantiate many objects
#   of a class (rows, small value objects) - it removes the per-instance
#   `__dict__`, at the cost of losing dynamic attribute assignment and
#   (without extra work) `__weakref__` support. Skip it for classes
#   instantiated rarely; the savings there don't matter and the loss of
#   flexibility does.
# - `min()` over repeated `timeit` batches, not `mean()` - stated
#   explicitly above because it's the single most common
#   microbenchmarking mistake.
# - Always consume a benchmarked function's return value inside the timed
#   region - a call whose result is never used measures a code path a
#   real caller never takes.
#
# Alternative approaches
# -----------------------
# - `line_profiler` / `memory_profiler` (third-party) give per-*line*
#   granularity instead of per-function; not used here to stay within
#   the curriculum's stdlib-first toolchain, but worth knowing for deep
#   dives `cProfile`'s per-function granularity can't resolve.
# - `perf` (Linux) or `py-spy` (sampling profiler, works on a live
#   process without code changes) are the production-incident tools when
#   you can't/shouldn't instrument code with `cProfile` ahead of time.
# - For allocation-heavy hot paths beyond `__slots__`, `array.array` or
#   `numpy` arrays trade Python-object flexibility for packed, typed
#   memory layouts - a bigger structural change than this problem's
#   scope, appropriate once profiling shows object overhead itself (not
#   just algorithmic complexity) is the bottleneck.
