"""
19 - Generic utilities
========================

WHAT WE'RE BUILDING
--------------------
Two small, from-scratch generic containers using **PEP 695** syntax
(Python 3.12+'s `class Foo[T]:` / `def f[T](...)` type-parameter syntax,
which replaces the older `TypeVar` + `Generic[T]` boilerplate):

1. `Option[T]` - a container that is either `Some(value)` or `Nothing`,
   modeling "a value that might be absent" without using `None` (which
   conflates "absent" with "the actual value is `None`" - a real bug
   source when `T` itself can legitimately be `None`).
2. `Result[T, E]` - a container that is either `Ok(value)` or `Err(error)`,
   modeling "a computation that might fail" without exceptions - an
   explicit alternative used heavily in Rust and increasingly in Python
   codebases that want typed, exhaustively-handled error paths instead of
   `try`/`except` at every call site.

Both are implemented as a **discriminated union of frozen dataclasses**,
dispatched with structural pattern matching (`match`/`case`) - the
idiomatic modern-Python answer to "a sum type," since Python has no
built-in `enum`-of-payloads construct like Rust's `enum` or Kotlin's
`sealed class`.

WHY THIS MATTERS IN REAL SYSTEMS
----------------------------------
`Result`/`Option` push error/absence handling into the type system: a
function returning `Result[User, LookupError]` tells every caller, at the
type level, "this can fail, and here's how" - callers can't silently
ignore the failure case the way they can forget a `try`/`except` around a
function that raises. This is genuinely valuable at API boundaries where
failure is a normal, expected outcome (a lookup that might miss, a parse
that might fail, a validation step) as opposed to an exceptional one (a
database connection dying mid-transaction) - exceptions remain the right
tool for the latter.

But Python is not Rust: it has no exhaustiveness checking that forces you
to handle every `case`, `assert_never` is opt-in (not enforced by the
runtime), and idiomatic Python leans on duck typing and `Protocol`-based
structural interfaces (problem 18) far more than on generic containers.
Overusing `Result`/`Option` - wrapping *every* function, including ones
where exceptions are perfectly idiomatic - produces un-Pythonic code that
fights the standard library (which raises exceptions everywhere: `dict`
lookups, `int()` parsing, file I/O) and forces callers to unwrap at every
step. The trade-offs section at the bottom of the solution file is the
actual point of this exercise as much as the containers themselves.

CONCEPTS COVERED
------------------
- PEP 695 generics: `class Option[T]:`, `class Ok[T, E]:`, `def f[T](...)`
  - no `TypeVar`/`Generic` imports needed
  - a **bounded** type parameter (`[T: SupportsLessThan]`-style constraint)
    on the standalone generic utility function
- A discriminated union built from frozen dataclasses, matched via
  `match`/`case` with pattern-matched class deconstruction
  (`case Some(value):`)
- `typing.Never` / `typing.assert_never` for exhaustiveness hinting
- When generics are the wrong tool in Python vs when `Protocol`/duck
  typing already covers it (see problem 18)

THE SPEC
---------
`Option[T]` - one of:
    `Some[T]` (frozen dataclass): `value: T`
    `Nothing` (frozen dataclass, no fields - use a module-level singleton
        instance since it carries no data and there's no reason to
        allocate more than one)
    Type alias: `Option[T] = Some[T] | Nothing`

    `Option.unwrap_or(self, default: T) -> T` - is easiest to implement as
        a free function `unwrap_or(opt: Option[T], default: T) -> T`
        (methods on a union-of-dataclasses aren't shared naturally, so the
        idiomatic move is `match`/`case` free functions operating on the
        union type; see the solution for the exact function set).
    `map_option[T, U](opt: Option[T], fn: Callable[[T], U]) -> Option[U]`
        - apply `fn` to the value if `Some`, else stay `Nothing`.
    `option_from_optional(value: T | None) -> Option[T]` - `None` becomes
        `Nothing`, anything else becomes `Some(value)`.

`Result[T, E]` - one of:
    `Ok[T, E]` (frozen dataclass): `value: T`
    `Err[T, E]` (frozen dataclass): `error: E`
    Type alias: `Result[T, E] = Ok[T, E] | Err[T, E]`

    `unwrap_or(result: Result[T, E], default: T) -> T`
    `map_result[T, U, E](result: Result[T, E], fn: Callable[[T], U]) -> Result[U, E]`
        - apply `fn` to the value if `Ok`, pass `Err` through unchanged.
    `map_err[T, E, F](result: Result[T, E], fn: Callable[[E], F]) -> Result[T, F]`
        - apply `fn` to the error if `Err`, pass `Ok` through unchanged.
    `result_from_exception[T](fn: Callable[[], T]) -> Result[T, Exception]`
        - call `fn()`; return `Ok(value)` on success, `Err(exc)` if it
          raises `Exception` (the bridge from exception-style code into
          `Result`-style code at a boundary).

A standalone bounded-generic utility (not part of Option/Result):
    `clamp[T: SupportsRichComparison](value: T, lo: T, hi: T) -> T` -
        constrain `value` to `[lo, hi]`. Demonstrates a *bounded* PEP 695
        type parameter (`T` must support `<`/`>` comparisons) as opposed
        to `Option`/`Result`'s unbounded `T`/`E`.

ACCEPTANCE CRITERIA
---------------------
1. `Option`/`Result` are implemented with PEP 695 syntax, zero `TypeVar`/
   `Generic` imports.
2. All the free functions above use `match`/`case` for dispatch (not
   `isinstance` chains).
3. `option_from_optional`/`result_from_exception` correctly bridge from
   "ordinary Python" (`None`, exceptions) into the container types.
4. `clamp` is correctly bounded so mypy rejects calling it with a type
   that has no `<`/`>` (document this in a comment; a concrete mypy
   *failure* isn't required to be demonstrated in the test suite, but the
   bound must be present and correctly expressed).
5. A "when generics hurt" trade-offs note exists (bottom of the solution
   file) covering at least: exhaustiveness not being enforced at runtime,
   fighting stdlib exception-based APIs, and Protocol/duck-typing as the
   more idiomatic default.
6. mypy-clean, black-formatted, ruff-clean.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


# ---------------------------------------------------------------------------
# Option[T] - Some(value) | Nothing
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Some[T]:
    value: T


@dataclass(frozen=True)
class Nothing:
    pass


# Module-level singleton: Nothing carries no data, so every "absent"
# value can share one instance instead of allocating a fresh one.
NOTHING: Nothing = Nothing()

type Option[T] = Some[T] | Nothing


def unwrap_or[T](opt: Option[T], default: T) -> T:
    """Return the wrapped value, or `default` if `opt` is `Nothing`."""
    # TODO: match opt: case Some(value): return value
    #       case Nothing(): return default
    raise NotImplementedError("TODO: implement unwrap_or")


def map_option[T, U](opt: Option[T], fn: Callable[[T], U]) -> Option[U]:
    """Apply `fn` to the wrapped value if present; pass `Nothing` through."""
    # TODO: match opt: case Some(value): return Some(fn(value))
    #       case Nothing(): return NOTHING
    raise NotImplementedError("TODO: implement map_option")


def option_from_optional[T](value: T | None) -> Option[T]:
    """Bridge from ordinary `T | None` into `Option[T]`."""
    # TODO: return NOTHING if value is None else Some(value)
    raise NotImplementedError("TODO: implement option_from_optional")


# ---------------------------------------------------------------------------
# Result[T, E] - Ok(value) | Err(error)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Ok[T, E]:
    value: T


@dataclass(frozen=True)
class Err[T, E]:
    error: E


type Result[T, E] = Ok[T, E] | Err[T, E]


def unwrap_or_result[T, E](result: Result[T, E], default: T) -> T:
    """Return the wrapped value, or `default` if `result` is `Err`."""
    # TODO: match result: case Ok(value): return value
    #       case Err(_error): return default
    raise NotImplementedError("TODO: implement unwrap_or_result")


def map_result[T, U, E](result: Result[T, E], fn: Callable[[T], U]) -> Result[U, E]:
    """Apply `fn` to the wrapped value if `Ok`; pass `Err` through unchanged."""
    # TODO: match result: case Ok(value): return Ok(fn(value))
    #       case Err(error): return Err(error)
    raise NotImplementedError("TODO: implement map_result")


def map_err[T, E, F](result: Result[T, E], fn: Callable[[E], F]) -> Result[T, F]:
    """Apply `fn` to the error if `Err`; pass `Ok` through unchanged."""
    # TODO: match result: case Ok(value): return Ok(value)
    #       case Err(error): return Err(fn(error))
    raise NotImplementedError("TODO: implement map_err")


def result_from_exception[T](fn: Callable[[], T]) -> Result[T, Exception]:
    """Call `fn()`, converting a raised `Exception` into `Err`.

    Bridges ordinary exception-raising code into Result-style code at a
    boundary (e.g. wrapping a third-party call). Only `Exception` (not
    `BaseException`) is caught - `KeyboardInterrupt`/`SystemExit` should
    never be silently turned into a value.
    """
    # TODO: try: return Ok(fn()) except Exception as exc: return Err(exc)
    raise NotImplementedError("TODO: implement result_from_exception")


# ---------------------------------------------------------------------------
# A standalone bounded generic utility.
# ---------------------------------------------------------------------------
class SupportsRichComparison(Protocol):
    """Structural bound for clamp's type parameter: anything orderable.

    TODO: declare the two methods needed for `<`/`>` comparisons:
    `def __lt__(self, other: Any) -> bool: ...` and
    `def __gt__(self, other: Any) -> bool: ...`
    """


def clamp[T: SupportsRichComparison](value: T, lo: T, hi: T) -> T:
    """Constrain `value` to the closed range `[lo, hi]`.

    TODO: return lo if value < lo else hi if value > hi else value.
    The bound `T: SupportsRichComparison` is what lets mypy reject calling
    this with a type that has no `<`/`>` - contrast with the unbounded
    `T`/`U`/`E` on Option/Result above, which only need equality/identity.
    """
    raise NotImplementedError("TODO: implement clamp with a bounded T")


# ---------------------------------------------------------------------------
# HINTS
# -----
# - PEP 695: `class Some[T]:` declares a type parameter scoped to the
#   class body - no `from typing import Generic, TypeVar` needed at all.
#   Same for `def f[T](...)` on functions, and `type Alias[T] = ...` for
#   generic type aliases.
# - `match`/`case` on a dataclass instance does *positional or keyword*
#   deconstruction: `case Some(value):` binds `value` to the `.value`
#   field because dataclasses auto-generate `__match_args__`. `case
#   Nothing():` matches by class with zero captured fields.
# - For the bound on `clamp`, define your own minimal Protocol:
#   `class SupportsRichComparison(Protocol): def __lt__(self, other:
#   Any) -> bool: ...` etc. - don't reach for a nonexistent stdlib
#   "Comparable" type.
# - `type Option[T] = Some[T] | Nothing` (PEP 695 type alias syntax) is
#   preferred over the older `Option = Some[T] | Nothing` at module scope
#   because it creates a lazily-evaluated, properly generic alias that
#   mypy understands as parameterizable.
#
# COMMON PITFALLS
# ---------------
# - Forgetting `frozen=True` - these are value types meant to be compared
#   by equality and never mutated after construction; a mutable `Some`
#   would be a footgun (aliasing bugs) with no compensating benefit.
# - Using `isinstance(opt, Some)` chains instead of `match`/`case` -
#   works, but loses the structural-binding conciseness and (with
#   `assert_never` in a trailing `case _:`) the exhaustiveness hint that
#   `match` gives a type checker.
# - Catching `BaseException` instead of `Exception` in
#   `result_from_exception` - would silently absorb
#   `KeyboardInterrupt`/`SystemExit`, which must always propagate.
# - Reaching for `Result`/`Option` everywhere "because Rust does it" -
#   read the trade-offs note in the solution file before doing this in
#   real code.
#
# STRETCH GOALS
# --------------
# - Add `and_then[T, U, E](result: Result[T, E], fn: Callable[[T],
#   Result[U, E]]) -> Result[U, E]` (monadic bind / flatMap) and chain
#   several fallible steps without nested `match` blocks.
# - Add `typing.assert_never` to a trailing `case _:` in one of the match
#   statements and show mypy flagging it as unreachable when all cases
#   are already covered (proves the union is exhaustively handled).
# - Write a tiny benchmark (see problem 22) comparing `Result`-style
#   error handling against exception-based handling for a hot loop where
#   failure is common (e.g. parsing a stream of mostly-invalid records) -
#   exceptions are surprisingly expensive when raised in a tight loop,
#   which is one of the few places `Result` is a real performance win in
#   Python, not just a style preference.
