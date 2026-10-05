"""
21 - Fuzzing & property testing
================================

WHAT WE'RE BUILDING
--------------------
Two independent artifacts exercised by `hypothesis`, the real-world default
for property-based testing in Python:

1. A small recursive binary encoding for a `Record` tree (name: str,
   value: int, children: list[Record]) - `encode_record`/`decode_record`.
   The property under test is a **round-trip invariant**:
   `decode_record(encode_record(r)) == r` for *any* record `r`, including
   deeply nested ones, records with negative/zero/huge integers, and names
   containing non-ASCII text, embedded nulls, or empty strings.

2. A `SortedList` container backed by `bisect.insort` whose invariant is
   structural, not a round trip: after any sequence of `insert`/`remove`
   operations chosen by Hypothesis, the internal list must (a) stay sorted
   and (b) contain exactly the multiset of items actually inserted minus
   removed. This is tested with `@st.composite` to generate a *sequence of
   operations* (a mini fuzzer for the object's state machine), not just a
   single input.

WHY THIS MATTERS IN REAL SYSTEMS
----------------------------------
Example-based tests ("assert encode(Record('a', 1, [])) == b'...'") only
prove the one case you thought of. Any hand-rolled binary format, parser,
cache, or stateful container has a combinatorial space of edge cases -
empty containers, single-element containers, deeply nested structures,
integer boundaries (0, -1, sys.maxsize), unicode edge cases (empty string,
combining characters, surrogate-adjacent codepoints) - that a human will
systematically under-sample. Property-based testing inverts the burden:
you state an *invariant that must hold for all inputs* and Hypothesis
searches for a counterexample. When your hand-rolled encoder has a bug in
how it handles an empty children list or a name with embedded null bytes,
Hypothesis finds it in milliseconds; you would need to remember to write
that exact example by hand.

SHRINKING VS RANDOM FUZZING
-----------------------------
A naive fuzzer that just throws random bytes/objects at your code and
reports the first failure gives you the *least* useful failing example:
some enormous, incidentally-generated Record tree with 40 nodes and a
19-character garbage string, where most of that complexity is irrelevant
to the actual bug. Hypothesis instead:

1. Generates random examples from your `strategies` (this part IS fuzzing -
   biased random search over the input space, with corpus reuse across
   runs via `.hypothesis/` so it remembers past failures).
2. On finding a failing example, **shrinks** it: it repeatedly tries
   simpler/smaller variants of the failing input (fewer children, shorter
   strings, smaller integers, closer to zero) that *still* fail, converging
   on a locally-minimal counterexample. This is a integrated search over a
   partial order of "simpler than", not just "try smaller sizes" - it also
   normalizes structure (e.g. replacing a weird unicode character with 'a'
   if the failure doesn't depend on which character it is).
3. Reports the shrunk example, which is almost always a 1-3 line
   reproduction of the actual bug ("children=[Record('', 0, [])]" instead
   of a 40-node tree), and replays it first on every subsequent run so a
   fixed regression is caught immediately if it reappears.

Shrinking is why property tests are debuggable in practice: raw fuzzing
finds bugs, but shrinking is what makes the failure *readable*.

CONCEPTS COVERED
------------------
- `hypothesis.strategies` (`st.text()`, `st.integers()`, `st.builds()`,
  `st.recursive()`, `st.lists()`, `@st.composite`)
- `@given` property tests, `assume()` to filter invalid generated inputs
- A genuinely nontrivial invariant: serializer round-trip + a stateful
  container invariant (not "addition is commutative")
- `hypothesis.settings` (`max_examples`, `deadline`) and why they matter
  for CI stability
- Why shrinking matters vs raw random fuzzing

THE SPEC
---------
`Record` (frozen dataclass): `name: str`, `value: int`, `children: tuple[Record, ...]`

Binary format (big-endian, via `struct`):
    string  := <4-byte unsigned length><utf-8 bytes>
    int     := <8-byte signed integer>           (must fit in a signed i64)
    record  := <string name><int value><4-byte unsigned child count><record>*count

`encode_record(r: Record) -> bytes`
`decode_record(data: bytes) -> Record`
    - `decode_record` must raise `ValueError` (not crash with an unrelated
      exception) on truncated/malformed input.
    - Round trip must hold for arbitrary nesting, arbitrary (in-range)
      integers, and arbitrary unicode text in `name` (including the empty
      string and strings containing U+0000).

`SortedList`
    - `insert(x: int) -> None` - insert maintaining sorted order (use
      `bisect.insort`).
    - `remove(x: int) -> None` - remove one occurrence; raise `ValueError`
      if absent (matches `list.remove` semantics).
    - `__iter__`, `__len__`, `__contains__`.
    - Invariant: at every point in a sequence of operations, `list(sl)` is
      sorted and equals the sorted multiset of survivors.

ACCEPTANCE CRITERIA
---------------------
1. `encode_record`/`decode_record` round-trip for records generated by a
   recursive Hypothesis strategy (`st.recursive`), including empty
   children, empty names, negative/zero/boundary integers.
2. `decode_record` raises `ValueError` (never `IndexError`/`struct.error`
   leaking out) on arbitrary truncated byte prefixes of a valid encoding.
3. `SortedList` maintains its sortedness + membership invariant after a
   Hypothesis-generated sequence of insert/remove operations.
4. mypy-clean, black-formatted, ruff-clean.
"""

