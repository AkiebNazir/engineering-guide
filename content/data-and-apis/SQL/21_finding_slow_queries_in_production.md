# Finding Slow Queries in Production

## The mental model

Level 10 taught you to read `EXPLAIN ANALYZE` for a query you already suspect. In
production the hard part comes first: a database serving thousands of statements a
second is "slow", and you have to work out **which** query to `EXPLAIN`. You don't
guess from the application code. You ask Postgres, which already records what it runs
if you let it. There are four places to look, and each one answers a different
question:

| Tool | Question it answers | Granularity |
|---|---|---|
| **`pg_stat_statements`** | Which query *shapes* use the most time overall, since the stats were last reset? | Aggregated per normalized query |
| **`log_min_duration_statement`** | Which individual executions took longer than N ms, and with what parameters? | One log line per slow execution |
| **`auto_explain`** | What plan did that slow execution actually use? | One plan per slow execution, in the log |
| **`pg_stat_activity`** | What is running, waiting or stuck **right now**? | One row per connection, live |

Then you still have to fix the query, which means reading its plan with
`EXPLAIN (ANALYZE, BUFFERS)` and knowing which lines matter. This level goes through all
four tools on a workload with one obvious problem and two hidden ones, fixes them, and
measures the result.

```arch
%% caption: Where each tool sits. Every statement updates the cumulative counters; only slow ones reach the log; pg_stat_activity is a live view of each connection.
node app "App servers" at 1,0 icon=server sub="sets application_name"
node be "Postgres backend" at 1,1 icon=postgresql sub="parse, plan, execute"
node pss "pg_stat_statements" at 0,2 shape=card icon=metrics sub="totals per query shape"
node log "Server log" at 1,2 shape=card icon=logs sub="slow statements + plans"
node act "pg_stat_activity" at 2,2 shape=card icon=monitor sub="each session, right now"
node you "On-call engineer" at 1,3 icon=user
app -> be : "SQL"
be -> pss : "all"
be -> log : "slow"
be -> act : "live"
pss -> you
log -> you
act -> you
```

## Setup used for this level

Two tables that look like an online shop: 50,000 customers and 1,000,000 orders
(65 MB), with only primary-key indexes:

```sql
DROP TABLE IF EXISTS shop_orders, shop_customers;
CREATE TABLE shop_customers (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email      TEXT NOT NULL,
    country    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE shop_orders (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES shop_customers(id),
    status      TEXT NOT NULL,
    total_cents INT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL
);
INSERT INTO shop_customers (email, country)
SELECT 'User' || i || '@Example.com',
       (ARRAY['US','UK','DE','FR','BR','IN'])[1 + i % 6]
FROM generate_series(1, 50000) AS i;
INSERT INTO shop_orders (customer_id, status, total_cents, created_at)
SELECT 1 + (i::bigint * 7919) % (SELECT count(*) FROM shop_customers),   -- spread over every customer
       (ARRAY['paid','paid','paid','shipped','refunded'])[1 + i % 5],
       500 + (i * 37) % 20000,
       now() - (i % 525600) * interval '1 minute'
FROM generate_series(1, 1000000) AS i;
ANALYZE shop_customers, shop_orders;
```

Note what's missing: `shop_orders.customer_id` is a foreign key, and **Postgres does
not index foreign-key columns automatically** (the referenced side, the primary key,
is indexed; the referencing side is not). That's the most common missing index in real
schemas.

### Turning the tools on

Most of this level is server administration, so run it in `psql` against the lab
Postgres. The in-browser Postgres behind **Run** has no `pg_stat_statements`, no server
log and no other connections; the blocks that need those say so in a comment and show
the error you'd get. The setup above, `pg_stat_activity`, the `EXPLAIN` and the index
fix all run in the browser.

`pg_stat_statements` and `auto_explain` ship with Postgres but are loaded as shared
libraries at server start, so they need a config change and a restart:

```sql
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements, auto_explain';
```

```bash
docker restart dsa-postgres        # shared_preload_libraries only takes effect at startup
```

```sql
-- in the browser, expect an error: the extension isn't available there
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;   -- once per database: creates the view
SELECT pg_stat_statements_reset();                   -- start counting from zero
```

`ALTER SYSTEM` writes to `postgresql.auto.conf` inside the data volume, so it survives
restarts but not `docker compose ... down -v`. (If you'd rather make it permanent, add
`"-c", "shared_preload_libraries=pg_stat_statements,auto_explain"` to the `command:` list
for `postgres` in `docker-compose.databases.yml`.) Managed services have their own switch
(a parameter group on Amazon RDS/Aurora, database flags on Cloud SQL). On most of them
`pg_stat_statements` is already available and needs only the `CREATE EXTENSION`;
`auto_explain` is usually something you enable yourself.

