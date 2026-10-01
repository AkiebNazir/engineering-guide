"""
10 — Transactions & Concurrency Control — Reference Solution
================================================================

See `10_transactions_concurrency_control_explanation.py` for the full spec
and rationale.
"""

from __future__ import annotations

import random
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price_cents INTEGER NOT NULL,
    version INTEGER NOT NULL DEFAULT 1
)
"""

_LOCK_MESSAGE = "database is locked"


@dataclass(frozen=True)
class Product:
    id: int
    sku: str
    name: str
    quantity: int
    price_cents: int
    version: int


class ProductNotFoundError(Exception):
    """Raised when a lookup/update/delete targets a missing product id."""


class InsufficientStockError(Exception):
    """Raised when a transfer or delta-update would drive quantity negative."""


class ConcurrentUpdateError(Exception):
    """Raised when an optimistic UPDATE's expected_version no longer matches."""


class InventoryStore:
    """Transactional, optimistically-locked inventory store (builds on 09)."""

    def __init__(self, db_path: str | Path) -> None:
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        # busy_timeout raises the threshold at which SQLite's own C layer
        # gives up waiting for a lock and surfaces "database is locked" --
        # it buys short lock waits time to resolve on their own, but does
        # NOT replace the application-level retry loop below (a sustained
        # writer holding the lock longer than this timeout still needs to
        # be handled by update_quantity_with_retry).
        self._conn.execute("PRAGMA busy_timeout = 2000")
        self._conn.execute(_CREATE_TABLE_SQL)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> InventoryStore:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    @staticmethod
    def _row_to_product(row: sqlite3.Row) -> Product:
        return Product(
            id=row["id"],
            sku=row["sku"],
            name=row["name"],
            quantity=row["quantity"],
            price_cents=row["price_cents"],
            version=row["version"],
        )

    def create_product(
        self, sku: str, name: str, quantity: int, price_cents: int
    ) -> Product:
        cursor = self._conn.execute(
            "INSERT INTO products (sku, name, quantity, price_cents, version) "
            "VALUES (?, ?, ?, ?, 1)",
            (sku, name, quantity, price_cents),
        )
        self._conn.commit()
        assert cursor.lastrowid is not None
        return self.get(cursor.lastrowid)

    def get(self, product_id: int) -> Product:
        row = self._conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise ProductNotFoundError(f"no product with id={product_id}")
        return self._row_to_product(row)

    def transfer_stock(self, from_id: int, to_id: int, amount: int) -> None:
        # BEGIN IMMEDIATE takes SQLite's RESERVED write lock *before* any
        # reads happen. With the (default) DEFERRED level, two concurrent
        # transfers out of the same account could both read stale stock
        # before either write-locks the DB, both pass the sufficiency
        # check, and both proceed to write -- exactly the race this
        # exercise exists to close.
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            from_row = self._conn.execute(
                "SELECT quantity FROM products WHERE id = ?", (from_id,)
            ).fetchone()
            if from_row is None:
                raise ProductNotFoundError(f"no product with id={from_id}")
            to_row = self._conn.execute(
                "SELECT quantity FROM products WHERE id = ?", (to_id,)
            ).fetchone()
            if to_row is None:
                raise ProductNotFoundError(f"no product with id={to_id}")

            if from_row["quantity"] < amount:
                raise InsufficientStockError(
                    f"product {from_id} has {from_row['quantity']} units, "
                    f"cannot transfer {amount}"
                )

            self._conn.execute(
                "UPDATE products SET quantity = quantity - ?, "
                "version = version + 1 WHERE id = ?",
                (amount, from_id),
            )
            self._conn.execute(
                "UPDATE products SET quantity = quantity + ?, "
                "version = version + 1 WHERE id = ?",
                (amount, to_id),
            )
        except BaseException:
            self._conn.rollback()
            raise
        else:
            self._conn.commit()

    def update_quantity_optimistic(
        self, product_id: int, expected_version: int, new_quantity: int
    ) -> Product:
        cursor = self._conn.execute(
            "UPDATE products SET quantity = ?, version = version + 1 "
            "WHERE id = ? AND version = ?",
            (new_quantity, product_id, expected_version),
        )
        self._conn.commit()
        if cursor.rowcount == 0:
            # rowcount == 0 is ambiguous by itself: either the row doesn't
            # exist at all, or it exists but someone else already bumped
            # its version. These are different failures the caller needs
            # to distinguish (retry vs. give up entirely).
            current = self._conn.execute(
                "SELECT version FROM products WHERE id = ?", (product_id,)
            ).fetchone()
            if current is None:
                raise ProductNotFoundError(f"no product with id={product_id}")
            raise ConcurrentUpdateError(
                f"product {product_id} version mismatch: expected "
                f"{expected_version}, found {current['version']}"
            )
        return self.get(product_id)

    def update_quantity_with_retry(
        self, product_id: int, delta: int, *, max_attempts: int = 5
    ) -> Product:
        last_error: Exception | None = None
        for attempt in range(max_attempts):
            try:
                current = self.get(product_id)
                new_quantity = current.quantity + delta
                if new_quantity < 0:
                    raise InsufficientStockError(
                        f"product {product_id} has {current.quantity} units, "
                        f"delta {delta} would go negative"
                    )
                return self.update_quantity_optimistic(
                    product_id, current.version, new_quantity
                )
            except ConcurrentUpdateError as exc:
                # Correctness signal: our read was stale. Re-read fresh
                # state and recompute immediately -- no backoff needed,
                # the data (not the database) changed.
                last_error = exc
                continue
            except sqlite3.OperationalError as exc:
                if _LOCK_MESSAGE not in str(exc):
                    raise
                # Contention signal: the statement never even ran. Back off
                # with jitter so competing retriers don't collide in
                # lockstep, then retry the same attempt.
                last_error = exc
                time.sleep(random.uniform(0, 0.05 * (attempt + 1)))
                continue

        assert last_error is not None
        raise last_error


