# Caching Patterns

Everything up to here was Redis's data types. This level is about the *pattern* most
people actually reach for Redis to build: a cache sitting in front of a slower system of
record (a database, an external <abbr title="Application Programming Interface">API</abbr>). The data type barely matters (usually a plain
string holding serialized JSON); what matters is **who writes to the cache, and when**.

## Three patterns

```arch
%% caption: Cache-aside: the app reads the cache, falls back to the DB on a miss, then populates the cache itself.
grid 220x120
group ca "Cache-aside (lazy loading)" color=blue icon=cache
node app "App" at 0,0 in ca icon=app
node cache "Cache" at 1,0 in ca icon=cache
node db "DB" at 0,1 in ca icon=db
app:R -> cache:L : "1. read"
app -> db : "2. miss: read"
app:T -> cache:T : "3. populate"
```

**Cache-aside** (a.k.a. lazy loading): the application checks the cache first; on a miss,
it reads the real source, then writes the result into the cache for next time. The cache
never talks to the DB directly — the app is the one holding both connections and doing
the orchestration. This is the pattern used in most apps because it's simple and the
cache can be down without breaking writes.

```python
def cache_aside_get(product_id, ttl=30):
    key = f"lab05:product:{product_id}"
    cached = r.get(key)
    if cached is not None:
        return cached, True          # hit
    value = slow_db_lookup(product_id)   # the real, slow source
    r.set(key, value, ex=ttl)
    return value, False              # miss
```

Run against the live instance, with a fake 50ms "DB":

```
first call: hit=False value=product-9-data took=56.5ms
second call: hit=True value=product-9-data took=0.6ms
```

Roughly a 90x speedup on the cached path in this run — the actual number depends on how
slow the real backend is, but the shape (miss pays full cost once, every hit after is
near-free) is the whole point of the pattern.

**Go (`go-redis/v9`):**

```go
func cacheAsideGet(ctx context.Context, r *redis.Client, productID int, ttl time.Duration) (string, bool) {
    key := fmt.Sprintf("lab05:product:%d", productID)
    cached, err := r.Get(ctx, key).Result()
    if err == nil {
        return cached, true // hit
    }
    value := slowDBLookup(ctx, productID)
    r.Set(ctx, key, value, ttl)
    return value, false // miss
}
```

Real output, same fake 50ms "DB":

```text
first call: hit=false value=product-9-data took=53.6ms
second call: hit=true value=product-9-data took=0.5ms
```

Roughly a **107x** speedup this run — a `Get` returning `redis.Nil` (not a Go `error`
in the everyday sense, see level 01) is the miss signal here, the same role `None` plays
in the Python version.

