# Distributed Locking

Sometimes you need "only one process, anywhere in the fleet, does this thing right now" —
a cron job that must not double-run across replicas, a resource that must not be modified
by two workers at once. Redis's atomicity (level 00) makes it a natural place to
implement this. It is also a place where it's easy to be *more confident than the
guarantee actually deserves* — so this level ends with the honest limits, not just the
happy path.

## The `SET key value NX PX milliseconds` pattern

```python
import uuid

def acquire(lock_key, ttl_ms=5000):
    token = str(uuid.uuid4())           # a value unique to THIS acquisition attempt
    ok = r.set(lock_key, token, nx=True, px=ttl_ms)
    return token if ok else None
```

Three pieces doing three separate jobs, all in one atomic command:

- **`NX`** ("only if the key does not already exist") is the actual lock: it fails if
  someone else holds it, atomically — no separate "check, then set" race, because it's
  one server-side command (level 00 again).
- **`PX milliseconds`** is a safety-net expiry: if the holder crashes or hangs before
  releasing, the lock self-destructs instead of being held forever.
- **A random unique token as the value** is what makes release *safe* — see below.

Confirmed on the live instance:

```
client A acquired -> True
client B tries to acquire same lock while held -> None
```

**Go (`go-redis/v9`):** `SetNX` maps directly onto `SET key value NX` — the `PX`
milliseconds part is just the `time.Duration` argument, same as every other TTL-bearing
call in this module:

```go
func acquire(ctx context.Context, r *redis.Client, lockKey string, ttl time.Duration) (string, bool) {
    token := uuid.NewString()
    ok, _ := r.SetNX(ctx, lockKey, token, ttl).Result()
    return token, ok
}
```

Real output:

```text
client A acquired -> true
client B tries to acquire same lock while held -> false
```

`go-redis`'s `SetNX` returns a plain `bool` for "did this acquire," where `redis-py`'s
`r.set(..., nx=True)` returns the token or `None` — same information, a Go-idiomatic
`(value, ok)`-shaped return instead of Python's "falsy sentinel" convention.

## Releasing safely: don't just `DEL`

The naive release is `r.delete(lock_key)`. The bug: if your process was slow (a GC pause,
a network stall) and the lock's TTL already expired, releasing by plain `DEL` might delete
a lock that a *different* client has since legitimately acquired — you'd release someone
else's lock, and now two clients both believe they hold it.

The fix is a **compare-and-delete**, done atomically with a small Lua script (Redis
guarantees a Lua script runs as one atomic unit, same as `MULTI`/`EXEC`):

```python
RELEASE_SCRIPT = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
else
    return 0
end
"""

def release(lock_key, token):
    return r.eval(RELEASE_SCRIPT, 1, lock_key, token)
```

Confirmed:

```
release with WRONG token -> 0 (0 = refused)
lock still held? -> True
release with correct token -> 1
```

**Go (`go-redis/v9`):** the same compare-and-delete Lua script, unmodified, run via
`r.Eval`:

```go
const releaseScript = `
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
else
    return 0
end
`

func release(ctx context.Context, r *redis.Client, lockKey, token string) int64 {
    res, _ := r.Eval(ctx, releaseScript, []string{lockKey}, token).Result()
    return res.(int64)
}
```

Real output:

```text
release with WRONG token -> 0
lock still held? -> true
release with correct token -> 1
```

Note the Lua script itself is byte-for-byte identical between the Python and Go
versions — Lua scripts run *inside Redis*, so the calling language is irrelevant to the
script's own logic; only the client-side call to invoke it differs.

And the TTL safety net actually works if a holder never releases at all:

```
orphan lock present -> True
orphan lock present after TTL -> False
```

**Go:**

```go
r.SetNX(ctx, orphanKey, uuid.NewString(), 1*time.Second)
```

Real output: `orphan lock present -> true` immediately after acquiring, then
`orphan lock present after TTL -> false` after sleeping past the 1-second TTL — same
guarantee, same mechanism, Redis's own expiry doing the work regardless of which
client set the key.

## The Redlock disagreement — and why it matters here

