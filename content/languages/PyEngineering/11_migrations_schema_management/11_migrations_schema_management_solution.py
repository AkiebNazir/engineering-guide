"""
11 — Migrations & Schema Management — solution.

Full runner: idempotent versioned migrations, drift detection, per-migration
transactions, online backup, and down-migration rollback.
"""

from __future__ import annotations

import hashlib
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
        # sha256 over the up_sql text is enough to detect "this migration's
        # SQL changed after it was recorded as applied". We hash only
        # up_sql (not down_sql/name) because up_sql is what actually shaped
        # the schema the tracking row attests to.
        return hashlib.sha256(self.up_sql.encode("utf-8")).hexdigest()


def _split_statements(script: str) -> list[str]:
    # Naive `;`-splitting is sufficient for the DDL/DML used in this
    # exercise (no stored procedures, no string literals containing `;`).
    # A real loader parsing arbitrary SQL files would want a proper SQL
    # tokenizer, but for migration scripts written by us that's overkill.
    return [stmt.strip() for stmt in script.split(";") if stmt.strip()]


class MigrationRunner:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        # We manage transactions explicitly (BEGIN/COMMIT/ROLLBACK), so
        # isolation_level=None puts the connection in autocommit mode and
        # stops sqlite3's implicit transaction machinery from fighting us.
        self._conn.isolation_level = None

    def ensure_tracking_table(self) -> None:
        # IF NOT EXISTS makes constructing a new MigrationRunner against an
        # already-migrated database a no-op here -- the first layer of
        # idempotency, independent of the tracking-row bookkeeping below.
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version    INTEGER PRIMARY KEY,
                name       TEXT NOT NULL,
                checksum   TEXT NOT NULL,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """)

    def applied_versions(self) -> list[int]:
        rows = self._conn.execute(
            "SELECT version FROM schema_migrations ORDER BY version ASC"
        ).fetchall()
        return [row[0] for row in rows]

    def _applied_checksums(self) -> dict[int, str]:
        rows = self._conn.execute(
            "SELECT version, checksum FROM schema_migrations"
        ).fetchall()
        return {version: checksum for version, checksum in rows}

    def pending(self, migrations: list[Migration]) -> list[Migration]:
        seen: dict[int, Migration] = {}
        for m in migrations:
            if m.version in seen:
                raise DuplicateVersionError(
                    f"version {m.version} declared more than once "
                    f"({seen[m.version].name!r} and {m.name!r})"
                )
            seen[m.version] = m

        applied = self._applied_checksums()
        for version, recorded_checksum in applied.items():
            candidate = seen.get(version)
            if candidate is not None and candidate.checksum() != recorded_checksum:
                raise SchemaDriftError(
                    f"migration {version} ({candidate.name!r}) has been "
                    "modified since it was applied: recorded checksum "
                    f"{recorded_checksum} != current {candidate.checksum()}"
                )

        return sorted(
            (m for m in migrations if m.version not in applied),
            key=lambda m: m.version,
        )

    def migrate(self, migrations: list[Migration]) -> list[int]:
        self.ensure_tracking_table()
        to_apply = self.pending(migrations)

        applied_now: list[int] = []
        for migration in to_apply:
            self._conn.execute("BEGIN")
            try:
                for statement in _split_statements(migration.up_sql):
                    self._conn.execute(statement)
                self._conn.execute(
                    "INSERT INTO schema_migrations (version, name, checksum) "
                    "VALUES (?, ?, ?)",
                    (migration.version, migration.name, migration.checksum()),
                )
            except Exception:
                # Any failure mid-migration rolls back *this* migration's
                # transaction entirely -- the schema is left exactly as it
                # was before this step started. We deliberately stop the
                # run rather than attempt later migrations, since they may
                # depend on this one's (now-absent) schema change.
                self._conn.rollback()
                raise
            else:
                self._conn.commit()
                applied_now.append(migration.version)

        return applied_now

    def backup(self, dest_path: str) -> None:
        # SQLite's online backup API copies the live database
        # page-by-page, safely even against a database with an open
        # connection, without requiring exclusive access for the whole
        # copy. This is the forward-only-migration safety net: snapshot
        # before a risky migrate(), restore the file wholesale if it goes
        # wrong in ways down_sql can't or shouldn't undo.
        dest = sqlite3.connect(dest_path)
        try:
            self._conn.backup(dest)
        finally:
            dest.close()

    def rollback(self, migrations: list[Migration], steps: int = 1) -> list[int]:
        by_version = {m.version: m for m in migrations}
        applied_desc = sorted(self.applied_versions(), reverse=True)
        targets = applied_desc[:steps]

        # Validate every target is reversible *before* touching the
        # database -- an all-or-nothing check up front, so a partially
        # irreversible rollback request never leaves the schema half
        # rolled back.
        for version in targets:
            migration = by_version.get(version)
            if migration is None:
                raise MigrationError(
                    f"applied version {version} not found in supplied "
                    "migrations list -- cannot determine its down_sql"
                )
            if migration.down_sql is None:
                raise IrreversibleMigrationError(
                    f"migration {version} ({migration.name!r}) has no "
                    "down_sql; use backup()/restore instead"
                )

        rolled_back: list[int] = []
        for version in targets:
            migration = by_version[version]
            assert migration.down_sql is not None  # validated above
            self._conn.execute("BEGIN")
            try:
                for statement in _split_statements(migration.down_sql):
                    self._conn.execute(statement)
                self._conn.execute(
                    "DELETE FROM schema_migrations WHERE version = ?",
                    (version,),
                )
            except Exception:
                self._conn.rollback()
                raise
            else:
                self._conn.commit()
                rolled_back.append(version)

        return rolled_back


# ---------------------------------------------------------------------------
# Best practices
# ---------------------------------------------------------------------------
# - Explicit BEGIN/COMMIT/ROLLBACK per migration, with isolation_level=None,
#   makes the transaction boundary match the unit of idempotency (one
#   tracking row per migration) exactly -- no implicit-transaction surprises
#   from sqlite3's DBAPI wrapper.
# - Checksums turn "migration history is a git-tracked, append-only log"
#   from a convention into something the runner *verifies* -- drift is
#   caught at pending()-time, before any SQL runs, rather than silently
#   producing different schemas across environments.
# - Validating all rollback targets before executing any of them avoids a
#   half-completed rollback when steps > 1 and an early target turns out
#   to be irreversible.
# - The tracking table itself is created with IF NOT EXISTS and is never
#   dropped/recreated, so constructing a MigrationRunner is always safe to
#   repeat -- mirrors how Alembic/Flyway treat their own bookkeeping table.
#
# Alternative approaches
# -----------------------
# - File-based discovery (e.g. `migrations/0001_x.sql` / `0001_x_down.sql`
#   pairs) instead of in-code Migration objects -- more realistic for a
#   large project, but adds a filesystem/naming-convention layer that's
#   orthogonal to the runner logic exercised here.
# - A single big transaction for the whole migrate() run, rather than one
#   per migration -- gives you all-or-nothing across the *entire* batch,
#   which some teams prefer for deploy-time migrations, at the cost of
#   holding one transaction open (and any associated locks) for the whole
#   run. Per-migration transactions are usually the better default because
#   they let already-applied migrations from a partially-successful run
#   stay applied rather than being rolled back on an unrelated later
#   failure.
# - `conn.executescript()` for multi-statement SQL is tempting but commits
#   any currently-open transaction as a side effect before running, which
#   breaks explicit transaction boundaries -- hence the manual `;`-split.
