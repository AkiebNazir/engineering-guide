"""
09 — Database Repository Layer
=================================

WHAT
----
Build a repository layer around stdlib `sqlite3` for an "inventory" domain:

    class Product(NamedTuple / dataclass): id, sku, name, quantity, price_cents
    class ProductRepository:
        create(sku, name, quantity, price_cents) -> Product
        get(product_id) -> Product | None
        get_by_sku(sku) -> Product | None
        list_all() -> list[Product]
        update_quantity(product_id, quantity) -> None
        delete(product_id) -> None
        search_by_name(query: str) -> list[Product]   # deliberately shows
                                                          the injection risk

WHY THIS MATTERS
----------------
`sqlite3` is the stdlib's only bundled database, but it is *not* toy-grade —
it's the actual embedded database inside SQLite-backed production systems
(mobile apps, browsers, and plenty of backend services for embedded/edge
deployments). The engineering concerns here — connection lifetime,
thread-safety, injection-safe querying, and row-to-object mapping — transfer
directly to any DB-API-2.0-shaped driver (psycopg2, mysqlclient) you'll use
against Postgres/MySQL in a real service. Problem 10 builds transactions and
concurrency control directly on top of this repository.

CONNECTION HANDLING
--------------------
`sqlite3.connect(path)` returns a connection that, by default, has
`check_same_thread=True`: using it from a thread other than the one that
created it raises `ProgrammingError`. There are two legitimate real-world
patterns:
  1. **One connection per thread** (e.g. a thread-local connection pool) —
     the most robust, avoids any cross-thread sharing entirely.
  2. **A single shared connection with `check_same_thread=False`** plus your
     own external locking — only safe if you fully understand SQLite's own
     locking model underneath (a whole connection-level lock per writer);
     this is what problem 10 explores deliberately, including the
     `database is locked` failure mode.
This module keeps it simple: `ProductRepository` owns exactly one
connection for its lifetime, used as a context manager so the connection is
always closed. Multi-connection/thread-safety concerns are pushed to
problem 10 where they're the actual subject.

THE INJECTION RISK (do this deliberately, once, to feel it)
--------------------------------------------------------------
`search_by_name` must be implemented TWICE for this exercise:
  - `search_by_name_unsafe(query)` — builds SQL via an f-string. Demonstrate
    (in the test file) that `query = "' OR '1'='1"` returns every row,
    proving the vulnerability exists, not just asserting it in prose.
  - `search_by_name(query)` — the real, shipped method — uses a parameterized
    query (`?` placeholders + a tuple of bound values) so the DB driver
    handles escaping; the same malicious `query` string returns zero rows
    (or only rows that literally contain that substring), because it's
    treated as *data*, never as *SQL*.

ROW MAPPING
------------
Configure the connection's `row_factory = sqlite3.Row` so query results
support both index and column-name access (`row["name"]`, `row[1]`), then
map each `sqlite3.Row` to a `Product` dataclass at the repository boundary —
callers of `ProductRepository` should never see a raw `sqlite3.Row` or
tuple; the DB library's return shape is an implementation detail that must
not leak past this layer.

SPEC
----
    @dataclass(frozen=True)
    class Product:
        id: int
        sku: str
        name: str
        quantity: int
        price_cents: int

    class ProductNotFoundError(Exception): ...
    class DuplicateSkuError(Exception): ...

    class ProductRepository:
        def __init__(self, db_path: str | Path) -> None: ...
            # opens the connection, creates the table if missing
        def close(self) -> None: ...
        def __enter__(self) -> "ProductRepository": ...
        def __exit__(self, *exc_info: object) -> None: ...

        def create(self, sku: str, name: str, quantity: int, price_cents: int) -> Product: ...
            # raises DuplicateSkuError on a UNIQUE constraint violation
        def get(self, product_id: int) -> Product: ...
            # raises ProductNotFoundError if missing
        def get_by_sku(self, sku: str) -> Product | None: ...
        def list_all(self) -> list[Product]: ...
        def update_quantity(self, product_id: int, quantity: int) -> None: ...
            # raises ProductNotFoundError if missing
        def delete(self, product_id: int) -> None: ...
            # raises ProductNotFoundError if missing
        def search_by_name(self, query: str) -> list[Product]: ...
            # parameterized LIKE query, injection-safe
        def search_by_name_unsafe(self, query: str) -> list[Product]: ...
            # deliberately vulnerable, for the injection-demo test only

ACCEPTANCE CRITERIA
--------------------
- `sqlite3.Row` (or any raw tuple/row) never crosses the repository's public
  API boundary — every public method returns `Product` (or `None`/raises).
- Creating a product with a duplicate `sku` raises `DuplicateSkuError`, not
  a raw `sqlite3.IntegrityError`.
- Every query with user-controllable input uses `?` placeholders — the test
  suite explicitly demonstrates `search_by_name_unsafe`'s vulnerability and
  `search_by_name`'s immunity to the identical crafted input.
- `get`/`update_quantity`/`delete` on a missing id raise
  `ProductNotFoundError`, not `None` or a silent no-op — silent no-ops on a
  missing row hide real bugs (e.g. deleting an already-deleted order twice
  should be loud, not silently "successful").
- The connection is always closed (context manager `__exit__`/explicit
  `close()`), even when an exception propagates out of a `with` block.
- Table creation is idempotent (`CREATE TABLE IF NOT EXISTS`) so opening the
  same `db_path` twice in a row never raises.
- Tests use `tmp_path / "test.db"` for a fresh file-backed SQLite DB per
  test (real SQLite, not mocked) — this exercises actual constraint
  enforcement, actual type affinity, actual locking, which a mock cannot.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


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
        """TODO:
        - open sqlite3.connect(str(db_path))
        - set connection.row_factory = sqlite3.Row
        - CREATE TABLE IF NOT EXISTS products (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              sku TEXT NOT NULL UNIQUE,
              name TEXT NOT NULL,
              quantity INTEGER NOT NULL,
              price_cents INTEGER NOT NULL
          )
        - commit the DDL
        """
        raise NotImplementedError

    def close(self) -> None:
        """TODO: close the connection."""
        raise NotImplementedError

    def __enter__(self) -> ProductRepository:
        raise NotImplementedError

    def __exit__(self, *exc_info: object) -> None:
        raise NotImplementedError

    def _row_to_product(self, row: sqlite3.Row) -> Product:
        """TODO: map a sqlite3.Row to a Product. Keep this the ONLY place
        that knows about column names/order."""
        raise NotImplementedError

    def create(self, sku: str, name: str, quantity: int, price_cents: int) -> Product:
        """TODO: INSERT with ? placeholders. Catch sqlite3.IntegrityError
        from the UNIQUE constraint and re-raise as DuplicateSkuError. Use
        cursor.lastrowid to fetch and return the created Product."""
        raise NotImplementedError

    def get(self, product_id: int) -> Product:
        """TODO: SELECT by id with a ? placeholder. Raise
        ProductNotFoundError if no row."""
        raise NotImplementedError

    def get_by_sku(self, sku: str) -> Product | None:
        """TODO: SELECT by sku with a ? placeholder. Return None if
        missing (this one's optional-by-design, unlike get())."""
        raise NotImplementedError

    def list_all(self) -> list[Product]:
        """TODO: SELECT all rows ordered by id."""
        raise NotImplementedError

    def update_quantity(self, product_id: int, quantity: int) -> None:
        """TODO: UPDATE with ? placeholders. Check cursor.rowcount == 0 to
        detect a missing id and raise ProductNotFoundError (rowcount is
        SQLite's way of telling you whether the WHERE clause matched
        anything, without a separate SELECT)."""
        raise NotImplementedError

    def delete(self, product_id: int) -> None:
        """TODO: DELETE with a ? placeholder; rowcount == 0 ->
        ProductNotFoundError."""
        raise NotImplementedError

    def search_by_name(self, query: str) -> list[Product]:
        """TODO: parameterized LIKE search: WHERE name LIKE ? with bound
        value f"%{query}%" passed as a *parameter*, never interpolated into
        the SQL string itself."""
        raise NotImplementedError

    def search_by_name_unsafe(self, query: str) -> list[Product]:
        """TODO (deliberately vulnerable, for the injection-demo test ONLY):
        build the SQL via an f-string/`.format()` with `query` spliced
        directly into the WHERE clause. Never write real code like this —
        this method exists solely so the test suite can prove the
        vulnerability exists and that search_by_name avoids it."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Hints
# ---------------------------------------------------------------------------
# - `cursor.execute("... WHERE id = ?", (product_id,))` — always pass a
#   tuple/sequence of parameters, even for a single value (the trailing
#   comma matters: `(x,)` is a 1-tuple, `(x)` is just `x`).
# - `cursor.lastrowid` after an INSERT gives you the AUTOINCREMENT id
#   without a second round-trip query.
# - `cursor.rowcount` after an UPDATE/DELETE tells you how many rows
#   matched — 0 means "no such id", the correct/cheap way to detect a
#   missing row without doing a SELECT first (which would also race).
# - Wrap the UNIQUE-constraint INSERT in `try: ... except sqlite3.
#   IntegrityError as exc: raise DuplicateSkuError(...) from exc`.
#
# Pitfalls
# --------
# - Forgetting `row_factory = sqlite3.Row` and returning raw index-only
#   tuples from internal helpers — fragile the moment column order changes.
# - Using `%s`-style or f-string interpolation for *any* user-controllable
#   value in SQL — sqlite3 uses `?` placeholders (not `%s`, that's the
#   psycopg2/MySQL convention) or named `:name` placeholders.
# - Not committing DDL/DML — sqlite3's default `isolation_level` starts an
#   implicit transaction on the first DML statement; forgetting `commit()`
#   silently loses writes when the connection closes uncleanly. (Problem 10
#   goes deep on isolation levels.)
# - Returning `None` instead of raising for a missing id on `delete`/
#   `update_quantity` — makes "nothing happened" indistinguishable from
#   "it worked", which hides real bugs like double-deletes.
#
# Stretch goals
# -------------
# - Add `bulk_create(items: list[tuple]) -> None` using
#   `cursor.executemany` and measure/comment on why it's faster than a
#   Python-level loop of individual `execute` calls.
# - Add an index on `sku` explicitly (even though UNIQUE already implies
#   one) and explain in a comment when you'd want a *non-unique* index vs.
#   relying on the implicit one.
# - Add `.pragma_foreign_keys(True)` scaffolding in preparation for a
#   second table (e.g. `orders` referencing `products`) in a later problem.
