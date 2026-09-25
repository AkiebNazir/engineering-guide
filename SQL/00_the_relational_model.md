# The Relational Model

## The mental model

A relational database stores everything as **tables**. A table is a fixed set of
**columns** (named, typed slots) and a growing set of **rows** (one entry per
column, per row). That's the entire storage model — no nested objects, no arrays of
arbitrary shape inside a cell (Postgres bends this rule a little with `jsonb`, more
on that in the next level, but the *default* shape is flat rows in tables).

```text
customers
+----+-------------------+----------------+
| id | email             | country        |
+----+-------------------+----------------+
| 1  | ana@example.com   | PT             |
| 2  | bo@example.com     | US             |
| 3  | cy@example.com     | JP             |
+----+-------------------+----------------+
```

A **schema** is a named collection of tables (plus the indexes, constraints, and
other objects that go with them) inside a database. Postgres's default schema is
called `public`; you can create more (`CREATE SCHEMA lab_09;`) to namespace things —
this module uses that trick so each level's practice tables don't collide.

## Why relational, not "just a spreadsheet"

A spreadsheet and a table *look* similar — rows and columns — but a spreadsheet has
no enforced structure. Nothing stops you from putting text in a column that's
supposed to hold numbers, duplicating a row, or leaving a required cell blank. A
relational database adds three things a spreadsheet doesn't have, and they are the
entire reason to use one:

1. **Enforced structure.** Every column has a declared type (`INT`, `TEXT`,
   `TIMESTAMPTZ`, ...). Try to put text where a number belongs and the database
   rejects the write, immediately, before bad data ever lands. A spreadsheet cell
   accepts anything you type into it.
2. **Enforced relationships.** A `customer_id` column in an `orders` table can be
   declared to *reference* the `customers` table's `id` column (a **foreign key**).
   The database then refuses to insert an order for a customer that doesn't exist,
   and refuses to delete a customer who still has orders (unless you explicitly say
   otherwise). Nothing like this exists between two spreadsheet tabs.
3. **A query language, not manual lookup.** "Give me every customer in Japan who
   placed an order over $100 last month, sorted by total spend" is one <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> query.
   In a spreadsheet, it's a chain of manually-maintained filters, VLOOKUPs, and
   pivot tables that silently go stale the moment the data changes shape.

## Rows, columns, and the primary key

Every well-designed table has a **primary key**: one column (or a small combination
of columns) that uniquely identifies each row and can never be duplicated or left
blank. Nothing else in the table's design matters more — every foreign key in every
other table that points at this table points at its primary key, and the database
uses it to find one specific row instantly rather than scanning everything.

```text
orders
+----+-------------+------------+   customer_id here is a FOREIGN KEY:
| id | customer_id | total_usd  |   it must match some row's id in customers.
+----+-------------+------------+
| 1  | 1           | 42.50      |
| 2  | 1           | 15.00      |
| 3  | 3           | 200.00     |
+----+-------------+------------+
     ^id here is the PRIMARY KEY: unique, never null, one per row.
```

Two rows in `orders` are allowed to share a `customer_id` (that's the whole point —
one customer, many orders) but no two rows may share an `id`. That asymmetry — one
column that must be unique, versus other columns that are free to repeat — is the
first design decision you make for every table you write.

Most Postgres tables today use an auto-incrementing integer (or a `UUID`) as a
synthetic primary key rather than a "natural" one like an email address, because
natural keys have a habit of turning out not to be as unique or as permanent as they
looked on day one (people change emails; two people can share a legal name).
Level 02 shows exactly how to declare one.

## What "relational" actually refers to

The word doesn't mean "tables relate to each other via foreign keys" — that's a
consequence, not the definition. It comes from Edgar Codd's 1970 model, where a
**relation** is the formal term for what we've been calling a table: a set of
tuples (rows) all conforming to the same header (columns). The practical takeaway
is simpler than the history: design your data as a set of small, well-typed tables
connected by keys, and let the database enforce the connections. Level 06 (joins) is
where you start *reading across* those connections in a single query — that's the
payoff for structuring the data this way in the first place.

## A statically-typed client sees this structure explicitly

Python's database drivers hand back loosely-typed tuples — `('ana@example.com', 'PT')` —
and let you worry about field names and types later. A Go client is upfront about it:
you declare a struct whose fields mirror the table's columns before you can scan a row
into anything, which makes level 00's "enforced structure" claim visible in the client
code, not just in the database:

```go
// Customer mirrors the customers table's row shape: one struct field per
// column, with a Go type matching each declared SQL type.
type Customer struct {
    ID      int64
    Email   string
    Country string
}
```

Levels 01 onward scan real query results into structs (or plain variables) exactly
this way — the struct definition *is* the client-side half of the schema.

## What's next

Level 01 gets you actually connected to a running Postgres instance, from both
`psql` and Python. Level 02 turns this level's concepts into real `CREATE TABLE`
statements with Postgres's actual data types.
