"""
02 · Middleware chain — SOLUTION
=================================

Complete reference implementation of the five pure-ASGI middleware described
in `02_middleware_chain_explanation.py`. Read that file first for the full
spec, the ASGI message-protocol primer, and acceptance criteria.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable, MutableMapping
from contextvars import ContextVar

from fastapi import FastAPI

Scope = MutableMapping[str, object]
Message = MutableMapping[str, object]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

logger = logging.getLogger("middleware_chain")


# ---------------------------------------------------------------------------
# Shared helper: send a complete JSON response "by hand" from inside
# middleware, without going through Starlette's Response classes (those
# expect to run *inside* an app, not as raw ASGI send calls — reusing this
# tiny helper avoids repeating the two-message ASGI dance three times).
# ---------------------------------------------------------------------------
async def _send_json(send: Send, status: int, body: dict[str, object]) -> None:
    payload = json.dumps(body).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": payload})


class RequestIDMiddleware:
    """Tags every HTTP request with a per-request correlation id."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex
        token = request_id_var.set(request_id)

        async def send_wrapper(message: Message) -> None:
            if message.get("type") == "http.response.start":
                # ASGI headers are a list of (bytes, bytes) pairs; append
                # rather than replace since Starlette may already have
                # written its own headers into this same message.
                headers = list(message.get("headers", []))  # type: ignore[arg-type]
                headers.append((b"x-request-id", request_id.encode("ascii")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Always reset, on both the success and exception paths, so a
            # reused Task (some test-client/server setups pool tasks) never
            # sees a stale request id from a prior request.
            request_id_var.reset(token)


class AccessLogMiddleware:
    """Emits one structured JSON log line per request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        start = time.monotonic()
        status_holder: dict[str, int | None] = {"status": None}

        async def send_wrapper(message: Message) -> None:
            if message.get("type") == "http.response.start":
                status_holder["status"] = message.get("status")  # type: ignore[assignment]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.monotonic() - start) * 1000
            logger.info(
                json.dumps(
                    {
                        "request_id": request_id_var.get(),
                        "method": scope.get("method"),
                        "path": scope.get("path"),
                        "status": status_holder["status"],
                        "duration_ms": round(duration_ms, 3),
                    }
                )
            )


class TimeoutMiddleware:
    """Bounds how long the inner app may take to produce a response."""

    def __init__(self, app: ASGIApp, *, timeout_seconds: float) -> None:
        self.app = app
        self.timeout_seconds = timeout_seconds

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal started
            if message.get("type") == "http.response.start":
                started = True
            await send(message)

        try:
            async with asyncio.timeout(self.timeout_seconds):
                await self.app(scope, receive, send_wrapper)
        except TimeoutError:
            if not started:
                await _send_json(send, 504, {"detail": "request timed out"})
            else:
                # A response is already partway out the door; there is no
                # safe way to replace it with a 504 now. Re-raise so the
                # server/transport tears the connection down rather than
                # silently emitting a truncated 200.
                raise


class AuthMiddleware:
    """Rejects requests without a valid bearer token (except /health)."""

    def __init__(self, app: ASGIApp, *, valid_tokens: set[str]) -> None:
        self.app = app
        self.valid_tokens = valid_tokens

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http" or scope.get("path") == "/health":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))  # type: ignore[arg-type]
        raw = headers.get(b"authorization", b"")
        token = self._extract_token(raw)

        if token is None or token not in self.valid_tokens:
            await _send_json(send, 401, {"detail": "unauthorized"})
            return

        await self.app(scope, receive, send)

    @staticmethod
    def _extract_token(raw: bytes) -> str | None:
        try:
            scheme, _, value = raw.decode("latin-1").partition(" ")
        except UnicodeDecodeError:
            return None
        if scheme.lower() != "bearer" or not value:
            return None
        return value


class ExceptionHandlingMiddleware:
    """Outermost layer: converts any unhandled Exception into a clean 500."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal started
            if message.get("type") == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            # Deliberately `Exception`, not `BaseException` — a
            # `CancelledError` (e.g. surfacing from TimeoutMiddleware, or
            # from the ASGI server shutting the connection down) is
            # cooperative cancellation, not an application error, and must
            # keep propagating so the task actually gets cancelled.
            logger.error(
                json.dumps(
                    {
                        "request_id": request_id_var.get(),
                        "method": scope.get("method"),
                        "path": scope.get("path"),
                        "event": "unhandled_exception",
                    }
                ),
                exc_info=True,
            )
            if not started:
                await _send_json(send, 500, {"detail": "internal server error"})
            else:
                raise


def build_app(*, valid_tokens: set[str], timeout_seconds: float = 2.0) -> ASGIApp:
    """Wire the demo FastAPI app with all five middleware, nested so
    ExceptionHandlingMiddleware ends up outermost at runtime.

    Returns the wrapped ASGI callable, not the bare `FastAPI` instance.
    This matters: `app(scope, receive, send)` resolves via
    `type(app).__call__` in Python (special methods are looked up on the
    type, never the instance `__dict__`), so overwriting
    `app.__call__ = wrapped` on an instance would silently do nothing —
    calling `app(...)` would still run FastAPI's own dispatch, bypassing
    every middleware here. The only correct way to compose ASGI middleware
    around an app you don't control the class of is to return a NEW
    callable (the outermost wrapper) and have callers (tests, `uvicorn`)
    serve *that* object instead of the raw `FastAPI()` instance.
    """
    app = FastAPI()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/whoami")
    async def whoami() -> dict[str, str | None]:
        return {"request_id": request_id_var.get()}

    @app.get("/boom")
    async def boom() -> dict[str, str]:
        raise RuntimeError("boom")

    @app.get("/slow")
    async def slow(seconds: float = 0.0) -> dict[str, float]:
        await asyncio.sleep(seconds)
        return {"slept": seconds}

    # Nesting order: `Outer(Inner(app))` makes `Outer` run FIRST at request
    # time (it's the thing the server calls; it decides whether/when to
    # call `Inner`). To get the documented runtime order
    # (ExceptionHandling -> RequestID -> AccessLog -> Timeout -> Auth ->
    # app), wrap from the INSIDE OUT: start with `app`, wrap it in the
    # middleware that should run LAST (closest to the routes) first, and
    # wrap that result in the next-outer layer, ending with
    # ExceptionHandlingMiddleware as the final (outermost) wrap.
    wrapped: ASGIApp = app
    wrapped = AuthMiddleware(wrapped, valid_tokens=valid_tokens)
    wrapped = TimeoutMiddleware(wrapped, timeout_seconds=timeout_seconds)
    wrapped = AccessLogMiddleware(wrapped)
    wrapped = RequestIDMiddleware(wrapped)
    wrapped = ExceptionHandlingMiddleware(wrapped)
    return wrapped


# ---------------------------------------------------------------------------
# Best practices demonstrated here
# ---------------------------------------------------------------------------
# - Pure ASGI middleware composes via plain function/callable wrapping — no
#   framework-specific base class needed, and no response buffering.
# - `ContextVar` (not a module global) for request-scoped state under
#   `asyncio` — isolates concurrent requests sharing one event loop/task
#   set correctly, and `.reset(token)` prevents leakage across reused tasks.
# - Exception-handling middleware as the OUTERMOST layer catches bugs in
#   every layer beneath it, including your own other middleware — the
#   single place that guarantees "no unhandled exception ever reaches an
#   ASGI server as a raw 500 with a traceback."
# - `asyncio.timeout()` (3.11+) as a context manager avoids juggling a bare
#   coroutine/Task the way `asyncio.wait_for` requires.
# - Track "has a response started" via a `send` wrapper flag before trying
#   to send a fallback error response — sending two `http.response.start`
#   messages is a protocol violation, not just bad practice.
#
# Alternative approaches considered
# ----------------------------------
# - `Starlette.add_middleware()` with `BaseHTTPMiddleware` subclasses: less
#   code, but buffers full response bodies and adds per-layer task-group
#   overhead (see the explanation file's WHY section) — the wrong choice
#   for a timeout/logging middleware stack meant to sit in front of every
#   request in a real service.
# - A single monolithic middleware doing all five jobs: fewer classes, but
#   defeats composability/testability (you can no longer unit-test "does
#   auth short-circuit correctly" independent of "does timeout work").
#
# Testing notes
# -------------
# - Test each middleware in isolation by wrapping a minimal fake ASGI app
#   (a lambda-like async function) rather than always going through the
#   full FastAPI demo app — faster and pinpoints failures precisely.
# - For concurrency isolation, fire N concurrent requests via
#   `httpx.AsyncClient` + `asyncio.gather` and assert each response's
#   `X-Request-ID` header is unique.
# - `TimeoutMiddleware` is tested by asserting `/slow?seconds=<longer than
#   timeout>` returns 504 in bounded wall-clock time (not by asserting an
#   exact duration, which would be flaky).
#
# Failure-mode notes
# -------------------
# - If TimeoutMiddleware fires AFTER a response already started streaming,
#   this implementation re-raises rather than attempting a second response
#   — the client will see a truncated/reset connection, which is honest
#   (better than a silently "successful" but incomplete body).
# - `build_app()` returns the wrapped ASGI callable rather than the bare
#   `FastAPI` instance, precisely because Python resolves `app(...)` via
#   `type(app).__call__`, not an instance attribute — there is no way to
#   retrofit middleware onto an existing instance's call behavior after the
#   fact. A larger real service would follow the same pattern: build the
#   framework app, wrap it, and export the WRAPPED object as `app` at
#   module scope (what `uvicorn app_module:app` actually serves).
