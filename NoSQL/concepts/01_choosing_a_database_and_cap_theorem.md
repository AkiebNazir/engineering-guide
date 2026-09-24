# Choosing a Database, and CAP Theorem Applied

**Already covered elsewhere:** `SystemDesign/building_blocks/10_distributed_systems_theory.md`
states CAP precisely — read that first if the term itself is shaky. It also makes the
point this level builds on directly: **CAP is not a static per-product label**
("relational = CA, NoSQL = AP" is explicitly called out there as a misconception) —
it's a per-operation choice a system's *configuration* makes during a partition. This
level's job is narrower and more practical: given the four real systems this repo's
`SQL/` and `NoSQL/` modules actually run (Postgres, MongoDB, Redis, plus Cassandra/
DynamoDB from `concepts/00`), which concrete, nameable setting expresses that choice in
each one, and how an engineer actually decides which database to reach for.

## The decision framework, in the order a working engineer actually applies it

**1. Does the data have relationships that need enforcing, and does the workload need
multi-row transactions?** If yes — a relational database (`SQL/`) is the default
answer, not because it's older, but because foreign keys, joins, and multi-statement
ACID transactions are things it does for free that every other option makes you build
yourself. This is a "yes by default, no requires a reason" starting point, mirroring
`SQL/16`'s "normalize by default" stance one level up.

**2. Is the data's shape genuinely variable or naturally nested, and does the access
pattern mostly read/write whole documents?** — a document store (MongoDB,
`NoSQL/mongodb/`). The honest reason to reach for this is schema flexibility during
fast iteration or genuinely polymorphic data (see `NoSQL/mongodb/04_embedding_vs_referencing.md`),
not "NoSQL is faster" — a well-indexed Postgres table with a `JSONB` column often
outperforms a naively-modeled Mongo collection.

**3. Is there a hot, latency-critical path that needs sub-millisecond responses, or a
need for data structures (counters, sorted sets, pub/sub) that don't map cleanly onto
rows?** — a key-value/cache store (Redis, `NoSQL/redis/`). This is almost always
layered *in front of* one of the above, not a replacement for it — see
`NoSQL/redis/05_caching_patterns.md`.

**4. Does a single machine's write throughput or storage capacity genuinely limit the
system, after indexing/partitioning/replicas have been tried?** — this is when
sharding (`SQL/18`) or a wide-column store designed for it from the ground up
(`NoSQL/concepts/00`) earns its complexity. Reaching for this *before* the first three
steps have been exhausted is the single most common "sounds impressive, isn't
justified" answer in a system design interview.

**The wrong question to lead with:** "SQL or NoSQL?" as a binary. The right question is
"what does this specific access pattern need?" — real systems mix several of the above
for different parts of the same product (Postgres for the ledger, Redis for sessions
and rate limiting, Mongo or a search index for a flexible catalog), and naming that mix
explicitly is a stronger answer than picking one database for the whole system.

## The same consistency knob, expressed differently by each system

CAP's per-operation tradeoff — wait for agreement (consistent, possibly slower or
unavailable during a partition) vs. answer immediately (available, possibly stale) —
is not abstract in any of these systems. Each one exposes it as a real, named setting:

| System | The knob | What "consistent" costs | What "available/fast" costs |
|---|---|---|---|
| **Postgres** | `synchronous_standby_names` / `synchronous_commit` (`SQL/17`) | Every commit waits for a replica's confirmation — added latency, and the primary blocks if the replica is unreachable | Async (default): commit returns immediately; a promoted replica can be missing the last few transactions |
| **MongoDB** | Write concern (`w: majority` vs `w: 1`) and read concern, `NoSQL/mongodb/10_replication_and_write_read_concern.md` | `w: majority` waits for most replica-set members to acknowledge | `w: 1` acknowledges after the primary alone writes — faster, loses the write if the primary fails before replicating it |
| **Cassandra** | Per-query consistency level, `R + W > N` (`concepts/00`) | `QUORUM` reads/writes wait for a majority of replicas | `ONE` returns after a single replica responds — fastest, may read stale data |
| **DynamoDB** | Eventually- vs. strongly-consistent reads (`concepts/00`) | Strongly consistent reads cost more, aren't available cross-region | Eventually consistent (default) may briefly return stale data after a write |

The pattern across all four: **nobody gets consistency and low latency for free** — every
system that lets you tune this is handing you the exact same tradeoff CAP describes,
just per-request instead of as a single global mode. Naming the specific setting for
whichever database is under discussion is a stronger interview answer than reciting
"CAP theorem" as a concept.

## ACID vs. BASE, precisely

- **ACID** (Atomicity, Consistency, Isolation, Durability — `SQL/09`): the relational
  default. Correctness is enforced by the database, synchronously, before a write is
  acknowledged.
- **BASE** (**B**asically **A**vailable, **S**oft state, **E**ventual consistency): the
  informal name for the tradeoff most NoSQL systems default to — the system stays
  available and accepts writes even when it can't immediately reconcile every replica,
  and consistency arrives *eventually* rather than being guaranteed at commit time.

BASE is not "no guarantees" — MongoDB and Cassandra both offer strongly consistent
configurations (see the table above); BASE describes the *default*, optimized-for-
availability posture that document and wide-column stores ship with, which ACID
systems intentionally do not.

## Common mistakes

- **Treating CAP as a label on the product** rather than a per-operation, per-config
  decision — the exact misconception `SystemDesign/building_blocks/10` already calls
  out, restated here because it's the single most common way this topic goes wrong in
  an interview answer.
- **Picking a database by reputation** ("Mongo is web-scale," "Postgres can't scale")
  instead of by the four-step framework above.
- **Reciting "eventual consistency" without being able to name the specific setting**
  (write concern, consistency level, sync/async replication) that controls it in
  whichever system is actually being discussed.
- **Assuming a document/key-value store can't do transactions.** MongoDB has
  multi-document ACID transactions (`NoSQL/mongodb/09`); the honest tradeoff is that
  they're more expensive there than in a system designed around them from the start,
  not that they're impossible.

## What's next

`concepts/02_interview_playbook.md` closes the module with the concrete NoSQL
questions this ladder gets asked as, worked the same way `SQL/19` did for the
relational side.
