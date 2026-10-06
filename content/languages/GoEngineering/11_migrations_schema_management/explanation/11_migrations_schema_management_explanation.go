/*
Problem 11 — Migrations & Schema Management
=============================================

WHAT WE'RE BUILDING

A minimal, dependency-free migration runner: the piece of infrastructure every
non-trivial service needs the moment its schema will change more than once.
Rails has ActiveRecord migrations, Django has its migration framework, the Go
ecosystem has golang-migrate / goose / atlas — but understanding what those
tools do under the hood (and why) is what separates "I ran a CLI command" from
"I can debug a broken deploy at 2am because migration 0042 half-applied".

We run against a REAL embedded database (SQLite via the pure-Go
modernc.org/sqlite driver — no cgo, no external service, so the tests in this
repo are hermetic) on a temp file, so every operation here is the same
`database/sql` code path you'd use against Postgres or MySQL in production.

WHY THIS MATTERS IN REAL SYSTEMS

  - Schema changes are the highest-blast-radius deploys a service makes. A bad
    migration can take down every replica simultaneously (unlike a bad binary,
    which you can roll back instantly — a bad migration may have already
    mutated data).
  - Migrations MUST be idempotent and re-runnable: deploy tooling retries,
    multiple replicas may race to apply the same migration on boot, and a
    human may re-run the migrate command after a partial failure.
  - Migrations MUST be ordered and tracked: the database itself is the source
    of truth for "what has already been applied" — not a flag file, not an
    environment variable.
  - Rollback is a deliberate, limited tool — not every migration is safely
    reversible (you cannot "undo" a dropped column's data), but the mechanism
    to go backward during a bad deploy must exist and be tested.

CONCEPTS COVERED

  - Versioned, ordered migrations with an up/down pair per version.
  - A `schema_migrations` bookkeeping table living IN the same database,
    updated transactionally with the schema change itself (so a crash never
    leaves the tracking table and the schema disagreeing).
  - Idempotency: applying an already-applied migration, or an already-reverted
    rollback, is a safe no-op.
  - Partial-failure safety: if migration N's SQL fails partway through, the
    whole transaction (DDL + bookkeeping row) rolls back, leaving the schema
    exactly as it was before the attempt — SQLite supports transactional DDL,
    which is what makes this possible without a lock file.
  - Rollback strategy: revert N steps, or down-to a specific target version,
    running Down scripts in reverse order.
  - `database/sql` fundamentals: driver registration via blank import,
    context-aware `ExecContext`/`QueryContext`, `*sql.Tx` for atomicity.

# THE SPEC

Package `main` — chosen deliberately over a library package because a
migration runner is naturally something you EXECUTE (a CLI/init-container
binary that runs once at deploy time and exits), not something another
service imports and calls in the request path. `main()` here is a runnable
demonstration: it opens a temp-file SQLite database, applies all migrations,
prints status, and cleans up. The interesting logic is exported from the
`Migrator` type so it's directly testable.

Implement:

	type Migration struct {
	    Version int    // strictly increasing, unique across the set
	    Name    string // human-readable, e.g. "create_users_table"
	    Up      string // DDL/DML to apply the migration
	    Down    string // DDL/DML to revert it (may be empty = irreversible)
	}

	type MigrationStatus struct {
	    Version int
	    Name    string
	    Applied bool
	    AppliedAt time.Time // zero value if not applied
	}

	type Migrator struct { ... } // unexported fields: *sql.DB, sorted []Migration

	func NewMigrator(db *sql.DB, migrations []Migration) (*Migrator, error)
	    - Validates: no duplicate versions, all versions > 0, sorts by version
	      ascending. Returns an error (wrapped, not panicked) on a bad set —
	      this is a programmer error caught at startup, not a runtime one.

	func (m *Migrator) EnsureSchemaTable(ctx context.Context) error
	    - Creates the `schema_migrations` bookkeeping table if it doesn't
	      exist. Must itself be idempotent (CREATE TABLE IF NOT EXISTS).

	func (m *Migrator) AppliedVersions(ctx context.Context) (map[int]time.Time, error)
	    - Reads the bookkeeping table. Empty map (not an error) if nothing has
	      run yet.

	func (m *Migrator) Up(ctx context.Context) (applied []int, err error)
	    - Applies every pending migration in ascending version order. Each
	      migration runs in its own transaction: the migration's SQL AND the
	      bookkeeping INSERT happen atomically. Stops and returns an error on
	      the first failure, leaving already-applied migrations applied and the
	      failed one (and everything after it) untouched. Returns the list of
	      versions actually applied (empty slice, not nil, if nothing was
	      pending — calling Up twice in a row is a safe no-op).

	func (m *Migrator) UpTo(ctx context.Context, target int) (applied []int, err error)
	    - Same as Up but stops after applying `target` (inclusive). Useful for
	      step-by-step deploys or tests that want a specific schema snapshot.

	func (m *Migrator) Down(ctx context.Context, steps int) (reverted []int, err error)
	    - Reverts the `steps` most-recently-applied migrations, in reverse
	      version order, each in its own transaction. Returns an error
	      (sentinel, checkable with errors.Is) if a migration in range has no
	      Down script — never silently skip it.

	func (m *Migrator) DownTo(ctx context.Context, target int) (reverted []int, err error)
	    - Reverts everything applied with version > target.

	func (m *Migrator) Status(ctx context.Context) ([]MigrationStatus, error)
	    - Full picture: every known migration plus whether/when it was applied,
	      in version order.

	Sentinel errors to define:
	    ErrNoDownScript   — Down() hit a migration with an empty Down field.
	    ErrUnknownVersion — DownTo/UpTo given a version not in the migration set.

ACCEPTANCE CRITERIA

  - Calling Up() twice in a row applies nothing the second time and returns
    an empty, non-nil slice.
  - A migration whose Up SQL fails leaves the database schema and the
    schema_migrations table exactly as they were before the call (verified by
    re-querying both after the error).
  - Down() reverts in strict reverse-version order and updates
    schema_migrations to remove the reverted rows.
  - Status() accurately reflects applied/pending state after any sequence of
    Up/Down calls.
  - All of it passes `go test -race`: the Migrator itself isn't required to
    be safe for concurrent Up() calls from multiple goroutines in this
    problem (real deployments use a DB-level advisory lock for that — see the
    stretch goals) but the test suite must still be race-clean.

HINTS

  - `sql.DB` is a connection pool, not a single connection. For SQLite in
    particular, keep it simple: a temp file + default pool settings is fine
    for this exercise. Production SQLite tends to pin MaxOpenConns(1) or use
    WAL mode to deal with the single-writer constraint — that's a stretch
    goal, not baseline behavior here.
  - Use `db.BeginTx(ctx, nil)` and always `defer tx.Rollback()` immediately
    after a successful Begin — calling Rollback on an already-committed tx is
    a documented no-op, so this pattern is always safe and is the idiomatic
    way to guarantee cleanup on every early-return path.
  - The bookkeeping INSERT and the migration's own SQL must be executed
    against the SAME `*sql.Tx`, not the `*sql.DB` — that's the whole trick
    that makes this atomic.
  - `%w` every wrapped error so callers can `errors.Is`/`errors.As` through
    your Migrator's errors down to the underlying driver error.

COMMON PITFALLS

  - Running the bookkeeping INSERT against `db` instead of `tx` — silently
    breaks atomicity; a crash between the two leaves you with a schema change
    applied but not recorded (or vice versa), and the next Up() either
    re-applies (if your Up SQL isn't itself idempotent, e.g. a bare
    `CREATE TABLE` without `IF NOT EXISTS`) or skips forever.
  - Forgetting `ORDER BY version` when reading back applied versions — map
    iteration order in Go is randomized, so anything read into a map and then
    ranged over for anything ORDER-sensitive (like Down()) will misbehave
    intermittently, which is exactly the kind of bug that passes locally and
    fails in CI.
  - Not sorting the input migrations slice in NewMigrator and instead trusting
    caller order.

STRETCH GOALS

  - Add a checksum (e.g. FNV or SHA-256 of the Up+Down SQL) stored alongside
    each applied version, and detect "a migration that was already applied
    has since been edited in the source" — a common source of prod/staging
    drift bugs.
  - Add an advisory lock (SQLite: a dedicated `migration_lock` table with a
    single row and `BEGIN IMMEDIATE`) so two replicas racing to migrate on
    boot don't double-apply or corrupt the bookkeeping table.
  - Support a `-dry-run` mode that prints the SQL that WOULD run without
    executing it.
  - Generalize `Migrator` to accept migrations loaded from an `embed.FS` of
    `.sql` files named `0001_create_users.up.sql` / `.down.sql`, parsed at
    startup instead of being hardcoded Go literals.
*/
package main

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"log"
	"os"
	"time"

	_ "modernc.org/sqlite"
)

