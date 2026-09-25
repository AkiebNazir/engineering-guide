# Replication and High Availability

**Already covered elsewhere:** `SystemDesign/building_blocks/10_distributed_systems_theory.md`
covers replication's role in <abbr title="CAP Theorem - A concept stating that a distributed data store can only simultaneously provide two out of three guarantees: Consistency, Availability, and Partition tolerance.">CAP</abbr>/consistency tradeoffs in the abstract, and
`CSFundamentals/03_databases_deep_dive.md` §3 covers <abbr title="Write-Ahead Logging. A family of techniques for providing atomicity and durability in database systems by writing modifications to a log before they are applied.">WAL</abbr> internals. This level is the
Postgres-specific mechanics — what actually ships between two instances, what
"replication lag" measures, and what a real failover involves — proven with a live
replica, not just diagrammed.

## The mental model

Every write to Postgres is first recorded in the **write-ahead log (<abbr title="Write-Ahead Logging. A family of techniques for providing atomicity and durability in database systems by writing modifications to a log before they are applied.">WAL</abbr>)** — an
append-only record of every change, written and fsynced *before* the change is
considered durable (this is the same <abbr title="Write-Ahead Logging. A family of techniques for providing atomicity and durability in database systems by writing modifications to a log before they are applied.">WAL</abbr> levels 09 and 15 already rely on for crash
recovery). Replication is simply: **ship that same <abbr title="Write-Ahead Logging. A family of techniques for providing atomicity and durability in database systems by writing modifications to a log before they are applied.">WAL</abbr> to a second server, and have it
replay the same changes.** Two flavors matter, and interviewers routinely test whether
you know which is which:

| | **Physical (streaming) replication** | **Logical replication** |
|---|---|---|
| Ships | Raw <abbr title="Write-Ahead Logging. A family of techniques for providing atomicity and durability in database systems by writing modifications to a log before they are applied.">WAL</abbr> bytes — page-level changes | Decoded row-level changes (`INSERT`/`UPDATE`/`DELETE`) |
| Replica is | An exact byte-for-byte copy of the whole cluster, read-only | A separate database that can have a different schema, extra indexes, or a subset of tables |
| Granularity | Whole database cluster | Per-table, via `PUBLICATION`/`SUBSCRIPTION` |
| Typical use | High availability, failover, read replicas | Selective sync, zero-downtime major-version upgrades, feeding a different system (e.g. a reporting warehouse) |
| Postgres feature | `primary_conninfo`, <abbr title="Write-Ahead Logging. A family of techniques for providing atomicity and durability in database systems by writing modifications to a log before they are applied.">WAL</abbr> streaming, `pg_basebackup` | `CREATE PUBLICATION` / `CREATE SUBSCRIPTION` (built in since Postgres 10) |

Both are **asynchronous by default** in Postgres: the primary commits and returns to
the client *before* confirming the replica received the change. That default is a
real, tunable tradeoff, covered below.

## Demo: real logical replication, set up and measured

This demo uses logical replication because it's runnable entirely inside the existing
lab Postgres instance — a second database, not a second container — while still
exercising the real <abbr title="Write-Ahead Logging. A family of techniques for providing atomicity and durability in database systems by writing modifications to a log before they are applied.">WAL</abbr>-shipping, replication-slot, and lag-measurement mechanics that
apply identically to physical streaming replication between two servers.

Logical replication requires `wal_level = logical` (the default `replica` isn't
enough — this lab's `docker-compose.databases.yml` Postgres is already configured for
it):

```sql
SHOW wal_level;   -- must read 'logical' for what follows
```

**1. On the "primary" (`dsa` database): expose a table via a publication.**

```sql
CREATE TABLE repl_demo (id INT PRIMARY KEY, note TEXT NOT NULL);
INSERT INTO repl_demo VALUES (1, 'created before publication');
CREATE PUBLICATION pub_repl_demo FOR TABLE repl_demo;
```

**2. Create the replication slot separately, before the subscription.** On a single
instance, creating the slot *as part of* `CREATE SUBSCRIPTION` can self-deadlock — the
slot's snapshot has to wait for "all transactions older than this one" to finish, and
the `CREATE SUBSCRIPTION` statement's own still-open transaction counts as one of them.
Creating the slot as its own, separate, already-committed statement avoids that:

```sql
SELECT pg_create_logical_replication_slot('sub_repl_demo', 'pgoutput');
```

**3. On the "replica" (a separate `dsa_replica` database, same instance): subscribe.**

