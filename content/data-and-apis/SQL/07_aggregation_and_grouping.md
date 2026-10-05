# Aggregation and Grouping

## The mental model

An aggregate function collapses many rows into one value — `COUNT`, `SUM`, `AVG`,
`MIN`, `MAX`. `GROUP BY` runs that collapse separately per distinct value of some
column, turning "one number for the whole table" into "one number per group."
Window functions (the last section) do something related but different: they
compute an aggregate-like value *per row*, without collapsing the rows away — you
keep every row and get an extra computed column alongside it.

## Setup used for this level

```sql
CREATE TABLE sales (
    id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region   TEXT NOT NULL,
    rep      TEXT NOT NULL,
    amount   NUMERIC(10,2) NOT NULL,
    sold_on  DATE NOT NULL
);
INSERT INTO sales (region, rep, amount, sold_on) VALUES
    ('west', 'Ana', 100, '2026-01-01'),
    ('west', 'Ana', 150, '2026-01-05'),
    ('west', 'Bo',  200, '2026-01-03'),
    ('east', 'Cy',  300, '2026-01-02'),
    ('east', 'Cy',  50,  '2026-01-06'),
    ('east', 'Deb', 400, '2026-01-04');
```

## `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`

```sql
SELECT count(*), sum(amount), avg(amount), min(amount), max(amount) FROM sales;
```

```text
 count |  sum   |          avg           | min | max
-------+--------+-------------------------+-----+-----
     6 | 1200.00 | 200.0000000000000000  | 50.00 | 400.00
```

(Real output, reformatted for readability — Postgres's `avg()` over a `NUMERIC`
column returns extra decimal precision, which is expected: it's exact decimal
division, not floating point.) With no `GROUP BY`, the whole table is one group —
one row of output, no matter how many rows went in.

## `GROUP BY`

```sql
SELECT region, sum(amount) AS total
FROM sales
GROUP BY region
ORDER BY region;
```

```text
 region | total
--------+--------
 east   | 750.00
 west   | 450.00
```

Every column in the `SELECT` list that isn't wrapped in an aggregate function must
appear in `GROUP BY` — Postgres enforces this and errors if you forget (unlike some
databases that silently pick an arbitrary row's value, which is almost never what
you want).

## `HAVING` vs `WHERE`

`WHERE` filters rows **before** grouping happens; `HAVING` filters groups **after**
aggregation. This is the entire reason `HAVING` exists as a separate keyword: you
cannot write `WHERE sum(amount) > 500` — at the point `WHERE` runs, individual rows
haven't been aggregated yet, so there's no `sum(amount)` to compare.

```sql
SELECT region, sum(amount) AS total
FROM sales
GROUP BY region
HAVING sum(amount) > 500
ORDER BY region;
```

