// Package txnctl is the reference implementation of Problem 10:
// optimistic locking (version column + CAS) and real transactions
// (multi-statement atomicity, retry-on-SQLITE_BUSY) over the same
// accounts domain from Problem 09. Read the header comment in
// ../explanation/10_transactions_concurrency_control_explanation.go first —
// it has the full spec and, importantly, the "SQLite has no configurable
// isolation levels" writeup this file's Transfer/BeginTx usage depends on.
package txnctl

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"math/rand"
	"time"

	sqlitedrv "modernc.org/sqlite" // non-blank: we need *sqlitedrv.Error for isRetryable
)

// Account is one row of the accounts table, carrying an optimistic-lock
// version alongside the balance-in-cents from Problem 09.
type Account struct {
	ID      int64
	Owner   string
	Balance int64
	Version int64
}

// ErrNotFound mirrors Problem 09: returned (wrapped) whenever a lookup by ID
// finds no row.
var ErrNotFound = errors.New("txnctl: account not found")

// ErrVersionConflict is returned by UpdateBalanceCAS when the row exists but
// its version no longer matches the caller's expected version.
var ErrVersionConflict = errors.New("txnctl: version conflict")

// ErrInsufficientFunds is returned by Transfer when the source account's
// balance is less than the requested amount. A business-rule failure, not a
// concurrency one — WithRetry must never retry it.
var ErrInsufficientFunds = errors.New("txnctl: insufficient funds")

// sqliteBusyCode is SQLITE_BUSY's numeric result code (5). Hardcoded with a
// comment rather than importing the internal modernc.org/sqlite/lib package
// for a single constant — that package is an implementation detail of the
// driver, not part of its public API surface.
const sqliteBusyCode = 5

// Repository wraps *sql.DB for the accounts-with-versioning domain. Unlike
// Problem 09, no package-level *sql.Stmt is prepared for the CAS/Transfer
// paths: those run inside caller-scoped transactions (tx.ExecContext), so a
// pool-level prepared statement wouldn't apply to them anyway.
type Repository struct {
	db *sql.DB
}

// Open opens dsn, tunes the pool, ensures the versioned schema exists, and
// returns a ready *Repository.
//
// Step 1: sql.Open + PingContext, identical rationale to Problem 09 — fail
// fast on a bad DSN/unreachable file at startup rather than on the first
// query.
func Open(ctx context.Context, dsn string) (*Repository, error) {
	db, err := sql.Open("sqlite", dsn)
	if err != nil {
		return nil, fmt.Errorf("txnctl: open %q: %w", dsn, err)
	}
	if err := db.PingContext(ctx); err != nil {
		db.Close()
		return nil, fmt.Errorf("txnctl: ping %q: %w", dsn, err)
	}

	// Step 2: pool tuning. SetMaxOpenConns(1) is the same reasoning as
	// Problem 09: SQLite serializes writers regardless of how many
	// connections the pool hands out, so a pool of 1 fully serializes this
	// PROCESS's own access and sidesteps SQLITE_BUSY entirely for
	// same-process callers. It does NOT make the retry machinery below
	// pointless, though: WithRetry/isRetryable exist for the general case
	// of a second process (or a differently-configured Repository) writing
	// to the same file concurrently, which MaxOpenConns(1) cannot prevent.
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)

	const schema = `
CREATE TABLE IF NOT EXISTS accounts (
	id      INTEGER PRIMARY KEY AUTOINCREMENT,
	owner   TEXT    NOT NULL,
	balance INTEGER NOT NULL,
	version INTEGER NOT NULL DEFAULT 1
);`
	if _, err := db.ExecContext(ctx, schema); err != nil {
		db.Close()
		return nil, fmt.Errorf("txnctl: create schema: %w", err)
	}

	return &Repository{db: db}, nil
}

// Close releases the underlying *sql.DB. Safe to call more than once
// (sql.DB.Close is documented idempotent).
func (r *Repository) Close() error {
	return r.db.Close()
}

// CreateAccount inserts a new account at version 1.
func (r *Repository) CreateAccount(ctx context.Context, owner string, initialBalanceCents int64) (Account, error) {
	res, err := r.db.ExecContext(ctx,
		`INSERT INTO accounts (owner, balance, version) VALUES (?, ?, 1)`, owner, initialBalanceCents)
	if err != nil {
		return Account{}, fmt.Errorf("txnctl: create account for %q: %w", owner, err)
	}
	id, err := res.LastInsertId()
	if err != nil {
		return Account{}, fmt.Errorf("txnctl: read last insert id: %w", err)
	}
	return Account{ID: id, Owner: owner, Balance: initialBalanceCents, Version: 1}, nil
}