### The workload

A script plays the application: lots of cheap primary-key lookups, a "my recent orders"
query, a case-insensitive login lookup, and a handful of report queries:

```python
"""Simulate an application's traffic: many cheap queries, a few expensive ones."""
import random
import psycopg

DSN = "postgresql://dsa:dsa@localhost:5544/dsa"
random.seed(21)

with psycopg.connect(DSN, autocommit=True) as conn:
    conn.execute("SET application_name = 'shop-api'")
    for _ in range(20_000):                       # 1. profile page: PK lookup, very cheap
        conn.execute("SELECT id, email, country FROM shop_customers WHERE id = %s",
                     (random.randint(1, 50_000),)).fetchone()
    for _ in range(300):                          # 2. "my recent orders": no index on customer_id
        conn.execute("SELECT id, status, total_cents, created_at FROM shop_orders "
                     "WHERE customer_id = %s ORDER BY created_at DESC LIMIT 10",
                     (random.randint(1, 50_000),)).fetchall()
    for _ in range(200):                          # 3. login: case-insensitive email match
        conn.execute("SELECT id FROM shop_customers WHERE lower(email) = %s",
                     (f"user{random.randint(1, 50_000)}@example.com",)).fetchone()
    for _ in range(5):                            # 4. nightly-style revenue report
        conn.execute("SELECT date_trunc('day', created_at) AS day, sum(total_cents) "
                     "FROM shop_orders WHERE status = 'paid' "
                     "AND created_at > now() - interval '30 days' "
                     "GROUP BY 1 ORDER BY 1").fetchall()
print("workload done")
```

It takes about 15 seconds. If you had to guess which query to optimize from reading
the code, the report (a 30-day aggregate over a million rows) looks like the obvious
suspect. It isn't.

## Tool 1: `pg_stat_statements`, the first place to look

`pg_stat_statements` keeps one row per **normalized** statement: literals become `$1`,
`$2`..., so `WHERE id = 7` and `WHERE id = 99` count as one query shape. For each shape
it accumulates calls, total/mean/min/max/stddev execution time, rows returned, buffer
hits and reads, temp-file usage, WAL generated, and (with `track_io_timing` on) time
spent waiting on I/O. It's cheap enough to leave on permanently; almost every production
Postgres runs it.

The query you'll run most often, sorted by **total** time:

```sql
-- in the browser, expect an error: relation "pg_stat_statements" does not exist
SELECT queryid, calls,
       round(total_exec_time::numeric, 0)  AS total_ms,
       round(mean_exec_time::numeric, 2)   AS mean_ms,
       left(regexp_replace(query, '\s+', ' ', 'g'), 48) AS query
FROM pg_stat_statements
WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
ORDER BY total_exec_time DESC
LIMIT 6;
```

Real output after one run of the workload:

```text
       queryid        | calls | total_ms | mean_ms |                      query
----------------------+-------+----------+---------+--------------------------------------------------
  7094747253405871443 |   196 |     5195 |   26.50 | SELECT id, status, total_cents, created_at FROM
  8396259851670863588 |   104 |     2851 |   27.42 | SELECT id, status, total_cents, created_at FROM
  3628322604940054147 |   200 |     2752 |   13.76 | SELECT id FROM shop_customers WHERE lower(email)
 -7132989859111832772 |     5 |      265 |   53.03 | SELECT date_trunc($1, created_at) AS day, sum(to
 -8684704282471483609 | 13164 |      111 |    0.01 | SELECT id, email, country FROM shop_customers WH
   595846252465972475 |  6836 |       58 |    0.01 | SELECT id, email, country FROM shop_customers WH
(6 rows)
```

Two surprises before we even rank anything.

**The same query appears twice.** The orders query is split 196 + 104, the PK lookup
13,164 + 6,836. The `queryid` is a hash of the *parsed* query, and that includes the
parameter types. psycopg 3 sends a Python `int` as the smallest type that fits it:
`int2` for values up to 32,767 and `int4` above. Random ids from 1 to 50,000 fall below
32,768 about 65% of the time, and 13,164 / 20,000 = 65.8%. Different search paths,
different users and different databases also split a query into several rows. Group by
the query text when you rank, or you'll under-count exactly the queries that matter:

