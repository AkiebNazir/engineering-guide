"""
24 - gRPC service
====================

WHAT WE'RE BUILDING
--------------------
A `TaskService` gRPC server built on `grpc.aio` (the asyncio-native gRPC
API, preferred over the legacy thread-pool-based sync `grpc.server()` for
new asyncio services), covering the four RPC types worth knowing plus the
production concerns around them:

- `CreateTask` / `GetTask` - unary RPCs, and the error model
  (`grpc.StatusCode` + `context.abort`) via a bad request and a missing id.
- `ListTasks` - a server-streaming RPC, the streaming half of the exercise.
- `SlowOperation` - a deliberately slow, cooperatively-cancellable unary
  RPC used to demonstrate deadline propagation: it polls
  `context.cancelled()` instead of sleeping blindly, so a client deadline
  that fires mid-call stops server-side work instead of wasting it.
- `LoggingInterceptor` - a `grpc.aio.ServerInterceptor` that times every
  RPC (unary and streaming) without the servicer methods knowing it's
  there.

The contract lives in `task_service.proto`, compiled to real Python/gRPC
bindings with `grpc_tools.protoc` (exact command in that file's header
comment, repeated below). The test spins up the server in-process on an
ephemeral port and drives it through a real `grpc.aio` client - no
mocking of gRPC internals.

WHY THIS MATTERS IN REAL SYSTEMS
-----------------------------------
1. **`grpc.aio` over the sync API for new asyncio services.** The legacy
   `grpc.server()` runs handlers in a thread pool - fine for CPU-bound or
   blocking code, but it means a service already built on `asyncio` for
   its I/O (database, HTTP calls to other services) either pays a
   thread-hop per RPC or can't use `await` inside a handler at all.
   `grpc.aio.server()` runs handlers as real coroutines on the event
   loop, so a handler can `await` a database call or another RPC
   natively, exactly like the rest of the codebase.
2. **Interceptors are how you add a cross-cutting concern without
   touching every handler.** Logging, auth, metrics, tracing - anything
   that applies to *every* RPC belongs in an interceptor, not copy-pasted
   into each servicer method (the same argument as HTTP middleware in
   problem 02, adapted to gRPC's handler-wrapping model instead of an
   ASGI call chain).
3. **Streaming is a first-class gRPC feature, not bolted on.** A
   server-streaming RPC (`returns (stream Task)`) lets a server push
   results as they're ready instead of buffering the whole response -
   the same "don't build one giant string/list" discipline as problem
   23's JSON Lines streaming, but at the RPC layer.
4. **Deadlines propagate, and ignoring them wastes real resources.** A
   gRPC client sets a deadline (absolute wall-clock time); the server
   sees it as a countdown via `context.cancelled()`/the call becoming
   done. A handler that ignores this and keeps working past a blown
   deadline burns CPU/DB connections computing an answer nobody will
   receive - `SlowOperation` here demonstrates checking cooperatively
   instead.
5. **The error model is part of the API contract.** Returning
   `grpc.StatusCode.NOT_FOUND` (not `INTERNAL` for everything, not a
   `200`-shaped "error" message in the response body) lets a client's
   generic retry/error-handling logic work correctly - `INVALID_ARGUMENT`
   is not retried the same way `UNAVAILABLE` is, and conflating them
   breaks that machinery. `context.abort(code, details)` is the
   `grpc.aio` way to set both in one call and stop handler execution
   immediately (it raises internally, cooperative with `async def`
   handlers).

CONCEPTS COVERED
------------------
- A hand-written `.proto` compiled with `grpc_tools.protoc` into
  `_pb2.py` (messages) / `_pb2_grpc.py` (servicer base class + stub)
- `grpc.aio.server()`, `add_insecure_port`, `server.start()`/`.stop()`
- Unary-unary and unary-stream (server-streaming) RPC handlers as
  `async def` methods
- `grpc.aio.ServerInterceptor.intercept_service` wrapping both unary and
  streaming handlers generically
- `context.abort(grpc.StatusCode.X, "details")` for the error model
- Deadline propagation: a client-side `timeout=` on the call and
  server-side cooperative cancellation via `context.cancelled()`
- Driving the server through a real `grpc.aio.insecure_channel` client
  in-process, in tests

THE SPEC
---------
See `task_service.proto` for the exact message/service shapes. Server-side:

`class TaskServicer(task_service_pb2_grpc.TaskServiceServicer)`
    In-memory task store (`dict[str, Task]`), guarded by nothing extra -
    a single `grpc.aio` server runs its handlers on one event loop, so a
    plain dict mutated only via `await`-free sections between awaits is
    safe without a lock (no other coroutine can interleave mid-dict-write
    since dict mutation itself doesn't await).

    `CreateTask(request, context) -> Task`
        `context.abort(grpc.StatusCode.INVALID_ARGUMENT, ...)` if
        `request.title` is blank/whitespace-only. Otherwise generate a
        new id (`uuid.uuid4().hex` is fine), store, and return the `Task`.

    `GetTask(request, context) -> Task`
        `context.abort(grpc.StatusCode.NOT_FOUND, ...)` if `request.id`
        isn't in the store. Otherwise return the stored `Task`.

    `ListTasks(request, context) -> AsyncIterator[Task]`
        `async def` **generator** (server-streaming): yield each stored
        `Task` one at a time.

    `SlowOperation(request, context) -> SlowResponse`
        Poll in small increments (e.g. 50ms) up to `request.delay_seconds`
        total, checking `context.cancelled()` each iteration and
        returning early (an empty `SlowResponse`) if the client's deadline
        has fired. Otherwise return `SlowResponse(message=...)` once the
        full delay has elapsed.

`class LoggingInterceptor(grpc.aio.ServerInterceptor)`
    `calls: list[tuple[str, float]]` - `(method_name, duration_seconds)`
    appended after each RPC completes, for both unary-unary and
    unary-stream handlers (this service has no client-streaming or
    bidi-streaming methods, so those handler kinds can pass through
    unwrapped).

`async def serve(port: int = 0) -> tuple[grpc.aio.Server, int, TaskServicer, LoggingInterceptor]`
    Build a `grpc.aio.server()` with `LoggingInterceptor` installed, add
    `TaskServicer` to it, bind `add_insecure_port(f"[::]:{port}")` (port 0
    picks a free ephemeral port - the actual bound port is read back from
    the return value of `add_insecure_port`), `await server.start()`, and
    return the server, the real bound port, the servicer, and the
    interceptor (so tests/callers can inspect state and shut it down).

ACCEPTANCE CRITERIA
---------------------
1. `CreateTask` then `GetTask` with the returned id round-trips the same
   `Task` through a real client.
2. `CreateTask` with a blank title raises a client-side
   `grpc.aio.AioRpcError` with `code() == grpc.StatusCode.INVALID_ARGUMENT`.
3. `GetTask` with an unknown id raises `grpc.aio.AioRpcError` with
   `code() == grpc.StatusCode.NOT_FOUND`.
4. `ListTasks` streams back every previously created task (order
   irrelevant), consumed via `async for` on the client stub call.
5. `SlowOperation` called with a client `timeout` shorter than
   `delay_seconds` raises `grpc.aio.AioRpcError` with
   `code() == grpc.StatusCode.DEADLINE_EXCEEDED`, and the server-side
   `SlowOperation` handler observes `context.cancelled()` and returns
   early rather than sleeping the full duration (demonstrated by the
   handler completing in well under `delay_seconds`).
6. `SlowOperation` called with a sufficient timeout completes normally
   and returns the expected message.
7. After making several RPCs (a mix of unary and the streaming call),
   `LoggingInterceptor.calls` has one entry per RPC with a plausible
   non-negative duration and the correct method path for each.
8. The server is actually run in-process via `grpc.aio` and driven
   through a real client for every test above - no mocking of gRPC
   internals.
9. mypy-clean, black-formatted, ruff-clean (generated `_pb2*.py` files
   excepted, per their own header comments).

Regenerate the bindings any time `task_service.proto` changes, from the
`PyEngineering/` directory:

    .venv/bin/python -m grpc_tools.protoc \\
        -I24_grpc_service \\
        --python_out=24_grpc_service \\
        --grpc_python_out=24_grpc_service \\
        --pyi_out=24_grpc_service \\
        24_grpc_service/task_service.proto
"""

