# Filtering, Sorting, Pagination

## The mental model

`WHERE` picks which rows come back; `ORDER BY` decides what order they come back in;
`LIMIT`/`OFFSET` (or keyset pagination) decides which slice of that ordered set you
actually see. These three combine into almost every "show me a page of results"
query you'll ever write — and the difference between the naive and the correct way
to do the third one is one of the most common real-world performance bugs in SQL.

## Setup used for this level

```sql
DROP TABLE IF EXISTS events;

CREATE TABLE events (
    id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    kind    TEXT NOT NULL,
    payload TEXT NOT NULL
);

INSERT INTO events (kind, payload)
SELECT
    (ARRAY['click','view','purchase','signup'])[1 + floor(random()*4)::int],
    md5(random()::text)
FROM generate_series(1, 500000);
```

500,000 rows — enough to make the pagination cost in this level real and measurable,
not theoretical.

## `WHERE`: comparison and logical operators

```sql
SELECT id, kind FROM events WHERE kind = 'purchase' ORDER BY id DESC LIMIT 3;
```

```text
   id   |   kind
--------+----------
 499994 | purchase
 499993 | purchase
 499990 | purchase
```

Standard comparison operators: `=`, `<>` (or `!=`), `<`, `<=`, `>`, `>=`. Combine
conditions with `AND`/`OR`/`NOT`, and remember `AND` binds tighter than `OR` — wrap
mixed conditions in parentheses:

```sql
WHERE kind = 'purchase' AND (payload LIKE 'a%' OR payload LIKE 'b%')
```

Other operators worth knowing immediately: `IN (...)` for "matches any of these
values," `BETWEEN a AND b` for an inclusive range, `IS NULL`/`IS NOT NULL` (never
`= NULL` — `NULL` compared with `=` to anything, including another `NULL`, evaluates
to unknown, not true), and `LIKE`/`ILIKE` for pattern matching (`ILIKE` is Postgres's
case-insensitive variant).

## `ORDER BY`

```sql
SELECT id, kind FROM events ORDER BY id DESC LIMIT 3;
```

Sorts ascending (`ASC`, the default) or descending (`DESC`). You can sort by
multiple columns (`ORDER BY kind, id DESC`) and by an expression, not just a column
name.

## `LIMIT`/`OFFSET` — and why it degrades

The obvious way to paginate is to ask for successive slices:

```sql
-- "page 1" (rows 1-20)
SELECT id, kind FROM events ORDER BY id LIMIT 20 OFFSET 0;
-- "page 2501" (rows 50,001-50,020)
SELECT id, kind FROM events ORDER BY id LIMIT 20 OFFSET 50000;
```

The problem: Postgres can't skip straight to row 50,001 of a sorted result. It has
to walk the index (or scan the table) counting off and discarding the first 50,000
matching rows before it can return your 20. The further into the table you page, the
more rows get thrown away just to find your starting point — cost grows linearly
with the offset.

Measured on this environment, timing `SELECT id, kind FROM events ORDER BY id LIMIT 20 OFFSET :n`
at increasing offsets (best of 3 runs each, on the 500,000-row table above):

```text
OFFSET       0: 0.32 ms
OFFSET   50000: 2.24 ms
OFFSET  490000: 20.78 ms
```

Offset 490,000 is roughly **65x slower** than offset 0, on the exact same query
shape, purely because of how far into the table it has to walk and discard rows.
This is not a small-table artifact — it gets worse, not better, as the table grows,
which is exactly backwards from what you want out of "page 10,000 of my results."

## Keyset (seek) pagination — the fix

Instead of "skip N rows," keyset pagination asks "give me the next rows after the
last one I saw." It needs the previous page's last sort-key value, which the caller
(the <abbr title="Application Programming Interface">API</abbr> client, typically) already has:

```sql
-- first page
SELECT id, kind FROM events ORDER BY id LIMIT 20;
-- next page: caller passes back the last id it received, say 20
SELECT id, kind FROM events WHERE id > 20 ORDER BY id LIMIT 20;
```

With an index on `id` (the primary key already provides one), `WHERE id > :cursor`
seeks directly to the right starting point — no counting and discarding rows along
the way. Measured on the same table and query shape as above:

```text
keyset after id=490000: 0.35 ms
keyset after id=0:      0.35 ms
```

Constant time regardless of how deep into the table you're paging — 0.35 ms whether
you're on page 1 or page 25,000, versus `OFFSET`'s 20.78 ms at the deep end of the
exact same dataset.

**The same measurement, in Go (native `pgxpool`)** — same table, same three offsets,
same two keyset cursors, timed the same way (best of 3 runs each):

```go
pool, _ := pgxpool.New(ctx, "postgresql://dsa:dsa@localhost:5544/dsa")

timeIt := func(sql string, args ...any) time.Duration {
    var best time.Duration
    for i := 0; i < 3; i++ {
        t0 := time.Now()
        rows, _ := pool.Query(ctx, sql, args...)
        for rows.Next() {
            var id int64
            var kind string
            rows.Scan(&id, &kind)
        }
        rows.Close()
        if dt := time.Since(t0); best == 0 || dt < best {
            best = dt
        }
    }
    return best
}

for _, offset := range []int{0, 50_000, 490_000} {
    dt := timeIt("SELECT id, kind FROM events ORDER BY id LIMIT 20 OFFSET $1;", offset)
    fmt.Printf("OFFSET %7d: %.2f ms\n", offset, float64(dt.Microseconds())/1000.0)
}
for _, cursor := range []int{490_000, 0} {
    dt := timeIt("SELECT id, kind FROM events WHERE id > $1 ORDER BY id LIMIT 20;", cursor)
    fmt.Printf("keyset after id=%d: %.2f ms\n", cursor, float64(dt.Microseconds())/1000.0)
}
```

Real output, same live 500,000-row `events` table the Python run above used:

```text
OFFSET       0: 0.28 ms
OFFSET   50000: 2.39 ms
OFFSET  490000: 25.22 ms
keyset after id=490000: 0.19 ms
keyset after id=0: 0.18 ms
```

Same story, same database, different client: **~90x** between the shallowest and
deepest `OFFSET` (0.28ms → 25.22ms) here, keyset pagination flat at ~0.2ms regardless
of depth. The exact multiplier moved a little from the Python run's 65x — normal
run-to-run variance on a shared machine, not a language difference — but the shape of
the result (linear-in-offset vs. constant-time) is identical, because it's Postgres's
query planner doing the work in both cases, not the client language.

Full script used for the measurements above:

```python
import time
import psycopg

with psycopg.connect("postgresql://dsa:dsa@localhost:5544/dsa") as conn:
    def time_it(sql, params=None, n=3):
        best = None
        for _ in range(n):
            t0 = time.perf_counter()
            conn.execute(sql, params).fetchall()
            dt = time.perf_counter() - t0
            best = dt if best is None else min(best, dt)
        return best

    for offset in (0, 50_000, 490_000):
        dt = time_it("SELECT id, kind FROM events ORDER BY id LIMIT 20 OFFSET %s;", (offset,))
        print(f"OFFSET {offset:>7}: {dt*1000:.2f} ms")

    for cursor in (490_000, 0):
        dt = time_it("SELECT id, kind FROM events WHERE id > %s ORDER BY id LIMIT 20;", (cursor,))
        print(f"keyset after id={cursor}: {dt*1000:.2f} ms")
```

## Common mistakes

- **`OFFSET`-based "page 50" links in a public <abbr title="Application Programming Interface">API</abbr>** that gets meaningfully slower
  under real data volume, then gets blamed on "the database" rather than the
  pagination strategy.
- **Keyset pagination on a non-unique or non-indexed column.** The seek predicate
  (`WHERE id > :cursor`) needs an index to be fast, and the sort key needs to be
  unique (or paired with a tie-breaker, like `(created_at, id)`) or you can skip or
  repeat rows when multiple rows share the same cursor value.
- **Forgetting `ORDER BY` entirely** and assuming "insertion order" — as level 03
  noted, a table has no guaranteed order without one.

## What's next

Level 05 covers `UPDATE`, `DELETE`, and the constraints that keep bad writes out of
your tables in the first place.
