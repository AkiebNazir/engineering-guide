# Connecting and Your First Query

## The mental model

Before any <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> matters, you need to know what you're actually talking to. A running
Postgres instance is one **server process** (`postgres`) that listens on a <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> port
and manages one shared set of databases on disk. When a client connects, Postgres
forks (or hands off to) a dedicated **backend process** for that one **connection** —
this is Postgres's per-connection process model, and it's the reason connection
pooling (level 13) matters at all: every connection is a real <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr> process with real
memory overhead, not a free abstraction.

```arch
%% caption: Every client connection gets its own backend process, forked by the postgres server; all backends share the same database on disk.
node c1 "psql" at 0,0 icon=cli
node c2 "psycopg script" at 2,0 icon=code
node s "postgres server process" at 1,1 icon=postgresql
node b1 "backend process" at 0,2 icon=process sub="for C1's connection"
node b2 "backend process" at 2,2 icon=process sub="for C2's connection"
node d "dsa database" at 1,3 icon=db sub="on disk"
c1 -> s : "TCP :5544"
c2 -> s : "TCP :5544"
s -> b1 : "forks"
s -> b2 : "forks"
b1 -> d
b2 -> d
```

A **session** is everything that happens on one connection between the time it
opens and the time it closes: which database and user you're acting as, any
session-level settings you've changed (`SET statement_timeout = ...`), and any
transaction currently in progress. A **cursor**, in the client-library sense used
here, is a small object that represents "the result of the last statement I ran" —
you fetch rows from it, and closing it (or the connection) discards them.

This module's Postgres instance is already running via `docker-compose.databases.yml`
at the repo root, mapped to **host port 5544** — see `SQL/README.md` if it isn't up
yet.

## Connecting with `psql`

`psql` is Postgres's official command-line client. It opens one connection, gives
you an interactive <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> prompt, and is the fastest way to poke at a database by hand.

```bash
psql "postgresql://dsa:dsa@localhost:5544/dsa"
```

```text
psql (16.15)
Type "help" for help.

dsa=# SELECT 1;
 ?column?
----------
        1
(1 row)

dsa=# SELECT version();
                                                          version
----------------------------------------------------------------------------------------------------------------------------
 PostgreSQL 16.15 (Debian 16.15-1.pgdg13+2) on aarch64-unknown-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
(1 row)

dsa=# \q
```

(Output above is a real transcript from this environment — `\q` quits.) Useful
`psql` meta-commands while you're learning: `\dt` lists tables, `\d tablename`
describes a table's columns and constraints, `\timing` toggles showing how long each
query took.

## Connecting with Python (`psycopg` v3)

`psycopg` is the standard PostgreSQL driver for Python. This module uses **v3**,
whose <abbr title="Application Programming Interface">API</abbr> differs from the older, still-widely-deployed psycopg2 in a few ways worth
knowing up front: v3 supports `with psycopg.connect(...) as conn:` to auto-close the
connection, `conn.execute(...)` runs a statement directly on the connection without
you creating a cursor first (though `conn.cursor()` still exists and is used when you
need more control), and `%s` is still the placeholder syntax for parameters.

```python
import psycopg

with psycopg.connect("postgresql://dsa:dsa@localhost:5544/dsa") as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT 1;")
        print("SELECT 1 ->", cur.fetchone())

        cur.execute("SELECT version();")
        print("version ->", cur.fetchone()[0])

        cur.execute("SELECT current_database(), current_user;")
        print("db/user ->", cur.fetchone())
```

Real output from running this against the lab database:

```text
SELECT 1 -> (1,)
version -> PostgreSQL 16.15 (Debian 16.15-1.pgdg13+2) on aarch64-unknown-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
db/user -> ('dsa', 'dsa')
```

The shorthand used everywhere else in this module — `conn.execute(...)` instead of
opening an explicit cursor — does the same thing and returns a cursor you can chain
`.fetchone()` / `.fetchall()` onto directly:

```python
with psycopg.connect("postgresql://dsa:dsa@localhost:5544/dsa") as conn:
    row = conn.execute("SELECT 1;").fetchone()
    print(row)   # (1,)
```

## Connecting with Go

Go has no single official driver the way Python has `psycopg` — the ecosystem
converged on two different, both-legitimate ways in:

- **`database/sql`** — Go's standard library defines a generic `database/sql` <abbr title="Application Programming Interface">API</abbr>
  that works against *any* <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> database, with the actual database-specific code living
  in a separate driver package you import purely for its side effect of registering
  itself (the blank `_` import below). `github.com/lib/pq` was the traditional Postgres
  driver for this <abbr title="Application Programming Interface">API</abbr> for years and is still extremely common in existing codebases,
  but it's in maintenance mode (no new features) — `github.com/jackc/pgx/v5/stdlib`
  is the actively-maintained way to get a `database/sql`-compatible driver today,
  backed by pgx underneath. Reach for `database/sql` when you want your code portable
  across <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> databases, or need to work with tooling built against the standard
  interface (many ORMs, migration tools, and observability wrappers expect a
  `*sql.DB`).
