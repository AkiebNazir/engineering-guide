# Sharding and Horizontal Scaling

**Already covered elsewhere:** `SystemDesign/building_blocks/` covers sharding as a
general distributed-systems concept (consistent hashing, shard key selection at the
architecture level). This level is specifically about what's *hard about sharding a
relational database* — joins, transactions, and foreign keys don't shard for free the
way a key-value store's lookups do — and about Postgres's own built-in partitioning,
which solves a narrower, adjacent problem and is frequently confused with sharding in
interviews.

## The mental model: scaling reads vs. scaling writes

Level 17's replicas scale **reads** — every replica has a full copy of the data, so
read traffic spreads across them. They do nothing for **write** throughput: every
write still has to land on the single primary and gets shipped to every replica.
**Sharding** (a.k.a. horizontal partitioning across servers) is the answer for write
scaling: split the data itself across multiple independent database instances (shards),
each owning a disjoint slice of the rows, so writes to different shards can happen in
parallel on different machines.

This is the point where relational databases stop being simple. A single-instance
Postgres gives you free joins, free foreign keys, and free multi-row transactions
because everything lives on one machine. The moment `orders` and `customers` live on
*different* shards:

- **A join across shards** can no longer run as one query inside the database — it
  requires the application (or a routing layer) to query both shards and join in
  memory, or a distributed-query extension (Citus, `postgres_fdw`) that does this for
  you at real latency and complexity cost.
- **A foreign key across shards** cannot be enforced by the database at all — Postgres
  has no mechanism to check a constraint against a row that isn't in the same instance.
- **A transaction touching rows on two shards** needs a distributed-transaction
  protocol (two-phase commit) or has to be redesigned to avoid needing atomicity across
  shards in the first place — plain `BEGIN`/`COMMIT` only guarantees atomicity within
  one Postgres instance.

**The single most important sharding decision is the shard (partition) key** — the
column whose value decides which shard a row lives on. Choose one that keeps almost
all of your queries and transactions confined to a single shard (e.g., shard `orders`
by `customer_id`, since "show me this customer's orders" is the overwhelmingly common
query and lands entirely on one shard), or you've paid all of sharding's complexity
cost while still needing cross-shard joins on your hot path.

## Postgres's own answer to part of this: declarative partitioning

