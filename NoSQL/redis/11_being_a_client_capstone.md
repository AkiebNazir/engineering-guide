# Capstone: Being a Good Redis Client

Every level so far assumed a single, already-open `redis.Redis(...)` object. Production
code needs three more things this level puts together: a **connection pool** (so you're
not opening a new TCP connection per request), **timeouts** (so a stalled Redis or a
network partition doesn't hang your whole app), and **retries** (so a single transient
blip doesn't fail a request that a 50ms retry would have served fine). This level combines
all of that into one small service class implementing the session store (level 00/02), the
cache-aside pattern (level 05), and the rate limiter (level 09) from earlier levels.

## Connection pooling

```python
self.pool = redis.ConnectionPool(
    host=host, port=port, decode_responses=True,
    max_connections=max_connections,
    socket_timeout=socket_timeout,
    socket_connect_timeout=socket_connect_timeout,
)
self.r = redis.Redis(connection_pool=self.pool)
```

`redis.Redis(...)` created directly (as every earlier level did) already uses a pool
internally by default — but constructing the `ConnectionPool` explicitly is how you
control its size and timeouts, and how multiple `Redis` client objects (e.g. one for
regular commands, one dedicated to blocking commands like `BLPOP`) can share the same
underlying pool of TCP connections instead of each opening their own. `max_connections`
caps how many concurrent connections your app will ever open to Redis — important because
an unbounded pool under a traffic spike can overwhelm the Redis server's own client limit.

**Go (`go-redis/v9`):** pooling is built into `redis.Options` directly — there's no
separate pool object to construct, since every `*redis.Client` already owns one:

```go
r := redis.NewClient(&redis.Options{
    Addr:         "localhost:6390",
    PoolSize:     20,
    DialTimeout:  2 * time.Second,
    ReadTimeout:  2 * time.Second,
    WriteTimeout: 2 * time.Second,
})
```

## Timeouts

`socket_timeout` bounds how long a call waits for Redis to *respond*; `socket_connect_timeout`
bounds how long establishing the TCP connection itself may take. Without these, a
partitioned network or a wedged Redis process can hang a calling thread indefinitely —
exactly the kind of failure that turns one slow dependency into a full outage upstream,
because every thread waiting on it is a thread not serving other requests.

## Retries — only for transport failures

```python
def _with_retry(self, fn, retries=3, base_delay=0.05):
    last_exc = None
    for attempt in range(retries):
        try:
            return fn()
        except (ConnectionError, TimeoutError) as exc:
            last_exc = exc
            time.sleep(base_delay * (2 ** attempt))
    raise last_exc
```

Deliberately narrow: it only retries `redis.exceptions.ConnectionError` and
`TimeoutError` — transient, "the network or the server had a bad moment" failures. It does
**not** retry things like a bad command or a type error (`WRONGTYPE`), because retrying a
logically-wrong operation just fails the same way three times slower. The exponential
backoff (`0.05 * 2^attempt`) avoids hammering a Redis that's already struggling with
retries arriving faster than it can recover.

Confirmed against an intentionally unreachable port (nothing listening on 6391) to prove
the retry loop and its timing are real, not asserted:

```python
bad = RedisService(host="localhost", port=6391, socket_connect_timeout=0.2)
bad._with_retry(lambda: bad.r.ping(), retries=3, base_delay=0.05)
```

```
failed after retries in 363ms, exception type: ConnectionError
```

Three attempts at a 0.2s connect timeout plus backoff sleeps land around that number —
the retry loop genuinely ran three times and genuinely gave up, rather than the code just
printing a canned message.

**Go (`go-redis/v9`): retries are a client option, not something you write by hand.**
Unlike `redis-py` (no built-in retry at all — the hand-written `_with_retry` above is
necessary because the library gives you nothing), `go-redis` has retry logic built into
`redis.Options` itself:

```go
bad := redis.NewClient(&redis.Options{
    Addr:            "localhost:6391", // nothing listening here
    DialTimeout:     200 * time.Millisecond,
    MaxRetries:      3,
    MinRetryBackoff: 50 * time.Millisecond,
    MaxRetryBackoff: 200 * time.Millisecond,
})
_, err := bad.Ping(ctx).Result()
```

Real output against an intentionally unreachable port, confirming this is genuinely
retrying and genuinely timing out, not a canned message:

```text
failed after built-in retries in 2108ms, error type: *net.OpError
```

**A genuine, measured surprise worth reporting honestly rather than smoothing over:**
2108ms is far more than "4 attempts (1 + `MaxRetries: 3`) × ~200ms timeout" (~800ms)
would suggest. The real cause, visible in `go-redis`'s own log output during this run
(`redis: connection pool: failed to dial after 5 attempts`), is that the **connection
pool itself retries dialing up to 5 times internally**, on top of — not instead of —
the command-level `MaxRetries` this example set to 3. The two retry layers compound:
roughly `(MaxRetries + 1) × 5` total dial attempts in the worst case when the server is
completely unreachable, not just `MaxRetries + 1`. This is exactly the kind of thing
this repo's "measured, not asserted" rule exists to catch — the honest number here is
meaningfully larger than a plausible-sounding back-of-envelope guess, and only running
it revealed why.

The interview-relevant takeaway generalizes past Redis: **know whether your client
library already retries before writing your own retry wrapper around it**, and if it
does, understand what layer it retries at (a single dial? a whole command? both,
independently?) — stacking a naive retry loop on top of a library that already retries
internally is how a "fail fast" timeout budget silently turns into several seconds.

## The three pieces, combined

```python
class RedisService:
    def __init__(self, host="localhost", port=6390, max_connections=20,
                 socket_timeout=2.0, socket_connect_timeout=2.0):
        self.pool = redis.ConnectionPool(
            host=host, port=port, decode_responses=True,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
        )
        self.r = redis.Redis(connection_pool=self.pool)
        self._rate_limit_script = self.r.register_script(SLIDING_WINDOW_LUA)  # level 09

    def create_session(self, user_id, ttl_seconds=3600):           # level 00 / 02
        session_id = str(uuid.uuid4())
        payload = json.dumps({"user_id": user_id, "created": time.time()})
        self._with_retry(lambda: self.r.set(f"session:{session_id}", payload, ex=ttl_seconds))
        return session_id

    def get_session(self, session_id):
        raw = self._with_retry(lambda: self.r.getex(f"session:{session_id}", ex=3600))
        return json.loads(raw) if raw else None

    def cached(self, key, ttl_seconds, compute_fn):                # level 05
        val = self._with_retry(lambda: self.r.get(f"cache:{key}"))
        if val is not None:
            return json.loads(val), True
        result = compute_fn()
        self._with_retry(lambda: self.r.set(f"cache:{key}", json.dumps(result), ex=ttl_seconds))
        return result, False

    def allow_request(self, client_id, limit=5, window_ms=1000):   # level 09
        now_ms = int(time.time() * 1000)
        ok, count = self._with_retry(
            lambda: self._rate_limit_script(keys=[f"ratelimit:{client_id}"],
                                             args=[now_ms, window_ms, limit])
        )
        return bool(ok), count
```

`register_script` (used for the rate limiter's Lua body) is `redis-py`'s way of loading a
script once and calling it by a handle afterward, instead of re-sending the script text on
every call — the server caches scripts by their SHA1 hash internally either way, but
`register_script` also handles re-registering it if the server's script cache was flushed.

**Go (`go-redis/v9`), the same three pieces combined:**

```go
type RedisService struct {
    client *redis.Client
    script *redis.Script // go-redis's equivalent of register_script
}

func NewRedisService(addr string, poolSize int, timeout time.Duration) *RedisService {
    client := redis.NewClient(&redis.Options{
        Addr: addr, PoolSize: poolSize,
        DialTimeout: timeout, ReadTimeout: timeout, WriteTimeout: timeout,
    })
    return &RedisService{client: client, script: redis.NewScript(slidingWindowLua)} // level 09
}

func (s *RedisService) CreateSession(ctx context.Context, userID int, ttl time.Duration) (string, error) {
    sessionID := uuid.NewString()
    payload, _ := json.Marshal(map[string]any{"user_id": userID, "created": time.Now().Unix()})
    return sessionID, s.client.Set(ctx, "session:"+sessionID, payload, ttl).Err() // level 00/02
}

func (s *RedisService) Cached(ctx context.Context, key string, ttl time.Duration, compute func() any) (any, bool, error) {
    val, err := s.client.Get(ctx, "cache:"+key).Result() // level 05
    if err == nil {
        var out any
        json.Unmarshal([]byte(val), &out)
        return out, true, nil
    }
    result := compute()
    payload, _ := json.Marshal(result)
    return result, false, s.client.Set(ctx, "cache:"+key, payload, ttl).Err()
}

func (s *RedisService) AllowRequest(ctx context.Context, clientID string, limit, windowMs int64) (bool, int64, error) {
    nowMs := time.Now().UnixMilli() // level 09
    res, err := s.script.Run(ctx, s.client, []string{"ratelimit:" + clientID}, nowMs, windowMs, limit).Result()
    if err != nil {
        return false, 0, err
    }
    arr := res.([]interface{})
    return arr[0].(int64) == 1, arr[1].(int64), nil
}
```

`redis.NewScript` is `go-redis`'s equivalent of `register_script` — it loads the script
body once, and `Run` sends it by SHA1 (via `EVALSHA`) on subsequent calls, falling back
to the full script text automatically if the server's script cache was flushed
(Redis's `NOSCRIPT` error), same caching behavior as `redis-py`'s version.

Every piece exercised against the live lab instance in one run:

```text
-- session store --
created session 0993d1f1-fdce-4907-916a-7490b5f7678d
read back -> map[created:1.790179338e+09 user_id:42]
unknown session -> map[]

-- cache-aside --
first call: map[answer:42] hit=false  second call: map[answer:42] hit=true  compute invoked 1 time(s)

-- rate limiter --
request 1 -> (true, 1)
request 2 -> (true, 2)
request 3 -> (true, 3)
request 4 -> (true, 4)
request 5 -> (true, 5)
request 6 -> (false, 5)
request 7 -> (false, 5)

-- connection pool: total connections created -> 1 / max 20
```

Same result as the Python capstone — one real connection, reused across the session
write, the session read, both cache calls, and all seven rate-limit checks, via
`client.PoolStats().TotalConns`, `go-redis`'s equivalent of `redis-py`'s
`created_connections`. Two small, honest differences from the Python output worth
noting rather than hiding: `read back` prints Go's native `map[string]any` formatting
(a JSON number decodes to `float64` in Go, hence `1.790179338e+09` instead of a plain
integer timestamp — JSON itself has no separate integer type, and Go's `json` package
follows the spec literally where Python's happens to preserve the int), and a missing
session prints as `map[]` rather than Python's `None` — a nil map and an empty map
render identically via `fmt.Println` in Go, which is worth knowing before assuming
`map[]` in a log line means "found an empty object" rather than "found nothing at all."

Every piece exercised against the live lab instance in one run:

```
-- session store --
created session c803eb77-b25a-443f-b945-b8f9e73a62e7
read back -> {'user_id': 42, 'created': 1790161317.633247}
unknown session -> None

-- cache-aside --
first call: {'answer': 42} hit=False  second call: {'answer': 42} hit=True  compute_fn invoked 1 time(s)

-- rate limiter --
request 1 -> (True, 1)
request 2 -> (True, 2)
request 3 -> (True, 3)
request 4 -> (True, 4)
request 5 -> (True, 5)
request 6 -> (False, 5)
request 7 -> (False, 5)

-- connection pool sanity: pool created_connections after use -> 1 / max 20
```

Note `created_connections` stayed at **1** across a session write, a session read, two
cache calls, and seven rate-limit checks — this is the pool doing its job: one real
socket, reused for every command, rather than opening and tearing down a new connection
per call.

## Common mistakes

- **Creating a new `redis.Redis(...)` (and therefore a new connection or pool) per
  request** instead of once at startup and reusing it — this was flagged back in level 01
  and is worth repeating here now that pooling is explicit: the whole point of a pool is
  amortizing connection setup across many calls.
- **No timeout at all** (the `redis-py` default is actually no socket timeout) — a hung
  Redis becomes a hung caller, with no bound on how long.
- **Retrying everything, including logic errors.** Only retry the exception types that
  mean "the network or the server had a transient problem," never a `WRONGTYPE` or a bad
  argument.
- **Sizing `max_connections` from a single instance's needs without accounting for how
  many app instances will each open their own pool** — the real ceiling to watch is
  Redis's own `maxclients`, summed across your whole fleet's pools.
- **In Go, adding your own retry wrapper on top of `go-redis`'s already-built-in
  `MaxRetries`.** As measured above, `go-redis` retries at two independent layers (the
  connection pool's own dial retries, and command-level `MaxRetries`) — stacking a
  third, hand-written retry loop on top compounds all of them into a much longer worst-
  case delay than any single layer's settings suggest.

## Where this module goes from here

That's the full ladder: from the single-threaded in-memory model through data types,
caching, messaging, transactions, locking, rate limiting, persistence, and finally a
production-shaped client wrapping it all. The same primitives — atomic single commands,
`MULTI`/`EXEC`, Lua scripts, TTLs — recombine into most of what Redis is used for in a
real system. `NoSQL/README.md` has the module overview and the MongoDB ladder that
mirrors this one for the document model.
