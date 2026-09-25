# Updating, Deleting, and Constraints

## The mental model

`UPDATE` and `DELETE` mutate existing rows — and both are dangerous in the exact
same way: run either without a `WHERE` clause and it applies to *every row in the
table*. Constraints are the database's half of the safety story: they let you
declare invariants once (a column must be unique, a foreign key must point at a real
row, a check must hold) and have every future write — from every client, forever —
be validated against them automatically, instead of trusting every caller to
remember the rule.

## Setup used for this level

```sql
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE orders (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    total_cents INT NOT NULL CHECK (total_cents >= 0)
);

INSERT INTO customers (email) VALUES ('a@example.com'), ('b@example.com');
INSERT INTO orders (customer_id, total_cents) VALUES (1, 1500), (1, 2200), (2, 900);
```

## `UPDATE` and `DELETE`

```sql
UPDATE orders SET total_cents = total_cents + 100 WHERE customer_id = 1;
```

```text
 id | customer_id | total_cents
----+-------------+-------------
  1 |           1 |        1600
  2 |           1 |        2300
  3 |           2 |         900
```

```sql
DELETE FROM orders WHERE id = 3;
```

```text
 id | customer_id | total_cents
----+-------------+-------------
  1 |           1 |        1600
  2 |           1 |        2300
```

Both statements were run and verified against a live table (output above is a real
transcript). Note that `UPDATE`'s `SET total_cents = total_cents + 100` reads and
writes the column in one atomic statement per row — no read-then-write race, unlike
the naive application-level pattern level 09 shows failing.

**Go (`database/sql` + pgx):**

```go
db, _ := sql.Open("pgx", "postgresql://dsa:dsa@localhost:5544/dsa")

db.ExecContext(ctx, `UPDATE orders SET total_cents = total_cents + 100 WHERE customer_id = 1`)

rows, _ := db.QueryContext(ctx, `SELECT id, customer_id, total_cents FROM orders ORDER BY id`)
for rows.Next() {
    var id, custID, total int
    rows.Scan(&id, &custID, &total)
    fmt.Printf("id=%d customer_id=%d total_cents=%d\n", id, custID, total)
}
```

Real output — identical result, driven from Go instead of `psql`:

```text
id=1 customer_id=1 total_cents=1600
id=2 customer_id=1 total_cents=2300
id=3 customer_id=2 total_cents=900
```

## The four constraints you'll use constantly

| Constraint | Declares | Example |
|---|---|---|
| `PRIMARY KEY` | Unique, non-null, one per row — the row's identity | `id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY` |
| `UNIQUE` | No two rows may share this value (nulls are an exception — multiple `NULL`s are allowed) | `email TEXT NOT NULL UNIQUE` |
| `CHECK` | A boolean expression every row must satisfy | `total_cents INT NOT NULL CHECK (total_cents >= 0)` |
| `FOREIGN KEY` (`REFERENCES`) | This column's value must exist as a primary/unique key value in another table | `customer_id BIGINT NOT NULL REFERENCES customers(id)` |

`ON DELETE CASCADE` on a foreign key says: if the referenced row (the customer) is
deleted, automatically delete every row that references it (that customer's
orders) too, instead of blocking the delete or leaving orphaned rows. The
alternatives are `ON DELETE RESTRICT` (the default — block the delete if references
exist), `ON DELETE SET NULL` (null out the reference), and `ON DELETE SET DEFAULT`.
Choose deliberately per relationship — cascading delete is correct for "order items
belong to this order and have no meaning without it," and wrong for "this audit log
row references a user, and must survive the user's deletion."

## Live constraint violations

Each of these was actually run against the live database and the error shown is the
real one Postgres raised, not a paraphrase:

```python
try:
    conn.execute("INSERT INTO customers (email) VALUES ('a@example.com');")
except Exception as e:
    print(f"{type(e).__name__}: {e}")
```
```text
UniqueViolation: duplicate key value violates unique constraint "customers_email_key"
DETAIL:  Key (email)=(a@example.com) already exists.
```

```python
try:
    conn.execute("INSERT INTO orders (customer_id, total_cents) VALUES (1, -50);")
except Exception as e:
    print(f"{type(e).__name__}: {e}")
```
```text
CheckViolation: new row for relation "orders" violates check constraint "orders_total_cents_check"
DETAIL:  Failing row contains (4, 1, -50).
```

