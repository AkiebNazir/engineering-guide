"""
10 — Transactions & Concurrency Control
==========================================

WHAT
----
Extend problem 09's inventory domain with transactional transfers and
optimistic concurrency control:

    class InsufficientStockError(Exception): ...
    class ConcurrentUpdateError(Exception): ...

    class InventoryStore:
        def __init__(self, db_path) -> None: ...
        def create_product(self, sku, name, quantity, price_cents) -> Product: ...
        def get(self, product_id) -> Product: ...

        def transfer_stock(self, from_id, to_id, amount) -> None:
            "Move `amount` units from one product's quantity to another's,
            atomically: either both quantities change or neither does."

        def update_quantity_optimistic(
            self, product_id, expected_version, new_quantity
        ) -> Product:
            "Conditional UPDATE keyed on a version column -- raises
            ConcurrentUpdateError if another writer changed the row first."

        def update_quantity_with_retry(
            self, product_id, delta, *, max_attempts=5
        ) -> Product:
            "Read-modify-write quantity by `delta` using optimistic locking,
            retrying on ConcurrentUpdateError with backoff."

WHY THIS MATTERS
----------------
Problem 09 built single-row CRUD. Real systems need *multi-statement*
correctness (a transfer between two rows must never leave money/stock
half-moved) and *concurrent-writer* correctness (two requests updating the
same row at once must not silently overwrite each other's work — the
classic lost-update bug). This is the same domain (inventory/account
balance) as problem 09 on purpose: everything you already know about the
schema and repository shape carries over; only the write path changes.

ISOLATION LEVELS
------------------
`sqlite3.connect(..., isolation_level=...)` controls when SQLite opens an
implicit transaction:
  - `isolation_level=""` (or `None` via `autocommit=True` on 3.12+'s new
    autocommit control) — every statement, including SELECT, is
    auto-committed unless you `BEGIN` explicitly.
  - `isolation_level="DEFERRED"` (the sqlite3 module's default) — a
    transaction opens on the first DML statement (INSERT/UPDATE/DELETE),
    not on SELECT, and the underlying SQLite lock is acquired lazily
    (deferred until an actual write occurs).
  - `isolation_level="IMMEDIATE"` — acquires a `RESERVED` write lock the
    moment `BEGIN` runs, even before the first write statement executes.
    This is what you want for the transfer method below: without it, two
    concurrent `transfer_stock` calls can both pass their DEFERRED read
    checks before either acquires the write lock, race past each other's
    validation, and both proceed to write — exactly the multi-statement
    atomicity bug this problem exists to prevent.
Use a single `with self._conn:` block (sqlite3's connection context manager
commits on clean exit / rolls back on exception) wrapped around an explicit
`BEGIN IMMEDIATE` for `transfer_stock`.

OPTIMISTIC LOCKING
--------------------
Add a `version INTEGER NOT NULL DEFAULT 1` column. A caller reads a row
(getting its current `version`), computes a new value, then issues:

    UPDATE products
    SET quantity = ?, version = version + 1
    WHERE id = ? AND version = ?

If another writer already bumped `version` between the read and this
UPDATE, `cursor.rowcount == 0` — nothing matched the WHERE clause — and
`update_quantity_optimistic` must raise `ConcurrentUpdateError` rather than
silently doing nothing. This is compare-and-swap implemented entirely in
SQL, with no application-level lock required, and it's the standard pattern
for "detect concurrent modification" in any database that supports
conditional UPDATE + rowcount.

RETRYABLE LOCK ERRORS
------------------------
Under real concurrent write load, SQLite's own locking can produce
`sqlite3.OperationalError: database is locked` (one connection holds the
write lock while another times out waiting for it — see `busy_timeout`).
This is different from `ConcurrentUpdateError` (a *correctness* signal: the
data changed) — a locked-database error is a *contention* signal: no data
was seen, the statement never even ran. The correct response is: retry with
jittered exponential backoff up to `max_attempts`, and only then give up
loudly. `update_quantity_with_retry` must handle BOTH failure modes:
`ConcurrentUpdateError` (re-read and reapply the delta) AND
`sqlite3.OperationalError` matching "database is locked" (back off and
retry the same attempt).

SPEC / ACCEPTANCE CRITERIA
----------------------------
- `transfer_stock(from_id, to_id, amount)`:
    - raises `InsufficientStockError` if `from_id`'s quantity < amount,
      *without* writing anything.
    - on success, `from_id`'s quantity decreases by `amount` and `to_id`'s
      increases by `amount`, atomically — verified by a test that raises an
      exception partway through a monkeypatched transfer and asserts BOTH
      rows are unchanged afterward (no partial transfer).
    - uses `BEGIN IMMEDIATE` (or equivalent) so two concurrent transfers out
      of the same account cannot both read stale stock and both succeed
      when only one should.
- `update_quantity_optimistic(product_id, expected_version, new_quantity)`:
    - succeeds and bumps `version` by 1 when `expected_version` matches the
      current row.
    - raises `ConcurrentUpdateError` (not a silent no-op) when
      `expected_version` is stale.
- `update_quantity_with_retry`:
    - converges to the correct final quantity when simulated concurrent
      writers interleave (test via two `InventoryStore` handles against the
      same `tmp_path` db file, or by manually racing optimistic updates).
    - retries (does not immediately raise) on a simulated
      `sqlite3.OperationalError("database is locked")`, and gives up with
      that same exception type after `max_attempts`.
- All of this is tested against real file-backed SQLite via `tmp_path`, not
  mocked — lock contention and rowcount behavior are exactly the kind of
  thing a mock would get wrong by construction.
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
    version: int


class ProductNotFoundError(Exception):
    """Raised when a lookup/update/delete targets a missing product id."""


class InsufficientStockError(Exception):
    """Raised when a transfer would drive quantity negative."""


class ConcurrentUpdateError(Exception):
    """Raised when an optimistic UPDATE's expected_version no longer matches."""