// GetAccount fetches one account (including its current version) by ID.
// Returns an error satisfying errors.Is(err, ErrNotFound) if no such
// account exists.
func (r *Repository) GetAccount(ctx context.Context, id int64) (Account, error) {
	return getAccount(ctx, r.db, id)
}

// getAccount is factored out of GetAccount so both the top-level pool
// (*sql.DB) and an in-flight transaction (*sql.Tx) can share the exact same
// query/scan logic — Transfer needs the latter to read both accounts inside
// its transaction.
func getAccount(ctx context.Context, q interface {
	QueryRowContext(context.Context, string, ...any) *sql.Row
}, id int64) (Account, error) {
	var a Account
	err := q.QueryRowContext(ctx,
		`SELECT id, owner, balance, version FROM accounts WHERE id = ?`, id,
	).Scan(&a.ID, &a.Owner, &a.Balance, &a.Version)
	if errors.Is(err, sql.ErrNoRows) {
		return Account{}, fmt.Errorf("txnctl: get account %d: %w", id, ErrNotFound)
	}
	if err != nil {
		return Account{}, fmt.Errorf("txnctl: get account %d: %w", id, err)
	}
	return a, nil
}

// UpdateBalanceCAS performs a compare-and-swap update: it writes
// newBalanceCents (and bumps the version) only if the row's CURRENT version
// still equals expectedVersion.
//
// The UPDATE's WHERE clause does the compare-and-swap atomically at the
// database level — there is no read-then-write race window here even under
// concurrent callers, because SQLite's write lock serializes the UPDATE
// itself; two concurrent UpdateBalanceCAS calls against the same row with
// the same expectedVersion cannot both succeed.
func (r *Repository) UpdateBalanceCAS(ctx context.Context, id int64, newBalanceCents int64, expectedVersion int64) error {
	res, err := r.db.ExecContext(ctx,
		`UPDATE accounts SET balance = ?, version = version + 1 WHERE id = ? AND version = ?`,
		newBalanceCents, id, expectedVersion)
	if err != nil {
		return fmt.Errorf("txnctl: CAS update account %d: %w", id, err)
	}
	n, err := res.RowsAffected()
	if err != nil {
		return fmt.Errorf("txnctl: read rows affected for account %d: %w", id, err)
	}
	if n == 1 {
		return nil
	}

	// Zero rows affected: either the id doesn't exist, or it exists but a
	// concurrent writer already moved its version. Re-query to tell the
	// two apart and give the caller an actionable, specific error.
	current, err := r.GetAccount(ctx, id)
	if errors.Is(err, ErrNotFound) {
		return fmt.Errorf("txnctl: CAS update account %d: %w", id, ErrNotFound)
	}
	if err != nil {
		return fmt.Errorf("txnctl: CAS update account %d: re-check after failed CAS: %w", id, err)
	}
	if current.Version != expectedVersion {
		return fmt.Errorf("txnctl: CAS update account %d: expected version %d, found %d: %w",
			id, expectedVersion, current.Version, ErrVersionConflict)
	}
	// Found, and version matches expectedVersion, yet the UPDATE affected
	// zero rows — shouldn't happen given SetMaxOpenConns(1) and the WHERE
	// clause above; surfaced as a generic error rather than silently
	// treated as success, in case a future pool-tuning change makes it
	// reachable.
	return fmt.Errorf("txnctl: CAS update account %d: update affected 0 rows for unknown reason (version matched)", id)
}

// Transfer atomically moves amountCents from the fromID account to the
// toID account, retrying the whole transaction (fresh BeginTx per attempt)
// on a retryable SQLITE_BUSY failure.
func (r *Repository) Transfer(ctx context.Context, fromID, toID int64, amountCents int64) error {
	const maxAttempts = 5
	return WithRetry(ctx, maxAttempts, func() error {
		return r.transferOnce(ctx, fromID, toID, amountCents)
	})
}

