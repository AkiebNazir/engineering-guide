# Rate Limiting With Redis

`content/data-and-apis/API/REST/labs/golang/04_rate_limit_middleware` builds a token-bucket rate limiter with a
Go `map[string]*bucket` protected by a `sync.Mutex`. It's correct, fast, and a genuinely
good pattern — for **one process**. This level builds the same idea shared across every
process in your fleet, and is explicit about exactly where the in-memory version stops
working.

## Why an in-memory limiter breaks with more than one app server

The Go limiter's state lives in that one process's heap. The moment you run **two**
instances of that app behind a load balancer (which is the normal way to scale — not the
exception), each instance has its own independent map, its own independent bucket for
"client X." A client hitting instance A five times and instance B five times has, from
each instance's own point of view, only used 5 of its 5-request budget — but has actually
made 10 requests against your system. The limiter isn't wrong; it's answering a question
("has *this process* seen too many requests from X?") that no longer matches the real
question ("has X exceeded its limit against the whole service?").

The fix is the same move as the session-store problem in level 00: pull the shared state
out of any one process's memory and into something every instance can reach — Redis.

## A sliding-window limiter, atomic via a Lua script

A sliding-window-log approach: keep a sorted set (level 04) of request timestamps per
client; on each request, drop timestamps outside the window, count what's left, and admit
the request only if under the limit. All of that has to happen as one atomic step — if
"count" and "add" were two separate round trips, two concurrent requests could both read
"4 of 5 used" and both get admitted, blowing the limit. A Lua script executes atomically
on the server (same guarantee as `MULTI`/`EXEC`, level 07), so this is safe under real
concurrency:

```python
SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

redis.call("ZREMRANGEBYSCORE", key, 0, now - window_ms)
local count = redis.call("ZCARD", key)
if count < limit then
    redis.call("ZADD", key, now, now .. "-" .. math.random())
    redis.call("PEXPIRE", key, window_ms)
    return {1, count + 1}
else
    return {0, count}
end
"""

def allow(client_id, limit=5, window_ms=1000):
    key = f"lab09:ratelimit:{client_id}"
    now_ms = int(time.time() * 1000)
    ok, count = r.eval(SLIDING_WINDOW_SCRIPT, 1, key, now_ms, window_ms, limit)
    return bool(ok), count
```

Run against the live instance — one client firing 8 requests instantly against a
limit of 5 per second:

```
-- single client, limit=5 per 1000ms, firing 8 requests instantly --
[(True, 1), (True, 2), (True, 3), (True, 4), (True, 5), (False, 5), (False, 5), (False, 5)]

-- wait for the window to roll, then retry --
(True, 1)
```

Requests 6–8 are denied within the same window; once the 1-second window rolls forward,
the limit resets, exactly as expected.

**Go (`go-redis/v9`):** the Lua script body is unchanged — same point as level 08:
Lua runs server-side inside Redis, so it's identical regardless of caller language.
Only the invocation differs:

```go
func allow(ctx context.Context, r *redis.Client, clientID string, limit, windowMs int64) (bool, int64) {
    key := fmt.Sprintf("lab09:ratelimit:%s", clientID)
    nowMs := time.Now().UnixMilli()
    res, _ := r.Eval(ctx, slidingWindowScript, []string{key}, nowMs, windowMs, limit).Result()
    arr := res.([]interface{})
    return arr[0].(int64) == 1, arr[1].(int64)
}
```

Real output, same 8-requests-instantly scenario:

```text
-- single client, limit=5 per 1000ms, firing 8 requests instantly --
(true 1) (true 2) (true 3) (true 4) (true 5) (false 5) (false 5) (false 5)
-- wait for the window to roll, then retry --
true 1
```

