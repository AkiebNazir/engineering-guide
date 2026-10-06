"""
22 - Profiling & optimization
===============================

WHAT WE'RE BUILDING
--------------------
A small "log line aggregation" workload implemented two ways - a `_naive`
version with the allocation habits most Python code accidentally has, and
a `_fast` version that fixes them - plus a reusable profiling/benchmarking
toolkit (`profile_call`, `peak_memory_of`, `time_it`) built on the stdlib
(`cProfile`, `tracemalloc`, `timeit`) that you'd reach for on a real
service before touching a line of "optimized" code.

Workload: given an iterable of `"key,value"` log lines, compute the sum of
`value` per `key`. `aggregate_naive` and `aggregate_fast` must produce
identical results; the exercise is entirely about *how* they get there.

WHY THIS MATTERS IN REAL SYSTEMS
-----------------------------------
"Just optimize it" without measurement first is how you spend a day
shaving 2% off a function that's 1% of runtime while the actual hot path
sits untouched. The discipline this problem drills:

1. **Profile before optimizing.** `cProfile` tells you *where* time goes
   (call counts, cumulative time per function) - guessing is not a
   substitute, and intuition about "what's slow in Python" is frequently
   wrong (string formatting and attribute lookups are cheaper than people
   assume; needless list materialization and repeated `+=` concatenation
   are usually the real cost).
2. **`tracemalloc` for allocations.** Time isn't the only cost - a
   pipeline that materializes three intermediate lists to process a
   10M-line file will OOM a container long before it's "slow." Tracking
   peak memory, not just wall time, is what catches this.
3. **Reduce allocations, don't just micro-optimize.** Generators instead
   of building intermediate lists; avoiding `list.copy()`/slicing when a
   view or a single pass would do; `__slots__` on classes instantiated in
   bulk (removes the per-instance `__dict__`, which is real, measurable
   memory - `sys.getsizeof` plus `tracemalloc` on a large collection of
   instances makes this concrete instead of folklore).
4. **Benchmark honestly.** CPython has no JIT (3.13's experimental JIT is
   off by default) - `timeit` numbers are real wall-clock interpreter
   cost, but only if you (a) warm up (import/first-call overhead,
   attribute-cache effects), (b) run enough iterations that background
   noise averages out, (c) take the *minimum* of several repeats (per the
   `timeit` docs - min, not mean, is the right summary statistic for
   noise-dominated measurements), and (d) actually consume the return
   value inside the timed code, or the optimizer-adjacent risk is that a
   pure computation whose result is thrown away gets partially skipped by
   CPython's peephole optimizer in a way that doesn't reflect real usage
   (less of an issue than in compiled/JITed languages, but a benchmark
   that ignores its own output is still measuring the wrong thing if any
   part of the call chain short-circuits on an unused result).

CONCEPTS COVERED
------------------
- `cProfile.Profile` as a context manager; `pstats.Stats` sorting/formatting
- `tracemalloc` start/stop, `get_traced_memory()` for peak-memory deltas
- Generators over eagerly-built lists for a linear pipeline
- `__slots__` to remove per-instance `__dict__` overhead
- `timeit.repeat` with explicit warm-up, `min()` over repeats, and
  result-consumption to keep the benchmark honest

THE SPEC
---------
`aggregate_naive(lines: list[str]) -> dict[str, float]`
    Parses "key,value" lines into totals per key. Deliberately allocates
    more than necessary: builds an intermediate list of parsed tuples,
    another list of keys, and uses string concatenation in a loop
    somewhere in the pipeline (this is the "code that looks fine in a
    code review" version - the point is that it profiles worse).

`aggregate_fast(lines: Iterable[str]) -> dict[str, float]`
    Same result, single pass, no intermediate list materialization -
    parses and accumulates in one generator-driven loop.

`Point` / `PointSlotted`
    Two otherwise-identical classes (`x: float`, `y: float`,
    `distance_from_origin() -> float`); `PointSlotted` declares
    `__slots__ = ("x", "y")`. Building a large list of each and comparing
    `tracemalloc` peak usage should show `PointSlotted` using
    meaningfully less memory.

Profiling/benchmarking toolkit:
    `profile_call(fn, *args, **kwargs) -> str`
        Runs `fn(*args, **kwargs)` under `cProfile`, returns a
        cumulative-time-sorted text report (via `pstats.Stats`).
    `peak_memory_of(fn, *args, **kwargs) -> int`
        Runs `fn(*args, **kwargs)` under `tracemalloc`, returns peak
        traced memory in bytes.
    `time_it(fn, *args, number=1000, repeat=5, **kwargs) -> float`
        Returns the minimum per-call time in seconds across `repeat`
        batches of `number` calls each, after one untimed warm-up call.
        The timed callable must consume `fn`'s return value (e.g. via a
        cheap reduction) so the benchmark reflects real use, not a
        computation whose result nothing observes.

ACCEPTANCE CRITERIA
---------------------
1. `aggregate_naive` and `aggregate_fast` produce identical results for
   the same input across varied inputs (property-style or table-driven).
2. `peak_memory_of(aggregate_fast, big_input) <
   peak_memory_of(aggregate_naive, big_input)` for a sufficiently large
   input (the fast version must demonstrably allocate less peak memory).
3. A list of `PointSlotted` instances uses less peak traced memory than
   an equal-length list of `Point` instances for the same data.
4. `profile_call` returns a string containing the profiled function's
   name and is non-empty.
5. `time_it` returns a positive float and does not raise when timing
   either aggregate function.
6. mypy-clean, black-formatted, ruff-clean.
"""

