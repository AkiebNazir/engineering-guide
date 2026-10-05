"""
09 — Database Repository Layer — Reference Solution
======================================================

See `09_database_repository_layer_explanation.py` for the full spec and
rationale.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price_cents INTEGER NOT NULL
)
"""


@dataclass(frozen=True)
class Product:
    id: int
    sku: str
    name: str
    quantity: int
    price_cents: int


class ProductNotFoundError(Exception):
    """Raised when a lookup/update/delete targets a missing product id."""


class DuplicateSkuError(Exception):
    """Raised when creating a product whose sku already exists."""


class ProductRepository:
    """Repository over a single sqlite3 connection for the inventory domain."""

    def __init__(self, db_path: str | Path) -> None:
        self._conn = sqlite3.connect(str(db_path))
        # Row objects support both index and column-name access, so the
        # mapping helper below never depends on fragile positional column
        # order.
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(_CREATE_TABLE_SQL)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> ProductRepository:
        return self

    def __exit__(self, *exc_info: object) -> None:
        # Close unconditionally, whether the with-block exited normally or
        # via an exception -- a leaked connection holds a file handle (and,
        # on some platforms, a lock) for the life of the process.
        self.close()

    @staticmethod
    def _row_to_product(row: sqlite3.Row) -> Product:
        # The only place that knows sqlite3.Row's column names -- callers of
        # the public API never see a raw Row.
        return Product(
            id=row["id"],
            sku=row["sku"],
            name=row["name"],
            quantity=row["quantity"],
            price_cents=row["price_cents"],
        )

    def create(self, sku: str, name: str, quantity: int, price_cents: int) -> Product:
        try:
            cursor = self._conn.execute(
                "INSERT INTO products (sku, name, quantity, price_cents) "
                "VALUES (?, ?, ?, ?)",
                (sku, name, quantity, price_cents),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise DuplicateSkuError(f"sku already exists: {sku!r}") from exc

        # lastrowid avoids a second round trip to fetch the assigned id.
        assert cursor.lastrowid is not None
        return self.get(cursor.lastrowid)

    def get(self, product_id: int) -> Product:
        row = self._conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise ProductNotFoundError(f"no product with id={product_id}")
        return self._row_to_product(row)

    def get_by_sku(self, sku: str) -> Product | None:
        row = self._conn.execute(
            "SELECT * FROM products WHERE sku = ?", (sku,)
        ).fetchone()
        return None if row is None else self._row_to_product(row)

    def list_all(self) -> list[Product]:
        rows = self._conn.execute("SELECT * FROM products ORDER BY id").fetchall()
        return [self._row_to_product(row) for row in rows]

    def update_quantity(self, product_id: int, quantity: int) -> None:
        cursor = self._conn.execute(
            "UPDATE products SET quantity = ? WHERE id = ?",
            (quantity, product_id),
        )
        self._conn.commit()
        # rowcount is the cheap, race-free way to tell whether the WHERE
        # clause matched anything -- no separate SELECT needed.
        if cursor.rowcount == 0:
            raise ProductNotFoundError(f"no product with id={product_id}")

    def delete(self, product_id: int) -> None:
        cursor = self._conn.execute(
            "DELETE FROM products WHERE id = ?", (product_id,)
        )
        self._conn.commit()
        if cursor.rowcount == 0:
            raise ProductNotFoundError(f"no product with id={product_id}")

    def search_by_name(self, query: str) -> list[Product]:
        # The `%` wildcards are baked into the *bound parameter*, not the
        # SQL text -- `query` is treated purely as data by the driver, so a
        # crafted `query` containing quotes/SQL keywords cannot alter the
        # query's structure.
        rows = self._conn.execute(
            "SELECT * FROM products WHERE name LIKE ?", (f"%{query}%",)
        ).fetchall()
        return [self._row_to_product(row) for row in rows]

    def search_by_name_unsafe(self, query: str) -> list[Product]:
        # DELIBERATELY VULNERABLE -- exists only so the test suite can prove
        # the injection risk is real and that search_by_name is immune to
        # the identical input. Never splice untrusted input into SQL text
        # in real code.
        sql = f"SELECT * FROM products WHERE name LIKE '%{query}%'"
        rows = self._conn.execute(sql).fetchall()
        return [self._row_to_product(row) for row in rows]


# ---------------------------------------------------------------------------
# Best practices
# ---------------------------------------------------------------------------
# - `?` placeholders for every user-controllable value, no exceptions --
#   even values that "look safe" (e.g. an id derived from URL routing) can
#   carry attacker-controlled bytes over the network.
# - `cursor.rowcount` to detect "no matching row" on UPDATE/DELETE instead
#   of a separate existence-check SELECT, which would also be racy against
#   a concurrent delete between the check and the write.
# - Translate driver-level exceptions (`sqlite3.IntegrityError`) into
#   domain-level ones (`DuplicateSkuError`) at the repository boundary --
#   callers should depend on this module's exception types, not sqlite3's.
# - `row_factory = sqlite3.Row` + a single `_row_to_product` mapping
#   function keeps column-name knowledge in exactly one place.
#
# Alternative approaches
# -----------------------
# - Named placeholders (`:sku`, `:name`, ...) with a dict of parameters read
#   better than positional `?` once a query has more than ~4 bound values.
# - A connection pool (or one connection per thread) instead of a single
#   long-lived connection is the real-world default under real concurrent
#   load -- this problem intentionally keeps one connection to isolate the
#   repository-pattern and injection lessons; problem 10 is where
#   concurrency/locking becomes the actual subject.
# - For a larger schema, an ORM (SQLAlchemy) or a query builder trades some
#   of this explicitness for less boilerplate -- worth knowing what it's
#   doing under the hood, which is exactly what this exercise shows.
