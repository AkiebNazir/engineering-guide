# Indexing and Query Planning

## The mental model

Without an index, finding rows that match a condition means checking every row in
the table — a **sequential scan**. An index is a separate, ordered data structure
(Postgres's default is a **B-tree**) that lets the database jump almost directly to
matching rows instead. The trade is real, not free: an index makes the matching
reads much faster and every write to the indexed column(s) slightly slower (the
index itself has to be updated too). `EXPLAIN`/`EXPLAIN ANALYZE` is how you stop
guessing about this trade-off and actually look at what Postgres is doing.

## Setup used for this level

A table large enough that a sequential scan actually costs something measurable —
300,000 rows:

```sql
CREATE TABLE accounts_big (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email      TEXT NOT NULL,
    country    TEXT NOT NULL,
    status     TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO accounts_big (email, country, status)
SELECT
    'user' || i || '@example.com',
    (ARRAY['US','UK','DE','FR','BR','IN'])[1 + floor(random()*6)::int],
    (ARRAY['active','suspended','closed'])[1 + floor(random()*3)::int]
FROM generate_series(1, 300000) AS i;

ANALYZE accounts_big;   -- refresh planner statistics after a bulk load
```

`ANALYZE` matters: Postgres's query planner decides seq-scan-vs-index-scan based on
*statistics* about the table (row counts, how selective a value is), not by
recomputing from scratch every time. Skip it after a big bulk load and the planner
can make bad choices based on stale statistics.

## `EXPLAIN` vs `EXPLAIN ANALYZE`

`EXPLAIN` shows the planner's *chosen plan and cost estimate* without running the
query. `EXPLAIN ANALYZE` actually **runs** the query and shows real measured time and
row counts alongside the estimate — always prefer `ANALYZE` when you're diagnosing a
real performance question, since the estimate alone can be wrong. (Caution: `EXPLAIN
ANALYZE` really executes the query, including any `INSERT`/`UPDATE`/`DELETE` — never
run it on a destructive statement against real data without a transaction you intend
to roll back.)

## Measured: sequential scan vs index scan, same query, same data

No index on `email` yet — a point lookup for one specific email address:

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM accounts_big WHERE email = 'user123456@example.com';
```

Real output:

```text
Gather  (cost=1000.00..6235.98 rows=1 width=48) (actual time=5.196..5.859 rows=1 loops=1)
  Workers Planned: 1
  Workers Launched: 1
  Buffers: shared hit=3030
  ->  Parallel Seq Scan on accounts_big  (cost=0.00..5235.88 rows=1 width=48) (actual time=3.300..4.655 rows=0 loops=2)
        Filter: (email = 'user123456@example.com'::text)
        Rows Removed by Filter: 150000
        Buffers: shared hit=3030
Planning Time: 0.050 ms
Execution Time: 5.865 ms
```

Postgres even parallelized the scan across a worker process and it *still* took
**5.865 ms**, having read all 3,030 pages of the table (`Buffers: shared hit=3030`)
and thrown away ~150,000 non-matching rows per worker to find the one row that
matched.

Now add an index and re-run the identical query:

```sql
CREATE INDEX idx_accounts_big_email ON accounts_big (email);
ANALYZE accounts_big;

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM accounts_big WHERE email = 'user123456@example.com';
```

```text
Index Scan using idx_accounts_big_email on accounts_big  (cost=0.42..8.44 rows=1 width=49) (actual time=0.016..0.017 rows=1 loops=1)
  Index Cond: (email = 'user123456@example.com'::text)
  Buffers: shared hit=1 read=3
Planning Time: 0.059 ms
Execution Time: 0.024 ms
```

**5.865 ms → 0.024 ms — roughly 244x faster**, on the exact same table and query,
having read 4 buffer pages instead of 3,030. This is not a hypothetical
"indexes are faster" claim — it's the same query, measured, before and after, on
300,000 real rows.

**Go (native pgxpool):** the query plan is a property of the database, not the
client language — running the identical `EXPLAIN` through Go instead of `psql`
produces the same plan shape, proving the point:

```go
pool, err := pgxpool.New(ctx, "postgresql://dsa:dsa@localhost:5544/dsa")
if err != nil {
    log.Fatal(err)
}
defer pool.Close()

rows, err := pool.Query(ctx, `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
    SELECT * FROM accounts_big WHERE email = 'user123456@example.com';`)
if err != nil {
    log.Fatal(err)
}
defer rows.Close()
for rows.Next() {
    var line string
    rows.Scan(&line)
    fmt.Println(line)
}
```

Real output — an `Index Scan` again, sub-millisecond, same index:

```text
Index Scan using idx_accounts_big_email on accounts_big  (cost=0.42..8.44 rows=1 width=72) (actual time=0.164..0.165 rows=1 loops=1)
  Index Cond: (email = 'user123456@example.com'::text)
  Buffers: shared read=4
Planning:
  Buffers: shared hit=117
Planning Time: 0.263 ms
Execution Time: 0.197 ms
```

The exact millisecond values differ run to run (cache warmth, scheduler noise) — the
part that doesn't change is *which plan* Postgres picks, because that decision is made
entirely inside the database, before a single row is sent back to whichever client
asked for it.

```arch
%% caption: A sequential scan reads every page of the table; an index scan traverses a B-tree to read only the few pages containing the match.
group seq "Sequential Scan (No Index)" color=red style=dashed
node full "Table Data\n(Reads 3,000+ pages)" at 0,0 in seq icon=db
node filter "Filter Rows\n(Discards 299,999)" at 0,1 in seq icon=filter

full -> filter : "scan all"

group idx "Index Scan (With Index)" color=green style=dashed
node btree "B-Tree Index\n(Reads 3 pages)" at 3,0 in idx icon=tree
node targeted "Table Data\n(Reads 1 page)" at 3,1 in idx icon=db

btree -> targeted : "pointer"
```

## Composite index column order matters

A composite (multi-column) index `(a, b)` is only usable, as an index, for
predicates that constrain a **prefix** of its columns — `a` alone, or `a AND b`
together — not for `b` alone, in the same way a phone book sorted by (last name,
first name) lets you jump straight to "Smith, John" but is useless for finding
everyone named "John" regardless of last name.

```sql
CREATE INDEX idx_accounts_big_country_status ON accounts_big (country, status);
ANALYZE accounts_big;
```

Querying on both columns of the composite index, in order:

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT count(*) FROM accounts_big WHERE country = 'DE' AND status = 'active';
```

```text
Aggregate  (cost=3548.69..3548.70 rows=1 width=8) (actual time=3.247..3.247 rows=1 loops=1)
  ->  Bitmap Heap Scan on accounts_big  (cost=229.69..3507.40 rows=16514 width=0) (actual time=0.442..2.889 rows=16612 loops=1)
        Recheck Cond: ((country = 'DE'::text) AND (status = 'active'::text))
        Heap Blocks: exact=3018
        ->  Bitmap Index Scan on idx_accounts_big_country_status  (cost=0.00..225.56 rows=16514 width=0) (actual time=0.272..0.272 rows=16612 loops=1)
              Index Cond: ((country = 'DE'::text) AND (status = 'active'::text))
Execution Time: 3.258 ms
```

The composite index was used (`Bitmap Index Scan using idx_accounts_big_country_status`),
matching both columns.

Now query on `status` **alone** — the second column of the composite index, without
the first:

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT count(*) FROM accounts_big WHERE status = 'active';
```

```text
Finalize Aggregate  (cost=6382.41..6382.42 rows=1 width=8) (actual time=8.780..9.506 rows=1 loops=1)
  ->  Gather  (cost=6382.29..6382.40 rows=1 width=8) (actual time=8.746..9.504 rows=2 loops=1)
        ->  Partial Aggregate  (cost=5382.29..5382.30 rows=1 width=8) (actual time=8.084..8.084 rows=1 loops=2)
              ->  Parallel Seq Scan on accounts_big  (cost=0.00..5235.88 rows=58565 width=0) (actual time=0.005..6.935 rows=49912 loops=2)
                    Filter: (status = 'active'::text)
                    Rows Removed by Filter: 100088
Execution Time: 9.514 ms
```

The composite index `(country, status)` was **not used at all** — Postgres fell
back to a parallel sequential scan (9.514 ms), because `status` alone doesn't touch
the index's leading column. This is exactly the "column order matters" claim, shown
rather than asserted: same table, same total data, and whether the index helps
depends entirely on which column of the *query's* predicate lines up with the
*index's* leading column. If both single-column and `status`-first queries were
common in a real workload, the fix would be a second index with `status` leading
(`(status, country)`), or a single index in whichever order matches the more
selective, more frequently-filtered-alone column.

## Common mistakes

- **Indexing every column "just in case."** Every index slows every write to that
  column and costs storage — index for queries you actually run, and verify with
  `EXPLAIN ANALYZE` that the index is actually chosen, not just present.
- **Trusting `EXPLAIN`'s estimated cost/rows without `ANALYZE`.** Estimates can be
  wrong when statistics are stale (see the `ANALYZE` note above) or when the
  planner's assumptions about data distribution don't hold.
- **Assuming a composite index helps a query on any of its columns.** As measured
  above, only prefix-matching predicates can use it.
- **Forgetting to re-run `ANALYZE` after a large bulk load or bulk delete.** The
  planner's row-count and selectivity estimates go stale, which can silently flip a
  query from an index scan to a sequential scan (or vice versa, wrongly).

## What's next

Level 11 is a hard turn into security: building a genuinely exploitable query,
attacking it for real, then fixing it.
