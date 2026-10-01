"""Property tests for `21_fuzzing_property_testing_solution.py`.

Run: .venv/bin/pytest 21_fuzzing_property_testing/ -v
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

# The module under test is named "21_..." which is not a valid Python
# identifier, so it can't be reached with a normal `import` statement (that
# requires dotted-identifier module names) - `importlib.import_module` takes
# an arbitrary string and works fine for this file-based module. The
# consequence is that mypy can't statically resolve `Record`/`SortedList` as
# *types*, only as runtime values (see the `Any` annotations below).
_solution = import_module("21_fuzzing_property_testing_solution")
Record = _solution.Record
SortedList = _solution.SortedList
encode_record = _solution.encode_record
decode_record = _solution.decode_record
INT64_MIN = _solution.INT64_MIN
INT64_MAX = _solution.INT64_MAX


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------
_int64 = st.integers(min_value=INT64_MIN, max_value=INT64_MAX)
_name = st.text(max_size=40)  # includes "", unicode, embedded U+0000, etc.

_record_strategy = st.recursive(
    st.builds(Record, name=_name, value=_int64, children=st.just(())),
    lambda children: st.builds(
        Record,
        name=_name,
        value=_int64,
        children=st.lists(children, max_size=4).map(tuple),
    ),
    max_leaves=30,
)


# ---------------------------------------------------------------------------
# Record round-trip property
# ---------------------------------------------------------------------------
@given(record=_record_strategy)
@settings(max_examples=200)
def test_record_round_trip(record: Any) -> None:
    """decode(encode(r)) == r for arbitrarily nested, arbitrary-content records."""
    assert decode_record(encode_record(record)) == record


@given(record=_record_strategy, data=st.data())
@settings(max_examples=200)
def test_truncated_input_raises_value_error(record: Any, data: st.DataObject) -> None:
    """Any strict prefix of a valid encoding is either invalid or must not
    crash with anything other than ValueError."""
    encoded = encode_record(record)
    cut = data.draw(st.integers(min_value=0, max_value=len(encoded)))
    prefix = encoded[:cut]
    if cut == len(encoded):
        # The full encoding must still decode correctly.
        assert decode_record(prefix) == record
        return
    try:
        decode_record(prefix)
    except ValueError:
        pass  # expected outcome for a truncated / malformed buffer
    else:
        # A short prefix that still happens to decode cleanly is only
        # acceptable if it decodes to something other than a truncation
        # bug slipping through silently - for this format a strict prefix
        # shorter than the full encoding can never re-parse as a complete,
        # self-consistent record without hitting a bounds check, so reaching
        # here indicates a real problem.
        raise AssertionError(
            f"expected ValueError for truncated input (cut={cut}, "
            f"total={len(encoded)}), but decode_record succeeded"
        )


def test_decode_empty_bytes_raises_value_error() -> None:
    import pytest

    with pytest.raises(ValueError):
        decode_record(b"")


# ---------------------------------------------------------------------------
# SortedList invariant property (sequence of insert/remove operations)
# ---------------------------------------------------------------------------
_op_strategy = st.tuples(
    st.sampled_from(["insert", "remove"]),
    st.integers(min_value=-50, max_value=50),
)


@given(ops=st.lists(_op_strategy, max_size=50))
@settings(max_examples=200)
def test_sorted_list_invariant(ops: list[tuple[str, int]]) -> None:
    """After any sequence of insert/remove ops, the list stays sorted and
    matches a reference `list`-based model exactly."""
    sl = SortedList()
    model: list[int] = []

    for op, x in ops:
        if op == "insert":
            sl.insert(x)
            model.append(x)
            model.sort()
        else:
            if x in model:
                sl.remove(x)
                model.remove(x)
            else:
                try:
                    sl.remove(x)
                except ValueError:
                    pass
                else:
                    raise AssertionError(f"remove({x!r}) should have raised ValueError")

        # Invariants must hold after *every* operation, not just at the end.
        current = list(sl)
        assert current == sorted(current), "SortedList lost sortedness"
        assert current == model, "SortedList diverged from the reference model"
        assert len(sl) == len(model)
        for v in set(model) | {x}:
            assert (v in sl) == (v in model)
