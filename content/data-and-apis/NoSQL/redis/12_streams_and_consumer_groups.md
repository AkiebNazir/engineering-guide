# Streams and Consumer Groups

Level 06 ended on a hard limit: a pub/sub message that nobody is subscribed to at that
instant is gone, with no replay and no "catch up on what you missed." A **Redis Stream**
fixes that. It is a data type (a key, like a list or a hash) that holds an
**append-only log of entries**. Each entry is a small set of field/value pairs with a
unique, ordered ID. Reading an entry doesn't remove it, so any number of readers can walk
the same log at their own pace, and a reader that was offline picks up from the last ID it
saw.

On top of the log, **consumer groups** turn a stream into a work queue. A group splits
entries across several workers, tracks which entries each worker has been handed and not
yet confirmed, and lets another worker take over the entries of one that crashed. That
gives you **at-least-once delivery** inside Redis, without running Kafka or RabbitMQ.

Streams arrived in Redis 5.0. `XAUTOCLAIM` and `MINID` trimming came in 6.2, and in 7.0
`XAUTOCLAIM` started reporting deleted entries and `XINFO` gained the group `lag` field.
Everything below ran for real against this module's `redis:7` lab instance (port 6390).
The IDs in the output are real millisecond timestamps from that run, so yours will differ.

## Entry IDs: a timestamp and a sequence number

```text
> XADD lab12:cli * sensor t1 temp 21.5
"1790312026718-0"
> XADD lab12:cli * sensor t1 temp 21.7
"1790312026725-0"
> XLEN lab12:cli
(integer) 2
> XADD lab12:cli 5-0 sensor t1
(error) ERR The ID specified in XADD is equal or smaller than the target stream top item
```

`*` asks Redis to generate the ID. The format is `<milliseconds>-<sequence>`: the server's
Unix time in milliseconds, then a counter for entries added in the same millisecond. IDs
only ever go up, and that is enforced. An explicit ID at or below the stream's last one is
rejected, as the last command shows. If the server clock steps backwards, Redis keeps
using the last ID's millisecond part and bumps the sequence, so ordering holds anyway.

Two things follow from this, and both come up in interviews:

- **The ID is the cursor.** A reader keeps "the last ID I processed" and asks for
  everything after it. There's no separate offset bookkeeping like Kafka's.
- **The ID is a timestamp.** "Everything since 10:00" is a range query on IDs
  (`XRANGE key <ms-at-10:00> +`). Time-based retention (`MINID`, below) works the same
  way.

## Appending and reading: `XADD`, `XRANGE`, `XREAD`

```python
import redis
r = redis.Redis(host="localhost", port=6390, decode_responses=True)
for k in r.scan_iter("lab12:*"):
    r.delete(k)

ids = []
for i, (sku, qty) in enumerate([("book", 1), ("pen", 3), ("lamp", 1)]):
    ids.append(r.xadd("lab12:orders", {"order_id": 1000 + i, "sku": sku, "qty": qty}))
print("XADD ids ->", ids)
print("XLEN ->", r.xlen("lab12:orders"))

for entry_id, fields in r.xrange("lab12:orders", "-", "+"):
    print("  ", entry_id, fields)

print("XREAD from 0, COUNT 2 ->", r.xread({"lab12:orders": "0"}, count=2))
last_seen = ids[1]
print("XREAD after", last_seen, "->", r.xread({"lab12:orders": last_seen}))
print("XLEN after all those reads ->", r.xlen("lab12:orders"))
```

Real output:

```text
XADD ids -> ['1790311941351-0', '1790311941352-0', '1790311941352-1']
XLEN -> 3
   1790311941351-0 {'order_id': '1000', 'sku': 'book', 'qty': '1'}
   1790311941352-0 {'order_id': '1001', 'sku': 'pen', 'qty': '3'}
   1790311941352-1 {'order_id': '1002', 'sku': 'lamp', 'qty': '1'}
XREAD from 0, COUNT 2 -> [['lab12:orders', [('1790311941351-0', {'order_id': '1000', 'sku': 'book', 'qty': '1'}), ('1790311941352-0', {'order_id': '1001', 'sku': 'pen', 'qty': '3'})]]]
XREAD after 1790311941352-0 -> [['lab12:orders', [('1790311941352-1', {'order_id': '1002', 'sku': 'lamp', 'qty': '1'})]]]
XLEN after all those reads -> 3
```

