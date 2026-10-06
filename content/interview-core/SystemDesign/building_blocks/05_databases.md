# Databases: Source of Truth

The database is where a business fact becomes durable and authoritative. Everything else in a system — cache, search index, warehouse — is a derived copy that can be rebuilt. The database cannot be "rebuilt"; if it loses a fact, the fact is gone.

Default to a relational database (PostgreSQL/MySQL) for user, order, catalog, and permission workflows. Constraints, indexes, joins, and transactions model real invariants directly instead of pushing them into application code. Reach for something else only when a specific access pattern or scale limit justifies it — see [Database Internals: How They Actually Work](06_database_internals.md) for the family comparison.

## Foundations — What a Database Actually Promises

### Four guarantees you would otherwise build yourself

A file can store bytes. A database adds the four things every application needs and almost
nobody should write by hand:

1. **Durability** — once it says "committed," the fact survives a crash (a write-ahead log and
   `fsync`, [Database Storage Engines & Advanced Structures](../../CSFundamentals/03_databases_deep_dive.md) §9).
2. **Transactions** — several changes happen together or not at all, and concurrent transactions
   don't see each other's half-done work (isolation levels, [Transactions, Isolation, Locking, and Sagas](11_transactions_and_concurrency.md)).
3. **Constraints** — the database itself refuses data that breaks an invariant: unique emails,
   non-negative stock, an order that references a real customer.
4. **Queries** — ask for data by what it *is* ("orders for user 17 this month"), and the planner
   finds a fast way using indexes.

Every time a design moves data out of a relational database — into a cache, a key-value store, a
queue — ask which of the four it gives up, and who now provides it.

### Two workloads: OLTP and OLAP

| | OLTP (transactions) | OLAP (analytics) |
|---|---|---|
| Typical query | "This user's cart", "place this order" | "Revenue by region by week, last two years" |
| Rows touched | A few, by key | Millions, scanned |
| Latency target | Milliseconds | Seconds to minutes |
| Storage layout | Row-oriented, B-tree indexes | Column-oriented, compressed |
| Examples | PostgreSQL, MySQL, Spanner, DynamoDB | BigQuery, Snowflake, ClickHouse, Redshift |

Running analytics on the OLTP primary is a classic incident: one scan evicts the hot working set
from memory and every user request slows down. Replicate into an analytical store
([Batch and Stream Processing](21_batch_and_stream_processing.md)) instead.

### The database families in one table

| Family | Data shape | Reach for it when | Examples |
|---|---|---|---|
| Relational | Tables, rows, joins, constraints | The default: entities with relationships and invariants | PostgreSQL, MySQL, Spanner, CockroachDB |
| Document | Nested JSON documents | Data read and written as one self-contained unit | MongoDB, Firestore |
| Key-value | Opaque value by key | Very high throughput by key, no queries | DynamoDB, Redis, RocksDB |
| Wide-column | Rows partitioned by key, sorted by a clustering key | Huge write volume, queries always by partition key | Cassandra, Bigtable, HBase |
| Search | Inverted index over text | Full-text relevance, faceting | Elasticsearch, OpenSearch |
| Time-series | Timestamped measurements | Metrics, IoT, append-heavy time ranges | Prometheus, InfluxDB, TimescaleDB |
| Graph | Nodes and edges | Many-hop relationship queries | Neo4j, social-graph services |

[Database Internals: How They Actually Work](06_database_internals.md) explains the storage engines underneath; the SQL and NoSQL modules of
this repository cover PostgreSQL, MongoDB and Redis hands-on.

### Vocabulary

| Term | Meaning |
|---|---|
| Source of truth | The one store whose copy wins; everything else is derived and rebuildable |
| Access pattern | A query the application runs, with its frequency and latency need |
| Selectivity | The fraction of rows a predicate keeps; indexes pay off when it is small |
| Covering index | An index containing every column a query needs |
| Write amplification | Physical writes per logical write (every index is another write) |
| Replication lag | How far a replica is behind the primary |
| Read model / projection | A denormalised copy shaped for one query, kept in sync from the source of truth |

