"""
11 — Migrations & Schema Management
====================================

WHAT
----
A minimal but production-representative migration runner for `sqlite3`:

    - Migrations are plain Python objects (version, name, `up_sql`, optional
      `down_sql`), not files on disk — this keeps the exercise self-contained
      and testable without a filesystem/package-discovery layer, but the
      *runner* logic below is exactly what a file-based loader would drive.
    - A `schema_migrations` tracking table records which versions have been
      applied (and when), so `migrate()` is idempotent: running it twice is a
      no-op the second time, and running it after adding new migrations only
      applies the delta.
    - Migrations run inside a transaction each, so a mid-migration failure
      does not leave the schema half-updated for that step.
    - Rollback is supported two ways, and you're asked to reason about the
      trade-off explicitly (see `MigrationRunner.rollback`):
        1. down-migrations (`down_sql`) — reverse the specific DDL/DML.
        2. forward-only + backup — snapshot the DB file before migrating,
           and "rollback" means restoring the snapshot. This is what most
           real systems with irreversible migrations (e.g. dropped columns
           with data loss) actually do in practice.

WHY THIS MATTERS
-----------------
Schema migrations are one of the few places where "just re-run it" is not
safe by default — every real migration tool (Alembic, Flyway, golang-migrate,
Django migrations) solves the same core problems:

    1. **Idempotency** — deploying twice, or a crashed deploy restarting,
       must not double-apply or error out on already-applied migrations.
    2. **Ordering** — migrations must apply in a well-defined, monotonic
       order, and the runner must detect if the recorded history diverges
       from what's on disk/in code (e.g. someone re-numbered a file).
    3. **Atomicity** — a migration either fully applies or the schema is left
       as if it never started (per-migration transaction boundaries).
    4. **Rollback strategy** — not all DDL is reversible (SQLite in
       particular has very limited `ALTER TABLE` support: you cannot drop a
       column or change a column type without a table-rebuild dance), so a
       real system must pick a rollback story and document it, not assume
       one exists for free.

CONCEPTS EXERCISED
-------------------
    - `sqlite3` DDL/DML inside explicit transactions
      (`connection.execute("BEGIN")` / `commit()` / `rollback()`).
    - `IF NOT EXISTS` / `IF EXISTS` guards for idempotent DDL as a *second*
      layer of defense beneath the tracking table.
    - Designing a tracking table schema (version, name, checksum, applied_at).
    - Detecting schema drift: a migration already recorded whose `up_sql`
      hash no longer matches what's registered (someone edited history).
    - Backup-before-migrate via SQLite's online backup API
      (`sqlite3.Connection.backup`).

SPEC
----
    class Migration:
        version: int                 # monotonically increasing, unique
        name: str
        up_sql: str                  # one or more `;`-separated statements
        down_sql: str | None = None  # None => irreversible via down-migration

    class MigrationRunner:
        def __init__(self, conn: sqlite3.Connection) -> None: ...

        def ensure_tracking_table(self) -> None:
            "Create `schema_migrations` if it doesn't exist. Idempotent."

        def applied_versions(self) -> list[int]:
            "Versions already recorded, ascending."

        def pending(self, migrations: list[Migration]) -> list[Migration]:
            "Migrations from `migrations` not yet applied, sorted by version.
             Raise on duplicate versions or on a version whose recorded
             checksum doesn't match (schema drift)."

        def migrate(self, migrations: list[Migration]) -> list[int]:
            "Apply all pending migrations in order, each in its own
             transaction, recording it in schema_migrations on success.
             Returns the list of versions actually applied (empty if
             already up to date -- idempotent)."

        def backup(self, dest_path: str) -> None:
            "Snapshot the live DB to `dest_path` using the online backup API.
             Call before a risky migrate() as the forward-only rollback
             strategy."

        def rollback(self, migrations: list[Migration], steps: int = 1) -> list[int]:
            "Revert the last `steps` applied migrations using their
             `down_sql`, most-recent first. Raise if any target migration
             has no `down_sql` -- forces the caller to consciously choose
             the backup-restore path instead for irreversible steps.
             Returns the list of versions rolled back."

ACCEPTANCE CRITERIA
--------------------
    - Running `migrate()` twice with the same migration list applies nothing
      the second time and returns `[]`.
    - Migrations apply strictly in ascending version order regardless of the
      order they're passed in.
    - A migration whose SQL raises leaves the schema as it was before that
      migration started (no partial DDL for that step) and stops the run
      (later migrations are not attempted).
    - `rollback()` reverses migrations in reverse-applied order and removes
      their tracking rows.
    - `rollback()` on a migration with `down_sql=None` raises
      `IrreversibleMigrationError` rather than silently skipping it.
    - Re-registering a version with different `up_sql` than what's recorded
      is detected as drift and raises before applying anything.

Everything below is a stub. Fill in the `# TODO:` markers. Full type hints
are already in place -- match them.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


class MigrationError(Exception):
    """Base class for migration failures."""


class SchemaDriftError(MigrationError):
    """A recorded migration's checksum no longer matches its source."""