The second and third entries landed in the same millisecond, so they got sequence numbers
`-0` and `-1`. And `XLEN` is still 3 after every read. This is the core difference from a
list used as a queue (`LPOP`/`BRPOP`, level 03), where reading an item removes it.

`XREAD` takes the ID to read **after**, which is exclusive. `0` means "from the
beginning." `$` means "only entries added after this call starts" and is meant for
`XREAD BLOCK <ms> STREAMS key $`, which blocks until something new arrives, like a
`SUBSCRIBE` that can also replay history. One trap: in a loop, pass `$` only on the first
call and then the last ID you received. Passing `$` every time skips whatever arrived
between two calls.

Plain `XREAD` is a **fan-out** read. Every reader sees every entry and tracks its own
position, so this is the "many independent subscribers, but durable" version of pub/sub.
To split work so each entry is handled by one worker, you need a consumer group.

## Consumer groups: split the work, track what's unconfirmed

```arch
%% caption: One stream, one consumer group. Each new entry is handed to exactly one consumer and sits in the group's pending list until that consumer ACKs it.
grid 190x120
node prod "Producers" at 1,0 icon=service sub="order service"
node s "Stream lab12:jobs" at 1,1 icon=stream sub="append-only log"
group g "Consumer group workers" color=pink icon=group
node pel "Pending entries list" at 1,2 in g icon=table sub="delivered, not ACKed"
node a "worker-a" at 0,3 in g icon=worker
node b "worker-b" at 1,3 in g icon=worker
node c "worker-c" at 2,3 in g icon=worker
prod -> s : "XADD"
s -> pel : "XREADGROUP >"
pel -> a : "jobs 0-2"
pel -> b : "jobs 3-5"
b ..> c : "XAUTOCLAIM idle"
```

A **consumer group** is a named cursor attached to a stream. It stores:

- **`last-delivered-id`**: the newest entry the group has handed out. `XREADGROUP ... >`
  means "give me entries after that," and each one goes to exactly **one** consumer in the
  group.
- **The pending entries list (PEL)**: every entry that was delivered to some consumer and
  not yet acknowledged with `XACK`, with the owning consumer, the time since last delivery
  (idle time), and a **delivery counter**.
- **Consumers**: named on first use. There is no registration step, so a consumer is just
  a name you pass to `XREADGROUP`.

Several groups can hang off the same stream, each with its own cursor and PEL. That's how
one stream serves both "billing processes every order once" and "analytics also processes
every order once" without the two affecting each other.

The whole lifecycle, on the live instance:

```python
import redis, time
r = redis.Redis(host="localhost", port=6390, decode_responses=True)
for k in r.scan_iter("lab12:*"):
    r.delete(k)

S, G = "lab12:jobs", "workers"
r.xgroup_create(S, G, id="$", mkstream=True)   # "$" = only entries added from now on
for n in range(6):
    r.xadd(S, {"job": n})

a = r.xreadgroup(G, "worker-a", {S: ">"}, count=3)
b = r.xreadgroup(G, "worker-b", {S: ">"}, count=3)
print("worker-a got jobs", [f["job"] for _, f in a[0][1]])
print("worker-b got jobs", [f["job"] for _, f in b[0][1]])
print("nothing left for a third read ->", r.xreadgroup(G, "worker-c", {S: ">"}, count=3))

# worker-a processes and ACKs all three; worker-b "crashes" after acking only one
print("XACK by a ->", r.xack(S, G, *[i for i, _ in a[0][1]]))
b_ids = [i for i, _ in b[0][1]]
print("XACK by b ->", r.xack(S, G, b_ids[0]))

print("XPENDING summary ->", r.xpending(S, G))
for p in r.xpending_range(S, G, min="-", max="+", count=10):
    print("  pending:", p["message_id"], "owner:", p["consumer"], "deliveries:", p["times_delivered"])
```

Real output:

```text
worker-a got jobs ['0', '1', '2']
worker-b got jobs ['3', '4', '5']
nothing left for a third read -> []
XACK by a -> 3
XACK by b -> 1
XPENDING summary -> {'pending': 2, 'min': '1790311952482-1', 'max': '1790311952482-2', 'consumers': [{'name': 'worker-b', 'pending': 2}]}
  pending: 1790311952482-1 owner: worker-b deliveries: 1
  pending: 1790311952482-2 owner: worker-b deliveries: 1
```

The same thing from `redis-cli`, so you can see the raw reply shapes:

```text
> XGROUP CREATE lab12:cli alerts 0
OK
> XREADGROUP GROUP alerts c1 COUNT 1 STREAMS lab12:cli >
1) 1) "lab12:cli"
   2) 1) 1) "1790312026718-0"
         2) 1) "sensor"
            2) "t1"
            3) "temp"
            4) "21.5"
> XPENDING lab12:cli alerts
1) (integer) 1
2) "1790312026718-0"
3) "1790312026718-0"
4) 1) 1) "c1"
      2) "1"
```

Jobs 4 and 5 are the point of all this. Level 06 showed that pub/sub would have lost them
outright. A plain `BRPOP` queue would have lost them too, because the pop already removed
them from Redis before worker-b crashed. Here they sit in the PEL, owned by worker-b, with
a delivery count of 1, waiting for one of two recovery paths.

### Recovery path 1: the same consumer restarts and re-reads its own PEL

`XREADGROUP` with an explicit ID instead of `>` doesn't fetch new entries. It returns
**this consumer's own pending entries** after that ID. A worker that restarts with a
stable name (hostname, pod name) should start with ID `0`, finish or fail everything it
still owns, and switch to `>` once that returns nothing:

```python
again = r.xreadgroup(G, "worker-b", {S: "0"})
print("worker-b re-reads its own PEL with id 0 ->", [f["job"] for _, f in again[0][1]])
```

```text
worker-b re-reads its own PEL with id 0 -> ['4', '5']
```

### Recovery path 2: another consumer claims entries that sat idle too long

If worker-b never comes back (the pod was rescheduled under a new name, say), its entries
would stay pending forever. `XAUTOCLAIM` scans the PEL and transfers ownership of every
entry idle longer than `min-idle-time` to the calling consumer, returning those entries
so it can process them:

```python
time.sleep(0.2)
nxt, claimed, deleted = r.xautoclaim(S, G, "worker-c", min_idle_time=100, start_id="0-0")
print("XAUTOCLAIM by worker-c -> claimed", [f["job"] for _, f in claimed], "next cursor", nxt, "deleted", deleted)
for p in r.xpending_range(S, G, min="-", max="+", count=10):
    print("  pending:", p["message_id"], "owner:", p["consumer"], "deliveries:", p["times_delivered"])
r.xack(S, G, *[i for i, _ in claimed])
print("after worker-c ACKs ->", r.xpending(S, G)["pending"], "pending")

info = r.xinfo_groups(S)[0]
print("XINFO GROUPS ->", {k: info[k] for k in ("name", "consumers", "pending", "last-delivered-id", "lag")})
```

```text
XAUTOCLAIM by worker-c -> claimed ['4', '5'] next cursor 0-0 deleted []
  pending: 1790311952482-1 owner: worker-c deliveries: 3
  pending: 1790311952482-2 owner: worker-c deliveries: 3
after worker-c ACKs -> 0 pending
XINFO GROUPS -> {'name': 'workers', 'consumers': 3, 'pending': 0, 'last-delivered-id': '1790311952482-2', 'lag': 0}
```

Details worth knowing:

- **The delivery counter went to 3.** Delivery 1 was worker-b's original read, delivery 2
  was worker-b's `0` re-read, and delivery 3 was the claim. Every hand-out counts, which
  is exactly what you need to detect a **poison message**: one that crashes every worker
  that touches it.
- **`XAUTOCLAIM` is a cursor scan.** It returns the ID to continue from (`0-0` means the
  scan wrapped around and is finished). Call it with `COUNT` (default 100) in a loop to
  walk a big PEL. `XCLAIM` is the older, explicit version: you name the IDs yourself,
  usually after inspecting `XPENDING`.
- **`min-idle-time` is your visibility timeout.** It is the same idea as SQS's visibility
  timeout. Set it comfortably above your slowest normal processing time, or a live but
  slow worker gets its entry stolen and the entry is processed twice.
- **`lag`** (Redis 7.0+) is how many entries in the stream the group hasn't been handed
  yet. It's the number to alert on, the same way you'd alert on consumer lag in Kafka.

### A worker loop with retries and a dead-letter stream

Putting both recovery paths and the delivery counter together gives the standard worker
shape. This is at-least-once processing with a cap on retries:

