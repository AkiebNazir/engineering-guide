# Subqueries and CTEs

## The mental model

A subquery is a `SELECT` nested inside another statement — a way to use a query's
result as an input to a bigger query, instead of computing it in two round trips
from application code. A CTE (`WITH ... AS (...)`, Common Table Expression) is the
same idea with a name attached, so you can build a query out of clearly-labeled
steps instead of one deeply nested blob. A **recursive** CTE goes one step further:
it can reference itself, which is how you traverse a tree or hierarchy — or generate
a sequence — in pure <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>.

## Setup used for this level

```sql
CREATE TABLE employees (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       TEXT NOT NULL,
    salary     NUMERIC(10,2) NOT NULL,
    manager_id BIGINT REFERENCES employees(id)
);
INSERT INTO employees (name, salary, manager_id) VALUES
    ('Grace', 220000, NULL),
    ('Huan', 180000, 1),
    ('Ivy', 175000, 1),
    ('Jai', 140000, 2),
    ('Kim', 130000, 2),
    ('Leo', 120000, 3);
```

## Scalar subquery

Returns exactly one value, used anywhere a single value is expected:

```sql
SELECT name, salary FROM employees
WHERE salary > (SELECT avg(salary) FROM employees)
ORDER BY salary DESC;
```

```text
 name  |  salary
-------+-----------
 Grace | 220000.00
 Huan  | 180000.00
 Ivy   | 175000.00
```

The inner query runs once, produces one number (the average salary), and the outer
query compares every row's salary against it.

## `IN` subquery

Returns a set of values the outer query checks membership against:

```sql
SELECT name FROM employees
WHERE id IN (SELECT manager_id FROM employees WHERE manager_id IS NOT NULL)
ORDER BY name;
```

```text
 name
-------
 Grace
 Huan
 Ivy
```

"Everyone whose `id` shows up as *someone's* `manager_id`" — i.e., everyone who
manages at least one other employee.

## `EXISTS` subquery

Checks only whether the inner query returns *any* row at all — it doesn't care what
the row contains, which lets Postgres stop scanning as soon as it finds one match:

```sql
SELECT m.name FROM employees m
WHERE EXISTS (
    SELECT 1 FROM employees e
    WHERE e.manager_id = m.id AND e.salary > 150000
)
ORDER BY m.name;
```

```text
 name
-------
 Grace
```

Only Grace has a direct report earning over 150,000 (Huan, at 180,000). `EXISTS` is
usually the right tool over `IN` when you're checking for *any matching related
row* rather than membership in a specific set of values — it also handles `NULL`
values in the subquery's column more predictably than `IN`/`NOT IN` do (a
well-known `NOT IN` + `NULL` trap: if the subquery's result set contains even one
`NULL`, `NOT IN` returns no rows at all, which surprises almost everyone the first
time they hit it).

**Go (`database/sql` + `lib/pq`)** — the classic `database/sql` driver, shown here
instead of pgx for variety; it registers itself as driver name `"postgres"`:

```go
db, _ := sql.Open("postgres", "postgresql://dsa:dsa@localhost:5544/dsa?sslmode=disable")

rows, _ := db.QueryContext(ctx, `
    SELECT m.name FROM employees m
    WHERE EXISTS (
        SELECT 1 FROM employees e
        WHERE e.manager_id = m.id AND e.salary > 150000
    ) ORDER BY m.name`)
for rows.Next() {
    var name string
    rows.Scan(&name)
    fmt.Println(name)
}
```

Real output:

```text
Grace
```

(`lib/pq` needs `sslmode=disable` in the DSN for a local, non-<abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr> lab database — pgx
infers this automatically. `lib/pq` is in maintenance mode upstream; it still works
fine and is worth recognizing in older codebases, but `pgx/v5/stdlib` is the
actively-maintained choice for new `database/sql` code today.)

## CTE (`WITH`)

Names an intermediate result so the rest of the query can refer to it like a table:

```sql
WITH team_totals AS (
    SELECT manager_id, sum(salary) AS team_salary
    FROM employees
    WHERE manager_id IS NOT NULL
    GROUP BY manager_id
)
SELECT m.name AS manager, t.team_salary
FROM team_totals t
JOIN employees m ON m.id = t.manager_id
ORDER BY t.team_salary DESC;
```