from __future__ import annotations

import asyncio  # noqa: F401 - used once you implement SlowOperation/serve
import uuid  # noqa: F401 - used once you implement CreateTask
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

import grpc  # type: ignore[import-untyped]

# Generated by `python -m grpc_tools.protoc` from task_service.proto (see
# that file's header comment, and the module docstring above, for the
# exact command). mypy has no stub/type information for generated
# protobuf/gRPC modules, so the ignore is scoped to these two imports.
import task_service_pb2 as pb2  # type: ignore[import-untyped]
import task_service_pb2_grpc as pb2_grpc  # type: ignore[import-untyped]


# ---------------------------------------------------------------------------
# Server: TaskServicer.
# ---------------------------------------------------------------------------
class TaskServicer(pb2_grpc.TaskServiceServicer):
    """In-memory implementation of `TaskService`."""

    def __init__(self) -> None:
        self._tasks: dict[str, pb2.Task] = {}

    async def CreateTask(
        self, request: pb2.CreateTaskRequest, context: grpc.aio.ServicerContext
    ) -> pb2.Task:
        """TODO:
        1. If `request.title.strip()` is empty, `context.abort(
           grpc.StatusCode.INVALID_ARGUMENT, "title must not be blank")`.
           `context.abort` raises internally - no `return` needed after it
           (mypy/runtime both treat it as NoReturn-shaped in practice, but
           the generated stub types it loosely - it's fine to fall through
           a `raise` if you prefer being explicit).
        2. Otherwise build `task = pb2.Task(id=uuid.uuid4().hex,
           title=request.title, done=False)`, store it in `self._tasks`,
           and return it.
        """
        raise NotImplementedError("TODO: implement TaskServicer.CreateTask")

    async def GetTask(
        self, request: pb2.GetTaskRequest, context: grpc.aio.ServicerContext
    ) -> pb2.Task:
        """TODO: return `self._tasks[request.id]` if present, else
        `context.abort(grpc.StatusCode.NOT_FOUND, f"task {request.id!r}
        not found")`.
        """
        raise NotImplementedError("TODO: implement TaskServicer.GetTask")

    async def ListTasks(
        self, request: pb2.ListTasksRequest, context: grpc.aio.ServicerContext
    ) -> AsyncIterator[pb2.Task]:
        """TODO: `async def` generator - `for task in
        self._tasks.values(): yield task`. (Server-streaming handlers in
        `grpc.aio` are plain async generators - no manual `context.write`
        call needed.)
        """
        raise NotImplementedError("TODO: implement TaskServicer.ListTasks")
        yield  # pragma: no cover - makes this an async generator for mypy

    async def SlowOperation(
        self, request: pb2.SlowRequest, context: grpc.aio.ServicerContext
    ) -> pb2.SlowResponse:
        """TODO: poll in small increments (e.g. `step = 0.05`) up to
        `request.delay_seconds` total. Each iteration: if
        `context.cancelled()` is true, return `pb2.SlowResponse()`
        immediately (the client's deadline fired or it cancelled - do not
        keep sleeping). Otherwise `await asyncio.sleep(step)` and
        accumulate elapsed time. Once elapsed >= delay_seconds, return
        `pb2.SlowResponse(message=f"slept {request.delay_seconds}s")`.
        """
        raise NotImplementedError("TODO: implement TaskServicer.SlowOperation")


