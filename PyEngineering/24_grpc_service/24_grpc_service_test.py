"""Tests for `24_grpc_service_solution.py`.

Spins up the real `grpc.aio` server in-process on an ephemeral port and
drives it through a real `grpc.aio` client for every test - no mocking of
gRPC internals.

Run: .venv/bin/pytest 24_grpc_service/ -v
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from importlib import import_module
from typing import Any

import grpc  # type: ignore[import-untyped]
import pytest
import pytest_asyncio

# The directory (and thus module) name starts with a digit, so it can't be
# named in a real `import` statement; pytest puts this file's directory on
# sys.path so the dynamic imports below resolve at runtime. mypy has no
# static visibility into dynamically-named modules, so these are typed
# `Any` rather than faked into precise types.
_solution = import_module("24_grpc_service_solution")
serve: Any = _solution.serve

pb2: Any = import_module("task_service_pb2")
pb2_grpc: Any = import_module("task_service_pb2_grpc")


@pytest_asyncio.fixture
async def server_address() -> AsyncIterator[str]:
    """Starts the real server on an ephemeral port; stops it after the test."""
    server, port, _servicer, _interceptor = await serve(port=0)
    try:
        yield f"127.0.0.1:{port}"
    finally:
        await server.stop(None)


@pytest_asyncio.fixture
async def running_server() -> AsyncIterator[tuple[Any, int, Any, Any]]:
    """Same as `server_address` but also exposes the servicer/interceptor
    for tests that want to inspect interceptor state directly."""
    server, port, servicer, interceptor = await serve(port=0)
    try:
        yield server, port, servicer, interceptor
    finally:
        await server.stop(None)


# ---------------------------------------------------------------------------
# Unary RPCs: CreateTask / GetTask, happy path and error model.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_then_get_round_trips(server_address: str) -> None:
    async with grpc.aio.insecure_channel(server_address) as channel:
        stub = pb2_grpc.TaskServiceStub(channel)
        created = await stub.CreateTask(pb2.CreateTaskRequest(title="write tests"))
        assert created.title == "write tests"
        assert created.done is False
        assert created.id

        fetched = await stub.GetTask(pb2.GetTaskRequest(id=created.id))
        assert fetched == created


@pytest.mark.asyncio
async def test_create_task_blank_title_is_invalid_argument(
    server_address: str,
) -> None:
    async with grpc.aio.insecure_channel(server_address) as channel:
        stub = pb2_grpc.TaskServiceStub(channel)
        with pytest.raises(grpc.aio.AioRpcError) as exc_info:
            await stub.CreateTask(pb2.CreateTaskRequest(title="   "))
        assert exc_info.value.code() == grpc.StatusCode.INVALID_ARGUMENT


@pytest.mark.asyncio
async def test_get_task_unknown_id_is_not_found(server_address: str) -> None:
    async with grpc.aio.insecure_channel(server_address) as channel:
        stub = pb2_grpc.TaskServiceStub(channel)
        with pytest.raises(grpc.aio.AioRpcError) as exc_info:
            await stub.GetTask(pb2.GetTaskRequest(id="does-not-exist"))
        assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND


# ---------------------------------------------------------------------------
# Server-streaming RPC: ListTasks.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_list_tasks_streams_every_created_task(server_address: str) -> None:
    async with grpc.aio.insecure_channel(server_address) as channel:
        stub = pb2_grpc.TaskServiceStub(channel)
        titles = ["a", "b", "c"]
        for title in titles:
            await stub.CreateTask(pb2.CreateTaskRequest(title=title))

        streamed_titles = set()
        async for task in stub.ListTasks(pb2.ListTasksRequest()):
            streamed_titles.add(task.title)

        assert streamed_titles == set(titles)


@pytest.mark.asyncio
async def test_list_tasks_empty_store_yields_nothing(server_address: str) -> None:
    async with grpc.aio.insecure_channel(server_address) as channel:
        stub = pb2_grpc.TaskServiceStub(channel)
        results = [task async for task in stub.ListTasks(pb2.ListTasksRequest())]
        assert results == []


# ---------------------------------------------------------------------------
# Deadline propagation: SlowOperation.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_slow_operation_completes_within_sufficient_timeout(
    server_address: str,
) -> None:
    async with grpc.aio.insecure_channel(server_address) as channel:
        stub = pb2_grpc.TaskServiceStub(channel)
        response = await stub.SlowOperation(
            pb2.SlowRequest(delay_seconds=0.1), timeout=5.0
        )
        assert response.message == "slept 0.1s"


@pytest.mark.asyncio
async def test_slow_operation_deadline_exceeded_and_stops_early(
    running_server: tuple[Any, int, Any, Any],
) -> None:
    _server, port, _servicer, _interceptor = running_server
    async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = pb2_grpc.TaskServiceStub(channel)
        start = time.monotonic()
        with pytest.raises(grpc.aio.AioRpcError) as exc_info:
            # Server would need 2s to finish; client only allows 0.3s.
            await stub.SlowOperation(pb2.SlowRequest(delay_seconds=2.0), timeout=0.3)
        elapsed = time.monotonic() - start

        assert exc_info.value.code() == grpc.StatusCode.DEADLINE_EXCEEDED
        # The server's cooperative-cancellation check must have kicked in
        # well before the full 2s delay would otherwise elapse.
        assert elapsed < 1.5


# ---------------------------------------------------------------------------
# Interceptor: LoggingInterceptor records unary and streaming RPCs.
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_logging_interceptor_records_unary_and_streaming_calls(
    running_server: tuple[Any, int, Any, Any],
) -> None:
    _server, port, _servicer, interceptor = running_server
    async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = pb2_grpc.TaskServiceStub(channel)
        await stub.CreateTask(pb2.CreateTaskRequest(title="x"))
        async for _ in stub.ListTasks(pb2.ListTasksRequest()):
            pass

    assert len(interceptor.calls) == 2
    methods = [method for method, _duration in interceptor.calls]
    assert any(m.endswith("/CreateTask") for m in methods)
    assert any(m.endswith("/ListTasks") for m in methods)
    for _method, duration in interceptor.calls:
        assert duration >= 0.0


@pytest.mark.asyncio
async def test_logging_interceptor_records_failed_calls_too(
    running_server: tuple[Any, int, Any, Any],
) -> None:
    _server, port, _servicer, interceptor = running_server
    async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as channel:
        stub = pb2_grpc.TaskServiceStub(channel)
        with pytest.raises(grpc.aio.AioRpcError):
            await stub.GetTask(pb2.GetTaskRequest(id="missing"))

    assert len(interceptor.calls) == 1
    assert interceptor.calls[0][0].endswith("/GetTask")
