/*
Package repository — Database Repository Layer (Problem 09)

WHAT WE'RE BUILDING

A repository layer over database/sql for a simple "accounts" domain (an
account has an ID, an owner name, and a balance in cents), backed by
modernc.org/sqlite — a pure-Go, cgo-free SQLite driver. The repository owns
connection pooling, prepared statements, context propagation, and row
scanning behind a small, testable interface. This same domain (accounts with
a balance) continues into Problem 10, which adds transactions, optimistic
locking, and concurrent-update safety on top of what's built here.

# WHY IT MATTERS IN REAL SYSTEMS

database/sql is a thin, driver-agnostic abstraction: almost every production
bug in a hand-rolled repository layer traces back to misunderstanding one of
a small number of things it does NOT do for you — it does not retry, it does
not manage transactions for you beyond what you explicitly Begin/Commit, and
critically, it pools connections in a way that has sharp edges with SQLite
specifically. Getting comfortable with *Row/*Rows scanning, prepared
statement reuse, context-aware queries (QueryContext/ExecContext, never the
context-less variants in a service), and connection pool tuning is
foundational to every service that talks to a real database.

THE `:memory:` + CONNECTION POOL FOOTGUN (read this before writing any code)

sql.Open("sqlite", ":memory:") does NOT give you one in-memory database
shared across your whole process. database/sql maintains a POOL of
connections and opens new ones lazily as needed; with modernc.org/sqlite (and
essentially every SQLite driver), each physical connection to ":memory:" is
its own separate, independent in-memory database. So the very first query
that happens to grab connection #2 from the pool sees a "database" with none
of the tables you created on connection #1 — intermittent, hard-to-reproduce
"table not found" or "no rows" bugs that appear only under concurrency (once
the pool actually opens more than one connection).

Two correct fixes:
 1. db.SetMaxOpenConns(1) — force the whole pool down to a single physical
    connection, so ":memory:" is always the same database. Correct, but
    means every query is fully serialized — fine for tests, wrong for
    anything with real concurrent load.
 2. Use a real file on disk — even a t.TempDir()-rooted temp file — as the
    DSN. Every pooled connection opens the SAME file, so this works
    correctly with the pool's default (concurrent) behavior. This is what
    this problem's tests do, and what you should default to for anything
    beyond a single quick throwaway script.

(There is a third option — SQLite's shared-cache mode via a
"file::memory:?cache=shared" DSN — which also fixes it, but has its own
locking quirks and is generally considered more surprising than just using a
temp file, so we don't use it here.)

CONCEPTS COVERED
  - database/sql: sql.DB is a pool, not a connection — Open doesn't connect
  - Connection pool tuning: SetMaxOpenConns, SetMaxIdleConns, SetConnMaxLifetime
  - Prepared statements: *sql.Stmt reuse vs ad-hoc query strings
  - Context propagation: QueryContext/ExecContext/QueryRowContext everywhere,
    never the non-Context variants, so callers can cancel/timeout DB calls
  - Row scanning: sql.ErrNoRows, scanning into typed structs, NULL handling
    via sql.NullString/sql.NullInt64 or driver-level *string
  - Resource cleanup: defer rows.Close(), checking rows.Err() after the loop
  - Schema setup for tests: golang-migrate-style raw DDL executed once per
    test DB

REQUIREMENTS / SPEC

	type Account struct {
	    ID      int64
	    Owner   string
	    Balance int64 // cents, to avoid float rounding issues with money
	}

	type Repository struct { ... } // wraps *sql.DB + prepared statements

	func Open(ctx context.Context, dsn string) (*Repository, error)
	    Opens the DB (sql.Open + Ping to fail fast on a bad DSN), configures
	    the connection pool (document your chosen limits and why), runs
	    schema migration (CREATE TABLE IF NOT EXISTS), and prepares the
	    statements this repository will reuse. Must accept ctx and propagate
	    it into the Ping and schema-setup calls.

	func (r *Repository) Close() error
	    Closes prepared statements then the DB. Must be safe to call once
	    (document whether double-Close is safe — sql.DB.Close is idempotent,
	    prepared statement Close should be handled the same way or guarded).

	func (r *Repository) CreateAccount(ctx context.Context, owner string, initialBalanceCents int64) (Account, error)
	func (r *Repository) GetAccount(ctx context.Context, id int64) (Account, error)
	    Not found -> a wrapped error satisfying errors.Is(err, ErrNotFound).
	func (r *Repository) ListAccounts(ctx context.Context, ownerLike string) ([]Account, error)
	    ownerLike "" means "all accounts"; otherwise a SQL LIKE pattern
	    against owner (caller supplies %-wildcards).
	func (r *Repository) UpdateBalance(ctx context.Context, id int64, newBalanceCents int64) error
	    Not found -> ErrNotFound. (Problem 10 replaces/extends this with
	    optimistic-locking and transactional variants — keep this one
	    simple: a straight UPDATE.)
	func (r *Repository) DeleteAccount(ctx context.Context, id int64) error
	    Not found -> ErrNotFound.

ACCEPTANCE CRITERIA
  - Every exported method takes a context.Context as its first parameter and
    uses the *Context variant of the relevant database/sql call — no bare
    Query/Exec/QueryRow anywhere in the repository.
  - GetAccount/UpdateBalance/DeleteAccount on a nonexistent ID return an
    error satisfying errors.Is(err, ErrNotFound), never a bare sql.ErrNoRows
    leaking out of the package.
  - Tests use t.TempDir() + a file-based SQLite DSN (per the footgun note
    above), never ":memory:" with the default pool settings, and each test
    gets its own fresh DB file (hermetic, safe under -parallel).
  - Close() releases all resources and a second Close() call does not panic.
  - ListAccounts with ownerLike == "" returns every account; with a LIKE
    pattern, only matches.
  - go vet and go test -race are clean.

Read the HINTS and PITFALLS at the bottom before opening the solution file.
*/
package repository

