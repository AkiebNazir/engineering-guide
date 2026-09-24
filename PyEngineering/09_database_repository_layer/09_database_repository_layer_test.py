"""Table-driven tests for ProductRepository against real SQLite (tmp_path)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SOLUTION_PATH = Path(__file__).parent / "09_database_repository_layer_solution.py"
_spec = importlib.util.spec_from_file_location(
    "database_repository_layer_solution", _SOLUTION_PATH
)
assert _spec is not None and _spec.loader is not None
_solution = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _solution
_spec.loader.exec_module(_solution)

ProductRepository = _solution.ProductRepository
ProductNotFoundError = _solution.ProductNotFoundError
DuplicateSkuError = _solution.DuplicateSkuError


@pytest.fixture
def repo(tmp_path: Path):
    with ProductRepository(tmp_path / "test.db") as r:
        yield r


def test_create_then_get_round_trips(repo) -> None:
    created = repo.create(sku="SKU-1", name="Widget", quantity=10, price_cents=999)
    fetched = repo.get(created.id)
    assert fetched == created
    assert fetched.sku == "SKU-1"
    assert fetched.name == "Widget"
    assert fetched.quantity == 10
    assert fetched.price_cents == 999


def test_create_duplicate_sku_raises_duplicate_sku_error(repo) -> None:
    repo.create(sku="SKU-1", name="Widget", quantity=10, price_cents=999)
    with pytest.raises(DuplicateSkuError):
        repo.create(sku="SKU-1", name="Other Widget", quantity=5, price_cents=500)


def test_get_missing_id_raises_not_found(repo) -> None:
    with pytest.raises(ProductNotFoundError):
        repo.get(9999)


def test_get_by_sku_found_and_missing(repo) -> None:
    created = repo.create(sku="SKU-1", name="Widget", quantity=10, price_cents=999)
    assert repo.get_by_sku("SKU-1") == created
    assert repo.get_by_sku("NOPE") is None


def test_list_all_returns_all_products_in_id_order(repo) -> None:
    a = repo.create(sku="A", name="Alpha", quantity=1, price_cents=100)
    b = repo.create(sku="B", name="Beta", quantity=2, price_cents=200)
    assert repo.list_all() == [a, b]


def test_list_all_empty(repo) -> None:
    assert repo.list_all() == []


def test_update_quantity_changes_value(repo) -> None:
    created = repo.create(sku="SKU-1", name="Widget", quantity=10, price_cents=999)
    repo.update_quantity(created.id, 50)
    assert repo.get(created.id).quantity == 50


def test_update_quantity_missing_id_raises_not_found(repo) -> None:
    with pytest.raises(ProductNotFoundError):
        repo.update_quantity(9999, 50)


def test_delete_removes_product(repo) -> None:
    created = repo.create(sku="SKU-1", name="Widget", quantity=10, price_cents=999)
    repo.delete(created.id)
    with pytest.raises(ProductNotFoundError):
        repo.get(created.id)


def test_delete_missing_id_raises_not_found(repo) -> None:
    with pytest.raises(ProductNotFoundError):
        repo.delete(9999)


def test_delete_twice_raises_not_found_second_time(repo) -> None:
    created = repo.create(sku="SKU-1", name="Widget", quantity=10, price_cents=999)
    repo.delete(created.id)
    with pytest.raises(ProductNotFoundError):
        repo.delete(created.id)


def test_search_by_name_finds_substring_matches(repo) -> None:
    repo.create(sku="A", name="Blue Widget", quantity=1, price_cents=100)
    repo.create(sku="B", name="Red Widget", quantity=1, price_cents=100)
    repo.create(sku="C", name="Gadget", quantity=1, price_cents=100)

    results = repo.search_by_name("Widget")
    assert {p.name for p in results} == {"Blue Widget", "Red Widget"}


def test_search_by_name_no_match_returns_empty(repo) -> None:
    repo.create(sku="A", name="Widget", quantity=1, price_cents=100)
    assert repo.search_by_name("Nonexistent") == []


def test_returned_objects_are_products_not_raw_rows(repo) -> None:
    created = repo.create(sku="SKU-1", name="Widget", quantity=10, price_cents=999)
    assert isinstance(created, _solution.Product)
    assert isinstance(repo.get(created.id), _solution.Product)
    for p in repo.list_all():
        assert isinstance(p, _solution.Product)


def test_injection_demo_unsafe_method_is_vulnerable(repo) -> None:
    repo.create(sku="A", name="Widget", quantity=1, price_cents=100)
    repo.create(sku="B", name="Gadget", quantity=1, price_cents=100)

    malicious = "' OR '1'='1"
    # The unsafe method's f-string-built SQL turns this into a tautology
    # that matches every row, proving the injection vulnerability is real.
    vulnerable_results = repo.search_by_name_unsafe(malicious)
    assert len(vulnerable_results) == 2


def test_injection_demo_safe_method_is_immune(repo) -> None:
    repo.create(sku="A", name="Widget", quantity=1, price_cents=100)
    repo.create(sku="B", name="Gadget", quantity=1, price_cents=100)

    malicious = "' OR '1'='1"
    # The parameterized method treats the exact same crafted string as
    # literal data to search for, not as SQL -- no rows contain it.
    safe_results = repo.search_by_name(malicious)
    assert safe_results == []


def test_reopening_same_db_path_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    with ProductRepository(db_path) as r1:
        r1.create(sku="A", name="Widget", quantity=1, price_cents=100)

    # Re-opening the same file must not raise on CREATE TABLE, and must see
    # the previously committed row.
    with ProductRepository(db_path) as r2:
        assert len(r2.list_all()) == 1


def test_connection_closed_after_context_manager_exit_even_on_exception(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "test.db"
    with pytest.raises(RuntimeError):
        with ProductRepository(db_path) as r:
            r.create(sku="A", name="Widget", quantity=1, price_cents=100)
            raise RuntimeError("boom")

    # Connection should be closed; further use raises sqlite3.ProgrammingError.
    import sqlite3

    with pytest.raises(sqlite3.ProgrammingError):
        r.list_all()
