# Distributed Systems Theory: CAP, Consistency, Time, and Ordering

A network call is not a function call. It can be delayed, duplicated, reordered, or appear to fail after the remote side actually completed the work. Everything in this file is about designing correctly around that fact, not about memorizing slogans for an interview whiteboard.

## The three outcomes of a remote call

Every dependency call your service makes ends in exactly one of these, and each demands a different response:

| What the caller sees | What may really have happened | Safe response |
|---|---|---|
| Success response | Remote side completed work. | Use the result. |
| Explicit rejection | Remote side did not accept the work. | Correct the request, or retry only if the error is transient. |
| Timeout/connection loss | Work may have happened, not happened, or still be running. | Query by idempotency key/status, or retry the same logical intent safely — never assume either outcome. |

The third row is the one people get wrong. A timeout is not "it failed" — it is "I don't know." Treating a timeout as failure and blindly retrying a non-idempotent write (charge a card, send an email, place an order) is how systems double-charge and double-send. The only safe fix is to make the operation idempotent (a stable idempotency key, a conditional write) or to reconcile by querying actual state before acting again.

> ⚠️ "We retry on timeout" is an incomplete answer in an interview — and in production. The complete answer names *what* makes the retry safe: an idempotency key, a conditional write, or a reconciliation read. Say the mechanism, not just the intent.

## CAP theorem, stated precisely

CAP applies to a **distributed system that replicates data**, during a **network partition** (replicas cannot communicate reliably). In that moment, a system cannot simultaneously guarantee:

- **Consistency (C):** commonly linearizability — every successful read observes the latest successful write, in one real-time-respecting order.
- **Availability (A):** every request to a non-failed replica gets a non-error response.
- **Partition tolerance (P):** the system keeps operating despite the communication break.

```arch
%% caption: The three pairwise trade-offs CAP actually names
route straight
node P "Partition tolerance" at 1,0 shape=circle color=purple w=100
node cp "CP" at 0.5,1 shape=box color=blue sub="reject or wait when replicas disagree"
node ap "AP" at 1.5,1 shape=box color=green sub="answer anyway, maybe stale"
node C "Consistency" at 0,2 shape=circle color=blue w=100
node A "Availability" at 2,2 shape=circle color=green w=100
node ca "CA" at 1,2 shape=box color=slate sub="only real without partitions at all"
C -- cp
cp -- P
A -- ap
ap -- P
C .. ca
ca .. A
```

Partitions are not optional to defend against — they happen. So the real decision CAP forces is per-operation, during a partition:

```arch
%% caption: The per-operation decision CAP actually forces, during a partition
node start "A request arrives" at 1,0 shape=pill sub="during a partition"
node ask "Need the latest correct answer now?" at 1,1 shape=diamond color=amber
node c "Wait, or fail" at 0,2 shape=card color=blue icon=lock sub="when replicas disagree: favor Consistency over Availability"
node a "Return a possibly stale answer" at 2,2 shape=card color=green icon=check sub="or conflicting: favor Availability over Consistency"
start -> ask
ask -> c : "yes"
ask -> a : "no, staleness is okay"
```

### What CAP does NOT mean

- It does not mean "pick any two, always." Partition tolerance isn't optional for a real multi-node deployment — you are really choosing C or A *for the duration of a partition*, not architecting the system in general.
- It does not mean relational databases are "CA" and NoSQL databases are "AP." A single-node database isn't partition tolerant because it has no replicas at all — CAP doesn't even apply to it.
- It does not excuse a vague "eventually consistent" answer in an interview. State the actual freshness bound and the conflict rule.
- A single system can make different C/A choices for different operations (payments strongly consistent, search results eventually consistent) — CAP is not one global label for a product.

## PACELC: the normal-case complement

CAP only describes behavior during a partition, which is rare. PACELC covers the rest of the time, when the network is healthy:

- **If P**artitioned: choose **A**vailability or **C**onsistency (this is CAP).
- **Else (E)**, in normal operation: choose **L**atency or stronger **C**onsistency/coordination.

