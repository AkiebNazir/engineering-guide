"""
02 · Middleware chain
======================

WHAT WE'RE BUILDING
--------------------
A small stack of composable **pure-ASGI middleware** (not `BaseHTTPMiddleware`
— see WHY below) wrapping a FastAPI app, in this order from outermost to
innermost:

    ExceptionHandlingMiddleware   # never let an unhandled exception reach the client
      -> RequestIDMiddleware      # tag every request with a correlation id
        -> AccessLogMiddleware    # structured JSON log line per request
          -> TimeoutMiddleware    # bound how long a handler may run
            -> AuthMiddleware     # reject unauthenticated requests
              -> app              # your route handlers

WHY PURE ASGI, NOT `BaseHTTPMiddleware`
-----------------------------------------
Starlette's `BaseHTTPMiddleware` is the "easy" way to write middleware (it
gives you a `request`/`call_next` shape that looks like Flask/Express), but
it has two real production costs worth knowing:

1. It buffers the *entire* response body in memory before your middleware's
   code can inspect it — this breaks streaming responses and wastes memory
   on large payloads.
2. Every layer of `BaseHTTPMiddleware` spawns its own `anyio` task group to
   bridge the callback-based `call_next` back into ASGI's message-passing
   model — measurable overhead per layer, per request.

Pure ASGI middleware (a callable class implementing
`__call__(self, scope, receive, send)`, wrapping an inner `app` of the same
shape) has none of this overhead and is what production middleware
(`GZipMiddleware`, `CORSMiddleware`, Sentry's ASGI integration, etc.) is
actually built from in Starlette itself. It's more code up front — you must
understand the ASGI message protocol (`http.request`, `http.response.start`,
`http.response.body`) — but it composes cleanly and doesn't buffer.

CONCEPTS COVERED
-----------------
- The ASGI 3-callable protocol (`scope`, `receive`, `send`) and how
  middleware wraps another ASGI app of the same shape
- `contextvars.ContextVar` for request-scoped correlation IDs that are safe
  under `asyncio` (unlike a plain module global, which would leak across
  concurrent requests sharing one event loop)
- Structured (JSON) logging via stdlib `logging` + a custom `Formatter`
- Exception-handling middleware as the *outermost* layer, so it can catch
  failures from every layer beneath it, including bugs in your own other
  middleware
- Enforcing a per-request timeout with `asyncio.wait_for` / `asyncio.timeout`
  and mapping cancellation to a clean `504`
- Auth middleware that inspects a header and short-circuits the chain by
  sending a response directly (never calling the inner `app`) on failure

THE ASGI MESSAGE PROTOCOL (what you're actually wrapping)
------------------------------------------------------------
For an HTTP request, the ASGI server calls your app as
`await app(scope, receive, send)`. `scope` is a dict describing the request
(method, path, headers, ...). `receive()` is an async callable yielding
request body chunks. `send(message)` is an async callable your app calls
(possibly multiple times) to emit the response:

    await send({"type": "http.response.start", "status": 200,
                 "headers": [(b"content-type", b"application/json")]})
    await send({"type": "http.response.body", "body": b'{"ok": true}'})

Middleware wraps this: it receives `(scope, receive, send)` from the layer
above, and calls `await self.app(scope, receive, wrapped_send)` where
`wrapped_send` is a function you write that intercepts/mutates outgoing
messages (e.g. to add a header) before forwarding them to the real `send`.
To short-circuit (never reach the inner app — e.g. a failed auth check),
just call `send(...)` directly yourself and return without calling
`self.app(...)` at all.

THE SPEC
--------
Implement five ASGI middleware classes plus a small demo FastAPI app to
exercise them:

    RequestIDMiddleware
        - Generate a `uuid.uuid4().hex` request id per HTTP request (skip
          non-"http" scope types, e.g. "lifespan", by passing through
          unchanged).
        - Store it in a `ContextVar` so route handlers / other middleware
          can read it via `request_id_var.get()`.
        - Add it as an `X-Request-ID` response header on the way out.
        - Reset the ContextVar (via the token from `.set()`) in a `finally`
          so it never leaks into an unrelated request reusing the same task.

    AccessLogMiddleware
        - Time the request (`time.monotonic()` before/after).
        - After the inner app completes (success OR exception — use
          try/finally), emit ONE structured JSON log line via a
          module-level `logging.Logger` containing at least: `request_id`,
          `method`, `path`, `status` (captured by intercepting
          `http.response.start`), and `duration_ms`.
        - If the inner app raised, `status` should reflect what actually
          got sent (if `ExceptionHandlingMiddleware` above this layer sent a
          500, that 500 is what gets logged) or `None`/`0` if nothing was
          sent before the exception propagated past this layer too.

    TimeoutMiddleware
        - Constructor takes `timeout_seconds: float`.
        - Wrap the call to the inner app in `asyncio.timeout(timeout_seconds)`
          (3.11+, preferred over `asyncio.wait_for` for this — no need to
          juggle a coroutine object) or `asyncio.wait_for`.
        - On `TimeoutError`, if no response has started yet (track this via
          your `send` wrapper), send a clean `504` JSON response. If a
          response already started, there's nothing safe left to send —
          just let the cancellation propagate (do not try to send a second
          `http.response.start`; ASGI servers will reject or ignore it).

    AuthMiddleware
        - Constructor takes a `set[str]` of valid bearer tokens.
        - Read the `Authorization` header from `scope["headers"]` (a list of
          `(bytes, bytes)` tuples — headers are ALWAYS lower-cased bytes in
          ASGI scope, unlike the mixed-case strings you see in an HTTP
          client's response object).
        - Expect the format `Bearer <token>`. Missing/malformed header or a
          token not in the valid set -> send `401` directly (never call the
          inner app) with body `{"detail": "unauthorized"}`.
        - A `/health` path (exact match) bypasses auth entirely — a common
          real-world carve-out for load-balancer health checks.

    ExceptionHandlingMiddleware
        - The OUTERMOST layer (wraps everything else, including the other
          four middleware, so a bug in any of them is also caught here).
        - Catch any `Exception` (not `BaseException` — let
          `asyncio.CancelledError`/`KeyboardInterrupt` propagate, they are
          not application errors) raised by the inner app.
        - Log it (with `exc_info=True` so the traceback is captured) via the
          same structured logger.
        - If no response has started yet, send a `500` JSON body
          `{"detail": "internal server error"}` — never leak the exception
          message or traceback to the client.
        - If a response already started, there's nothing safe to do but
          re-raise (same reasoning as TimeoutMiddleware).

    build_app() -> ASGIApp
        - Returns the WRAPPED ASGI callable, not the bare `FastAPI`
          instance — `app(scope, receive, send)` resolves via
          `type(app).__call__`, never an instance attribute, so there is
          no way to retrofit middleware onto an existing `FastAPI()`
          instance's call behavior after the fact. Build the routes on a
          `FastAPI()` instance, then wrap *that* and return the outermost
          wrapper.
        - A tiny demo app with:
            GET /health          -> {"status": "ok"}  (no auth required)
            GET /whoami          -> {"request_id": <the current request id>}
            GET /boom            -> raises RuntimeError("boom") on purpose
            GET /slow?seconds=N  -> `await asyncio.sleep(N)` then 200 (used
                                    to exercise the timeout middleware)
        - Wrap it with all five middleware in the order given at the top of
          this file. Remember: in ASGI, the FIRST middleware you wrap with
          becomes the OUTERMOST layer only if you wrap in the right order —
          work out (and comment on) which order of `app = X(app)` calls
          produces "ExceptionHandling is outermost."

ACCEPTANCE CRITERIA
--------------------
1. `GET /health` succeeds with no `Authorization` header (auth bypass).
2. Any other route without a valid `Authorization: Bearer <token>` header
   returns 401 and never reaches the route handler (verify via a route that
   would otherwise have an observable side effect, or simply that `/boom`
   with no auth returns 401, not 500).
3. `GET /whoami` (with valid auth) returns a `request_id` that also appears
   in the response's `X-Request-ID` header, and the two match.
4. `GET /boom` (with valid auth) returns 500 with a generic body — the
   `RuntimeError` message is never present in the response.
5. `GET /slow?seconds=<longer than the configured timeout>` (with valid
   auth) returns 504, not 200 and not a hung connection.
6. Every request produces exactly one structured log record with the
   correct `status` and a `duration_ms >= 0`.
7. Two concurrent requests never see each other's `request_id` (the
   ContextVar isolation actually works) — provable by firing concurrent
   requests and asserting each response's id is unique and self-consistent.
8. mypy-clean, black-formatted, ruff-clean.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, MutableMapping
from contextvars import ContextVar

from fastapi import FastAPI

# ASGI type aliases (the stdlib/Starlette don't export these as a stable
# public API at time of writing, so most ASGI middleware in the wild rolls
# its own aliases like this).
Scope = MutableMapping[str, object]
Message = MutableMapping[str, object]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

logger = logging.getLogger("middleware_chain")


class RequestIDMiddleware:
    """Tags every HTTP request with a per-request correlation id."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # TODO: pass through unchanged for non-"http" scope types.
        # TODO: generate a uuid4 hex id, `request_id_var.set(...)`, and
        # `.reset(token)` in a finally block.
        # TODO: build a `send` wrapper that appends an `x-request-id` header
        # on the `http.response.start` message before forwarding it.
        raise NotImplementedError("TODO: implement RequestIDMiddleware")


