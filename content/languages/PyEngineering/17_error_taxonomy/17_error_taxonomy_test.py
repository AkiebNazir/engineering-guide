"""Tests for 17 · Error taxonomy."""

from __future__ import annotations

from importlib import import_module

import grpc  # type: ignore[import-untyped]  # no bundled/installed stubs
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_solution = import_module("17_error_taxonomy_solution")
AppError = _solution.AppError
ValidationError = _solution.ValidationError
NotFoundError = _solution.NotFoundError
ConflictError = _solution.ConflictError
AuthorizationError = _solution.AuthorizationError
RateLimitedError = _solution.RateLimitedError
UnavailableError = _solution.UnavailableError
InternalError = _solution.InternalError
to_http_status = _solution.to_http_status
to_grpc_status = _solution.to_grpc_status
install_exception_handlers = _solution.install_exception_handlers
run_batch = _solution.run_batch
summarize_group = _solution.summarize_group


# ---------------------------------------------------------------------------
# Hierarchy + status mapping
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "exc_type,expected_http,expected_grpc",
    [
        (ValidationError, 422, grpc.StatusCode.INVALID_ARGUMENT),
        (NotFoundError, 404, grpc.StatusCode.NOT_FOUND),
        (ConflictError, 409, grpc.StatusCode.ALREADY_EXISTS),
        (AuthorizationError, 403, grpc.StatusCode.PERMISSION_DENIED),
        (RateLimitedError, 429, grpc.StatusCode.RESOURCE_EXHAUSTED),
        (UnavailableError, 503, grpc.StatusCode.UNAVAILABLE),
        (InternalError, 500, grpc.StatusCode.INTERNAL),
    ],
    ids=lambda v: v.__name__ if isinstance(v, type) else str(v),
)
def test_status_mapping(
    exc_type: type, expected_http: int, expected_grpc: object
) -> None:
    exc = exc_type("boom")
    assert to_http_status(exc) == expected_http
    assert to_grpc_status(exc) == expected_grpc


def test_every_appError_subclass_is_mapped() -> None:
    """Guards against a new subclass being added but forgotten in the tables."""
    subclasses = AppError.__subclasses__()
    assert subclasses, "expected at least one AppError subclass"
    for cls in subclasses:
        exc = cls("x")
        assert isinstance(to_http_status(exc), int)
        assert isinstance(to_grpc_status(exc), grpc.StatusCode)


def test_unmapped_subclass_defaults_to_internal() -> None:
    class WeirdError(AppError):  # type: ignore[valid-type, misc]
        # AppError is pulled off a dynamically `import_module`-ed module
        # (digit-leading filename, can't `from ... import`), so mypy sees
        # it as `Any` and won't accept it as a base class statically —
        # this is real and correct at runtime, just unprovable to mypy.
        pass

    exc = WeirdError("unexpected")
    assert to_http_status(exc) == 500
    assert to_grpc_status(exc) == grpc.StatusCode.INTERNAL


def test_context_defaults_to_empty_dict() -> None:
    exc = NotFoundError("missing")
    assert exc.context == {}
    exc2 = NotFoundError("missing", context={"id": "42"})
    assert exc2.context == {"id": "42"}


# ---------------------------------------------------------------------------
# Exception chaining
# ---------------------------------------------------------------------------
def test_raise_from_preserves_cause() -> None:
    original = KeyError("user_id")
    try:
        try:
            raise original
        except KeyError as err:
            raise NotFoundError("user not found") from err
    except NotFoundError as exc:
        assert exc.__cause__ is original
        assert isinstance(exc.__cause__, KeyError)


def test_raise_from_none_suppresses_cause() -> None:
    try:
        try:
            raise ValueError("internal detail")
        except ValueError:
            raise ValidationError("bad input") from None
    except ValidationError as exc:
        assert exc.__cause__ is None
        # __context__ is still set implicitly by Python's exception
        # chaining machinery even when __cause__ is suppressed.
        assert isinstance(exc.__context__, ValueError)


# ---------------------------------------------------------------------------
# TaskGroup aggregation + except*
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_run_batch_aggregates_failures_into_exception_group() -> None:
    async def ok() -> str:
        return "fine"

    async def fails_validation() -> None:
        raise ValidationError("bad field")

    async def fails_not_found() -> None:
        raise NotFoundError("missing row")

    with pytest.raises(ExceptionGroup) as excinfo:
        await run_batch([ok(), fails_validation(), fails_not_found()])

    eg = excinfo.value
    kinds = sorted(type(e).__name__ for e in eg.exceptions)
    assert kinds == ["NotFoundError", "ValidationError"]


@pytest.mark.asyncio
async def test_run_batch_returns_results_when_all_succeed() -> None:
    async def double(n: int) -> int:
        return n * 2

    results = await run_batch([double(1), double(2), double(3)])
    assert results == [2, 4, 6]


def test_summarize_group_splits_by_type() -> None:
    eg = ExceptionGroup(
        "batch failed",
        [
            ValidationError("a"),
            ValidationError("b"),
            NotFoundError("c"),
        ],
    )
    assert summarize_group(eg) == {"ValidationError": 2, "NotFoundError": 1}


def test_summarize_group_reraises_unmatched_exceptions() -> None:
    """A non-AppError inside the group must not be silently dropped."""
    eg = ExceptionGroup(
        "mixed", [ValidationError("a"), RuntimeError("not a domain error")]
    )
    with pytest.raises(ExceptionGroup) as excinfo:
        summarize_group(eg)
    remaining = excinfo.value
    assert len(remaining.exceptions) == 1
    assert isinstance(remaining.exceptions[0], RuntimeError)


# ---------------------------------------------------------------------------
# FastAPI HTTP mapping
# ---------------------------------------------------------------------------
def _build_app() -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)

    @app.get("/tasks/{task_id}")
    async def get_task(task_id: str) -> dict[str, str]:
        if task_id != "known":
            raise NotFoundError(
                f"task {task_id} not found", context={"task_id": task_id}
            )
        return {"id": task_id}

    @app.get("/throttled")
    async def throttled() -> None:
        raise RateLimitedError("slow down")

    return app


def test_not_found_error_maps_to_http_404() -> None:
    client = TestClient(_build_app())
    resp = client.get("/tasks/missing")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"] == "NotFoundError"
    assert "missing" in body["detail"]


def test_known_task_returns_200() -> None:
    client = TestClient(_build_app())
    resp = client.get("/tasks/known")
    assert resp.status_code == 200
    assert resp.json() == {"id": "known"}


def test_rate_limited_error_maps_to_http_429() -> None:
    client = TestClient(_build_app())
    resp = client.get("/throttled")
    assert resp.status_code == 429
    assert resp.json()["error"] == "RateLimitedError"
