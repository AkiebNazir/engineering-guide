# Transactions and Isolation Levels

**Already covered elsewhere:** `CSFundamentals/03_databases_deep_dive.md` §3 covers
<abbr title="Multi-Version Concurrency Control. A concurrency control method commonly used by database management systems to provide concurrent access without locking.">MVCC</abbr> internals in depth (how Postgres actually implements snapshots via `xmin`/`xmax`
row versioning) and already has the isolation-level/anomaly reference table. This
level does not re-derive *how* <abbr title="Multi-Version Concurrency Control. A concurrency control method commonly used by database management systems to provide concurrent access without locking.">MVCC</abbr> works — it links there for that — and instead
focuses on *what happens* when transactions collide in Postgres specifically, proven
with two real concurrent sessions, and *how to avoid it*.

## The mental model

A **transaction** groups multiple statements into one all-or-nothing unit:
`BEGIN`, some statements, then either `COMMIT` (make it all permanent) or
`ROLLBACK` (undo all of it, as if none of it happened). Every single statement you've
run in levels 01-08 was already an implicit one-statement transaction — Postgres
auto-commits each statement unless you explicitly `BEGIN` first. What transactions
add is the ability to make **several** statements atomic together — critical the
moment "transfer $50 from account A to account B" needs to debit one row and credit
another as a single, indivisible operation.

```sql
BEGIN;
UPDATE accounts SET balance = balance - 50 WHERE id = 1;
UPDATE accounts SET balance = balance + 50 WHERE id = 2;
COMMIT;   -- or ROLLBACK to undo both if something went wrong
```

```arch
%% caption: A transaction groups multiple statements into a single atomic unit that either entirely succeeds or entirely rolls back.
group txn "Transaction (BEGIN)" color=blue
node s1 "Statement 1\n(UPDATE A)" at 0,0 in txn icon=db
node s2 "Statement 2\n(UPDATE B)" at 2,0 in txn icon=db

node commit "COMMIT\n(Permanent)" at 4,-1 icon=check color=green
node rb "ROLLBACK\n(Undo all)" at 4,1 icon=error color=red

s1 -> s2 : "success"
s2 -> commit : "success"
s2 -> rb : "error/abort"
s1 -> rb : "error/abort"
```

## <abbr title="Atomicity, Consistency, Isolation, Durability - A set of properties of database transactions intended to guarantee data validity despite errors.">ACID</abbr>, precisely

| Property | Means | Postgres mechanism |
|---|---|---|
| **Atomicity** | All of a transaction's writes happen, or none do | The whole transaction is undone on `ROLLBACK` or a crash before `COMMIT` |
| **Consistency** | A transaction moves the database from one valid state to another, respecting every constraint | Enforced by constraints (level 05) checked before commit; not something the database "provides" beyond that — it's on you to define constraints that capture your invariants |
| **Isolation** | Concurrent transactions don't see each other's uncommitted, in-progress work | <abbr title="Multi-Version Concurrency Control. A concurrency control method commonly used by database management systems to provide concurrent access without locking.">MVCC</abbr> snapshots (see `CSFundamentals/03_databases_deep_dive.md` §3) — *how much* isolation is a tunable choice, covered below |
| **Durability** | Once committed, a transaction's writes survive a crash | The write-ahead log (<abbr title="Write-Ahead Logging. A family of techniques for providing atomicity and durability in database systems by writing modifications to a log before they are applied.">WAL</abbr>) is fsynced before `COMMIT` returns |

Consistency is the odd one out: it isn't a mechanism the database runs for you the
way atomicity/isolation/durability are — it's a property that *falls out of*
correctly using the other three plus correctly-declared constraints. A transaction
that violates a `CHECK` constraint simply never commits; the "C" in <abbr title="Atomicity, Consistency, Isolation, Durability - A set of properties of database transactions intended to guarantee data validity despite errors.">ACID</abbr> is really a
statement about what atomicity + constraints together guarantee.

## Isolation levels and the anomalies they allow

Full anomaly definitions and the complete level-by-level table live in
`CSFundamentals/03_databases_deep_dive.md` §3 — reproduced here only as a quick
reference, since the rest of this level assumes you know these terms:

| Anomaly | What happens |
|---|---|
| Dirty read | Read another transaction's uncommitted write |
| Non-repeatable read | Read the same row twice in one transaction, get different committed values |
| Phantom | Re-run a range query, new rows appear that match the condition |
| Lost update | Two read-modify-write cycles interleave; one overwrites the other's change entirely |
| Write skew | Two transactions read overlapping data and write *different* rows, together breaking an invariant neither one violated alone |