- **Native `pgx`** (`github.com/jackc/pgx/v5/pgxpool`) — bypasses `database/sql`
  entirely for direct access to Postgres-specific features `database/sql`'s generic
  interface can't express (the binary wire protocol, `COPY`, richer native type
  mapping, batched queries) and is typically faster as a result. Reach for this when
  you know you're committed to Postgres specifically and want its full feature set.

**`database/sql` + `pgx/v5/stdlib`:**

```go
package main

import (
    "database/sql"
    "fmt"

    _ "github.com/jackc/pgx/v5/stdlib" // registers the "pgx" database/sql driver
)

func main() {
    db, err := sql.Open("pgx", "postgresql://dsa:dsa@localhost:5544/dsa")
    if err != nil {
        panic(err)
    }
    defer db.Close()

    var one int
    db.QueryRow("SELECT 1;").Scan(&one)
    fmt.Println("SELECT 1 ->", one)

    var version string
    db.QueryRow("SELECT version();").Scan(&version)
    fmt.Println("version ->", version)

    var dbName, user string
    db.QueryRow("SELECT current_database(), current_user;").Scan(&dbName, &user)
    fmt.Println("db/user ->", dbName, user)
}
```

Real output from running this against the lab database:

```text
SELECT 1 -> 1
version -> PostgreSQL 16.15 (Debian 16.15-1.pgdg13+2) on aarch64-unknown-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
db/user -> dsa dsa
```

**Native `pgxpool`** — same three queries, no `database/sql` in between:

```go
package main

import (
    "context"
    "fmt"

    "github.com/jackc/pgx/v5/pgxpool"
)

func main() {
    ctx := context.Background()

    pool, err := pgxpool.New(ctx, "postgresql://dsa:dsa@localhost:5544/dsa")
    if err != nil {
        panic(err)
    }
    defer pool.Close()

    var one int
    pool.QueryRow(ctx, "SELECT 1;").Scan(&one)
    fmt.Println("SELECT 1 ->", one)

    var version string
    pool.QueryRow(ctx, "SELECT version();").Scan(&version)
    fmt.Println("version ->", version)
}
```

Real output — identical, since it's the same database answering the same query:

```text
SELECT 1 -> 1
version -> PostgreSQL 16.15 (Debian 16.15-1.pgdg13+2) on aarch64-unknown-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
```

Notice `pgxpool.New` — unlike `psycopg.connect`'s single connection, both Go styles
shown here hand you a **pool** by default (`sql.DB` is also a pool, not a single
connection, even though `sql.Open` doesn't dial anything until the first query) —
level 13's connection-pooling lesson is Go's *default* behavior from the first line
of code, not an opt-in optimization added later the way it is in the `psycopg`
examples in this module.

## What `with psycopg.connect(...) as conn` actually does

Using the connection as a context manager does **two** things, and mixing them up is
the single most common `psycopg` v3 gotcha:

- On a clean exit, it **commits** whatever transaction was open (level 09 covers
  transactions properly, but note now: `psycopg` starts a transaction implicitly on
  your first statement unless the connection is in `autocommit` mode).
- On an exception, it **rolls back** instead.
- Either way, it does **not** close the connection for you when used this way inside
  a function that keeps using `conn` afterward — the outer `with` block *does* close
  it when the block exits. If you want every statement to commit immediately without
  an explicit `conn.commit()`, pass `autocommit=True` to `connect()` — several later
  levels use this for scratch/demo code where transaction boundaries aren't the
  point being taught.

```python
with psycopg.connect("postgresql://dsa:dsa@localhost:5544/dsa", autocommit=True) as conn:
    conn.execute("SELECT 1;")   # takes effect immediately, no conn.commit() needed
```

## Common mistakes

- **Forgetting to commit.** Without `autocommit=True`, an `INSERT`/`UPDATE`/`DELETE`
  is invisible to every other connection (and lost if the process crashes) until you
  call `conn.commit()`. This is the #1 "my data disappeared" bug for people new to
  `psycopg`.
- **Opening a new connection per query in a loop.** Each connection is a real
  process fork on the server side with real setup cost — level 13 measures exactly
  how much this costs and what a connection pool buys you instead.
- **Confusing `psql`'s `\q`/`\d` meta-commands with <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>.** They start with a
  backslash and are `psql`-specific; they are not valid inside a Python string
  passed to `execute()`.
- **Assuming Go's `sql.Open` connected.** It doesn't — it just validates the DSN and
  sets up the pool's bookkeeping; the actual <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> connection happens lazily on the
  first query. A typo'd host or a database that isn't up yet won't error until then,
  which surprises people expecting `sql.Open` to behave like `psycopg.connect` (which
  does connect immediately). Call `db.Ping()` right after `sql.Open` if you want to
  fail fast instead.

## What's next

Level 02 uses this connection to actually create a table with real Postgres data
types.
