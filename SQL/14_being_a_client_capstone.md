# Being a Client: Capstone

## The mental model

Every level so far taught one concept in isolation. A real service talking to
Postgres needs all of them working together: a pool instead of one raw connection
(level 13), bounded statement timeouts so a stuck query can't hang a request
forever, retry logic for the transient failures a real database under real load
actually produces (a dropped connection, a `SerializationFailure` from level 09),
and parameterized queries everywhere (level 11) — non-negotiable, not a nice-to-have
for a "later" pass.

This level builds a small `TaskStore` <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr> service that does all of this, and proves
each behavior actually works by running it.

## The service

```python
import time
import psycopg
from psycopg_pool import ConnectionPool
from dataclasses import dataclass
from typing import Optional

DSN = "postgresql://dsa:dsa@localhost:5544/dsa"


@dataclass
class Task:
    id: int
    title: str
    done: bool


class TaskStoreError(Exception):
    pass


class TaskStore:
    """A small CRUD service in front of Postgres: pooled connections, bounded
    statement timeouts, and retry-with-backoff on transient errors."""

    def __init__(self, dsn: str, min_size: int = 2, max_size: int = 8,
                 statement_timeout_ms: int = 2000, max_retries: int = 3):
        self.max_retries = max_retries
        self.statement_timeout_ms = statement_timeout_ms
        self.pool = ConnectionPool(
            dsn,
            min_size=min_size,
            max_size=max_size,
            kwargs={"autocommit": True, "connect_timeout": 3},
            open=True,
        )
        self.pool.wait(timeout=5)
        self._ensure_schema()

    def _ensure_schema(self):
        with self.pool.connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    title TEXT NOT NULL,
                    done  BOOLEAN NOT NULL DEFAULT false
                );
            """)

    def _run(self, fn):
        """Retry transient (connection-level / serialization) errors with backoff.
        Does NOT retry on data errors (e.g. bad input) -- those will just fail again."""
        delay = 0.05
        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with self.pool.connection() as conn:
                    conn.execute(f"SET statement_timeout = {self.statement_timeout_ms};")
                    return fn(conn)
            except (psycopg.OperationalError, psycopg.errors.SerializationFailure) as e:
                last_err = e
                if attempt == self.max_retries:
                    break
                time.sleep(delay)
                delay *= 2
        raise TaskStoreError(f"operation failed after {self.max_retries} attempts: {last_err}")

    def create(self, title: str) -> Task:
        def op(conn):
            row = conn.execute(
                "INSERT INTO tasks (title) VALUES (%s) RETURNING id, title, done;", (title,)
            ).fetchone()
            return Task(*row)
        return self._run(op)

    def get(self, task_id: int) -> Optional[Task]:
        def op(conn):
            row = conn.execute(
                "SELECT id, title, done FROM tasks WHERE id = %s;", (task_id,)
            ).fetchone()
            return Task(*row) if row else None
        return self._run(op)

    def list(self) -> list[Task]:
        def op(conn):
            rows = conn.execute("SELECT id, title, done FROM tasks ORDER BY id;").fetchall()
            return [Task(*r) for r in rows]
        return self._run(op)

    def mark_done(self, task_id: int) -> Optional[Task]:
        def op(conn):
            row = conn.execute(
                "UPDATE tasks SET done = true WHERE id = %s RETURNING id, title, done;", (task_id,)
            ).fetchone()
            return Task(*row) if row else None
        return self._run(op)

    def delete(self, task_id: int) -> bool:
        def op(conn):
            cur = conn.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
            return cur.rowcount > 0
        return self._run(op)

    def close(self):
        self.pool.close()
```

## The same service, in Go (native `pgxpool`)