Given the measured totals above (`east = 750.00`, `west = 450.00`), this returns
only `east` — `west`'s total doesn't clear the 500 threshold. Contrast with a
`WHERE` clause on the same query, which filters individual *sale rows* before
grouping (e.g. `WHERE amount > 100` would drop Ana's 100 and Cy's 50 rows before
either region's total gets summed) — a completely different operation that happens
to use similar-looking syntax.

**Go (native `pgxpool`):**

```go
rows, _ := pool.Query(ctx, `
    SELECT region, sum(amount) AS total
    FROM sales GROUP BY region HAVING sum(amount) > 500 ORDER BY region`)
for rows.Next() {
    var region string
    var total float64
    rows.Scan(&region, &total)
    fmt.Printf("region=%s total=%.2f\n", region, total)
}
```

Real output:

```text
region=east total=750.00
```

## Window functions: aggregate *per row*, without collapsing rows

```sql
SELECT region, rep, amount,
       ROW_NUMBER() OVER (PARTITION BY region ORDER BY amount DESC) AS rn,
       RANK()       OVER (PARTITION BY region ORDER BY amount DESC) AS rnk
FROM sales
ORDER BY region, amount DESC;
```

```text
 region | rep | amount | rn | rnk
--------+-----+--------+----+-----
 east   | Deb | 400.00 |  1 |   1
 east   | Cy  | 300.00 |  2 |   2
 east   | Cy  |  50.00 |  3 |   3
 west   | Bo  | 200.00 |  1 |   1
 west   | Ana | 150.00 |  2 |   2
 west   | Ana | 100.00 |  3 |   3
```

`PARTITION BY region` resets the numbering for each region — this dataset has no
tied amounts, so `ROW_NUMBER()` (always distinct, 1-2-3-...) and `RANK()` (ties share
a rank, and the next rank skips accordingly) happen to match here; they'd diverge if
two reps in the same region had the identical amount.

Running total via `SUM() OVER`:

```sql
SELECT sold_on, region, amount,
       SUM(amount) OVER (PARTITION BY region ORDER BY sold_on
                          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM sales
ORDER BY region, sold_on;
```

```text
 sold_on    | region | amount | running_total
------------+--------+--------+----------------
 2026-01-02 | east   | 300.00 |         300.00
 2026-01-04 | east   | 400.00 |         700.00
 2026-01-06 | east   |  50.00 |         750.00
 2026-01-01 | west   | 100.00 |         100.00
 2026-01-03 | west   | 200.00 |         300.00
 2026-01-05 | west   | 150.00 |         450.00
```

`ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` defines the "window frame" as
"every row from the start of this partition up to and including the current row" —
that's what makes it a running total instead of a whole-partition sum. Every row is
still present in the output (six rows in, six rows out) — this is the defining
difference from `GROUP BY`, which would have collapsed this into two rows (one per
region).

**Go (native `pgxpool`) — and a real `DATE`-scanning gotcha:**

```go
rows, _ := pool.Query(ctx, `
    SELECT sold_on, region, amount,
           SUM(amount) OVER (PARTITION BY region ORDER BY sold_on
                              ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
    FROM sales ORDER BY region, sold_on`)
for rows.Next() {
    var soldOn time.Time   // NOT string -- see the mistake below
    var region string
    var amount, running float64
    rows.Scan(&soldOn, &region, &amount, &running)
    fmt.Printf("sold_on=%s region=%s amount=%.2f running_total=%.2f\n",
        soldOn.Format("2006-01-02"), region, amount, running)
}
```

Real output:

```text
sold_on=2026-01-02 region=east amount=300.00 running_total=300.00
sold_on=2026-01-04 region=east amount=400.00 running_total=700.00
sold_on=2026-01-06 region=east amount=50.00 running_total=750.00
sold_on=2026-01-01 region=west amount=100.00 running_total=100.00
sold_on=2026-01-03 region=west amount=200.00 running_total=300.00
sold_on=2026-01-05 region=west amount=150.00 running_total=450.00
```

The comment isn't decoration — this was a real error hit while writing this level.
Scanning `sold_on` into a Go `string` panics: `cannot scan date (OID 1082) in binary
format into *string`. Unlike `psycopg`, which happily hands back a Python `date`
object that stringifies on demand, native pgx's binary protocol path requires the
destination type it actually knows how to decode a `DATE` into — `time.Time` (or
`pgtype.Date`) — not a bare string.

## Common mistakes

- **Trying to filter on an aggregate with `WHERE`.** Use `HAVING`.
- **Selecting a non-aggregated, non-grouped column** alongside `GROUP BY` and
  expecting it to "just work" — Postgres rejects this at parse time rather than
  silently picking an arbitrary value, which is a feature, not a limitation.
- **Confusing `RANK()` and `ROW_NUMBER()`** when there are ties — `RANK()` leaves
  gaps after ties (1, 1, 3), `DENSE_RANK()` doesn't (1, 1, 2), `ROW_NUMBER()` ignores
  ties entirely and just counts (1, 2, 3). Pick based on whether ties in your data
  should share a position.
- **Scanning a `DATE`/`TIMESTAMP` column into a Go `string` with native pgx** — as
  measured above, it panics; scan into `time.Time` and format it explicitly if you
  need a string representation.

## What's next

Level 08 covers subqueries and CTEs — ways to build a query out of smaller named
pieces, including one that can reference itself.
