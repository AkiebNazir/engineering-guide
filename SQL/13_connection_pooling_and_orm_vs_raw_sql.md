# Connection Pooling, and ORM vs Raw SQL

## The mental model

Two client-side habits determine how much load your application actually puts on the
database, independent of how good your schema and indexes are: whether you reuse
connections instead of opening a new one per request, and whether you fetch related
data in one query or accidentally in N+1. Both are measured live in this level with
real timings, not estimated.

## Why opening a connection is expensive: Postgres's per-connection process model

Level 01 introduced this: Postgres forks a dedicated **backend process** per
connection, not a lightweight thread or an in-memory handle. Opening a connection
means a TCP handshake, (optionally) a TLS handshake, process/fork overhead on the
server, authentication, and session setup — real, measurable cost paid **every
time**, before your query even runs.

Measured on this environment — 50 trivial `SELECT 1` "requests," opening a brand-new
connection each time versus reusing four pooled connections:

```python
import time
import psycopg
from psycopg_pool import ConnectionPool

DSN = "postgresql://dsa:dsa@localhost:5544/dsa"
N_REQUESTS = 50

t0 = time.perf_counter()
for _ in range(N_REQUESTS):
    conn = psycopg.connect(DSN)
    conn.execute("SELECT 1;").fetchone()
    conn.close()
dt_new = time.perf_counter() - t0

pool = ConnectionPool(DSN, min_size=4, max_size=4, open=True)
pool.wait()
t0 = time.perf_counter()
for _ in range(N_REQUESTS):
    with pool.connection() as conn:
        conn.execute("SELECT 1;").fetchone()
dt_pool = time.perf_counter() - t0
pool.close()
```

Real output:

```text
50 requests, NEW connection each time: 194.2 ms total, 3.88 ms/request
50 requests, POOLED connection: 24.9 ms total, 0.50 ms/request
speedup: 7.8x
```

**7.8x faster per request** just from reusing connections — and this is measured
against `localhost`, with no real network latency or TLS in the mix. Over a real
network to a managed database (a different AZ, let alone a different region), the
per-connection setup cost is dramatically higher, and the relative win from pooling
grows accordingly.

A **connection pool** is a small, pre-opened set of live connections that requests
borrow and return instead of opening/closing per request — `psycopg_pool`'s
`ConnectionPool` above is exactly this, client-side, inside your application
process.

**Go has two idiomatic ways to pool, and it's worth measuring both.**
`database/sql`'s pool is built into the standard library itself (`SetMaxOpenConns`);
native `pgxpool` (used from level 16 onward in this ladder) is pgx's own pool with
Postgres-specific tuning:

```go
// database/sql + pgx's stdlib driver: new connection per request vs. its own pool
for i := 0; i < 50; i++ {
    db, _ := sql.Open("pgx", dsn)
    db.SetMaxOpenConns(1)
    var one int
    db.QueryRowContext(ctx, "SELECT 1").Scan(&one)
    db.Close()
}
// -- vs --
pooledDB, _ := sql.Open("pgx", dsn)
pooledDB.SetMaxOpenConns(4)
pooledDB.SetMaxIdleConns(4)
for i := 0; i < 50; i++ {
    var one int
    pooledDB.QueryRowContext(ctx, "SELECT 1").Scan(&one)
}

// native pgxpool, same 50 requests, 4-connection pool
pool, _ := pgxpool.New(ctx, dsn+"?pool_max_conns=4&pool_min_conns=4")
for i := 0; i < 50; i++ {
    var one int
    pool.QueryRow(ctx, "SELECT 1").Scan(&one)
}
```

Real output:

```text
database/sql, NEW connection each time: 209.5 ms total, 4.19 ms/request
database/sql, pooled (SetMaxOpenConns=4): 5.6 ms total, 0.11 ms/request
speedup: 37.1x

native pgxpool (4 conns): 6.1 ms total, 0.12 ms/request
```