class AccessLogMiddleware:
    """Emits one structured JSON log line per request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # TODO: pass through unchanged for non-"http" scope types.
        # TODO: time the call, capture the eventual status via a `send`
        # wrapper, and log exactly once in a finally block (covers both the
        # success and exception paths).
        raise NotImplementedError("TODO: implement AccessLogMiddleware")


class TimeoutMiddleware:
    """Bounds how long the inner app may take to produce a response."""

    def __init__(self, app: ASGIApp, *, timeout_seconds: float) -> None:
        self.app = app
        self.timeout_seconds = timeout_seconds

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # TODO: pass through unchanged for non-"http" scope types.
        # TODO: track whether a response has started (via a `send`
        # wrapper). On `TimeoutError` from `asyncio.timeout(...)`, send a
        # 504 JSON body IF nothing has started yet; otherwise re-raise.
        raise NotImplementedError("TODO: implement TimeoutMiddleware")


class AuthMiddleware:
    """Rejects requests without a valid bearer token (except /health)."""

    def __init__(self, app: ASGIApp, *, valid_tokens: set[str]) -> None:
        self.app = app
        self.valid_tokens = valid_tokens

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # TODO: pass through unchanged for non-"http" scope types and for
        # scope["path"] == "/health".
        # TODO: read scope["headers"] (list[tuple[bytes, bytes]], lower-cased
        # names), parse "authorization: Bearer <token>", and send a 401
        # directly (do not call self.app) if missing/invalid.
        raise NotImplementedError("TODO: implement AuthMiddleware")


class ExceptionHandlingMiddleware:
    """Outermost layer: converts any unhandled Exception into a clean 500."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # TODO: pass through unchanged for non-"http" scope types.
        # TODO: try/except Exception around `await self.app(...)`; track
        # whether a response has started via a `send` wrapper; on exception,
        # log with exc_info=True and send a 500 JSON body if nothing has
        # started yet, else re-raise.
        raise NotImplementedError("TODO: implement ExceptionHandlingMiddleware")


