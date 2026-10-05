# Redis Query Lab: Interview and Everyday Commands

Redis as it's used in real systems (caches, counters, sessions, rate limits, leaderboards,
queues, activity tracking, geo search, event streams) against a seeded dataset whose ids match
the SQL and MongoDB labs (`product:105` is product 105, `customer:3` is customer 3).

Open them in the app's **Query Lab** (NoSQL module → Query Lab → Redis) to run commands in an
in-browser Redis, check your answer and reveal the solution, or load the seed into the lab Redis
and use `redis-cli` (see [the datasets](datasets/README.md)).

Type one command per line, exactly as in `redis-cli`. The checker compares the **reply to your
last command** with the reply the reference solution gets; for exercises that change data it
also runs a check command afterwards. Every attempt starts from a fresh copy of the seed.

<!-- Format, for authors: same as SQL/lab/questions.md. Solutions are ```redis blocks, one
     command per line; a ```redis verify block runs after them. Tag "nil" marks an exercise
     whose correct final reply is (nil). -->

## Strings and counters

### Read a counter
<!-- id: get-pageviews | dataset: seed | level: Easy | tags: get, strings | order: strict -->

How many times has the home page been viewed? The count is stored in `pageviews:home`.

<details>
<summary>Solution</summary>

```redis
GET pageviews:home
```

Redis stores every string value as bytes, so even a number comes back as a bulk string
(`"184213"`); the client converts it.

</details>

### Count a page view
<!-- id: incr-pageviews | dataset: seed | level: Easy | tags: incr, counters, atomic | order: strict -->

Record one more view of the pricing page (`pageviews:pricing`) and return the new count.

> **Hint:** One command reads, adds and writes atomically.

<details>
<summary>Solution</summary>

```redis
INCR pageviews:pricing
```

`INCR` is atomic: a thousand clients incrementing at once lose no updates, with no locks. `GET` +
`SET` from the application would race. That's why counters are Redis's first use case.

</details>

### Read many keys in one round trip
<!-- id: mget-pageviews | dataset: seed | level: Easy | tags: mget, round trips | order: strict -->

Fetch the view counts of `home`, `pricing`, `docs` and `checkout` (keys `pageviews:<page>`) in a
single command.

<details>
<summary>Solution</summary>

```redis
MGET pageviews:home pageviews:pricing pageviews:docs pageviews:checkout
```

One `MGET` instead of four `GET`s saves three network round trips. At 0.5 ms per round trip and
thousands of requests per second, that's often the biggest latency win available.

</details>

### Cache with an expiry
<!-- id: cache-with-ttl | dataset: seed | level: Easy | tags: set, ex, ttl, caching | order: strict -->

Cache the rendered homepage under `cache:homepage` (any value) so it **expires after 60 seconds**,
then ask Redis how long it has left.

<details>
<summary>Solution</summary>

```redis
SET cache:homepage "<html>...</html>" EX 60
TTL cache:homepage
```

Setting the value and its expiry in one command matters: `SET` then `EXPIRE` leaves a window
where a crash would keep the key forever.

</details>

### A lock that can be taken once
<!-- id: lock-set-nx | dataset: seed | level: Medium | tags: set nx px, distributed lock, nil | order: strict -->

Implement a simple distributed lock on `lock:order:10001` for 30 seconds: worker 1 acquires it
with token `worker-1`. Then worker 2 tries to acquire it with token `worker-2`, which must fail.

Your last command should be worker 2's attempt.

> **Hint:** `SET key value NX PX 30000`: only set if not exists, expire after 30 s.

<details>
<summary>Solution</summary>

```redis
SET lock:order:10001 worker-1 NX PX 30000
SET lock:order:10001 worker-2 NX PX 30000
```

The second `SET ... NX` returns `(nil)`: the key exists. The expiry guarantees a crashed holder
can't block everyone forever. To release safely, a holder must delete the key only if it still
holds its own token (a check-and-delete done atomically with a Lua script), or it may delete a
lock that expired and was re-acquired by someone else. See the distributed locking chapter.