Same story as Python's 7.8x, and an even bigger gap here (37.1x) because
`sql.Open` per iteration in the unpooled loop pays Go's driver-registration and
connection-handshake overhead on every single call — the qualitative point is
identical either language: reusing connections beats opening one per request, and
both Go pooling styles land at essentially the same per-request cost once warm
(0.11ms vs 0.12ms) — the choice between them (covered fully in level 19) is about <abbr title="Application Programming Interface">API</abbr>
surface and portability, not raw speed.

## PgBouncer: pooling at the infrastructure level

`psycopg_pool` pools connections *within one application process*. **PgBouncer** is
a separate, standalone process that sits between your application(s) and Postgres
and pools connections *across every client that connects to it* — the standard
answer to "I have 50 application server processes, each wanting its own pool of 10
connections, and Postgres can't handle 500 real backend processes."

Three PgBouncer pooling modes, in increasing aggressiveness:

- **Session pooling** — a client keeps the same backend connection for its entire
  session (closest to no pooling at the database level, safest for session state
  like `SET` or advisory locks).
- **Transaction pooling** — the connection is returned to the pool as soon as a
  transaction commits, and the next transaction (possibly from a different client)
  may get a different underlying connection. This is the common production choice —
  it lets a small number of real Postgres connections serve a much larger number of
  concurrent application-level transactions.
- **Statement pooling** — returned after every single statement; most restrictive,
  incompatible with multi-statement transactions.

The trade-off with transaction pooling: anything that depends on a connection's
*session* state persisting across statements (session-level `SET`, `PREPARE`d
statements outside a transaction, advisory locks meant to outlive one transaction)
breaks, because the "connection" your client thinks it has may be a different
physical backend on the next statement. This is a real operational gotcha, not a
theoretical one — teams migrating onto PgBouncer in transaction mode routinely have
to find and fix code that assumed session persistence.

<div class="lab" data-viz="flow-pg-pooling"></div>

## The N+1 query problem — measured live

The N+1 pattern: fetch a list of N rows, then loop over them issuing one more query
per row to fetch related data — exactly what an ORM's naive "lazy loading" does by
default when you access a relationship inside a loop.

Setup: 200 orders, each referencing one of 200 customers.

```python
# N+1 style: one query for the list, then one query PER ROW for the related data
order_ids = [r[0] for r in conn.execute("SELECT id FROM n1_orders ORDER BY id;").fetchall()]
results = []
for oid in order_ids:
    row = conn.execute(
        "SELECT o.id, o.total, c.name FROM n1_orders o JOIN n1_customers c ON c.id = o.customer_id WHERE o.id = %s;",
        (oid,),
    ).fetchone()
    results.append(row)
```

Real output (query count tracked by wrapping `conn.execute`):

```text
N+1 style (lazy per-row load): 201 queries, 32.0 ms, 200 rows
```

201 queries — 1 to list the order IDs, 200 more, one per order, to fetch its
customer. The fix: fetch everything needed in **one** query with a join, up front:

```python
results2 = conn.execute("""
    SELECT o.id, o.total, c.name FROM n1_orders o JOIN n1_customers c ON c.id = o.customer_id ORDER BY o.id;
""").fetchall()
```

```text
single JOIN (eager load): 1 query, 0.4 ms, 200 rows
```

**1 query instead of 201, and 74.3x faster wall-clock time** — on `localhost`, where
each extra query only costs the local round-trip overhead measured in the pooling
section above. Against a real network with real per-round-trip latency (even 1-2 ms
each), 200 extra queries is 200-400 ms added to a single request purely from query
count, independent of how fast each individual query runs.

**Go, the identical N+1-vs-join comparison** (native `pgxpool`, same `n1_orders`/
`n1_customers` tables — Go has no "lazy relationship" ORM magic to accidentally
trigger this, but the exact same *hand-written* loop-per-row mistake is just as easy
to write and just as costly):