# ---------------------------------------------------------------------------
# Interceptor: times every RPC without the servicer knowing.
# ---------------------------------------------------------------------------
class LoggingInterceptor(grpc.aio.ServerInterceptor):
    """Records `(method_path, duration_seconds)` for every completed RPC.

    TODO: `__init__`: `self.calls: list[tuple[str, float]] = []`.

    TODO: `async def intercept_service(self, continuation, handler_call_details)`:
    1. `handler = await continuation(handler_call_details)`.
    2. If `handler is None`, return it unchanged (method not found -
       let the framework produce its own UNIMPLEMENTED error).
    3. `method = handler_call_details.method`.
    4. If `handler.unary_unary is not None`: wrap it in an `async def`
       that times `await inner(request, context)`, appends
       `(method, duration)` to `self.calls` in a `finally` block (so a
       raised/aborted call is still timed), and returns the awaited
       result. Rebuild the handler via
       `grpc.unary_unary_rpc_method_handler(wrapped,
       request_deserializer=handler.request_deserializer,
       response_serializer=handler.response_serializer)`.
    5. Else if `handler.unary_stream is not None`: same idea, but the
       wrapper is an `async def` **generator** that does
       `async for response in inner(request, context): yield response`
       inside a `try`, with the timing/append in `finally`. Rebuild via
       `grpc.unary_stream_rpc_method_handler(...)`.
    6. Else (this service has no client-streaming/bidi methods) return
       `handler` unchanged.
    """

    def __init__(self) -> None:
        raise NotImplementedError("TODO: implement LoggingInterceptor.__init__")

    async def intercept_service(
        self,
        continuation: Callable[[Any], Awaitable[Any]],
        handler_call_details: Any,
    ) -> Any:
        raise NotImplementedError(
            "TODO: implement LoggingInterceptor.intercept_service"
        )


