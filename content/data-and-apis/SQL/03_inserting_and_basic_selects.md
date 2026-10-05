# Inserting and Basic Selects

## The mental model

`INSERT` adds rows; `SELECT` reads them back. Everything else in this module is
refinement on these two statements — filtering which rows `SELECT` returns (level
04), combining rows across tables (level 06), summarizing them (level 07). Get
comfortable with the plain form first.

## Setup used for this level

```sql
DROP TABLE IF EXISTS books;

CREATE TABLE books (
    id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title  TEXT NOT NULL,
    author TEXT NOT NULL,
    pages  INT NOT NULL
);
```

## `INSERT`

```sql
INSERT INTO books (title, author, pages) VALUES
    ('Dune', 'Frank Herbert', 412),
    ('Foundation', 'Isaac Asimov', 255),
    ('Neuromancer', 'William Gibson', 271);
```

Column names are listed explicitly (`(title, author, pages)`) rather than relying on
table order — this means the statement keeps working even if someone later adds a
column in the middle of the table, and it documents which values map to which
column at the call site. A single `INSERT` can (and, when inserting more than one
row, should) supply multiple `VALUES` tuples in one statement — this is one round
trip to the database instead of three.

`id` isn't listed: it's `GENERATED ALWAYS AS IDENTITY`, so Postgres assigns it.

## `SELECT *` vs a column list

```sql
SELECT * FROM books;
```

```text
 id |    title    |     author     | pages
----+-------------+----------------+-------
  1 | Dune        | Frank Herbert  |   412
  2 | Foundation  | Isaac Asimov   |   255
  3 | Neuromancer | William Gibson |   271
```

`SELECT *` returns every column, in table-definition order. It's convenient at the
`psql` prompt while exploring, but avoid it in application code and stored queries:
if someone adds a column later, every caller of `SELECT *` silently starts receiving
an extra field it didn't ask for (and, worse, positional access like `row[3]` now
points at the wrong thing). Name the columns you actually need:

```sql
SELECT title, author FROM books;
```

```text
    title    |     author
-------------+----------------
 Dune        | Frank Herbert
 Foundation  | Isaac Asimov
 Neuromancer | William Gibson
```

## `LIMIT`

```sql
SELECT title, author FROM books LIMIT 2;
```

```text
   title    |    author
------------+---------------
 Dune       | Frank Herbert
 Foundation | Isaac Asimov
```

`LIMIT n` caps how many rows come back. Without an `ORDER BY`, *which* rows you get
when there are more than `n` is not guaranteed by the SQL standard — Postgres will
usually return them in physical storage order for a simple query like this one, but
that's an implementation detail, not a contract. Level 04 combines `LIMIT` with
`ORDER BY` to make "the first N rows" mean something specific and repeatable.

## `RETURNING` — reading back what you just wrote

Postgres extends plain `INSERT` with `RETURNING`, which hands back columns from the
row(s) you just inserted in the same round trip — useful for getting a
database-generated ID without a second `SELECT`:

```sql
INSERT INTO books (title, author, pages) VALUES ('Snow Crash', 'Neal Stephenson', 470)
RETURNING id, title;
```

Verified end to end in Python:

```python
import psycopg

with psycopg.connect("postgresql://dsa:dsa@localhost:5544/dsa") as conn:
    conn.execute("DROP TABLE IF EXISTS books;")
    conn.execute("""
        CREATE TABLE books (
            id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            title  TEXT NOT NULL,
            author TEXT NOT NULL,
            pages  INT NOT NULL
        );
    """)
    conn.execute("""
        INSERT INTO books (title, author, pages) VALUES
            ('Dune', 'Frank Herbert', 412),
            ('Foundation', 'Isaac Asimov', 255),
            ('Neuromancer', 'William Gibson', 271);
    """)
    conn.commit()

    cur = conn.execute("""
        INSERT INTO books (title, author, pages) VALUES ('Snow Crash', 'Neal Stephenson', 470)
        RETURNING id, title;
    """)
    print(cur.fetchone())
    conn.commit()
```

Real output: `(4, 'Snow Crash')` — the auto-generated `id` came back without a
follow-up query.

**Go (`database/sql` + pgx):** `RETURNING` makes an `INSERT` behave like a query
that produces a row, so it goes through `QueryRow`, not `Exec` — `Exec` throws away
any rows a statement returns.

```go
db, _ := sql.Open("pgx", "postgresql://dsa:dsa@localhost:5544/dsa")

db.Exec(`DROP TABLE IF EXISTS books;`)
db.Exec(`
    CREATE TABLE books (
        id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        title  TEXT NOT NULL,
        author TEXT NOT NULL,
        pages  INT NOT NULL
    );
`)
db.Exec(`
    INSERT INTO books (title, author, pages) VALUES
        ('Dune', 'Frank Herbert', 412),
        ('Foundation', 'Isaac Asimov', 255),
        ('Neuromancer', 'William Gibson', 271);
`)

var id int64
var title string
err := db.QueryRow(`
    INSERT INTO books (title, author, pages) VALUES ('Snow Crash', 'Neal Stephenson', 470)
    RETURNING id, title;
`).Scan(&id, &title)
fmt.Println(id, title)
```

Real output — same result, same database, same auto-generated ID:

```text
4 Snow Crash
```

## Common mistakes

- **`SELECT *` in application code**, as covered above — it couples your code to the
  table's current shape.
- **Multiple single-row `INSERT` statements in a loop** instead of one multi-row
  `INSERT`. Each statement is a network round trip; batching them into one
  statement (or using `executemany`/`COPY` for genuinely large loads) is
  meaningfully faster, the same lesson level 13 revisits for queries in general.
- **Relying on row order without `ORDER BY`.** A table has no inherent order once
  updates and deletes start happening — "first" and "last" only mean something once
  you say what you're ordering by.
- **Using `Exec` instead of `QueryRow`/`Query` for a `RETURNING` statement in Go.**
  `Exec` is built for statements with no result rows (it hands back only an affected-row
  count) — calling it on a `RETURNING` insert compiles and "succeeds," but silently
  discards the very row you added `RETURNING` to get back.

## What's next

Level 04 adds `WHERE`, `ORDER BY`, and proper pagination.