</details>

### Rate limit a user
<!-- id: rate-limit-window | dataset: seed | level: Medium | tags: multi, incr, expire, rate limiting | order: strict -->

A fixed-window rate limiter: count a request for user 42 in the window key
`ratelimit:user:42:2025-10-05T10:16`, make the key expire after 60 seconds, and do both
**atomically**.

Your last command should return both replies.

<details>
<summary>Solution</summary>

```redis
MULTI
INCR ratelimit:user:42:2025-10-05T10:16
EXPIRE ratelimit:user:42:2025-10-05T10:16 60
EXEC
```

`MULTI`/`EXEC` queues commands and runs them as one unit, so no request can increment the
counter between `INCR` and `EXPIRE`. The app then compares the count with its limit (say 100
per minute). Sliding-window limiters use a sorted set of timestamps instead.

</details>

## Keys and expiry

### Find keys by pattern
<!-- id: scan-sessions | dataset: seed | level: Easy | tags: scan, keys, patterns | order: strict -->

List all session keys (`session:*`) using the production-safe command.

<details>
<summary>Solution</summary>

```redis
SCAN 0 MATCH session:* COUNT 1000
```

`KEYS session:*` gives the same answer here but blocks the whole server while it walks every
key: never run it on a production Redis. `SCAN` returns a cursor; keep calling it with the
returned cursor until it comes back as `0`.

</details>

### How long until it expires?
<!-- id: ttl-product | dataset: seed | level: Easy | tags: ttl | order: strict -->

The cached product `product:101` was stored with a one-hour expiry. How many seconds does it
have left?

<details>
<summary>Solution</summary>

```redis
TTL product:101
```

`TTL` returns `-1` for a key without an expiry and `-2` for a key that doesn't exist.

</details>

### Keep a key forever
<!-- id: persist-key | dataset: seed | level: Easy | tags: persist, ttl | order: strict -->

Remove the expiry from `product:102`, then show its TTL.

<details>
<summary>Solution</summary>

```redis
PERSIST product:102
TTL product:102
```

</details>

### What type is it?
<!-- id: key-type | dataset: seed | level: Easy | tags: type | order: strict -->

What data type is stored at `stream:orders`?

<details>
<summary>Solution</summary>

```redis
TYPE stream:orders
```

Every Redis command works on one type; using the wrong one gives a `WRONGTYPE` error rather than
converting.

</details>

## Hashes

### Read a cached product
<!-- id: hgetall-product | dataset: seed | level: Easy | tags: hgetall, hashes | order: strict -->

Product 105 is cached as a hash at `product:105`. Return all of its fields and values.

<details>
<summary>Solution</summary>

```redis
HGETALL product:105
```

A hash per object is the usual way to cache a row: you can read or update one field without
fetching and rewriting the whole object (which a JSON string would require).

</details>

### Read two fields
<!-- id: hmget-fields | dataset: seed | level: Easy | tags: hmget | order: strict -->

Return just the `name` and `price` of product 105.

<details>
<summary>Solution</summary>

```redis
HMGET product:105 name price
```

</details>

### Sell two units
<!-- id: hincrby-stock | dataset: seed | level: Easy | tags: hincrby, atomic | order: strict -->

Two units of product 105 were just sold. Decrease its cached `stock` and return the new value.

<details>
<summary>Solution</summary>

```redis
HINCRBY product:105 stock -2
```

</details>

### Add to cart
<!-- id: cart-add | dataset: seed | level: Easy | tags: hincrby, carts | order: strict -->

Customer 3's cart is the hash `cart:customer:3` (field = product key, value = quantity). Add one
`product:185` to it and return the new quantity.

<details>
<summary>Solution</summary>

```redis
HINCRBY cart:customer:3 product:185 1
```

