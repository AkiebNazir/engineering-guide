# Creating Tables and Data Types

## The mental model

`CREATE TABLE` is where you make the design decisions from level 00 concrete: which
columns exist, what type each one holds, which ones are required, and what a column
should default to when a row doesn't specify it. Postgres enforces every one of
these at write time — a bad `INSERT` is rejected immediately, not silently coerced
or accepted with a `NULL`.

## A real `CREATE TABLE`

```sql
DROP TABLE IF EXISTS products;

CREATE TABLE products (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sku         UUID NOT NULL DEFAULT gen_random_uuid(),
    name        VARCHAR(120) NOT NULL,
    description TEXT,
    price_cents NUMERIC(12,2) NOT NULL,
    in_stock    BOOLEAN NOT NULL DEFAULT true,
    attributes  JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Run through Python and inspected via `information_schema` (the standard,
database-agnostic catalog of table structure that every <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> database exposes):

```python
import psycopg

with psycopg.connect("postgresql://dsa:dsa@localhost:5544/dsa") as conn:
    conn.execute("DROP TABLE IF EXISTS products;")
    conn.execute("""
        CREATE TABLE products (
            id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            sku         UUID NOT NULL DEFAULT gen_random_uuid(),
            name        VARCHAR(120) NOT NULL,
            description TEXT,
            price_cents NUMERIC(12,2) NOT NULL,
            in_stock    BOOLEAN NOT NULL DEFAULT true,
            attributes  JSONB NOT NULL DEFAULT '{}',
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)
    conn.commit()

    cur = conn.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'products'
        ORDER BY ordinal_position;
    """)
    for r in cur.fetchall():
        print(r)
```

Real output:

```text
('id', 'bigint', 'NO', None)
('sku', 'uuid', 'NO', 'gen_random_uuid()')
('name', 'character varying', 'NO', None)
('description', 'text', 'YES', None)
('price_cents', 'numeric', 'NO', None)
('in_stock', 'boolean', 'NO', 'true')
('attributes', 'jsonb', 'NO', "'{}'::jsonb")
('created_at', 'timestamp with time zone', 'NO', 'now()')
```

**Go (native `pgxpool`)** — the same `CREATE TABLE` and `information_schema` check,
scanning into a nullable pointer for `column_default` since not every column has one:

```go
pool, err := pgxpool.New(ctx, "postgresql://dsa:dsa@localhost:5544/dsa")
// ... error handling omitted, see level 01

pool.Exec(ctx, `DROP TABLE IF EXISTS products;`)
pool.Exec(ctx, `
    CREATE TABLE products (
        id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        sku         UUID NOT NULL DEFAULT gen_random_uuid(),
        name        VARCHAR(120) NOT NULL,
        description TEXT,
        price_cents NUMERIC(12,2) NOT NULL,
        in_stock    BOOLEAN NOT NULL DEFAULT true,
        attributes  JSONB NOT NULL DEFAULT '{}',
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    );
`)

