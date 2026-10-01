// Package repository is the reference implementation of Problem 09: a
// database/sql repository layer over modernc.org/sqlite (pure-Go, no cgo)
// for a simple accounts domain. Read the header comment in
// ../explanation/09_database_repository_layer_explanation.go first — it has
// the full spec, the ":memory:" + connection-pool footgun writeup, and the
// rationale this file builds on.
package repository

import (
	"context"
	"database/sql"
	"errors"
	"fmt"

	_ "modernc.org/sqlite" // registers the "sqlite" driver name
)

// Account is one row of the accounts table. Balance is integer cents to
// avoid float rounding hazards with money.
type Account struct {
	ID      int64
	Owner   string
	Balance int64
}

// ErrNotFound is returned (wrapped) by any lookup-by-ID method that found
// no matching row. Callers use errors.Is(err, ErrNotFound); sql.ErrNoRows
// never escapes this package directly.
var ErrNotFound = errors.New("repository: account not found")

// Repository wraps *sql.DB and the prepared statements this package reuses
// across calls.
type Repository struct {
	db *sql.DB

	getByIDStmt *sql.Stmt
}

// Open opens dsn with the "sqlite" driver, verifies connectivity, tunes the
// connection pool, ensures the schema exists, and prepares reusable
// statements.
//
// Step 1: sql.Open + PingContext. sql.Open never actually dials/opens the
// file — it just validates the driver name and DSN string are well-formed
// and returns a *sql.DB wrapping a lazy pool. PingContext forces the first
// real connection attempt right here, so a bad path, permissions problem,
// or corrupt file fails loudly at startup instead of on some unlucky
// request's first query.
func Open(ctx context.Context, dsn string) (*Repository, error) {
	db, err := sql.Open("sqlite", dsn)
	if err != nil {
		return nil, fmt.Errorf("repository: open %q: %w", dsn, err)
	}

	if err := db.PingContext(ctx); err != nil {
		db.Close()
		return nil, fmt.Errorf("repository: ping %q: %w", dsn, err)
	}

	// Step 2: pool tuning.
	//
	// SetMaxOpenConns(1) here is deliberate and specific to SQLite, not a
	// generic default: SQLite serializes writers at the file-lock level
	// regardless of how many connections database/sql hands out (a
	// second writer just blocks on SQLITE_BUSY until the first commits or
	// the busy_timeout fires), so a pool of many connections mostly buys
	// you concurrent READERS, at the cost of exactly the ":memory:"
	// footgun described in the package doc when the DSN is ":memory:".
	// For a FILE-based DSN (what this package's tests and any real
	// deployment of this package should use), a pool of 1 avoids
	// SQLITE_BUSY errors entirely by fully serializing access in-process,
	// trading a little throughput for zero busy-retry logic — a
	// reasonable default for a small embedded-style service. A
	// higher-throughput service fronting SQLite would instead keep a
	// larger pool and add BUSY-retry with backoff (see Problem 10's
	// retryable-serialization-failure handling for the general pattern);
	// we keep it simple and correct here.
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)
	// No SetConnMaxLifetime: a local SQLite file connection doesn't go
	// stale the way a TCP connection to a remote Postgres does (no
	// firewall/LB idle-connection reaping to defend against), so there's
	// nothing this setting buys here — worth a comment specifically
	// because omitting a pool setting a reviewer expects to see should
	// look deliberate, not forgotten.

	const schema = `
CREATE TABLE IF NOT EXISTS accounts (
	id      INTEGER PRIMARY KEY AUTOINCREMENT,
	owner   TEXT    NOT NULL,
	balance INTEGER NOT NULL
);`
	if _, err := db.ExecContext(ctx, schema); err != nil {
		db.Close()
		return nil, fmt.Errorf("repository: create schema: %w", err)
	}

	// Step 3: prepare the hot-path statement. GetAccount is the query most
	// likely to be called at high frequency (balance checks), so it's
	// worth the one-time prepare cost; the other methods use ad-hoc
	// ExecContext/QueryContext calls since preparing every single query
	// unconditionally adds a statement-lifecycle to manage for marginal
	// benefit on low-frequency paths (CreateAccount, DeleteAccount).
	getByIDStmt, err := db.PrepareContext(ctx, `SELECT id, owner, balance FROM accounts WHERE id = ?`)
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("repository: prepare getByID: %w", err)
	}

	return &Repository{db: db, getByIDStmt: getByIDStmt}, nil
}

// Close releases the prepared statement and the underlying *sql.DB. Safe
// to call more than once: sql.DB.Close and sql.Stmt.Close are both
// documented as idempotent by database/sql, so no extra guard is needed
// here beyond what the standard library already guarantees.
func (r *Repository) Close() error {
	stmtErr := r.getByIDStmt.Close()
	dbErr := r.db.Close()
	return errors.Join(stmtErr, dbErr)
}

