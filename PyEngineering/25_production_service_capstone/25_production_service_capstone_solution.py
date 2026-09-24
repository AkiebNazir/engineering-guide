"""
25 - Production service capstone - Reference Solution
==========================================================

See `25_production_service_capstone_explanation.py` for the full spec,
rationale, and acceptance criteria. See `Dockerfile` and `ci.yml` in this
directory for the deploy-path artifacts.
"""

from __future__ import annotations

import asyncio
import json
import logging
import signal
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

# The fixed attribute set on a bare LogRecord - anything beyond this on a
# given record was passed via `extra={...}` and belongs in the JSON output.
_STANDARD_LOG_RECORD_ATTRS = frozenset(
    vars(logging.LogRecord("", 0, "", 0, "", (), None)).keys()
)


# ---------------------------------------------------------------------------
# Structured JSON logging.
# ---------------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    """Formats each `LogRecord` as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            # .getMessage(), not .msg - applies %-style args, matching
            # what a plain (non-JSON) formatter would actually print.
            "message": record.getMessage(),
        }
        extras = {
            key: value
            for key, value in vars(record).items()
            if key not in _STANDARD_LOG_RECORD_ATTRS
        }
        payload.update(extras)
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Idempotent: calling this more than once never attaches a second
    handler to the same logger."""
    logger = logging.getLogger("service")
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


# ---------------------------------------------------------------------------
# Prometheus metrics + middleware.
# ---------------------------------------------------------------------------
# Defined once, at import time: Counter/Histogram register with the global
# default CollectorRegistry at construction and raise on a duplicate name,
# so these must never be (re)created inside create_app().
REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)


async def metrics_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    path = request.url.path
    REQUEST_LATENCY.labels(request.method, path).observe(duration)
    REQUEST_COUNTER.labels(request.method, path, str(response.status_code)).inc()
    return response


# ---------------------------------------------------------------------------
# Lifespan: startup warmup / shutdown drain, readiness flips first.
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger = configure_logging()
    app.state.ready = False
    logger.info("startup: warming up")
    # Stand-in for real warmup work (opening a DB pool, priming a cache).
    await asyncio.sleep(0)
    app.state.ready = True
    logger.info("startup: ready")

    try:
        yield
    finally:
        # Readiness flips false FIRST, before any other shutdown work -
        # this is the one ordering that matters: a load balancer polling
        # /readyz must stop routing new traffic before in-flight requests
        # start draining, not after.
        app.state.ready = False
        logger.info("shutdown: draining")
        await asyncio.sleep(0)  # stand-in for a real drain/cleanup step
        logger.info("shutdown: complete")


# ---------------------------------------------------------------------------
# App factory.
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.middleware("http")(metrics_middleware)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        # Liveness: "is this process alive and able to serve a request at
        # all." Always 200 regardless of readiness - a warming-up or
        # draining process is still alive and should not be restarted.
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz() -> Response:
        # Readiness: "should this process receive new traffic right now."
        if app.state.ready:
            return JSONResponse({"status": "ready"}, status_code=200)
        return JSONResponse({"status": "not ready"}, status_code=503)

    @app.get("/metrics")
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/work")
    async def work() -> dict[str, str]:
        # Trivial endpoint whose only purpose is to exercise
        # metrics_middleware in tests.
        return {"status": "done"}

    return app


# ---------------------------------------------------------------------------
# Signal handling + programmatic uvicorn server for graceful shutdown.
# ---------------------------------------------------------------------------
async def install_signal_handlers(shutdown_event: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown_event.set)


async def run() -> None:  # pragma: no cover - exercised manually, not by pytest
    configure_logging()
    app = create_app()
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_config=None)
    server = uvicorn.Server(config)

    shutdown_event = asyncio.Event()
    await install_signal_handlers(shutdown_event)

    # Run the server as a background task (not the blocking uvicorn.run())
    # so this coroutine can await a custom shutdown trigger - uvicorn.run()
    # installs its own SIGTERM/SIGINT handlers and blocks the calling
    # thread, leaving no room to layer in different shutdown logic.
    server_task = asyncio.create_task(server.serve())
    await shutdown_event.wait()

    # Graceful stop: finish in-flight requests, then return from serve().
    # Distinct from cancelling server_task outright, which drops
    # connections immediately instead of draining them.
    server.should_exit = True
    await server_task


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(run())


# ---------------------------------------------------------------------------
# Best practices
# ---------------------------------------------------------------------------
# - Keep liveness and readiness genuinely separate endpoints backed by
#   genuinely separate questions - "is the process alive" vs "should it
#   receive traffic" - and wire an orchestrator's liveness/readiness
#   probes to the matching one, never both to the same endpoint.
# - Flip readiness false before draining, not after, on shutdown - this
#   ordering is the entire mechanism that makes a rolling deploy invisible
#   to clients instead of dropping their in-flight requests.
# - Define Prometheus metrics once, at module import time, never inside a
#   per-request or per-app-instance function - the client registers them
#   globally and a re-registration is a hard error, not a silent no-op.
# - Emit structured (JSON) logs with a fixed key set
#   (timestamp/level/logger/message) plus request-scoped extras, so a log
#   aggregator can filter/query on real fields instead of regexing prose.
# - Prefer a programmatic `uvicorn.Server` over the blocking `uvicorn.run()`
#   whenever the process needs custom shutdown wiring (a signal handler
#   driving an `asyncio.Event`, here) - `uvicorn.run()` owns the event
#   loop and its own signal handlers, leaving no hook for anything else.
# - Multi-stage, non-root, slim Docker images by default: a build
#   toolchain has no business shipping to production, and a process
#   should never run as root inside its container unless it has a real,
#   specific reason to.
#
# Alternative approaches
# -----------------------
# - `starlette.middleware.base.BaseHTTPMiddleware` vs the `@app.middleware
#   ("http")` decorator used here - equivalent for this use case;
#   `BaseHTTPMiddleware` subclassing reads better once you have several
#   middlewares that need to share state/configuration via `__init__`.
# - `structlog` or `python-json-logger` (third-party) instead of a
#   hand-rolled `logging.Formatter` - richer context-binding APIs, not
#   used here to stay within this curriculum's stdlib-first default; a
#   real service reaching for more than "flat JSON of a few fields" often
#   upgrades to one of these.
# - `prometheus_client.exposition.start_http_server` runs metrics on a
#   *separate* port/server outside the main app - common when you want
#   metrics scraping isolated from application traffic (e.g. different
#   network policy for the scrape port); this solution serves `/metrics`
#   on the same app instead, simpler when that isolation isn't needed.
#
# A note on project layout (this file vs. a real service):
# -----------------------------------------------------------
# This curriculum keeps every problem as flat sibling files
# (`NN_topic_slug_explanation.py` / `_solution.py` / `_test.py`) so the
# three files for a topic sit together and the web-app-free workflow in
# this repo's README stays simple. A real standalone service built from
# this code would instead use a `src/` layout:
#
#     pyproject.toml
#     src/
#       taskservice/
#         __init__.py
#         app.py          # create_app(), lifespan, routes
#         logging.py      # JSONFormatter, configure_logging
#         metrics.py      # REQUEST_COUNTER, REQUEST_LATENCY, middleware
#         main.py         # run(), install_signal_handlers, __main__
#     tests/
#       test_app.py
#
# The `src/` layout (package code under `src/<package>/`, not directly
# under the repo root) forces tests to import the *installed* package
# rather than accidentally picking up the working directory's copy - it
# catches "works here, fails once packaged" bugs (missing `__init__.py`,
# a file not included in the distribution) that a flat layout can hide.
# `pyproject.toml` (PEP 621 `[project]` table, `[build-system]` pointing
# at a backend like `setuptools`/`hatchling`) replaces `setup.py`/
# `setup.cfg` as the single declarative source of package metadata,
# dependencies, and tool configuration (`[tool.mypy]`, `[tool.ruff]`,
# `[tool.pytest.ini_options]`) - one file instead of several.