def build_app(*, valid_tokens: set[str], timeout_seconds: float = 2.0) -> ASGIApp:
    """Wire the demo FastAPI app with all five middleware, in the correct
    nesting order so ExceptionHandlingMiddleware ends up outermost."""
    app = FastAPI()

    # TODO: add the four demo routes (/health, /whoami, /boom, /slow).

    # TODO: wrap `app` with the five middleware. Note that FastAPI/Starlette
    # is itself a valid ASGI app, so `app` can be passed directly as the
    # `app` argument to your outermost middleware constructor — but the
    # ORDER you nest them in determines the runtime call order. Work out
    # (and comment) which nesting produces the order documented at the top
    # of this file. Return the final (outermost) wrapped callable, not
    # `app` itself.
    raise NotImplementedError("TODO: implement build_app")


# ---------------------------------------------------------------------------
# Hints
# -----
# - `scope["headers"]` entries are `(bytes, bytes)` with LOWER-CASED header
#   names — `b"authorization"`, never `b"Authorization"`.
# - You can send a complete response "by hand" from inside middleware with
#   two `send()` calls; write a small private helper
#   `_send_json(send, status, body)` and reuse it in Auth/Timeout/
#   ExceptionHandling middleware instead of repeating the two calls three
#   times.
# - `asyncio.timeout(seconds)` (3.11+) is a context manager — prefer it over
#   `asyncio.wait_for(coro, seconds)` when you're not holding a bare
#   coroutine object already (here you're awaiting `self.app(...)` inline,
#   which `asyncio.timeout` handles more naturally).
# - To know whether a response already started inside Timeout/Exception
#   middleware, set a `bool` flag (e.g. `started = False`) in an enclosing
#   scope and flip it to `True` inside your `send` wrapper on
#   `"http.response.start"`.
#
# Pitfalls
# --------
# - Using a plain module-level variable instead of `ContextVar` for the
#   request id — under `asyncio`, concurrent requests interleave on one
#   thread/event loop, and a plain global gets clobbered by whichever
#   request set it last, not the request currently running.
# - Forgetting `.reset(token)` on the ContextVar — without it, in contexts
#   where tasks are reused (some server/test-client setups), a stale
#   request id can leak into the next request.
# - Sending a second `http.response.start` after one has already gone out
#   (e.g. Timeout or ExceptionHandling firing after the inner app already
#   began streaming) — ASGI servers will raise or the message is simply
#   invalid. Always gate on the `started` flag.
# - Catching `BaseException` instead of `Exception` in
#   ExceptionHandlingMiddleware — this would swallow
#   `asyncio.CancelledError`, breaking cooperative cancellation (e.g. from
#   TimeoutMiddleware itself, or from the ASGI server shutting down).
# - Forgetting the `/health` bypass and health-checking infrastructure
#   (load balancers, k8s probes) start getting 401s and taking the service
#   out of rotation.
#
# Stretch goals
# -------------
# - Add a `RateLimitMiddleware` (foreshadows problem 15) between Auth and
#   the app, keyed by the bearer token.
# - Make `AccessLogMiddleware` also log request body SIZE (not content —
#   never log bodies verbatim in production, they may contain secrets/PII)
#   by summing `http.request` message body chunks as they pass through
#   `receive`.
# - Propagate `X-Request-ID` from an *inbound* header if the caller already
#   set one (common when this service is itself downstream of another
#   service in a call chain) instead of always generating a fresh one.
