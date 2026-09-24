# Strings and Atomic Counters

The Redis "string" type holds anything up to 512 MB — text, JSON, a serialized blob, or a
number. When it holds a number, Redis gives you a set of commands that increment or
decrement it **atomically**, with no read-modify-write race, because (level 00) only one
command executes on the server at a time.

## `INCR` / `DECR` / `INCRBY` / `DECRBY`

```bash
SET lab02:views 0
INCR lab02:views       # -> 1
INCR lab02:views       # -> 2
INCRBY lab02:views 10  # -> 12
DECR lab02:views       # -> 11
DECRBY lab02:views 5   # -> 6
```

`INCR` on a key that doesn't exist yet treats it as `0` first, then increments — you don't
need to `SET` a counter to `0` before using it:

```python
>>> r.incr("lab02:views")   # key didn't exist
1
>>> r.incr("lab02:views")
2
```

## Why atomicity actually matters here

The naive way to build a counter without `INCR` is "read the value, add one, write it
back" in application code. That's a classic race: two processes can both read `41`,
both compute `42`, and both write `42` — one increment is silently lost. `INCR` closes
that gap because Redis executes it as one indivisible server-side step; there is no
window where two clients can interleave.

This was actually measured, not just asserted: 10 threads each called `INCR` on the same
key 1000 times concurrently (10,000 increments total) against the live lab instance:

```python
import redis, threading

r = redis.Redis(host="localhost", port=6390, decode_responses=True)
r.set("lab02:stock", 0)

def hammer():
    for _ in range(1000):
        r.incr("lab02:stock")

threads = [threading.Thread(target=hammer) for _ in range(10)]
[t.start() for t in threads]
[t.join() for t in threads]
print("expected 10000, got ->", r.get("lab02:stock"))
```

Output:

```
expected 10000, got -> 10000
```

No lost updates. If this were "read in Python, add 1, write back," the result would come
in under 10,000 almost every run — one of countless naive-counter bugs that atomic
`INCR` simply removes from the problem space.

**Go (`go-redis/v9`):** the same race, using 10 goroutines instead of 10 threads:

```go
r.Set(ctx, "lab02:stock", 0, 0)

var wg sync.WaitGroup
for i := 0; i < 10; i++ {
    wg.Add(1)
    go func() {
        defer wg.Done()
        for j := 0; j < 1000; j++ {
            r.Incr(ctx, "lab02:stock")
        }
    }()
}
wg.Wait()
final, _ := r.Get(ctx, "lab02:stock").Result()
fmt.Println("expected 10000, got ->", final)
```

Real output:

```text
expected 10000, got -> 10000
```

Same result, same reason — the race Python's threads and Go's goroutines are both
racing to hit doesn't exist on Redis's side either way, because `INCR` is one atomic
server-side step regardless of which language, or how many concurrent callers, issue
it.

## Combining a value with expiry

Three different tools, three different shapes of the same need:

| Command | Does |
|---|---|
| `SET key val EX seconds` | Set a value **and** an expiry in one round trip |
| `SETEX key seconds val` | Same thing, older/dedicated form (now considered legacy — `SET ... EX` is preferred) |
| `GETEX key EX seconds` | **Read** the current value and (optionally) change its TTL in the same call |

```python
>>> r.setex("lab02:sess", 3, "session-data")   # deprecated form, still works
>>> r.ttl("lab02:sess")
3
```

`redis-py` actually emits a `DeprecationWarning` for `.setex()` now, nudging you toward
`r.set("lab02:sess", "session-data", ex=3)` — same effect, one blessed spelling.

`GETEX` is the interesting one: it lets you **read a value while sliding its expiry
forward**, which is exactly the "keep this session alive as long as it's being used"
pattern:

```python
>>> r.set("lab02:sess", "session-data")
>>> r.getex("lab02:sess", ex=2)      # read it, and reset TTL to 2s
'session-data'
>>> r.ttl("lab02:sess")
2
>>> r.getex("lab02:sess", persist=True)   # read it, and remove the TTL entirely
'session-data'
>>> r.ttl("lab02:sess")
-1
```

Confirmed against the live instance:

```
SETEX ttl -> 3
GETEX returned -> session-data new ttl -> 2
GETEX persist -> ttl now -> -1
```

Before `GETEX` existed (Redis < 6.2), doing "read, then refresh TTL" took two round
trips (`GET` then `EXPIRE`) — not atomic against a concurrent `DEL`, and twice the
network latency. `GETEX` folds it into one.

**Go (`go-redis/v9`):** `go-redis` doesn't expose a separate `SETEX` method at all —
`Set` with a non-zero `time.Duration` *is* `SET ... EX`, one blessed spelling from the
start (Go never had the legacy two-name problem `redis-py` is only now deprecating).
`GetEx` mirrors the Python version, and `Persist` is the equivalent of Python's
`getex(persist=True)`:

```go
r.Set(ctx, "lab02:sess", "session-data", 3*time.Second)
ttl, _ := r.TTL(ctx, "lab02:sess").Result()
fmt.Println("SET EX ttl ->", ttl)

r.Set(ctx, "lab02:sess2", "session-data", 0)
val, _ := r.GetEx(ctx, "lab02:sess2", 2*time.Second).Result()
ttl2, _ := r.TTL(ctx, "lab02:sess2").Result()
fmt.Println("GetEx returned ->", val, "new ttl ->", ttl2)

r.Persist(ctx, "lab02:sess2")
ttl3, _ := r.TTL(ctx, "lab02:sess2").Result()
fmt.Println("ttl after Persist ->", ttl3)
```

Real output:

```text
SET EX ttl -> 3s
GetEx returned -> session-data new ttl -> 2s
ttl after Persist -> -1ns
```

That last line is a genuine Go client gotcha, caught by actually running it rather
than assumed: `go-redis` represents Redis's `-1` ("no expiry") and `-2` ("key doesn't
exist") TTL sentinels as raw `time.Duration(-1)`/`time.Duration(-2)` — which
`fmt.Println` renders as `-1ns`/`-2ns`, not as the value 1 or 2 seconds negated. Code
that reads `-1ns` and assumes "a small negative duration" instead of recognizing it as
the same `-1` sentinel level 01 already covers is exactly the trap this repo's "measured,
not asserted" rule exists to catch — print the raw value before writing logic against
it, don't assume the client library normalized it into something more intuitive.

## Common mistakes

- **Using `GET`+increment-in-app-code instead of `INCR`.** If you ever find yourself doing
  `val = int(r.get(key)); r.set(key, val + 1)`, stop — that's the exact race `INCR` exists
  to prevent.
- **Forgetting `INCR` fails on non-numeric strings.** `SET x hello` then `INCR x` raises
  an error (`ERR value is not an integer or out of range`) — expected, but worth knowing
  before it surprises you in production logs.
- **Confusing `SETEX`'s argument order.** It's `SETEX key seconds value` — seconds *before*
  the value, the reverse of what `SET key value EX seconds` reads like. Easy to transpose.

## What's next

Level 03 moves past single strings into hashes, lists, and sets — Redis's structured
types for modeling an object, a queue, and a collection of unique items.
