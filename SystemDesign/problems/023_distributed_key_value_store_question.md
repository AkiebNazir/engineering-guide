# 023 — Design a Distributed Key-Value Store

Design a highly available, horizontally scalable key-value store in the spirit of Dynamo or Cassandra: `put(key, value)` and `get(key)`, running on hundreds of commodity servers.

## Functional requirements

- `put(key, value)`, `get(key)`, and `delete(key)`; values up to 1 MB.
- Configurable consistency per request (e.g. fast and eventually consistent, or read-your-writes).
- Adding or removing servers without downtime and with minimal data movement.
- Automatic recovery when servers fail or return after an outage.

## Constraints to assume

- 10 TB of data growing to 100 TB; average value 10 KB, keys under 256 bytes.
- 200,000 reads/second and 50,000 writes/second at peak.
- p99 latency under 10 ms for single-key operations within a region.
- Tolerate the loss of any two servers without losing acknowledged writes; stay writable during a network partition.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope storage, node count, and per-node load.
3. <abbr title="Application Programming Interface">API</abbr> contract, including consistency parameters and version/conflict semantics.
4. Baseline architecture: request coordination, partitioning, and replication.
5. Consistency: quorums, conflict detection and resolution, and read repair.
6. Membership, failure detection, hinted handoff, anti-entropy, and the storage engine.
7. One explicit trade-off you would revisit if the product needed strong consistency.

Do not open the solution until you have made and explained your own design.
