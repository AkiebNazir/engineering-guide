# 040 — Design a Distributed Lock and Coordination Service

Design a lock and coordination service in the style of Chubby, ZooKeeper or etcd. Thousands of long-running processes use it to elect leaders, hold locks, publish small config and find each other, and a wrong answer (two leaders at once) is worse than no answer.

## Functional requirements

- Named locks (exclusive and shared), released automatically when the holder dies.
- Leader election for service groups, and a way to find the current leader.
- A small hierarchical namespace of files with compare-and-set updates.
- Watches on files, locks and membership, without polling.
- Sessions with liveness detection, so a crashed or partitioned client loses its locks.
- Protection for resources behind a lock when a client wrongly believes it still holds it.

## Constraints to assume

- One cell is 5 replicas across 3 zones; it must survive any 2 replica failures and one full zone loss with no lost acknowledged write.
- 30,000 client processes per cell, each holding one session. Rolling restarts touch the whole fleet in 30 minutes.
- 200,000 nodes (files, lock and membership entries), 2 KB on average, 256 KB maximum. About 100,000 read calls per second from application code, but only 200 writes per second at peak.
- Uncontended lock acquisition p99 under 50 ms. After a lock holder crashes, the lock is available to others within about 15 seconds. Watch notifications reach all watchers of a node within 1 second at p99.
- A cell master failure must not cost clients their sessions and locks if it is repaired within about a minute. Cell availability target 99.99%.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>, storage, and bandwidth estimates.
3. <abbr title="Application Programming Interface">API</abbr> contracts and core data model.
4. Baseline architecture and read/write flows.
5. Sessions and leases, the paused-holder hazard and fencing tokens, client caching and watch ordering, and behaviour when the cell master fails.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