## Data modeling questions

Ask these for every fact before writing a schema, not after:

1. **Who owns it and who may mutate it?** — determines write authorization, not just read authorization.
2. **What is its primary key?** — natural key (email, SKU) vs surrogate key (generated ID); natural keys can change, surrogate keys can't leak meaning.
3. **What queries must be fast, and which index supports each one?** — an unindexed hot query is a future incident, not a future optimization.
4. **What invariant must never be violated?** — "available quantity never goes negative," "a user has at most one active subscription." These become `CHECK` constraints, unique indexes, or transaction logic, not just application assertions.
5. **How long is it retained, and how is it deleted?** — soft delete vs hard delete vs TTL-expiry has compliance and query-complexity consequences.
6. **Can it be stale in a read, and for whom?** — answering this up front tells you whether a read replica is even allowed to serve that query.

The interview-quality version of this: don't jump to a schema diagram. Walk the six questions out loud per entity first.

## Primary keys

Prefer a surrogate key (auto-increment, UUID, or a time-sortable ID like ULID/snowflake) over a natural key as the primary key, even when a natural key looks unique today. Natural keys change (emails get corrected, SKUs get reissued), and a primary key change cascades through every foreign key referencing it. Keep the natural key as a separate `UNIQUE` constraint instead.

Sequential surrogate keys (auto-increment) give good B-tree insert locality but leak volume/order information and create write hotspots on the last page under very high insert concurrency. Random UUIDs avoid the hotspot and the leak but scatter inserts across the whole index, hurting cache locality and page-split behavior. Time-sortable IDs (ULID, snowflake) are the common middle ground: monotonic-ish for locality, opaque enough not to leak sequential meaning.

## Indexing intuition

An index speeds up a known access path and costs storage plus write-path maintenance — every insert/update/delete has to update every index on that table, not just the base row. Index the query you actually run, then confirm with a real execution plan (`EXPLAIN ANALYZE`), not intuition.

**Leading-column rule for composite indexes:** an index on `(user_id, created_at)` is usable for "recent records for one user" (`WHERE user_id = ? ORDER BY created_at DESC`) because the query can walk the index using `user_id` as a prefix. The same index does **not** help "all records ordered by time across all users," because `created_at` is not the leading column — the database would have to scan every `user_id` bucket. If you need both access patterns, you generally need two indexes, or a different leading column ordering depending on which query is hotter.

```text
Index (user_id, created_at):
  user_id=17 → [t1, t3, t9, t12]   ← range scan on created_at within user 17: fast
  user_id=18 → [t2, t5, t8]
  ...
Query "all records after t5 across all users" → no usable prefix → full scan
```

**When an index doesn't help:** low-selectivity columns (a boolean flag with 90% one value), queries that already return most of the table, or predicates the planner can't use because of a function wrapped around the column (`WHERE LOWER(email) = ?` needs an index on `LOWER(email)`, not on `email`).

**Cost of over-indexing:** every additional index roughly multiplies write amplification — a single-row `INSERT` becomes N B-tree page writes for N indexes, plus more WAL volume and more pages that can become hot under concurrent writers. Index for the queries that exist, remove indexes nothing uses.

## Covering indexes and index-only scans

A normal secondary index gives the database the *location* of matching rows; it then fetches each row from the table (a "heap fetch" in PostgreSQL, a primary-key lookup in InnoDB). For a query returning 5,000 rows that's 5,000 extra random lookups.

A **covering index** contains every column the query needs, so the database answers from the index alone:

```sql
-- Query: a user's recent order totals
SELECT created_at, total FROM orders
WHERE user_id = :u ORDER BY created_at DESC LIMIT 20;

-- Covering index: filter column, sort column, then the selected column
CREATE INDEX orders_user_recent ON orders (user_id, created_at DESC) INCLUDE (total);  -- PostgreSQL 11+, SQL Server
-- MySQL/InnoDB: (user_id, created_at, total); secondary indexes also carry the primary key automatically
```

