# Databases: Source of Truth

The database is where a business fact becomes durable and authoritative. Everything else in a system — cache, search index, warehouse — is a derived copy that can be rebuilt. The database cannot be "rebuilt"; if it loses a fact, the fact is gone.

Default to a relational database (PostgreSQL/MySQL) for user, order, catalog, and permission workflows. Constraints, indexes, joins, and transactions model real invariants directly instead of pushing them into application code. Reach for something else only when a specific access pattern or scale limit justifies it — see `06_database_internals.md` for the family comparison.

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

For the deeper mechanics of *why* isolation levels allow or prevent this — dirty reads, non-repeatable reads, write skew, optimistic vs. pessimistic concurrency — see `11_transactions_and_concurrency.md`.

## Related building blocks

- [06_database_internals.md](06_database_internals.md)
- [11_transactions_and_concurrency.md](11_transactions_and_concurrency.md)
- [07_caching.md](07_caching.md)
- [13_scaling_and_load_balancing.md](13_scaling_and_load_balancing.md)
- [17_decision_framework.md](17_decision_framework.md)