```sql
CREATE TABLE repl_demo (id INT PRIMARY KEY, note TEXT NOT NULL);  -- schema not auto-created
CREATE SUBSCRIPTION sub_repl_demo
  CONNECTION 'host=localhost port=5432 dbname=dsa user=dsa password=dsa'
  PUBLICATION pub_repl_demo
  WITH (create_slot = false, slot_name = 'sub_repl_demo', copy_data = true);
```

Real output — the initial sync copied the pre-existing row:

```text
 id |            note
----+----------------------------
  1 | created before publication
```

**4. Measure real replication lag.** Insert on the primary, poll the replica until the
new row appears:

```sql
INSERT INTO repl_demo VALUES (2, 'inserted on publisher, watch it arrive on the subscriber');
```

Real measured result, polling the replica in a loop from the moment the `INSERT`
returned:

```text
row visible on subscriber after 0.0260s
```

**26 milliseconds** from commit on the primary to visible on the replica — this is
what "asynchronous replication" concretely means: the `INSERT` on the primary returned
immediately, and the replica caught up a few dozen milliseconds later. `pg_replication_slots`
also exposes exactly how far behind a replica is, in bytes of un-replayed <abbr title="Write-Ahead Logging. A family of techniques for providing atomicity and durability in database systems by writing modifications to a log before they are applied.">WAL</abbr>:

```sql
SELECT slot_name, active,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn)) AS lag
FROM pg_replication_slots WHERE slot_name = 'sub_repl_demo';
```

```text
   slot_name   | active | lag
---------------+--------+--------
 sub_repl_demo | t      | 0 bytes
```

`pg_replication_slots` and `pg_stat_replication` (the primary-side equivalent, showing
`write_lag`/`flush_lag`/`replay_lag`) are the two views a real on-call engineer checks
first when asked "is the replica keeping up" — this level's lag number came from the
same mechanism a production dashboard would use.

**The same setup and measurement, in Go (native `pgxpool`)** — one pool for the
publisher, one for the `postgres` admin connection (to create/drop the `dsa_replica_go`
database), one for the subscriber, since each is logically a different server
connection even though all three databases live on this one instance:

```go
primary, _ := pgxpool.New(ctx, "postgresql://dsa:dsa@localhost:5544/dsa")
admin, _   := pgxpool.New(ctx, "postgresql://dsa:dsa@localhost:5544/postgres")

primary.Exec(ctx, `CREATE TABLE repl_demo (id INT PRIMARY KEY, note TEXT NOT NULL)`)
primary.Exec(ctx, `INSERT INTO repl_demo VALUES (1, 'created before publication')`)
primary.Exec(ctx, `CREATE PUBLICATION pub_repl_demo_go FOR TABLE repl_demo`)
primary.Exec(ctx, `SELECT pg_create_logical_replication_slot('sub_repl_demo_go', 'pgoutput')`)

admin.Exec(ctx, `CREATE DATABASE dsa_replica_go OWNER dsa`)
replica, _ := pgxpool.New(ctx, "postgresql://dsa:dsa@localhost:5544/dsa_replica_go")
replica.Exec(ctx, `CREATE TABLE repl_demo (id INT PRIMARY KEY, note TEXT NOT NULL)`)
replica.Exec(ctx, `
    CREATE SUBSCRIPTION sub_repl_demo_go
      CONNECTION 'host=localhost port=5432 dbname=dsa user=dsa password=dsa'
      PUBLICATION pub_repl_demo_go
      WITH (create_slot = false, slot_name = 'sub_repl_demo_go', copy_data = true)`)

// Measure: insert on the primary, start a Go-side timer, poll the replica
// in a tight loop until the row is visible.
start := time.Now()
primary.Exec(ctx, `INSERT INTO repl_demo VALUES (2, 'inserted on publisher, watch it arrive on the subscriber')`)
for {
    var count int
    replica.QueryRow(ctx, `SELECT count(*) FROM repl_demo WHERE id = 2`).Scan(&count)
    if count == 1 {
        fmt.Printf("row visible on subscriber after %.4fs\n", time.Since(start).Seconds())
        break
    }
}
```

Real output from this exact Go program, same lab instance:

```text
initial sync, row 1 on replica: created before publication
row visible on subscriber after 0.0025s
slot=sub_repl_demo_go active=true lag=232 bytes
```

**2.5ms here, vs. ~26ms measured earlier in this same level with a Python polling
loop.** Both numbers are real, and the difference is not "Go is 10x faster at
replication" — it's polling-loop granularity and process scheduling noise on a single
lightly-loaded machine, not a property of logical replication itself. The fact worth
keeping from *either* run is the same one: asynchronous replication has a real,
non-zero, sub-second lag window, not "Go's number" or "Python's number" specifically —
re-run either version yourself and expect single-digit-to-tens-of-milliseconds, not an
exact figure.