```go
type TaskStore struct {
    pool               *pgxpool.Pool
    statementTimeoutMs int
    maxRetries         int
}

func NewTaskStore(ctx context.Context, dsn string, statementTimeoutMs, maxRetries int) (*TaskStore, error) {
    pool, err := pgxpool.New(ctx, dsn)
    if err != nil {
        return nil, err
    }
    ts := &TaskStore{pool: pool, statementTimeoutMs: statementTimeoutMs, maxRetries: maxRetries}
    _, err = pool.Exec(ctx, `CREATE TABLE IF NOT EXISTS tasks_go (
        id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, title TEXT NOT NULL, done BOOLEAN NOT NULL DEFAULT false
    )`)
    return ts, err
}

// run retries transient (connection-level / serialization / timeout) errors with
// backoff. Does NOT retry data errors (e.g. a constraint violation) -- those would
// just fail again identically.
func (ts *TaskStore) run(ctx context.Context, fn func(context.Context, *pgxpool.Conn) error) error {
    delay := 50 * time.Millisecond
    var lastErr error
    for attempt := 1; attempt <= ts.maxRetries; attempt++ {
        err := func() error {
            conn, err := ts.pool.Acquire(ctx)
            if err != nil {
                return err
            }
            defer conn.Release()
            stmtCtx, cancel := context.WithTimeout(ctx, time.Duration(ts.statementTimeoutMs)*time.Millisecond)
            defer cancel()
            conn.Exec(stmtCtx, fmt.Sprintf("SET statement_timeout = %d", ts.statementTimeoutMs))
            return fn(stmtCtx, conn)
        }()
        if err == nil {
            return nil
        }
        lastErr = err
        var pgErr *pgconn.PgError
        isTransient := errors.Is(err, context.DeadlineExceeded) ||
            (errors.As(err, &pgErr) && (pgErr.Code == "40001" || pgErr.Code == "57014")) || // serialization_failure, query_canceled
            !errors.As(err, &pgErr) // not a Postgres error at all -> a connection-level failure
        if !isTransient {
            return &TaskStoreError{Err: err}
        }
        if attempt == ts.maxRetries {
            break
        }
        time.Sleep(delay)
        delay *= 2
    }
    return &TaskStoreError{Err: fmt.Errorf("operation failed after %d attempts: %w", ts.maxRetries, lastErr)}
}

func (ts *TaskStore) Create(ctx context.Context, title string) (*Task, error) {
    var t Task
    err := ts.run(ctx, func(ctx context.Context, conn *pgxpool.Conn) error {
        return conn.QueryRow(ctx,
            "INSERT INTO tasks_go (title) VALUES ($1) RETURNING id, title, done", title,
        ).Scan(&t.ID, &t.Title, &t.Done)
    })
    return &t, err
}
// Get/List/MarkDone/Delete follow the identical run()-wrapped shape.
```

Every element maps to the same level as the Python version: `pgxpool.Pool` is the
pool (level 13); `context.WithTimeout` plus `SET statement_timeout` is the bounded
timeout; `run`'s `isTransient` check is the retry classification (Postgres error code
`40001` is `serialization_failure` from level 09, `57014` is `query_canceled` — a
timed-out statement); every query uses `$1`-style parameters (level 11); a real
`pgconn.PgError`'s `.Code` field is how Go code distinguishes "the database had a
transient bad moment" from "the data was actually wrong," the same distinction
`psycopg.errors.SerializationFailure` vs. everything else makes in the Python version.

Running it — real output, identical behavior to the Python version:

```text
created: {1 write the SQL capstone false} <nil>
created: {2 review the PR false} <nil>
get: {1 write the SQL capstone false}
mark done: {1 write the SQL capstone true}
list: [{1 write the SQL capstone true} {2 review the PR false}]
delete t2: true
list after delete: [{1 write the SQL capstone true}]
get missing id 999999: <nil>
```

And the same timeout proof, a 500ms-limited store asked to run `pg_sleep(5)`:

```text
timeout test: failed as expected -> task store error: operation failed after 1 attempts: timeout: context deadline exceeded
```

Postgres killed the query the same way it did for the Python version; the surfaced
error text differs (`context deadline exceeded` — Go's `context` package canceling
the call locally once its deadline passes, versus Python surfacing Postgres's own
`canceling statement due to statement timeout` message) because `pgxpool`'s
`QueryRow`/`Exec` return the *context's* cancellation error the moment the local
deadline fires, which races with (and typically wins against) the round trip needed
to receive Postgres's own cancellation error back over the wire — both mechanisms
still enforce the identical 500ms bound.

