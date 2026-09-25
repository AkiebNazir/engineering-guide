# Hashes, Lists, and Sets

A single string per key gets you a dictionary of scalars. Real applications need more
shapes: an object with fields, an ordered sequence, a collection with no duplicates.
Redis has a native type for each, and — same theme as level 02 — the operations on them
are atomic single commands, not "fetch the whole thing, mutate it in your app, write it
all back."

## Hashes: model an object without serializing it

A **hash** is a field → value map living under one key — like a mini row, or a small
<abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> object, except Redis knows about the individual fields, so you can read or update
one field without touching the rest.

```python
r.hset("lab03:user:42", mapping={"name": "Ana", "email": "ana@example.com", "logins": 7})
r.hgetall("lab03:user:42")
# {'name': 'Ana', 'email': 'ana@example.com', 'logins': '7'}
r.hget("lab03:user:42", "name")
# 'Ana'
r.hincrby("lab03:user:42", "logins", 1)   # atomic per-field increment
r.hget("lab03:user:42", "logins")
# '8'
```

Run against the live instance, confirming the above:

```
HGETALL -> {'name': 'Ana', 'email': 'ana@example.com', 'logins': '7'}
HGET name -> Ana
HGET logins after HINCRBY -> 8
```

**Go (`go-redis/v9`):**

```go
r.HSet(ctx, "lab03:user:42", map[string]interface{}{"name": "Ana", "email": "ana@example.com", "logins": 7})
all, _ := r.HGetAll(ctx, "lab03:user:42").Result()
name, _ := r.HGet(ctx, "lab03:user:42", "name").Result()
r.HIncrBy(ctx, "lab03:user:42", "logins", 1)
logins, _ := r.HGet(ctx, "lab03:user:42", "logins").Result()
```

Real output:

```text
HGETALL -> map[email:ana@example.com logins:7 name:Ana]
HGET name -> Ana
HGET logins after HIncrBy -> 8
```