```python
import redis, time
r = redis.Redis(host="localhost", port=6390, decode_responses=True)
for k in r.scan_iter("lab12:*"):
    r.delete(k)

S, G, DLQ = "lab12:tasks", "billing", "lab12:tasks:dead"
MAX_DELIVERIES, MIN_IDLE_MS = 3, 50
r.xgroup_create(S, G, id="0", mkstream=True)
for n in range(5):
    r.xadd(S, {"task": n, "poison": int(n == 3)})

done = []
def handle(fields):
    if fields["poison"] == "1":
        raise ValueError("cannot parse task")
    done.append(fields["task"])

def run_once(consumer):
    # 1) recover entries left un-acked too long (by anyone, including this consumer)
    _, batch, _ = r.xautoclaim(S, G, consumer, min_idle_time=MIN_IDLE_MS, start_id="0-0", count=10)
    # 2) otherwise take new work, blocking up to 100 ms if there is none
    if not batch:
        resp = r.xreadgroup(G, consumer, {S: ">"}, count=10, block=100)
        batch = resp[0][1] if resp else []
    for entry_id, fields in batch:
        try:
            handle(fields)
            r.xack(S, G, entry_id)
        except Exception as exc:
            info = r.xpending_range(S, G, min=entry_id, max=entry_id, count=1)[0]
            if info["times_delivered"] >= MAX_DELIVERIES:
                r.xadd(DLQ, {**fields, "error": str(exc), "source_id": entry_id})
                r.xack(S, G, entry_id)
                print(f"  {entry_id} -> dead-lettered after {info['times_delivered']} deliveries")
            else:
                print(f"  {entry_id} failed (delivery {info['times_delivered']}), left pending")

for _ in range(5):
    run_once("worker-1")
    time.sleep(MIN_IDLE_MS / 1000 + 0.01)

print("processed:", done)
print("pending now:", r.xpending(S, G)["pending"])
print("dead-letter stream:", [f for _, f in r.xrange(DLQ)])
```

Real output:

```text
  1790311983191-3 failed (delivery 1), left pending
  1790311983191-3 failed (delivery 2), left pending
  1790311983191-3 -> dead-lettered after 3 deliveries
processed: ['0', '1', '2', '4']
pending now: 0
dead-letter stream: [{'task': '3', 'poison': '1', 'error': 'cannot parse task', 'source_id': '1790311983191-3'}]
```

Task 3 failed on each delivery, was retried each time `XAUTOCLAIM` found it idle, and was
moved to a separate stream on its third failure. The other four went through untouched.
Without the cap, one bad message would loop forever and keep a worker busy. Note that
`XADD` to the DLQ followed by `XACK` is two commands. A crash between them leaves the
entry both dead-lettered and still pending, so it will be dead-lettered again later. The
fix is the one that applies to the whole design: **handlers must be idempotent**. A
`MULTI`/`EXEC` (level 07) or a Lua script can make the pair atomic when that matters.

**Go (`go-redis/v9`):** the same consumer-group lifecycle. `XReadGroup` with `Block` set
returns `redis.Nil` when the block times out with nothing new, and that's a normal
"no work" signal, not a failure:

```go
package main

import (
	"context"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

func jobs(msgs []redis.XMessage) []any {
	out := []any{}
	for _, m := range msgs {
		out = append(out, m.Values["job"])
	}
	return out
}

func main() {
	ctx := context.Background()
	r := redis.NewClient(&redis.Options{Addr: "localhost:6390"})
	defer r.Close()

	const S, G = "lab12:gojobs", "workers"
	r.Del(ctx, S)
	r.XGroupCreateMkStream(ctx, S, G, "$")
	for n := 0; n < 6; n++ {
		r.XAdd(ctx, &redis.XAddArgs{Stream: S, Values: map[string]any{"job": n}})
	}

	read := func(consumer string) []redis.XMessage {
		res, err := r.XReadGroup(ctx, &redis.XReadGroupArgs{
			Group: G, Consumer: consumer, Streams: []string{S, ">"}, Count: 3, Block: 100 * time.Millisecond,
		}).Result()
		if err == redis.Nil { // BLOCK timed out with nothing new
			return nil
		}
		return res[0].Messages
	}
	a, b := read("worker-a"), read("worker-b")
	fmt.Println("worker-a got jobs", jobs(a))
	fmt.Println("worker-b got jobs", jobs(b))

	for _, m := range a {
		r.XAck(ctx, S, G, m.ID)
	}
	r.XAck(ctx, S, G, b[0].ID) // worker-b acks one, then "crashes"

	p, _ := r.XPending(ctx, S, G).Result()
	fmt.Println("pending:", p.Count, "by consumer:", p.Consumers)

	time.Sleep(200 * time.Millisecond)
	claimed, next, err := r.XAutoClaim(ctx, &redis.XAutoClaimArgs{
		Stream: S, Group: G, Consumer: "worker-c", MinIdle: 100 * time.Millisecond, Start: "0-0",
	}).Result()
	fmt.Println("XAUTOCLAIM by worker-c -> claimed", jobs(claimed), "next cursor", next, "err", err)
	for _, m := range claimed {
		r.XAck(ctx, S, G, m.ID)
	}
	p, _ = r.XPending(ctx, S, G).Result()
	fmt.Println("pending after worker-c ACKs:", p.Count)
}
```

