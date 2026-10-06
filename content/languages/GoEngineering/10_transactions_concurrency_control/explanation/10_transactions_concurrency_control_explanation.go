/*
Package txnctl — Transactions & Concurrency Control (Problem 10)

WHAT WE'RE BUILDING

The same "accounts" domain from Problem 09 (id, owner, balance-in-cents),
now with a `version` column, backed by the same modernc.org/sqlite driver
against a temp-file database. Three concurrency-safety patterns are added on
top of the plain repository from Problem 09:

 1. Optimistic locking via a version column + compare-and-swap UPDATE, for
    "read-modify-write" flows where a caller read a row, computed a new
    value, and wants to write it back only if nobody else changed the row
    in between.
 2. A real multi-statement transaction (Transfer, moving cents between two
    accounts) that must be atomic — both balances change or neither does.
 3. A generic retry-on-serialization-failure helper, because SQLite (like
    Postgres SERIALIZABLE or MySQL under certain isolation levels) can
    legitimately fail a transaction's COMMIT with a "come back later, this
    conflicted with a concurrent writer" error, and a production system is
    expected to retry that, not surface it to the caller as a hard failure.

# WHY IT MATTERS IN REAL SYSTEMS

Every service with a database eventually has to answer: "what happens when
two requests touch the same row at (almost) the same time?" There are
exactly two disciplined answers — pessimistic locking (SELECT ... FOR
UPDATE / hold a DB-level lock for the duration) and optimistic locking
(assume no conflict, detect it after the fact, retry) — and reaching for
neither (a bare read-then-write with no version check and no transaction)
is how "the balance is occasionally wrong under load" bugs get into
production. Multi-row transactions that aren't wrapped in an actual
database transaction are the other classic: a crash or error between the
debit and the credit half of a transfer either loses money or creates it.

SQLITE HAS NO CONFIGURABLE ISOLATION LEVELS (read this before writing code)

Postgres and MySQL let you request READ COMMITTED / REPEATABLE READ /
SERIALIZABLE per-transaction via `sql.TxOptions{Isolation: ...}`, and the
driver actually changes behavior. modernc.org/sqlite does NOT: its BeginTx
implementation reads only `opts.ReadOnly` — the `Isolation` field is
accepted (Go's database/sql never rejects it) but silently ignored. What
you get instead is SQLite's own transaction model:

  - A single writer at a time, full stop — SQLite locks the whole database
    file for the duration of a write transaction (WAL mode narrows this to
    "one writer, many concurrent readers" but never "many concurrent
    writers").
  - What "SERIALIZABLE-like" behavior you get comes from that single-writer
    lock, not from an isolation-level parameter — it's closer to Postgres
    SERIALIZABLE than to READ COMMITTED, but it's a structural property of
    SQLite, not something you dial up or down.
  - Whether a write transaction grabs that lock at BEGIN (`_txlock=
    immediate`) or lazily at its first actual write (`_txlock=deferred`,
    SQLite's default) is what you DO control, via a DSN query parameter.
    Deferred is the classic footgun: two transactions can both BEGIN
    successfully (both currently read-only), then both try to upgrade to a
    write lock on their first UPDATE — one wins, the other gets
    SQLITE_BUSY ("database is locked") instead of blocking indefinitely
    without a busy_timeout set. Using `_txlock=immediate` for any
    transaction you know will write moves that failure to BEGIN time,
    which is easier to reason about and retry around.

CONCEPTS COVERED
  - Optimistic locking: version column, compare-and-swap UPDATE
    (`WHERE id = ? AND version = ?`), distinguishing "no such row" from
    "row exists but version moved" by re-querying after a zero-row UPDATE.
  - Real transactions: BeginTx/Commit/Rollback, the defer-rollback-is-safe-
    after-commit pattern, ordering lock acquisition (by ascending account
    ID) to avoid a classic two-transaction deadlock.
  - Retryable failures: recognizing SQLITE_BUSY (via the driver's typed
    *sqlite.Error and its Code() method) as retryable, everything else as
    not, and retrying with jittered exponential backoff bounded by ctx.
  - DSN tuning for write-heavy SQLite: `_txlock=immediate` and
    `_pragma=busy_timeout(...)`.

REQUIREMENTS / SPEC

	type Account struct {
	    ID      int64
	    Owner   string
	    Balance int64 // cents
	    Version int64 // starts at 1, incremented on every successful update
	}

	type Repository struct { ... } // wraps *sql.DB

	func Open(ctx context.Context, dsn string) (*Repository, error)
	    Like Problem 09's Open, but the schema includes `version INTEGER
	    NOT NULL DEFAULT 1`, and the DSN handling documents (or applies,
	    your choice — see TODO) `_txlock=immediate` for this package's
	    write-transaction-heavy workload.

	func (r *Repository) Close() error

	func (r *Repository) CreateAccount(ctx context.Context, owner string, initialBalanceCents int64) (Account, error)
	func (r *Repository) GetAccount(ctx context.Context, id int64) (Account, error)
	    Not found -> ErrNotFound (same contract as Problem 09).

	func (r *Repository) UpdateBalanceCAS(ctx context.Context, id int64, newBalanceCents int64, expectedVersion int64) error
	    UPDATE ... SET balance = ?, version = version + 1
	    WHERE id = ? AND version = ?
	    - 1 row affected -> success.
	    - 0 rows affected -> re-query the row: if it doesn't exist, return
	      ErrNotFound; if it exists but its version != expectedVersion,
	      return ErrVersionConflict (the caller should re-read and retry).

	func (r *Repository) Transfer(ctx context.Context, fromID, toID int64, amountCents int64) error
	    Atomically moves amountCents from fromID to toID:
	      - Runs inside a single BeginTx/Commit transaction.
	      - Locks/reads both accounts in a FIXED order (ascending ID) to
	        avoid the deadlock where transfer(A->B) and transfer(B->A) run
	        concurrently and each holds the lock the other wants.
	      - Returns ErrInsufficientFunds (rolling back) if fromID's balance
	        < amountCents.
	      - Returns ErrNotFound (rolling back) if either account doesn't
	        exist.
	      - Retries the whole transaction (fresh BeginTx each attempt) on a
	        retryable SQLITE_BUSY failure, bounded attempts, via the
	        WithRetry helper below.

	func WithRetry(ctx context.Context, maxAttempts int, fn func() error) error
	    Calls fn(); if it returns a retryable error (see isRetryable),
	    sleeps a jittered exponential backoff (bounded by ctx) and retries,
	    up to maxAttempts total calls to fn. Returns the last error if every
	    attempt is exhausted, or immediately returns any non-retryable
	    error without retrying.

	func isRetryable(err error) bool
	    True for a SQLITE_BUSY error (errors.As into *sqlite.Error, check
	    Code() against the SQLITE_BUSY code), false otherwise. Unexported —
	    it's an implementation detail of this package's retry policy, not a
	    contract callers should depend on.

ACCEPTANCE CRITERIA
  - UpdateBalanceCAS never blind-overwrites a row another writer already
    changed: a stale expectedVersion always yields ErrVersionConflict, not
    a silently "successful" update of a value the caller didn't actually
    see.
  - Transfer is atomic under concurrent load: run many concurrent transfers
    between the same pair of accounts (both directions) and the sum of all
    balances in the system never changes and no balance goes negative.
  - Transfer acquires both accounts in ascending-ID order regardless of the
    fromID/toID argument order, so concurrent opposite-direction transfers
    cannot deadlock each other.
  - WithRetry never retries a non-retryable error (e.g. ErrInsufficientFunds
    must propagate on the FIRST attempt, not be masked by a retry loop).
  - go vet and go test -race are clean; the concurrent-transfer test in
    particular must pass reliably under -race, not just by luck.

Read the HINTS and PITFALLS at the bottom before opening the solution file.
*/
package txnctl

