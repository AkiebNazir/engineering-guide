"""
01 · REST API service — SOLUTION
=================================

Complete, idiomatic reference implementation of the "Tasks" REST API
described in `01_rest_api_service_explanation.py`. Read that file first for
the full spec, rationale, and acceptance criteria; this file assumes that
context and focuses its comments on *how* each piece is built and why this
shape wins over the obvious alternatives.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("tasks")


# ---------------------------------------------------------------------------
# Domain exceptions — HTTP-agnostic on purpose. `TaskStore` never imports
# `fastapi`; it raises plain Python exceptions that a thin adapter layer
# (the `@app.exception_handler` below) translates to HTTP. This means the
# store can be unit-tested, reused from a CLI, or swapped onto a real DB in
# problem 09 without touching a single HTTP concept.
# ---------------------------------------------------------------------------
class TaskError(Exception):
    """Base class for all task-store domain errors."""


class TaskNotFoundError(TaskError):
    """Raised when a task id does not exist in the store."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"task {task_id} not found")


# ---------------------------------------------------------------------------
# Pydantic models — the request/response contract at the API boundary.
# ---------------------------------------------------------------------------
class TaskCreate(BaseModel):
    """Body for POST /tasks."""

    # `min_length=1` alone would accept " " (whitespace-only). Stripping in
    # a field_validator (mode="after" is not needed here — the default
    # "after" validator runs after Pydantic's own length check, but we want
    # to strip *before* the length check applies to leading/trailing
    # whitespace) via `str_strip_whitespace` in model_config is the cleanest
    # fix: it strips first, then min_length/max_length apply to the
    # stripped result, so " " fails min_length=1 automatically.
    model_config = {"str_strip_whitespace": True}

    title: str = Field(min_length=1, max_length=200)
    done: bool = False


class TaskUpdate(BaseModel):
    """Body for PATCH /tasks/{id}. Every field optional (partial update)."""

    model_config = {"str_strip_whitespace": True}

    title: str | None = Field(default=None, min_length=1, max_length=200)
    done: bool | None = None

    @field_validator("title")
    @classmethod
    def _reject_blank_after_strip(cls, v: str | None) -> str | None:
        # str_strip_whitespace already strips before min_length runs, so a
        # value that arrives here as "" only happens if the *stripped*
        # string was empty — Pydantic's own min_length=1 already rejects
        # that with a 422. This validator is kept deliberately trivial
        # (identity) to document that the stripping/validation order was
        # considered, not accidental.
        return v


class TaskOut(BaseModel):
    """Response model. Server-generated fields are never client-writable."""

    id: str
    title: str
    done: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Store — an async-safe in-memory repository. A single `asyncio.Lock` guards
# every read-modify-write sequence. This is coarser-grained than it needs to
# be (a single global lock serializes all store access, even unrelated
# reads), but it is *correct* and simple — the right starting point before
# reaching for per-key locking or `asyncio.Queue`-based single-flight
# (problem 14 territory). Correctness first, then measure before optimizing.
# ---------------------------------------------------------------------------
class TaskStore:
    """In-memory task repository, safe under concurrent async handlers."""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskOut] = {}
        self._lock = asyncio.Lock()

    async def create(self, data: TaskCreate) -> TaskOut:
        """Generate an id + created_at, store, and return the new task."""
        task = TaskOut(
            id=uuid.uuid4().hex,
            title=data.title,
            done=data.done,
            created_at=datetime.now(UTC),
        )
        async with self._lock:
            self._tasks[task.id] = task
        return task

    async def list(self, *, done: bool | None = None) -> list[TaskOut]:
        """Return all tasks, optionally filtered by `done`."""
        async with self._lock:
            # Snapshot under the lock (list() of .values()) so the caller
            # never sees a dict that another coroutine mutates mid-iteration
            # once the lock is released.
            tasks = list(self._tasks.values())
        if done is None:
            return tasks
        return [t for t in tasks if t.done == done]

    async def get(self, task_id: str) -> TaskOut:
        """Return one task or raise TaskNotFoundError."""
        async with self._lock:
            task = self._tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    async def update(self, task_id: str, data: TaskUpdate) -> TaskOut:
        """Apply only the fields set on `data`; raise TaskNotFoundError if missing."""
        async with self._lock:
            existing = self._tasks.get(task_id)
            if existing is None:
                raise TaskNotFoundError(task_id)
            # model_dump(exclude_unset=True) captures only fields the
            # client actually sent — critical for PATCH semantics. Without
            # exclude_unset, an omitted `done` would come through as its
            # Pydantic default (None) and *overwrite* the field with the
            # merge below would still be fine here since we skip None
            # explicitly, but exclude_unset is the robust, general pattern
            # (it also covers the case where a field's "unset" default is
            # not None).
            updates = data.model_dump(exclude_unset=True)
            merged = existing.model_copy(update=updates)
            self._tasks[task_id] = merged
            return merged

    async def delete(self, task_id: str) -> None:
        """Remove a task or raise TaskNotFoundError."""
        async with self._lock:
            if task_id not in self._tasks:
                raise TaskNotFoundError(task_id)
            del self._tasks[task_id]

    def clear(self) -> None:
        """Synchronous — only ever called from lifespan shutdown, where no
        concurrent request handlers are still running."""
        self._tasks.clear()


