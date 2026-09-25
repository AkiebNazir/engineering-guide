# <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> — PostgreSQL from First Query to Production Client

This module teaches relational databases hands-on, using **PostgreSQL 16** as the
concrete system throughout. Every level runs real <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> against a real local database —
nothing here is theoretical pseudo-<abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>. Where a claim can be measured (a timing
number, a row count, an error message), it is measured on this machine and reported
honestly, including when the result is a little surprising. Every level's client-code
demos are shown in **both Python and Go**, side by side.

## Why a relational database, and why PostgreSQL specifically

A relational database stores data as **tables** — rows and typed columns — and lets
you declare relationships and invariants (foreign keys, uniqueness, checks) that the
database itself enforces, not your application code. You query with **<abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>**, a
declarative language: you say *what* rows you want, and the database's query planner
decides *how* to get them. That separation is the whole value proposition: your
queries stay simple while the engine gets smarter (better indexes, better plans)
underneath them.

This module uses PostgreSQL because:

- It is the closest thing the industry has to a **default answer** to "which
  database do I reach for" — used at every FAANG-adjacent company for OLTP
  workloads, and the one most interviewers assume when they say "<abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> database."
- It has genuinely good tooling for *learning* the concepts that generalize to every
  other relational database: a real query planner you can inspect with `EXPLAIN`, a
  strict type system, real constraint enforcement, real transaction isolation levels,
  and `psql`/`psycopg` that make the client side easy to see.
- Its internals (<abbr title="Multi-Version Concurrency Control. A concurrency control method commonly used by database management systems to provide concurrent access without locking.">MVCC</abbr>, <abbr title="Write-Ahead Logging. A family of techniques for providing atomicity and durability in database systems by writing modifications to a log before they are applied.">WAL</abbr>, B-tree indexes) are the same internals `CSFundamentals/03_databases_deep_dive.md`
  and `SystemDesign/building_blocks/06_database_internals.md` already teach in the
  abstract — this module is where those concepts stop being diagrams and start being
  things you run.

Nothing here is Postgres trivia for its own sake. Every level's *concept* (joins,
transactions, indexes, injection, migrations, pooling) applies to MySQL, <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> Server,
or any other relational database — the syntax and specific behaviors shown are
Postgres's, called out as such where they differ from other engines.

## Starting the lab environment

A `docker-compose.databases.yml` at the repo root brings up Postgres 16 on a
non-default port so it never collides with anything already running on your machine:

```bash
docker compose -f docker-compose.databases.yml up -d       # start (keeps data across restarts)
docker compose -f docker-compose.databases.yml down        # stop, keep data
docker compose -f docker-compose.databases.yml down -v     # stop, wipe data (fresh start)
```

Connection details: host `localhost`, port **5544**, user `dsa`, password `dsa`,
database `dsa`. The compose file sets `wal_level = logical` (needed for level 17's
logical-replication demo) on top of Postgres's `replica`-capable default.

```bash
psql "postgresql://dsa:dsa@localhost:5544/dsa"
```

```python
import psycopg   # psycopg v3 — pip install "psycopg[binary]"

with psycopg.connect("postgresql://dsa:dsa@localhost:5544/dsa") as conn:
    print(conn.execute("SELECT 1;").fetchone())
```

`SQL/requirements.txt` lists the Python packages every level's code samples need
(`psycopg[binary]`, `psycopg_pool`). Install them into whatever virtualenv you run
the samples from: `pip install -r SQL/requirements.txt`.

**Go.** Every level also shows Go client code, in two styles: `database/sql` (using
`github.com/jackc/pgx/v5/stdlib` as the driver — `github.com/lib/pq` is mentioned in
level 01 as the older, maintenance-mode alternative) and native `github.com/jackc/pgx/v5`
(`pgxpool`) for pgx's full feature set. As with the Python side, no `.go` files are
committed here — copy a snippet into your own scratch module and run it:

```bash
mkdir sql-lab && cd sql-lab && go mod init sql-lab
go get github.com/jackc/pgx/v5/pgxpool github.com/jackc/pgx/v5/stdlib github.com/lib/pq
```