import (
	"context"
	"errors"
)

// Account is one row of the accounts table, now carrying an optimistic-lock
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
// its version no longer matches expectedVersion — someone else updated it
// since the caller last read it. The caller should re-read the account and
// decide whether to retry with the new version.
var ErrVersionConflict = errors.New("txnctl: version conflict")

// ErrInsufficientFunds is returned by Transfer when the source account's
// balance is less than the requested transfer amount. This is a business
// rule violation, not a concurrency failure — WithRetry must never retry it.
var ErrInsufficientFunds = errors.New("txnctl: insufficient funds")

// Repository wraps *sql.DB for the accounts-with-versioning domain.
type Repository struct {
	// TODO: hold *sql.DB. Unlike Problem 09, this package deliberately
	// does NOT prepare a package-level *sql.Stmt for CAS/Transfer, since
	// those need to run inside caller-controlled transactions
	// (tx.StmtContext or ad-hoc tx.ExecContext) rather than against the
	// pool directly.
}

// Open opens dsn, configures the pool, ensures the versioned schema exists,
// and returns a ready *Repository.
//
// IMPORTANT: read the "SQLite has no configurable isolation levels" section
// in the package doc comment above before touching BeginTx anywhere in this
// file — sql.TxOptions{Isolation: ...} is accepted but silently ignored by
// this driver.
func Open(ctx context.Context, dsn string) (*Repository, error) {
	// TODO:
	//  1. sql.Open("sqlite", dsn) + db.PingContext(ctx), same as Problem 09.
	//  2. Pool tuning: SetMaxOpenConns(1) is the same reasoning as Problem
	//     09 (SQLite serializes writers regardless; a pool of 1 avoids
	//     SQLITE_BUSY entirely for THIS process's own concurrent callers,
	//     though the retry machinery below still matters for the general
	//     case / multi-process access to the same file).
	//  3. CREATE TABLE IF NOT EXISTS accounts (..., version INTEGER NOT
	//     NULL DEFAULT 1).
	//  4. Wrap in *Repository, return.
	panic("TODO: implement Open")
}