Real output:

```text
worker-a got jobs [0 1 2]
worker-b got jobs [3 4 5]
pending: 2 by consumer: map[worker-b:2]
XAUTOCLAIM by worker-c -> claimed [4 5] next cursor 0-0 err <nil>
pending after worker-c ACKs: 0
```

Same server behavior, same split, same recovery. Stream field values come back as strings
on the wire (you `XADD` an int and read `"4"`), in Go exactly as in Python.

## Trimming: a stream grows until you cap it

Reading never removes entries, and neither does `XACK`. It only clears the PEL record.
Left alone, a stream grows until Redis hits `maxmemory`, so every production stream needs
a retention policy, applied either on each `XADD` or with a periodic `XTRIM`:

```python
seen_exact, seen_approx = set(), set()
for n in range(1000):
    r.xadd("lab12:exact", {"n": n}, maxlen=100, approximate=False)   # MAXLEN 100
    r.xadd("lab12:approx", {"n": n}, maxlen=100, approximate=True)   # MAXLEN ~ 100
    seen_exact.add(r.xlen("lab12:exact")); seen_approx.add(r.xlen("lab12:approx"))
print("MAXLEN 100   -> XLEN ranged", min(x for x in seen_exact if x >= 100), "to", max(seen_exact), "once full")
print("MAXLEN ~ 100 -> XLEN ranged", min(x for x in seen_approx if x >= 100), "to", max(seen_approx), "once full")
print("stream-node-max-entries ->", r.config_get("stream-node-max-entries"))

# Time-based retention: IDs start with a ms timestamp, so MINID = "drop older than"
r.xadd("lab12:ttl", {"n": "old"}, id="1000-0")
r.xadd("lab12:ttl", {"n": "old2"}, id="2000-0")
r.xadd("lab12:ttl", {"n": "new"}, id="5000-0")
print("XTRIM MINID 3000 removed ->", r.xtrim("lab12:ttl", minid="3000", approximate=False),
      "left:", [f["n"] for _, f in r.xrange("lab12:ttl")])
```

```text
MAXLEN 100   -> XLEN ranged 100 to 100 once full
MAXLEN ~ 100 -> XLEN ranged 100 to 199 once full
stream-node-max-entries -> {'stream-node-max-entries': '100'}
XTRIM MINID 3000 removed -> 2 left: ['new']
```

Why the approximate form ranged up to 199: internally a stream is a **radix tree of
macro-nodes**, each a packed block (a listpack) of up to `stream-node-max-entries` entries
(100 by default) or `stream-node-max-bytes` (4 KB by default). Removing a whole node is
cheap. Removing part of one means rewriting it. `MAXLEN ~ 100` tells Redis it may keep
"at least 100" and only drop whole nodes, so the length saw-tooths between 100 and just
under 200. That's what you want in production: the cap is a memory bound, not an exact
business rule, and the approximate form avoids rewriting a node on almost every `XADD`.
Use the exact form only when the exact count actually matters.

### Trimming doesn't care about consumer groups

This is the sharp edge. Trimming deletes entries whether or not a group has delivered or
acknowledged them:

```python
S, G = "lab12:trim", "g"
r.xgroup_create(S, G, id="$", mkstream=True)
for n in range(5):
    r.xadd(S, {"n": n})
r.xreadgroup(G, "w1", {S: ">"}, count=5)       # 5 delivered, none ACKed
r.xtrim(S, maxlen=2, approximate=False)         # keep only the newest 2
print("XLEN after trim ->", r.xlen(S), "| still pending in PEL ->", r.xpending(S, G)["pending"])
time.sleep(0.05)
nxt, claimed, deleted = r.xautoclaim(S, G, "w2", min_idle_time=10, start_id="0-0")
print("XAUTOCLAIM claimed", len(claimed), "| deleted (trimmed while pending)", len(deleted))
print("PEL after XAUTOCLAIM cleaned up ->", r.xpending(S, G)["pending"])
```

