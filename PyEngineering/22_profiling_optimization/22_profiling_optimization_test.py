"""Tests for `22_profiling_optimization_solution.py`.

Run: .venv/bin/pytest 22_profiling_optimization/ -v
"""

from __future__ import annotations

import random
from importlib import import_module
from typing import Any

import pytest

_solution = import_module("22_profiling_optimization_solution")
aggregate_naive = _solution.aggregate_naive
aggregate_fast = _solution.aggregate_fast
Point = _solution.Point
PointSlotted = _solution.PointSlotted
profile_call = _solution.profile_call
peak_memory_of = _solution.peak_memory_of
time_it = _solution.time_it


def _make_lines(n: int, num_keys: int = 20, seed: int = 0) -> list[str]:
    rng = random.Random(seed)
    keys = [f"key-{i}" for i in range(num_keys)]
    return [f"{rng.choice(keys)},{rng.uniform(-100, 100):.4f}" for _ in range(n)]


# ---------------------------------------------------------------------------
# Equivalence
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("n", [0, 1, 5, 500])
def test_naive_and_fast_agree(n: int) -> None:
    lines = _make_lines(n)
    naive_result = aggregate_naive(lines)
    fast_result = aggregate_fast(lines)
    assert naive_result.keys() == fast_result.keys()
    for key in naive_result:
        assert naive_result[key] == pytest.approx(fast_result[key])


def test_empty_input() -> None:
    assert aggregate_naive([]) == {}
    assert aggregate_fast([]) == {}


# ---------------------------------------------------------------------------
# Memory: fast should peak lower than naive on a large input.
# ---------------------------------------------------------------------------
def test_fast_uses_less_peak_memory_than_naive() -> None:
    lines = _make_lines(20_000, num_keys=50)
    naive_peak = peak_memory_of(aggregate_naive, lines)
    fast_peak = peak_memory_of(aggregate_fast, lines)
    assert fast_peak < naive_peak


def test_slotted_points_use_less_peak_memory() -> None:
    n = 20_000
    coords = [(float(i), float(i * 2)) for i in range(n)]

    def build_plain() -> list[Any]:
        return [Point(x, y) for x, y in coords]

    def build_slotted() -> list[Any]:
        return [PointSlotted(x, y) for x, y in coords]

    plain_peak = peak_memory_of(build_plain)
    slotted_peak = peak_memory_of(build_slotted)
    assert slotted_peak < plain_peak


def test_point_and_pointslotted_behave_identically() -> None:
    p1 = Point(3.0, 4.0)
    p2 = PointSlotted(3.0, 4.0)
    assert p1.distance_from_origin() == pytest.approx(5.0)
    assert p2.distance_from_origin() == pytest.approx(5.0)
    with pytest.raises(AttributeError):
        p2.z = 1.0  # type: ignore[attr-defined]  # __slots__ forbids new attrs


# ---------------------------------------------------------------------------
# Profiling toolkit
# ---------------------------------------------------------------------------
def test_profile_call_reports_function_name() -> None:
    lines = _make_lines(1000)
    report = profile_call(aggregate_fast, lines)
    assert report
    assert "aggregate_fast" in report


def test_time_it_returns_positive_duration() -> None:
    lines = _make_lines(200)
    elapsed = time_it(aggregate_fast, lines, number=50, repeat=3)
    assert elapsed > 0.0


def test_time_it_works_on_naive_too() -> None:
    lines = _make_lines(200)
    elapsed = time_it(aggregate_naive, lines, number=50, repeat=3)
    assert elapsed > 0.0