// Migration is one versioned, reversible schema change.
type Migration struct {
	Version int
	Name    string
	Up      string
	Down    string
}

// MigrationStatus reports whether a known migration has been applied.
type MigrationStatus struct {
	Version   int
	Name      string
	Applied   bool
	AppliedAt time.Time
}

// Sentinel errors the Migrator returns. Wrap the underlying cause with %w so
// callers can still errors.Is/As through to it.
var (
	// ErrNoDownScript is returned by Down/DownTo when a migration in the
	// range being reverted has no Down script.
	ErrNoDownScript = errors.New("migrations: no down script for this version")
	// ErrUnknownVersion is returned by UpTo/DownTo when target is not a
	// version present in the migration set.
	ErrUnknownVersion = errors.New("migrations: unknown target version")
)

// Migrator applies and reverts a versioned set of migrations against db,
// tracking applied state in a schema_migrations table.
type Migrator struct {
	// TODO: unexported fields — *sql.DB, sorted []Migration
}

// NewMigrator validates migrations (unique, positive versions) and returns a
// Migrator with them sorted ascending by version.
func NewMigrator(db *sql.DB, migrations []Migration) (*Migrator, error) {
	panic("TODO: implement NewMigrator")
}

// EnsureSchemaTable creates the bookkeeping table if it does not exist.
func (m *Migrator) EnsureSchemaTable(ctx context.Context) error {
	panic("TODO: implement EnsureSchemaTable")
}