```python
try:
    conn.execute("INSERT INTO orders (customer_id, total_cents) VALUES (999, 100);")
except Exception as e:
    print(f"{type(e).__name__}: {e}")
```
```text
ForeignKeyViolation: insert or update on table "orders" violates foreign key constraint "orders_customer_id_fkey"
DETAIL:  Key (customer_id)=(999) is not present in table "customers".
```

And `ON DELETE CASCADE` actually cascading:

```python
print("orders before:", conn.execute("SELECT count(*) FROM orders WHERE customer_id = 1;").fetchone())
conn.execute("DELETE FROM customers WHERE id = 1;")
print("orders after customer 1 deleted:", conn.execute("SELECT count(*) FROM orders WHERE customer_id = 1;").fetchone())
```
```text
orders before: (2,)
orders after customer 1 deleted: (0,)
```

Deleting customer 1 silently removed both of their orders — exactly what
`ON DELETE CASCADE` promises, and worth pausing on: this is powerful and dangerous
in the same breath. Make sure cascading delete is genuinely what the relationship
means before declaring it.

`psycopg` maps each of these to a specific exception class (`UniqueViolation`,
`CheckViolation`, `ForeignKeyViolation`, all subclasses of `psycopg.errors.IntegrityError`)
so application code can catch the specific failure it expects (e.g. "email already
taken") without swallowing unrelated errors.

**Go (native `pgxpool`):** pgx doesn't map constraint violations to distinct
per-constraint-type Go types the way psycopg does — every Postgres error comes back as
one `*pgconn.PgError`, and your code inspects its `Code` (the SQLSTATE) or
`ConstraintName` field to tell them apart:

```go
_, err := pool.Exec(ctx, `INSERT INTO customers (email) VALUES ('a@example.com')`)
var pgErr *pgconn.PgError
if errors.As(err, &pgErr) {
    fmt.Printf("SQLSTATE %s (%s): %s\n", pgErr.Code, pgErr.ConstraintName, pgErr.Message)
    fmt.Println("DETAIL:", pgErr.Detail)
}
```

Real output, all three violations plus the cascade delete, run for real against the
same live tables:

```text
SQLSTATE 23505 (customers_email_key): duplicate key value violates unique constraint "customers_email_key"
DETAIL: Key (email)=(a@example.com) already exists.
SQLSTATE 23514 (orders_total_cents_check): new row for relation "orders" violates check constraint "orders_total_cents_check"
DETAIL: Failing row contains (4, 1, -50).
SQLSTATE 23503 (orders_customer_id_fkey): insert or update on table "orders" violates foreign key constraint "orders_customer_id_fkey"
DETAIL: Key (customer_id)=(999) is not present in table "customers".
orders before: 2
orders after customer 1 deleted: 0
```

The SQLSTATE codes (`23505` = unique_violation, `23514` = check_violation, `23503` =
foreign_key_violation) are part of the <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> standard, not Postgres- or driver-specific —
they're the same three codes `psycopg`'s exception classes wrap on the Python side,
just surfaced as a string field instead of a distinct exception type.

## Common mistakes

- **`UPDATE`/`DELETE` without a `WHERE` clause.** Always write and re-read the
  `WHERE` clause before the verb in your head, or run the equivalent `SELECT` first
  to see exactly which rows will be affected.
- **Adding constraints after the data already violates them.** Adding a `CHECK` or
  `UNIQUE` constraint to a table that already has bad data fails immediately — clean
  the data (or add the constraint as `NOT VALID` and validate later) before adding
  it.
- **Checking `err != nil` and stopping there in Go, instead of `errors.As`-ing into
  `*pgconn.PgError`.** A generic "insert failed" log line throws away exactly the
  information (which constraint, which SQLSTATE) that lets calling code react
  differently to "duplicate email" vs. "invalid data" vs. "dangling reference."
- **Choosing `ON DELETE CASCADE` reflexively.** It's right for true ownership
  relationships (order → order items) and often wrong for reference relationships
  (order → the customer who's allowed to be deleted independently, perhaps
  soft-deleted or anonymized instead).

## What's next

Level 06 uses these same tables to introduce joins — reading data back out across
the relationships these foreign keys declare.