Requires Go 1.25+ (pgx v5.11+'s minimum); with the default `GOTOOLCHAIN=auto`, `go run`
fetches a matching toolchain automatically if your installed `go` is older.

Every level's <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> is self-contained: each one drops and recreates its own tables (or
uses a `lab_NN` scratch schema) at the top of its code blocks, so you can run any
level's examples independently, in any order, without cleaning up after another
level first.

## Roadmap — 20 levels

| # | Level | What you'll be able to do |
|---|---|---|
| 00 | [The relational model](00_the_relational_model.md) | Explain tables/rows/columns/schemas and why relational beats a spreadsheet |
| 01 | [Connecting and your first query](01_connecting_and_first_query.md) | Connect via `psql` and Python `psycopg`; know what a connection, session, and cursor actually are |
| 02 | [Creating tables and data types](02_creating_tables_and_data_types.md) | Design a `CREATE TABLE` with the right Postgres types, `NOT NULL`, and `DEFAULT` |
| 03 | [Inserting and basic selects](03_inserting_and_basic_selects.md) | `INSERT`, `SELECT *` vs a column list, `LIMIT` |
| 04 | [Filtering, sorting, pagination](04_filtering_sorting_pagination.md) | `WHERE`/`ORDER BY`, and why keyset pagination beats `OFFSET` at scale |
| 05 | [Updating, deleting, constraints](05_updating_deleting_and_constraints.md) | `UPDATE`/`DELETE` safely, and let constraints reject bad data for you |
| 06 | [Joins](06_joins.md) | All four join types, self-joins, many-to-many, and why a bad join silently duplicates rows |
| 07 | [Aggregation and grouping](07_aggregation_and_grouping.md) | `GROUP BY`/`HAVING`, and window functions for running totals and rankings |
| 08 | [Subqueries and CTEs](08_subqueries_and_ctes.md) | Scalar/`IN`/`EXISTS` subqueries, `WITH`, and one recursive CTE |
| 09 | [Transactions and isolation levels](09_transactions_and_isolation_levels.md) | <abbr title="Atomicity, Consistency, Isolation, Durability - A set of properties of database transactions intended to guarantee data validity despite errors.">ACID</abbr> precisely, a real lost-update race, and how to prevent it in Postgres |
| 10 | [Indexing and query planning](10_indexing_and_query_planning.md) | Read `EXPLAIN ANALYZE`, and measure what an index is actually worth |
| 11 | [SQL injection and parameterized queries](11_sql_injection_and_parameterized_queries.md) | Exploit a real vulnerable query, then close the hole for good |
| 12 | [Schema migrations](12_schema_migrations.md) | Change a live schema without downtime, the expand/contract way |
| 13 | [Connection pooling, ORM vs raw SQL](13_connection_pooling_and_orm_vs_raw_sql.md) | Why pools exist, and the N+1 query trap measured live |
| 14 | [Being a client: capstone](14_being_a_client_capstone.md) | A small <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr> service with pooling, retries, and timeouts, tying it all together |
| 15 | [Bonus: how Postgres executes a query](15_bonus_how_postgres_executes_a_query.md) | *(optional)* parser → planner → executor → storage, connected end to end |
| 16 | [Normalization and denormalization](16_normalization_and_denormalization.md) | Prove the three anomalies live, then fix them by functional dependency — and know when to deliberately reverse it |
| 17 | [Replication and high availability](17_replication_and_high_availability.md) | Physical vs. logical replication, a real replica measured for lag, and what a failover actually requires |
| 18 | [Sharding and horizontal scaling](18_sharding_and_horizontal_scaling.md) | Why joins/FKs/transactions don't shard for free, Postgres's native partitioning measured, and shard-key tradeoffs |
| 19 | [Interview playbook](19_interview_playbook.md) | The concrete questions this ladder gets asked as, answered precisely, with worked queries |

Work through them in order — each level assumes the previous ones. Levels 09, 12,
15, and 18 point to deeper material already written elsewhere in this repo
(`CSFundamentals/03_databases_deep_dive.md`, `SoftwareDesign/09_data_design_and_schema_evolution.md`,
`SystemDesign/building_blocks/06_database_internals.md`, `SystemDesign/building_blocks/10_distributed_systems_theory.md`)
rather than repeating it — follow those links when a level says to.