**Write-through**: the application writes to the cache *and* the DB together, as part of
the same write path, so the cache is never stale — every write updates both. Costs extra
write latency (you're writing twice) in exchange for cache data that's always fresh.

**Write-back** (write-behind): the application writes only to the cache, which
acknowledges immediately; the cache (or a background process) flushes to the DB
asynchronously later. Fastest writes, but you can lose the unflushed data if the cache
crashes before the flush — a real durability tradeoff, not free performance.

| Pattern | Write path | Staleness risk | Data-loss risk |
|---|---|---|---|
| Cache-aside | App → DB (cache only touched on read-miss) | Stale until TTL expires or explicit invalidation | None (cache is disposable) |
| Write-through | App → Cache and DB together | Never stale | None |
| Write-back | App → Cache only, async flush later | Never stale (from the cache's view) | Yes, if the cache dies before flushing |

Redis itself doesn't enforce any of these — they're an application-level discipline about
who calls `SET` and when. Redis just provides the fast key-value layer underneath.

<div class="lab" data-viz="flow-cache-aside"></div>

## TTL-based expiry and eviction

TTL (level 01/02) handles per-key staleness: cached data automatically disappears after
`ex` seconds, forcing a refresh on the next read. But TTL doesn't handle **running out of
memory** — for that, Redis has `maxmemory` and `maxmemory-policy`.

```bash
CONFIG GET maxmemory-policy
```

Checked on the live lab instance:

```
current maxmemory-policy -> {'maxmemory-policy': 'noeviction'}
```

**Go:** `r.ConfigGet(ctx, "maxmemory-policy").Result()` → real output:
`current maxmemory-policy -> map[maxmemory-policy:noeviction]` — same fact, `go-redis`
returns Redis's `CONFIG GET` reply as a plain `map[string]string`.

`noeviction` is the default — once `maxmemory` is hit, writes start failing outright.
For a pure cache, that's almost never what you want. The common choice is
`allkeys-lru`: when memory is full, evict the **least recently used** key across the
whole keyspace to make room, regardless of TTL. Other policies exist (`allkeys-lfu` —
least *frequently* used; `volatile-lru`/`volatile-ttl` — only evict keys that have a TTL
set, leaving permanent keys alone) — `allkeys-lru` is the sane default for "this Redis
instance is purely a cache, nothing in it is precious."

```bash
CONFIG SET maxmemory 256mb
CONFIG SET maxmemory-policy allkeys-lru
```

## The cache stampede problem

Picture a popular cache key with a 60-second TTL. At the instant it expires, if the app
is getting steady traffic, **every concurrent request in that instant** sees a miss at
the same time and all of them hit the slow backend simultaneously — a "stampede" that can
take the real database down right when the cache was supposed to be protecting it.

Two practical fixes:

**1. TTL jitter** — instead of every key set in the same window expiring at exactly the
same instant, add a small random amount to each TTL so expirations spread out over time
instead of clustering:

```python
r.set(key, value, ex=base_ttl + random.randint(0, 5))
```

Demonstrated on the live instance — five keys set in the same instant, with and without
jitter:

```
no-jitter TTLs (all identical) -> [10, 10, 10, 10, 10]
jittered TTLs (spread out)     -> [13, 10, 13, 10, 10]
```

**Go (`go-redis/v9`):**

```go
jitter := time.Duration(rand.Intn(6)) * time.Second
r.Set(ctx, key, "v", 10*time.Second+jitter)
```

Real output, five keys set in the same instant:

```text
no-jitter TTLs (all identical) -> [10 10 10 10 10]
jittered TTLs (spread out)     -> [13 15 13 13 10]
```

Five identical TTLs will all expire in the same Redis event loop tick under load; the
jittered ones expire across a 5-second window instead, so at most a fraction of that
traffic ever hits a simultaneous miss.

**2. Locking (a.k.a. "single-flight" / mutex on rebuild)** — on a miss, before hitting the
slow backend, try to atomically acquire a short-lived lock for that specific key
(`SET lock:key 1 NX PX 5000`, see level 08). Whoever gets the lock rebuilds the cache;
everyone else either waits briefly and retries the cache read, or serves slightly-stale
data if one is cached under a secondary "stale-ok" key. This trades a small amount of
latency for the guarantee that only one request ever rebuilds a given key at a time.

Jitter is cheap and handles the common case (steady traffic). Locking is the stronger fix
for a genuinely hot key under high concurrency, at the cost of the added complexity in
level 08.

## Common mistakes

- **No TTL at all on cache entries.** A cache-aside key with no expiry never refreshes —
  you've built a permanent, silently-stale copy of your data, not a cache.
- **Leaving `maxmemory-policy` at `noeviction` for a pure cache.** Under memory pressure
  this turns into write failures across your whole app instead of graceful eviction.
- **Assuming cache-aside alone prevents stampedes.** It doesn't — every one of N
  concurrent requests on a miss will independently go to the DB unless you add jitter or
  locking.
- **Caching errors.** If `slow_db_lookup` fails, don't cache the failure — you'll serve a
  cached error for the whole TTL window instead of recovering on the next successful call.

## What's next

Level 06 covers pub/sub — Redis's fire-and-forget messaging primitive, and when you'd
reach for Streams instead.