```text
XLEN after trim -> 2 | still pending in PEL -> 5
XAUTOCLAIM claimed 2 | deleted (trimmed while pending) 3
PEL after XAUTOCLAIM cleaned up -> 2
```

Three unprocessed entries were trimmed away. The PEL kept pointing at them until
`XAUTOCLAIM` noticed they no longer exist, reported their IDs in the third return value
(Redis 7.0+), and dropped them from the PEL. The work itself is gone. So size the cap
from the **worst consumer lag you need to survive** (an outage of the consumer fleet at
peak write rate), not from normal steady state, and alert on the group's `lag` well before
it approaches the cap. Redis 8.2 added trimming and deletion options that take consumer
groups into account (`KEEPREF`/`DELREF`/`ACKED` on `XADD`/`XTRIM`, plus `XDELEX` and
`XACKDEL`). On 7.x, which this lab runs, the rule above applies.

## Durability and scaling: it's still Redis

A stream is only as durable as the Redis holding it:

- **Persistence.** Entries live in memory and survive a restart only through RDB/AOF
  (level 10). With `appendfsync everysec`, a crash can lose up to about a second of
  `XADD`s *and* `XACK`s. A lost `XACK` means a redelivery, which is fine if handlers are
  idempotent. A lost `XADD` is a lost message.
- **Replication is asynchronous.** An `XADD` acknowledged by the primary can disappear in
  a failover if the replica hadn't received it yet. `WAIT 1 100` after the `XADD` narrows
  that window (it blocks until one replica has the write), but it doesn't make Redis a
  consensus-replicated log.
- **One stream is one key, so it lives on one shard.** In Redis Cluster a hot stream
  doesn't spread across nodes. To scale writes, split into N streams yourself
  (`orders:{0}` … `orders:{N-1}`, choosing by a hash of the order ID) and run a group on
  each. At that point you're hand-building Kafka-style partitions.
- **Memory is the ceiling.** Retention is bounded by RAM, so hours or days of events at
  moderate rates, not months of history.

## Streams vs. pub/sub vs. lists vs. Kafka

| | Pub/Sub (level 06) | List queue (`LPUSH`/`BRPOP`, level 03) | Redis Stream + consumer group | Kafka |
|---|---|---|---|---|
| Message kept after delivery | No. Gone if nobody's listening | No. The pop removes it | **Yes**, until trimmed | **Yes**, until retention (time/size) |
| Replay / late readers | No | No | Yes, from any ID | Yes, from any offset |
| Fan-out to independent readers | Yes | No (one pop wins) | Yes: one group per reader type, or plain `XREAD` | Yes: one consumer group per reader type |
| Work split inside a group | n/a | Competing poppers | **Per entry**: any consumer can get any entry | **Per partition**: one consumer owns a partition |
| Ack / crash recovery | None | None built in (`BLMOVE` to a processing list, by hand) | **PEL + `XACK` + `XAUTOCLAIM`**, delivery counts | Commit offsets; uncommitted messages are re-read after a rebalance |
| Ordering | Per channel, live only | FIFO | Stream order, but parallel consumers finish out of order | Strict within a partition |
| Scale-out | Channel per node | One key, one shard | One key, one shard; shard manually | Partitions spread across brokers |
| Retention bound | None (nothing stored) | RAM | RAM | Disk, commonly TBs, with tiered storage |

The practical rule of thumb:

- **Pub/sub** for disposable, live-only signals.
- **Streams** when you already run Redis and need a durable, replayable queue or event
  log at moderate volume, with per-message acks and redelivery. Typical cases are job
  queues, webhook fan-out, activity feeds, and IoT readings over a bounded window.
- **Kafka** (or Kinesis/Pulsar) when you need long retention on disk, very high
  throughput spread over many brokers, strict per-key ordering with parallelism
  (partition by key), or an ecosystem (Connect, Streams, schema registry). Kafka's
  per-partition model buys ordering at the cost of per-message flexibility: one slow or
  poisoned message blocks its partition. The Streams PEL handles that one message
  individually.

## Try it in the browser

The ▶ Run buttons on this page run an in-browser Redis loaded with the Query Lab seed,
which includes `stream:orders`: the shop's last 40 orders as events, with fixed IDs, so
the replies below are predictable (see [the datasets README](../lab/datasets/README.md)).
Everything except blocking (`BLOCK` returns at once here) works as on the lab Redis,
including consumer groups, the PEL and `XAUTOCLAIM`. Writes stay in this page's session.