from __future__ import annotations

import cProfile  # noqa: F401 - used once you implement profile_call
import io  # noqa: F401 - used once you implement profile_call
import pstats  # noqa: F401 - used once you implement profile_call
import timeit  # noqa: F401 - used once you implement time_it
import tracemalloc  # noqa: F401 - used once you implement peak_memory_of
from collections.abc import Callable, Iterable
from typing import Any


# ---------------------------------------------------------------------------
# The workload: naive vs fast.
# ---------------------------------------------------------------------------
def _parse_line(line: str) -> tuple[str, float]:
    """Parse one "key,value" line. Raises ValueError on malformed input."""
    key, _, raw_value = line.partition(",")
    return key, float(raw_value)


def aggregate_naive(lines: list[str]) -> dict[str, float]:
    """Sum `value` per `key` - deliberately allocation-heavy version.

    TODO: implement this in the "looks fine, profiles badly" style
    described in the module docstring:
      1. Build a list of parsed (key, value) tuples from ALL of `lines`
         up front (`[_parse_line(l) for l in lines]`) instead of
         streaming.
      2. Build a separate list of just the keys via a second pass over
         that list (`[t[0] for t in parsed]`) - unused beyond
         demonstrating a redundant allocation; use it to build
         `sorted(set(keys))` before accumulating, to give this version
         genuine extra work the fast version skips.
      3. Accumulate totals into a dict by iterating the parsed list.
    """
    raise NotImplementedError("TODO: implement aggregate_naive")


def aggregate_fast(lines: Iterable[str]) -> dict[str, float]:
    """Sum `value` per `key` - single-pass, no intermediate materialization.

    TODO: iterate `lines` once, parse each line with `_parse_line`, and
    accumulate directly into a result dict using `dict.get(key, 0.0)` (or
    `collections.defaultdict(float)` - pick one and justify it in a
    comment). No intermediate list of parsed tuples or keys.
    """
    raise NotImplementedError("TODO: implement aggregate_fast")


# ---------------------------------------------------------------------------
# __slots__ vs a plain class.
# ---------------------------------------------------------------------------
class Point:
    """A plain point - each instance carries a `__dict__`."""

    def __init__(self, x: float, y: float) -> None:
        # TODO: self.x = x; self.y = y
        raise NotImplementedError("TODO: implement Point.__init__")

    def distance_from_origin(self) -> float:
        # TODO: return (self.x ** 2 + self.y ** 2) ** 0.5
        raise NotImplementedError("TODO: implement Point.distance_from_origin")


class PointSlotted:
    """Same shape as `Point`, but with `__slots__` - no per-instance `__dict__`."""

    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float) -> None:
        # TODO: same body as Point.__init__
        raise NotImplementedError("TODO: implement PointSlotted.__init__")

    def distance_from_origin(self) -> float:
        # TODO: same body as Point.distance_from_origin
        raise NotImplementedError("TODO: implement PointSlotted.distance_from_origin")


