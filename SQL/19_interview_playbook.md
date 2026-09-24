# Interview Playbook: SQL

This level is not new material — it's the ladder's content re-organized as the
concrete questions an interviewer actually asks, with a precise answer for each, and a
pointer back to the level that proves it. Use it as a pre-interview refresher, not a
first read.

## "What should every engineer be able to do cold, with no notes"

1. Write a query with a **join**, a **`GROUP BY` + `HAVING`**, and a **subquery or
   CTE** without hesitating over syntax (levels 06–08).
2. State the four **ACID** properties and which Postgres mechanism provides each
   (level 09).
3. Read an **`EXPLAIN ANALYZE`** plan and say, from the plan alone, whether a query
   used an index and why (level 10).
4. Explain **why a parameterized query prevents SQL injection** — not just "it's safer",
   but *what specifically* changes about how the database treats the input (level 11).
5. Name the difference between **normalization and denormalization** and give a real
   reason to choose each (level 16).
6. Explain **replication lag** and what "eventual consistency between a primary and a
   replica" concretely means for an application (level 17).
7. Explain why **joins don't shard for free** and name the shard-key tradeoff (level 18).

If any of these needs the reference file open to answer, that's the level to re-run
before an interview, not just re-read.

## Query patterns that come up constantly — worked, with real output

**"Find the Nth highest value"** (classic: Nth highest salary):

```sql
-- 2nd highest DISTINCT salary overall
SELECT DISTINCT salary FROM employees_demo ORDER BY salary DESC OFFSET 1 LIMIT 1;
```
```text
 salary
--------
  95000
```

The `DISTINCT` matters: without it, two people tied for 1st would make `OFFSET 1`
return the *first* place salary again, not the second-*distinct* value.

**"Find the Nth highest value per group"** (2nd highest salary per department) — the
window-function answer interviewers are actually checking for, since the naive
per-group subquery version is much harder to get right:

```sql
SELECT department, name, salary FROM (
  SELECT department, name, salary,
         DENSE_RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS rnk
  FROM employees_demo
) t WHERE rnk = 2;
```
```text
 department | name | salary
------------+------+--------
 Eng        | Cara |  95000
 Sales      | Faye |  60000
```

`DENSE_RANK` (not `ROW_NUMBER`) is the correct choice when ties should share a rank —
`ROW_NUMBER` would arbitrarily pick one of two tied top earners as "1st" and the other
as "2nd", silently hiding the tie.

**"Find duplicate rows"**:

```sql
SELECT salary, COUNT(*) FROM employees_demo GROUP BY salary HAVING COUNT(*) > 1;
```
```text
 salary | count
--------+-------
 120000 |     2
  80000 |     2
```

The `HAVING` (not `WHERE`) matters — filtering on an aggregate result requires
`HAVING`, since `WHERE` runs before `GROUP BY` computes the counts (level 07).

**"Running total / cumulative sum"** — a window function, not a self-join:

```sql
SELECT id, name, salary, SUM(salary) OVER (ORDER BY id) AS running_total
FROM employees_demo;
```
```text
 id | name  | salary | running_total
----+-------+--------+---------------
  1 | Alice | 120000 |        120000
  2 | Bob   | 120000 |        240000
  3 | Cara  |  95000 |        335000
```

## The same four patterns, in Go

Levels 16-18 used native `pgxpool` throughout. Here's the other real option — plain
`database/sql` with `pgx`'s driver registered underneath it
(`_ "github.com/jackc/pgx/v5/stdlib"`), which is what you'd reach for if the rest of
your codebase already standardizes on `database/sql` (ORMs, migration tools, and a lot
of existing Go code assume it) instead of pgx's richer native API:

```go
db, _ := sql.Open("pgx", "postgresql://dsa:dsa@localhost:5544/dsa")

var salary int
db.QueryRowContext(ctx, `SELECT DISTINCT salary FROM employees_demo ORDER BY salary DESC OFFSET 1 LIMIT 1`).Scan(&salary)

rows, _ := db.QueryContext(ctx, `
    SELECT department, name, salary FROM (
      SELECT department, name, salary, DENSE_RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS rnk
      FROM employees_demo
    ) t WHERE rnk = 2`)
for rows.Next() {
    var dept, name string
    var sal int
    rows.Scan(&dept, &name, &sal)
    fmt.Printf("%s %s %d\n", dept, name, sal)
}
rows.Err()   // always check after the loop -- Next() returning false can mean
             // "done" or "an error interrupted iteration", and only Err() distinguishes them
```