**Postgres-specific facts worth knowing precisely:**

- Postgres's default isolation level is **`READ COMMITTED`**.

<div class="lab" data-viz="flow-sql-isolation"></div>
- Postgres has no separate "repeatable read" implementation distinct from snapshot
  isolation — requesting `REPEATABLE READ` in Postgres gives you full snapshot
  isolation for the whole transaction, which is actually *stronger* than the <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>
  standard requires for that level.
- Postgres never allows dirty reads, at any isolation level — this is a Postgres
  guarantee, not a <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>-standard requirement (some other databases' lowest level does
  allow them).

## Demo 1: a real lost update, and the fix

Two "sessions" (two separate `psycopg` connections, run concurrently via threads to
force real interleaving) both read an account balance, both compute "balance − 10,"
and both write back — without any locking.

```python
import threading
import time
import psycopg

DSN = "postgresql://dsa:dsa@localhost:5544/dsa"

def race_without_locking(barrier, conn):
    conn.execute("BEGIN;")
    balance = conn.execute("SELECT balance FROM accounts WHERE id = 1;").fetchone()[0]
    barrier.wait()          # force both transactions to have READ before either WRITES
    time.sleep(0.2)
    new_balance = balance - 10
    conn.execute("UPDATE accounts SET balance = %s WHERE id = 1;", (new_balance,))
    conn.commit()
    return balance, new_balance
```

Starting balance: 100. Both sessions read 100 before either writes, so both compute
"90" and both write 90 — one withdrawal is silently lost. Real output from running
this against the live database with two threads:

```text
session A read/wrote: (100, 90)
session B read/wrote: (100, 90)
expected balance if both withdrawals applied: 80
actual final balance: 90
```

**The fix: `SELECT ... FOR UPDATE`.** It takes a row-level lock on the selected
row(s) for the rest of the transaction — a second transaction's own
`SELECT ... FOR UPDATE` on the same row *blocks* until the first transaction commits
or rolls back, instead of proceeding with a now-stale value:

```python
def race_with_for_update(start_gate, conn):
    conn.execute("BEGIN;")
    start_gate.wait()   # both threads attempt the SELECT FOR UPDATE at ~the same time
    balance = conn.execute("SELECT balance FROM accounts WHERE id = 1 FOR UPDATE;").fetchone()[0]
    # whichever session gets here second was BLOCKED on the row lock until the first
    # COMMITted, so it re-reads the post-commit balance -- that IS the fix.
    time.sleep(0.2)
    new_balance = balance - 10
    conn.execute("UPDATE accounts SET balance = %s WHERE id = 1;", (new_balance,))
    conn.commit()
    return balance, new_balance
```

Real output, same starting balance of 100:

```text
session A read/wrote: (90, 80)
session B read/wrote: (100, 90)
expected balance if both withdrawals applied: 80
actual final balance: 80
```

Session B's `SELECT ... FOR UPDATE` blocked until session A committed, so B read the
**post-commit** balance (90, not the stale 100) and correctly computed 80. Both
withdrawals landed. This is Postgres enforcing correctness through row locking,
independent of which isolation level the transaction is running at.

**The same two demos, in Go, with real concurrent goroutines** (native `pgxpool` —
its explicit `Begin`/`Exec`/`Commit` <abbr title="Application Programming Interface">API</abbr> maps directly onto manual transaction
control, which is exactly what this demo needs). Go has no direct equivalent of
Python's `threading.Barrier`, so the same "force both goroutines to have READ before
either WRITES" effect is built from a `sync.WaitGroup`: seed it with `Add(2)`, have
each goroutine call `Done()` then immediately `Wait()` — both block until the second
`Done()` brings the counter to zero, so both proceed at (as close as the scheduler
allows to) the same instant:

```go
func raceWithoutLocking(ctx context.Context, pool *pgxpool.Pool, barrier *sync.WaitGroup, label string, results chan<- string) {
    tx, _ := pool.Begin(ctx)
    defer tx.Rollback(ctx) // no-op if Commit already succeeded

    var balance int
    tx.QueryRow(ctx, "SELECT balance FROM accounts WHERE id = 1").Scan(&balance)

    barrier.Done()
    barrier.Wait() // force both transactions to have READ before either WRITES

    time.Sleep(200 * time.Millisecond)
    newBalance := balance - 10
    tx.Exec(ctx, "UPDATE accounts SET balance = $1 WHERE id = 1", newBalance)
    tx.Commit(ctx)

    results <- fmt.Sprintf("%s read/wrote: (%d, %d)", label, balance, newBalance)
}

// in main: barrier := &sync.WaitGroup{}; barrier.Add(2); run two goroutines
// calling raceWithoutLocking concurrently, then read the final balance.
```