// transferOnce is a single (non-retried) attempt at the transfer, run
// inside one BeginTx/Commit transaction.
func (r *Repository) transferOnce(ctx context.Context, fromID, toID int64, amountCents int64) (err error) {
	// nil TxOptions here is deliberate, not an oversight: passing
	// sql.TxOptions{Isolation: sql.LevelSerializable} would be misleading
	// given modernc.org/sqlite's BeginTx ignores the Isolation field
	// entirely (see the package doc comment) — nil communicates "this
	// driver has no isolation knob to turn" more honestly than a level
	// that's silently a no-op.
	tx, err := r.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("txnctl: begin transfer transaction: %w", err)
	}
	// Rollback after a successful Commit is a documented no-op
	// (sql.ErrTxDone), safe to ignore — this defer exists to guarantee
	// cleanup on every OTHER exit path (an early return, or a panic
	// unwinding through this function).
	defer tx.Rollback() //nolint:errcheck

	// Read both accounts in a FIXED ascending-ID order regardless of the
	// fromID/toID argument order. Without this, two concurrent transfers
	// running in opposite directions between the same pair of accounts
	// (A->B and B->A) can each acquire the lock the other wants and
	// deadlock (or, on SQLite specifically, one loses with SQLITE_BUSY) —
	// a fixed global lock order eliminates that regardless of caller
	// argument order.
	lowID, highID := fromID, toID
	if lowID > highID {
		lowID, highID = highID, lowID
	}
	rows, err := tx.QueryContext(ctx,
		`SELECT id, owner, balance, version FROM accounts WHERE id IN (?, ?) ORDER BY id`,
		lowID, highID)
	if err != nil {
		return fmt.Errorf("txnctl: read accounts for transfer: %w", err)
	}
	byID := make(map[int64]Account, 2)
	for rows.Next() {
		var a Account
		if err := rows.Scan(&a.ID, &a.Owner, &a.Balance, &a.Version); err != nil {
			rows.Close()
			return fmt.Errorf("txnctl: scan account row for transfer: %w", err)
		}
		byID[a.ID] = a
	}
	if err := rows.Err(); err != nil {
		rows.Close()
		return fmt.Errorf("txnctl: iterate accounts for transfer: %w", err)
	}
	rows.Close()

	from, ok := byID[fromID]
	if !ok {
		return fmt.Errorf("txnctl: transfer from account %d: %w", fromID, ErrNotFound)
	}
	to, ok := byID[toID]
	if !ok {
		return fmt.Errorf("txnctl: transfer to account %d: %w", toID, ErrNotFound)
	}
	if from.Balance < amountCents {
		return fmt.Errorf("txnctl: transfer %d cents from account %d (balance %d): %w",
			amountCents, fromID, from.Balance, ErrInsufficientFunds)
	}

	if _, err := tx.ExecContext(ctx,
		`UPDATE accounts SET balance = balance - ?, version = version + 1 WHERE id = ?`,
		amountCents, fromID); err != nil {
		return fmt.Errorf("txnctl: debit account %d: %w", fromID, err)
	}
	if _, err := tx.ExecContext(ctx,
		`UPDATE accounts SET balance = balance + ?, version = version + 1 WHERE id = ?`,
		amountCents, toID); err != nil {
		return fmt.Errorf("txnctl: credit account %d: %w", toID, err)
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("txnctl: commit transfer: %w", err)
	}
	_ = to // to.Balance intentionally unused beyond existence-check above
	return nil
}

// WithRetry calls fn, retrying with jittered exponential backoff (bounded
// by ctx) while fn's error is retryable per isRetryable, up to maxAttempts
// total calls to fn. Returns the last error if every attempt is exhausted,
// or returns immediately (no retry, no sleep) on a nil or non-retryable
// error.
func WithRetry(ctx context.Context, maxAttempts int, fn func() error) error {
	if maxAttempts < 1 {
		maxAttempts = 1
	}

	var lastErr error
	for attempt := 0; attempt < maxAttempts; attempt++ {
		lastErr = fn()
		if lastErr == nil {
			return nil
		}
		if !isRetryable(lastErr) {
			return lastErr
		}
		if attempt == maxAttempts-1 {
			break // don't sleep after the final attempt
		}

		// Jittered exponential backoff: base 5ms doubling per attempt,
		// capped at 200ms, plus up to 50% random jitter so many
		// concurrently-retrying callers don't all wake up and collide on
		// the SQLite write lock again in lockstep.
		base := 5 * time.Millisecond << uint(attempt)
		if base > 200*time.Millisecond {
			base = 200 * time.Millisecond
		}
		jitter := time.Duration(rand.Int63n(int64(base)/2 + 1))
		wait := base + jitter

		timer := time.NewTimer(wait)
		select {
		case <-ctx.Done():
			timer.Stop()
			return fmt.Errorf("txnctl: retry backoff interrupted: %w", ctx.Err())
		case <-timer.C:
		}
	}
	return fmt.Errorf("txnctl: exhausted %d attempts: %w", maxAttempts, lastErr)
}

