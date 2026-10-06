# 039 — Design a Social Graph Service

Design the service that stores a social network's people, pages and posts and the relationships between them, and answers the small graph questions every page render asks: who are your friends, how many followers, may this viewer see that post.

## Functional requirements

- Typed objects (user, page, post) and typed, directed associations (friend, follow, like, blocked) with a timestamp and optional payload.
- Add and delete an association; fetch the newest N of a list with a stable cursor; look up specific edges; return a count for any list.
- Friendship and follow are visible from both endpoints.
- A block or unfriend must take effect on content that is already cached or precomputed.
- Mutual friends of two users, and People You May Know candidates.
- Several regions; the user who performs a write sees it on their next read.

## Constraints to assume

- About 3 billion users, 1 billion daily active, 200 edges per user on average with a heavy tail (accounts with 10^8 followers; friend lists capped at 5,000).
- Read:write about 500:1, at least 10 million reads per second at peak across regions.
- p99 under 10 ms for association reads served from cache in a region; p99.9 under 25 ms including database reads.
- At least three regions, each with a full copy. Other users may see a write within seconds; blocks must be enforced everywhere within 5 seconds.
- A viral account can gain 5,000 followers per second; one celebrity profile can draw 200,000 reads per second.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, edge and storage counts, cache RAM, and fleet sizes.
3. API contracts and core data model (objects, associations, counts, shard mapping).
4. Baseline architecture and read/write flows, including the inverse edge.
5. Sharding and hot nodes, the cache tiers and invalidation flow, read-your-writes and cross-region consistency, counters, and two-hop queries.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