IDs first, as in the `redis-cli` transcript at the top. `*` generates a
`<ms>-<seq>` ID from the clock, and an explicit ID at or below the last one is rejected.
This block is meant to end with an error.

```redis
XADD lab12:cli * sensor t1 temp 21.5    # -> an ID like "1790312026718-0"
XADD lab12:cli * sensor t1 temp 21.7    # -> a larger ID ("-1" if in the same millisecond)
XLEN lab12:cli                          # -> 2
XADD lab12:cli 5-0 sensor t1            # ERROR: The ID specified in XADD is equal or smaller than the target stream top item
```

The seed's order stream. Read the oldest two entries, the newest one, and a time range:
the IDs are millisecond timestamps, so "orders between two instants" is an `XRANGE` on
IDs (a bare number means "any sequence in that millisecond").

```redis
XLEN stream:orders                                      # -> 40
XRANGE stream:orders - + COUNT 2                        # -> orders 14564 and 14563
XREVRANGE stream:orders + - COUNT 1                     # -> the newest order, 14598
XRANGE stream:orders 1767020400000 1767022920000        # -> the 3 orders in that window
```

`XREAD` is the plain fan-out read: give it the last ID you processed and it returns what
came after. Reading removes nothing, so `XLEN` is still 40, and any number of readers can
do this independently.

```redis
XREAD COUNT 2 STREAMS stream:orders 0                   # -> orders 14564 and 14563
XREAD COUNT 2 STREAMS stream:orders 1767020400000-0     # -> orders 14566 and 14565: after the last ID seen
XLEN stream:orders                                      # -> 40
```