# ---------------------------------------------------------------------------
# Profiling / benchmarking toolkit.
# ---------------------------------------------------------------------------
def profile_call(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
    """Run `fn(*args, **kwargs)` under cProfile; return a cumulative-time
    sorted text report.

    TODO:
      1. Create a `cProfile.Profile()`.
      2. Use it as a context manager (`with profiler:`) around the call
         to `fn(*args, **kwargs)`.
      3. Build a `pstats.Stats(profiler, stream=<io.StringIO()>)`, call
         `.sort_stats(pstats.SortKey.CUMULATIVE)` then `.print_stats()`,
         and return the StringIO's contents.
    """
    raise NotImplementedError("TODO: implement profile_call")


def peak_memory_of(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> int:
    """Run `fn(*args, **kwargs)` under tracemalloc; return peak bytes traced.

    TODO:
      1. tracemalloc.start()
      2. call fn(*args, **kwargs)
      3. _current, peak = tracemalloc.get_traced_memory()
      4. tracemalloc.stop()  (in a try/finally so a raise from fn doesn't
         leave tracing on)
      5. return peak
    """
    raise NotImplementedError("TODO: implement peak_memory_of")


def time_it(
    fn: Callable[..., Any],
    *args: Any,
    number: int = 1000,
    repeat: int = 5,
    **kwargs: Any,
) -> float:
    """Return the minimum per-call time in seconds across `repeat` batches
    of `number` calls, after one untimed warm-up call.

    TODO:
      1. Call fn(*args, **kwargs) once, unwrapped, to warm up (import
         machinery, attribute caches, etc. - do not include this call in
         the measurement).
      2. Build a zero-arg callable that calls fn(*args, **kwargs) and
         *consumes* the result (e.g. `len(result)` or `sum(result.values())`
         if it's a dict, discarding into a variable is not enough - the
         point is to do real work with the return value the way a caller
         would, not to leave a computed-and-discarded value that an
         optimizing runtime might treat differently from a real call
         site).
      3. `timeit.repeat(that_callable, number=number, repeat=repeat)`
         returns a list of `repeat` total times (each for `number` calls).
      4. Return `min(results) / number` - the minimum (not mean) per-call
         time, per the `timeit` module docs' guidance that min is the
         right summary statistic when noise is one-sided (only ever adds
         time, never subtracts it).
    """
    raise NotImplementedError("TODO: implement time_it")


# ---------------------------------------------------------------------------
# HINTS
# -----
# - `cProfile.Profile()` supports the context-manager protocol directly
#   since Python 3.8 - no need for `.enable()`/`.disable()` calls.
# - `pstats.SortKey.CUMULATIVE` sorts by cumulative time (including time
#   spent in callees) - the metric you want when hunting for "which call
#   tree is expensive", as opposed to `SortKey.TIME` (self time only,
#   useful for finding a hot leaf function).
# - `tracemalloc.get_traced_memory()` returns `(current, peak)` - peak is
#   the high-water mark since `start()`, not the memory at the moment you
#   call it, which is what makes it useful for "what's the worst-case
#   footprint of this call" rather than needing to sample continuously.
# - For the naive-vs-fast memory comparison, use an input large enough
#   (thousands of lines) that fixed overhead (module import, dict
#   creation) doesn't drown out the difference.
# - `sys.getsizeof(obj)` on a single `Point` vs `PointSlotted` instance
#   also demonstrates the difference directly (no `__dict__` on the
#   slotted one), but doesn't account for the instances' attribute
#   values' own sizes - `tracemalloc` over a whole list is the more
#   complete/realistic comparison used by the tests here.
#
# COMMON PITFALLS
# ---------------
# - Timing with `time.time()` around a single call - too noisy (OS
#   scheduling jitter, cache warm-up) to be meaningful; always batch many
#   calls and take a `min()` over repeated batches.
# - Warming up *inside* the timed batch instead of before it - the first
#   call in a fresh process pays import/attribute-cache costs a real
#   long-running service wouldn't pay repeatedly, so it skews small
#   `number` values badly.
# - Forgetting `tracemalloc.stop()` (or leaving it enabled on an
#   exception) - tracing has real overhead and stays on process-wide
#   until stopped.
# - Comparing profiler *wall time* output across machines/runs as if it
#   were a stable benchmark - `cProfile` is for finding *where* time
#   goes (call counts, relative cost), not for precise timing (its
#   instrumentation overhead itself perturbs timing) - that's what
#   `timeit` is for.
#
# STRETCH GOALS
# --------------
# - Add a third `aggregate_fast_defaultdict` variant using
#   `collections.defaultdict(float)` and benchmark it against the
#   `dict.get` version - the difference is usually small but real at
#   scale, and worth seeing measured rather than assumed.
# - Extend `profile_call` to accept a `sort_key` parameter and compare
#   `CUMULATIVE` vs `TIME` sorted output on the same profiled call.
# - Try `python -X importtime` separately (outside this module) to see
#   import-time cost profiling, a different (startup-time) dimension
#   from the runtime profiling this module covers.
