# Connecting and Your First Command

This module assumes the shared lab database from `docker-compose.databases.yml` at the
repo root is running:

```bash
docker compose -f docker-compose.databases.yml up -d
```

That starts a real `redis:7` container, mapped to **host port 6390** (not the Redis
default 6379, so it never collides with a Redis you already run natively). It has no
password — fine for a local throwaway lab, never do this in production.

## Connecting with `redis-cli`

`redis-cli` is Redis's own command-line client. If you have it installed locally:

```bash
redis-cli -p 6390
```

If you don't have a local binary, run it inside the container instead — this is what was
used to verify every command in this file:

```bash
docker exec -it dsa-redis redis-cli
```

Either way you land in an interactive prompt. You can also run one-off commands without
entering the prompt, which is how these docs demonstrate output:

```bash
$ docker exec dsa-redis redis-cli SET foo bar
OK
$ docker exec dsa-redis redis-cli GET foo
bar
```

## `SET` and `GET`

Redis's whole <abbr title="Application Programming Interface">API</abbr> is a big menu of commands over the shape `COMMAND key [args...]`. The
two you'll use most:

```bash
SET foo bar        # store the string "bar" under key "foo"
GET foo            # -> "bar"
GET missing_key    # -> (nil)   — reading a key that was never set is not an error
```

## Key expiry: `EXPIRE` and `TTL`

Keys live forever by default. `EXPIRE` attaches a countdown (in seconds) to an existing
key; Redis deletes it automatically when the countdown hits zero.

```bash
$ docker exec dsa-redis redis-cli SET foo bar
OK
$ docker exec dsa-redis redis-cli EXPIRE foo 100
(integer) 1
$ docker exec dsa-redis redis-cli TTL foo
(integer) 100
```

`TTL key` tells you how many seconds are left: a positive number counting down, `-1` if
the key exists but has no expiry, `-2` if the key doesn't exist at all. This distinction
(`-1` vs `-2`) is worth memorizing — code that treats both as "not expiring" will
misbehave on typos.

Cleanup: `DEL foo` removes a key immediately, expiry or not.

## Connecting from Python with `redis-py`

Interactive `redis-cli` is for exploring. Real applications use a client library —
`redis-py` (`pip install redis`) is the standard one for Python.

```python
import redis

r = redis.Redis(host="localhost", port=6390, decode_responses=True)
```

`decode_responses=True` matters: without it, every string Redis returns comes back as
`bytes` (`b"bar"`), because Redis itself is byte-string-oriented and doesn't know about
Python's `str`. Setting it makes the client decode to `str` for you, at the cost of
assuming <abbr title="Unicode Transformation Format. A family of character encodings capable of encoding all possible Unicode code points.">UTF</abbr>-8-safe data (fine for this module; a binary blob store would leave it off).

The following was run against the live lab instance to confirm real behavior — not just
described:

```python
import redis, time

r = redis.Redis(host="localhost", port=6390, decode_responses=True)
r.delete("lab01:greeting")

r.set("lab01:greeting", "hello redis")
print("GET ->", r.get("lab01:greeting"))

r.expire("lab01:greeting", 5)
print("TTL right after EXPIRE 5 ->", r.ttl("lab01:greeting"))
time.sleep(2)
print("TTL after sleeping 2s ->", r.ttl("lab01:greeting"))
time.sleep(4)
print("GET after the key should have expired ->", r.get("lab01:greeting"))
```

Actual output from running this against the lab container:

```
GET -> hello redis
TTL right after EXPIRE 5 -> 5
TTL after sleeping 2s -> 3
GET after the key should have expired -> None
```

Notice `redis-py` maps Redis's `(nil)` to Python's `None` — that's the client library's
job, translating the wire protocol into idiomatic values for the language.

## Connecting from Go with `go-redis`

`github.com/redis/go-redis/v9` (`go get github.com/redis/go-redis/v9`) is the standard
Go client, used throughout this module:

```go
import "github.com/redis/go-redis/v9"

r := redis.NewClient(&redis.Options{Addr: "localhost:6390"})
```

Every `go-redis` call takes a `context.Context` as its first argument — that's how
timeouts and cancellation propagate (level 11 covers this properly); a bare
`context.Background()` is fine for these small demos. Run against the live lab
instance, reproducing the same TTL sequence as the Python demo above:

```go
ctx := context.Background()
r.Del(ctx, "lab01:greeting")

r.Set(ctx, "lab01:greeting", "hello redis", 0)
val, _ := r.Get(ctx, "lab01:greeting").Result()
fmt.Println("GET ->", val)

r.Expire(ctx, "lab01:greeting", 5*time.Second)
ttl, _ := r.TTL(ctx, "lab01:greeting").Result()
fmt.Println("TTL right after Expire 5s ->", ttl)

time.Sleep(2 * time.Second)
ttl2, _ := r.TTL(ctx, "lab01:greeting").Result()
fmt.Println("TTL after sleeping 2s ->", ttl2)

time.Sleep(4 * time.Second)
_, err := r.Get(ctx, "lab01:greeting").Result()
if err == redis.Nil {
    fmt.Println("GET after the key should have expired -> redis.Nil (key does not exist)")
}
```

Real output from running this against the live lab instance:

```text
GET -> hello redis
TTL right after Expire 5s -> 5s
TTL after sleeping 2s -> 3s
GET after the key should have expired -> redis.Nil (key does not exist)
```

Where `redis-py` maps Redis's `(nil)` to Python's `None`, `go-redis` maps it to the
sentinel error value `redis.Nil` — Go has no universal "nullable" return, so a missing
key surfaces through the same `(value, error)` pair every other call returns, and you
check for this *specific* error rather than treating every error alike (see "Common
mistakes" below). Also notice `TTL` comes back as an idiomatic `time.Duration`
(`5s`, `3s`), not a bare integer of seconds — `go-redis` converts the wire protocol's
integer into Go's native duration type for you.

## Common mistakes

- **Forgetting `decode_responses=True`** and then being confused why `r.get("x") == "x"`
  is `False` (it's `b"x"`, not `"x"`).
- **Treating `-1` and `-2` TTL the same.** `-1` = "this key has no expiry, it's
  permanent." `-2` = "this key doesn't exist." Very different failure modes if your code
  assumes a session key is still alive.
- **One global client per app, not one per request.** `redis.Redis(...)` is safe to share
  across threads and reuse — it manages a connection pool internally (more in level 11).
  Creating a new client (and new <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> connection) per request is a common performance bug.
- **In Go, checking `err != nil` for "key doesn't exist" instead of `err == redis.Nil`.**
  A missing key is not a failure — it's `go-redis`'s normal way of returning "nothing
  here," and code that treats it the same as a real connection error will misreport a
  cache miss as an outage.

## What's next

Level 02 goes deeper on strings: atomic counters (`INCR`/`DECR`), and the different ways
to combine a value with an expiry (`SETEX`, `GETEX`).