// Close releases the repository's *sql.DB. Safe to call more than once.
func (r *Repository) Close() error {
	// TODO: db.Close() (idempotent per database/sql's own docs).
	panic("TODO: implement Close")
}

// CreateAccount inserts a new account at version 1.
func (r *Repository) CreateAccount(ctx context.Context, owner string, initialBalanceCents int64) (Account, error) {
	// TODO: same shape as Problem 09's CreateAccount, plus Version: 1 in
	// both the INSERT (implicit via the column DEFAULT) and the returned
	// Account.
	panic("TODO: implement CreateAccount")
}

// GetAccount fetches one account (including its current version) by ID.
func (r *Repository) GetAccount(ctx context.Context, id int64) (Account, error) {
	// TODO: QueryRowContext + Scan into all four fields; sql.ErrNoRows ->
	// wrapped ErrNotFound, same pattern as Problem 09.
	panic("TODO: implement GetAccount")
}

// UpdateBalanceCAS performs a compare-and-swap update: it only writes
// newBalanceCents if the row's CURRENT version still equals
// expectedVersion, and bumps the version by 1 as part of the same
// statement. See the package doc comment for the full contract, including
// how to distinguish ErrNotFound from ErrVersionConflict after a
// zero-rows-affected UPDATE.
func (r *Repository) UpdateBalanceCAS(ctx context.Context, id int64, newBalanceCents int64, expectedVersion int64) error {
	// TODO:
	//  1. res, err := db.ExecContext(ctx, `UPDATE accounts SET balance = ?,
	//     version = version + 1 WHERE id = ? AND version = ?`,
	//     newBalanceCents, id, expectedVersion)
	//  2. n, _ := res.RowsAffected(); if n == 1, success, return nil.
	//  3. If n == 0: re-query the row by id alone. Not found -> ErrNotFound.
	//     Found but Version != expectedVersion -> ErrVersionConflict. (A
	//     third case — found AND Version == expectedVersion despite the
	//     UPDATE affecting 0 rows — shouldn't happen outside a driver bug;
	//     treat it as an internal error if you want to be defensive.)
	panic("TODO: implement UpdateBalanceCAS")
}

// Transfer atomically moves amountCents from the fromID account to the
// toID account, retrying the whole transaction on a retryable SQLITE_BUSY
// failure. See the package doc comment for the full contract, in
// particular the fixed-ascending-ID lock ordering requirement.
func (r *Repository) Transfer(ctx context.Context, fromID, toID int64, amountCents int64) error {
	// TODO: WithRetry(ctx, someMaxAttempts, func() error { ...
	// one BeginTx + the transfer logic + Commit, all inside the closure so
	// a fresh transaction is started on every retry ... })
	//
	// Inside the closure:
	//  1. tx, err := db.BeginTx(ctx, nil) — nil TxOptions is fine given the
	//     isolation-level note above; document that explicitly rather than
	//     passing a misleading sql.LevelSerializable that does nothing.
	//  2. defer tx.Rollback() — calling Rollback after a successful Commit
	//     is a documented no-op error you can safely ignore; NOT calling
	//     Rollback on an early-return error path is the actual bug to
	//     avoid.
	//  3. Determine (lowID, highID) = (min(fromID, toID), max(fromID,
	//     toID)) and read/lock both rows in THAT order (two SELECTs, or a
	//     single SELECT ... WHERE id IN (?, ?) ORDER BY id — either is
	//     fine) to avoid a lock-order deadlock against a concurrent
	//     transfer running the opposite direction.
	//  4. Validate both accounts exist (ErrNotFound) and fromID's balance
	//     >= amountCents (ErrInsufficientFunds) BEFORE writing anything.
	//  5. Two UPDATEs (debit fromID, credit toID) via tx.ExecContext.
	//  6. tx.Commit().
	panic("TODO: implement Transfer")
}

