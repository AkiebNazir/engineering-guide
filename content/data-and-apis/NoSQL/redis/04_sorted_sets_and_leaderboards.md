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

## Try it in the browser

The ▶ Run buttons on this page run an in-browser Redis loaded with the Query Lab seed,
which has two weekly game leaderboards (`leaderboard:2025-W40` and `-W41`) and a
`bestsellers` ranking of products by units sold (see
[the datasets README](../lab/datasets/README.md)). Writes stay in this page's session.

The chapter's own example first. Notice the tie: bob and dave both have 2200, so
ascending order puts bob (alphabetically first) ahead of dave, and the reversed order puts
dave first. `ZRANGE ... REV` is the Redis 6.2+ spelling of `ZREVRANGE`.

```redis
ZADD lab04:leaderboard 1500 alice 2200 bob 1800 carol 2200 dave 900 erin  # -> 5
ZRANGE lab04:leaderboard 0 -1 WITHSCORES        # -> erin 900 ... bob 2200, dave 2200
ZRANGE lab04:leaderboard 0 2 REV WITHSCORES     # -> dave 2200, bob 2200, carol 1800
ZREVRANK lab04:leaderboard dave                 # -> 0
ZREVRANK lab04:leaderboard bob                  # -> 1
ZREVRANK lab04:leaderboard alice                # -> 3 (4th place)
```

`ZINCRBY` and `ZRANGEBYSCORE`, as in the sections above: erin wins a 400-point match, and
then a score-range query returns her. A `(` makes a bound exclusive.

```redis
ZINCRBY lab04:leaderboard 400 erin                       # -> "1300"
ZRANGEBYSCORE lab04:leaderboard 1000 2000 WITHSCORES     # -> erin 1300, alice 1500, carol 1800
ZRANGEBYSCORE lab04:leaderboard (1300 2000               # -> "alice", "carol"
ZCOUNT lab04:leaderboard 2000 +inf                       # -> 2
```

Now a real-sized board. The top 5 of week 40 with their scores, and how many players
there are:

```redis
ZRANGE leaderboard:2025-W40 0 4 REV WITHSCORES      # -> liam_12 9620, lucas_86 9494, ...
ZCARD leaderboard:2025-W40                          # -> 60
```

"Where am I?" for one player: their score, their 0-based rank from the top, and the
players right around them (rank − 2 to rank + 2, an "around me" view).

```redis
ZSCORE leaderboard:2025-W40 sophia_81                   # -> "9396"
ZREVRANK leaderboard:2025-W40 sophia_81                 # -> 4 (5th place)
ZRANGE leaderboard:2025-W40 2 6 REV WITHSCORES          # -> ravi_99, jun_10, sophia_81, aisha_65, diego_43
```

A score change re-sorts the member immediately. manish_33 has a great session; check the
rank before and after.

```redis
ZREVRANK leaderboard:2025-W40 manish_33         # -> 48 (49th place)
ZINCRBY leaderboard:2025-W40 7000 manish_33     # -> "9564"
ZREVRANK leaderboard:2025-W40 manish_33         # -> 1 (2nd place)
```

Paginate by score instead of rank: everyone between 8000 and 9000 points, highest first,
10 at a time. `LIMIT offset count` keeps a wide range from returning everything at once.

```redis
ZRANGE leaderboard:2025-W40 9000 8000 BYSCORE REV LIMIT 0 10 WITHSCORES  # -> sakura_26 8597 down to arjun_67 8245
ZCOUNT leaderboard:2025-W40 8000 9000           # -> 7, so one page holds them all
```

A two-week total is one command: `ZUNIONSTORE` adds each player's scores across the weeks
into a new sorted set (players in only one week keep that score).

```redis
ZUNIONSTORE lab04:2025-W40-41 2 leaderboard:2025-W40 leaderboard:2025-W41  # -> 60 players in either week
ZRANGE lab04:2025-W40-41 0 2 REV WITHSCORES                                # -> ravi_99 18984, yusuf_42 17846, lucas_86 17718
```

The same structure ranks products. A sale of 3 units is a `ZINCRBY`, and the top sellers
are a reverse range.

```redis
ZINCRBY bestsellers 3 product:105                   # -> "33"
ZRANGE bestsellers 0 2 REV WITHSCORES               # -> product:161 1289, product:171 611, product:103 543
ZREVRANK bestsellers product:105                    # -> 97: a long way down the list
```

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