`HGetAll` returns a plain `map[string]string` — every hash field value comes back as a
string regardless of what you stored (the `logins: 7` you set arrives back as the
string `"7"`, same as `redis-py`'s behavior); Go has no dynamic typing to paper over
this, so converting numeric fields is always an explicit `strconv.Atoi` in your own
code, not something the client infers for you.

**Hash vs. a <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> string in a plain key**: if you `SET user:42 '{"name": "Ana", ...}'`,
bumping `logins` means fetching the whole blob, parsing it in your app, incrementing, and
writing the whole thing back — not atomic, and wasteful for a 1-field change on a large
object. A hash lets `HINCRBY` touch just that field, atomically, in one round trip. Use a
hash when you need to read/write individual fields; use a plain string when you always
read/write the whole object as a unit anyway.

## Lists: a queue and a stack

A Redis **list** is a doubly-linked list of strings, with O(1) push/pop at *either* end
(`LPUSH`/`RPUSH`/`LPOP`/`RPOP`) and O(n) random access (`LRANGE`, `LINDEX`) — so use it
for sequential access patterns, not as an array you index into randomly.

**As a <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr> queue** (push at the tail, process from the head — first in, first out):

```python
r.rpush("lab03:queue", "job1", "job2", "job3")
r.lrange("lab03:queue", 0, -1)   # peek the whole list: ['job1', 'job2', 'job3']
r.lpop("lab03:queue")            # 'job1' — process the oldest job first
```

**As a <abbr title="Last-In, First-Out. A method for processing data where the last items entered are the first to be removed, characteristic of stack data structures.">LIFO</abbr> stack** (push and pop from the same end — last in, first out):

```python
r.lpush("lab03:stack", "a", "b", "c")   # each LPUSH goes to the head, so order is reversed
r.lrange("lab03:stack", 0, -1)          # ['c', 'b', 'a']
r.lpop("lab03:stack")                   # 'c' — the most recently pushed item
```

Confirmed output:

```
queue LRANGE -> ['job1', 'job2', 'job3']
LPOP (process job1) -> job1
queue after pop -> ['job2', 'job3']
stack LRANGE -> ['c', 'b', 'a']
LPOP (most recent) -> c
```

**Go (`go-redis/v9`):**

```go
r.RPush(ctx, "lab03:queue", "job1", "job2", "job3")
q, _ := r.LRange(ctx, "lab03:queue", 0, -1).Result()
popped, _ := r.LPop(ctx, "lab03:queue").Result()

r.LPush(ctx, "lab03:stack", "a", "b", "c")
s, _ := r.LRange(ctx, "lab03:stack", 0, -1).Result()
spop, _ := r.LPop(ctx, "lab03:stack").Result()
```

Real output:

```text
queue LRange -> [job1 job2 job3]
LPop (process job1) -> job1
queue after pop -> [job2 job3]
stack LRange -> [c b a]
LPop (most recent) -> c
```

The direction of push/pop is the whole difference between a queue and a stack — same
data structure, two different access patterns. In production you'd typically use
`BLPOP`/`BRPOP` (blocking pop — wait for an item instead of polling) for a real job
queue, so a worker doesn't spin in a tight loop when the queue is empty.

## Sets: unique members, with set algebra

A Redis **set** is an unordered collection of unique strings — `SADD` is a no-op if the
member is already present. The payoff is O(1) membership tests (`SISMEMBER`) and native
set operations across multiple keys:

```python
r.sadd("lab03:setA", "python", "go", "rust")
r.sadd("lab03:setB", "go", "rust", "typescript")

r.sinter("lab03:setA", "lab03:setB")   # intersection: in both
r.sunion("lab03:setA", "lab03:setB")   # union: in either
r.sdiff("lab03:setA", "lab03:setB")    # difference: in A but not B
```

Confirmed output:

```
SMEMBERS A -> ['go', 'python', 'rust']
SINTER A,B (common) -> ['go', 'rust']
SUNION A,B (all unique) -> ['go', 'python', 'rust', 'typescript']
SDIFF A,B (in A not B) -> ['python']
```

**Go (`go-redis/v9`):**

```go
r.SAdd(ctx, "lab03:setA", "python", "go", "rust")
r.SAdd(ctx, "lab03:setB", "go", "rust", "typescript")

inter, _ := r.SInter(ctx, "lab03:setA", "lab03:setB").Result()
union, _ := r.SUnion(ctx, "lab03:setA", "lab03:setB").Result()
diff, _ := r.SDiff(ctx, "lab03:setA", "lab03:setB").Result()
```

Real output:

```text
SMEMBERS A -> [python go rust]
SINTER A,B -> [go rust]
SUNION A,B -> [python go rust typescript]
SDIFF A,B -> [python]
```

Notice `SMEMBERS A` came back in a *different* order here (`[python go rust]`) than in
the Python run above (`['go', 'python', 'rust']`) — real output from the same set,
proving the "common mistakes" point below rather than just asserting it: a Redis set
has no guaranteed iteration order in any client language, so never write code (or a
test) that depends on the order `SMEMBERS`/`SMembers` returns.

A real use: "users who both liked post X and follow user Y" is `SINTER liked:X
following:Y` — one command, computed server-side, instead of pulling both sets into your
app and intersecting them in a loop.

## Common mistakes

- **Reaching for a list when you need random access.** `LINDEX`/`LSET` at an arbitrary
  offset are O(n) — a list is for sequential access at the ends, not an array.
- **Storing a whole object as a <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> string when you only ever update one field.** That's
  what hashes are for — see the `HINCRBY` example above.
- **`SMEMBERS` on a huge set.** It returns everything in one shot and blocks the single
  event-loop thread (level 00) for the duration. `SSCAN` cursors through a large
  collection instead of materializing it all at once.
- **Assuming set members are ordered.** They aren't — if you need order, that's a sorted
  set (next level).

## What's next

Level 04 covers sorted sets — sets with a score attached to every member — which is how
Redis builds leaderboards, priority queues, and anything else that needs "give me the
top N by some numeric value."