Carts in a hash per user is a classic Redis design: `HINCRBY` adds items, `HDEL` removes them,
`HGETALL` renders the cart, and an expiry cleans up abandoned carts.

</details>

## Lists

### Recently viewed
<!-- id: recent-views | dataset: seed | level: Easy | tags: lrange, lists | order: strict -->

Return customer 1's recently viewed products (`recent:customer:1`), most recent first.

<details>
<summary>Solution</summary>

```redis
LRANGE recent:customer:1 0 -1
```

</details>

### Keep the list capped
<!-- id: capped-list | dataset: seed | level: Medium | tags: lpush, ltrim, capped list | order: strict -->

Customer 1 just viewed `product:999`. Add it to the front of `recent:customer:1`, keep only the 5
most recent entries, then return the list.

<details>
<summary>Solution</summary>

```redis
LPUSH recent:customer:1 product:999
LTRIM recent:customer:1 0 4
LRANGE recent:customer:1 0 -1
```

`LPUSH` + `LTRIM` is the capped-list idiom (activity feeds, recent searches, logs): the list
never grows past N, and both commands are O(1) for the trimmed end.

</details>

### A work queue
<!-- id: fifo-queue | dataset: seed | level: Easy | tags: rpush, lpop, queue | order: strict -->

Use `jobs:email` as a FIFO queue: enqueue the jobs `welcome`, `receipt` and `reminder` in that
order, then take the next job off the queue.

<details>
<summary>Solution</summary>

```redis
RPUSH jobs:email welcome receipt reminder
LPOP jobs:email
```

Push on one end, pop from the other: that's a queue. A worker would use `BLPOP` to wait for work
instead of polling; for at-least-once processing with acknowledgements, use a stream with a
consumer group (see the Streams section).

</details>

## Sets

### Mutual follows
<!-- id: mutual-follows | dataset: seed | level: Easy | tags: sinter, sets, social graph | order: strict -->

`following:<id>` is the set of user ids that a user follows. Which users do both user 3 and user 8
follow?

<details>
<summary>Solution</summary>

```redis
SINTER following:3 following:8
```

Set intersection on the server: "people you both follow", "mutual friends", "products in both
tags". Real Redis returns set members in no particular order (the lab sorts them).

</details>

### Who to follow
<!-- id: follow-suggestions | dataset: seed | level: Easy | tags: sdiff | order: strict -->

Suggest accounts to user 3: users that user 8 follows but user 3 doesn't (and isn't user 3).

> **Hint:** `SDIFF` returns members of the first set that are in none of the others.

<details>
<summary>Solution</summary>

```redis
SDIFF following:8 following:3
```

</details>

### Products with two tags
<!-- id: tag-intersection | dataset: seed | level: Easy | tags: sinter, tags | order: strict -->

`products:tag:<tag>` holds the ids of products with that tag. Which products are tagged both
`electronics` and `volt`?

<details>
<summary>Solution</summary>

```redis
SINTER products:tag:electronics products:tag:volt
```

</details>

### Is it a member?
<!-- id: sismember | dataset: seed | level: Easy | tags: sismember | order: strict -->

Does user 3 follow user 17?

<details>
<summary>Solution</summary>

```redis
SISMEMBER following:3 17
```

Membership checks on a set are O(1), whatever its size.

</details>

## Sorted sets

### Leaderboard top 10
<!-- id: leaderboard-top10 | dataset: seed | level: Easy | tags: zrevrange, leaderboard | order: strict -->

Show the top 10 players of week 40 (`leaderboard:2025-W40`) with their scores, highest first.

<details>
<summary>Solution</summary>

```redis
ZREVRANGE leaderboard:2025-W40 0 9 WITHSCORES
```

In Redis 6.2+ the same is `ZRANGE leaderboard:2025-W40 0 9 REV WITHSCORES`. A sorted set keeps
members ordered by score at all times, so reading the top N is O(log n + N) no matter how many
players there are. That's why leaderboards are the textbook sorted-set use case.

