"""Pytest table-driven tests for `01_rest_api_service_solution`."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

_SOLUTION_PATH = Path(__file__).parent / "01_rest_api_service_solution.py"
_spec = importlib.util.spec_from_file_location(
    "rest_api_service_solution", _SOLUTION_PATH
)
assert _spec is not None and _spec.loader is not None
solution = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = solution
_spec.loader.exec_module(solution)


@pytest.fixture
def app() -> FastAPI:
    # Fresh app per test via the factory — no state leaks between tests.
    fastapi_app: FastAPI = solution.create_app()
    return fastapi_app


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


def test_import_has_no_side_effects() -> None:
    # `app` must be an ASGI app object, importable with no server started.
    assert solution.app is not None
    assert hasattr(solution.app, "router")


def test_lifespan_populates_and_clears_store(app: FastAPI, client: TestClient) -> None:
    # The fixture already entered `with TestClient(...) as client`, which
    # runs lifespan startup — the store must exist on app.state.
    assert isinstance(app.state.store, solution.TaskStore)


def test_create_task(client: TestClient) -> None:
    resp = client.post("/tasks", json={"title": "write tests"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "write tests"
    assert body["done"] is False
    assert "id" in body and "created_at" in body


@pytest.mark.parametrize(
    "payload",
    [
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 201},
        {},
    ],
)
def test_create_task_validation_422(client: TestClient, payload: dict) -> None:
    resp = client.post("/tasks", json=payload)
    assert resp.status_code == 422


def test_get_task_roundtrip(client: TestClient) -> None:
    created = client.post("/tasks", json={"title": "a"}).json()
    resp = client.get(f"/tasks/{created['id']}")
    assert resp.status_code == 200
    assert resp.json() == created


def test_get_missing_task_404(client: TestClient) -> None:
    resp = client.get("/tasks/does-not-exist")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]


def test_list_tasks_and_filter(client: TestClient) -> None:
    client.post("/tasks", json={"title": "a", "done": True})
    client.post("/tasks", json={"title": "b", "done": False})

    all_tasks = client.get("/tasks").json()
    assert len(all_tasks) == 2

    done_tasks = client.get("/tasks", params={"done": "true"}).json()
    assert len(done_tasks) == 1
    assert done_tasks[0]["title"] == "a"

    not_done = client.get("/tasks", params={"done": "false"}).json()
    assert len(not_done) == 1
    assert not_done[0]["title"] == "b"


def test_patch_partial_update(client: TestClient) -> None:
    created = client.post("/tasks", json={"title": "a"}).json()

    resp = client.patch(f"/tasks/{created['id']}", json={"done": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body["done"] is True
    assert body["title"] == "a"  # untouched field preserved

    resp2 = client.patch(f"/tasks/{created['id']}", json={"title": "b"})
    assert resp2.json()["title"] == "b"
    assert resp2.json()["done"] is True  # untouched field preserved


def test_patch_empty_body_400(client: TestClient) -> None:
    created = client.post("/tasks", json={"title": "a"}).json()
    resp = client.patch(f"/tasks/{created['id']}", json={})
    assert resp.status_code == 400


def test_patch_missing_task_404(client: TestClient) -> None:
    resp = client.patch("/tasks/does-not-exist", json={"done": True})
    assert resp.status_code == 404


def test_delete_task(client: TestClient) -> None:
    created = client.post("/tasks", json={"title": "a"}).json()

    resp = client.delete(f"/tasks/{created['id']}")
    assert resp.status_code == 204
    assert resp.content == b""

    # Now gone.
    assert client.get(f"/tasks/{created['id']}").status_code == 404


def test_delete_missing_task_404(client: TestClient) -> None:
    resp = client.delete("/tasks/does-not-exist")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_concurrent_creates_do_not_corrupt_store() -> None:
    """Two concurrent POSTs must never corrupt the store's internal dict —
    protected by the store's asyncio.Lock. Drives the ASGI app in-process
    over httpx.ASGITransport, without opening a real socket."""
    app = solution.create_app()

    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            n = 25
            responses = await asyncio.gather(
                *(ac.post("/tasks", json={"title": f"task-{i}"}) for i in range(n))
            )
            assert all(r.status_code == 201 for r in responses)
            ids = {r.json()["id"] for r in responses}
            # All ids distinct: no lost update / overwritten entry.
            assert len(ids) == n

            listed = await ac.get("/tasks")
            assert len(listed.json()) == n