# ---------------------------------------------------------------------------
# Server bootstrap.
# ---------------------------------------------------------------------------
async def serve(
    port: int = 0,
) -> tuple[grpc.aio.Server, int, TaskServicer, LoggingInterceptor]:
    """TODO:
    1. `interceptor = LoggingInterceptor()`.
    2. `server = grpc.aio.server(interceptors=[interceptor])`.
    3. `servicer = TaskServicer()`.
    4. `pb2_grpc.add_TaskServiceServicer_to_server(servicer, server)`.
    5. `bound_port = server.add_insecure_port(f"[::]:{port}")` - this
       returns the *actual* port bound (relevant when `port=0`).
    6. `await server.start()`.
    7. Return `(server, bound_port, servicer, interceptor)`.
    """
    raise NotImplementedError("TODO: implement serve")


# ---------------------------------------------------------------------------
# HINTS
# -----
# - `grpc.aio.server()` returns a server whose `start()`/`stop()`/
#   `wait_for_termination()` are coroutines - always `await` them.
#   `server.stop(grace_period_seconds)` (also a coroutine to await)
#   requests a graceful shutdown; pass `None` for immediate.
# - A server-streaming handler in `grpc.aio` is just an `async def` that
#   contains `yield` - no separate "streaming call" API to learn beyond
#   that.
# - `context.abort(...)` raises `grpc.aio.AbortError` internally in
#   `grpc.aio` handlers - you don't need (and shouldn't add) a `return`
#   after calling it, execution doesn't continue past it.
# - `context.cancelled()` becomes `True` once the RPC is done for any
#   reason from the server's point of view (client cancelled, deadline
#   exceeded) - checking it periodically inside a long-running handler is
#   the standard cooperative-cancellation pattern; there's no way to
#   forcibly interrupt an `await`-free CPU-bound loop from outside.
# - On the client side, `stub.SlowOperation(request, timeout=0.2)` sets a
#   deadline 0.2s from now; `grpc.aio.AioRpcError.code()` and `.details()`
#   surface what the server (or the channel itself, for a deadline with
#   no server response at all) reported.
#
# COMMON PITFALLS
# ----------------
# - Using the legacy `grpc.server()`/`grpc.insecure_channel` (sync,
#   thread-pool-based) instead of `grpc.aio.server()`/
#   `grpc.aio.insecure_channel` - they're a different API surface (no
#   `await`) and mixing them with `async def` handlers doesn't work.
# - Forgetting the `finally` in the interceptor wrappers - if a handler
#   raises/aborts and the timing code isn't in a `finally`, failed RPCs
#   silently vanish from `self.calls`, which is exactly the case you most
#   want logged.
# - Writing `ListTasks` as `async def ... -> AsyncIterator[Task]:
#   return [...]` - a server-streaming handler must actually `yield`
#   items; returning a list/iterable from a non-generator `async def`
#   does not stream anything to gRPC.
# - Sleeping the *entire* `delay_seconds` in one `await asyncio.sleep(...)`
#   call in `SlowOperation` - that can't observe cancellation partway
#   through, defeating the deadline-propagation demonstration entirely.
# - Forgetting `await server.stop(...)` (or `None`) at the end of a test/
#   script - an un-stopped `grpc.aio` server keeps its port bound and can
#   leave the event loop with pending tasks on interpreter shutdown.
#
# STRETCH GOALS
# --------------
# - Add an `AuthInterceptor` that inspects
#   `handler_call_details.invocation_metadata` for an `"authorization"`
#   entry and, if missing, returns a handler that immediately
#   `context.abort(grpc.StatusCode.UNAUTHENTICATED, ...)`s instead of
#   calling through - install both interceptors on the server
#   (`interceptors=[AuthInterceptor(), LoggingInterceptor()]`) and note
#   the ordering matters (auth should run before the timed call, not
#   after).
# - Add a client-side interceptor (`grpc.aio.UnaryUnaryClientInterceptor`)
#   that injects a fixed `authorization` metadata entry into every call,
#   to pair with the stretch goal above.
# - Add a bidirectional-streaming RPC (`stream Task returns (stream
#   Task)`) and extend `LoggingInterceptor` to handle
#   `handler.stream_stream` too, for full RPC-kind coverage.