// CreateAccount inserts a new account and returns it with its assigned ID.
//
// We use ExecContext (not QueryContext) for an INSERT since we only need
// the generated ID, not a result set — result.LastInsertId() reads back
// SQLite's rowid, which the `INTEGER PRIMARY KEY AUTOINCREMENT` column
// above aliases directly.
func (r *Repository) CreateAccount(ctx context.Context, owner string, initialBalanceCents int64) (Account, error) {
	res, err := r.db.ExecContext(ctx,
		`INSERT INTO accounts (owner, balance) VALUES (?, ?)`, owner, initialBalanceCents)
	if err != nil {
		return Account{}, fmt.Errorf("repository: create account for %q: %w", owner, err)
	}
	id, err := res.LastInsertId()
	if err != nil {
		return Account{}, fmt.Errorf("repository: read last insert id: %w", err)
	}
	return Account{ID: id, Owner: owner, Balance: initialBalanceCents}, nil
}

// GetAccount fetches one account by ID. Returns an error satisfying
// errors.Is(err, ErrNotFound) if no such account exists.
func (r *Repository) GetAccount(ctx context.Context, id int64) (Account, error) {
	var a Account
	err := r.getByIDStmt.QueryRowContext(ctx, id).Scan(&a.ID, &a.Owner, &a.Balance)
	if errors.Is(err, sql.ErrNoRows) {
		// Wrap our own ErrNotFound rather than letting sql.ErrNoRows
		// leak out: callers of this package should never need to import
		// database/sql just to check "did the lookup fail because it
		// doesn't exist" — that's an implementation detail of how we
		// store data, not part of this package's contract.
		return Account{}, fmt.Errorf("repository: get account %d: %w", id, ErrNotFound)
	}
	if err != nil {
		return Account{}, fmt.Errorf("repository: get account %d: %w", id, err)
	}
	return a, nil
}

// ListAccounts returns every account whose owner matches ownerLike (a SQL
// LIKE pattern, e.g. "alice%"), or every account if ownerLike == "".
//
// One query handles both cases via a "WHERE ? = empty-string OR owner LIKE
// ?" predicate rather than branching into two separate query strings: it
// keeps the SQL (and its plan) in one place, and SQLite's query planner
// handles the constant empty-string branch cheaply. The alternative (two
// prepared query strings) is equally valid and arguably reads slightly more
// explicitly — a matter of taste for a query this simple.
func (r *Repository) ListAccounts(ctx context.Context, ownerLike string) ([]Account, error) {
	rows, err := r.db.QueryContext(ctx,
		`SELECT id, owner, balance FROM accounts WHERE ? = '' OR owner LIKE ? ORDER BY id`,
		ownerLike, ownerLike)
	if err != nil {
		return nil, fmt.Errorf("repository: list accounts: %w", err)
	}
	defer rows.Close()

	var accounts []Account
	for rows.Next() {
		var a Account
		if err := rows.Scan(&a.ID, &a.Owner, &a.Balance); err != nil {
			return nil, fmt.Errorf("repository: scan account row: %w", err)
		}
		accounts = append(accounts, a)
	}
	// rows.Err() surfaces any error encountered while advancing the
	// result set (e.g. the underlying connection dropped mid-stream) that
	// would NOT show up as a Scan error or a false return from Next() by
	// itself — checking it is mandatory, not defensive paranoia.
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("repository: iterate accounts: %w", err)
	}
	return accounts, nil
}

// UpdateBalance sets id's balance to newBalanceCents directly (no
// optimistic locking — see Problem 10). Returns ErrNotFound if id doesn't
// exist.
func (r *Repository) UpdateBalance(ctx context.Context, id int64, newBalanceCents int64) error {
	res, err := r.db.ExecContext(ctx,
		`UPDATE accounts SET balance = ? WHERE id = ?`, newBalanceCents, id)
	if err != nil {
		return fmt.Errorf("repository: update balance for account %d: %w", id, err)
	}
	// database/sql does NOT turn "matched zero rows" into an error for
	// UPDATE/DELETE — an UPDATE against a nonexistent id "succeeds" with
	// RowsAffected() == 0. We must check this explicitly to distinguish
	// "updated" from "there was nothing to update".
	n, err := res.RowsAffected()
	if err != nil {
		return fmt.Errorf("repository: read rows affected for account %d: %w", id, err)
	}
	if n == 0 {
		return fmt.Errorf("repository: update balance for account %d: %w", id, ErrNotFound)
	}
	return nil
}