rows, _ := pool.Query(ctx, `
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_name = 'products'
    ORDER BY ordinal_position;
`)
defer rows.Close()
for rows.Next() {
    var colName, dataType, isNullable string
    var colDefault *string   // nullable column -> pointer, not a plain string
    rows.Scan(&colName, &dataType, &isNullable, &colDefault)
    def := "<nil>"
    if colDefault != nil {
        def = *colDefault
    }
    fmt.Printf("(%s, %s, %s, %s)\n", colName, dataType, isNullable, def)
}
```

Real output — identical shape to the Python run above, just Go's zero-value-free `nil`
in place of Python's `None`:

```text
(id, bigint, NO, <nil>)
(sku, uuid, NO, gen_random_uuid())
(name, character varying, NO, <nil>)
(description, text, YES, <nil>)
(price_cents, numeric, NO, <nil>)
(in_stock, boolean, NO, true)
(attributes, jsonb, NO, '{}'::jsonb)
(created_at, timestamp with time zone, NO, now())
```

The `*string` for `column_default` matters: Go has no direct equivalent of "this
column can hold `NULL`" the way Python's `None` fits into any variable. Scanning a
nullable <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> column into a plain `string` panics the moment a row's value is actually
`NULL` — you need a pointer type (`*string`) or one of `database/sql`'s `sql.NullString`
/ pgx's equivalents to represent "no value" safely.

## The data types, and when to reach for each

| Type | Use for | Watch out for |
|---|---|---|
| `INT` / `BIGINT` | Whole numbers, counters, IDs | `INT` maxes at ~2.1 billion — use `BIGINT` for any ID column that might grow large |
| `TEXT` | Any string, unbounded length | Postgres has no performance penalty for `TEXT` over `VARCHAR(n)` — Postgres stores both the same way internally |
| `VARCHAR(n)` | A string with a real, meaningful length cap | The cap is enforced (an insert over `n` chars errors), so only use it when the limit is a real business rule, not an arbitrary guess |
| `NUMERIC(p, s)` | Money, anything needing exact decimal arithmetic | `p` = total digits, `s` = digits after the decimal point. **Never use `FLOAT`/`REAL` for money** — binary floating point cannot represent most decimal fractions exactly |
| `BOOLEAN` | True/false flags | Postgres accepts `true`/`false`/`'t'`/`'f'`/`1`/`0` on input but always stores and returns `true`/`false` |
| `TIMESTAMP` | A date+time with **no** timezone attached | Rarely what you want for real-world event times — it means "some clock, unspecified" |
| `TIMESTAMPTZ` | A date+time **with** timezone handling | Despite the name, Postgres does not store the timezone — it converts to UTC internally and converts back to your session's timezone on read. This is almost always the right choice for "when did this happen" |
| `UUID` | A globally-unique, non-sequential identifier | `gen_random_uuid()` has been a Postgres built-in (no extension needed) since v13 |
| `JSONB` | Semi-structured or schema-flexible data | Binary, indexable, and comparable — prefer it over the older `JSON` type, which stores the input text verbatim and reparses it on every access |

**Precision note on `JSONB`:** having it available doesn't mean you should reach for
it by default. A `JSONB` column bypasses everything level 00 said relational
databases give you for free — types, `NOT NULL`, foreign keys — for whatever's inside
it. Use it for genuinely variable, sparse, or client-defined attributes (like
`products.attributes` above); keep anything you'll filter, join on, or need the
database to enforce as a real typed column.

## `NOT NULL` and `DEFAULT`

- **`NOT NULL`** makes a column required. An `INSERT` that omits it (and has no
  `DEFAULT`) is rejected. Default every column to `NOT NULL` unless "we genuinely
  don't have this value yet" is a real, meaningful state for that column — level 05
  covers the difference between `NULL`, an empty string, and a zero in more depth
  when constraints come up.
- **`DEFAULT`** supplies a value when an `INSERT` doesn't specify the column. It can
  be a constant (`DEFAULT true`), or a function call evaluated per row at insert
  time (`DEFAULT now()`, `DEFAULT gen_random_uuid()`). Level 12 comes back to this
  distinction — constant defaults and volatile (function-call) defaults behave very
  differently when you add a column to a table that already has millions of rows.

## Common mistakes

- **Using `FLOAT`/`REAL` for money.** `0.1 + 0.2` is not exactly `0.3` in binary
  floating point — this is a real, well-known bug class, not a theoretical concern.
  Use `NUMERIC` for anything financial.
- **`TIMESTAMP` instead of `TIMESTAMPTZ`** for event times, then getting bitten when
  the application server and the database run in different timezones (or a server
  moves regions) and "now" silently means two different clocks.
- **Reaching for `JSONB` to avoid a schema design decision.** It's a relief valve,
  not a replacement for level 00's column-per-fact design.
- **Scanning a nullable column into a plain Go `string`/`int` instead of a pointer or
  `sql.NullString`/`pgtype` equivalent.** Both `database/sql` and pgx return a real
  error the moment a `NULL` value hits a non-nullable destination type — demonstrated
  above with `description`/`column_default`.

## What's next

Level 03 puts rows into this table and reads them back.