</details>

### A player's rank
<!-- id: player-rank | dataset: seed | level: Easy | tags: zrevrank | order: strict -->

What is `sophia_81`'s position in week 40, where 0 is the top player?

<details>
<summary>Solution</summary>

```redis
ZREVRANK leaderboard:2025-W40 sophia_81
```

`ZRANK` counts from the lowest score, `ZREVRANK` from the highest. Both are 0-based, so add 1
before showing "rank 5" to a user.

</details>

### Award points
<!-- id: award-points | dataset: seed | level: Easy | tags: zincrby | order: strict -->

`sophia_81` scores 500 more points in week 40. Add them and return the new score.

<details>
<summary>Solution</summary>

```redis
ZINCRBY leaderboard:2025-W40 500 sophia_81
```

</details>

### Players in a score range
<!-- id: score-range | dataset: seed | level: Easy | tags: zcount | order: strict -->

How many week-40 players scored between 5000 and 7000 points, inclusive?

<details>
<summary>Solution</summary>

```redis
ZCOUNT leaderboard:2025-W40 5000 7000
```

Use `(5000` for an exclusive bound and `-inf` / `+inf` for open ranges.

</details>

### Two-week leaderboard
<!-- id: two-week-leaderboard | dataset: seed | level: Medium | tags: zunionstore, aggregation | order: strict -->