## What ties back to which level

- **Pooling (level 13):** the `ConnectionPool` in `__init__` — every operation
  borrows a connection from a small pre-opened set instead of paying per-call
  connection setup cost.
- **Timeouts:** `SET statement_timeout = ...` on every borrowed connection before
  running the caller's operation — a runaway query gets killed by Postgres itself
  after the configured limit, rather than hanging the calling thread indefinitely.
- **Retries:** `_run` retries only `OperationalError` (connection-level failures —
  the kind of thing a flaky network or a restarting database produces) and
  `SerializationFailure` (level 09's "first committer wins" abort) — both are
  genuinely transient and safe to retry. Notice what's deliberately **not** caught:
  a `UniqueViolation` or `CheckViolation` (level 05) means the *data* is wrong, not
  that the database had a bad moment — retrying it would just fail identically every
  time, so those propagate immediately instead of burning through retry attempts.
- **Parameterized queries (level 11):** every single method uses `%s` placeholders,
  with no exceptions — `title`, `task_id`, all of it.
- **`RETURNING` (level 03):** `create`, `mark_done` fetch the row back in the same
  round trip as the write.

## Running it — real output

```python
store = TaskStore(DSN)
t1 = store.create("write the SQL capstone")
t2 = store.create("review the PR")
print("created:", t1, t2)
print("get:", store.get(t1.id))
print("mark done:", store.mark_done(t1.id))
print("list:", store.list())
print("delete t2:", store.delete(t2.id))
print("list after delete:", store.list())
print("get missing id 999:", store.get(999))
```

```text
created: Task(id=1, title='write the SQL capstone', done=False) Task(id=2, title='review the PR', done=False)
get: Task(id=1, title='write the SQL capstone', done=False)
mark done: Task(id=1, title='write the SQL capstone', done=True)
list: [Task(id=1, title='write the SQL capstone', done=True), Task(id=2, title='review the PR', done=False)]
delete t2: True
list after delete: [Task(id=1, title='write the SQL capstone', done=True)]
get missing id 999: None
```

## Proving the timeout is real, not decorative

A second `TaskStore` configured with a 500 ms statement timeout, asked to run
`SELECT pg_sleep(5)` (a query that deliberately takes 5 seconds):

```python
store2 = TaskStore(DSN, statement_timeout_ms=500, max_retries=1)
try:
    store2._run(lambda conn: conn.execute("SELECT pg_sleep(5);").fetchone())
    print("timeout test: did NOT fail (unexpected)")
except TaskStoreError as e:
    print(f"timeout test: failed as expected -> {e}")
```

Real output:

```text
timeout test: failed as expected -> operation failed after 1 attempts: canceling statement due to statement timeout
```

Postgres itself killed the query after 500 ms and returned the exact error message
shown — `_run` wrapped it in `TaskStoreError` after exhausting the (deliberately set
to 1, for this test) retry budget. Without the `statement_timeout`, this call would
have blocked for the full 5 seconds regardless of any client-side timeout you
thought you'd configured elsewhere.

## What a production version would add

This capstone deliberately stays small enough to read in one sitting. A few things a
real production service would add on top, each traceable to a level above:

- **Circuit breaking** around `_run` — after enough consecutive failures, stop
  attempting new connections for a cooldown window instead of retrying into a
  database that's clearly down, to avoid making an outage worse.
- **Structured logging/metrics per query** — query name, latency, retry count — so
  the N+1-style problems from level 13 show up in dashboards before a user reports
  them.
- **A migration tool** (level 12) managing `tasks`'s schema instead of the
  `CREATE TABLE IF NOT EXISTS` shortcut used here for a self-contained demo.
- **`EXPLAIN ANALYZE`-verified indexes** (level 10) on any column this service
  actually filters or sorts by at scale — this demo's tables are far too small to
  need one.

## What's next

Level 15 is optional: a conceptual walk through what Postgres does internally, end
to end, for a single query — connecting the pieces from levels 01-14 into one
mental picture.