class InventoryStore:
    """Transactional, optimistically-locked inventory store (builds on 09)."""

    def __init__(self, db_path: str | Path) -> None:
        """TODO:
        - open sqlite3.connect(str(db_path))
        - row_factory = sqlite3.Row
        - isolation_level="" is NOT what you want here by default; use the
          module default (DEFERRED) for plain reads/writes, and issue an
          explicit `BEGIN IMMEDIATE` only inside transfer_stock.
        - set a busy_timeout PRAGMA so short lock waits resolve themselves
          before raising "database is locked" (e.g. `PRAGMA busy_timeout =
          2000`), and note in a comment that this doesn't replace your own
          retry loop -- it just raises the threshold before you need it.
        - CREATE TABLE IF NOT EXISTS products (..., version INTEGER NOT
          NULL DEFAULT 1)
        """
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def __enter__(self) -> InventoryStore:
        raise NotImplementedError

    def __exit__(self, *exc_info: object) -> None:
        raise NotImplementedError

    def create_product(
        self, sku: str, name: str, quantity: int, price_cents: int
    ) -> Product:
        """TODO: same as problem 09's create, plus the version column
        (defaults to 1)."""
        raise NotImplementedError

    def get(self, product_id: int) -> Product:
        """TODO: SELECT by id including version; ProductNotFoundError if
        missing."""
        raise NotImplementedError

    def transfer_stock(self, from_id: int, to_id: int, amount: int) -> None:
        """TODO:
        - `self._conn.execute("BEGIN IMMEDIATE")` to take the write lock
          up front, before reading anything.
        - read from_id's current quantity; if < amount, raise
          InsufficientStockError (and roll back -- no writes have happened
          yet, but be explicit: `self._conn.rollback()` or let the `with
          self._conn:` context manager's exception path handle it).
        - UPDATE both rows' quantity.
        - commit via the connection context manager or explicit commit().
        - on ANY exception, ensure rollback happens (no partial transfer
          visible).
        """
        raise NotImplementedError

    def update_quantity_optimistic(
        self, product_id: int, expected_version: int, new_quantity: int
    ) -> Product:
        """TODO:
        UPDATE products SET quantity = ?, version = version + 1
        WHERE id = ? AND version = ?
        using (new_quantity, product_id, expected_version). If
        cursor.rowcount == 0, first check whether the row exists at all
        (ProductNotFoundError) vs. exists with a different version
        (ConcurrentUpdateError) -- these are different failures and callers
        need to tell them apart.
        """
        raise NotImplementedError

    def update_quantity_with_retry(
        self, product_id: int, delta: int, *, max_attempts: int = 5
    ) -> Product:
        """TODO: loop up to max_attempts times:
        - read current product (get version + quantity)
        - compute new_quantity = quantity + delta (raise
          InsufficientStockError up front if this would go negative)
        - call update_quantity_optimistic; on success return it
        - on ConcurrentUpdateError: retry immediately (re-read fresh state)
        - on sqlite3.OperationalError matching "database is locked": sleep
          a short jittered backoff, then retry the SAME attempt
        - after max_attempts exhausted, re-raise the last error
        """
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Hints
# ---------------------------------------------------------------------------
# - `conn.execute("BEGIN IMMEDIATE")` then treat the rest of the method as
#   one transaction; `conn.commit()` on success, `conn.rollback()` in an
#   `except` clause (or a `try/except/else` where the happy path commits).
# - `"database is locked" in str(exc)` is the pragmatic way to distinguish
#   a lock-contention `OperationalError` from other `OperationalError`s
#   (e.g. a genuine SQL syntax error) since sqlite3 doesn't give a distinct
#   exception subclass for it.
# - `random.uniform(0, backoff)` jitter avoids two competing retriers
#   re-colliding in lockstep ("thundering herd").
# - To actually *observe* `database is locked` in a test, open a second
#   connection to the same file with a short `busy_timeout`, `BEGIN
#   IMMEDIATE` on it and hold it open (don't commit) while the code under
#   test tries to write.
#
# Pitfalls
# --------
# - Using the DEFERRED (default) isolation level for `transfer_stock` --
#   the write lock isn't taken until the first actual write, so two
#   concurrent transfers can both pass a stock-sufficiency check reading
#   stale data before either one's write lock blocks the other. IMMEDIATE
#   closes this window by taking the lock before any reads happen.
# - Treating `ConcurrentUpdateError` and "database is locked" as the same
#   failure -- one means "your read was stale, recompute", the other means
#   "the database was too busy to even attempt your statement, just
#   retry the identical write". Conflating them leads to either silently
#   dropped writes or infinite tight-loop retries.
# - Retrying forever with no cap -- always bound attempts and raise loudly
#   once exhausted; a production system needs to alert on sustained
#   contention, not spin silently.
# - Forgetting `PRAGMA busy_timeout` and then being surprised at how
#   quickly "database is locked" fires under even light concurrent load.
#
# Stretch goals
# -------------
# - Add a `history` table recording every quantity change (audit log) as
#   part of the same transaction as the update itself -- the same-
#   transaction requirement is the whole point (a log entry that ends up
#   out of sync with the balance is worse than no log at all).
# - Parametrize `update_quantity_with_retry`'s backoff strategy and write a
#   test asserting it actually sleeps increasing amounts (via
#   monkeypatching `time.sleep`, not real wall-clock waits).
# - Explore SQLite's WAL mode (`PRAGMA journal_mode=WAL`) and note in a
#   comment how it changes reader/writer concurrency compared to the
#   default rollback-journal mode (readers no longer block a writer).