Real output — identical to the `psql`/pgxpool results above, run against the same
table shape via `database/sql`:

```text
2nd highest salary overall: 95000
2nd highest per department:
  Eng Cara 95000
  Sales Faye 60000
duplicate salaries:
  salary=120000 count=2
  salary=80000 count=2
running total:
  id=1 name=Alice salary=120000 running_total=120000
  id=2 name=Bob salary=120000 running_total=240000
  ...
```

**`database/sql` + pgx's stdlib driver, vs. native `pgxpool` — the real decision:**
`database/sql` is the *portable* choice — the same interface works against MySQL,
SQLite, or any other `database/sql` driver, and every Go ORM/migration tool assumes
it, at the cost of a thin adapter layer between your code and pgx's actual protocol
implementation. Native `pgxpool` (used throughout levels 16-18) skips that adapter and
exposes pgx's full feature set directly — batch queries, `COPY` for bulk loads,
richer Postgres-specific type mapping, and a connection pool tuned for Postgres
specifically rather than `database/sql`'s generic pool. The honest interview answer:
default to `database/sql`+pgx if the codebase or its tooling needs driver-agnosticism;
reach for native `pgxpool` when you're Postgres-committed and want its full feature
set, which is most greenfield Go-on-Postgres services today.

## Conceptual questions, answered precisely

**"What's the difference between `WHERE` and `HAVING`?"** `WHERE` filters rows before
grouping; `HAVING` filters groups after aggregation. A condition on a raw column
(`salary > 50000`) belongs in `WHERE`; a condition on an aggregate (`COUNT(*) > 1`)
requires `HAVING`, because that value doesn't exist until the grouping happens.

**"What's the difference between `INNER JOIN` and `LEFT JOIN`, precisely?"** `INNER
JOIN` returns only rows with a match on both sides; `LEFT JOIN` returns every row from
the left table, with `NULL`s for unmatched right-side columns. The interview trap:
a `WHERE` clause filtering the *right* table's column after a `LEFT JOIN` silently
turns it back into an `INNER JOIN` (rows with `NULL` on that column get filtered out)
— the filter belongs in the `ON` clause if you want to keep unmatched left rows.

**"What does an index actually cost?"** Every write to an indexed column updates the
index too — level 10 measured a 244x read speedup from one index; the read side is
usually what gets quoted, but the honest answer names the write-side cost as well,
plus the storage the index itself occupies.

**"Explain isolation levels using a real example, not just definitions."** Use the
lost-update demo from level 09: two concurrent read-modify-write cycles on the same
row, unprotected, silently lose one write. Then name the fix ladder from weakest to
strongest tool (atomic `UPDATE ... WHERE`, `SELECT ... FOR UPDATE`, constraints,
`REPEATABLE READ`/`SERIALIZABLE` with retry logic) rather than reaching straight for
`SERIALIZABLE` as a default answer.

**"How would you design a schema for X?"** Default to normalized (3NF) unless you can
name a specific, measured reason to denormalize (level 16) — walk through the entities,
their functional dependencies, and where foreign keys enforce the relationships,
rather than free-associating table names.

**"How would you scale this database?"** Answer in the right order: (1) index and
query-plan work first (level 10) — usually the highest ROI and zero architectural
change; (2) read replicas (level 17) if the bottleneck is read traffic; (3) partitioning
(level 18) if one table has grown too large for its indexes or retention to stay cheap;
(4) sharding (level 18) only once write throughput on a single primary is the actual,
measured bottleneck — naming sharding first, before ruling out the cheaper three steps,
reads as not having operated a real database under load.

**"SQL vs. NoSQL — how do you choose?"** See `NoSQL/concepts/01_choosing_a_database_and_cap_theorem.md`
for the full decision framework shared across both modules.

## What's next

This closes the SQL ladder. `NoSQL/concepts/` has the equivalent playbook for the
document/key-value side, plus the cross-cutting SQL-vs-NoSQL and CAP-theorem material
that applies to both.
