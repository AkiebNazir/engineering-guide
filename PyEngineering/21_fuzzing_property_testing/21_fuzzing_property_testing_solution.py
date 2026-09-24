"""
21 - Fuzzing & property testing - Reference Solution
=====================================================

See `21_fuzzing_property_testing_explanation.py` for the full spec,
rationale, and acceptance criteria. Implements the `Record` binary codec
and `SortedList` exactly as specified there.
"""

from __future__ import annotations

import bisect
import struct
from collections.abc import Iterator
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# The Record tree + its binary encoding.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Record:
    """An immutable, arbitrarily nested named value."""

    name: str
    value: int
    children: tuple[Record, ...] = field(default_factory=tuple)


_LEN_FMT = ">I"
_INT_FMT = ">q"
_LEN_SIZE = struct.calcsize(_LEN_FMT)
_INT_SIZE = struct.calcsize(_INT_FMT)

INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1


def _encode_str(s: str) -> bytes:
    # utf-8 first (so we length-prefix the *byte* length, not the
    # character count - a length mismatch here is a classic unicode bug).
    raw = s.encode("utf-8")
    return struct.pack(_LEN_FMT, len(raw)) + raw


def _encode_int(n: int) -> bytes:
    # struct.error propagates for out-of-i64-range ints: a programmer
    # error at the call site, not malformed wire data.
    return struct.pack(_INT_FMT, n)


def encode_record(record: Record) -> bytes:
    # Collect parts and join once at the end rather than repeated `+=`,
    # which would be O(n^2) for a deep/wide tree (each += copies the
    # whole accumulated buffer).
    parts: list[bytes] = [
        _encode_str(record.name),
        _encode_int(record.value),
        struct.pack(_LEN_FMT, len(record.children)),
    ]
    for child in record.children:
        parts.append(encode_record(child))
    return b"".join(parts)


class _Cursor:
    """A tiny mutable read cursor over a `bytes` buffer.

    Centralizing bounds-checking here is what turns "read past the end of
    malformed input" into a single `ValueError` instead of letting
    `struct.error`/`IndexError` leak from a dozen call sites.
    """

    __slots__ = ("data", "pos")

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def take(self, n: int) -> bytes:
        end = self.pos + n
        if end > len(self.data):
            raise ValueError(
                f"truncated input: need {n} bytes at offset {self.pos}, "
                f"only {len(self.data) - self.pos} available"
            )
        chunk = self.data[self.pos : end]
        self.pos = end
        return chunk

    def read_str(self) -> str:
        (length,) = struct.unpack(_LEN_FMT, self.take(_LEN_SIZE))
        raw = self.take(length)
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"invalid utf-8 string at offset {self.pos}") from exc

    def read_int(self) -> int:
        value: int
        (value,) = struct.unpack(_INT_FMT, self.take(_INT_SIZE))
        return value

    def read_count(self) -> int:
        count: int
        (count,) = struct.unpack(_LEN_FMT, self.take(_LEN_SIZE))
        return count


def _decode_record(cursor: _Cursor) -> Record:
    name = cursor.read_str()
    value = cursor.read_int()
    count = cursor.read_count()
    children = tuple(_decode_record(cursor) for _ in range(count))
    return Record(name, value, children)


def decode_record(data: bytes) -> Record:
    cursor = _Cursor(data)
    try:
        record = _decode_record(cursor)
    except struct.error as exc:
        # Belt-and-braces: _Cursor.take already bounds-checks every read,
        # so struct.unpack should never see a short buffer, but any other
        # struct-level complaint (there are none we expect) still maps to
        # our documented error type rather than leaking a stdlib exception.
        raise ValueError(f"malformed record: {exc}") from exc
    # Design decision: trailing bytes after a fully-decoded record are an
    # error. A wire format that silently ignores trailing garbage hides
    # bugs (e.g. a caller that miscomputed a message boundary); rejecting
    # it makes decode_record a strict inverse of encode_record, which is
    # exactly the round-trip property we want to test.
    if cursor.pos != len(data):
        raise ValueError(
            f"trailing data: {len(data) - cursor.pos} unconsumed byte(s) "
            f"after a complete record"
        )
    return record


# ---------------------------------------------------------------------------
# SortedList - a stateful invariant, not a round trip.
# ---------------------------------------------------------------------------
class SortedList:
    """A list of ints that is always kept sorted."""

    __slots__ = ("_items",)

    def __init__(self) -> None:
        self._items: list[int] = []

    def insert(self, x: int) -> None:
        # bisect.insort finds the insertion point in O(log n) comparisons
        # and does the O(n) shift; still worst-case O(n) per insert, same
        # as any array-backed sorted container, but keeps the invariant
        # trivially correct - the point of this exercise is the property
        # test, not beating a balanced-tree implementation.
        bisect.insort(self._items, x)

    def remove(self, x: int) -> None:
        # list.remove is O(n) but already raises ValueError on a missing
        # item, matching the spec, and removing by value from a sorted
        # list keeps it sorted (no re-sort needed).
        self._items.remove(x)

    def __iter__(self) -> Iterator[int]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, x: object) -> bool:
        return x in self._items


# ---------------------------------------------------------------------------
# Best practices
# ---------------------------------------------------------------------------
# - State the invariant, not the algorithm: "decode(encode(x)) == x" and
#   "the container is always sorted and holds exactly what was inserted"
#   are true regardless of implementation, which is what makes them worth
#   fuzzing (an implementation-detail assertion would just re-describe the
#   code, catching nothing an example test wouldn't).
# - Centralize bounds-checking (`_Cursor.take`) so every read site gets
#   the "truncated input -> ValueError" guarantee for free, instead of
#   repeating a length check (and inevitably forgetting it once) at every
#   `struct.unpack` call.
# - `b"".join(parts)` over repeated `bytes += bytes` for anything
#   recursive/loop-accumulated - see problem 22 for why the latter is
#   quadratic.
# - Decide and document edge-case wire-format semantics explicitly
#   (trailing bytes are an error) rather than leaving them as accidental
#   behavior - a property test will otherwise "pass" while encoding an
#   arbitrary, undocumented choice.
#
# Alternative approaches
# -----------------------
# - `pickle`/`json` would round-trip `Record` trivially, but the point of
#   this exercise is exercising a hand-rolled binary format's edge cases -
#   real systems still hand-roll wire formats (protobuf, Cap'n Proto,
#   custom RPC framing) where a length-prefix bug is exactly the class of
#   bug Hypothesis is best at finding. See problem 23 for the
#   JSON/protobuf-specific treatment.
# - `hypothesis.stateful.RuleBasedStateMachine` is the more scalable way
#   to fuzz `SortedList` once it grows more operations (e.g. `discard`,
#   `__getitem__` by rank, merge) - the `@st.composite` sequence-of-ops
#   approach used in the tests here is simpler and sufficient for two ops.
# - `array.array("q", ...)` would give `SortedList` a more memory-compact
#   backing store than a `list[int]` for large collections, at the cost of
#   losing arbitrary-precision Python ints.