`Eval`'s result comes back as `interface{}` in Go (Redis's `EVAL` reply is
dynamically shaped — here, a 2-element array), so reading it means a type assertion
(`res.([]interface{})`, then each element's own assertion) — the price Go's static
typing pays for calling into a genuinely dynamic scripting language, versus Python's
scripting-language-to-scripting-language call needing no such unwrapping.

## The actual point: this is shared across processes

To make the "shared across servers" claim real rather than asserted, this simulates two
separate application server processes — two independent `redis.Redis` connections, each
standing in for a different instance behind a load balancer — both checking the *same*
Redis-backed counter for the same client:

```python
server_a = redis.Redis(host="localhost", port=6390, decode_responses=True)  # "app server A"
server_b = redis.Redis(host="localhost", port=6390, decode_responses=True)  # "app server B"

for i in range(3):
    print("server A:", allow_via(server_a, "shared_client"))
for i in range(3):
    print("server B:", allow_via(server_b, "shared_client"))
```

Actual output:

```
server A: (True, 1)
server A: (True, 2)
server A: (True, 3)
server B: (True, 4)
server B: (True, 5)
server B: (False, 5)
```

Server B's third request is denied — not because server B individually saw too many
requests (it only handled 3), but because the *combined* total across both servers hit
the shared limit of 5. This is exactly the coordination the Go in-memory limiter cannot
do: its map is per-process, so server A's 3 and server B's 3 would each independently
look like "well under 5," letting 6 requests through against a supposed limit of 5.

**Go (`go-redis/v9`), same two-"server" simulation** — two independent
`*redis.Client` instances, standing in for two app-server processes, both hitting the
same Redis-backed key:

```go
serverA := redis.NewClient(&redis.Options{Addr: "localhost:6390"})
serverB := redis.NewClient(&redis.Options{Addr: "localhost:6390"})

for i := 0; i < 3; i++ {
    ok, count := allow(ctx, serverA, "shared_client", 5, 1000)
    fmt.Println("server A:", ok, count)
}
for i := 0; i < 3; i++ {
    ok, count := allow(ctx, serverB, "shared_client", 5, 1000)
    fmt.Println("server B:", ok, count)
}
```

Real output — identical outcome to the Python run, because both clients are hitting
the same shared counter in Redis, not any per-process state either language's client
library holds:

```text
server A: true 1
server A: true 2
server A: true 3
server B: true 4
server B: true 5
server B: false 5
```

This is the concrete answer to "why not just use the Go `sync.Mutex` limiter from
`content/data-and-apis/API/REST/labs/golang/04_rate_limit_middleware` here" — that limiter is also written in
Go, and it *still* wouldn't coordinate across two processes, because its state lives in
one process's heap regardless of language. The fix was never "use a different
language's client" — it's "move the state into something every process can reach,"
which this demo proves by using the *same* language (Go) on both simulated servers and
still needing Redis to make them agree.

## `MULTI`/`WATCH` as the alternative to Lua

The same atomicity can be built with `WATCH` + `MULTI`/`EXEC` (level 07) instead of a Lua
script — read the count, check it, and conditionally write in a retry loop. A Lua script
is generally preferred for rate limiters because it's a single round trip with no retry
loop needed (the whole check-and-increment happens in one server-side execution), but the
`WATCH` version is worth knowing since it doesn't require `EVAL` permissions, which some
managed Redis providers restrict.

## Sliding window vs. token bucket

This level used a sliding-window log (`ZSET` of timestamps) because it maps directly onto
sorted sets you already know from level 04. The Go example in
`04_rate_limit_middleware` uses a token bucket instead (a float balance that refills over
time) — functionally similar (both smooth out bursts, both allow a bounded rate over
time), implementable in Redis the same way (a hash or two keys holding `tokens` and
`last_refill`, updated atomically via the same Lua-script approach). The choice between
them is usually about memory (a sliding-window log stores one entry per request in the
window; a token bucket stores two numbers regardless of request volume) rather than which
one is "shareable" — sharing across processes is what moving the state into Redis buys
you either way.

## Try it in the browser

The ▶ Run buttons on this page run an in-browser Redis loaded with the Query Lab seed
(its `ratelimit:user:<id>:<minute>` keys are fixed-window counters; see
[the datasets README](../lab/datasets/README.md)). It doesn't run Lua, so instead of
`EVAL` you run the script's commands yourself, one line at a time, with the timestamps
written out. Keep in mind that by hand they are *not* atomic: that's the gap the script, or
`WATCH`/`MULTI`, closes.

The simplest shared limiter is a fixed window: one counter per client per window (an
hour here, so the key name ends in the hour). `INCR` counts the request, and
`EXPIRE ... NX` (Redis 7.0+) sets the TTL only on the first request of the window, so
later requests don't keep pushing it back.

```redis
INCR ratelimit:user:42:2025-10-05T10            # -> 1
EXPIRE ratelimit:user:42:2025-10-05T10 3600 NX  # -> 1 (TTL set)
INCR ratelimit:user:42:2025-10-05T10            # -> 2
EXPIRE ratelimit:user:42:2025-10-05T10 3600 NX  # -> 0 (already has one)
TTL ratelimit:user:42:2025-10-05T10             # -> 3600
```

The point of this level: two app servers, one Redis. Each server's request lands on the
same key, so the count is the client's total across the fleet, not per process.

```redis
# app server A handles a request from user 42
INCR ratelimit:user:42:2025-10-05T10  # -> 3
# app server B handles the next one
INCR ratelimit:user:42:2025-10-05T10  # -> 4
```

To make "count, then set the expiry" one indivisible step without Lua, wrap the pair in
`MULTI`/`EXEC`. The app compares the first reply with the limit (say 1000 per hour).

```redis
MULTI                                           # -> OK
INCR ratelimit:user:42:2025-10-05T10            # -> QUEUED
EXPIRE ratelimit:user:42:2025-10-05T10 3600 NX  # -> QUEUED
EXEC                                            # -> 5, 0: request 5 of 1000, allowed
```

Now the sliding-window log from the Lua script, step by step, with a limit of 5 per
1000 ms. Five requests arrived between 10:16:00.100 and 10:16:00.900 (scores and members
are Unix millisecond timestamps).

```redis
ZADD lab09:ratelimit:client-a 1759659360100 1759659360100-1  # -> 1
ZADD lab09:ratelimit:client-a 1759659360300 1759659360300-1  # -> 1
ZADD lab09:ratelimit:client-a 1759659360500 1759659360500-1  # -> 1
ZADD lab09:ratelimit:client-a 1759659360700 1759659360700-1  # -> 1
ZADD lab09:ratelimit:client-a 1759659360900 1759659360900-1  # -> 1
```

Request 6 at `now = 1759659361000`: drop everything at or before `now - 1000`, count what's
left, and compare with the limit. Five are still inside the window, so it's denied and
nothing is added.

```redis
ZREMRANGEBYSCORE lab09:ratelimit:client-a 0 1759659360000  # -> 0 (nothing old enough to drop)
ZCARD lab09:ratelimit:client-a                             # -> 5: at the limit, deny
```

Request 7 arrives 400 ms later. The window has slid past the two oldest entries, so there
is room: record this request and refresh the key's expiry so an idle client's set cleans
itself up.

```redis
ZREMRANGEBYSCORE lab09:ratelimit:client-a 0 1759659360400    # -> 2 (the 10:16:00.100 and .300 requests)
ZCARD lab09:ratelimit:client-a                               # -> 3: under 5, allow
ZADD lab09:ratelimit:client-a 1759659361400 1759659361400-1  # -> 1
PEXPIRE lab09:ratelimit:client-a 1000                        # -> 1
ZRANGE lab09:ratelimit:client-a 0 -1 WITHSCORES              # -> the .500, .700, .900 and 01.400 requests
```

The `WATCH` version from "`MULTI`/`WATCH` as the alternative to Lua": watch the key, read
the in-window count with `ZCOUNT` (a read, which doesn't trip our own watch), and only
then queue the writes. If another request changed the key in between, `EXEC` returns
`(nil)` and the app retries.

```redis
WATCH lab09:ratelimit:client-b                               # -> OK
ZCOUNT lab09:ratelimit:client-b (1759659360500 +inf          # -> 0: under the limit
MULTI                                                        # -> OK
ZREMRANGEBYSCORE lab09:ratelimit:client-b 0 1759659360500    # -> QUEUED
ZADD lab09:ratelimit:client-b 1759659361500 1759659361500-1  # -> QUEUED
PEXPIRE lab09:ratelimit:client-b 1000                        # -> QUEUED
EXEC                                                         # -> 0, 1, 1: allowed
```

## Common mistakes

- **Doing the check and the increment as two separate Redis calls from application code.**
  That reopens exactly the race a single-command or Lua-script approach was built to
  close — two concurrent requests can both read "under limit" before either writes.
- **Forgetting to expire the key.** Without `PEXPIRE`, a rarely-hit client's sorted set
  keeps a tiny sliver of old data forever instead of being cleaned up.
- **Assuming Redis being down means "fail open" is automatically the right default.** For
  many APIs, if the rate limiter can't be reached, you want to fail open (let requests
  through) rather than take the whole API down — but that's a product decision, not a
  given; decide and document which one you want up front.

## What's next

Level 10 covers what happens to all of this state when the Redis process itself restarts
— RDB snapshots vs the append-only file (AOF), and the tradeoff between them.
