# Pub/Sub

Redis pub/sub is a message broadcast primitive: a publisher sends a message to a
**channel**, and every client currently subscribed to that channel receives it. It has
nothing to do with the key-value store — messages are not stored as keys, don't show up
in `KEYS`, and aren't affected by `maxmemory-policy`.

```arch
%% caption: Redis Pub/Sub Broadcast Pattern
node pub1 "Publisher 1" at 0,0 icon=client
node pub2 "Publisher 2" at 0,2 icon=client
node chan "Channel:\nupdates" at 2,1 shape=pill color=pink
node sub1 "Subscriber A" at 4,0 icon=worker
node sub2 "Subscriber B" at 4,1 icon=worker
node sub3 "Subscriber C" at 4,2 icon=worker

pub1 -> chan : "PUBLISH"
pub2 -> chan : "PUBLISH"
chan -> sub1 : "broadcast"
chan -> sub2 : "broadcast"
chan -> sub3 : "broadcast"
```

## `PUBLISH` / `SUBSCRIBE`

```bash
# terminal 1
SUBSCRIBE lab06:channel

# terminal 2
PUBLISH lab06:channel "hello subscribers"
```

In Python:

```python
# subscriber
p = r.pubsub()
p.subscribe("lab06:channel")
for msg in p.listen():
    if msg["type"] == "message":
        print("got:", msg["data"])

# publisher (different connection/process)
r.publish("lab06:channel", "hello subscribers")
```

`PUBLISH` returns the number of clients that received the message — useful as a live
signal, not a durability guarantee.

## The critical property: fire-and-forget, no persistence

This is the thing to internalize before using pub/sub for anything real: **a message that
nobody is subscribed to receive is gone.** There's no queue backing it, no replay, no
"catch up on what you missed." If your subscriber's connection dropped for two seconds
and three messages were published during that window, that subscriber simply never sees
them — not delayed, not buffered, just gone.

Demonstrated on the live instance — two scenarios:

```python
import redis, time, threading
r = redis.Redis(host="localhost", port=6390, decode_responses=True)

# Demo 1: a listener that IS subscribed before the publish
received = []
def listener():
    p = r.pubsub()
    p.subscribe("lab06:channel")
    for msg in p.listen():
        if msg["type"] == "message":
            received.append(msg["data"])
            break

t = threading.Thread(target=listener)
t.start()
time.sleep(0.3)
n = r.publish("lab06:channel", "hello subscribers")
t.join(timeout=2)
print("PUBLISH return value ->", n)
print("actually received ->", received)

# Demo 2: publish with nobody subscribed
n2 = r.publish("lab06:channel", "did anyone hear this?")
print("PUBLISH with zero listeners -> return value:", n2)
```

Output:

```
PUBLISH return value -> 1
actually received -> ['hello subscribers']
PUBLISH with zero listeners -> return value: 0 (0 = nobody got it, and it's gone)
```

`PUBLISH` returning `0` isn't an error — it's Redis honestly telling you "nobody was
listening," and the message is not retrievable afterward by any means. There is no
`SUBSCRIBE` option that means "and also give me what I missed."

**Go (`go-redis/v9`):** `go-redis`'s pub/sub <abbr title="Application Programming Interface">API</abbr> is shaped very differently from
Python's blocking `for msg in p.listen()` loop — `Subscribe` returns a `*PubSub` whose
`.Channel()` method gives you an ordinary Go channel of messages, meant to be read from
inside a goroutine (or a `select`), which fits Go's concurrency model far more
naturally than a blocking iterator does:

```go
sub := r.Subscribe(ctx, "lab06:channel")
_, _ = sub.Receive(ctx) // wait for the subscription itself to be confirmed
ch := sub.Channel()

received := make(chan string, 1)
go func() {
    msg := <-ch
    received <- msg.Payload
}()

time.Sleep(300 * time.Millisecond)
n, _ := r.Publish(ctx, "lab06:channel", "hello subscribers").Result()
fmt.Println("PUBLISH return value ->", n)
fmt.Println("actually received ->", <-received)
sub.Close()

// Demo 2: publish with nobody subscribed
n2, _ := r.Publish(ctx, "lab06:channel", "did anyone hear this?").Result()
fmt.Println("PUBLISH with zero listeners -> return value:", n2)
```

Real output:

```text
PUBLISH return value -> 1
actually received -> hello subscribers
PUBLISH with zero listeners -> return value: 0
```

Identical Redis-level behavior — the fire-and-forget, no-persistence guarantee (or
lack of one) is a property of Redis itself, not of either client library. What differs
is purely how each language's client exposes it: Python blocks a thread inside
`p.listen()`; Go hands you a channel and expects you to `select` on it alongside
whatever else your goroutine needs to watch (a shutdown signal, a timeout, other
channels) — the idiomatic Go shape for "wait for one of several things."

## What pub/sub is actually good for

Anything where losing a message under a brief disconnect is acceptable, because the
information is either transient or has another source of truth:

- Broadcasting a "cache key X was invalidated, refresh your local copy" notice to a fleet
  of app servers — if one server missed it, its stale copy just lives a bit longer, no
  correctness violation.
- Live UI updates (a chat "user is typing" indicator, a live dashboard tick) — the next
  update supersedes a missed one anyway.
- A simple internal signal ("a new deploy just happened, drop your connection pools").

## When you need actual delivery guarantees: Redis Streams

If a subscriber missing a message would actually break something — an order-processing
event, a task that must run exactly once, an audit event — pub/sub is the wrong tool.
**Redis Streams** (`XADD`/`XREAD`/`XGROUP`, not covered in depth in this module) is
Redis's durable alternative: messages are appended to a persisted, replayable log with
IDs, consumer groups can each track their own read position, and a consumer that was
offline can catch up on everything it missed when it reconnects. That's a fundamentally
different data structure and <abbr title="Application Programming Interface">API</abbr> from pub/sub, not a configuration flag on it.

The rule of thumb: reach for **pub/sub** when the message is disposable and "eventually
consistent, or don't care" is fine; reach for **Streams** (or a dedicated queue like
Kafka/RabbitMQ/SQS) the moment "what if a subscriber was briefly down" has a wrong
answer for your use case.

## Common mistakes

- **Using pub/sub as a task queue.** If the one worker that should process a job is
  restarting when it's published, the job is lost forever — use a list (level 03,
  `BLPUB`/`BRPOP`) or Streams for anything that must be processed at least once.
- **Assuming `PUBLISH`'s return value means "delivered and processed."** It only means "N
  clients were subscribed at that instant" — nothing about whether their handler code
  ran successfully afterward.
- **Forgetting a subscriber connection can silently drop.** Production pub/sub consumers
  need reconnect-and-resubscribe logic; a dropped connection isn't retried automatically,
  and everything published during the gap is unrecoverable.
- **In Go, never calling `sub.Close()`.** An unclosed `*PubSub` leaks both its
  underlying connection and the goroutine reading from `.Channel()` if nothing is ever
  sent again — always `defer sub.Close()` right after `Subscribe`, the same discipline
  as closing a file or an <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> response body.

## What's next

Level 07 covers transactions (`MULTI`/`EXEC`), optimistic locking with `WATCH`, and a
real measured demonstration of what pipelining buys you.