## Synchronous vs. asynchronous replication — a durability/latency tradeoff, not free

The demo above is asynchronous, Postgres's default. Setting `synchronous_standby_names`
on the primary makes a commit **wait** until at least one named replica confirms it
received (or, depending on `synchronous_commit`, flushed/replayed) the <abbr title="Write-Ahead Logging. A family of techniques for providing atomicity and durability in database systems by writing modifications to a log before they are applied.">WAL</abbr> — trading
commit latency (every write now pays a network round trip to the replica) for a
stronger guarantee: a promoted replica can never be missing a transaction the client
was told succeeded. This is the same durability-vs-latency axis `SQL/09` explores for
isolation, one level up: async replication can lose the last few commits' worth of
changes if the primary dies before they ship (a "durability gap" measured in the lag
number above); synchronous replication closes that gap at the cost of every write now
depending on the replica being reachable and healthy.

## Failover, honestly

Postgres does not fail over automatically on its own — a promoted-on-crash primary is
an *operational* capability, built from these pieces:

1. **Detection.** Something (a health check, a tool like **Patroni** or **repmgr**, or
   a cloud provider's managed layer) has to notice the primary is unreachable — and
   distinguish "primary is actually down" from "network partition between the checker
   and the primary" (naively promoting a replica during a partition, while the old
   primary is still alive and accepting writes, produces two primaries — "split
   brain" — each accepting conflicting writes).
2. **Promotion.** `pg_ctl promote` (or the equivalent in whatever orchestration layer
   is in front of it) turns a **read replica** into a writable primary. This is why
   physical streaming replicas are read-only until promoted — a replica applying <abbr title="Write-Ahead Logging. A family of techniques for providing atomicity and durability in database systems by writing modifications to a log before they are applied.">WAL</abbr>
   from a primary cannot simultaneously accept independent writes of its own.
3. **Reconfiguration.** Every client and every other replica needs to learn the new
   primary's address — a connection-pooler/proxy layer (`pgbouncer`, a virtual <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr>, <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr>,
   or the orchestration tool itself) usually owns this so application code doesn't
   need to know a failover happened.
4. **The old primary, if it comes back.** It doesn't automatically rejoin as a replica
   of the new primary — it may have <abbr title="Write-Ahead Logging. A family of techniques for providing atomicity and durability in database systems by writing modifications to a log before they are applied.">WAL</abbr> the new primary never saw (if replication was
   asynchronous and it died mid-lag), so it has to be explicitly resynced or rebuilt,
   never blindly restarted as a second writer.

The interview-relevant honesty here: **"Postgres has replication" and "Postgres has
automatic failover" are different claims** — the first is a database feature, the
second is a piece of operational tooling (Patroni, repmgr, a managed cloud service)
built on top of it. Saying "just add a replica" without naming what detects failure and
performs promotion is an incomplete answer.

<div class="lab" data-viz="flow-pg-ha"></div>

## Read replicas for read scaling — and the staleness they buy you

The same mechanism used for HA also scales reads: point read-only traffic at one or
more replicas, keep writes on the primary. The cost is the same lag measured above —
a client that writes, then immediately reads from a replica, can see stale data for
however many milliseconds replication lag currently is ("read your own writes"
consistency is *not* automatic across primary/replica the way it is on a single
connection to the primary). Real systems solve this by routing a user's own
post-write reads back to the primary for a short window, or by tracking a
causality token (the <abbr title="Write-Ahead Logging. A family of techniques for providing atomicity and durability in database systems by writing modifications to a log before they are applied.">WAL</abbr> LSN their write produced) and waiting for a replica to reach
it before serving their read from it.

## Common mistakes

- **Confusing physical and logical replication** — a physical replica cannot have a
  different schema or extra indexes from the primary (it's a byte-for-byte copy); a
  logical replica can, because it replays decoded row changes, not <abbr title="Write-Ahead Logging. A family of techniques for providing atomicity and durability in database systems by writing modifications to a log before they are applied.">WAL</abbr> pages.
- **Assuming Postgres fails over on its own.** It doesn't — see "Failover, honestly"
  above. A bare `docker-compose` with a primary and a replica has no automatic
  promotion.
- **Reading your own write from a replica and expecting to see it immediately.**
  Async replication's whole cost is exactly this staleness window — the demo measured
  it at ~26ms here, but it grows under load or network trouble.
- **Promoting a replica during a network partition without confirming the old primary
  is actually down** — the split-brain scenario in step 1 above.

## What's next

Level 18 covers sharding — what happens when one primary, however many replicas it has
for reads, can no longer take all the *writes* a workload needs, and how relational
databases (imperfectly) split write load across multiple machines.