A consumer group splits the work instead. Create `billing` at `0` (start from the
beginning of the stream), and two workers each take three orders with `>` ("entries never
delivered to this group"). They get different orders.

```redis
XGROUP CREATE stream:orders billing 0                               # -> OK
XREADGROUP GROUP billing worker-a COUNT 3 STREAMS stream:orders >   # -> orders 14564, 14563, 14566
XREADGROUP GROUP billing worker-b COUNT 3 STREAMS stream:orders >   # -> orders 14565, 14562, 14568
```

worker-a finishes and acknowledges all three; worker-b acknowledges one and "crashes".
`XPENDING` shows the two entries still owned by worker-b: the summary, then each entry's
owner, idle milliseconds and delivery count.

```redis
XACK stream:orders billing 1767001920000-0 1767020400000-0 1767022260000-0  # -> 3
XACK stream:orders billing 1767022920000-0                                  # -> 1
XPENDING stream:orders billing                                              # -> 2 pending, all worker-b's
XPENDING stream:orders billing - + 10                                       # -> each delivered once so far
```

Recovery path 1: worker-b restarts under the same name and reads its own PEL with ID `0`
instead of `>`. Recovery path 2: worker-c takes over whatever has been idle at least
`min-idle-time` ms. In production that's your visibility timeout (say `60000`); it's `0`
here so you don't have to wait. Notice the delivery count reach 3 (b's read, b's re-read,
c's claim), and the `0-0` cursor meaning the scan is finished.

```redis
XREADGROUP GROUP billing worker-b STREAMS stream:orders 0   # -> orders 14562 and 14568 again
XAUTOCLAIM stream:orders billing worker-c 0 0-0             # -> "0-0", both entries, (empty array)
XPENDING stream:orders billing - + 10                       # -> owner worker-c, 3 deliveries each
XACK stream:orders billing 1767033180000-0 1767035340000-0  # -> 2
XPENDING stream:orders billing                              # -> 0 pending
```

Time-based retention: IDs start with a timestamp, so `XTRIM ... MINID` means "drop
everything older than this".

```redis
XADD lab12:ttl 1000-0 n old             # -> "1000-0"
XADD lab12:ttl 2000-0 n old2            # -> "2000-0"
XADD lab12:ttl 5000-0 n new             # -> "5000-0"
XTRIM lab12:ttl MINID 3000              # -> 2
XRANGE lab12:ttl - +                    # -> only "5000-0" is left
```

The sharp edge from "Trimming doesn't care about consumer groups". Five entries are
delivered and none acknowledged, then the stream is trimmed to 2. The PEL still lists all
5 until `XAUTOCLAIM` finds that 3 of them no longer exist: it claims the 2 that do and
reports the 3 trimmed IDs in its third reply. That work is lost.

```redis
XGROUP CREATE lab12:trim g $ MKSTREAM                   # -> OK
XADD lab12:trim 1-0 n 0                                 # -> "1-0"
XADD lab12:trim 2-0 n 1                                 # -> "2-0"
XADD lab12:trim 3-0 n 2                                 # -> "3-0"
XADD lab12:trim 4-0 n 3                                 # -> "4-0"
XADD lab12:trim 5-0 n 4                                 # -> "5-0"
XREADGROUP GROUP g w1 COUNT 5 STREAMS lab12:trim >      # -> all 5, none ACKed
XTRIM lab12:trim MAXLEN 2                               # -> 3
XPENDING lab12:trim g                                   # -> 5 still pending
XAUTOCLAIM lab12:trim g w2 0 0-0                        # -> "0-0", entries 4-0 and 5-0, deleted 1-0 2-0 3-0
XPENDING lab12:trim g                                   # -> 2
```

## Common mistakes

- **Never trimming.** An untrimmed stream is a memory leak with a delay. Put `MAXLEN ~ N`
  or `MINID ~ <id>` on the `XADD`, or run `XTRIM` on a schedule.
- **Trimming tighter than the worst-case lag.** As shown above, trimming deletes pending,
  unprocessed entries without warning on Redis 7.x.
- **Never reading the PEL.** A worker that only ever calls `XREADGROUP ... >` never sees
  its own unacked entries again after a restart. Start with ID `0`, or run `XAUTOCLAIM`
  in the loop.
- **Random consumer names per process start.** Every restart creates a new consumer and
  orphans the old one's PEL until something claims it. Use stable names, and delete dead
  consumers with `XGROUP DELCONSUMER` (which discards their pending entries, so claim
  them first).
- **`min-idle-time` shorter than real processing time.** Slow but healthy workers get
  their entries claimed out from under them, and every such entry is processed twice.
- **Assuming exactly-once.** Consumer groups give at-least-once delivery. Crashes between
  "did the work" and `XACK` cause redelivery, so make handlers idempotent (dedupe on the
  entry ID or a business key, for example with `SET dedupe:<id> 1 NX EX 86400` before
  doing the work).
- **Passing `$` to `XREAD` on every loop iteration**, which silently skips entries that
  arrived between calls. Use the last seen ID.
- **Using `XREADGROUP ... NOACK` and expecting recovery.** `NOACK` skips the PEL entirely,
  which makes it pub/sub-like at-most-once delivery with history.

## Interview questions

**"How would you build a reliable job queue on Redis?"** A stream plus a consumer group.
Producers `XADD` with `MAXLEN ~`. Workers loop `XAUTOCLAIM` (recover idle entries) then
`XREADGROUP ... > BLOCK`, and `XACK` after the work succeeds. Use the delivery counter
from `XPENDING` to move poison messages to a dead-letter stream after N attempts, make
handlers idempotent because delivery is at-least-once, and alert on the group's `lag`.

**"What's the PEL, and what happens if a consumer dies?"** The pending entries list is
the group's record of entries delivered but not acknowledged: entry ID, owner, idle time,
delivery count. When a consumer dies, its entries stay in the PEL. Either it restarts
under the same name and re-reads them with `XREADGROUP ... 0`, or another consumer takes
them with `XAUTOCLAIM`/`XCLAIM` once they've been idle longer than the visibility
timeout.

**"Pub/sub or Streams for order events?"** Streams. Pub/sub drops anything published
while a subscriber is disconnected. A stream keeps the entry until it's trimmed, and a
group redelivers unacked entries.

**"Why not just use Redis Streams instead of Kafka?"** Often you can, at moderate volume
with retention measured in hours or days. Kafka wins when you need disk-backed retention
at TB scale, throughput spread across many brokers, per-key ordering with parallel
consumers, or replicated durability that doesn't depend on async replication plus fsync
settings. A Redis stream is a single key on a single shard, bounded by RAM.

**"How are stream IDs generated, and why does that matter?"** `<ms timestamp>-<sequence>`,
strictly increasing and enforced by the server. The ID doubles as the read cursor and as
a timestamp, which gives time-range queries (`XRANGE`) and time-based retention
(`MINID`) for free.

## What's next

This level completes the messaging story that level 06 started. For the broader design
question of when a system needs a queue or log at all, see
[Messaging and Streaming](../../../interview-core/SystemDesign/building_blocks/09_messaging_and_streaming.md),
and for how a Kafka-style partitioned, replicated log works inside, see
[Distributed Log Internals](../../../interview-core/SystemDesign/building_blocks/26_distributed_log_internals.md).
[NoSQL — Document and Key-Value Stores, Hands-On](../README.md) has the rest of the module.