```text
 manager | team_salary
---------+--------------
 Grace   |   355000.00
 Huan    |   270000.00
 Ivy     |   120000.00
```

This could be written as one nested subquery instead, but the CTE version reads
top-to-bottom as "first compute team totals, then join them to manager names" —
each step is named and can be tested/read on its own, which matters a lot once a
query grows past two or three steps.

## Recursive CTE: org chart traversal

A recursive CTE has two parts joined by `UNION ALL`: a **base case** (the starting
rows) and a **recursive case** (a query that references the CTE's own name, run
repeatedly against the *previous* iteration's output until it returns no more new
rows).

```sql
WITH RECURSIVE org AS (
    -- base case: the top of the hierarchy
    SELECT id, name, manager_id, 0 AS depth, name::text AS path
    FROM employees
    WHERE manager_id IS NULL

    UNION ALL

    -- recursive case: find direct reports of everyone found so far
    SELECT e.id, e.name, e.manager_id, o.depth + 1, o.path || ' -> ' || e.name
    FROM employees e
    JOIN org o ON e.manager_id = o.id
)
SELECT depth, path FROM org ORDER BY path;
```

```text
 depth |          path
-------+-------------------------
     0 | Grace
     1 | Grace -> Huan
     2 | Grace -> Huan -> Jai
     2 | Grace -> Huan -> Kim
     1 | Grace -> Ivy
     2 | Grace -> Ivy -> Leo
```

Each iteration finds the next level down: iteration 1 finds Grace (the only row with
no manager); iteration 2 finds Huan and Ivy (Grace's direct reports); iteration 3
finds Jai, Kim, and Leo. The recursion stops automatically once an iteration adds no
new rows.

**Go (`database/sql` + `lib/pq`):** a recursive CTE is just a `SELECT` as far as the
client is concerned — nothing about scanning it differs from any other multi-row
query:

```go
rows, _ := db.QueryContext(ctx, `
    WITH RECURSIVE org AS (
        SELECT id, name, manager_id, 0 AS depth, name::text AS path
        FROM employees WHERE manager_id IS NULL
        UNION ALL
        SELECT e.id, e.name, e.manager_id, o.depth + 1, o.path || ' -> ' || e.name
        FROM employees e JOIN org o ON e.manager_id = o.id
    )
    SELECT depth, path FROM org ORDER BY path`)
for rows.Next() {
    var depth int
    var path string
    rows.Scan(&depth, &path)
    fmt.Printf("depth=%d path=%s\n", depth, path)
}
```

Real output — identical traversal, same six rows:

```text
depth=0 path=Grace
depth=1 path=Grace -> Huan
depth=2 path=Grace -> Huan -> Jai
depth=2 path=Grace -> Huan -> Kim
depth=1 path=Grace -> Ivy
depth=2 path=Grace -> Ivy -> Leo
```

The other canonical recursive-CTE example, a plain number series (useful whenever
you need to generate rows that don't come from a table — `generate_series` is
usually simpler for this specific case, but the recursive form is the general
pattern):

```sql
WITH RECURSIVE nums(n) AS (
    SELECT 1
    UNION ALL
    SELECT n + 1 FROM nums WHERE n < 5
)
SELECT n FROM nums;
```

```text
 n
---
 1
 2
 3
 4
 5
```

## Common mistakes

- **`NOT IN` with a subquery that can return `NULL`.** As noted above, one `NULL` in
  the subquery's results makes the entire `NOT IN` match nothing. Use
  `NOT EXISTS` instead when there's any chance of a `NULL`.
- **Forgetting the recursive CTE's stopping condition.** `WHERE n < 5` above is what
  stops the recursion — omit a bounding condition on genuinely cyclic data (e.g. an
  org chart with a data-entry bug that makes someone their own indirect manager) and
  the query runs until Postgres's built-in recursion safety net (or your patience)
  gives out.
- **Reaching for a deeply nested subquery when a CTE would be more readable.**
  They're often equivalent in performance (Postgres can inline a non-recursive CTE
  into the surrounding query), so prefer whichever reads more clearly — usually the
  named, step-by-step CTE once there's more than one level of nesting.

## What's next

Level 09 moves from single statements to transactions — multiple statements that
succeed or fail together, and what can go wrong when two of them run concurrently.