from __future__ import annotations

import struct
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


# Struct formats: unsigned 32-bit length/count prefix, signed 64-bit value.
_LEN_FMT = ">I"
_INT_FMT = ">q"
_LEN_SIZE = struct.calcsize(_LEN_FMT)
_INT_SIZE = struct.calcsize(_INT_FMT)

# Signed 64-bit range that `_INT_FMT` can represent.
INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1


def _encode_str(s: str) -> bytes:
    """Length-prefix a UTF-8 encoded string."""
    # TODO: encode `s` to utf-8, then return struct.pack(_LEN_FMT, len(raw))
    # concatenated with `raw`.
    raise NotImplementedError("TODO: implement _encode_str")


def _encode_int(n: int) -> bytes:
    """Pack a signed integer that must fit in a signed 64-bit field."""
    # TODO: struct.pack(_INT_FMT, n). Let struct.error propagate to callers
    # of encode_record who pass out-of-range ints - that is a programmer
    # error, not malformed input.
    raise NotImplementedError("TODO: implement _encode_int")


def encode_record(record: Record) -> bytes:
    """Serialize `record` to the binary format described in the module
    docstring. Recurses into `record.children` in order."""
    # TODO:
    # 1. Encode record.name via _encode_str.
    # 2. Encode record.value via _encode_int.
    # 3. Encode struct.pack(_LEN_FMT, len(record.children)).
    # 4. Recursively encode each child and append, in order.
    # 5. Concatenate all parts (prefer b"".join over repeated += for
    #    larger trees - avoids O(n^2) bytes-object copying).
    raise NotImplementedError("TODO: implement encode_record")


class _Cursor:
    """A tiny mutable read cursor over a `bytes` buffer.

    Centralizing bounds-checking here is what lets `decode_record` turn
    "read past the end of malformed input" into a single `ValueError`
    instead of letting `struct.error`/`IndexError` leak from a dozen call
    sites.
    """

    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def take(self, n: int) -> bytes:
        """Consume and return exactly `n` bytes, or raise ValueError."""
        # TODO: if self.pos + n > len(self.data): raise ValueError(...)
        # else slice, advance self.pos by n, return the slice.
        raise NotImplementedError("TODO: implement _Cursor.take")

    def read_str(self) -> str:
        """Read a length-prefixed UTF-8 string."""
        # TODO: (length,) = struct.unpack(_LEN_FMT, self.take(_LEN_SIZE))
        # then self.take(length).decode("utf-8"); wrap UnicodeDecodeError
        # in ValueError.
        raise NotImplementedError("TODO: implement _Cursor.read_str")

    def read_int(self) -> int:
        """Read a signed 64-bit integer."""
        # TODO: struct.unpack(_INT_FMT, self.take(_INT_SIZE))[0]
        raise NotImplementedError("TODO: implement _Cursor.read_int")

    def read_count(self) -> int:
        """Read an unsigned 32-bit count (used for the children count)."""
        # TODO: struct.unpack(_LEN_FMT, self.take(_LEN_SIZE))[0]
        raise NotImplementedError("TODO: implement _Cursor.read_count")


def _decode_record(cursor: _Cursor) -> Record:
    """Decode one Record (and its children) starting at `cursor`'s position."""
    # TODO: name = cursor.read_str(); value = cursor.read_int();
    # count = cursor.read_count(); children = tuple(_decode_record(cursor)
    # for _ in range(count)); return Record(name, value, children).
    raise NotImplementedError("TODO: implement _decode_record")


