# 018 — Design a Distributed Cache

Design a distributed, in-memory caching system (client library plus a ring of cache nodes) sitting in front of a slower source of truth.

## Functional requirements

- Clients get/set/delete keys with a per-key TTL, with reads falling back to the source of truth on a miss.
- Keys are distributed across a ring of cache nodes so load is spread roughly evenly.
- The cache evicts entries under memory pressure using a defined policy.
- A single very hot key must not overload the node that owns it.
- Nodes can be added or removed with minimal cache-wide disruption (no full re-shuffle/stampede).
- Optionally, data is replicated so a single node failure doesn't cause a full cache-wide miss storm.

## Constraints to assume

- 2 million requests/second across the cluster at peak.
- 500 cache nodes, 1 TB total cache memory.
- Get/set p99 under 5 ms.
- Node replacement must not move more than ~1/N of keys.
- Source-of-truth fallback must not exceed 5% of traffic during steady state.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. <abbr title="Application Programming Interface">API</abbr> contracts and core data model.
4. Baseline architecture and read/write flows.
5. Consistent-hashing and hot-key mitigation strategy for node changes and skewed access.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