import (
	"context"
	"errors"
)

// Account is one row of the accounts table. Balance is stored in integer
// cents specifically to avoid the rounding/comparison hazards of storing
// money as a float.
type Account struct {
	ID      int64
	Owner   string
	Balance int64
}

// ErrNotFound is returned (wrapped, via fmt.Errorf("...: %w", ErrNotFound))
// by any method that looked up a row by ID and found none. Callers should
// use errors.Is(err, ErrNotFound), never compare against sql.ErrNoRows
// directly — that's a database/sql implementation detail this package must
// not leak.
var ErrNotFound = errors.New("repository: account not found")

// Repository wraps a *sql.DB (and its prepared statements) for the accounts
// domain.
type Repository struct {
	// TODO: hold *sql.DB and any *sql.Stmt you choose to prepare once and
	// reuse (e.g. the GetAccount-by-id query, hit on every balance check).
}

// Open opens dsn, configures the connection pool, ensures the schema
// exists, and returns a ready-to-use *Repository.
//
// IMPORTANT: read the ":memory:" + connection pool footgun note in the
// package doc comment above before choosing a DSN in tests or callers.
func Open(ctx context.Context, dsn string) (*Repository, error) {
	// TODO:
	//  1. sql.Open("sqlite", dsn) — this does NOT connect yet, it just
	//     validates the DSN format and sets up the pool's config struct.
	//  2. db.PingContext(ctx) — actually opens a connection, so bad DSNs /
	//     unreachable databases fail here, at Open time, not on the first
	//     real query deep inside request handling.
	//  3. Configure the pool: SetMaxOpenConns, SetMaxIdleConns,
	//     SetConnMaxLifetime. Pick real numbers and justify them in a
	//     comment (this is a SQLite file DB in tests/local dev — the
	//     numbers that make sense here differ from a Postgres pool sized
	//     for a busy service; say why).
	//  4. Run "CREATE TABLE IF NOT EXISTS accounts (...)" via
	//     ExecContext(ctx, ...) to ensure schema exists.
	//  5. Prepare any statements you want to reuse via db.PrepareContext.
	//  6. Wrap it all in a *Repository and return it.
	panic("TODO: implement Open")
}

// Close releases the repository's prepared statements and underlying
// *sql.DB. Safe to call more than once.
func (r *Repository) Close() error {
	// TODO: Close prepared statements (best-effort, join errors), then
	// db.Close(). sql.DB.Close() is documented idempotent; decide/document
	// whether your prepared-statement closing needs its own guard.
	panic("TODO: implement Close")
}

// CreateAccount inserts a new account and returns it with its assigned ID.
func (r *Repository) CreateAccount(ctx context.Context, owner string, initialBalanceCents int64) (Account, error) {
	// TODO: INSERT via ExecContext, then result.LastInsertId() for the new
	// row's ID (SQLite supports this via the rowid alias, as long as the
	// primary key is `INTEGER PRIMARY KEY`).
	panic("TODO: implement CreateAccount")
}