- **Column order:** equality predicates first, then the range/sort column, then extra columns that are only selected (via `INCLUDE` where supported, so they don't affect ordering or uniqueness).
- **PostgreSQL caveat:** an "index-only scan" still checks the visibility map to know whether a row version is visible to the transaction; on a table with many recently modified pages it falls back to heap fetches until `VACUUM` updates the map.
- **Cost:** a wider index means more storage and more write amplification; cover the hot queries, not every query.
- **Verify** with `EXPLAIN (ANALYZE, BUFFERS)`: look for `Index Only Scan` and low `Heap Fetches`.

## Normalization vs denormalization

Normalize the **source of truth** so each fact is stored once: no update anomalies (changing a customer's email in one place, not in every order row). Denormalize **read models** for speed (materialized views, per-user feed rows, search documents, cache entries) and own the process that keeps them in sync: synchronous dual writes are fragile; prefer change data capture or an outbox feeding projections. In a sharded or wide-column store, denormalization is the default because cross-partition joins are expensive or unavailable.

## Read replicas and staleness


```arch
%% caption: Asynchronous replication means a read immediately following a write might hit a replica that hasn't seen the update yet.
node client "Client" at 0,1 icon=client color=blue
node primary "Primary DB" at 2,0 icon=db color=green
node replica "Read Replica" at 2,2 icon=db color=amber

client -> primary : "1. write(x=1)"
primary ..> replica : "async replication\n(lag)"
client -> replica : "2. read(x) -> 0"
```
A read replica offloads read traffic and can improve geographic locality, but replication is asynchronous by default, so a replica can lag behind the primary by anywhere from milliseconds to seconds under load.

Never casually route a correctness-sensitive read — "did my write take effect" — to a replica that might not have it yet. Options, cheapest first:

| Approach | Mechanism | Cost |
|---|---|---|
| Read-your-writes window | Route reads for a user to the primary for N seconds after their own write. | Simple; adds primary load for that window. |
| Sticky session to primary | Pin a request/session that just wrote to the primary for subsequent reads. | Needs session affinity plumbing. |
| Replica lag tracking | Read the replica's replication position; reject/redirect if lag exceeds a bound. | Needs lag observability per replica. |
| Read from primary always for that query class | Skip the replica entirely for correctness-critical reads. | Simplest, costs primary capacity. |

Default posture: replicas are for read-scaling of tolerant queries (dashboards, catalogs, search-adjacent reads), not for "did my mutation just succeed."

## The read-available-then-subtract race

A classic bug shape: read current stock, check it's enough, then write the decremented value in a separate step.

```text
Request A: read available=1        Request B: read available=1
Request A: 1 >= 1, proceed         Request B: 1 >= 1, proceed
Request A: write available=0       Request B: write available=0
```

Both requests observed availability before either committed a change, so both "succeed" and you've oversold by one unit. A transaction around the read+write does not fix this by itself under weaker isolation levels — the read snapshot can still be taken before the other transaction's write is visible.

The fix is to make the database arbitrate the race directly with a conditional mutation, not a read-then-decide in application code:

```sql
UPDATE inventory
SET available = available - :qty
WHERE sku = :sku AND available >= :qty;
```

If zero rows are affected, the item was unavailable — the `WHERE` clause re-checks the invariant atomically against whatever the current row value is at the moment of the write, not a value read earlier. This pattern generalizes: any "check then act" business rule against a mutable row should be expressed as a single conditional `UPDATE`/`INSERT ... ON CONFLICT` rather than a read step followed by a write step.

For the deeper mechanics of *why* isolation levels allow or prevent this — dirty reads, non-repeatable reads, write skew, optimistic vs. pessimistic concurrency — see [Transactions, Isolation, Locking, and Sagas](11_transactions_and_concurrency.md).

## Indexes, measured

The indexing rules above are easy to state and easy to doubt. Here they are measured on a
million-row `orders` table in SQLite (the numbers differ in PostgreSQL or MySQL; the shape does
not — [Indexing and Query Planning](../../../data-and-apis/SQL/10_indexing_and_query_planning.md) measures PostgreSQL):

```python
"""Indexes, measured with SQLite (in memory): what an index buys a read,
what the leading-column rule means, and what each index costs a write."""
import random
import sqlite3
import time

rng = random.Random(5)
ROWS = 1_000_000
rows = [(rng.randrange(50_000), rng.randrange(10**9), rng.randrange(10_000)) for _ in range(ROWS)]


def fresh():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INT, created_at INT, total INT)")
    db.executemany("INSERT INTO orders (user_id, created_at, total) VALUES (?, ?, ?)", rows)
    return db


def timed(db, sql, args=(), reps=20):
    best = float("inf")
    for _ in range(reps):
        t = time.perf_counter()
        db.execute(sql, args).fetchall()
        best = min(best, time.perf_counter() - t)
    plan = " / ".join(r[-1] for r in db.execute("EXPLAIN QUERY PLAN " + sql, args))
    return best * 1000, plan


RECENT = "SELECT created_at, total FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 20"
db = fresh()
print("1) a user's 20 most recent orders, 1,000,000 rows")
ms, plan = timed(db, RECENT, (123,), reps=3)
print(f"   no index                  {ms:8.3f} ms   {plan}")
db.execute("CREATE INDEX by_user_time ON orders (user_id, created_at)")
ms, plan = timed(db, RECENT, (123,))
print(f"   index (user_id, created)  {ms:8.3f} ms   {plan}")
db.execute("CREATE INDEX by_user_time_total ON orders (user_id, created_at, total)")
ms, plan = timed(db, RECENT, (123,))
print(f"   + covering (… , total)    {ms:8.3f} ms   {plan}")

print("2) the leading-column rule: the same index, a query that skips user_id")
ms, plan = timed(db, "SELECT count(*) FROM orders WHERE created_at BETWEEN ? AND ?", (5 * 10**8, 5 * 10**8 + 10**6), reps=3)
print(f"   created_at range only     {ms:8.3f} ms   {plan}")

print("3) what indexes cost a write: inserting 200,000 rows")
batch = rows[:200_000]
for n_idx in (0, 1, 3, 5):
    w = sqlite3.connect(":memory:")
    w.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, a INT, b INT, c INT)")
    cols = ["a", "b", "c", "a, b", "b, c"][:n_idx]
    for i, c in enumerate(cols):
        w.execute(f"CREATE INDEX i{i} ON t ({c})")
    t = time.perf_counter()
    w.executemany("INSERT INTO t (a, b, c) VALUES (?, ?, ?)", batch)
    w.commit()
    dt = time.perf_counter() - t
    print(f"   {n_idx} secondary indexes:  {len(batch) / dt:9,.0f} rows/s")
```

```text
1) a user's 20 most recent orders, 1,000,000 rows
   no index                    35.142 ms   SCAN orders / USE TEMP B-TREE FOR ORDER BY
   index (user_id, created)     0.013 ms   SEARCH orders USING INDEX by_user_time (user_id=?)
   + covering (… , total)       0.008 ms   SEARCH orders USING COVERING INDEX by_user_time_total (user_id=?)
2) the leading-column rule: the same index, a query that skips user_id
   created_at range only       33.847 ms   SCAN orders USING COVERING INDEX by_user_time
3) what indexes cost a write: inserting 200,000 rows
   0 secondary indexes:  1,540,943 rows/s
   1 secondary indexes:    660,743 rows/s
   3 secondary indexes:    255,826 rows/s
   5 secondary indexes:    137,951 rows/s
```

- **The right index turns a scan into a lookup.** Without an index, "20 most recent orders for one
  user" reads all million rows and sorts the matches: 35 ms. With `(user_id, created_at)` the
  database jumps to user 123 and walks that user's entries already in time order: 0.013 ms —
  about 2,700× faster, and the gap grows with the table.
- **A covering index skips the table entirely** (`USING COVERING INDEX`) — here from 0.013 to
  0.008 ms. The saving matters more when many rows are returned, because each avoided table lookup
  is a random read.
- **The leading-column rule is real.** The same `(user_id, created_at)` index can't serve a
  `created_at` range on its own: the plan becomes a `SCAN` of the whole index (34 ms), no faster
  than no index at all.
- **Every index is paid for on every write.** Insert throughput fell from 1.54 million rows/s with
  no secondary indexes to 661,000 with one and 138,000 with five, because each insert must also
  update every index's B-tree. On a disk-backed, replicated production database each extra write
  also costs WAL volume and replication bandwidth. Index the queries you run; drop the ones nobody
  uses.

## Modeling from access patterns, worked

Schemas that survive production are designed from the **queries**, not from the nouns. A worked
example for an online shop:

**1. List the access patterns, with rates and consistency needs.**

| # | Access pattern | Rate | Needs |
|---|---|---|---|
| A | Get a product by ID | Very high | Can be slightly stale (cache) |
| B | Place an order: reserve stock, create order + items | High | Atomic; stock never negative |
| C | A user's recent orders, newest first | High | Read-your-writes for the buyer |
| D | An order with its items | High | Consistent with B |
| E | Orders by status for the warehouse, oldest first | Medium | Fresh within seconds |
| F | Revenue by day by category | Low | Analytics; minutes stale is fine |

**2. Relational model and the index each pattern needs.**

```sql
CREATE TABLE products (id BIGINT PRIMARY KEY, category TEXT NOT NULL, price_cents INT NOT NULL,
                       stock INT NOT NULL CHECK (stock >= 0));                      -- A; invariant for B
CREATE TABLE orders   (id BIGINT PRIMARY KEY, user_id BIGINT NOT NULL, status TEXT NOT NULL,
                       created_at TIMESTAMPTZ NOT NULL, total_cents INT NOT NULL);
CREATE TABLE order_items (order_id BIGINT REFERENCES orders(id), product_id BIGINT REFERENCES products(id),
                          qty INT NOT NULL CHECK (qty > 0), price_cents INT NOT NULL,
                          PRIMARY KEY (order_id, product_id));                          -- D: items by order
CREATE INDEX orders_by_user   ON orders (user_id, created_at DESC) INCLUDE (status, total_cents);  -- C
CREATE INDEX orders_by_status ON orders (status, created_at) WHERE status IN ('PAID', 'PICKING'); -- E, partial
```

- **B** is one transaction: a conditional `UPDATE products SET stock = stock - :q WHERE id = :p AND
  stock >= :q` per item (the race-free pattern below), then the inserts. The `CHECK` is the last line
  of defence.
- **E** uses a *partial* index: only the few thousand open orders are indexed, not the millions of
  delivered ones.
- **F** doesn't get an index at all: it is served by an analytical copy fed by change data capture.
  Adding it to the OLTP database would add write cost for a query that runs once a day.
- **A** is read-heavy and tolerates staleness, so it sits behind a cache ([Caching](07_caching.md)).

**3. The same patterns in a key-value / wide-column store.** Without joins, the key design *is*
the query design — one item collection per access pattern ([Wide-Column and DynamoDB-Style Databases](../../../data-and-apis/NoSQL/concepts/00_wide_column_and_dynamodb_style_databases.md)):

| Pattern | Partition key | Sort key | Item |
|---|---|---|---|
| C, D | `USER#17` | `ORDER#2026-09-30T10:00#9001` | Order summary |
| D | `ORDER#9001` | `ITEM#<product>` | One line item each |
| E | `STATUS#PAID#<day>` | `<created_at>#<order>` | A projection written when status changes |
| A | `PRODUCT#555` | `META` | Product |

Each query is now one partition read, which scales almost without limit — but the invariants moved
into the application: stock reservation needs a conditional write, the order and its items need a
transaction or an idempotent retry, and the status projection must be kept in sync. That is the
trade in one sentence: **relational stores enforce invariants and let you add queries later;
key-value stores give predictable scale for the queries you designed up front.**

## Scaling a database, in order

When the primary gets hot, the cheap steps come first, and each one should be justified by a
measurement:

| Step | Fixes | Cost / limit |
|---|---|---|
| 1. Find the slow queries (`pg_stat_statements`, slow log) and fix indexes and query shapes | Most "the database is slow" incidents | Engineering time only |
| 2. Pool connections (PgBouncer) | Too many connections, per-connection memory | Transaction-pooling limits some session features |
| 3. Cache hot reads ([Caching](07_caching.md)) | Read-heavy, staleness-tolerant queries | Invalidation, stampedes |
| 4. Read replicas | Read throughput, analytics isolation | Replication lag (next section); writes unchanged |
| 5. Scale up the primary | Everything, briefly | A ceiling, and a bigger failure blast radius |
| 6. Move data out: archive cold rows, split analytics, split by function (Y-axis) | Table size, mixed workloads | New pipelines; cross-database queries disappear |
| 7. Partition / shard by key ([Partitioning, Shard Keys, and Hot Keys](25_partitioning_and_hot_keys.md)) | Write throughput and size beyond one machine | Cross-shard joins, transactions and uniqueness become design problems |
| 8. A distributed SQL database (Spanner, CockroachDB, Yugabyte) | Sharding plus transactions, managed by the database | Latency of consensus writes, cost, operational novelty |

Interviewers probe the order as much as the steps: sharding first, without evidence that indexes,
caching and replicas are exhausted, signals inexperience.

## What each level should know

| Topic | L4 · Mid | L5 · Senior | L6+ · Staff |
|---|---|---|---|
| **Guarantees and families** | Knows relational is the default | Names which guarantee each alternative gives up; separates OLTP and OLAP | Chooses stores across a product line and owns the consistency story between them |
| **Modeling** | Designs tables from entities | Designs from access patterns; picks keys, constraints and partial/covering indexes | Plans schema evolution and migrations at scale (expand, migrate, contract) |
| **Indexes** | Adds an index for a slow query | Explains leading columns, covering indexes, selectivity and write cost with numbers | Sets indexing and query-review practice for many teams |
| **Replicas and races** | Uses replicas for reads | Handles read-your-writes and the check-then-act race with conditional writes | Designs consistency guarantees per query class |
| **Scaling** | Knows sharding exists | Walks the scaling ladder in order with triggers | Plans multi-year data growth, including moves to partitioned or distributed SQL |

## Interview checklist

- [ ] I can list the four guarantees a database provides and say which a cache or key-value store gives up.
- [ ] I can separate OLTP from OLAP and explain why analytics shouldn't run on the primary.
- [ ] I can pick a database family for a workload and say why the relational default doesn't fit (or does).
- [ ] I can design a schema from access patterns, with keys, constraints and the index for each query.
- [ ] I can explain leading-column, covering and partial indexes, and quantify what indexes cost writes.
- [ ] I can translate a relational model into partition and sort keys, and say where the invariants go.
- [ ] I can walk the database scaling ladder in order, with the trigger and cost of each step.

## Related building blocks

- [Database Internals: How They Actually Work](06_database_internals.md)
- [Transactions, Isolation, Locking, and Sagas](11_transactions_and_concurrency.md)
- [Caching](07_caching.md)
- [Scaling and Load Balancing](13_scaling_and_load_balancing.md)
- [Decision Framework](17_decision_framework.md)