Real output, starting balance 100, both goroutines running concurrently:

```text
goroutine B read/wrote: (100, 90)
goroutine A read/wrote: (100, 90)
expected balance if both withdrawals applied: 80
actual final balance: 90
```

Exactly the same lost update as the Python/`threading` version — this isn't a
Python-specific bug (e.g. the <abbr title="Global Interpreter Lock. A mutex that protects access to Python objects, preventing multiple threads from executing Python bytecodes at once.">GIL</abbr> is irrelevant here; both goroutines block on real
network I/O to Postgres, not on <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>-bound Python bytecode), it's a property of the
unprotected read-modify-write pattern itself, reproduced identically with real <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr>
threads under the goroutine scheduler.

The fix, `SELECT ... FOR UPDATE`, carries over directly — the only change from the
racy version is adding `FOR UPDATE` to the `SELECT` and using a `startGate` barrier
instead (same `sync.WaitGroup` pattern, gating the *read* this time instead of gating
between read and write):

```go
tx.QueryRow(ctx, "SELECT balance FROM accounts WHERE id = 1 FOR UPDATE").Scan(&balance)
// whichever goroutine's SELECT ... FOR UPDATE arrives second BLOCKS here until the
// first goroutine's transaction commits, then reads the POST-COMMIT balance.
```

Real output, same starting balance of 100:

```text
goroutine B read/wrote: (100, 90)
goroutine A read/wrote: (90, 80)
expected balance if both withdrawals applied: 80
actual final balance: 80
```

Goroutine A's `SELECT ... FOR UPDATE` blocked on B's row lock, so A woke up with the
post-commit balance (90) instead of the stale 100 — identical mechanism, identical
correct result, as the Python demo above.

<div class="lab" data-viz="flow-lost-update"></div>

## Demo 2: non-repeatable read at `READ COMMITTED`, prevented by `REPEATABLE READ`

```python
a = psycopg.connect(DSN)
a.execute("BEGIN;")   # default READ COMMITTED
print("A first read:", a.execute("SELECT balance FROM accounts WHERE id=1;").fetchone())

b = psycopg.connect(DSN, autocommit=True)
b.execute("UPDATE accounts SET balance = 500 WHERE id=1;")   # B commits immediately

print("A second read, same txn:", a.execute("SELECT balance FROM accounts WHERE id=1;").fetchone())
a.commit()
```

Real output:

```text
A first read: (100,)
B committed an update to 500
A second read in same txn: (500,)
```

At `READ COMMITTED`, each statement in transaction A sees the latest *committed*
data as of *that statement* — so A's two reads, in the same transaction, returned
two different values. That's the non-repeatable read anomaly, live.

Switching A to `BEGIN ISOLATION LEVEL REPEATABLE READ` and repeating the same
sequence:

```text
A (repeatable read) first read: (100,)
B committed an update to 999
A (repeatable read) second read, SAME txn snapshot: (100,)
A's write failed: SerializationFailure: could not serialize access due to concurrent update
final balance: (999,)
```

Two things happened, both real Postgres behavior:

1. A's second read still returned `100` — `REPEATABLE READ` pins A to the snapshot
   as of the transaction's start, so B's committed change to 999 is invisible to A
   for the rest of A's transaction. Non-repeatable reads: prevented.
2. When A then tried to **write** that same row (`UPDATE ... SET balance = balance - 10`),
   Postgres raised a real `SerializationFailure` and refused the write, rather than
   silently overwriting B's committed change. This is Postgres's "first committer
   wins" rule under snapshot isolation: A's snapshot is provably stale for a write to
   this row, so Postgres aborts A's transaction rather than let it clobber B's
   already-committed update. The application is expected to catch this specific
   error and retry the whole transaction.

**The same two isolation-level demos, in Go (native `pgxpool`):** pgx sets the
isolation level via `pgx.TxOptions` on `BeginTx`, rather than a literal
`BEGIN ISOLATION LEVEL ...` string:

```go
// READ COMMITTED (the default) -- non-repeatable read
a, _ := pool.Begin(ctx)
var first int
a.QueryRow(ctx, "SELECT balance FROM accounts WHERE id=1").Scan(&first)

pool.Exec(ctx, "UPDATE accounts SET balance = 500 WHERE id=1") // a separate, autocommitted connection

var second int
a.QueryRow(ctx, "SELECT balance FROM accounts WHERE id=1").Scan(&second)
a.Commit(ctx)
```

Real output — the same non-repeatable read, live:

```text
A first read: 100
B committed an update to 500 (autocommit)
A second read, same txn: 500
```

Switching to `REPEATABLE READ` via `pgx.TxOptions{IsoLevel: pgx.RepeatableRead}`:

```go
a2, _ := pool.BeginTx(ctx, pgx.TxOptions{IsoLevel: pgx.RepeatableRead})
var r1 int
a2.QueryRow(ctx, "SELECT balance FROM accounts WHERE id=1").Scan(&r1)

pool.Exec(ctx, "UPDATE accounts SET balance = 999 WHERE id=1")

var r2 int
a2.QueryRow(ctx, "SELECT balance FROM accounts WHERE id=1").Scan(&r2) // still the old snapshot

_, writeErr := a2.Exec(ctx, "UPDATE accounts SET balance = balance - 10 WHERE id=1")
if writeErr != nil {
    // handle pgErr.Code == "40001" (serialization_failure): retry the whole transaction
}
```

Real output:

```text
A (repeatable read) first read: 100
B committed an update to 999
A (repeatable read) second read, SAME txn snapshot: 100
A's write failed: ERROR: could not serialize access due to concurrent update (SQLSTATE 40001)
final balance: 999
```

Byte-for-byte the same story as the Python run above: A's snapshot stays pinned at
100 through both reads, and A's write is rejected with SQLSTATE `40001`
(`serialization_failure`) the moment it conflicts with B's already-committed change —
the exact same standardized error code `psycopg`'s `SerializationFailure` exception
wraps, confirming this is Postgres's guarantee, not an artifact of either client
library.

## Practical defenses, weakest guarantee to strongest

You do not need `SERIALIZABLE` for most problems — reach for the lightest tool that
actually prevents the anomaly you care about:

1. **Atomic conditional updates**, when the fix fits in one statement:
   `UPDATE accounts SET balance = balance - 10 WHERE id = 1 AND balance >= 10;` and
   check the row count affected — no read-modify-write race exists because the read
   and write happen inside one atomic statement.
2. **`SELECT ... FOR UPDATE`**, when you need to read, do application-level logic,
   then write — demonstrated above.
3. **Unique/check/exclusion constraints**, when the invariant can be expressed
   declaratively (level 05) — let the database reject the bad state outright instead
   of trying to prevent it via locking.
4. **`REPEATABLE READ`/`SERIALIZABLE`**, when the logic genuinely needs a consistent
   view across multiple statements and multiple rows (write skew territory) — at the
   cost of needing retry logic for the `SerializationFailure`s this demo just showed.

## Common mistakes

- **Read-modify-write in application code with no locking** — exactly the lost
  update demonstrated above, and the most common concurrency bug in real backend
  code (`balance = get_balance(); set_balance(balance - amount)` across two separate
  round trips).
- **Assuming `REPEATABLE READ` prevents write skew.** It doesn't — the anomaly table
  above (and `CSFundamentals/03_databases_deep_dive.md` §3) both mark write skew as
  possible even under snapshot isolation. Only `SERIALIZABLE` prevents it.
- **Not handling `SerializationFailure`.** If you use `REPEATABLE READ` or
  `SERIALIZABLE`, your application **must** catch this error and retry the
  transaction — it is an expected, routine outcome under those isolation levels, not
  an exceptional failure. In Go, that means `errors.As(err, &pgErr)` and checking
  `pgErr.Code == "40001"` (or `"40P01"` for a deadlock), not just logging the error
  string and giving up.
- **Reusing a `sync.WaitGroup` barrier for more than the two parties it was `Add()`ed
  for.** Unlike Python's `threading.Barrier`, which resets automatically and supports
  a party rejoining, a `WaitGroup`-based barrier is single-use for its exact party
  count — fine for a two-goroutine demo like this one, but reach for a real
  synchronization primitive (or a fresh `WaitGroup` per round) if you need a
  repeating barrier.

## What's next

Level 10 covers indexing — how Postgres actually finds the rows a query asks for,
and how to measure whether an index is doing its job.