def decode_record(data: bytes) -> Record:
    """Deserialize the output of `encode_record`.

    Must raise `ValueError` - never an unrelated exception - for any
    malformed or truncated input, including arbitrary byte prefixes of a
    valid encoding (a common Hypothesis-found bug class: off-by-one bounds
    checks that raise `IndexError`/`struct.error` instead).
    """
    # TODO: wrap _decode_record(_Cursor(data)) so that struct.error and
    # UnicodeDecodeError (if not already handled in _Cursor) become
    # ValueError. Consider: should trailing garbage after a complete record
    # be an error? (Yes - decide and document it, then enforce it here.)
    raise NotImplementedError("TODO: implement decode_record")


# ---------------------------------------------------------------------------
# SortedList - a stateful invariant, not a round trip.
# ---------------------------------------------------------------------------
class SortedList:
    """A list of ints that is always kept sorted."""

    def __init__(self) -> None:
        # TODO: self._items: list[int] = []
        raise NotImplementedError("TODO: implement SortedList.__init__")

    def insert(self, x: int) -> None:
        """Insert `x`, keeping `self._items` sorted."""
        # TODO: use bisect.insort(self._items, x)
        raise NotImplementedError("TODO: implement SortedList.insert")

    def remove(self, x: int) -> None:
        """Remove one occurrence of `x`. Raise ValueError if absent."""
        # TODO: self._items.remove(x) (list.remove already raises
        # ValueError on a missing item, and removing from a sorted list by
        # value keeps it sorted).
        raise NotImplementedError("TODO: implement SortedList.remove")

    def __iter__(self):  # type: ignore[no-untyped-def]
        # TODO: return iter(self._items)
        raise NotImplementedError("TODO: implement SortedList.__iter__")

    def __len__(self) -> int:
        # TODO: return len(self._items)
        raise NotImplementedError("TODO: implement SortedList.__len__")

    def __contains__(self, x: object) -> bool:
        # TODO: return x in self._items
        raise NotImplementedError("TODO: implement SortedList.__contains__")


# ---------------------------------------------------------------------------
# HINTS
# -----
# - `st.recursive(base, extend, max_leaves=...)` is the idiomatic way to
#   generate a recursive tree type: `base` produces leaves (no children),
#   `extend(children_strategy)` builds one more layer using it.
# - `st.builds(Record, name=..., value=..., children=...)` composes cleanly
#   with `st.recursive`.
# - `assume()` inside a test filters out generated examples that don't
#   satisfy a precondition, without counting as a failure - use it
#   sparingly (it can make Hypothesis's search less efficient); prefer
#   strategies that only generate valid inputs when possible (e.g.
#   `st.integers(min_value=INT64_MIN, max_value=INT64_MAX)` instead of
#   generating arbitrary ints and `assume`-ing them in range).
# - For the "truncated input raises ValueError" property, generate a valid
#   Record, encode it, then use `st.integers(min_value=0, max_value=len(data))`
#   to pick a prefix length and slice - this fuzzes "any truncation point",
#   far more thoroughly than hand-picking a few cut points.
# - For the SortedList state machine, `@st.composite` letting you draw a
#   sequence of `("insert", x)` / `("remove", x)` tuples (using
#   `st.lists(st.tuples(...))`) is simpler here than reaching for
#   `hypothesis.stateful.RuleBasedStateMachine` - reserve the latter for
#   containers with many more interacting operations.
#
# COMMON PITFALLS
# ---------------
# - Forgetting `frozen=True` on `Record` - without it, `==` still works
#   (dataclass generates `__eq__`) but instances become hashable-unsafe
#   and mutable, which is the wrong shape for something round-tripped
#   through an immutable byte encoding.
# - Off-by-one bounds checks in `_Cursor.take` that let a read past the
#   end of `data` raise `IndexError` (from slicing) instead of the
#   intended `ValueError` - Hypothesis's truncation property will find
#   this immediately if `take` doesn't check length itself.
# - Using `+=` to build up the encoded bytes across a large recursive tree
#   instead of collecting parts and `b"".join(parts)` - quadratic-time
#   bytes concatenation is the classic accidental-quadratic-allocation bug
#   (see problem 22).
#
# STRETCH GOALS
# --------------
# - Add a `hypothesis.settings(max_examples=500)` profile for a slower,
#   more thorough CI-only run vs a fast local default.
# - Extend the Record format with a version byte and demonstrate a schema
#   migration in `decode_record` (foreshadows problem 23).
# - Rewrite the `SortedList` test using
#   `hypothesis.stateful.RuleBasedStateMachine` and compare readability.