// WithRetry calls fn, retrying with jittered exponential backoff (bounded
// by ctx) while fn's error is retryable per isRetryable, up to maxAttempts
// total calls. See the package doc comment for the full contract.
func WithRetry(ctx context.Context, maxAttempts int, fn func() error) error {
	// TODO: loop up to maxAttempts times; on a non-retryable error (or nil)
	// return immediately; on a retryable error, sleep a backoff duration
	// (respecting ctx cancellation via a select on ctx.Done() and a
	// time.Timer, NOT a bare time.Sleep) before the next attempt.
	panic("TODO: implement WithRetry")
}

// isRetryable reports whether err represents a transient SQLite condition
// (specifically SQLITE_BUSY) worth retrying, as opposed to a permanent
// failure (bad SQL, constraint violation, context canceled, a business
// rule like ErrInsufficientFunds) that retrying cannot fix.
func isRetryable(err error) bool {
	// TODO: errors.As(err, &sqliteErr) into *sqlite.Error (import
	// "modernc.org/sqlite" directly, not blank, to get the type), then
	// compare sqliteErr.Code() against the numeric SQLITE_BUSY code (5).
	// Hardcode the constant with a comment rather than importing the
	// internal modernc.org/sqlite/lib package for one integer.
	panic("TODO: implement isRetryable")
}

/*
HINTS
  - `defer tx.Rollback()` immediately after a successful BeginTx, before any
    other error-checking, is the standard Go database/sql idiom: Rollback
    after Commit already succeeded is documented to return sql.ErrTxDone,
    which you simply ignore (don't check its return value at all) — the
    defer exists to guarantee cleanup on every OTHER exit path (an error
    return, or even a panic).
  - `res.RowsAffected()` on the CAS UPDATE tells you the update path
    (matched-and-changed) without a second query in the success case — only
    pay for the re-query when RowsAffected() == 0.
  - A single `SELECT ... WHERE id IN (?, ?) ORDER BY id` reads both accounts
    for Transfer in one round trip AND in a deterministic order for free
    (ORDER BY), rather than two separate SELECTs you'd have to sequence
    yourself.
  - time.NewTimer + select on ctx.Done() is the ctx-aware sleep pattern —
    time.Sleep cannot be interrupted by context cancellation, which would
    make WithRetry ignore a caller's timeout while it's backing off.

COMMON PITFALLS
  - Reading both accounts for Transfer in whatever order fromID/toID happen
    to be passed, instead of a FIXED (ascending ID) order — two concurrent
    transfers in opposite directions each acquire one lock and wait for the
    other's, deadlocking (or, with SQLite specifically, one gets
    SQLITE_BUSY rather than a true deadlock, but the ordering bug is the
    same either way and is the actual thing to avoid).
  - Treating ANY error from a Transfer attempt as retryable — retrying
    ErrInsufficientFunds or ErrNotFound just wastes attempts (and time)
    reproducing the same permanent failure; only SQLITE_BUSY-shaped errors
    should trigger a retry.
  - Forgetting version = version + 1 in the CAS UPDATE's SET clause — an
    UPDATE that changes balance but not version means the NEXT
    caller's CAS check (against the version they read before this update)
    would incorrectly succeed against a row that has, in fact, changed.
  - Using time.Sleep for backoff instead of a ctx-aware wait — makes
    WithRetry deaf to caller cancellation/timeouts during the backoff
    window.
  - Passing sql.TxOptions{Isolation: sql.LevelSerializable} and believing
    it changed anything with this driver — see the package doc comment.

STRETCH GOALS
  - Add a GetAccountsForUpdate(ctx, ids []int64) helper used by both
    Transfer and any future multi-account operation, so the ascending-ID
    lock-ordering logic lives in one place.
  - Make maxAttempts and the backoff schedule configurable via functional
    options on Open, rather than hardcoded inside Transfer.
  - Add a benchmark comparing UpdateBalanceCAS throughput under N concurrent
    goroutines racing to update the SAME account (expect most to fail with
    ErrVersionConflict and need caller-side retry) vs. Transfer's
    transaction-based approach for the same workload, and discuss when
    optimistic-locking-with-caller-retry is preferable to a transaction.
  - Add a `_txlock=immediate` DSN variant test and a `_txlock=deferred`
    (SQLite's default) variant test that demonstrates deferred mode can
    surface SQLITE_BUSY on COMMIT rather than on BEGIN under heavy
    concurrent write contention.
*/