```sql
-- in the browser, expect an error: relation "pg_stat_statements" does not exist
SELECT left(regexp_replace(query, '\s+', ' ', 'g'), 48) AS query,
       sum(calls) AS calls,
       round(sum(total_exec_time)::numeric, 0) AS total_ms,
       round((sum(total_exec_time) / sum(calls))::numeric, 3) AS mean_ms,
       round((100 * sum(total_exec_time) / sum(sum(total_exec_time)) OVER ())::numeric, 1) AS pct,
       sum(shared_blks_hit + shared_blks_read) AS blocks
FROM pg_stat_statements
WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
GROUP BY query
ORDER BY total_ms DESC
LIMIT 5;
```

```text
                      query                       | calls | total_ms | mean_ms | pct  | blocks
--------------------------------------------------+-------+----------+---------+------+---------
 SELECT id, status, total_cents, created_at FROM  |   300 |     8046 |  26.821 | 71.6 | 2534400
 SELECT id FROM shop_customers WHERE lower(email) |   200 |     2752 |  13.761 | 24.5 |   91600
 SELECT date_trunc($1, created_at) AS day, sum(to |     5 |      265 |  53.034 |  2.4 |   42240
 SELECT id, email, country FROM shop_customers WH | 20000 |      169 |   0.008 |  1.5 |   60006
 SELECT pg_stat_statements_reset()                |     1 |        0 |   0.091 |  0.0 |       0
(5 rows)
```

**The report is not the problem.** It has the worst *mean* (53 ms) but runs 5 times and
accounts for 2.4% of database time. The "recent orders" query is only 27 ms per call,
fast enough that nobody would flag it in a code review, but it runs 60x as often and
is **72% of all the time the database spent**. It also touched 2.5 million buffer pages
(about 20 GB of 8 kB page visits) to return 3,000 rows. The login lookup is second
at 24.5%.

That's the central rule of this tool: **sort by `total_exec_time` to find what's costing
the system, and by `mean_exec_time` to find what's hurting individual users.** Both
lists matter, but capacity problems (CPU at 90%, replicas falling behind) almost always
come from the top of the total list, and that's usually a frequent, moderately slow
query rather than a rare slow one.

Other orderings worth knowing:

| Sort by | Finds |
|---|---|
| `total_exec_time` | Where the database's time goes (the default) |
| `mean_exec_time` (with `calls > 100`) | Queries users feel as latency |
| `shared_blks_read` | Queries that pull pages from disk / OS cache: I/O pressure |
| `temp_blks_written` | Sorts and hashes spilling to disk: `work_mem` too small or a bad plan |
| `rows / calls` | Queries returning far more rows than the page can show |
| `stddev_exec_time / mean_exec_time` | Queries that are *sometimes* slow: lock waits, plan flips, parameter skew |
| `wal_bytes` | Writes that generate the most WAL, which is what replicas must replay |

Facts to get right about it:

- **Column names changed in Postgres 13**: `total_time` became `total_exec_time`, and
  `total_plan_time` was added (it stays 0 unless `pg_stat_statements.track_planning` is
  on). Old blog posts use the old names.
- **Counters are cumulative since the last reset** (or since the server started, if
  `pg_stat_statements.save` is off). To measure an incident, snapshot the view twice and
  diff, or reset, wait, and read. Most monitoring tools (pganalyze, Datadog, Grafana's
  Postgres dashboards, the RDS Performance Insights view) do the diffing for you.
- **It holds at most `pg_stat_statements.max` shapes** (default 5,000); the least-used
  are evicted and lose their history. Literals are normalized even when an app inlines
  them into the SQL text, but anything that changes the *structure* creates new shapes:
  generated table or column names, and `IN (...)` lists of varying length (one shape per
  length before Postgres 18, which collapses constant lists into one entry).
- **It can't tell you the parameter values** or which execution was slow. That's what
  the next two tools are for.

## Tool 2: `log_min_duration_statement`, the individual slow executions

This setting logs every statement that takes longer than a threshold, with its duration
and bind parameters:

```sql
-- in the browser, expect an error: Run sends a block as one transaction, and ALTER SYSTEM
-- can't run inside one (psql sends each statement on its own)
ALTER SYSTEM SET log_min_duration_statement = '250ms';   -- -1 disables; 0 logs everything
SELECT pg_reload_conf();                                  -- no restart needed
```

A lower threshold (20 ms) makes the login lookup show up. The line it writes when a
driver uses the extended protocol with bind parameters, as psycopg does:

```text
2026-09-29 09:05:10.415 UTC [4476] LOG:  duration: 31.691 ms  execute <unnamed>: SELECT id FROM shop_customers WHERE lower(email) = $1
2026-09-29 09:05:10.415 UTC [4476] DETAIL:  parameters: $1 = 'user4242@example.com'
```

The parameters are exactly what `pg_stat_statements` can't give you. They matter when a
query is fast for most inputs and slow for a few: a customer with 200,000 orders, a
tenant 100x bigger than the rest. Take the logged values and run `EXPLAIN ANALYZE` with
them.

Practical settings:

- **Pick a threshold you can afford.** Every line is written synchronously to the log,
  so `0` on a busy server can itself cause a slowdown and fills disks fast. 100 ms–1 s is
  a common production range, depending on what "slow" means for your application.
- **Sample when you need a low threshold.** Postgres 13+ has
  `log_min_duration_sample` + `log_statement_sample_rate` (log 1% of statements over
  10 ms, and 100% of those over the main threshold), and `log_transaction_sample_rate`
  (Postgres 12+) logs every statement of a random fraction of transactions.
- **Parameters are data**, often personal data: e-mail addresses, names, tokens. Treat
  the log as sensitive, and consider `log_parameter_max_length` (Postgres 13+) to
  truncate or suppress them (`0` hides them).
- **Put `application_name` in `log_line_prefix`** (for example `'%m [%p] %a %u@%d '`) so
  each line says which service sent it. Set `application_name` in every service's DSN.

## Tool 3: `auto_explain`, the plan that actually ran

Knowing a query was slow at 03:12 isn't enough, because the plan you get when you run
`EXPLAIN` at 10:00 can be different: statistics changed, the cache is warm, the
parameters differ. `auto_explain` writes the **plan of the actual slow execution** into
the log:

```sql
-- in the browser, expect an error: ALTER SYSTEM can't run inside the one transaction a Run uses
ALTER SYSTEM SET auto_explain.log_min_duration = '250ms';  -- -1 (default) = off
ALTER SYSTEM SET auto_explain.log_analyze = on;            -- actual rows, like EXPLAIN ANALYZE
ALTER SYSTEM SET auto_explain.log_buffers = on;            -- Buffers: lines
ALTER SYSTEM SET auto_explain.log_timing = off;            -- keep row counts, skip per-node clocks
SELECT pg_reload_conf();
```

With the threshold at 20 ms, one call of the recent-orders query logged this:

```text
2026-09-29 09:05:03.713 UTC [4440] LOG:  duration: 26.073 ms  plan:
	Query Text: PREPARE q(bigint) AS SELECT id, status, total_cents, created_at FROM shop_orders WHERE customer_id = $1 ORDER BY created_at DESC LIMIT 10
	Query Parameters: $1 = '4242'
	Limit  (cost=14542.48..14543.64 rows=10 width=26) (actual rows=10 loops=1)
	  Buffers: shared hit=242 read=8206
	  ->  Gather Merge  (cost=14542.48..14544.34 rows=16 width=26) (actual rows=10 loops=1)
	        Workers Planned: 2
	        Workers Launched: 2
	        Buffers: shared hit=242 read=8206
	        ->  Sort  (cost=13542.45..13542.47 rows=8 width=26) (actual rows=6 loops=3)
	              Sort Key: created_at DESC
	              Sort Method: quicksort  Memory: 25kB
	              Buffers: shared hit=242 read=8206
	              ->  Parallel Seq Scan on shop_orders  (cost=0.00..13542.33 rows=8 width=26) (actual rows=7 loops=3)
	                    Filter: (customer_id = '4242'::bigint)
	                    Rows Removed by Filter: 333327
	                    Buffers: shared hit=128 read=8206
```

There's the diagnosis without reproducing anything: a parallel sequential scan over the
whole table, discarding 333,327 rows per process to find about 20.

The cost is the reason for the settings above. `log_analyze = on` makes Postgres
instrument **every** statement (it can't know in advance which ones will cross the
threshold), and per-node timing calls the system clock twice per row per node, which
on some hardware adds noticeable overhead. `log_timing = off` keeps the row counts,
which are what you usually need. On a hot system, also set `auto_explain.sample_rate`
(for example `0.05`) to instrument a fraction of statements. To try it in one session
without touching the server config, a superuser can run `LOAD 'auto_explain';` and
`SET auto_explain.log_min_duration = 0;`.

## Tool 4: `pg_stat_activity`, what's happening right now

