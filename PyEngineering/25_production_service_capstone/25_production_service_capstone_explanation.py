"""
25 - Production service capstone
====================================

WHAT WE'RE BUILDING
--------------------
A minimal but genuinely production-shaped FastAPI service, wiring together
every operational concern this curriculum has treated separately into one
running app:

- `GET /healthz` - liveness: "is the process alive and serving requests."
- `GET /readyz` - readiness: "is the process ready to receive real
  traffic," separate from liveness on purpose (see below).
- `GET /metrics` - a Prometheus text-format exposition with a real
  `Counter` (request count) and `Histogram` (request latency), updated by
  a middleware that instruments every request generically.
- Structured JSON logging via a stdlib `logging.Formatter` subclass - no
  third-party logging library, matching this curriculum's stdlib-first
  default.
- Graceful shutdown via a FastAPI `lifespan` context manager (readiness
  flips false *before* cleanup, so a load balancer stops routing new
  traffic while in-flight requests finish) plus real OS signal handling
  (`SIGTERM`/`SIGINT`) driving that shutdown from outside the ASGI layer,
  the way a container orchestrator actually stops a process.
- A `Dockerfile` (multi-stage, slim final image, non-root user, `uvicorn`
  entrypoint) and a minimal CI YAML example (`ci.yml`, lint + typecheck +
  test) living in this directory as documentation of the deploy path this
  service is built for - not executed by the test suite, since this
  curriculum has no CI runner or Docker daemon to verify them against, but
  written as real, usable artifacts.

WHY THIS MATTERS IN REAL SYSTEMS
-----------------------------------
1. **Liveness and readiness are different questions, and conflating them
   causes outages.** Liveness answers "should the orchestrator restart
   this process" (a stuck/deadlocked process should be killed).
   Readiness answers "should the load balancer send this process
   traffic right now" (a process that's alive but still warming up, or
   mid-graceful-shutdown, should *not* receive new requests, but also
   should NOT be restarted for that). A single combined `/health` that a
   Kubernetes `livenessProbe` uses is the classic setup that causes a
   slow-starting or draining pod to get killed and restarted in a loop
   instead of just quietly not receiving traffic.
2. **`/metrics` is how a service's actual behavior gets observed in
   production**, not logs (too granular, expensive to aggregate
   numerically) and not traces alone (per-request, not aggregate-rate
   shaped). A `Counter` for "how many, and of what" and a `Histogram` for
   "how long, distributed" are the two metric shapes that cover the vast
   majority of what an on-call engineer needs at 3am: request rate,
   error rate, and latency percentiles - the well-known "RED" method
   (Rate, Errors, Duration).
3. **Structured (JSON) logs are what makes centralized log search
   possible.** A free-text `logger.info(f"got request {id}")` is fine on
   a laptop; at scale, a log aggregator (or `jq`) needs `level`,
   `logger`, `message`, and request-scoped fields as actual JSON keys to
   filter/query efficiently, not substrings to regex out of prose.
4. **Graceful shutdown is the difference between "deploys drop requests"
   and "deploys are invisible to users."** A rolling deploy sends
   `SIGTERM`, expects a brief drain window, then the process exits.
   Ignoring `SIGTERM` (or exiting instantly on it) either hangs the
   deploy (orchestrator waits out its grace period, then `SIGKILL`s -
   dropping in-flight requests) or drops requests immediately. Flipping
   readiness false *first*, waiting briefly, then actually stopping is
   the standard sequence.
5. **A multi-stage, non-root, slim Dockerfile is the production default,
   not paranoia.** A single-stage image built `FROM python:3.12` ships
   the entire build toolchain (compilers, package caches) in the image
   you run in production - bigger attack surface, bigger image, slower
   pulls. Running as a named non-root user is a baseline container
   security practice: a container-escape or dependency-RCE bug is worse
   when the process it compromises is already root inside the container.

CONCEPTS COVERED
------------------
- FastAPI `/healthz`, `/readyz` endpoints and why they're separate
- `prometheus_client.Counter`/`Histogram`, a generic timing middleware,
  and a `/metrics` endpoint serving `generate_latest()`
- A stdlib `logging.Formatter` subclass emitting JSON log lines
- FastAPI `lifespan` (startup warmup / shutdown drain) plus
  `asyncio`-level `SIGTERM`/`SIGINT` handling via
  `loop.add_signal_handler`
- Driving `uvicorn.Server` programmatically (`server.should_exit`)
  instead of the blocking `uvicorn.run()`, so a custom shutdown trigger
  (the signal handler) can stop it cooperatively
- A multi-stage `Dockerfile` (builder stage installs deps into a venv;
  final stage copies just the venv + app code, runs as non-root)
- A `src/` layout + `pyproject.toml` project-layout note (documented,
  not restructured - see the note at the bottom of the solution file for
  why this exercise itself stays flat)

THE SPEC
---------
`class JSONFormatter(logging.Formatter)`
    `format(self, record: logging.LogRecord) -> str` returns a JSON
    object with at least `"timestamp"`, `"level"`, `"logger"`,
    `"message"` keys, plus any *extra* fields the caller passed via
    `logger.info(msg, extra={...})` (anything on the record beyond the
    standard `logging.LogRecord` attributes).

`def configure_logging(level: int = logging.INFO) -> logging.Logger`
    Creates/returns a logger named `"service"` with a single
    `StreamHandler` using `JSONFormatter`, set to `level`. Idempotent -
    calling it twice must not attach a second handler.

`REQUEST_COUNTER: Counter` / `REQUEST_LATENCY: Histogram`
    Module-level Prometheus metrics (defined once, at import time -
    Prometheus client objects register themselves with a global registry
    and raise if you redefine the same metric name twice).
    `REQUEST_COUNTER` labeled by `("method", "path", "status")`;
    `REQUEST_LATENCY` labeled by `("method", "path")`.

`async def metrics_middleware(request, call_next) -> Response`
    Times `call_next(request)`, then increments `REQUEST_COUNTER` and
    observes `REQUEST_LATENCY` with the request's method, path, and
    (for the counter) response status code.

`def create_app() -> FastAPI`
    Builds and returns the app: registers `metrics_middleware`, the
    lifespan below, and the routes:
    - `GET /healthz -> {"status": "ok"}`, always 200.
    - `GET /readyz -> {"status": "ready"}` (200) or
      `{"status": "not ready"}` (503) based on `app.state.ready`.
    - `GET /metrics -> Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)`.
    - `GET /work -> {"status": "done"}` - a trivial endpoint whose only
      purpose is to exercise `metrics_middleware` in tests.

`lifespan(app: FastAPI) -> AsyncIterator[None]` (`@asynccontextmanager`)
    Startup: `app.state.ready = False`, do a (simulated) warmup step,
    then `app.state.ready = True`. Shutdown (in the `finally` after
    `yield`): `app.state.ready = False` *first* (so `/readyz` starts
    failing immediately), then a (simulated) drain step.

`async def install_signal_handlers(shutdown_event: asyncio.Event) -> None`
    Registers `shutdown_event.set` as the handler for `SIGTERM` and
    `SIGINT` on the running event loop via `loop.add_signal_handler`.

`async def run() -> None` (used by `if __name__ == "__main__":`)
    Builds the app, starts a `uvicorn.Server` as a background task
    instead of the blocking `uvicorn.run()`, installs signal handlers
    into a `shutdown_event`, awaits that event, then sets
    `server.should_exit = True` and awaits the server task - the
    programmatic equivalent of `uvicorn.run()` but with a custom
    shutdown trigger wired in.

ACCEPTANCE CRITERIA
---------------------
1. `GET /healthz` returns 200 regardless of `app.state.ready`.
2. `GET /readyz` returns 200 when `app.state.ready` is `True`, 503 when
   `False`.
3. Directly exercising `lifespan(app)` as an async context manager shows
   `app.state.ready` go `False` (start) `-> True` (after startup
   completes) `-> False` (immediately on shutdown, before any other
   shutdown work).
4. After a few requests to `/work`, `GET /metrics` response body contains
   both the counter's and the histogram's metric names, and the
   counter's value for `/work` reflects the number of calls made.
5. `JSONFormatter` produces valid JSON (parseable by `json.loads`) for a
   log record, containing `timestamp`/`level`/`logger`/`message`, and
   includes an `extra` field passed via `logger.info(..., extra=...)`.
6. `configure_logging()` called twice does not attach a duplicate
   handler (`logger.handlers` length unchanged on the second call).
7. `install_signal_handlers` actually installs a working handler: sending
   a real `SIGTERM` to the current process (`os.kill(os.getpid(),
   signal.SIGTERM)`) inside a test sets the `shutdown_event`.
8. `create_app()` has no import-time or call-time side effects beyond
   building the app object (no `uvicorn.run()`, no network calls) - it's
   safe to call from a test.
9. mypy-clean, black-formatted, ruff-clean.

Note on the `Dockerfile`/`ci.yml`/project-layout: these live in this
directory as real, hand-written artifacts documenting how this service
would actually be built and deployed. They are not executed by
`pytest`/`mypy`/`ruff` (no Docker daemon or CI runner is available in this
curriculum's verification loop) - review them by reading, the way you'd
review a colleague's PR that touches deploy config, not by running them.
"""

