# Joins

## The mental model

A join combines rows from two tables based on a matching condition, producing one
result set that reads across the relationship a foreign key declared. This is the
entire payoff of level 00's relational design: split data into small, non-repeating
tables, then join them back together at query time to answer whatever question you
actually have.

## Setup used for this level

A classic many-to-many: students and courses, connected through a **junction table**
(`enrollments`) that holds one row per (student, course) pairing plus data that
belongs to the pairing itself (the grade).

```sql
CREATE TABLE students (id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE courses  (id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, title TEXT NOT NULL);
CREATE TABLE enrollments (
    student_id BIGINT NOT NULL REFERENCES students(id),
    course_id  BIGINT NOT NULL REFERENCES courses(id),
    grade      TEXT,
    PRIMARY KEY (student_id, course_id)
);

INSERT INTO students (name) VALUES ('Alice'), ('Bob'), ('Cara');
INSERT INTO courses (title) VALUES ('Databases'), ('Networks'), ('Compilers');
INSERT INTO enrollments (student_id, course_id, grade) VALUES
    (1, 1, 'A'), (1, 2, 'B'),
    (2, 1, 'B'),
    (3, 3, 'A');
```

Note the junction table's primary key is the *pair* `(student_id, course_id)` — this
is what makes it many-to-many: one student can appear in many rows (many courses),
one course can appear in many rows (many students), but the same pairing can't be
inserted twice.

## `INNER JOIN`

Returns only rows where the join condition matches on **both** sides.

```sql
SELECT s.name, c.title, e.grade
FROM students s
JOIN enrollments e ON e.student_id = s.id
JOIN courses c ON c.id = e.course_id
ORDER BY s.name, c.title;
```

```text
 name  |   title    | grade
-------+------------+-------
 Alice | Databases  | A
 Alice | Networks   | B
 Bob   | Databases  | B
 Cara  | Compilers  | A
```

Bare `JOIN` means `INNER JOIN` — Bob and Cara only appear once each, and only for
courses they're actually enrolled in, because `INNER JOIN` drops any row that has no
match.

**Go (`database/sql` + pgx):**

```go
db, _ := sql.Open("pgx", "postgresql://dsa:dsa@localhost:5544/dsa")

rows, _ := db.QueryContext(ctx, `
    SELECT s.name, c.title, e.grade
    FROM students s
    JOIN enrollments e ON e.student_id = s.id
    JOIN courses c ON c.id = e.course_id
    ORDER BY s.name, c.title`)
for rows.Next() {
    var name, title, grade string
    rows.Scan(&name, &title, &grade)
    fmt.Printf("%s | %s | %s\n", name, title, grade)
}
```

Real output — same four rows, driven from Go:

```text
Alice | Databases | A
Alice | Networks | B
Bob | Databases | B
Cara | Compilers | A
```

## `LEFT JOIN`, `RIGHT JOIN`, `FULL JOIN`

`LEFT JOIN` keeps every row from the left table, filling unmatched right-side
columns with `NULL`:

```sql
SELECT s.name, c.title
FROM students s
LEFT JOIN enrollments e ON e.student_id = s.id
LEFT JOIN courses c ON c.id = e.course_id
ORDER BY s.name;
```

With this dataset every student has at least one enrollment, so the result happens
to look the same as the inner join above — the difference only shows up with a
student who has zero enrollments (they'd still appear once, with `title = NULL`,
under `LEFT JOIN`, and would vanish entirely under `INNER JOIN`).

