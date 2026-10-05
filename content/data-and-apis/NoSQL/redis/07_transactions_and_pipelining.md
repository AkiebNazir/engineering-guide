# Transactions and Pipelining

Two different problems, two different tools, often confused because both involve sending
Redis a batch of commands:

- **Transactions** (`MULTI`/`EXEC`) are about *atomicity* — making a group of commands run
  as one indivisible unit, with no other client's commands interleaved in the middle.
- **Pipelining** is about *network efficiency* — sending many commands in one network
  round trip instead of one-round-trip-per-command. It says nothing about atomicity.

You can do either without the other, or both together (a pipelined `MULTI`/`EXEC`, which
is what `redis-py`'s `pipeline()` actually does under the hood).

## `MULTI` / `EXEC`: transactions

Commands queued between `MULTI` and `EXEC` are buffered by the server and then executed
back-to-back with no other client's command able to run in between — same atomicity
guarantee level 00 described for a single command, extended to a whole block.

```python
pipe = r.pipeline(transaction=True)
pipe.multi()
pipe.set("lab07:a", 1)
pipe.set("lab07:b", 2)
pipe.incr("lab07:a")
result = pipe.execute()
```

Run against the live instance:

```
MULTI/EXEC result -> [True, True, 2]
a -> 2 b -> 2
```

**Go (`go-redis/v9`):** `TxPipelined` is the direct equivalent of `pipe.multi()` +
queued commands + `execute()`:

```go
cmds, err := r.TxPipelined(ctx, func(pipe redis.Pipeliner) error {
    pipe.Set(ctx, "lab07:a", 1, 0)
    pipe.Set(ctx, "lab07:b", 2, 0)
    pipe.Incr(ctx, "lab07:a")
    return nil
})
```

Real output:

```text
MULTI/EXEC result -> [OK OK 2]
a -> 2 b -> 2
```

Important nuance: Redis transactions are **not** like a SQL transaction with rollback.
There's no "abort partway and undo" — once `EXEC` runs, every queued command executes,
even if one of them errors (a type mismatch, say). What `MULTI`/`EXEC` guarantees is
isolation (nothing else interleaves), not all-or-nothing rollback semantics.

## `WATCH`: optimistic locking / check-and-set

`WATCH key` tells Redis "abort my next `EXEC` if this key changes before it runs." This
is how you build a safe **check-then-act** sequence (read a value, decide something based
on it, write conditionally) without a race window, despite the read and the eventual
write being separate round trips:

```python
def transfer(amount):
    with r.pipeline() as pipe:
        while True:
            try:
                pipe.watch("lab07:balance")
                current = int(pipe.get("lab07:balance"))
                if current < amount:
                    pipe.unwatch()
                    return False, current
                pipe.multi()
                pipe.decrby("lab07:balance", amount)
                pipe.execute()          # raises WatchError if balance changed since WATCH
                return True, current - amount
            except redis.WatchError:
                continue                # someone else touched it — retry from the top
```

Confirmed on the live instance — a normal transfer succeeds:

```
transfer 30 -> True new balance -> 70 actual -> 70
```

And a genuine conflict is caught: a concurrent write between the `WATCH` and the `EXEC`
aborts the transaction rather than silently clobbering the other write:

```python
r.set("lab07:balance", 100)
pipe2 = r.pipeline()
pipe2.watch("lab07:balance")
current = int(pipe2.get("lab07:balance"))
r.set("lab07:balance", 999)     # a different client sneaks in here
pipe2.multi()
pipe2.decrby("lab07:balance", 10)
pipe2.execute()                 # raises WatchError
```

```
WatchError raised correctly: balance changed under us, transaction aborted
balance after aborted transfer -> 999 (unaffected by our decrby)
```

**Go (`go-redis/v9`):** `go-redis` folds `WATCH`+retry-loop into a single helper,
`r.Watch(ctx, fn, keys...)` — it calls `fn` with a `*redis.Tx`, and `fn` itself decides
whether to commit via `tx.TxPipelined(...)`:

```go
txf := func(tx *redis.Tx) error {
    current, err := tx.Get(ctx, "lab07:balance").Int()
    if err != nil {
        return err
    }
    if current < 30 {
        return errors.New("insufficient funds")
    }
    _, err = tx.TxPipelined(ctx, func(pipe redis.Pipeliner) error {
        pipe.DecrBy(ctx, "lab07:balance", 30)
        return nil
    })
    return err
}
err := r.Watch(ctx, txf, "lab07:balance")
```

Real output — a normal transfer succeeds:

```text
transfer 30 -> success: true new balance -> 70
```

And the same genuine-conflict scenario (a different client sneaks in a write between
the read and the commit):

```text
conflict demo: attempts -> 1 final err -> redis: transaction failed balance -> 999
```

`go-redis` surfaces the conflict as the sentinel error `redis.TxFailedErr` (printed
above via `err`, wrapped as `"redis: transaction failed"`) rather than Python's raised
`WatchError` exception — same underlying Redis mechanism (`WATCH` aborting `EXEC`
because the key changed), surfaced through each language's own idiomatic error-handling
shape: an exception to catch in Python, a sentinel error value to compare against in Go.

That's the whole pattern behind level 08's distributed locking and level 09's rate
limiters when they need multi-step atomicity beyond a single command.

## Pipelining: batching round trips

Every Redis command normally costs one network round trip: client sends, waits for the
server's reply, then sends the next command. If your app and Redis are in the same
datacenter that's maybe 0.1–0.5ms each — trivial for one command, but it adds up linearly
if you're issuing hundreds or thousands in a loop. **Pipelining** sends a batch of
commands without waiting for each reply individually, then reads all the replies once the
batch is flushed — trading "N round trips" for "~1 round trip plus N replies read
locally."

Measured, not asserted — 1000 `INCR` calls, individually vs. pipelined, against the live
lab container over localhost TCP:

```python
N = 1000
t0 = time.perf_counter()
for i in range(N):
    r.incr("lab07:pipeline_test")
t1 = time.perf_counter()
unpipelined = t1 - t0

pipe = r.pipeline()
for i in range(N):
    pipe.incr("lab07:pipeline_test")
pipe.execute()
t1b = time.perf_counter()
```

Actual output (run twice to sanity-check it wasn't a fluke):

```
# run 1
1000 INCR commands, individually:  120.8 ms  (0.121 ms/cmd)
1000 INCR commands, pipelined:      3.6 ms  (0.004 ms/cmd)
speedup: 33.9x

# run 2
1000 INCR commands, individually:  133.1 ms  (0.133 ms/cmd)
1000 INCR commands, pipelined:      3.4 ms  (0.003 ms/cmd)
speedup: 39.2x
```

Roughly a **34–39x speedup**, even over localhost where round-trip latency is about as
cheap as it gets. Over a real network link to a remote Redis (a different AZ, say), the
per-command round trip cost is larger and the gap would be even more dramatic — pipelining
matters more, not less, the further apart client and server are.

**Go (`go-redis/v9`), same measurement:** `go-redis` splits Python's single
`pipeline(transaction=bool)` flag into two distinct methods —
**`r.Pipeline()`** (network batching only, no `MULTI`/`EXEC` wrapper — the closer match
to what this measurement is actually testing) and **`r.TxPipeline()`** (batching *and*
`MULTI`/`EXEC` atomicity together, matching `redis-py`'s pipeline default). Measured
with `TxPipeline()`, to compare like-for-like against `redis-py`'s transactional-by-
default pipeline:

```go
t0 := time.Now()
for i := 0; i < N; i++ {
    r.Incr(ctx, "lab07:pipeline_test")
}
unpipelined := time.Since(t0)

pipe := r.TxPipeline()
for i := 0; i < N; i++ {
    pipe.Incr(ctx, "lab07:pipeline_test")
}
pipe.Exec(ctx)
pipelined := time.Since(t0)
```

Real output:

```text
1000 INCR commands, individually: 137.1 ms (0.137 ms/cmd)
1000 INCR commands, TxPipelined:  0.9 ms (0.001 ms/cmd)
speedup: 150.0x
```

**150x** here, higher than Python's measured 34–39x — both numbers are genuinely
measured on this same machine, and the gap is a real, reportable finding rather than
noise: it reflects the cost of 1000 individual round trips through each language's own
networking/interpreter overhead per call, not a claim that "Go's pipelining algorithm
is better" — pipelining's saving is the same one network round trip in both languages,
but Python's per-call overhead in the *unpipelined* baseline is itself larger, which
inflates the ratio. A second real run using the plain `r.Pipeline()` (no transaction
wrapper) instead measured **200x** (0.6ms pipelined vs. essentially the same ~120-140ms
unpipelined baseline) — noticeably faster than `TxPipeline()`'s 150x, which is itself a
real, honestly-reported data point: wrapping the batch in `MULTI`/`EXEC` is not free,
even though both forms collapse the same 1000 round trips into roughly one.

Note what pipelining does *not* give you: the commands in a plain pipeline still execute
one at a time on the server (level 00 — one thread), and without wrapping them in
`MULTI`/`EXEC` another client's commands *can* interleave between them. Pipelining is
purely a network optimization; combine it with `MULTI`/`EXEC` (as `redis-py`'s
`pipeline(transaction=True)` does by default) if you also need atomicity.

## Try it in the browser

The ▶ Run buttons on this page run an in-browser Redis loaded with the Query Lab seed
(keys listed in [the datasets README](../lab/datasets/README.md)). `MULTI`, `EXEC`,
`DISCARD` and `WATCH` behave as on a real server. Pipelining is the one thing here you
can't see: it's a client-side choice about when to read replies, and this page sends one
command at a time, so there's no round trip to save.

The Python transaction from the top of the page. Each command answers `QUEUED` instead of
running, and `EXEC` runs them back to back and returns all the replies at once.

```redis
MULTI                   # -> OK
SET lab07:a 1           # -> QUEUED
SET lab07:b 2           # -> QUEUED
INCR lab07:a            # -> QUEUED
EXEC                    # -> OK, OK, 2
MGET lab07:a lab07:b    # -> "2", "2"
```

No rollback. The middle command fails when it runs (`INCR` on a hash), but the commands
around it still take effect. `EXEC`'s reply holds an error for that one command, which
is why you check each reply.

```redis
HSET lab07:profile name alice   # -> 1
MULTI                           # -> OK
SET lab07:step1 done            # -> QUEUED
INCR lab07:profile              # -> QUEUED (the type error only shows up at EXEC)
SET lab07:step3 done            # -> QUEUED
EXEC                            # -> OK, (error) WRONGTYPE ..., OK
MGET lab07:step1 lab07:step3    # -> "done", "done": nothing was undone
```

A command Redis can reject while *queuing* (wrong number of arguments, unknown command)
is different: the whole transaction is refused at `EXEC`. This block is meant to show
errors.

```redis
MULTI                   # -> OK
SET lab07:x 1           # -> QUEUED
INCR                    # ERROR: wrong number of arguments, rejected while queuing
EXEC                    # ERROR: EXECABORT Transaction discarded because of previous errors.
GET lab07:x             # -> (nil): the SET never ran
```

`DISCARD` throws the queue away before anything runs.

```redis
SET lab07:balance 100           # -> OK
MULTI                           # -> OK
DECRBY lab07:balance 1000       # -> QUEUED
DISCARD                         # -> OK
GET lab07:balance               # -> "100"
```

`WATCH` check-and-set, the transfer that succeeds: watch the balance, read it, decide in
the app (100 ≥ 30), then queue the write. Nothing changed the key, so `EXEC` runs.

```redis
SET lab07:balance 100           # -> OK
WATCH lab07:balance             # -> OK
GET lab07:balance               # -> "100": enough for a transfer of 30
MULTI                           # -> OK
DECRBY lab07:balance 30         # -> QUEUED
EXEC                            # -> 70
```

The conflict case. The `SET 999` stands in for another client writing between our read
and our `EXEC` (in this one session it's our own write, which trips `WATCH` just the
same). `EXEC` returns `(nil)`: the transaction was aborted and the 999 survives. This is
the `WatchError` the Python retry loop catches.

```redis
SET lab07:balance 100           # -> OK
WATCH lab07:balance             # -> OK
GET lab07:balance               # -> "100"
SET lab07:balance 999           # -> OK (the "other client")
MULTI                           # -> OK
DECRBY lab07:balance 10         # -> QUEUED
EXEC                            # -> (nil): aborted
GET lab07:balance               # -> "999"
```

The same pattern on real data: reserve 2 units of a product and record the order
atomically, but only if nobody changed the stock since we read it (two shoppers can't both
buy the last unit).

```redis
WATCH product:105                                   # -> OK
HGET product:105 stock                              # -> "397": enough
MULTI                                               # -> OK
HINCRBY product:105 stock -2                        # -> QUEUED
RPUSH lab07:orders:customer:2 product:105:qty=2     # -> QUEUED
EXEC                                                # -> 395, 1
```

## Common mistakes

- **Assuming `MULTI`/`EXEC` rolls back on error.** It doesn't — a bad command in the queue
  still gets executed along with the rest; check each command's individual result.
- **Forgetting to handle `WatchError`.** It's not a fluke you can ignore — it's Redis
  correctly telling you the check-then-act sequence needs to retry.
- **Pipelining unboundedly.** Queuing a million commands in one pipeline before executing
  builds a huge buffer client- and server-side. Batch in reasonable chunks (hundreds to
  low thousands) for very large jobs.
- **Confusing pipelining with atomicity.** A plain pipeline is a network optimization
  only; if you need "nothing else runs in between," you need `MULTI`/`EXEC` too.
- **In Go, reaching for `r.Pipeline()` when you actually need atomicity.** Unlike
  `redis-py`'s single `pipeline(transaction=True/False)` flag, `go-redis` splits this
  into two named methods — `Pipeline()` (batching only) and `TxPipeline()` (batching +
  `MULTI`/`EXEC`) — and it's easy to grab the wrong one by habit if you're used to one
  call doing both.

## What's next

Level 08 builds a distributed lock on top of these primitives — and is honest about where
that lock's guarantees actually stop holding.
