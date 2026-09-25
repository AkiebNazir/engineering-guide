# 022 — Design a Distributed Unique ID Generator

Design a service (or library) that hands out unique 64-bit IDs to thousands of application servers across several datacenters, for use as primary keys for posts, messages, and orders.

## Functional requirements

- Every ID is unique across all datacenters, forever.
- IDs fit in 64 bits so they can be stored as a `BIGINT` and used as database keys.
- IDs are roughly sortable by creation time (an ID created a second later is larger).
- Any application server can obtain IDs, including during a network partition between datacenters.
- IDs should not reveal exact business volumes to external users (nice to have).

## Constraints to assume

- 10,000 application servers in 5 datacenters.
- Peak demand of 1 million IDs per second system-wide, bursts of 10,000 per second on a single server.
- ID generation must add less than 1 ms at p99 to the calling request.
- The system must keep issuing IDs when any single machine or datacenter fails.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope throughput per generator and bit-budget arithmetic.
3. <abbr title="Application Programming Interface">API</abbr> contract (service call vs embedded library) and how callers obtain IDs.
4. Baseline design and how uniqueness is guaranteed without a central counter.
5. Handling clock drift, clocks moving backwards, and worker-ID assignment.
6. Failure, operability, and observability plan.
7. One explicit trade-off you would revisit if IDs had to be strictly monotonic globally.

Do not open the solution until you have made and explained your own design.