# ---------------------------------------------------------------------------
# Lifespan — startup/shutdown. `app.state` (not a module-level global) holds
# the store, so each `create_app()` call gets its own isolated instance —
# essential for running multiple tests in the same process without state
# leaking between them.
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.store = TaskStore()
    logger.info("tasks service starting up")
    try:
        yield
    finally:
        # The `finally` guarantees this runs even if something upstream
        # raises during the request-handling phase (which happens *inside*
        # the `yield`, conceptually) or if shutdown itself is interrupted —
        # in practice ASGI servers drain in-flight requests before tearing
        # lifespan down, but defensive cleanup costs nothing here.
        logger.info("tasks service shutting down")
        app.state.store.clear()


def create_app() -> FastAPI:
    """Application factory — lets tests build fresh, isolated app instances."""
    app = FastAPI(lifespan=lifespan)

    def get_store(request: Request) -> TaskStore:
        # A tiny accessor rather than sprinkling `request.app.state.store`
        # everywhere — one place to change if the state's shape ever moves
        # (e.g. behind a FastAPI `Depends`-based DI container later).
        store: TaskStore = request.app.state.store
        return store

    @app.exception_handler(TaskNotFoundError)
    async def _handle_not_found(
        request: Request, exc: TaskNotFoundError
    ) -> JSONResponse:
        # Registered once, here, rather than a try/except in every handler.
        # This is the payoff of keeping TaskStore HTTP-agnostic: one
        # adapter function bridges the entire domain-exception hierarchy to
        # HTTP status codes.
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @app.post("/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
    async def create_task(body: TaskCreate, request: Request) -> TaskOut:
        return await get_store(request).create(body)

    @app.get("/tasks", response_model=list[TaskOut])
    async def list_tasks(
        request: Request, done: bool | None = Query(default=None)
    ) -> list[TaskOut]:
        return await get_store(request).list(done=done)

    @app.get("/tasks/{task_id}", response_model=TaskOut)
    async def get_task(task_id: str, request: Request) -> TaskOut:
        return await get_store(request).get(task_id)

    @app.patch("/tasks/{task_id}", response_model=TaskOut)
    async def update_task(task_id: str, body: TaskUpdate, request: Request) -> TaskOut:
        # Pydantic can't express "at least one field present" for an
        # all-optional model without a custom model_validator that would
        # add more ceremony than this one-line manual check is worth.
        if not body.model_fields_set:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="at least one field must be provided",
            )
        return await get_store(request).update(task_id, body)

    @app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_task(task_id: str, request: Request) -> None:
        # No response_model / return value: a 204 response must carry an
        # empty body. FastAPI honors a `None` return with no response_model
        # by sending an empty body for this status code.
        await get_store(request).delete(task_id)

    return app


# Module-level `app` — importable with zero side effects (no server starts;
# `create_app()` only builds the ASGI app object and registers routes).
app = create_app()


# ---------------------------------------------------------------------------
# Best practices demonstrated here
# ---------------------------------------------------------------------------
# - Keep domain exceptions free of any web-framework import; translate them
#   to HTTP in exactly one place (`@app.exception_handler`).
# - Use an application factory (`create_app()`) instead of a single
#   module-level `app` built directly from global state — it's what makes
#   the app trivially testable with N independent instances.
# - Guard every read-modify-write sequence on shared mutable state with a
#   lock that wraps the *entire* sequence, not just the final mutation.
# - `model_dump(exclude_unset=True)` + `model_copy(update=...)` is the
#   idiomatic Pydantic v2 pattern for PATCH semantics — it distinguishes
#   "field omitted" from "field explicitly set to its default".
# - `response_model=` (rather than returning framework-specific response
#   objects) keeps handlers focused on domain types and gets automatic
#   OpenAPI schema + response validation for free.
#
# Alternative approaches considered
# ----------------------------------
# - A per-task `asyncio.Lock` (sharded locking) instead of one store-wide
#   lock: better concurrency under contention, but this store's critical
#   sections are so cheap (dict operations, no I/O) that the coarse lock
#   never becomes a bottleneck in practice — added complexity would not be
#   earned here. Worth revisiting once operations do I/O (problem 09+).
# - Raising `HTTPException` directly from `TaskStore` instead of a domain
#   exception hierarchy: simpler for this toy example, but it couples the
#   store to `fastapi` and makes it untestable without a running app —
#   exactly the anti-pattern this problem is designed to steer away from.
#
# Testing notes
# -------------
# - `with TestClient(app) as client:` is required (not a bare
#   `TestClient(app)`) to exercise `lifespan` — this is what makes the
#   startup/shutdown logging and `app.state.store` assignment observable in
#   tests.
# - Concurrency safety is tested by firing N concurrent POSTs via
#   `asyncio.gather` against `httpx.AsyncClient(transport=ASGITransport(...))`
#   and asserting the store ends up with exactly N distinct ids — a bug in
#   the locking would manifest as duplicate ids or a `RuntimeError` from
#   mutating a dict during iteration.
#
# Failure-mode notes
# -------------------
# - A `PATCH` with an empty body (`{}`) is valid JSON and passes Pydantic
#   validation (all fields optional) — that's exactly why the manual
#   `model_fields_set` check exists; without it, an empty PATCH would
#   silently no-op with a 200 instead of clearly telling the caller nothing
#   was provided.
# - `uuid4().hex` collisions are cryptographically negligible (2^122
#   possibility space) and are not defended against here; a real system
#   backed by a DB would still enforce uniqueness via a primary key
#   constraint as defense in depth.
