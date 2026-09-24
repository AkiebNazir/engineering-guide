"""Tests for `19_generic_utilities_solution.py`.

Run: .venv/bin/pytest 19_generic_utilities/ -v
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from importlib import import_module
from typing import Any

import pytest

# The module under test is named "19_..." which is not a valid Python
# identifier, so it can't be reached with a normal `import` statement -
# `importlib.import_module` takes an arbitrary string and works fine for a
# file-based module. mypy can't statically resolve these as *types*, only
# as runtime values, hence the `Any` annotations below.
_solution = import_module("19_generic_utilities_solution")
Some = _solution.Some
Nothing = _solution.Nothing
NOTHING = _solution.NOTHING
unwrap_or = _solution.unwrap_or
map_option = _solution.map_option
option_from_optional = _solution.option_from_optional
Ok = _solution.Ok
Err = _solution.Err
unwrap_or_result = _solution.unwrap_or_result
map_result = _solution.map_result
map_err = _solution.map_err
result_from_exception = _solution.result_from_exception
clamp = _solution.clamp


# ---------------------------------------------------------------------------
# Option[T]
# ---------------------------------------------------------------------------
def test_unwrap_or_returns_value_for_some() -> None:
    assert unwrap_or(Some(42), default=0) == 42


def test_unwrap_or_returns_default_for_nothing() -> None:
    assert unwrap_or(NOTHING, default=99) == 99


def test_nothing_module_constant_is_a_nothing_instance() -> None:
    assert isinstance(NOTHING, Nothing)
    assert NOTHING == Nothing()


def test_map_option_transforms_some() -> None:
    result: Any = map_option(Some(3), lambda x: x * 2)
    assert result == Some(6)


def test_map_option_passes_nothing_through() -> None:
    result: Any = map_option(NOTHING, lambda x: x * 2)
    assert isinstance(result, Nothing)


def test_option_from_optional_none_becomes_nothing() -> None:
    result: Any = option_from_optional(None)
    assert isinstance(result, Nothing)


def test_option_from_optional_value_becomes_some() -> None:
    result: Any = option_from_optional("hello")
    assert result == Some("hello")


def test_option_from_optional_falsy_but_non_none_becomes_some() -> None:
    # 0, "", [] are not None - they must NOT collapse to Nothing. This is
    # exactly the bug Option avoids: `value or default` would treat 0 as
    # absent, but `option_from_optional` must not.
    assert option_from_optional(0) == Some(0)
    assert option_from_optional("") == Some("")


def test_some_and_nothing_are_frozen() -> None:
    some = Some(1)
    with pytest.raises(FrozenInstanceError):
        some.value = 2  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Result[T, E]
# ---------------------------------------------------------------------------
def test_unwrap_or_result_returns_value_for_ok() -> None:
    assert unwrap_or_result(Ok(10), default=0) == 10


def test_unwrap_or_result_returns_default_for_err() -> None:
    assert unwrap_or_result(Err("boom"), default=-1) == -1


def test_map_result_transforms_ok() -> None:
    result: Any = map_result(Ok(5), lambda x: x + 1)
    assert result == Ok(6)


def test_map_result_passes_err_through_unchanged() -> None:
    result: Any = map_result(Err("boom"), lambda x: x + 1)
    assert result == Err("boom")


def test_map_err_transforms_err() -> None:
    result: Any = map_err(Err("boom"), lambda e: e.upper())
    assert result == Err("BOOM")


def test_map_err_passes_ok_through_unchanged() -> None:
    result: Any = map_err(Ok(5), lambda e: e.upper())
    assert result == Ok(5)


def test_result_from_exception_ok_on_success() -> None:
    result: Any = result_from_exception(lambda: 1 + 1)
    assert result == Ok(2)


def test_result_from_exception_err_on_raise() -> None:
    def boom() -> int:
        raise ValueError("bad input")

    result: Any = result_from_exception(boom)
    assert isinstance(result, Err)
    assert isinstance(result.error, ValueError)
    assert str(result.error) == "bad input"


def test_result_from_exception_does_not_catch_keyboard_interrupt() -> None:
    def interrupt() -> int:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        result_from_exception(interrupt)


def test_ok_and_err_are_frozen() -> None:
    ok = Ok(1)
    with pytest.raises(FrozenInstanceError):
        ok.value = 2  # type: ignore[misc]


# ---------------------------------------------------------------------------
# clamp - bounded generic utility
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("value", "lo", "hi", "expected"),
    [
        (5, 0, 10, 5),
        (-5, 0, 10, 0),
        (15, 0, 10, 10),
        (0, 0, 10, 0),
        (10, 0, 10, 10),
    ],
    ids=["within-range", "below-lo", "above-hi", "equal-lo", "equal-hi"],
)
def test_clamp_int(value: int, lo: int, hi: int, expected: int) -> None:
    assert clamp(value, lo, hi) == expected


def test_clamp_float() -> None:
    assert clamp(3.5, 0.0, 1.0) == 1.0
    assert clamp(-0.5, 0.0, 1.0) == 0.0
    assert clamp(0.5, 0.0, 1.0) == 0.5


def test_clamp_str_is_orderable_too() -> None:
    # Strings support < and > lexicographically, so they satisfy the
    # SupportsRichComparison bound just as well as numbers.
    assert clamp("m", "a", "z") == "m"
    assert clamp("0", "a", "z") == "a"
    assert clamp("zz", "a", "z") == "z"
