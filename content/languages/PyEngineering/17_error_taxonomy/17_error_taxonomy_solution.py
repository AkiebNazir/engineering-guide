"""
17 · Error taxonomy — solution.

See `17_error_taxonomy_explanation.py` for the full spec, rationale, and
acceptance criteria. This file is the complete, idiomatic implementation.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any

import grpc  # type: ignore[import-untyped]  # no bundled/installed stubs
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Step 1: the domain exception hierarchy. Every exception carries a message
# plus optional structured context — this is what a structured logger reads
# at the point the exception is finally handled, instead of regex-parsing a
# formatted string.
# ---------------------------------------------------------------------------
class AppError(Exception):
    """Base of the domain exception hierarchy."""

    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context: dict[str, Any] = context or {}


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


# ---------------------------------------------------------------------------
# Step 2: mapping tables. A dict keyed by exact type, looked up via
# type(exc) with a safe default — never a long if/elif isinstance() chain,
# which is easy to get subtly wrong once subclasses of subclasses appear.
# ---------------------------------------------------------------------------
_HTTP_STATUS: dict[type[AppError], int] = {
    ValidationError: 422,
    NotFoundError: 404,
    ConflictError: 409,
    AuthorizationError: 403,
    RateLimitedError: 429,
    UnavailableError: 503,
    InternalError: 500,
}

_GRPC_STATUS: dict[type[AppError], grpc.StatusCode] = {
    ValidationError: grpc.StatusCode.INVALID_ARGUMENT,
    NotFoundError: grpc.StatusCode.NOT_FOUND,
    ConflictError: grpc.StatusCode.ALREADY_EXISTS,
    AuthorizationError: grpc.StatusCode.PERMISSION_DENIED,
    RateLimitedError: grpc.StatusCode.RESOURCE_EXHAUSTED,
    UnavailableError: grpc.StatusCode.UNAVAILABLE,
    InternalError: grpc.StatusCode.INTERNAL,
}


def to_http_status(exc: AppError) -> int:
    """Map a domain exception to an HTTP status code (FastAPI-style).

    Falls back to 500 for any AppError subclass not explicitly listed
    (e.g. a new subclass added later and not yet wired into the table) —
    an unmapped domain error should degrade to "something went wrong", not
    raise a KeyError while handling an error.
    """
    return _HTTP_STATUS.get(type(exc), 500)


def to_grpc_status(exc: AppError) -> grpc.StatusCode:
    """Map a domain exception to a grpc.StatusCode, defaulting to INTERNAL."""
    return _GRPC_STATUS.get(type(exc), grpc.StatusCode.INTERNAL)


def install_exception_handlers(app: FastAPI) -> None:
    """Register a single AppError -> JSONResponse handler on `app`.

    One handler for the whole hierarchy (registered on the base class)
    means adding a new AppError subclass later needs zero changes here —
    only a new entry in the mapping tables above.
    """

    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=to_http_status(exc),
            content={"error": type(exc).__name__, "detail": exc.message},
        )


# ---------------------------------------------------------------------------
# Step 3: asyncio.TaskGroup aggregation. We deliberately do NOT catch
# anything here — TaskGroup's contract is that the `async with` block
# itself raises an ExceptionGroup (or BaseExceptionGroup) once every child
# task has finished unwinding, and callers are expected to use except* on
# the call site, not inside this function.
# ---------------------------------------------------------------------------
async def run_batch(coros: list[Coroutine[Any, Any, Any]]) -> list[Any]:
    """Run every coroutine concurrently; propagate failures as a group."""
    results: list[Any] = [None] * len(coros)

    async def _run(index: int, coro: Coroutine[Any, Any, Any]) -> None:
        results[index] = await coro

    async with asyncio.TaskGroup() as tg:
        for i, coro in enumerate(coros):
            tg.create_task(_run(i, coro))
    # Reached only if every task succeeded — TaskGroup raises before this
    # point if any child failed, cancelling the rest.
    return results


def summarize_group(eg: ExceptionGroup[AppError]) -> dict[str, int]:
    """Count exceptions in `eg` by concrete AppError subclass name.

    Uses except* to split the group: the matched branch handles every
    AppError inside (at any nesting depth `except*` searches), and Python
    automatically re-raises whatever wasn't matched as a new group once the
    try block exits — nothing non-AppError is silently dropped.
    """
    counts: dict[str, int] = {}
    try:
        raise eg
    except* AppError as matched:
        for e in matched.exceptions:
            counts[type(e).__name__] = counts.get(type(e).__name__, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Best practices demonstrated here
# ---------------------------------------------------------------------------
# - One mapping table per transport, keyed by exact exception type, with an
#   explicit fallback — never let error-handling code itself raise on an
#   unexpected input; that's the surest way to turn a 404 into a 500 with
#   no log line explaining why.
# - Register exception handlers once, on the common base class, so adding a
#   new domain exception subclass never requires touching the transport
#   layer again — only the mapping tables need a new row.
# - Never catch broadly inside code that participates in an
#   `asyncio.TaskGroup`'s child tasks unless you specifically want to
#   suppress that child's contribution to the eventual ExceptionGroup —
#   letting exceptions propagate is what makes TaskGroup's aggregation useful.
# - Prefer `raise NewError(...) from original` at every translation
#   boundary (see the test file for a demonstrated chain) — `__cause__`
#   costs nothing to keep and is frequently the only thing that makes a
#   production incident diagnosable after the fact.
#
# Alternative approaches
# -----------------------
# - `match`/`case` on `type(exc)` instead of a dict lookup — works, but a
#   dict is O(1), doesn't require maintaining case-order, and is trivially
#   introspectable (`list(_HTTP_STATUS)`) for building documentation or a
#   test that asserts every subclass has an entry.
# - Attaching the HTTP/gRPC status directly as a class attribute on each
#   exception (`NotFoundError.http_status = 404`) instead of external
#   mapping tables — simpler for a small hierarchy, but couples the domain
#   exception classes to transport concerns the module docstring explicitly
#   says to avoid; it also makes "list every exception mapped to 404"
#   harder than scanning one table.
# - `contextlib.suppress`-style helpers for "log and re-raise as domain
#   error" boilerplate, if the same catch/translate pattern repeats across
#   many call sites in a larger codebase.
