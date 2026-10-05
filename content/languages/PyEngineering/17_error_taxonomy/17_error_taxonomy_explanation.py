"""
17 · Error taxonomy
====================

WHAT WE'RE BUILDING
--------------------
A layered, typed exception hierarchy for a service's domain logic, plus the
machinery every real backend needs around it: exception chaining that
preserves root causes, `ExceptionGroup`/`except*` handling for concurrent
failures raised by `asyncio.TaskGroup`, and two independent mappings from
the same domain exceptions to (a) FastAPI/HTTP status codes and (b) gRPC
status codes — because the same business logic is frequently exposed over
both a REST API and a gRPC service.

WHY THIS MATTERS IN REAL SYSTEMS
---------------------------------
- **A domain exception hierarchy decouples business logic from transport.**
  Domain code should never raise `HTTPException` or set a `grpc.StatusCode`
  directly — that welds your business logic to one transport and makes it
  untestable without an HTTP/gRPC stack. Raise typed domain exceptions;
  map them to a transport status *once*, at the edge.
- **Exception chaining (`raise ... from ...`) is not optional in
  production.** When you catch a low-level exception (a `sqlite3.Error`, a
  `httpx.TimeoutException`) and re-raise a domain exception, losing the
  original traceback turns a five-minute log investigation into a
  half-hour one. `from err` preserves the full chain in `__cause__`;
  `raise NewError(...) from None` is the explicit, intentional way to say
  "this chain truly is irrelevant," never the default.
- **`asyncio.TaskGroup` changes concurrent error handling.** Before
  `TaskGroup` (3.11+), a failed task in a fire-and-forget group could be
  silently swallowed if nobody awaited it. `TaskGroup` guarantees: the
  first unhandled exception in any child task cancels every sibling task,
  waits for them to finish unwinding, and re-raises **all** of their
  exceptions together as an `ExceptionGroup` (or `BaseExceptionGroup` if
  any was a `BaseException`) — even if only one task actually failed.
  `except*` is the syntax built specifically to pull matching exceptions
  back out of that group.
- **Two status models, two different granularities.** HTTP has ~60 status
  codes but only a handful are used for domain errors (400/401/403/404/
  409/422/429/500/503). gRPC's `StatusCode` enum is deliberately smaller and
  RPC-shaped (`NOT_FOUND`, `ALREADY_EXISTS`, `FAILED_PRECONDITION`,
  `RESOURCE_EXHAUSTED`, ...). A single domain exception hierarchy mapped to
  both keeps the two transports consistent without duplicating business
  logic per transport.

CONCEPTS COVERED
-----------------
- Custom exception hierarchy with a common base carrying structured context
- `raise ... from ...` exception chaining; `from None` to suppress it
  deliberately
- `ExceptionGroup` / `except*` (PEP 654, Python 3.11+) tied directly to
  `asyncio.TaskGroup`'s failure-aggregation behavior
- Mapping domain exceptions to HTTP status codes (FastAPI-style, via a
  small `@app.exception_handler` demo) and to `grpc.StatusCode`

THE SPEC
--------
Build a domain exception hierarchy rooted at `AppError`:

    AppError(Exception)                     -- base; carries `.message`
      ValidationError(AppError)             -- bad input        -> 422 / INVALID_ARGUMENT
      NotFoundError(AppError)               -- missing resource -> 404 / NOT_FOUND
      ConflictError(AppError)               -- state conflict   -> 409 / ALREADY_EXISTS
      AuthorizationError(AppError)          -- forbidden        -> 403 / PERMISSION_DENIED
      RateLimitedError(AppError)            -- throttled        -> 429 / RESOURCE_EXHAUSTED
      UnavailableError(AppError)            -- dependency down  -> 503 / UNAVAILABLE
      InternalError(AppError)               -- unexpected       -> 500 / INTERNAL

Build:

    def to_http_status(exc: AppError) -> int: ...
    def to_grpc_status(exc: AppError) -> "grpc.StatusCode": ...
    def install_exception_handlers(app: "FastAPI") -> None: ...
        # registers one handler for AppError (and subclasses) that returns
        # a JSONResponse with the mapped status code and a
        # {"error": type(exc).__name__, "detail": str(exc)} body.

    async def run_batch(coros: list[Coroutine]) -> list[Any]:
        # runs every coroutine concurrently in an asyncio.TaskGroup; if one
        # or more fail, must let the resulting ExceptionGroup propagate
        # (do not swallow it) so callers can use except* on it.

    def summarize_group(eg: ExceptionGroup) -> dict[str, int]:
        # returns a count of exceptions in `eg` per AppError subclass name,
        # using `except*` to split the group by type. Non-AppError
        # exceptions in the group must still be accounted for (and
        # re-raised, not dropped) as the "other" case.

ACCEPTANCE CRITERIA
--------------------
1. Every domain exception subclasses `AppError`; each carries a
   human-readable `.message` and an optional structured `.context: dict`.
2. `to_http_status`/`to_grpc_status` cover every subclass listed above and
   default `InternalError` (or any unmapped `AppError`) to 500 /
   `INTERNAL`.
3. A demonstrated chain: catching a low-level exception (e.g.
   `KeyError`/`ValueError`) and re-raising a domain exception via
   `raise DomainErr(...) from original` preserves `__cause__`.
4. `run_batch` with 3 coroutines where 2 raise different `AppError`
   subclasses raises an `ExceptionGroup` containing exactly those 2
   exceptions (TaskGroup's aggregation, not manually assembled).
5. `summarize_group` correctly splits a group by exception type using
   `except*`, verified against a hand-built `ExceptionGroup`.
6. `install_exception_handlers` on a FastAPI app: a route raising
   `NotFoundError` returns HTTP 404 with the mapped JSON body, verified
   via `TestClient`.
7. mypy-clean, black-formatted, ruff-clean.
"""