# ---------------------------------------------------------------------------
# Best practices
# ---------------------------------------------------------------------------
# - `BEGIN IMMEDIATE` for any multi-statement read-then-write sequence
#   whose correctness depends on nothing else writing in between --
#   DEFERRED's lazy locking is a race waiting to happen for exactly this
#   shape of code.
# - Optimistic locking (version column + conditional UPDATE + rowcount) is
#   a lock-free way to detect lost updates; it scales better than a
#   pessimistic row lock under low-contention workloads because readers
#   never block anything.
# - Distinguish contention (`OperationalError: database is locked` -- retry
#   the same operation) from a correctness conflict (`ConcurrentUpdateError`
#   -- re-read and recompute) -- collapsing them into one handler either
#   drops writes or spins forever.
# - Jittered backoff on lock contention avoids synchronized retry storms
#   among competing writers.
# - `try/except BaseException: rollback(); raise` (not bare `except
#   Exception`) ensures even a `KeyboardInterrupt` mid-transfer leaves no
#   dangling open transaction.
#
# Alternative approaches
# -----------------------
# - Pessimistic locking (`SELECT ... FOR UPDATE` in Postgres/MySQL; SQLite
#   has no row-level lock primitive, so `BEGIN IMMEDIATE`'s whole-database
#   write lock is the closest equivalent) trades throughput for simpler
#   reasoning under high contention.
# - `PRAGMA journal_mode=WAL` lets readers proceed without blocking on a
#   writer (and vice versa up to one writer at a time), which changes the
#   concurrency profile substantially versus the default rollback journal
#   -- worth a benchmark if this store saw real concurrent load.
# - A message queue / outbox pattern for the audit-log stretch goal keeps
#   the write path fast while still guaranteeing eventual consistency of
#   the log, at the cost of the log no longer being strictly
#   same-transaction-atomic with the balance change.