The first three tools are about history. During an incident ("the API is timing out
*now*") you need the present: one row per server process, with its state, what it's
waiting on, and how long it's been doing it.

To see it, run three sessions: an admin tool that opens a transaction, updates a row
and then sits idle (someone's `psql` window left open before lunch); an API request that
needs to update the same row; and a report running `pg_sleep(5)` to stand in for a long
query. Two seconds in:

```sql
-- in the browser this returns no rows: your session is the only one, and it's excluded
SELECT pid, application_name AS app, state,
       wait_event_type || ':' || wait_event AS waiting_on,
       now() - xact_start  AS xact_age,
       now() - query_start AS query_age,
       pg_blocking_pids(pid) AS blocked_by,
       left(query, 45) AS query
FROM pg_stat_activity
WHERE datname = current_database() AND pid <> pg_backend_pid()
  AND backend_type = 'client backend'
ORDER BY xact_start;
```

```text
 pid  |      app       |        state        |     waiting_on     |    xact_age     |    query_age    | blocked_by |                     query
------+----------------+---------------------+--------------------+-----------------+-----------------+------------+-----------------------------------------------
 4595 | admin-tool     | idle in transaction | Client:ClientRead  | 00:00:02.094117 | 00:00:02.093162 | {}         | UPDATE shop_customers SET country = 'CA' WHER
 4598 | shop-api       | active              | Lock:transactionid | 00:00:01.593261 | 00:00:01.592964 | {4595}     | UPDATE shop_customers SET email = 'new42@exam
 4599 | nightly-report | active              | Timeout:PgSleep    | 00:00:01.592718 | 00:00:01.592492 | {}         | SELECT pg_sleep(5)
(3 rows)
```

How to read it:

- **`state`**: `active` (running a statement), `idle` (connected, nothing to do: normal
  for pooled connections), **`idle in transaction`** (a transaction is open but the
  client isn't sending anything). For `idle` sessions, `query` shows the *last*
  statement, not a current one.
- **`wait_event_type:wait_event`**: why an active backend isn't using CPU. `Lock:*` is a
  lock wait, `IO:DataFileRead` is disk, `LWLock:*` is internal contention,
  `Client:ClientRead` is waiting for the application. NULL on an active session means
  it's on the CPU.
- **`pg_blocking_pids(pid)`** names who holds the lock you're waiting for. Here the API
  request (4598) is blocked by the admin tool (4595), which isn't running anything. It
  just holds a row lock from its uncommitted `UPDATE`. Every other request for that
  customer row will queue behind it, and if the pool fills with blocked requests the
  whole API stops. An `idle in transaction` session with a large `xact_age` is the
  first thing to look for in a lock-up.
- **`xact_start` vs `query_start`**: a transaction that has been open for hours also
  stops `VACUUM` from removing dead rows anywhere in the database (it might still need
  to see them), which slowly bloats every table.

Getting out of it: `SELECT pg_cancel_backend(pid)` cancels the current statement (the
session survives); `SELECT pg_terminate_backend(pid)` closes the connection and rolls
back its transaction. For an idle-in-transaction blocker, cancel does nothing (there's
no running statement), so terminate is the tool.

And preventing it, with timeouts that belong in every production role's settings:

```sql
CREATE ROLE app_user LOGIN;   -- your application's role; skip this line if it exists
ALTER ROLE app_user SET statement_timeout = '5s';                     -- no query runs forever
ALTER ROLE app_user SET lock_timeout = '2s';                          -- fail fast instead of queueing on a lock
ALTER ROLE app_user SET idle_in_transaction_session_timeout = '60s';  -- kill forgotten transactions

SELECT rolname, rolconfig FROM pg_roles WHERE rolname = 'app_user';
```

Two more cumulative views are worth one query each. `pg_stat_user_tables` counts
sequential scans per table: a large table with a high `seq_scan` and a huge
`seq_tup_read` is missing an index for something. `pg_stat_user_indexes` shows indexes
with `idx_scan = 0`, which cost write time and disk for nothing (check replicas before
dropping one: the counters are per server).

```sql
-- unused indexes (empty for now: so far there are only primary keys, which are unique)
SELECT s.relname, s.indexrelname, s.idx_scan, pg_size_pretty(pg_relation_size(s.indexrelid))
FROM pg_stat_user_indexes s JOIN pg_index i ON i.indexrelid = s.indexrelid
WHERE NOT i.indisunique ORDER BY s.idx_scan, pg_relation_size(s.indexrelid) DESC;

-- tables read mostly by sequential scans
SELECT relname, seq_scan, seq_tup_read, idx_scan
FROM pg_stat_user_tables ORDER BY seq_tup_read DESC LIMIT 5;
```

## Reading `EXPLAIN (ANALYZE, BUFFERS)` like you mean it

Once you have the query and realistic parameters, you run it with `EXPLAIN (ANALYZE,
BUFFERS)`. Level 10 covered the basics. These are the lines that find the problem. Turn
on I/O timing first (session-level; it's cheap on modern Linux, and
`pg_test_timing` tells you if your clock source is slow):

```sql
SET track_io_timing = on;
```

**1. `Rows Removed by Filter` vs rows returned.** The recent-orders plan above: 333,327
removed per process to return 7. A filter that throws away almost everything it reads
means an index is missing or not usable.

**2. Estimated vs actual rows.** Each node shows the planner's guess (`rows=` inside
`cost=`) and the truth (`rows=` inside `actual`). The login query:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id FROM shop_customers WHERE lower(email) = 'user777@example.com';
```

```text
 Seq Scan on shop_customers  (cost=0.00..1208.00 rows=250 width=8) (actual time=1.503..15.038 rows=1 loops=1)
   Filter: (lower(email) = 'user777@example.com'::text)
   Rows Removed by Filter: 49999
   Buffers: shared hit=458
 Planning Time: 0.128 ms
 Execution Time: 15.058 ms
```

Estimated 250, actual 1. Postgres has no statistics on `lower(email)`, so it used its
default guess of 0.5% of the table. Here the error is harmless, but inside a join a 100x
misestimate is how the planner picks a nested loop that runs a billion times. When
estimates are off by 10x or more at the node where the time goes, fix the statistics
before anything else (`ANALYZE`, a higher `default_statistics_target` for that column,
`CREATE STATISTICS` for correlated columns, or an expression index, which gets its own
statistics).

**3. `loops`.** `actual time` and `rows` are **per loop**. A node showing
`rows=6 loops=3` produced 18 rows. In a nested loop, the inner side's per-loop time
multiplied by `loops` is its real cost. This is the most common misreading of a plan.
For parallel plans, `loops` counts the leader plus workers.

**4. `Buffers: shared hit / read / dirtied / written`.** Each unit is an 8 kB page.
`hit` came from Postgres's shared buffers, `read` had to come from the operating system
(its page cache, or the disk). Buffer counts don't vary with cache warmth the way timings
do, which makes them the best number to compare before and after a change. The report
query, run just after a restart:

```text
 Finalize GroupAggregate  (cost=19275.52..25538.57 rows=50525 width=16) (actual time=144.406..153.683 rows=31 loops=1)
   Group Key: (date_trunc('day'::text, created_at))
   Buffers: shared hit=114 read=8334
   I/O Timings: shared read=272.634
   ...
               ->  Parallel Seq Scan on shop_orders  (cost=0.00..16721.31 rows=21589 width=12) (actual time=0.109..134.473 rows=17280 loops=3)
                     Filter: ((status = 'paid'::text) AND (created_at > (now() - '30 days'::interval)))
                     Rows Removed by Filter: 316054
                     Buffers: shared read=8334
                     I/O Timings: shared read=272.634
 Execution Time: 153.929 ms
```

8,334 pages (65 MB) read to aggregate 51,840 rows. `I/O Timings` (272 ms) is larger than
the whole execution (154 ms) because it sums the time across the three parallel
processes. Also note the estimate: 50,525 groups predicted, 31 actual.

**5. Spills: `Sort Method: external merge  Disk:` and `Batches: N` on a Hash.** An
operation needed more than `work_mem` and wrote temp files. Sorting a million rows with
`work_mem = 1MB`:

```text
 Sort  (cost=169263.34..171763.34 rows=1000000 width=12) (actual time=437.079..511.692 rows=1000000 loops=1)
   Sort Key: total_cents DESC, id
   Sort Method: external merge  Disk: 21552kB
   Buffers: shared hit=102 read=8238, temp read=8079 written=8144
   I/O Timings: shared read=14.570, temp read=15.554 write=32.937
```

Raise `work_mem` for that session or query (it's per sort/hash node, per process, so
don't raise it globally without doing the arithmetic), or avoid the sort with an index
that already returns the rows in order.

**6. Where the time is.** `actual time=A..B` is time to first row..time to last row,
including children. Subtract the children's time to find the node that is expensive on
its own. For a long plan, paste it into a visualizer (explain.depesz.com,
explain.dalibo.com); they do the subtraction and the `loops` multiplication for you.

## Fixing it, and checking the fix

Two indexes, built with `CONCURRENTLY` so that production writes aren't blocked while
they build (it takes longer and can't run inside a transaction; if it fails it leaves an
`INVALID` index you must drop and retry):

```sql
-- in the browser, expect an error: Run sends a block as one transaction, and CONCURRENTLY
-- refuses to run inside one (psql sends each statement on its own)
CREATE INDEX CONCURRENTLY shop_orders_customer_created
    ON shop_orders (customer_id, created_at DESC);          -- filter AND sort order
CREATE INDEX CONCURRENTLY shop_customers_lower_email
    ON shop_customers (lower(email));                       -- matches the query's expression
ANALYZE shop_customers, shop_orders;
```

In the browser there are no other writers to block, so build the same two indexes the
plain way and look at the recent-orders plan:

```sql
CREATE INDEX IF NOT EXISTS shop_orders_customer_created
    ON shop_orders (customer_id, created_at DESC);
CREATE INDEX IF NOT EXISTS shop_customers_lower_email
    ON shop_customers (lower(email));
ANALYZE shop_customers, shop_orders;

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, status, total_cents, created_at FROM shop_orders
WHERE customer_id = 777 ORDER BY created_at DESC LIMIT 10;
```

The composite index serves both the `WHERE customer_id = $1` and the
`ORDER BY created_at DESC LIMIT 10`, so Postgres reads the first 10 index entries and
stops, with no sort:

```text
 Limit  (cost=0.42..42.60 rows=10 width=26) (actual time=0.044..0.062 rows=10 loops=1)
   Buffers: shared hit=17
   ->  Index Scan using shop_orders_customer_created on shop_orders  (cost=0.42..84.77 rows=20 width=26) (actual time=0.040..0.057 rows=10 loops=1)
         Index Cond: (customer_id = 4242)
         Buffers: shared hit=17
 Planning Time: 0.256 ms
 Execution Time: 0.080 ms
```

8,448 buffers → 17. Then reset the statistics, run the same workload, and rank again:

```text
                       query                        | calls | total_ms | mean_ms | pct
----------------------------------------------------+-------+----------+---------+------
 SELECT date_trunc($1, created_at) AS day, sum(tota |     5 |      274 |  54.842 | 59.3
 SELECT id, email, country FROM shop_customers WHER | 20000 |      164 |   0.008 | 35.6
 SELECT id, status, total_cents, created_at FROM sh |   300 |       22 |   0.074 |  4.8
 SELECT id FROM shop_customers WHERE lower(email) = |   200 |        2 |   0.008 |  0.3
```

Total database time for the same workload went from **about 11.2 s to about 0.46 s**
(roughly 24x). Recent orders went from 26.8 ms to 0.074 ms per call, and login from
13.8 ms to 0.008 ms. The report is now at the top of the list, with 59% of a much smaller
total. That's normal: the list always has a top entry. Stop when the top entries are
cheap enough for the workload, not when the list looks different.

**Go (native pgxpool):** a small "top queries" report you could run from a cron job or
an admin endpoint:

```go
package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	pool, err := pgxpool.New(ctx,
		"postgresql://dsa:dsa@localhost:5544/dsa?application_name=slow-query-report")
	if err != nil {
		log.Fatal(err)
	}
	defer pool.Close()

	rows, err := pool.Query(ctx, `
		SELECT left(regexp_replace(query, '\s+', ' ', 'g'), 50),
		       sum(calls)::bigint,
		       sum(total_exec_time),
		       sum(total_exec_time) / sum(calls)
		FROM pg_stat_statements
		WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
		GROUP BY query
		ORDER BY 3 DESC
		LIMIT $1`, 3)
	if err != nil {
		log.Fatal(err)
	}
	defer rows.Close()
	for rows.Next() {
		var query string
		var calls int64
		var totalMs, meanMs float64
		if err := rows.Scan(&query, &calls, &totalMs, &meanMs); err != nil {
			log.Fatal(err)
		}
		fmt.Printf("%8.0f ms total  %7d calls  %8.3f ms/call  %s\n", totalMs, calls, meanMs, query)
	}
	if err := rows.Err(); err != nil {
		log.Fatal(err)
	}
}
```

Real output (after the fix):

```text
     274 ms total        5 calls    54.842 ms/call  SELECT date_trunc($1, created_at) AS day, sum(tota
     164 ms total    20000 calls     0.008 ms/call  SELECT id, email, country FROM shop_customers WHER
      22 ms total      300 calls     0.074 ms/call  SELECT id, status, total_cents, created_at FROM sh
```

`application_name=slow-query-report` in the DSN is the habit to copy: every service,
job and tool that connects should name itself, so `pg_stat_activity` and the log say who
is doing what.

## The workflow, in order

1. **Is it happening now?** `pg_stat_activity`: long-running `active` queries, `Lock`
   waits and their `pg_blocking_pids`, old `idle in transaction` sessions. Cancel or
   terminate to stop the bleeding.
2. **What costs the most overall?** `pg_stat_statements` by `total_exec_time` (grouped by
   query text), diffed over the incident window. Also check the mean list.
3. **What parameters and plan did the slow executions have?** The log:
   `log_min_duration_statement` lines and `auto_explain` plans.
4. **Why is it slow?** `EXPLAIN (ANALYZE, BUFFERS)` with those parameters, on a replica or
   inside `BEGIN ... ROLLBACK` for writes. Look for rows removed by filter, estimate vs
   actual, loops, buffers read, spills.
5. **Fix and verify.** Index (`CONCURRENTLY`), rewrite, fix statistics, or change the
   access pattern (N+1 queries, level 13). Reset or snapshot the stats and compare the
   same workload before and after, using buffers as well as milliseconds.

## Common mistakes

- **Optimizing the slowest query instead of the most expensive one.** A 50 ms report run
  5 times a night matters less than a 27 ms query run 300 times a minute. Sort by total.
- **Forgetting that one query can be several `pg_stat_statements` rows.** Parameter
  types, users and search paths split it. Group by query text.
- **Running `EXPLAIN ANALYZE` with made-up parameters.** Plans depend on the values. Use
  the ones from the slow-query log.
- **Setting `log_min_duration_statement = 0` in production** "just for a bit". The
  logging becomes the load, and the log holds everyone's personal data.
- **Enabling `auto_explain.log_analyze` with timing on every statement** on a busy
  server without sampling.
- **Killing the waiting session instead of the blocker.** `pg_blocking_pids` tells you
  which is which. The blocker is often `idle in transaction`.
- **Plain `CREATE INDEX` on a busy table.** It blocks writes to the table for the whole
  build. Use `CONCURRENTLY`.
- **Having no timeouts.** Without `statement_timeout`, `lock_timeout` and
  `idle_in_transaction_session_timeout`, one bad session can hold up everything else.

## Interview questions

**"The database CPU is at 95%. How do you find the cause?"** `pg_stat_statements`,
ordered by `total_exec_time`, over the window when CPU went up (diff two snapshots). The
top few query shapes nearly always explain most of the load. Then `EXPLAIN (ANALYZE,
BUFFERS)` the top one with realistic parameters, and look for sequential scans with
large `Rows Removed by Filter`, misestimates and spills. Check `pg_stat_activity` too, in
case it's one runaway query rather than a pattern.

**"`pg_stat_statements` vs the slow query log?"** `pg_stat_statements` is aggregated and
cheap: it catches a 5 ms query run a million times, which a log threshold never would.
It has no parameters and no individual executions. The slow log (`log_min_duration_statement`)
has individual executions with parameters but only above a threshold. `auto_explain` adds
the plan that actually ran. Use them together.

**"A query is fast when I run it but slow in production. Why?"** Different parameters (a
skewed value hits a different plan), a generic plan for a prepared statement (after 5
executions Postgres may switch to a plan that ignores parameter values; see
`plan_cache_mode`), cold cache, lock waits (check `wait_event`), or concurrency. Get the
production plan with `auto_explain` instead of trusting your own `EXPLAIN`.

**"The API is timing out and the database looks idle."** Look for lock waits in
`pg_stat_activity`: sessions with `wait_event_type = 'Lock'`, their `pg_blocking_pids`,
and an `idle in transaction` blocker. Also check whether the connection pool is exhausted
(level 13). Fix with `pg_terminate_backend` on the blocker and prevent it with
`idle_in_transaction_session_timeout` and `lock_timeout`.

**"What does `Buffers: shared hit=17 read=4` mean?"** 21 pages of 8 kB touched: 17 found
in Postgres's shared buffers and 4 requested from the OS (which may still have had them
in its page cache). Buffer counts are more stable than timings, so compare them before
and after a change.

## What's next

Level 22 goes back to CTEs, the part level 08 only touched: recursive queries on real
graphs with cycles, the `CYCLE` and `SEARCH` clauses, and when Postgres inlines a CTE
versus materializing it, which you can now see in a plan.
