"""Tests for `25_production_service_capstone_solution.py`.

Run: .venv/bin/pytest 25_production_service_capstone/ -v
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
from importlib import import_module
from typing import Any

import pytest
from fastapi.testclient import TestClient

# The directory (and thus module) name starts with a digit, so it can't be
# named in a real `import` statement; pytest puts this file's directory on
# sys.path so the dynamic import below resolves at runtime. mypy has no
# static visibility into a dynamically-named module, so these are typed
# `Any` rather than faked into precise types.
_solution = import_module("25_production_service_capstone_solution")
JSONFormatter: Any = _solution.JSONFormatter
configure_logging: Any = _solution.configure_logging
create_app: Any = _solution.create_app
lifespan: Any = _solution.lifespan
install_signal_handlers: Any = _solution.install_signal_handlers
REQUEST_COUNTER: Any = _solution.REQUEST_COUNTER


@pytest.fixture
def client() -> Any:
    app = create_app()
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# /healthz, /readyz.
# ---------------------------------------------------------------------------
def test_healthz_always_ok(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_ok_after_lifespan_startup(client: TestClient) -> None:
    # The fixture already entered `with TestClient(...) as client`, which
    # runs lifespan startup to completion before any request is sent.
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


# ---------------------------------------------------------------------------
# Lifespan readiness transitions, exercised directly.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_lifespan_flips_readiness_start_then_stop() -> None:
    app = create_app()
    assert not hasattr(app.state, "ready") or app.state.ready is False

    async with lifespan(app):
        assert app.state.ready is True

    # Readiness must flip false immediately on shutdown - the ordering
    # that makes graceful shutdown actually graceful.
    assert app.state.ready is False


# ---------------------------------------------------------------------------
# /metrics.
# ---------------------------------------------------------------------------
def test_metrics_endpoint_reports_counter_and_histogram(client: TestClient) -> None:
    for _ in range(3):
        response = client.get("/work")
        assert response.status_code == 200

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    body = metrics_response.text

    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body
    # The /work path with 3 calls should show up in the counter's labels.
    assert 'path="/work"' in body


def test_request_counter_value_reflects_call_count(client: TestClient) -> None:
    before = REQUEST_COUNTER.labels("GET", "/work", "200")._value.get()
    for _ in range(4):
        client.get("/work")
    after = REQUEST_COUNTER.labels("GET", "/work", "200")._value.get()
    assert after - before == 4


# ---------------------------------------------------------------------------
# Structured JSON logging.
# ---------------------------------------------------------------------------
def test_json_formatter_produces_valid_json_with_required_keys() -> None:
    import json

    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="service",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello %s",
        args=("world",),
        exc_info=None,
    )
    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["message"] == "hello world"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "service"
    assert "timestamp" in parsed


def test_json_formatter_includes_extra_fields() -> None:
    import json

    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="service",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request handled",
        args=(),
        exc_info=None,
    )
    record.request_id = "abc-123"  # simulates logger.info(..., extra={...})
    parsed = json.loads(formatter.format(record))
    assert parsed["request_id"] == "abc-123"


def test_configure_logging_is_idempotent() -> None:
    logger1 = configure_logging()
    handler_count = len(logger1.handlers)
    logger2 = configure_logging()
    assert logger2 is logger1
    assert len(logger2.handlers) == handler_count


# ---------------------------------------------------------------------------
# Signal handling.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_install_signal_handlers_sets_event_on_sigterm() -> None:
    shutdown_event = asyncio.Event()
    await install_signal_handlers(shutdown_event)
    try:
        os.kill(os.getpid(), signal.SIGTERM)
        await asyncio.wait_for(shutdown_event.wait(), timeout=2.0)
        assert shutdown_event.is_set()
    finally:
        # Clean up so this handler doesn't leak into other tests' event
        # loops (pytest-asyncio uses a fresh loop per test, but the OS
        # signal disposition is process-wide until reset or the loop
        # closes).
        loop = asyncio.get_running_loop()
        loop.remove_signal_handler(signal.SIGTERM)
        loop.remove_signal_handler(signal.SIGINT)


# ---------------------------------------------------------------------------
# create_app has no import/call-time side effects beyond building the app.
# ---------------------------------------------------------------------------
def test_create_app_is_side_effect_free() -> None:
    app = create_app()
    assert app.routes  # built successfully, has registered routes
    # Calling it again must not raise (e.g. from re-registering metrics).
    app2 = create_app()
    assert app2.routes