// DeleteAccount removes id. Returns ErrNotFound if id doesn't exist.
func (r *Repository) DeleteAccount(ctx context.Context, id int64) error {
	res, err := r.db.ExecContext(ctx, `DELETE FROM accounts WHERE id = ?`, id)
	if err != nil {
		return fmt.Errorf("repository: delete account %d: %w", id, err)
	}
	n, err := res.RowsAffected()
	if err != nil {
		return fmt.Errorf("repository: read rows affected for account %d: %w", id, err)
	}
	if n == 0 {
		return fmt.Errorf("repository: delete account %d: %w", id, ErrNotFound)
	}
	return nil
}

/*
BEST PRACTICES DEMONSTRATED
  - Every method takes ctx and uses the *Context database/sql variant —
    no bare Query/Exec/QueryRow anywhere, so a caller's timeout or
    cancellation always actually reaches the database driver.
  - PingContext in Open() converts "unreachable/misconfigured database"
    from a random-first-request failure into a fail-fast startup error.
  - sql.ErrNoRows is translated to a package-level ErrNotFound at the
    boundary — callers never need to know this package uses database/sql
    internally, let alone SQLite specifically.
  - RowsAffected() is checked after every UPDATE/DELETE, since
    database/sql has no other way to signal "matched nothing".
  - rows.Err() is checked after every Next()-loop, catching iteration-time
    errors that Scan/Next alone would miss.
  - Close() is safe to call twice by relying on the standard library's own
    idempotency guarantees for sql.DB.Close and sql.Stmt.Close, rather than
    adding a redundant sync.Once that would just duplicate what the
    library already promises.

ALTERNATIVE APPROACHES / TRADE-OFFS
  - SetMaxOpenConns(1) trades throughput for correctness-and-simplicity
    with SQLite. A read-heavy service could instead allow more open
    connections (SQLite supports concurrent readers with WAL mode:
    `PRAGMA journal_mode=WAL`) while still serializing writers via
    SQLITE_BUSY + retry-with-backoff — meaningfully more complex, and out
    of scope for this problem, but the natural next step for a real
    service (see Problem 10's retry-on-serialization-failure pattern,
    which generalizes directly to SQLITE_BUSY retries).
  - Preparing every statement up front (including CreateAccount, List,
    Update, Delete) instead of just GetAccount: marginally faster on
    steady-state throughput, but requires the Repository to track and
    Close N statements instead of one, and re-Prepare after any schema
    migration — the trade favors "prepare only your hottest, simplest
    queries" for a small repository like this one.
  - A single `WHERE ? = '' OR owner LIKE ?` query for ListAccounts vs two
    separate SQL strings branched on ownerLike == "": one query is less
    code to maintain; two queries let each be independently indexable/
    EXPLAIN-analyzed without the OR obscuring the planner's choice. For a
    table this size either is fine; the OR-based version is chosen here to
    keep the method to one query path.

TESTING NOTES
  - Every test opens its own SQLite database at a t.TempDir()-rooted file
    path (never ":memory:" with default pool settings) — this is what
    keeps tests hermetic and safe to run with -parallel, per the footgun
    write-up in the explanation file.
  - Because SetMaxOpenConns(1) is set inside Open() itself, the
    ":memory:" footgun is actually structurally impossible to hit through
    this package's own Open() even if a caller passed ":memory:" — but
    the tests still use a temp file, both to exercise the realistic path
    a real deployment would take and to make that defense-in-depth
    explicit rather than incidental.
  - `go test -race ./09_database_repository_layer/...` is run even though
    MaxOpenConns(1) serializes DB access, because the test suite itself
    launches concurrent goroutines calling Repository methods to prove
    there's no *Go-level* data race in this package's own code (as opposed
    to relying entirely on SQLite's file locking for correctness).

FAILURE MODES TO KNOW ABOUT
  - SQLITE_BUSY: with MaxOpenConns(1) this package cannot generate
    cross-connection contention against itself, but a SEPARATE process (or
    a second *Repository in the same process pointed at the same file)
    writing to the same SQLite file concurrently can still hit
    SQLITE_BUSY; modernc.org/sqlite's default busy behavior/timeout
    applies and is not overridden here — a production hardening pass would
    set `PRAGMA busy_timeout` via the DSN or a post-open PRAGMA.
  - A canceled ctx mid-query returns a context-wrapped error from the
    *Context call in progress; no partial writes are left in an
    inconsistent state for the single-statement operations here (each is
    one atomic SQL statement), but a caller composing several of these
    calls together without a transaction (e.g. GetAccount then
    UpdateBalance) is NOT atomic across that pair — see Problem 10.
  - Deleting an account that other in-flight goroutines are concurrently
    reading via GetAccount is not itself an error case this package
    guards against (SQLite just returns "not found" for the delete race
    loser) — application-level referential integrity (e.g. "don't delete
    an account with pending transfers") is out of scope for this layer.
*/