Before reaching for multiple servers, Postgres can split **one** table into multiple
physical sub-tables (**partitions**) *within a single instance*, transparently, via
`PARTITION BY`. This is not sharding — every partition still lives on the same
machine, in the same instance, so joins/foreign keys/transactions across partitions
work exactly as normal — but it solves a real, adjacent, very-commonly-asked-about
problem: a single table too large for its indexes to stay efficient, or one where old
data (last year's logs) needs to be dropped in O(1) instead of a slow `DELETE`.

**Demo, measured: same 2,000,000-row range query, flat+indexed vs. partitioned.**

```sql
DROP TABLE IF EXISTS events_flat;
DROP TABLE IF EXISTS events_part CASCADE;

-- Flat table, one B-tree index on the date column.
CREATE TABLE events_flat (
    id          BIGINT GENERATED ALWAYS AS IDENTITY,
    occurred_at DATE NOT NULL,
    payload     TEXT NOT NULL
);
INSERT INTO events_flat (occurred_at, payload)
SELECT DATE '2026-01-01' + (i % 365), 'payload_' || i
FROM generate_series(1, 2000000) AS i;
CREATE INDEX idx_events_flat_date ON events_flat (occurred_at);
ANALYZE events_flat;

-- Same data, range-partitioned by month.
CREATE TABLE events_part (
    id          BIGINT GENERATED ALWAYS AS IDENTITY,
    occurred_at DATE NOT NULL,
    payload     TEXT NOT NULL
) PARTITION BY RANGE (occurred_at);

CREATE TABLE events_part_2026_01 PARTITION OF events_part FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE events_part_2026_02 PARTITION OF events_part FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE events_part_2026_03 PARTITION OF events_part FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
CREATE TABLE events_part_rest    PARTITION OF events_part DEFAULT;

INSERT INTO events_part (occurred_at, payload) SELECT occurred_at, payload FROM events_flat;
ANALYZE events_part;
```

Same query — one month's worth of rows — against both:

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT count(*) FROM events_flat
WHERE occurred_at >= '2026-02-01' AND occurred_at < '2026-03-01';

EXPLAIN (ANALYZE, BUFFERS) SELECT count(*) FROM events_part
WHERE occurred_at >= '2026-02-01' AND occurred_at < '2026-03-01';
```

Real captured output, flat table (bitmap index scan over the whole indexed table):

```text
Parallel Bitmap Heap Scan on events_flat
  Recheck Cond: ((occurred_at >= '2026-02-01') AND (occurred_at < '2026-03-01'))
Execution Time: 26.294 ms
```

Real captured output, partitioned table:

```text
Parallel Seq Scan on events_part_2026_02 events_part
  Filter: ((occurred_at >= '2026-02-01') AND (occurred_at < '2026-03-01'))
Execution Time: 8.357 ms
```

**The same comparison, run from Go** (native `pgxpool`, `EXPLAIN (ANALYZE, BUFFERS)`
issued as a query and its output rows printed directly — Postgres returns `EXPLAIN`'s
output as ordinary text rows, so no special client-side support is needed in any
language):

```go
rows, _ := pool.Query(ctx, "EXPLAIN (ANALYZE, BUFFERS) "+query)
for rows.Next() {
    var line string
    rows.Scan(&line)
    fmt.Println(line)
}
```

Real output, same two queries, same two tables (rebuilt identically under `_go`-suffixed
names to avoid colliding with the originals), run independently from Go:

```text
--- flat + indexed ---
Parallel Bitmap Heap Scan on events_flat_go
  Recheck Cond: ((occurred_at >= '2026-02-01') AND (occurred_at < '2026-03-01'))
Execution Time: 22.987 ms
--- partitioned ---
Parallel Seq Scan on events_part_go_2026_02 events_part_go
  Filter: ((occurred_at >= '2026-02-01') AND (occurred_at < '2026-03-01'))
Execution Time: 8.686 ms
```

**22.987ms → 8.686ms this run** (vs. 26.294ms → 8.357ms in the original Python-driven
run above) — the exact millisecond figures move a little between runs, as real
measurements always do on a shared machine, but the result that actually matters is
identical and stable both times: the partitioned plan touches exactly one partition
(`events_part_go_2026_02`), never the other three. That pruning behavior — not the
specific millisecond count — is the fact worth remembering, and it's Postgres's
planner doing the same work regardless of which client language sent the query.

**26.294ms → 8.357ms, roughly 3x faster** — but the *plan itself* is the real proof,
not just the timing: notice the partitioned plan mentions exactly **one** partition,
`events_part_2026_02`. Postgres's planner performed **partition pruning** — it looked
at the query's `WHERE` clause, matched it against each partition's declared range, and
never even considered `events_part_2026_01`, `events_part_2026_03`, or
`events_part_rest`. The flat table's plan, by contrast, had to consult an index that
spans all 2,000,000 rows. At real production scale (partitioning a genuinely huge
table by month, then dropping partitions older than a retention window with
`DROP TABLE events_part_2025_01` instead of a `DELETE` that has to find and remove
millions of individual rows), pruning is the entire point.

## Partitioning vs. sharding: don't conflate them in an interview

| | **Partitioning** (this level) | **Sharding** |
|---|---|---|
| Where the data lives | One table, one Postgres instance, split into physical sub-tables | Multiple independent Postgres instances (or a distributed system like Citus/Vitess/CockroachDB) |
| Joins across the split | Free — same instance, same transaction | Requires application-level joins, a distributed query layer, or redesigning the query |
| Foreign keys across the split | Enforced normally | Not enforceable by the database at all |
| Solves | Query/maintenance efficiency on one very large table (index size, bulk retention drops) | **Write throughput** and total storage beyond what one machine can hold |
| Common strategies | Range (dates, IDs), list (region, tenant), hash (even spread with no natural range) | Same key strategies, but the key now decides which *server*, not which sub-table |

A single-instance partitioned table can be a **step toward** sharding — Postgres
extensions like **Citus** turn declarative partitions into shards distributed across
multiple physical nodes, reusing the same `PARTITION BY`-style key concept — but
plain, vanilla Postgres partitioning by itself never crosses a machine boundary.

```arch
%% caption: Partitioning splits a table within a single database instance; Sharding splits data across multiple independent database servers.
group part "Partitioning (Single Node)" color=slate style=dashed
node db1 "Database Server" at 0,0 in part icon=server color=blue
node p1 "Table (Jan)" at -0.5,1 in part icon=table color=green
node p2 "Table (Feb)" at 0.5,1 in part icon=table color=green

db1 -> p1 : "local route"
db1 -> p2 : "local route"

group shard "Sharding (Multi-Node)" color=slate style=dashed
node router "Router / Proxy" at 4,0 in shard icon=proxy color=blue
node s1 "Server 1 (A-M)" at 3,1 in shard icon=server color=amber
node s2 "Server 2 (N-Z)" at 5,1 in shard icon=server color=amber

router -> s1 : "network route"
router -> s2 : "network route"
```

## Sharding strategies, and what breaks with each

- **Range sharding** (shard by ID or date range, e.g. users 1–1M on shard A). Simple,
  but creates **hot shards**: new users (and new writes) always land on the
  most-recent shard until it fills, while older shards go cold — the same "everyone
  writes to the newest partition" problem levels 04/10 discuss for indexes, one level
  up in scale.
- **Hash sharding** (shard by `hash(user_id) % N`). Spreads write load evenly, but a
  range query ("all orders from March") now has to fan out to every shard, since
  consecutive IDs land on unrelated shards.
- **Directory/lookup-based sharding** (a separate mapping service tells you which
  shard a given key lives on). Most flexible — supports rebalancing without a formula
  change — but the lookup service itself becomes a critical, must-scale dependency.

**Resharding is the operational cost nobody's diagram shows.** Changing the number of
shards (adding capacity) means re-distributing existing data according to the new
scheme, live, without downtime — this is genuinely one of the hardest problems in
distributed data systems, which is why consistent hashing (covered at the concept
level in `SystemDesign/building_blocks/`) exists specifically to minimize how much data
moves when the shard count changes.

## Common mistakes

- **Sharding before you need to.** A single well-indexed, well-partitioned Postgres
  instance handles far more write throughput than most systems ever need — sharding's
  complexity (no free joins, no free FKs, no free cross-shard transactions) is a real
  cost, not a free scaling knob to reach for early.
- **Calling table partitioning "sharding" in an interview.** They solve different
  problems (see the table above) — an interviewer asking "how would you scale writes
  past one machine" wants sharding, not a `PARTITION BY` answer.
- **Picking a shard key by convenience (e.g., auto-increment ID) instead of by query
  pattern.** If most queries filter by `customer_id`, sharding by raw `id` forces
  those queries to fan out to every shard instead of hitting one.
- **Not planning for resharding.** A hash-mod-N scheme where N is hardcoded means
  changing shard count re-maps almost every key — consistent hashing exists precisely
  to avoid this.

## What's next

Level 19 is an interview-focused playbook: the concrete questions this ladder gets
asked as, and how to answer them precisely instead of just recognizing the
vocabulary.