// AppliedVersions returns every applied version mapped to its applied time.
func (m *Migrator) AppliedVersions(ctx context.Context) (map[int]time.Time, error) {
	panic("TODO: implement AppliedVersions")
}

// Up applies every pending migration in ascending order, one transaction per
// migration. Returns the versions actually applied.
func (m *Migrator) Up(ctx context.Context) ([]int, error) {
	panic("TODO: implement Up")
}

// UpTo applies pending migrations up to and including target.
func (m *Migrator) UpTo(ctx context.Context, target int) ([]int, error) {
	panic("TODO: implement UpTo")
}

// Down reverts the `steps` most recently applied migrations, newest first.
func (m *Migrator) Down(ctx context.Context, steps int) ([]int, error) {
	panic("TODO: implement Down")
}

// DownTo reverts every applied migration with version > target.
func (m *Migrator) DownTo(ctx context.Context, target int) ([]int, error) {
	panic("TODO: implement DownTo")
}

// Status reports every known migration and its applied state, version order.
func (m *Migrator) Status(ctx context.Context) ([]MigrationStatus, error) {
	panic("TODO: implement Status")
}

// sampleMigrations is a small, representative set: two forward-compatible
// schema changes with reversible Down scripts. Real projects load these from
// embedded .sql files (see stretch goals) rather than hardcoding literals,
// but inline literals keep this demo self-contained.
func sampleMigrations() []Migration {
	return []Migration{
		{
			Version: 1,
			Name:    "create_users_table",
			Up: `CREATE TABLE users (
				id INTEGER PRIMARY KEY,
				email TEXT NOT NULL UNIQUE
			);`,
			Down: `DROP TABLE users;`,
		},
		{
			Version: 2,
			Name:    "add_users_created_at",
			Up:      `ALTER TABLE users ADD COLUMN created_at TIMESTAMP;`,
			Down:    ``, // SQLite can't drop columns pre-3.35 without a table
			// rebuild; treat this one as irreversible on purpose so Down()'s
			// ErrNoDownScript path has a realistic example to exercise.
		},
	}
}

// main is a runnable demonstration, not the interesting part of this
// exercise: it wires a temp-file SQLite database to a Migrator and drives it
// through the same Up -> Status -> Down lifecycle a deploy tool would. Every
// method it calls is a TODO above, so running this (after `go build`
// succeeds) will panic until you implement them — that's expected. The point
// of this file, unlike solution/, is to compile immediately so you can
// iterate with `go build ./...` while filling in the TODOs.
func main() {
	dbFile, err := os.CreateTemp("", "migrator-demo-*.db")
	if err != nil {
		log.Fatalf("create temp db file: %v", err)
	}
	dbPath := dbFile.Name()
	_ = dbFile.Close()
	defer os.Remove(dbPath)

	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		log.Fatalf("open sqlite: %v", err)
	}
	defer db.Close()

	ctx := context.Background()

	m, err := NewMigrator(db, sampleMigrations())
	if err != nil {
		log.Fatalf("new migrator: %v", err)
	}

	if err := m.EnsureSchemaTable(ctx); err != nil {
		log.Fatalf("ensure schema table: %v", err)
	}

	applied, err := m.Up(ctx)
	if err != nil {
		log.Fatalf("up: %v", err)
	}
	fmt.Printf("applied versions: %v\n", applied)

	status, err := m.Status(ctx)
	if err != nil {
		log.Fatalf("status: %v", err)
	}
	for _, s := range status {
		fmt.Printf("  v%d %-25s applied=%v at=%s\n", s.Version, s.Name, s.Applied, s.AppliedAt)
	}

	reverted, err := m.Down(ctx, 1)
	if err != nil {
		// Expected once you implement Down correctly: version 2 has no Down
		// script, so reverting it must fail with ErrNoDownScript rather than
		// silently skipping it.
		if errors.Is(err, ErrNoDownScript) {
			fmt.Printf("down refused as expected: %v\n", err)
		} else {
			log.Fatalf("down: %v", err)
		}
	} else {
		fmt.Printf("reverted versions: %v\n", reverted)
	}
}
