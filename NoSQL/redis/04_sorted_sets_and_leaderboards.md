# Sorted Sets and Leaderboards

A **sorted set** (`ZSET`) is a set (level 03) where every member also carries a floating-
point **score**. Redis keeps the whole set ordered by score internally (implemented as a
skip list + hash table), so "give me the top N" or "where does this member rank" are
O(log n) operations, not a full scan-and-sort in your application. This is the data
structure behind every real-time leaderboard, priority queue, and "trending now" feature
built on Redis.

## Building a leaderboard

```python
r.zadd("lab04:leaderboard", {"alice": 1500, "bob": 2200, "carol": 1800,
                              "dave": 2200, "erin": 900})
```

**Ascending order** (`ZRANGE`) and **descending order** (`ZREVRANGE`) — descending is what
a leaderboard actually wants (highest score first):

```python
r.zrange("lab04:leaderboard", 0, -1, withscores=True)     # whole set, low to high
r.zrevrange("lab04:leaderboard", 0, 2, withscores=True)   # top 3, high to low
```

Run against the live instance:

```
ZRANGE all, ascending -> [('erin', 900.0), ('alice', 1500.0), ('carol', 1800.0), ('bob', 2200.0), ('dave', 2200.0)]
ZREVRANGE top 3 -> [('dave', 2200.0), ('bob', 2200.0), ('carol', 1800.0)]
```

**Go (`go-redis/v9`):** `go-redis` returns members-with-scores as `[]redis.Z`, a struct
slice, rather than a list of tuples — an idiomatic difference in shape, same data:

```go
r.ZAdd(ctx, "lab04:leaderboard",
    redis.Z{Score: 1500, Member: "alice"},
    redis.Z{Score: 2200, Member: "bob"},
    redis.Z{Score: 1800, Member: "carol"},
    redis.Z{Score: 2200, Member: "dave"},
    redis.Z{Score: 900, Member: "erin"},
)

asc, _ := r.ZRangeWithScores(ctx, "lab04:leaderboard", 0, -1).Result()
top3, _ := r.ZRevRangeWithScores(ctx, "lab04:leaderboard", 0, 2).Result()
```

Real output:

```text
ZRANGE all, ascending -> [(erin 900.0) (alice 1500.0) (carol 1800.0) (bob 2200.0) (dave 2200.0)]
ZREVRANGE top 3 -> [(dave 2200.0) (bob 2200.0) (carol 1800.0)]
```

## A player's rank

`ZRANK` gives 0-indexed position in ascending order; `ZREVRANK` gives position in
descending order — which is what you'd actually show a player ("you're #4"):

```python
r.zrank("lab04:leaderboard", "alice")      # ascending position
r.zrevrank("lab04:leaderboard", "alice")   # leaderboard position (0 = first place)
```

```
ZRANK alice (low-to-high) -> 1
ZREVRANK alice (high-to-low, i.e. her leaderboard position) -> 3
```

**Go (`go-redis/v9`):**

```go
rank, _ := r.ZRank(ctx, "lab04:leaderboard", "alice").Result()
revrank, _ := r.ZRevRank(ctx, "lab04:leaderboard", "alice").Result()
```

Real output:

```text
ZRANK alice (low-to-high) -> 1
ZREVRANK alice (leaderboard position) -> 3
```

Alice is 4th place (`ZREVRANK` returns 3, 0-indexed).

### Tie-breaking

Bob and Dave both scored 2200. Redis breaks ties **lexicographically by member name,
ascending**, and that same relative order holds in both directions — `ZREVRANGE` reverses
the *whole* ordering, tie order included, it doesn't independently re-sort each tie group
descending:

```
ZREVRANK bob -> 1
ZREVRANK dave -> 0
```

`"bob" < "dave"` lexicographically, so in ascending order bob comes before dave; reversing
the whole set puts dave first. If your application needs a different tiebreak (e.g. "the
player who reached this score first wins ties"), you need a secondary signal baked into
the score itself (a common trick: `score * 10^13 - timestamp`, so higher score always
wins and, within equal scores, the earlier timestamp produces the larger combined value).

## Updating a score: `ZINCRBY`

Like `INCR` for sorted sets — atomically adjusts a member's score without a read-modify-
write round trip, and Redis re-threads its position in the ordering automatically:

```python
r.zincrby("lab04:leaderboard", 400, "erin")   # erin just won a match worth 400 points
r.zscore("lab04:leaderboard", "erin")
```

```
ZINCRBY erin +400 -> new score 1300.0
```

**Go:** `r.ZIncrBy(ctx, "lab04:leaderboard", 400, "erin").Result()` → real output:
`ZINCRBY erin +400 -> new score 1300`.

## Range by score

Beyond rank-based ranges, `ZRANGEBYSCORE` slices by the score value itself — "everyone
between 1000 and 2000 points":

```python
r.zrangebyscore("lab04:leaderboard", 1000, 2000, withscores=True)
```

```
ZRANGEBYSCORE 1000-2000 -> [('erin', 1300.0), ('alice', 1500.0), ('carol', 1800.0)]
```

**Go:**

```go
byScore, _ := r.ZRangeByScoreWithScores(ctx, "lab04:leaderboard",
    &redis.ZRangeBy{Min: "1000", Max: "2000"}).Result()
```

Real output: `ZRANGEBYSCORE 1000-2000 -> [(erin 1300.0) (alice 1500.0) (carol 1800.0)]`
— `Min`/`Max` are strings in `go-redis`'s `ZRangeBy`, not numbers, because Redis's
range syntax also accepts `(` prefixes for exclusive bounds (`(1000` = "greater than
1000, not equal") — a string is the only type that can represent both an inclusive
number and an exclusive-bound marker in one field.

## Common mistakes

- **Using a plain `SET`/list and sorting in application code.** That means pulling
  potentially every member across the network on every leaderboard read. A sorted set
  keeps the order maintained server-side as scores change, so reads are already sorted.
- **Forgetting scores are floats.** Two very large or very precise values can lose
  precision the same way any IEEE-754 double can — don't use a sorted set score as the
  sole source of truth for money.
- **Not planning for ties.** If tie order matters to your product, bake a tiebreaker into
  the score (see above) rather than relying on Redis's default lexicographic fallback.
- **`ZRANGEBYSCORE` on an unbounded range on a huge set.** Same O(output size) caution as
  `SMEMBERS` in level 03 — bound your ranges or paginate with `LIMIT offset count`.

## What's next

Level 05 steps back from individual data types to caching *patterns* — cache-aside,
write-through, eviction policies, and the cache stampede problem.