// GetAccount fetches one account by ID. Returns an error satisfying
// errors.Is(err, ErrNotFound) if no such account exists.
func (r *Repository) GetAccount(ctx context.Context, id int64) (Account, error) {
	// TODO: QueryRowContext + Scan; translate sql.ErrNoRows to a wrapped
	// ErrNotFound via fmt.Errorf("...: %w", ErrNotFound) (NOT
	// errors.Join — you want a single linear chain here so
	// errors.Is(err, ErrNotFound) and errors.Is(err, sql.ErrNoRows) can
	// both work if you wrap sql.ErrNoRows too, though only ErrNotFound is
	// part of this package's public contract).
	panic("TODO: implement GetAccount")
}

// ListAccounts returns every account whose owner matches ownerLike (a SQL
// LIKE pattern), or every account if ownerLike == "".
func (r *Repository) ListAccounts(ctx context.Context, ownerLike string) ([]Account, error) {
	// TODO: two query paths (all rows vs LIKE-filtered), or one query with
	// a `WHERE ? = '' OR owner LIKE ?` — pick one and justify it. Remember:
	// defer rows.Close(), and check rows.Err() after the scan loop (a
	// mid-stream I/O error can surface there even if every individual Scan
	// succeeded).
	panic("TODO: implement ListAccounts")
}

// UpdateBalance sets id's balance to newBalanceCents directly (no
// optimistic locking here — see Problem 10 for that). Returns ErrNotFound
// if id doesn't exist.
func (r *Repository) UpdateBalance(ctx context.Context, id int64, newBalanceCents int64) error {
	// TODO: ExecContext an UPDATE, then check result.RowsAffected() == 0
	// to detect "no such id" (an UPDATE matching zero rows is NOT an error
	// from database/sql's point of view — you must check RowsAffected
	// yourself).
	panic("TODO: implement UpdateBalance")
}

// DeleteAccount removes id. Returns ErrNotFound if id doesn't exist.
func (r *Repository) DeleteAccount(ctx context.Context, id int64) error {
	// TODO: same RowsAffected-based existence check as UpdateBalance.
	panic("TODO: implement DeleteAccount")
}

/*
HINTS
  - sql.Open never returns an error for "the database is unreachable" — it
    only validates the DSN's shape. The FIRST real network/file I/O happens
    lazily, on the first query OR on an explicit Ping/PingContext. Always
    Ping in Open() so misconfiguration fails at startup, not on a random
    user's first request.
  - result.RowsAffected() is how you detect "my UPDATE/DELETE matched
    nothing" — database/sql does not turn "0 rows affected" into an error.
  - sql.ErrNoRows is returned ONLY by QueryRow's .Scan(), never by Query
    (Query on zero rows just gives you a *sql.Rows that iterates zero
    times, no error).
  - Prepared statements (*sql.Stmt) obtained from *sql.DB are themselves
    pool-aware: calling stmt.QueryContext concurrently is safe and reuses
    the pool's connections. You don't need one *sql.Stmt per connection.

COMMON PITFALLS
  - Using ":memory:" as the DSN in tests without SetMaxOpenConns(1) — read
    the footgun section above. This produces flaky, pool-state-dependent
    "table not found" failures that are miserable to debug because they
    often pass locally (small pool, few queries) and fail in CI (more
    concurrent test parallelism triggering a second connection).
  - Calling Query/Exec/QueryRow (no "Context" suffix) anywhere in service
    code — these use context.Background() internally, silently defeating
    caller-supplied timeouts and cancellation.
  - Forgetting `defer rows.Close()` after Query/QueryContext — leaks the
    underlying connection back to the pool late (or never, if a panic
    happens before an explicit Close later in the function), which under
    load exhausts the pool.
  - Not checking rows.Err() after the scan loop — an error reading the next
    row from the wire/file mid-iteration is only surfaced there, not from
    Scan or the loop condition.
  - Treating "0 rows affected" from an UPDATE/DELETE as success — it means
    "nothing matched", which for an ID-keyed lookup means the ID doesn't
    exist and should surface as ErrNotFound, not silently look like it
    worked.

STRETCH GOALS
  - Add a `WithTx(ctx, func(*Repository) error) error` helper that begins a
    transaction, hands the caller a Repository bound to that tx, and
    commits/rolls back based on the callback's return — foreshadows
    Problem 10.
  - Benchmark CreateAccount with and without a prepared statement to
    measure SQLite's parse/plan overhead per call.
  - Add an index on `owner` and benchmark ListAccounts with a LIKE prefix
    query before/after, discussing why a LIKE '%foo%' pattern can't use a
    standard b-tree index even with one present.
  - Add OpenTelemetry-style span instrumentation around each method to
    show where per-call context propagation earns its keep operationally.
*/