A globally coordinated write (wait for quorum across regions) is strongly consistent but pays cross-region round-trip latency on every write, partition or not. An asynchronous local replica is fast but stale, partition or not. This is the trade-off you actually live with day to day — CAP only fires during the rare partition event. State it as a product decision: "payments use strongly coordinated ledger writes (accept the latency); product search reads from an asynchronous index (accept staleness up to ~1 minute)."

## Consistency models

These models are not one line from strong to weak. They live on two axes: **single-object, real-time guarantees** (what a reader may see of one key or register) and **multi-object transaction guarantees** (which whole transactions may interleave). Linearizability sits on the first, serializability on the second, and neither implies the other.

| Model | Promise | Use / example |
|---|---|---|
| Strict serializable (Spanner calls it "external consistency") | Transactions behave as if executed one at a time **and** that order respects real time: if T1 commits before T2 starts, T1 is ordered first. Both linearizable and serializable. | Google's Spanner (OSDI 2012) — the strongest, and the most coordination (TrueTime commit wait). Financial ledgers, inventory that must never oversell. |
| Linearizable | Each single object's operations appear atomic, in one real-time-respecting order. Says nothing about multi-object transactions. | Balance of one account, lease/fencing token, one seat's state, leader election. |
| Serializable | Concurrent multi-object transactions produce a result equivalent to *some* one-at-a-time order. That order need not match real time, so a transaction that started later can be ordered before an earlier one. | Correctness-heavy multi-statement transactions inside one database. |
| Causal | Effects are never observed before their causes; independent (concurrent) writes may appear in different orders to different observers. Implies the session guarantees below. | A reply never appears before the post it replies to. |
| Read-your-writes | A session sees its own acknowledged updates. | Profile edit visible to the editor immediately. |
| Monotonic reads | A session never goes backward to an older version after seeing a newer one. | Session pinned across replica switches. |
| Eventual | With no new writes and no failures, replicas converge — no bound stated, no ordering promised meanwhile. | Search index, analytics, feed fan-out. |

```arch
%% caption: A partial order, not a line: strict serializable implies both linearizable and serializable, which are incomparable, and causal implies the session guarantees.
node ss "Strict serializable" at 1,0 color=purple sub="Spanner: external consistency"
node lin "Linearizable" at 0,1 color=blue sub="one object, real-time order"
node ser "Serializable" at 2,1 color=indigo sub="multi-object transactions"
node caus "Causal" at 0,2 color=blue
node iso "Weaker isolation levels" at 2,2 color=indigo sub="repeatable read, read committed"
node ryw "Read-your-writes" at 0,3 color=teal
node mono "Monotonic reads" at 1,3 color=teal
node ev "Eventual" at 0.5,4 color=slate
ss:B -> lin:T
ss:B -> ser:T
lin -> caus
caus:B -> ryw:T
caus:B -> mono:T
ryw:B -> ev:T
mono:B -> ev:T
ser -> iso
```

Reading the diagram: an arrow means "implies" (every system giving the tail also gives the head). Linearizable and serializable have no arrow between them — Spanner gets both only by paying for cross-replica coordination and, in its design, waiting out clock uncertainty on commit. Serializable alone does not imply causal or read-your-writes, because its equivalent serial order is free to ignore real time and session order (the literature adds "strong session serializability" for exactly that reason). Causal consistency is stronger than the session guarantees: a causally consistent store gives you read-your-writes and monotonic reads (plus monotonic writes and writes-follow-reads) for free, and it is generally cited as the strongest model a replicated system can still offer while every replica stays available during a partition (Mahajan, Alvisi and Dahlin, 2011).

> 💡 Nothing here is "the right one." Strength costs coordination (latency, availability during a partition); weakness costs the caller having to tolerate surprise. The design decision is picking a point *per operation*, with a stated reason: "the ledger write is strict serializable, the profile read is read-your-writes via a sticky session, the search index is eventual with a 60-second bound." Isolation levels (read committed, snapshot isolation, serializable) are the transactional half of this map — see [11_transactions_and_concurrency.md](11_transactions_and_concurrency.md).