Redis's creator (antirez) proposed **Redlock**: to make this pattern safe against a
*single Redis node* dying, acquire the same lock against N independent Redis nodes (say
5) and consider it held only if you get a majority (3 of 5) within a time budget. The
idea is that a single node's failure shouldn't compromise the lock's safety, the same
argument behind any quorum system.

Martin Kleppmann published a widely-discussed critique of Redlock's *safety* claims
(not just efficiency). The actual argument, stripped to its core:

- Redlock's safety proof assumes that once a client's lock TTL expires from its own point
  of view, no *other* process can still believe that same client legitimately holds the
  lock and act on that belief. That assumption quietly depends on clocks and process
  execution behaving within bounds.
- In the real world, that assumption can break in two independent ways:
  1. **Clock jumps.** If a node's system clock jumps forward (NTP correction, manual
     admin action, a VM being paused and resumed), a lock can appear expired to the
     algorithm sooner than the holder's actual elapsed wall-clock work — the lock frees up
     while the original holder is still working under the assumption it's still valid.
  2. **Process pauses.** A GC pause, a disk stall, a hypervisor CPU steal, or just an OS
     scheduling a process out for longer than expected can freeze a client between "I
     confirmed I hold the lock" and "I actually perform the protected action." The lock's
     TTL can expire *during that pause*, another client acquires it and starts working,
     and then the first client wakes up and finishes its now-unsafe action — believing,
     correctly at the time it checked, that it held the lock.
- Redlock's majority-of-5-nodes construction defends against a Redis node failing, but it
  does **nothing** about either of those — the failure mode isn't "Redis lied," it's
  "wall-clock time and real execution time diverged from what the algorithm assumed."

antirez's response, in essence: Redlock was never claimed to be a substitute for a proper
consensus-based fencing mechanism for hard correctness guarantees (like Chubby or a
database's own transactional guarantees); it's a best-effort lock for reducing the
*likelihood* of concurrent access in practice, and for many real use cases (a
best-effort "don't run this cron job twice, but a rare double-run is a minor
inconvenience, not data corruption") that's an acceptable, useful tool.

**The practical takeaway, independent of who's more "right":** a Redis lock (single-node
`SET NX PX` or multi-node Redlock) tells you "very probably, only one holder at a time."
It does not give you the airtight guarantee a fencing token backed by a linearizable store
(like a monotonically increasing counter checked by the resource itself) can give you.

## When NOT to rely on Redis locking for correctness-critical work

Reach for something stronger than a Redis lock when the cost of a rare double-execution
is genuinely unacceptable — moving money, issuing a single physical resource, anything
where "this happened exactly once" is a hard business invariant. In those cases:

- Use a **fencing token**: every lock acquisition returns a strictly increasing number,
  and the *protected resource itself* rejects any write tagged with an older token than
  one it's already seen. This defends against the exact GC-pause scenario above — even if
  a paused client wakes up and acts late, its stale token gets rejected by the resource,
  not just by the lock.
- Or push the mutual-exclusion requirement into the system that must already be
  authoritative for that data (a database transaction, a uniqueness constraint,
  optimistic concurrency control at the row level) instead of a side-channel lock.

Redis locking is a good, cheap tool for "reduce the odds of two workers stepping on each
other" when a rare miss is tolerable. It's the wrong tool when a miss is a P0 incident.

## Common mistakes

- **Releasing with plain `DEL` instead of the token-checked script.** This is the bug that
  makes a stale client release someone else's active lock.
- **Setting the TTL too short relative to the actual work.** If the protected operation
  can occasionally take longer than the TTL, you get exactly the "two holders at once"
  failure mode Kleppmann describes — size the TTL with real margin, and consider
  extending it (a "lock renewal" heartbeat) for long-running work.
- **Treating a successful acquire as a permanent guarantee.** It's a snapshot-in-time
  belief; a slow client can still act after its lock has logically expired underneath it.
- **Reaching for Redlock as a knee-jerk "more nodes = safer" upgrade** without reading
  what it does and does not defend against — it raises availability (survives a node
  loss) more than it raises the correctness ceiling described above.

## What's next

Level 09 applies the same atomic-command toolkit to a much more common production need:
rate limiting shared across every instance of your app, not just one process.
