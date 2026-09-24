from __future__ import annotations

import os
import sqlite3
import tempfile
from collections.abc import Iterator
from importlib import import_module
from typing import Any

import pytest

# The directory (and thus module) name starts with a digit, so it can't be
# named in a real `import` statement. pytest inserts this file's directory
# on sys.path, so the module is importable dynamically by name at runtime.
# mypy has no static visibility into a dynamically-named module, so the
# re-exported names below are intentionally typed as `Any` rather than
# faked into precise types.
_solution = import_module("11_migrations_schema_management_solution")
Migration: Any = _solution.Migration
MigrationRunner: Any = _solution.MigrationRunner
MigrationError: Any = _solution.MigrationError
SchemaDriftError: Any = _solution.SchemaDriftError
IrreversibleMigrationError: Any = _solution.IrreversibleMigrationError
DuplicateVersionError: Any = _solution.DuplicateVersionError


@pytest.fixture
def conn() -> Iterator[sqlite3.Connection]:
    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    connection = sqlite3.connect(path)
    try:
        yield connection
    finally:
        connection.close()
        os.remove(path)


@pytest.fixture
def runner(conn: sqlite3.Connection) -> Any:
    return MigrationRunner(conn)


def make_users_migration() -> Any:
    return Migration(
        version=1,
        name="create_users",
        up_sql="CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)",
        down_sql="DROP TABLE users",
    )


def make_email_migration() -> Any:
    return Migration(
        version=2,
        name="add_email_to_users",
        up_sql="ALTER TABLE users ADD COLUMN email TEXT",
        down_sql=None,  # SQLite can't drop columns without a table rebuild
    )


def test_migrate_applies_in_order_and_records_versions(runner: Any) -> None:
    m2 = make_email_migration()
    m1 = make_users_migration()

    applied = runner.migrate([m2, m1])  # passed out of order

    assert applied == [1, 2]
    assert runner.applied_versions() == [1, 2]


def test_migrate_is_idempotent(runner: Any) -> None:
    migrations = [make_users_migration(), make_email_migration()]

    first = runner.migrate(migrations)
    second = runner.migrate(migrations)

    assert first == [1, 2]
    assert second == []


def test_migrate_applies_only_pending_delta(runner: Any) -> None:
    m1 = make_users_migration()
    runner.migrate([m1])

    m2 = make_email_migration()
    applied = runner.migrate([m1, m2])

    assert applied == [2]


def test_ensure_tracking_table_idempotent_across_constructions(
    conn: sqlite3.Connection,
) -> None:
    MigrationRunner(conn).ensure_tracking_table()
    # Constructing a second runner on the same connection and calling
    # ensure_tracking_table again must not raise.
    MigrationRunner(conn).ensure_tracking_table()


def test_failed_migration_leaves_schema_unchanged_and_stops_run(
    runner: Any, conn: sqlite3.Connection
) -> None:
    good = make_users_migration()
    bad = Migration(
        version=2, name="broken", up_sql="CREATE TABLE users (bad syntax HERE"
    )
    never_reached = Migration(
        version=3, name="never", up_sql="CREATE TABLE ghosts (id INTEGER)"
    )

    with pytest.raises(sqlite3.OperationalError):
        runner.migrate([good, bad, never_reached])

    # version 1 succeeded and was recorded; the run stopped before 3.
    assert runner.applied_versions() == [1]
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "ghosts" not in tables
    assert "users" in tables  # migration 1's own effect persisted


def test_duplicate_version_raises(runner: Any) -> None:
    m1 = make_users_migration()
    dupe = Migration(version=1, name="dupe", up_sql="SELECT 1")

    with pytest.raises(DuplicateVersionError):
        runner.migrate([m1, dupe])


def test_schema_drift_detected(runner: Any) -> None:
    original = make_users_migration()
    runner.migrate([original])

    tampered = Migration(
        version=1,
        name="create_users",
        up_sql="CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, extra TEXT)",
        down_sql="DROP TABLE users",
    )

    with pytest.raises(SchemaDriftError):
        runner.migrate([tampered])


def test_rollback_reverses_last_migration(runner: Any) -> None:
    m1 = make_users_migration()
    runner.migrate([m1])

    rolled_back = runner.rollback([m1], steps=1)

    assert rolled_back == [1]
    assert runner.applied_versions() == []


def test_rollback_irreversible_raises(runner: Any) -> None:
    m1 = make_users_migration()
    m2 = make_email_migration()  # down_sql=None
    runner.migrate([m1, m2])

    with pytest.raises(IrreversibleMigrationError):
        runner.rollback([m1, m2], steps=1)

    # Nothing should have been rolled back on a rejected request.
    assert runner.applied_versions() == [1, 2]


def test_backup_creates_restorable_snapshot(runner: Any, tmp_path: object) -> None:
    import pathlib

    assert isinstance(tmp_path, pathlib.Path)
    runner.migrate([make_users_migration()])

    backup_path = tmp_path / "backup.sqlite3"
    runner.backup(str(backup_path))

    backup_conn = sqlite3.connect(str(backup_path))
    try:
        tables = {
            row[0]
            for row in backup_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        backup_conn.close()

    assert "users" in tables
    assert "schema_migrations" in tables