Combine weeks 40 and 41 into `leaderboard:2025-W40-41` (a player's scores add up; players who
only played one week keep that week's score), then show the top 5 with scores.

<details>
<summary>Solution</summary>

```redis
ZUNIONSTORE leaderboard:2025-W40-41 2 leaderboard:2025-W40 leaderboard:2025-W41
ZREVRANGE leaderboard:2025-W40-41 0 4 WITHSCORES
```

`ZUNIONSTORE` sums scores by default; `AGGREGATE MAX` would keep each player's best week, and
`WEIGHTS` can scale one week (e.g. weight older weeks less).

</details>

### Best-selling products
<!-- id: bestsellers-top5 | dataset: seed | level: Easy | tags: zrange rev, ranking | order: strict -->

`bestsellers` scores each product by units sold. Return the top 5 with their unit counts.

<details>
<summary>Solution</summary>

```redis
ZRANGE bestsellers 0 4 REV WITHSCORES
```

</details>

## Bitmaps and HyperLogLog

### Daily active users
<!-- id: dau-bitcount | dataset: seed | level: Easy | tags: bitmaps, bitcount, dau | order: strict -->

`dau:<date>` is a bitmap where bit N is 1 if user N was active that day. How many users were
active on 2025-09-01?

<details>
<summary>Solution</summary>

```redis
BITCOUNT dau:2025-09-01
```

One bit per user: 100 million users fit in about 12 MB per day, and counting is a fast popcount.

</details>

### Active every day of the week
<!-- id: active-all-week | dataset: seed | level: Medium | tags: bitop, bitmaps, retention | order: strict -->

How many users were active on **every** day from 2025-09-01 to 2025-09-07? Store the combined
bitmap in `active:2025-09-01..07`, then count it.

<details>
<summary>Solution</summary>

```redis
BITOP AND active:2025-09-01..07 dau:2025-09-01 dau:2025-09-02 dau:2025-09-03 dau:2025-09-04 dau:2025-09-05 dau:2025-09-06 dau:2025-09-07
BITCOUNT active:2025-09-01..07
```

`BITOP AND` keeps users active on all days; `OR` would give weekly actives (anyone active at
least once). That's a whole retention query in two commands.

</details>

### Was a user active?
<!-- id: getbit-user | dataset: seed | level: Easy | tags: getbit | order: strict -->

Was user 9 active on 2025-09-03?

<details>
<summary>Solution</summary>

```redis
GETBIT dau:2025-09-03 9
```

</details>

### Unique visitors this week
<!-- id: weekly-uniques-hll | dataset: seed | level: Medium | tags: hyperloglog, pfcount, cardinality | order: strict -->

`uniques:<date>` is a HyperLogLog of visitor ids. How many distinct visitors came during
2025-09-01 to 2025-09-07?

<details>
<summary>Solution</summary>

```redis
PFCOUNT uniques:2025-09-01 uniques:2025-09-02 uniques:2025-09-03 uniques:2025-09-04 uniques:2025-09-05 uniques:2025-09-06 uniques:2025-09-07
```

`PFCOUNT` over several keys counts the union, without double-counting people who came on
several days. A HyperLogLog uses at most 12 KB per key whatever the count, at the cost of a
~0.81% standard error. (The lab's in-browser Redis counts exactly; a real server's answer can
differ by a few.)

</details>

## Geo

### Stores near Pune
<!-- id: stores-near | dataset: seed | level: Medium | tags: geosearch, geo | order: strict -->

`stores` holds store locations. Which stores are within 500 km of the **Pune** store, nearest
first, with their distance in km?

<details>
<summary>Solution</summary>

```redis
GEOSEARCH stores FROMMEMBER Pune BYRADIUS 500 km ASC WITHDIST
```

Geo commands store coordinates as a geohash in a sorted set, so a radius search is a few range
scans. Use `FROMLONLAT <lon> <lat>` to search around a user's position instead.

</details>

### Distance between two stores
<!-- id: geodist | dataset: seed | level: Easy | tags: geodist | order: strict -->

How far is the London store from the Paris store, in kilometres?

<details>
<summary>Solution</summary>

```redis
GEODIST stores London Paris km
```

</details>

## Streams

### Latest orders
<!-- id: stream-latest | dataset: seed | level: Easy | tags: streams, xrevrange | order: strict -->

`stream:orders` is an event stream of orders. Return the 3 most recent entries.

<details>
<summary>Solution</summary>

```redis
XREVRANGE stream:orders + - COUNT 3
```

`+` and `-` mean the largest and smallest possible ids. Entry ids are `<milliseconds>-<sequence>`,
so ranges can also be times.

</details>

### A consumer group
<!-- id: consumer-group | dataset: seed | level: Hard | tags: streams, xgroup, xreadgroup, xack, xpending | order: strict -->

Process the stream with a consumer group: create group `fulfilment` on `stream:orders` starting
from the beginning, let consumer `worker-1` read 5 entries, acknowledge the first one
(`1767001920000-0`), then show the group's pending summary.

<details>
<summary>Solution</summary>

```redis
XGROUP CREATE stream:orders fulfilment 0
XREADGROUP GROUP fulfilment worker-1 COUNT 5 STREAMS stream:orders >
XACK stream:orders fulfilment 1767001920000-0
XPENDING stream:orders fulfilment
```

Each entry is delivered to one consumer in the group and stays *pending* until acknowledged.
If `worker-1` crashes, `XPENDING` shows what it held and `XCLAIM` (or `XAUTOCLAIM`) hands those
entries to another worker. That's at-least-once processing, which a plain list queue can't give.

</details>

## Transactions

### Optimistic locking with WATCH
<!-- id: watch-multi | dataset: seed | level: Hard | tags: watch, multi, exec, optimistic locking | order: strict -->

Sell one unit of product 105 with optimistic locking: `WATCH` the key, then decrement `stock` in a
`MULTI`/`EXEC` transaction. Return the transaction's result.

<details>
<summary>Solution</summary>

```redis
WATCH product:105
MULTI
HINCRBY product:105 stock -1
EXEC
```

If another client changes `product:105` between `WATCH` and `EXEC`, `EXEC` returns `(nil)` and
nothing runs; the client retries. This check-and-set pattern is how you do read-modify-write in
Redis without locks (when the logic is too complex for a single atomic command or a Lua script).

</details>
