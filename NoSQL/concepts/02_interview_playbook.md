# Interview Playbook: NoSQL

Same purpose as `SQL/19_interview_playbook.md` — not new material, the ladder's
content re-organized as the concrete questions an interviewer asks, with a precise
answer and a pointer back to the level that proves it. Use it as a pre-interview
refresher.

## "What should every engineer be able to do cold, with no notes"

1. Explain **embedding vs. referencing** in MongoDB and give a real reason to choose
   each (`mongodb/04`).
2. State what **write concern and read concern** actually control, and connect them to
   the CAP/BASE tradeoff (`mongodb/10`, `concepts/01`).
3. Explain **why Redis is single-threaded** and why that's a feature, not a limitation,
   for its use case (`redis/00`).
4. Name at least two **cache invalidation strategies** and the failure mode each one is
   vulnerable to — cache-aside staleness, write-through latency, a stampede on a hot
   key expiring (`redis/05`).
5. Explain the **`SET NX PX`** distributed lock pattern and its real limitation
   (`redis/08`) — "I know Redlock is debated" is a stronger answer than presenting
   distributed locking as solved.
6. Design a **single-table access pattern** for a DynamoDB-style store given a short
   list of required queries (`concepts/00`).
7. Answer **"SQL or NoSQL for this system"** by naming the actual access pattern, not
   the brand (`concepts/01`).

## Data modeling questions, worked

**"Model a blog: posts and comments. MongoDB or a wide-column store — how?"**

- *MongoDB:* embed comments inside the post document if comments are always read
  together with the post and rarely exceed a few hundred per post (stay well under the
  16MB document limit measured in `mongodb/04`); reference them as a separate
  collection if comments are queried independently (e.g., "show me all of a user's
  comments across posts") or can grow unbounded.
- *DynamoDB-style:* `PK = POST#<id>`, `SK = COMMENT#<timestamp>` alongside
  `PK = POST#<id>`, `SK = METADATA` for the post itself — one partition query returns
  the post and all its comments in timestamp order, the single-table pattern from
  `concepts/00`.

**"Design a leaderboard for 10 million players, top-100 and a player's own rank."**
Redis sorted set (`redis/04`): `ZADD leaderboard <score> <player_id>` for updates,
`ZREVRANGE leaderboard 0 99` for the top 100, `ZREVRANK leaderboard <player_id>` for
any player's rank — all O(log N), which a relational `ORDER BY score DESC LIMIT 100`
plus a separate `COUNT(*) WHERE score >` query for rank cannot match at this scale
without building the equivalent of a sorted-set structure yourself. In Go
(`go-redis/v9`, real output from the live lab instance, `redis/04`'s dataset):

```go
r.ZAdd(ctx, "leaderboard",
    redis.Z{Score: 2200, Member: "bob"}, redis.Z{Score: 1800, Member: "carol"})
top, _ := r.ZRevRangeWithScores(ctx, "leaderboard", 0, 99).Result()
rank, _ := r.ZRevRank(ctx, "leaderboard", "alice").Result()
```
```text
ZREVRANK alice (her leaderboard position) -> 3
```

**"Rate-limit an <abbr title="Application Programming Interface">API</abbr> to 100 requests/minute per user, across multiple app servers."**
Shared Redis, not an in-process counter (`redis/09`) — the counter has to live
somewhere every app server instance can see it, or a user hitting different servers
bypasses the limit entirely. Name the sliding-window approach specifically over a fixed
window, since fixed windows allow a burst of 2x the limit right at the window boundary.
Real proof this is actually shared, not per-process, from `redis/09`: two independent
Go `*redis.Client`s standing in for two app servers, both hitting the same
Lua-scripted sliding-window key, produced `server A: true,true,true` then
`server B: true,true,false` — server B's *own* third request only, denied because the
*combined* total across both simulated servers hit the shared limit of 5, not because
either server individually saw too many requests.

**"Two app servers both try to process the same job — prevent double processing."**
`SET lock_key <owner_id> NX PX <ttl>` (`redis/08`): the lock is acquired only if the
key doesn't already exist, with a TTL so a crashed holder doesn't lock it forever.
Release with a compare-and-delete script (check the owner before deleting), not a bare
`DEL`, so one process can't release a lock it doesn't hold after its TTL already
expired and someone else acquired it. In Go: `r.SetNX(ctx, lockKey, token, ttl)` for
acquisition (`redis/08`'s real run: `client A acquired -> true`,
`client B tries to acquire same lock while held -> false`), and the identical
compare-and-delete Lua script via `r.Eval` for release — the script body is
language-agnostic, since it runs inside Redis regardless of which client sent it.

## Conceptual questions, answered precisely

**"Why would you ever choose eventual consistency?"** Because strong consistency has a
real, measured cost — every one of the settings in `concepts/01`'s table trades latency
or availability for it. A social media like-counter or a product view count can be
briefly stale with zero real consequence; a bank balance cannot. The skill being tested
is naming *which* operations in a system can tolerate staleness and which can't, not
picking one answer for the whole system.

**"What happens if MongoDB's primary goes down?"** The replica set holds an election
among the remaining members (`mongodb/10`) and promotes a new primary automatically —
this is MongoDB's built-in equivalent of the failover *tooling* `SQL/17` points out
Postgres needs bolted on separately (Patroni/repmgr); citing this contrast directly is
a strong, specific answer.

**"Why can't Redis be a primary database for everything?"** It's in-memory by design —
durability is a deliberate afterthought (RDB snapshots / AOF, `redis/10`), both slower
and less durable than a WAL-backed disk-first database by default. It excels at being
fast and disposable-if-needed (a cache, a session store, a rate limiter) precisely
because it isn't trying to be the system of record.

**"How would you migrate a schema in MongoDB without downtime?"** The same
expand/contract principle `SoftwareDesign/09_data_design_and_schema_evolution.md`
teaches for relational schemas applies directly: write code that tolerates both the
old and new document shape simultaneously, backfill existing documents in the
background, then remove the old-shape handling once the backfill is confirmed
complete — schema validation (`mongodb/08`) can be introduced gradually the same way,
starting in `warn` mode before becoming enforced.

**"What's the actual difference between a cache-aside and a write-through cache?"**
Cache-aside: the application checks the cache, and on a miss, reads the database and
populates the cache itself — the cache can go momentarily stale relative to the
database, and a cold cache means every key's first read is slow. Write-through: every
write goes to the cache and the database together, synchronously — reads are always
warm, at the cost of every write now paying the cache's latency too, and needing a
plan for what happens if the cache write succeeds but the database write doesn't (or
vice versa).

## What's next

This closes the SQL and NoSQL modules together. Both point back to
`SystemDesign/building_blocks/` and `CSFundamentals/03_databases_deep_dive.md` for the
storage-engine and distributed-systems theory underlying everything demonstrated
hands-on across both ladders.