`RIGHT JOIN` is the mirror image (keep every row from the right table); Postgres
supports it, but in practice most people just swap table order and use `LEFT JOIN`
for readability, so `RIGHT JOIN` is rare in real codebases. `FULL JOIN` (or
`FULL OUTER JOIN`) keeps unmatched rows from **both** sides — useful for finding
mismatches between two tables that are supposed to correspond (e.g. reconciling two
systems' records).

## Self-join

A self-join joins a table to itself — used whenever rows reference other rows in the
same table, like an employee referencing their manager (who is also an employee):

```sql
CREATE TABLE employees (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       TEXT NOT NULL,
    manager_id BIGINT REFERENCES employees(id)
);
INSERT INTO employees (name, manager_id) VALUES
    ('Grace', NULL), ('Huan', 1), ('Ivy', 1), ('Jai', 2);

SELECT e.name AS employee, m.name AS manager
FROM employees e
LEFT JOIN employees m ON m.id = e.manager_id
ORDER BY e.id;
```

```text
 employee | manager
----------+---------
 Grace    |
 Huan     | Grace
 Ivy      | Grace
 Jai      | Huan
```

`LEFT JOIN` here (rather than `INNER JOIN`) is deliberate: Grace has no manager
(`manager_id IS NULL`), and an inner join would drop her from the result entirely
instead of showing her with a blank manager column. Table aliases (`e`, `m`) are
mandatory here — without them, `SELECT name FROM employees JOIN employees ...` is
ambiguous about which `employees.name` you mean.

**Go — the nullable-column gotcha:** a Go `string` cannot hold <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> `NULL`; scanning
`manager` (which is `NULL` for Grace) directly into a `string` panics at runtime the
first time a row actually has no manager. `database/sql` provides `sql.NullString`
for exactly this:

```go
rows, _ := db.QueryContext(ctx, `
    SELECT e.name AS employee, m.name AS manager
    FROM employees e LEFT JOIN employees m ON m.id = e.manager_id
    ORDER BY e.id`)
for rows.Next() {
    var employee string
    var manager sql.NullString
    rows.Scan(&employee, &manager)
    mgr := "NULL"
    if manager.Valid {
        mgr = manager.String
    }
    fmt.Printf("employee=%s manager=%s\n", employee, mgr)
}
```

Real output:

```text
employee=Grace manager=NULL
employee=Huan manager=Grace
employee=Ivy manager=Grace
employee=Jai manager=Huan
```

(Native `pgxpool` has the same requirement — it just uses `*string` or `pgtype.Text`
instead of `sql.NullString`; the underlying issue, a nullable <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> column has no direct
Go primitive equivalent, is identical regardless of driver.)

## A wrong join, live: forgetting the join condition

The single most common join bug is a missing or incomplete `ON` condition — it
doesn't error, it silently multiplies rows. Simulated here by literally forgetting
to match `courses.id` to `enrollments.course_id`:

```sql
-- BUG: "JOIN courses c ON true" instead of "ON c.id = e.course_id"
SELECT s.name, e.grade, c.title
FROM students s
JOIN enrollments e ON e.student_id = s.id
JOIN courses c ON true   -- forgot the real condition
WHERE s.name = 'Alice'
ORDER BY c.title;
```

Alice has exactly 2 real enrollments. Run live, this query returns:

```text
rows returned for Alice (should be 2, got 6):
  ('Alice', 'A', 'Compilers')
  ('Alice', 'B', 'Compilers')
  ('Alice', 'A', 'Databases')
  ('Alice', 'B', 'Databases')
  ('Alice', 'A', 'Networks')
  ('Alice', 'B', 'Networks')
```

Six rows: Alice's 2 real enrollment rows × all 3 courses in the table, because
`ON true` matches every row against every row — a full cross product, restricted
only by the (correct) `student_id` join to `enrollments`. Every one of Alice's two
grades got paired with every course, including courses she was never enrolled in.
This is exactly what a genuinely missing or wrong `ON` clause looks like in
production: not an error, a row-count explosion that's easy to miss if you don't
sanity-check row counts.

The fix — restoring the real condition:

```sql
SELECT s.name, e.grade, c.title
FROM students s
JOIN enrollments e ON e.student_id = s.id
JOIN courses c ON c.id = e.course_id   -- fixed
WHERE s.name = 'Alice'
ORDER BY c.title;
```

```text
rows returned for Alice (should be 2, got 2):
  ('Alice', 'A', 'Databases')
  ('Alice', 'B', 'Networks')
```

Back to the correct 2 rows, each course matched to the grade it actually belongs to.

## Common mistakes

- **A missing or incomplete `ON` condition**, as demonstrated above — the defense is
  to sanity-check row counts (`SELECT count(*)`) against what you expect, especially
  after adding a join to an existing query.
- **Using `WHERE` instead of the join's `ON` for a `LEFT JOIN`'s condition on the
  right-hand table.** `LEFT JOIN b ON b.x = a.x WHERE b.y = 5` silently turns back
  into an inner join, because rows where the left join produced `NULL`s for `b` get
  filtered out by the `WHERE`. If you need to keep unmatched rows, put the
  right-side filter in the `ON` clause instead: `LEFT JOIN b ON b.x = a.x AND b.y = 5`.
- **Joining on a column that isn't actually unique on one side** without realizing
  it — this produces the same kind of row-multiplication as the missing-`ON` bug
  above, just harder to spot because the condition looks reasonable.
- **Scanning a nullable joined column straight into a Go `string`.** As shown above,
  it panics the moment a row actually has a `NULL` there — use `sql.NullString` (or
  pgx's `pgtype.Text`/a pointer type) whenever the column can be `NULL`, which any
  column coming from the "unmatched" side of a `LEFT`/`RIGHT`/`FULL` join always can.

## What's next

Level 07 aggregates and summarizes the rows a join like this produces —
`COUNT`/`SUM`/`GROUP BY`, and window functions.
