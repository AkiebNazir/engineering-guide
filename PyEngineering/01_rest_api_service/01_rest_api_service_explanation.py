"""
01 · REST API service
=====================

WHAT WE'RE BUILDING
--------------------
```arch
%% caption: REST API Service Architecture
node req "Client Request" at 0,1 icon=client color=blue
node api "FastAPI Router\n(HTTP endpoints)" at 1,1 icon=api color=green
node valid "Pydantic\n(Validation)" at 2,1 icon=check color=amber
node domain "Domain Logic\n(CRUD ops)" at 3,1 icon=process color=slate
node db "In-Memory Store\n(with asyncio.Lock)" at 4,1 icon=memory color=red

req -> api
api -> valid : "parses JSON"
valid -> domain : "valid payload"
domain -> db : "safe mutation"
```

A small but production-shaped "Tasks" REST API on FastAPI: full CRUD over an
in-memory store, Pydantic request/response validation, a typed custom
exception hierarchy mapped to HTTP status codes, and a `lifespan` context
manager that models graceful startup/shutdown — the same shape you'd use to
open/close a DB pool, an HTTP client, or a message-bus connection in a real
service.

WHY THIS MATTERS IN REAL SYSTEMS
---------------------------------
Almost every backend Python service written today is "a FastAPI app with a
handful of routers." The parts that separate a toy example from something
you'd put in front of traffic are exactly the parts this problem drills:

- **Validation at the boundary.** Pydantic models mean malformed input never
  reaches your business logic — FastAPI returns a 422 automatically, with a
  machine-readable error body, before your code runs at all.
- **A typed error taxonomy.** Raising bare `HTTPException`s everywhere
  couples your domain logic to HTTP. A domain exception
  (`TaskNotFoundError`) raised deep in a store method, caught once by an
  `@app.exception_handler`, keeps the store layer HTTP-agnostic and testable
  on its own.
- **Concurrency-safety of shared state.** FastAPI runs each request handler
  as its own task on one event loop. An in-memory dict "store" is *not*
  automatically safe for interleaved read-modify-write sequences across
  concurrent requests unless you protect the critical section — this is the
  single most common bug when people hand-roll an in-memory store under
  async handlers.
- **Graceful shutdown.** A `lifespan` context manager is where you open
  resources once (not per-request) and guarantee they're closed even if the
  process receives SIGTERM (as it will, constantly, in a container
  orchestrator doing a rolling deploy).

CONCEPTS COVERED
-----------------
- FastAPI routing (`APIRouter`, path/query params, response models)
- Pydantic v2 models: validation, `model_config`, computed/default fields
- Custom exception hierarchy + `@app.exception_handler`
- `asyncio.Lock` to guard shared in-memory state under concurrent handlers
- `lifespan` context manager (the modern replacement for
  `@app.on_event("startup"/"shutdown")`)
- Graceful shutdown story: what `lifespan` guarantees vs. what
  `uvicorn`'s SIGTERM handling does at the process level (explained in
  comments; not exercised by the test suite, which drives the app via
  `TestClient`/`httpx.ASGITransport` rather than a live server+signals)

THE SPEC
--------
Build a `Task` resource:

    Task:
        id:         str   (server-generated UUID4 hex, read-only)
        title:      str   (1..200 chars, required)
        done:       bool  (default False)
        created_at: datetime (server-generated, UTC, read-only)

Endpoints (all under `/tasks`):

    POST   /tasks          create a task from {title, done?}      -> 201, Task
    GET    /tasks          list tasks, optional ?done=true/false  -> 200, list[Task]
    GET    /tasks/{id}     fetch one task                         -> 200, Task | 404
    PATCH  /tasks/{id}     partial update {title?, done?}         -> 200, Task | 404
    DELETE /tasks/{id}     delete a task                          -> 204 | 404

Validation rules:
    - `title` must be 1..200 characters after stripping whitespace; a
      title that is empty/whitespace-only is a 422, not a 400 — that's
      FastAPI/Pydantic's job, not yours to hand-code.
    - `PATCH` body fields are all optional; omitted fields are left
      unchanged. At least one field must be present, or respond 400 (this
      one *is* your job — Pydantic can't express "not all fields empty" for
      a partial-update body without extra work not worth it here, so it's a
      manual check in the handler).

Error mapping:
    - `TaskNotFoundError` (raised by the store)  -> 404 with
      `{"detail": "task <id> not found"}`
    - Pydantic validation failure                -> 422 (FastAPI's default,
      do not override it)

ACCEPTANCE CRITERIA
--------------------
1. `from NN_rest_api_service_solution import app` succeeds with no side
   effects (no server starts on import — `app` is just the ASGI app object).
2. All five endpoints behave per the table above, verified via
   `fastapi.testclient.TestClient` (which drives the ASGI app in-process,
   including running `lifespan` startup/shutdown — no real socket needed).
3. Two concurrent requests that both mutate the store (e.g. two concurrent
   `POST`s) never corrupt the store's internal dict — protected by an
   `asyncio.Lock`.
4. `lifespan` startup populates `app.state` with the store and logs a
   startup message; shutdown clears the store and logs a shutdown message —
   both observable in a test using `with TestClient(app) as client:`.
5. mypy-clean, black-formatted, ruff-clean.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

# NOTE (stub only): you'll need more imports once you fill in the TODOs
# below — at minimum `uuid` (task ids), `datetime.UTC`/`datetime.datetime`
# (timestamps), `pydantic.Field` (length-constrained fields), and from
# `fastapi`: `HTTPException`, `Query` (the `?done=` filter), `Request`
# (reaching `request.app.state.store`), and `status` (named status codes).
# They're listed here rather than pre-imported so this file imports cleanly
# as a stub without tripping an unused-import lint error.


# ---------------------------------------------------------------------------
# Domain exceptions — HTTP-agnostic. The store layer should never import
# `fastapi` or raise `HTTPException` directly; that keeps it testable and
# reusable outside of a web context (e.g. from a CLI or a background job).
# ---------------------------------------------------------------------------
class TaskError(Exception):
    """Base class for all task-store domain errors."""


class TaskNotFoundError(TaskError):
    """Raised when a task id does not exist in the store."""

    def __init__(self, task_id: str) -> None:
        # TODO: store `task_id` on the instance and call
        # super().__init__ with a human-readable message. Callers (the
        # exception handler) will read the message via str(exc).
        raise NotImplementedError("TODO: implement TaskNotFoundError.__init__")


# ---------------------------------------------------------------------------
# Pydantic models — the request/response contract.
# ---------------------------------------------------------------------------
class TaskCreate(BaseModel):
    """Body for POST /tasks."""

    # TODO: `title: str` constrained to 1..200 chars after stripping
    # whitespace (use pydantic.Field with min_length/max_length, and either
    # a field validator that strips, or str_strip_whitespace in model_config).
    # TODO: `done: bool = False`


class TaskUpdate(BaseModel):
    """Body for PATCH /tasks/{id}. Every field optional (partial update)."""

    # TODO: `title: str | None = None` (same length constraint when present)
    # TODO: `done: bool | None = None`


class TaskOut(BaseModel):
    """Response model. Server-generated fields are never client-writable."""

    # TODO: id: str, title: str, done: bool, created_at: datetime


# ---------------------------------------------------------------------------
# Store — an async-safe in-memory repository. In a real service this would
# be a thin wrapper over a DB connection pool; the concurrency-safety shape
# (guard the critical section, keep methods small) is identical either way.
# ---------------------------------------------------------------------------
class TaskStore:
    """In-memory task repository, safe under concurrent async handlers."""

    def __init__(self) -> None:
        # TODO: self._tasks: dict[str, TaskOut] = {}
        # TODO: self._lock = asyncio.Lock()
        raise NotImplementedError("TODO: implement TaskStore.__init__")

    async def create(self, data: TaskCreate) -> TaskOut:
        """Generate an id + created_at, store, and return the new task."""
        # TODO: build a TaskOut with uuid.uuid4().hex and datetime.now(UTC),
        # insert it under the lock, return it.
        raise NotImplementedError("TODO: implement TaskStore.create")

    async def list(self, *, done: bool | None = None) -> list[TaskOut]:
        """Return all tasks, optionally filtered by `done`."""
        raise NotImplementedError("TODO: implement TaskStore.list")

    async def get(self, task_id: str) -> TaskOut:
        """Return one task or raise TaskNotFoundError."""
        raise NotImplementedError("TODO: implement TaskStore.get")

    async def update(self, task_id: str, data: TaskUpdate) -> TaskOut:
        """Apply only the fields set on `data`; raise TaskNotFoundError if missing."""
        raise NotImplementedError("TODO: implement TaskStore.update")

    async def delete(self, task_id: str) -> None:
        """Remove a task or raise TaskNotFoundError."""
        raise NotImplementedError("TODO: implement TaskStore.delete")


# ---------------------------------------------------------------------------
# Lifespan — startup/shutdown. This is where you'd open a DB pool or an
# httpx.AsyncClient once per process and guarantee it's closed on shutdown,
# including on SIGTERM (uvicorn translates SIGTERM into a clean ASGI
# lifespan "shutdown" event, which is what makes this pattern "graceful").
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # TODO: create a TaskStore, assign it to app.state.store, log/print a
    # startup message, `yield`, then log/print a shutdown message and clear
    # the store. Everything before `yield` runs on startup; everything after
    # runs on shutdown — even if the process is asked to stop while requests
    # are in flight, ASGI servers drain in-flight requests before calling
    # the shutdown half of lifespan.
    raise NotImplementedError("TODO: implement lifespan")
    yield  # pragma: no cover - unreachable, keeps this a valid generator


def create_app() -> FastAPI:
    """Application factory — lets tests build fresh app instances."""
    app = FastAPI(lifespan=lifespan)

    # TODO: register routes on `app` (either directly or via an APIRouter),
    # and register an exception_handler for TaskNotFoundError that returns
    # a 404 JSONResponse. Access the store as request.app.state.store inside
    # handlers, never as a module-level global — that's what makes the app
    # testable with multiple independent instances.
    raise NotImplementedError("TODO: implement create_app routes")

    return app  # pragma: no cover - unreachable until TODO above is done


# NOTE (stub only): unlike the solution file, `app` is *not* built at import
# time here. `create_app()` still raises `NotImplementedError` until you fill
# in the TODOs above, and this file must import cleanly as-is — so calling
# it unconditionally at module scope would break that contract. Once your
# implementation is in place, either uncomment the line below or drive
# `create_app()` from your own `if __name__ == "__main__":` block:
#
#     app = create_app()


# ---------------------------------------------------------------------------
# HINTS
# -----
# - `request.app.state.store` is the idiomatic way to reach per-app state
#   from inside a route handler without module-level globals.
# - Prefer `response_model=TaskOut` (or a return-type annotation FastAPI can
#   introspect) over building JSONResponse by hand — you get automatic
#   OpenAPI docs and response validation for free.
# - `TestClient` from `fastapi.testclient` runs the full ASGI lifecycle
#   (including `lifespan`) when used as a context manager:
#   `with TestClient(app) as client: ...` — a bare `TestClient(app)` without
#   the `with` does NOT run lifespan in recent FastAPI/Starlette versions.
# - `HTTPException(status_code=..., detail=...)` is fine for hand-authored
#   4xx paths inside a handler (e.g. the "at least one field" 400 on
#   PATCH); reserve the domain exception hierarchy for errors raised deep
#   in the store, away from any `Request`/`HTTPException` import.
#
# COMMON PITFALLS
# ---------------
# - Forgetting the `asyncio.Lock` and doing "check-then-act" on the dict
#   (e.g. `if id in self._tasks: del self._tasks[id]`) — under concurrent
#   requests two coroutines can both pass the check before either acts.
#   The lock must wrap the *entire* read-modify-write sequence, not just
#   the mutation.
# - Returning `204 No Content` with a body — FastAPI/Starlette will reject
#   this; a 204 response must have an empty body (don't set
#   `response_model` on the DELETE handler).
# - Using a *module-level* `TaskStore()` instance instead of `app.state` —
#   this leaks state across test cases that each construct their own `app`
#   and makes lifespan startup/shutdown meaningless (there's nothing left
#   for it to create/destroy).
# - `datetime.utcnow()` is deprecated in modern Python — use
#   `datetime.now(UTC)` for a timezone-aware timestamp.
#
# STRETCH GOALS
# --------------
# - Add pagination (`?limit=&cursor=`) to `GET /tasks` instead of returning
#   the whole store.
# - Add an `ETag`/`If-Match` optimistic-concurrency check on `PATCH`.
# - Swap the in-memory dict for stdlib `sqlite3` (foreshadows problem 09)
#   without changing the router code — only `TaskStore`'s internals change,
#   which is the point of keeping HTTP and storage layered.
# - Add a real uvicorn entrypoint (`if __name__ == "__main__":
#   uvicorn.run(...)`) and manually send SIGTERM to a running process to
#   observe the lifespan shutdown log fire before the process exits.