"Eventual consistency" alone is not a design answer. Attach a freshness bound and a conflict rule: "the search index reflects 99% of changes within 60 seconds; on conflict, deletion wins."

## Conflict resolution for multi-writer systems

If more than one location can accept a write for the same record, you must have an explicit answer for what happens when two writes race:

- **Single writer / home region:** simplest — all writes for a record go through one owner. Lower write availability for callers far from that region.
- **Last-write-wins (LWW):** pick the write with the latest timestamp and discard the other. Cheap, but **unsafe for anything that matters** — clock skew and drift mean "latest" is not reliably "actually last," and the losing write is silently and permanently gone, including partial data (e.g. two concurrent profile edits to different fields — LWW throws one edit away entirely instead of merging).
- **Version / compare-and-swap (CAS):** write succeeds only if the expected version still matches; loser gets an explicit conflict to retry or merge. Correct, but pushes conflict handling to the caller.
- **Domain merge:** use semantics that make conflicts mergeable by construction — counters add, sets union, state machines only allow legal transitions. Requires modeling the domain, not generic infrastructure.
- **CRDT (conflict-free replicated data type):** a data type with a mathematically deterministic merge rule, so any two replicas converge without coordination. Useful for specific collaborative/offline-editing state (shared documents, presence). Not a universal replacement for transactions — it only works for data shapes with well-defined merges.

Don't reach for LWW on anything with business consequences (inventory, money, permissions). It is the "it compiles" of conflict resolution — it always produces *an* answer, often the wrong one.

## Time, ordering, and unique IDs

Physical clocks drift, jump on NTP correction, and differ across machines. Never use client-supplied time as authority for money, ordering, or conflict resolution. Server time is more controlled, but it is still not a global total order across machines.

| Need | Practical mechanism | Trade-off |
|---|---|---|
| Unique identifier | UUID/random ID, database sequence, snowflake-style time+worker ID. | Random IDs hurt index locality (B-tree page splits); sequences reveal volume and centralize allocation. |
| Per-entity order | Per-key sequence number assigned at durable write. | Limits parallelism only for that one key — cheap and usually sufficient. |
| Global order | Single sequencer or consensus-backed log. | Coordination latency and an availability cost on every write. |
| Detect concurrent update | Version field / ETag / compare-and-swap. | Caller must handle the conflict response — retry or merge. |
| Temporary exclusive ownership | Lease + monotonically increasing fencing token. | Must handle lease expiry and a stale holder waking up after a pause (GC, scheduling) and still trying to act — the fencing token, checked by the resource, is what rejects it. |

Prefer per-key ordering over global ordering by default — a global sequencer is a shared bottleneck and a single point of coordination cost on every write. Only reach for it when the domain genuinely needs one total order across all entities (rare — most "ordering" requirements are actually per-conversation, per-account, or per-aggregate).

### Lamport clocks vs. vector clocks

- **Lamport clocks** attach a counter to each event such that if event A causally happened-before event B, `Lamport(A) < Lamport(B)`. They give you a **partial-to-total causal ordering**, not real wall-clock time, and they cannot tell you whether two events with unordered causality are truly concurrent or just unrelated.
- **Vector clocks** extend this with one counter per participant, so you *can* detect true concurrency (two writes neither of which happened-before the other) — this is what lets a system flag "these two versions genuinely conflict, here are both." The cost is that the vector grows with the number of participants, which doesn't scale to large, dynamic sets of writers.

Don't introduce either unless you have a concrete multi-writer conflict-detection problem (e.g. building a Dynamo-style leaderless store or a CRDT-backed collaborative editor). Most interview designs need nothing fancier than a per-key version number or a lease + fencing token.

## Related building blocks

- [11_transactions_and_concurrency.md](11_transactions_and_concurrency.md)
- [06_database_internals.md](06_database_internals.md)
- [05_databases.md](05_databases.md)
- [09_messaging_and_streaming.md](09_messaging_and_streaming.md)
- [17_decision_framework.md](17_decision_framework.md)
