/*
Problem 11 — Migrations & Schema Management (solution)
=======================================================

Reference implementation of the versioned migration runner specified in
explanation/11_migrations_schema_management_explanation.go. Package name
differs (`migrations` vs `main`) because this is the library-style,
directly-testable half of the exercise — see that file's header for the full
spec, acceptance criteria, and design rationale; comments here focus on the
"how" and the trade-offs made along the way.
*/
package migrations

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"sort"
	"time"
)

// Migration is one versioned, reversible schema change.
type Migration struct {
	Version int
	Name    string
	Up      string
	Down    string // empty means "no down script" — irreversible by design
}

// MigrationStatus reports whether a known migration has been applied.
type MigrationStatus struct {
	Version   int
	Name      string
	Applied   bool
	AppliedAt time.Time
}

// Sentinel errors. Wrapped with %w wherever a driver error is the direct
// cause, so callers can errors.Is/As through to both these and the
// underlying *sqlite.Error.
var (
	ErrNoDownScript   = errors.New("migrations: no down script for this version")
	ErrUnknownVersion = errors.New("migrations: unknown target version")
)

// Migrator applies and reverts a versioned set of migrations against db,
// tracking applied state in a schema_migrations table that lives in the same
// database as the schema it manages — that's what lets bookkeeping and
// schema change commit or roll back together in one transaction.
type Migrator struct {
	db         *sql.DB
	migrations []Migration // sorted ascending by Version
}

// NewMigrator validates the migration set (positive, unique versions) and
// returns a Migrator with them sorted ascending. Validation happens once at
// construction — a malformed migration set is a programmer error you want to
// catch at process startup, not three migrations into a partially-applied
// Up().
func NewMigrator(db *sql.DB, migrations []Migration) (*Migrator, error) {
	seen := make(map[int]struct{}, len(migrations))
	sorted := make([]Migration, len(migrations))
	copy(sorted, migrations)

	for _, mig := range sorted {
		if mig.Version <= 0 {
			return nil, fmt.Errorf("migrations: migration %q has non-positive version %d", mig.Name, mig.Version)
		}
		if _, dup := seen[mig.Version]; dup {
			return nil, fmt.Errorf("migrations: duplicate version %d", mig.Version)
		}
		seen[mig.Version] = struct{}{}
	}

	sort.Slice(sorted, func(i, j int) bool { return sorted[i].Version < sorted[j].Version })

	return &Migrator{db: db, migrations: sorted}, nil
}

// EnsureSchemaTable creates the bookkeeping table if absent. IF NOT EXISTS
// makes this idempotent by construction — safe to call on every process
// boot ahead of Up(), which is exactly how it's meant to be used.
func (m *Migrator) EnsureSchemaTable(ctx context.Context) error {
	const ddl = `
		CREATE TABLE IF NOT EXISTS schema_migrations (
			version    INTEGER PRIMARY KEY,
			name       TEXT NOT NULL,
			applied_at TIMESTAMP NOT NULL
		);`
	if _, err := m.db.ExecContext(ctx, ddl); err != nil {
		return fmt.Errorf("migrations: ensure schema table: %w", err)
	}
	return nil
}

// AppliedVersions reads the bookkeeping table into a version->appliedAt map.
// An empty map (not an error) is the correct answer for a fresh database.
func (m *Migrator) AppliedVersions(ctx context.Context) (map[int]time.Time, error) {
	rows, err := m.db.QueryContext(ctx, `SELECT version, applied_at FROM schema_migrations`)
	if err != nil {
		return nil, fmt.Errorf("migrations: query applied versions: %w", err)
	}
	defer rows.Close()

	applied := make(map[int]time.Time)
	for rows.Next() {
		var v int
		var at time.Time
		if err := rows.Scan(&v, &at); err != nil {
			return nil, fmt.Errorf("migrations: scan applied version: %w", err)
		}
		applied[v] = at
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("migrations: iterate applied versions: %w", err)
	}
	return applied, nil
}