// isRetryable reports whether err represents SQLITE_BUSY — a transient
// "someone else holds the write lock right now" condition worth retrying —
// as opposed to a permanent failure (bad SQL, ErrNotFound,
// ErrInsufficientFunds, a canceled context) that retrying cannot fix.
func isRetryable(err error) bool {
	var sqliteErr *sqlitedrv.Error
	if errors.As(err, &sqliteErr) {
		return sqliteErr.Code() == sqliteBusyCode
	}
	return false
}

/*
BEST PRACTICES DEMONSTRATED
  - UpdateBalanceCAS folds the compare-and-swap into the UPDATE's WHERE
    clause itself (atomic at the database level) rather than doing a
    SELECT-then-compare-in-Go-then-UPDATE, which would reopen the exact
    race window optimistic locking exists to close.
  - Transfer reads both accounts in a fixed, argument-order-independent
    lock sequence (ascending ID), eliminating a whole class of
    opposite-direction-transfer deadlocks by construction rather than by
    convention callers have to remember.
  - `defer tx.Rollback()` immediately after BeginTx guarantees cleanup on
    every exit path; its error is deliberately ignored because
    Rollback-after-Commit returning sql.ErrTxDone is the expected,
    harmless case on the success path.
  - isRetryable distinguishes SQLITE_BUSY (retry) from every other error
    (don't retry) via the driver's typed *sqlite.Error, not a fragile
    err.Error() substring match against driver-specific message text.
  - WithRetry's backoff is ctx-aware (select on ctx.Done(), never a bare
    time.Sleep) so a caller's timeout/cancellation actually interrupts a
    pending retry instead of being silently ignored during the sleep.
  - Business-rule failures (ErrInsufficientFunds, ErrNotFound) propagate on
    the FIRST attempt — WithRetry only retries the specific transient
    condition it knows how to fix.

ALTERNATIVE APPROACHES / TRADE-OFFS
  - Pessimistic locking (`BEGIN IMMEDIATE` + hold the write lock for the
    whole read-modify-write) instead of optimistic CAS for
    UpdateBalanceCAS: simpler reasoning (no conflict to detect after the
    fact), but every caller serializes on the lock even when conflicts are
    rare — optimistic locking trades a small chance of a caller-visible
    retry for not blocking anyone in the common case.
  - `_txlock=immediate` in the DSN (acquiring the write lock at BEGIN
    rather than lazily at the first write) is NOT set here — Transfer's
    BeginTx uses SQLite's default deferred mode. That's a deliberate choice
    for this problem: WithRetry already handles the resulting SQLITE_BUSY
    on write-upgrade, so the extra DSN tuning is presented as a stretch
    goal rather than baked in, to keep the retry path exercised by the
    tests instead of mostly avoided.
  - A single `SELECT ... WHERE id IN (?, ?)` for both Transfer accounts
    instead of two sequential SELECTs: one round trip, and ORDER BY gives
    the lock ordering "for free" instead of requiring the caller to issue
    the two SELECTs themselves in the right sequence.

TESTING NOTES
  - Every test uses a t.TempDir()-rooted file DSN, same footgun rationale
    as Problem 09.
  - The concurrent-transfer stress test launches many goroutines
    transferring in BOTH directions between the same account pair
    simultaneously and asserts the total balance across the system is
    unchanged afterward and no balance goes negative — the property that
    actually matters, rather than asserting exact per-goroutine outcomes
    which depend on scheduling.
  - `go test -race` matters here independent of SQLite's own file-level
    locking: it proves this package's own Go code (the byID map built from
    rows.Scan, the WithRetry loop) has no data race, which SQLite
    serializing the underlying writes would not, by itself, guarantee.

FAILURE MODES TO KNOW ABOUT
  - WithRetry's maxAttempts is a hard cap: under sustained heavy write
    contention from OTHER processes/connections against the same file
    (this package's own MaxOpenConns(1) can't cause self-contention),
    Transfer can still legitimately exhaust its retries and return the
    last SQLITE_BUSY-wrapped error — callers must handle that as a
    "try again later" signal, not assume Transfer always eventually
    succeeds.
  - A canceled ctx during the backoff sleep surfaces as a wrapped
    ctx.Err(), not as the underlying SQLITE_BUSY — callers checking
    errors.Is(err, context.Canceled/DeadlineExceeded) still work correctly
    through that wrap.
  - UpdateBalanceCAS's "version matched but 0 rows affected" branch is
    reachable only under a driver/pool misconfiguration this package's own
    Open() prevents (MaxOpenConns(1)); it's kept as a loud error rather
    than silently treated as either success or ErrVersionConflict,
    specifically so it would be noticed if that invariant ever changed.
*/