class IrreversibleMigrationError(MigrationError):
    """A rollback was requested for a migration with no down_sql."""


class DuplicateVersionError(MigrationError):
    """Two migrations declare the same version number."""


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    name: str
    up_sql: str
    down_sql: str | None = None

    def checksum(self) -> str:
        # TODO: return a stable hash of `up_sql` (e.g. sha256 hexdigest).
        raise NotImplementedError


class MigrationRunner:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        # TODO: anything else to initialize?

    def ensure_tracking_table(self) -> None:
        # TODO: CREATE TABLE IF NOT EXISTS schema_migrations(
        #   version INTEGER PRIMARY KEY,
        #   name TEXT NOT NULL,
        #   checksum TEXT NOT NULL,
        #   applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        # )
        raise NotImplementedError

    def applied_versions(self) -> list[int]:
        # TODO: SELECT version ORDER BY version ASC
        raise NotImplementedError

    def pending(self, migrations: list[Migration]) -> list[Migration]:
        # TODO:
        #  - detect duplicate versions in `migrations` -> DuplicateVersionError
        #  - detect drift against already-applied checksums -> SchemaDriftError
        #  - return not-yet-applied migrations sorted ascending by version
        raise NotImplementedError

    def migrate(self, migrations: list[Migration]) -> list[int]:
        # TODO:
        #  - self.ensure_tracking_table()
        #  - for each pending migration, in its own transaction:
        #      execute up_sql, insert tracking row, commit
        #    on failure: rollback that transaction and re-raise, stop the run
        #  - return versions actually applied
        raise NotImplementedError

    def backup(self, dest_path: str) -> None:
        # TODO: use sqlite3.Connection.backup() to snapshot to dest_path
        raise NotImplementedError

    def rollback(self, migrations: list[Migration], steps: int = 1) -> list[int]:
        # TODO:
        #  - determine last `steps` applied versions (descending)
        #  - look up each corresponding Migration by version
        #  - if any has down_sql is None -> IrreversibleMigrationError
        #  - execute down_sql, delete tracking row, per migration transaction
        #  - return versions rolled back, in the order rolled back
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Hints
# ---------------------------------------------------------------------------
# - `sqlite3.Connection` in `autocommit`-friendly usage: call
#   `conn.execute("BEGIN")` explicitly, then `conn.commit()` /
#   `conn.rollback()`, rather than relying on the implicit transaction
#   sqlite3 opens on the first DML statement -- it's clearer about intent
#   and lets you wrap DDL too (SQLite DDL is transactional, unlike most
#   other databases).
# - `up_sql`/`down_sql` may contain multiple `;`-separated statements --
#   `conn.executescript()` runs a whole script but *commits any open
#   transaction first*, which fights explicit transaction control. Prefer
#   splitting on `;` and using `conn.execute()` per statement, or accept
#   the executescript quirk and document it.
# - checksum drift detection is what stops "someone edited an already-
#   deployed migration's SQL" from silently reapplying differently in a
#   fresh environment vs. an existing one.
# - SQLite's limited ALTER TABLE is *why* the down-migration path is often
#   infeasible for column drops/type changes in practice -- the backup
#   path exists for exactly that case.
#
# Pitfalls
# --------
# - Forgetting `IF NOT EXISTS` on the tracking table breaks idempotent
#   `ensure_tracking_table()` calls across repeated runner construction.
# - Applying migrations in the order passed in, rather than sorted by
#   version, breaks the ordering acceptance criterion.
# - Not stopping the run after a failed migration lets ordering get out of
#   sync (a later migration might depend on the failed one's schema change).
#
# Stretch goals
# -------------
# - Add a `dry_run` mode to `migrate()` that reports what would run without
#   applying it.
# - Support "repeatable" migrations (re-run whenever their checksum changes,
#   e.g. for view/trigger definitions) alongside versioned ones.
# - Add a CLI-style `status()` method that prints applied vs. pending in a
#   table.