```go
orderIDs := /* ... SELECT id FROM n1_orders ORDER BY id ... */
var results []result
for _, oid := range orderIDs {
    var r result
    pool.QueryRow(ctx,
        "SELECT o.id, o.total, c.name FROM n1_orders o JOIN n1_customers c ON c.id = o.customer_id WHERE o.id = $1",
        oid).Scan(&r.id, &r.total, &r.name)
    results = append(results, r)
}
// vs. one query:
rows, _ := pool.Query(ctx,
    "SELECT o.id, o.total, c.name FROM n1_orders o JOIN n1_customers c ON c.id = o.customer_id ORDER BY o.id")
```

Real output:

```text
N+1 style (lazy per-row load): 201 queries, 27.4 ms, 200 rows
single JOIN (eager load): 1 query, 0.4 ms, 200 rows
speedup: 63.2x
```

Same order of magnitude as the Python measurement (74.3x there, 63.2x here — both
"tens of times," and both dominated by query *count*, not per-query cost) — the N+1
problem is a query-pattern mistake, not a language or ORM-specific one; Go code that
hand-writes a loop-and-query is exactly as vulnerable to it as an ORM's default lazy
loading.

## Raw SQL vs ORM — the actual trade-off

An ORM's real value is object-relational mapping *convenience* (rows become typed
objects, migrations get generated from model classes, simple CRUD is less
boilerplate) — not, contrary to how it's sometimes pitched, "safety" (parameterized
raw SQL is exactly as safe against injection, per level 11) or "performance" (an ORM
adds a translation layer, not a query optimization).

| | Raw SQL | ORM |
|---|---|---|
| Simple CRUD | More boilerplate | Less boilerplate |
| Complex queries (multi-way joins, window functions, CTEs) | Full control, exactly what you write | Often awkward or requires dropping to raw SQL anyway |
| N+1 risk | Only if you write the loop yourself | High by default — lazy loading inside a loop is the ORM's *normal* behavior unless you explicitly eager-load |
| Injection safety | Safe if parameterized (level 11) | Safe for generated queries; equally unsafe the moment you use its raw-SQL escape hatch carelessly |
| Portability across databases | None — you own the SQL dialect | Often better, at the cost of lowest-common-denominator features |

The practical rule that falls out of the N+1 measurement above: whichever you use,
know exactly how many queries a piece of code issues before it ships, not after a
slow endpoint gets reported. Most ORMs have an eager-loading mechanism
(`.select_related()`/`.prefetch_related()` in Django, `joinedload()`/`selectinload()`
in SQLAlchemy) specifically to collapse N+1 patterns back down to the join-based
shape measured above — using it is the difference between the two numbers in this
level.

## Common mistakes

- **Opening a connection per request without a pool**, as measured above — a
  correctness-neutral but real performance and resource cost that compounds under
  load (each unpooled connection is a full backend process on the Postgres side too).
- **Accessing a lazy-loaded relationship inside a loop** — the single most common way
  ORMs produce N+1 patterns, usually invisible in development with 3 test rows and
  very visible in production with 3,000.
- **Sizing a pool without sizing Postgres's `max_connections` alongside it.** A pool
  (or many pooled application instances) requesting more total connections than
  Postgres is configured to accept just moves the bottleneck to connection
  rejections instead of queueing — this is exactly the problem PgBouncer's
  transaction pooling exists to solve at the infrastructure level.
- **In Go specifically: assuming `sql.Open` connects immediately.** It doesn't —
  `sql.Open` only validates the DSN and returns a pool handle; the first real TCP
  connection happens lazily, on the first `Query`/`Exec`/`Ping`. Benchmarking
  "connection setup cost" by timing `sql.Open` alone measures almost nothing — the
  measurement above times the first real query too, for exactly this reason.

## What's next

Level 14 is the capstone: a small CRUD service that combines pooling, retries, and
timeouts into one coherent client.