from __future__ import annotations

from collections.abc import Coroutine
from typing import Any

import grpc  # type: ignore[import-untyped]  # no bundled/installed stubs
from fastapi import FastAPI


class AppError(Exception):
    """Base of the domain exception hierarchy.

    Carries a human-readable message plus optional structured context
    (e.g. `{"user_id": "42"}`) useful for structured logging at the point
    the exception is finally handled, without needing to parse the message
    string.
    """

    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        # TODO: super().__init__(message); store message + context
        # (context defaulting to {} rather than None, to keep call sites
        # simple: `exc.context.get("user_id")` should never need a None
        # check).
        raise NotImplementedError("TODO: implement AppError.__init__")


class ValidationError(AppError):
    """Input failed validation. HTTP 422 / gRPC INVALID_ARGUMENT."""


class NotFoundError(AppError):
    """Referenced resource does not exist. HTTP 404 / gRPC NOT_FOUND."""


class ConflictError(AppError):
    """Operation conflicts with current state. HTTP 409 / gRPC ALREADY_EXISTS."""


class AuthorizationError(AppError):
    """Caller is not permitted to perform this operation. HTTP 403 / gRPC PERMISSION_DENIED."""


class RateLimitedError(AppError):
    """Caller has been throttled. HTTP 429 / gRPC RESOURCE_EXHAUSTED."""


class UnavailableError(AppError):
    """A downstream dependency is unavailable. HTTP 503 / gRPC UNAVAILABLE."""


class InternalError(AppError):
    """Unexpected/unclassified failure. HTTP 500 / gRPC INTERNAL."""


# TODO: build `_HTTP_STATUS: dict[type[AppError], int]` and
# `_GRPC_STATUS: dict[type[AppError], grpc.StatusCode]` mapping tables, one
# entry per subclass above.


def to_http_status(exc: AppError) -> int:
    """Map a domain exception to an HTTP status code (FastAPI-style)."""
    # TODO: look up type(exc) in the mapping table; default to 500 for any
    # AppError subclass not explicitly listed (never let a lookup fail).
    raise NotImplementedError("TODO: implement to_http_status")


def to_grpc_status(exc: AppError) -> grpc.StatusCode:
    """Map a domain exception to a grpc.StatusCode."""
    raise NotImplementedError("TODO: implement to_grpc_status")