// applyOne runs a single migration's Up SQL and its bookkeeping INSERT in
// one transaction. This is the crux of the whole exercise: both statements
// go through the SAME *sql.Tx, so a crash or error between them is
// impossible to observe from outside — either both landed or neither did.
func (m *Migrator) applyOne(ctx context.Context, mig Migration) error {
	tx, err := m.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("migrations: begin tx for v%d: %w", mig.Version, err)
	}
	// Rollback on an already-committed tx is a documented no-op, so this
	// defer is safe on every return path including the success one.
	defer tx.Rollback()

	if _, err := tx.ExecContext(ctx, mig.Up); err != nil {
		return fmt.Errorf("migrations: apply v%d %q: %w", mig.Version, mig.Name, err)
	}

	const insert = `INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)`
	if _, err := tx.ExecContext(ctx, insert, mig.Version, mig.Name, time.Now().UTC()); err != nil {
		return fmt.Errorf("migrations: record v%d %q: %w", mig.Version, mig.Name, err)
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("migrations: commit v%d %q: %w", mig.Version, mig.Name, err)
	}
	return nil
}

// revertOne mirrors applyOne for the reverse direction: the Down SQL and the
// bookkeeping DELETE happen in the same transaction.
func (m *Migrator) revertOne(ctx context.Context, mig Migration) error {
	if mig.Down == "" {
		return fmt.Errorf("%w: v%d %q", ErrNoDownScript, mig.Version, mig.Name)
	}

	tx, err := m.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("migrations: begin tx for down v%d: %w", mig.Version, err)
	}
	defer tx.Rollback()

	if _, err := tx.ExecContext(ctx, mig.Down); err != nil {
		return fmt.Errorf("migrations: revert v%d %q: %w", mig.Version, mig.Name, err)
	}

	const del = `DELETE FROM schema_migrations WHERE version = ?`
	if _, err := tx.ExecContext(ctx, del, mig.Version); err != nil {
		return fmt.Errorf("migrations: unrecord v%d %q: %w", mig.Version, mig.Name, err)
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("migrations: commit down v%d %q: %w", mig.Version, mig.Name, err)
	}
	return nil
}

// Up applies every pending migration in ascending order. Returns the
// versions actually applied — an empty, non-nil slice if nothing was
// pending, so calling Up twice in a row is a safe, observable no-op.
func (m *Migrator) Up(ctx context.Context) ([]int, error) {
	return m.upTo(ctx, nil)
}

// UpTo applies pending migrations up to and including target.
func (m *Migrator) UpTo(ctx context.Context, target int) ([]int, error) {
	if !m.hasVersion(target) {
		return nil, fmt.Errorf("%w: %d", ErrUnknownVersion, target)
	}
	return m.upTo(ctx, &target)
}

// upTo is the shared engine behind Up/UpTo. target == nil means "apply
// everything pending".
func (m *Migrator) upTo(ctx context.Context, target *int) ([]int, error) {
	applied, err := m.AppliedVersions(ctx)
	if err != nil {
		return nil, err
	}

	result := make([]int, 0, len(m.migrations))
	for _, mig := range m.migrations {
		if target != nil && mig.Version > *target {
			break
		}
		if _, ok := applied[mig.Version]; ok {
			continue
		}
		if err := m.applyOne(ctx, mig); err != nil {
			// Stop on first failure: everything applied so far in this call
			// stays applied (each was its own committed transaction), the
			// failed migration's transaction rolled back cleanly, and
			// nothing after it was attempted.
			return result, err
		}
		result = append(result, mig.Version)
	}
	return result, nil
}

// Down reverts the `steps` most recently applied migrations, newest first.
func (m *Migrator) Down(ctx context.Context, steps int) ([]int, error) {
	if steps <= 0 {
		return []int{}, nil
	}

	applied, err := m.AppliedVersions(ctx)
	if err != nil {
		return nil, err
	}

	// Walk the known migration set in descending version order, skipping
	// anything not applied, taking the first `steps` matches. This — rather
	// than sorting the applied map's keys — guarantees we revert in the
	// exact reverse of the order migrations were defined/applied in.
	descending := m.descendingMigrations()

	result := make([]int, 0, steps)
	for _, mig := range descending {
		if len(result) == steps {
			break
		}
		if _, ok := applied[mig.Version]; !ok {
			continue
		}
		if err := m.revertOne(ctx, mig); err != nil {
			return result, err
		}
		result = append(result, mig.Version)
	}
	return result, nil
}