from __future__ import annotations

import asyncio
import json  # noqa: F401 - used once you implement JSONFormatter
import logging
import signal  # noqa: F401 - used once you implement install_signal_handlers
import time  # noqa: F401 - used once you implement metrics_middleware
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime  # noqa: F401 - used once you implement JSONFormatter

import uvicorn  # noqa: F401 - used once you implement run()
from fastapi import FastAPI, Request, Response
from prometheus_client import (  # noqa: F401 - used once you implement the metrics
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)


# ---------------------------------------------------------------------------
# Structured JSON logging.
# ---------------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    """Formats each `LogRecord` as a single JSON line.

    TODO: override `format(self, record: logging.LogRecord) -> str`.
      1. Build a dict with `"timestamp"` (e.g.
         `datetime.fromtimestamp(record.created, tz=UTC).isoformat()`),
         `"level"` (`record.levelname`), `"logger"` (`record.name`),
         `"message"` (`record.getMessage()` - NOT `record.msg`, which
         doesn't apply `%`-args).
      2. Merge in "extra" fields: anything set on `record.__dict__` that
         isn't one of the standard `logging.LogRecord` attributes (name,
         msg, args, levelname, levelno, pathname, filename, module,
         exc_info, exc_text, stack_info, lineno, funcName, created,
         msecs, relativeCreated, thread, threadName, processName,
         process, taskName). A `logging.LogRecord()` constructed with no
         extras has a fixed, known attribute set - diff against that
         rather than hand-maintaining the list yourself if you'd rather;
         either approach is fine.
      3. `json.dumps(...)` the merged dict and return it.
    """

    def format(self, record: logging.LogRecord) -> str:
        raise NotImplementedError("TODO: implement JSONFormatter.format")


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """TODO:
    1. `logger = logging.getLogger("service")`.
    2. If `logger.handlers` is already non-empty, return it as-is
       (idempotent - avoids attaching a second handler if called again,
       e.g. once at import and once in a test fixture).
    3. Otherwise: create a `logging.StreamHandler()`, set its formatter
       to `JSONFormatter()`, `logger.addHandler(handler)`,
       `logger.setLevel(level)`.
    4. Return `logger`.
    """
    raise NotImplementedError("TODO: implement configure_logging")


# ---------------------------------------------------------------------------
# Prometheus metrics + middleware.
# ---------------------------------------------------------------------------
# TODO: define at module level (NOT inside a function - Prometheus client
# objects register with a global registry at construction time and raise
# ValueError on a duplicate name, so these must be created exactly once,
# at import time):
#
# REQUEST_COUNTER = Counter(
#     "http_requests_total", "Total HTTP requests",
#     ["method", "path", "status"],
# )
# REQUEST_LATENCY = Histogram(
#     "http_request_duration_seconds", "HTTP request latency in seconds",
#     ["method", "path"],
# )


async def metrics_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """TODO:
    1. `start = time.perf_counter()`.
    2. `response = await call_next(request)`.
    3. `duration = time.perf_counter() - start`.
    4. `REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)`.
    5. `REQUEST_COUNTER.labels(request.method, request.url.path,
       str(response.status_code)).inc()`.
    6. Return `response`.
    """
    raise NotImplementedError("TODO: implement metrics_middleware")


# ---------------------------------------------------------------------------
# Lifespan: startup warmup / shutdown drain, readiness flips first.
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """TODO:
    1. `app.state.ready = False`.
    2. (Simulated warmup - a real service might open a DB pool, warm a
       cache, etc.) `await asyncio.sleep(0)`.
    3. `app.state.ready = True`.
    4. `yield`.
    5. In a way that always runs even if the app raises during its
       lifetime (a plain statement after `yield` already does - no
       explicit try/finally is required here since there's no
       async-with/resource to release beyond these two state flips, but
       wrapping in `try/finally` is also fine and arguably clearer -
       either is acceptable): `app.state.ready = False` FIRST (so
       `/readyz` starts failing immediately, before any other shutdown
       work), then a (simulated) drain step, e.g.
       `await asyncio.sleep(0)`.
    """
    raise NotImplementedError("TODO: implement lifespan")
    yield  # pragma: no cover - makes this an async generator for mypy


# ---------------------------------------------------------------------------
# App factory.
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    """TODO:
    1. `app = FastAPI(lifespan=lifespan)`.
    2. `app.middleware("http")(metrics_middleware)` (or the
       `@app.middleware("http")` decorator form if you prefer - both
       register the same function).
    3. Register routes:
       - `GET /healthz`: `async def healthz() -> dict[str, str]: return
         {"status": "ok"}`.
       - `GET /readyz`: return 200 `{"status": "ready"}` if
         `app.state.ready` else a 503 `JSONResponse({"status": "not
         ready"}, status_code=503)`.
       - `GET /metrics`: `return Response(generate_latest(),
         media_type=CONTENT_TYPE_LATEST)`.
       - `GET /work`: trivial handler returning `{"status": "done"}`,
         used only to exercise the metrics middleware in tests.
    4. Return `app`.
    """
    raise NotImplementedError("TODO: implement create_app")


# ---------------------------------------------------------------------------
# Signal handling + programmatic uvicorn server for graceful shutdown.
# ---------------------------------------------------------------------------
async def install_signal_handlers(shutdown_event: asyncio.Event) -> None:
    """TODO:
    1. `loop = asyncio.get_running_loop()`.
    2. For each of `signal.SIGTERM`, `signal.SIGINT`:
       `loop.add_signal_handler(sig, shutdown_event.set)`.
    """
    raise NotImplementedError("TODO: implement install_signal_handlers")


async def run() -> None:  # pragma: no cover - exercised manually, not by pytest
    """TODO:
    1. `configure_logging()`.
    2. `app = create_app()`.
    3. `config = uvicorn.Config(app, host="0.0.0.0", port=8000,
       log_config=None)`.
    4. `server = uvicorn.Server(config)`.
    5. `shutdown_event = asyncio.Event()`.
    6. `await install_signal_handlers(shutdown_event)`.
    7. `server_task = asyncio.create_task(server.serve())`.
    8. `await shutdown_event.wait()`.
    9. `server.should_exit = True` (tells uvicorn to stop accepting new
       connections and drain in-flight ones, then return from `serve()`).
    10. `await server_task`.
    """
    raise NotImplementedError("TODO: implement run")


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(run())


# ---------------------------------------------------------------------------
# HINTS
# -----
# - `record.getMessage()` (not `record.msg`) applies `%`-style formatting
#   args (`logger.info("x=%s", x)`) - using `.msg` directly would emit
#   the unformatted template string into the JSON log.
# - A `logging.LogRecord`'s standard attribute set is fixed; you can get
#   it once via `set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__)`
#   and diff any record's `__dict__` keys against it to find "extra" keys
#   - simpler than hand-maintaining the list.
# - `Counter.labels(...)` / `Histogram.labels(...)` return a *view* bound
#   to that label combination - call `.inc()`/`.observe()` on the result
#   of `.labels(...)`, not on the metric object itself when labels are
#   declared.
# - `loop.add_signal_handler` only works on the main thread of a Unix
#   event loop (not Windows' default proactor loop) - fine for this
#   curriculum's target platforms, worth knowing as a portability limit.
# - `uvicorn.Server.should_exit = True` triggers the *graceful* shutdown
#   path (finish in-flight requests, then stop) - distinct from just
#   cancelling the `server.serve()` task, which would drop connections
#   immediately.
#
# COMMON PITFALLS
# ----------------
# - Defining `Counter`/`Histogram` inside `create_app()` instead of at
#   module level - calling `create_app()` twice (e.g. once per test) then
#   raises `ValueError: Duplicated timeseries in CollectorRegistry`.
# - Flipping `app.state.ready = False` *after* the drain step instead of
#   before - that's the one ordering that actually matters for graceful
#   shutdown; readiness must fail first so no *new* traffic arrives while
#   old traffic drains.
# - Combining `/healthz` and `/readyz` into one endpoint - defeats the
#   entire liveness-vs-readiness distinction described in the module
#   docstring; an orchestrator polling a combined endpoint restarts a
#   draining/warming-up pod instead of just routing around it.
# - Calling `uvicorn.run()` (blocking, owns its own event loop and signal
#   handling) instead of the programmatic `uvicorn.Server`/`server.serve()`
#   pattern when you need a *custom* shutdown trigger layered in -
#   `uvicorn.run()` already installs its own SIGTERM/SIGINT handlers,
#   which would conflict with `install_signal_handlers` here.
#
# STRETCH GOALS
# --------------
# - Add a `/readyz` dependency check (e.g. a fake "database ping" that
#   fails for the first N calls) so readiness can flip back to `False`
#   mid-run, not just during startup/shutdown, and demonstrate a
#   load-balancer-style client backing off while it's false.
# - Add request-ID propagation: generate a UUID per request in the
#   metrics middleware, bind it into the JSON log formatter's "extra"
#   fields via a `contextvars.ContextVar`, so every log line emitted
#   while handling a request carries the same `request_id`.
# - Add a `Gauge` (`prometheus_client.Gauge`) tracking in-flight request
#   count, incremented at the start of `metrics_middleware` and
#   decremented in a `finally` - the third common Prometheus metric type
#   alongside `Counter`/`Histogram`.