def install_exception_handlers(app: FastAPI) -> None:
    """Register a single AppError -> JSONResponse handler on `app`."""
    # TODO: @app.exception_handler(AppError) async def handler(request,
    # exc: AppError) -> JSONResponse: return JSONResponse(
    #   status_code=to_http_status(exc),
    #   content={"error": type(exc).__name__, "detail": str(exc)},
    # )
    raise NotImplementedError("TODO: implement install_exception_handlers")


async def run_batch(coros: list[Coroutine[Any, Any, Any]]) -> list[Any]:
    """Run every coroutine concurrently; propagate failures as a group.

    Uses asyncio.TaskGroup so that if any coroutine raises, all siblings
    are cancelled and every exception (not just the first) surfaces
    together as an ExceptionGroup/BaseExceptionGroup from the `async with`
    block. Do NOT catch exceptions here — the whole point is to let
    TaskGroup's aggregation behavior reach the caller.
    """
    # TODO: `results: list[Any] = [None] * len(coros)`; inside
    # `async with asyncio.TaskGroup() as tg:`, create one task per coro
    # that stores its result at the right index; after the `async with`
    # block (which raises ExceptionGroup on failure before falling
    # through), return results.
    raise NotImplementedError("TODO: implement run_batch")


def summarize_group(eg: ExceptionGroup[AppError]) -> dict[str, int]:
    """Count exceptions in `eg` by concrete AppError subclass name.

    Any exception in the group that is NOT an AppError must be re-raised
    (as its own group, via except*'s automatic re-raise of the unmatched
    portion) rather than silently dropped.
    """
    # TODO: counts: dict[str, int] = {}
    # try:
    #     raise eg
    # except* AppError as matched:
    #     for e in matched.exceptions:
    #         counts[type(e).__name__] = counts.get(type(e).__name__, 0) + 1
    # return counts
    #
    # Note: any exceptions NOT matched by `except* AppError` are
    # automatically re-raised by Python as a new ExceptionGroup containing
    # just the unmatched ones, once the try block finishes — you don't
    # write that re-raise yourself.
    raise NotImplementedError("TODO: implement summarize_group")


# ---------------------------------------------------------------------------
# HINTS
# -----
# - `except*` can only appear in a `try` block that has no plain `except`
#   clauses mixed in — a try/except* block is exclusively except* clauses.
# - `ExceptionGroup(message, [exc1, exc2])` is how you construct one by
#   hand for tests; `eg.exceptions` is the tuple of contained exceptions.
# - `grpc.StatusCode` is an enum (`grpc.StatusCode.NOT_FOUND`, etc.) — see
#   `python -c "import grpc; print(list(grpc.StatusCode))"` for the full
#   set. No network/server needed to use the enum values themselves.
# - FastAPI's `TestClient` re-raises unhandled server exceptions by default
#   unless caught by a registered exception_handler — that's exactly why
#   `install_exception_handlers` matters; without it your test would see a
#   raised `NotFoundError`, not a 404 response.
#
# COMMON PITFALLS
# ---------------
# - Catching `Exception` broadly inside `run_batch` "to be safe" — this
#   defeats the entire point of the exercise. Let TaskGroup do its job.
# - Forgetting `from err`/`from None` when translating a low-level
#   exception to a domain one — silently losing `__cause__` makes
#   production debugging much harder for no benefit.
# - Mixing `except*` and plain `except` in the same `try` — SyntaxError.
# - Treating `grpc.StatusCode` members as strings — they're enum members;
#   compare with `is`/`==` against the enum, not against `.name`.
#
# STRETCH GOALS
# --------------
# - Add an `AppError.to_dict()` method producing a stable machine-readable
#   error payload (code, message, context) shared by both the HTTP and
#   gRPC mapping paths, instead of only `str(exc)`.
# - Add a `grpc.aio` interceptor sketch that catches `AppError` server-side
#   and calls `context.abort(to_grpc_status(exc), str(exc))`.
# - Extend `summarize_group` to handle *nested* ExceptionGroups (a
#   TaskGroup whose child tasks are themselves TaskGroups).