// DownTo reverts every applied migration with version > target.
func (m *Migrator) DownTo(ctx context.Context, target int) ([]int, error) {
	if !m.hasVersion(target) {
		return nil, fmt.Errorf("%w: %d", ErrUnknownVersion, target)
	}

	applied, err := m.AppliedVersions(ctx)
	if err != nil {
		return nil, err
	}

	result := make([]int, 0)
	for _, mig := range m.descendingMigrations() {
		if mig.Version <= target {
			break
		}
		if _, ok := applied[mig.Version]; !ok {
			continue
		}
		if err := m.revertOne(ctx, mig); err != nil {
			return result, err
		}
		result = append(result, mig.Version)
	}
	return result, nil
}

// Status reports every known migration and its applied state, version order.
func (m *Migrator) Status(ctx context.Context) ([]MigrationStatus, error) {
	applied, err := m.AppliedVersions(ctx)
	if err != nil {
		return nil, err
	}

	statuses := make([]MigrationStatus, 0, len(m.migrations))
	for _, mig := range m.migrations {
		at, ok := applied[mig.Version]
		statuses = append(statuses, MigrationStatus{
			Version:   mig.Version,
			Name:      mig.Name,
			Applied:   ok,
			AppliedAt: at, // zero value when !ok, matching the spec
		})
	}
	return statuses, nil
}

// hasVersion reports whether v is a version present in the migration set.
func (m *Migrator) hasVersion(v int) bool {
	for _, mig := range m.migrations {
		if mig.Version == v {
			return true
		}
	}
	return false
}

// descendingMigrations returns a copy of the migration set sorted by
// version descending, for the Down-direction walks.
func (m *Migrator) descendingMigrations() []Migration {
	out := make([]Migration, len(m.migrations))
	copy(out, m.migrations)
	sort.Slice(out, func(i, j int) bool { return out[i].Version > out[j].Version })
	return out
}

/*
Best practices demonstrated here:

  - Bookkeeping and schema mutation share one *sql.Tx per migration, never
    the pooled *sql.DB directly — this is the entire mechanism that makes
    "applied" and "actually changed the schema" atomic without an external
    lock file or two-phase commit.
  - Every exported method takes a context.Context and threads it through to
    every ExecContext/QueryContext call, so callers can bound migration time
    or cancel on shutdown.
  - Sentinel errors (ErrNoDownScript, ErrUnknownVersion) wrapped with %w:
    callers can errors.Is() without string-matching, while the message still
    carries the offending version for logs.
  - defer tx.Rollback() immediately after a successful BeginTx, unconditionally
    — the documented no-op-after-commit behavior of database/sql makes this
    the only cleanup you need on every early-return path.
  - NewMigrator validates the whole migration set up front (positive, unique
    versions) rather than discovering a duplicate mid-deploy.

Alternative approaches / what a production system adds on top:

  - Advisory locking: multiple replicas booting simultaneously will otherwise
    race to call Up() concurrently. A `BEGIN IMMEDIATE` against a dedicated
    single-row lock table (or, on Postgres, pg_advisory_lock) serializes
    that. This solution deliberately does not add it — the acceptance
    criteria only requires the test suite to be race-clean, not the Migrator
    to support concurrent Up() callers.
  - Checksums: golang-migrate/goose-style tools hash each migration's SQL and
    store the hash alongside the version, so a since-edited "already applied"
    migration is detected instead of silently drifting between environments.
  - Loading migrations from embedded .sql files instead of Go literals keeps
    migration authoring out of the Go build entirely — see the stretch goals
    in the explanation file.

Testing notes:

  - Tests use a real modernc.org/sqlite temp-file database rather than mocks:
    database/sql mock libraries can't exercise real transaction/rollback
    semantics, and that's precisely the behavior under test here.
  - A migration with deliberately invalid SQL is the way to test the
    "partial failure leaves the DB untouched" acceptance criterion — assert
    both the schema (e.g. a table that should NOT exist) and the bookkeeping
    table agree after the error.
  - go test -race is run even though Migrator isn't concurrent-safe by
    contract: the test suite itself (goroutines, if any, plus the SQLite
    driver's internal locking) still must be race-clean.
*/
