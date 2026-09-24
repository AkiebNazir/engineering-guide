# 007 — Design a News Feed

Design a home feed that shows users posts from the accounts they follow, ranked and reasonably fresh.

## Functional requirements

- A user follows/unfollows other accounts.
- A user's home feed shows posts from followed accounts, ranked (not strictly chronological).
- New posts appear in followers' feeds within a short freshness window.
- A deleted post disappears from all feeds promptly.
- Celebrity accounts with tens of millions of followers are supported without degrading write latency.
- A user can page through their feed (pagination/infinite scroll).

## Constraints to assume

- 50 million followers on the largest accounts.
- New posts should be visible in feeds within 30 seconds.
- Feed read latency under 200 ms p99.
- Hundreds of millions of posts/day system-wide.
- Deletions must be reflected in feeds within a minute.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. API contracts and core data model.
4. Baseline architecture and read/write flows.
5. Fan-out-on-write vs fan-out-on-read strategy, especially for celebrity accounts.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
