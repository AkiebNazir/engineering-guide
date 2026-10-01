# API Design — High Level

The API is the contract your service makes with every caller — browser, mobile app, another team's service, or a third party. Get the contract wrong and you can't fix it without breaking someone; this file is about the contract itself. Wire-level mechanics (status codes, headers, serialization formats, auth tokens) live in [API Design — Low Level](04_api_design_low_level.md).

It starts with what a contract contains and how to design one from the caller's side, then goes
as deep as a senior design round: pagination and N+1 queries measured, rate-limiting algorithms
compared against an adversarial client, a table of compatible and breaking changes, and a complete
worked API design.

## Foundations — What an API Contract Contains

### More than a list of endpoints

An API contract is every promise a caller can observe and come to depend on:

| Part | Examples | What goes wrong if it's left implicit |
|---|---|---|
| **Operations** | Create an order, list a user's orders, cancel an order | Endpoints mirror database tables, so callers must make five calls and know your schema |
| **Data shapes** | Field names, types, which fields are required, units, time zones | `amount` in cents on one endpoint and dollars on another |
| **Semantics** | Is this call safe to retry? What order are lists in? Is the read fresh? | Callers retry a charge and bill a customer twice |
| **Errors** | Which failures exist, how each is reported, which are retryable | Every client parses message strings to decide what to do |
| **Limits** | Page sizes, rate limits, payload sizes, timeouts | One client's batch job takes the service down |
| **Evolution** | What may change without notice, and how breaking changes are announced | A "harmless" rename breaks a partner integration in production |

**Hyrum's law** is why the last row matters: with enough callers, every observable behaviour of an
API will be depended on by somebody, including ones you never promised, such as the order of fields
or the exact text of an error. Design the contract deliberately, document what is and isn't
guaranteed, and assume anything you expose becomes permanent.

### Design from the caller's side

Good API design starts from the caller's use cases, not the storage model:

1. List what callers need to do ("show a user's recent orders with their status", "cancel an order
   that hasn't shipped").
2. Name the resources and actions those use cases touch.
3. For each call, decide the semantics: idempotent or not, synchronous or not, fresh or possibly
   stale, what errors it can return.
4. Only then decide the style (REST, gRPC, GraphQL, events) and the wire details
   ([API Design — Low Level](04_api_design_low_level.md)).

HTTP method semantics (safe, idempotent, cacheable), status codes and headers are covered in
[API Design — Low Level](04_api_design_low_level.md); this file covers the shape of the contract and the behaviour behind it.

### Vocabulary

| Term | Meaning |
|---|---|
| Resource | A thing the API exposes (an order, a user), addressed by a stable identifier |
| Idempotent | Repeating the call leaves the same end state as calling once |
| Cursor | An opaque token marking where the next page starts |
| Backward compatible | Existing clients keep working after the server changes |
| Forward compatible | Old servers or clients cope with data from newer versions (for example, unknown fields) |
| Tolerant reader | A client that ignores fields and values it doesn't recognise |
| Rate limit / quota | A cap on requests per time unit / on total usage over a billing period |
| N+1 queries | Fetching a list with one query, then one more query per item |
| Deprecation | Announcing that something will be removed, with a date and a migration path |

## The client is not trusted

The client handles presentation, UX-level input validation, local caching, and retry behavior. It is not a trusted authority for permissions, prices, quantities, or any invariant — a user can modify requests, replay them, or write a custom client that skips your UI entirely. Every rule enforced client-side must also be enforced server-side, or it isn't actually enforced.

## Choosing an API style

| Style | Choose it when | Strength | Caution |
|---|---|---|---|
| HTTP/JSON REST-like | Public/browser integrations, resource-shaped domain, broad client compatibility | Ubiquitous tooling, cacheable, human-debuggable | Forcing every action into CRUD produces awkward endpoints (`POST /orders/{id}/cancel` vs a fake `PATCH` that means five different things) |
| gRPC/RPC | Internal service-to-service calls, need typed contracts/codegen, streaming | Efficient binary schema, generated clients, native streaming | Browser support needs a proxy (gRPC-Web); harder to debug ad hoc; deadlines still mandatory, not automatic |
| GraphQL | Many heterogeneous clients need different shapes of the same underlying graph (e.g. mobile wants a thin payload, web wants nested detail) | One endpoint, client-specified shape, avoids over/under-fetching | N+1 query risk if resolvers naively fetch per field; complicates HTTP caching (single endpoint, POST-shaped queries) and per-field rate limiting; query cost must be bounded server-side or a client can request an arbitrarily expensive graph traversal |
| WebSocket | Bidirectional, low-latency, server-initiated pushes | Chat, collaboration, live updates | Connection ownership/reconnection/backpressure/offline sync all become your problem |
| Webhook | Notify another system asynchronously, caller doesn't poll | Loose coupling between systems | Must verify signatures, handle retries/duplicates, and the receiver may be down — needs its own retry/DLQ story |
| Queue/event | Caller doesn't need the result synchronously | Buffering, retry, fan-out | Eventual consistency; caller needs a way to check status later |

**GraphQL specifically**: it earns its place when you have multiple client shapes pulling from the same underlying data graph and REST would otherwise force either chatty multi-endpoint calls or bespoke per-client endpoints. It does *not* earn its place for a single client type or a simple resource CRUD API — you inherit resolver N+1 risk (a naive resolver for `author` on each of 50 posts issues 50 queries unless batched via a dataloader pattern) and lose the free HTTP-level caching and per-route rate limiting that REST gets from distinct URLs and GET semantics.

## Resource modeling (REST-ish)

Model nouns, not verbs: `/orders`, `/orders/{id}`, `/orders/{id}/items`. Actions that don't fit CRUD get an explicit sub-resource or action endpoint rather than overloading a generic `PATCH`: `POST /orders/{id}/cancel`, not `PATCH /orders/{id} {"status":"cancelled"}` pretending to be a generic update when it's actually a specific state-transition business rule with its own validation.

```text
GET    /orders            list (paginated, filterable)
POST   /orders            create
GET    /orders/{id}       read one
PATCH  /orders/{id}       partial update of genuinely mutable fields
POST   /orders/{id}/cancel   explicit business action, not a fake PATCH
```

## Pagination

Offset/limit pagination (`?offset=200&limit=50`) breaks under concurrent writes: an insert before offset 200 shifts every subsequent page by one, causing skipped or duplicated rows. Use a **stable cursor** instead — an opaque token encoding the last-seen sort key (often `(sort_value, id)` for a tiebreak on ties):

```http
GET /orders?limit=50&cursor=eyJpZCI6MTIzNDUsInRzIjoxNzI2fQ==
```

```json
{ "items": [...], "next_cursor": "eyJpZCI6MTIzOTUsInRzIjoxNzMwfQ==" }
```

The cursor is opaque to the client — you can change its internal encoding without breaking callers, as long as they keep passing back what you gave them.

## Versioning without breaking clients

- Add optional fields; never repurpose an existing field's meaning (a field named `total` that changes from "pre-tax" to "post-tax" silently is a production incident for every consumer, even though the schema "didn't change").
- Additive changes (new optional field, new endpoint, new enum value a client should ignore if unrecognized) don't need a version bump.
- Breaking changes (removing/renaming a field, changing a type, changing required-ness) need a new version (`/v2/orders`) or a deprecation window with both versions live, sunset communicated and enforced by date, not indefinitely.
- Enums are a common trap: adding a new enum value is "additive" to you but breaking to a client with an exhaustive `switch` and no default case — document that enums may grow and clients must handle unknown values gracefully.

## Error contract

Every error response should give a caller enough to act on programmatically, not just a message for a human:

```json
{
  "error": {
    "code": "INSUFFICIENT_INVENTORY",
    "message": "Item book-1 is out of stock.",
    "correlation_id": "8f3e1c2a-...",
    "retryable": false
  }
}
```

- **Code**: stable, machine-matchable string — not the HTTP status alone (a 400 could mean a dozen different things; the client needs to distinguish them).
- **Message**: safe to show/log, never a stack trace or internal detail.
- **Correlation ID**: ties the error back to server-side logs/traces for support/debugging (see [Observability and Reliability](15_observability_and_reliability.md)).
- **Retry guidance**: is this transient (retry with backoff) or a permanent rejection (don't retry, fix the request)? Conflating the two causes retry storms against permanently-failing requests.

## Idempotency key pattern

Give every unsafe mutation (anything that isn't naturally idempotent, like `POST /orders`) a client-supplied idempotency key, because a network failure between response and client leaves the client unable to tell whether the mutation actually happened (see [Networking](02_networking.md) on TCP connection breakage after server-side completion — this is the API-level answer to that transport-level fact).

```http
POST /v1/orders
Idempotency-Key: 8db8c2f1-4a3e-4b1c-9f2a-...

{ "items": [{"sku":"book-1","quantity":1}] }
```

The server stores the logical outcome keyed by that idempotency key (commonly in the same transaction as the business write, or via an outbox — see [Messaging and Streaming](09_messaging_and_streaming.md)). If the client doesn't get a response, it retries with the **same key**: the server recognizes the key, returns the original stored outcome, and does not create a second order. A new key means a genuinely new intended order — the key represents *intent*, not the request body alone (so it should be scoped/expired sensibly; an indefinitely-retained key store grows forever).

## Synchronous vs asynchronous contracts

A synchronous contract (`POST /orders` returns the created order in the response) is simpler for the caller but couples the caller's request lifetime to your full processing time — including anything slow downstream. An asynchronous contract (`POST /orders` returns `202 Accepted` + a status URL, or the caller subscribes to a webhook/event) decouples that, at the cost of the caller needing a polling or callback mechanism and your API surface needing a status/result resource. Choose based on whether the *caller* can usefully wait — a checkout confirmation UI usually needs synchronous-feeling UX even if the backend defers work internally (accept fast, confirm fast, finish the slow parts async and notify).

## API gateway's role


```arch
%% caption: The API Gateway intercepts external traffic, enforces cross-cutting concerns, and routes to internal services.
node ext "External Client" at 0,0 icon=client color=blue
node gw "API Gateway\n(Auth, Quotas, Routing)" at 2,0 icon=server color=slate
group svcs "Internal Microservices" color=green style=dashed
node s1 "Order Service" at 4,-1 in svcs icon=app
node s2 "User Service" at 4,1 in svcs icon=app

ext -> gw : "HTTPS"
gw -> s1 : "route /orders"
gw -> s2 : "route /users"
```
An API gateway centralizes coarse authentication, request routing, quota/rate-limit enforcement, and a consistent edge contract across multiple backend APIs — it is not where business logic lives. See [Platform and Infrastructure](16_platform_and_infra.md) for gateway/ingress placement in the platform stack and [Networking](02_networking.md) for where it sits in the request path relative to the load balancer and TLS termination.

## Pagination, measured

The pagination section above claims offset pagination is slow deep in a list and wrong when the
data changes. Both claims, measured on a million orders in SQLite, listed newest first:

```python
"""Offset pagination vs keyset (cursor) pagination on 1,000,000 orders in SQLite:
how long does page N take, and what happens when rows arrive while a client pages?"""
import sqlite3, time

db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, created INTEGER, total INTEGER)")
db.execute("CREATE INDEX by_created ON orders (created, id)")
db.executemany("INSERT INTO orders VALUES (?, ?, ?)",
               ((i, 1_700_000_000 + i // 3, i % 997) for i in range(1, 1_000_001)))

PAGE = 50
OFFSET_SQL = "SELECT id, created FROM orders ORDER BY created DESC, id DESC LIMIT ? OFFSET ?"
KEYSET_SQL = ("SELECT id, created FROM orders WHERE (created, id) < (?, ?) "
              "ORDER BY created DESC, id DESC LIMIT ?")


def ms(fn, reps=20):
    t = time.perf_counter()
    for _ in range(reps):
        fn()
    return (time.perf_counter() - t) / reps * 1000


print("Time to fetch one page of 50")
print(f"  {'page':>6} {'OFFSET':>10} {'keyset':>10}")
for page in (1, 100, 1_000, 10_000, 19_999):
    off = (page - 1) * PAGE
    last = db.execute(OFFSET_SQL, (1, off - 1)).fetchone() if off else None
    t_off = ms(lambda: db.execute(OFFSET_SQL, (PAGE, off)).fetchall())
    if last:
        t_key = ms(lambda: db.execute(KEYSET_SQL, (last[1], last[0], PAGE)).fetchall())
    else:
        t_key = ms(lambda: db.execute(OFFSET_SQL, (PAGE, 0)).fetchall())
    print(f"  {page:6,} {t_off:8.2f} ms {t_key:8.3f} ms")


def page_through(kind, change, pages=5, per_gap=7):
    """Read 5 pages newest-first; between requests, 7 rows are inserted at the
    top (new orders) or deleted from the top (orders the client already saw)."""
    db.execute("SAVEPOINT s")
    seen, cursor, next_id = [], None, 2_000_000
    for p in range(pages):
        if kind == "offset":
            rows = db.execute(OFFSET_SQL, (PAGE, p * PAGE)).fetchall()
        else:
            rows = (db.execute(OFFSET_SQL, (PAGE, 0)) if cursor is None else
                    db.execute(KEYSET_SQL, (cursor[1], cursor[0], PAGE))).fetchall()
            cursor = rows[-1]
        seen += [r[0] for r in rows]
        for _ in range(per_gap):
            if change == "insert":
                next_id += 1
                db.execute("INSERT INTO orders VALUES (?, ?, 0)", (next_id, 1_800_000_000 + next_id))
            else:
                db.execute("DELETE FROM orders WHERE id = (SELECT max(id) FROM orders)")
    oldest = min(seen)
    missed = [i for i in range(oldest, 1_000_001) if i not in set(seen)
              and db.execute("SELECT 1 FROM orders WHERE id = ?", (i,)).fetchone()]
    db.execute("ROLLBACK TO s")
    db.execute("RELEASE s")
    return len(seen) - len(set(seen)), len(missed)


print("\nPaging 5 pages of 50 while the data changes between requests")
for change in ("insert", "delete"):
    for kind in ("offset", "keyset"):
        dupes, missed = page_through(kind, change)
        print(f"  7 {change}s per gap, {kind:6}: duplicates {dupes:2}, rows skipped {missed:2}")
```

```text
Time to fetch one page of 50
    page     OFFSET     keyset
       1     0.02 ms    0.022 ms
     100     0.05 ms    0.024 ms
   1,000     0.40 ms    0.022 ms
  10,000     4.20 ms    0.021 ms
  19,999     8.89 ms    0.023 ms

Paging 5 pages of 50 while the data changes between requests
  7 inserts per gap, offset: duplicates 28, rows skipped  0
  7 inserts per gap, keyset: duplicates  0, rows skipped  0
  7 deletes per gap, offset: duplicates  0, rows skipped 28
  7 deletes per gap, keyset: duplicates  0, rows skipped  0
```

- **Offset gets slower the deeper you go.** `OFFSET 999,900` still makes the database walk past
  999,900 index entries to throw them away, so page 19,999 is hundreds of times slower than page 1.
  Keyset pagination seeks straight to the cursor in the `(created, id)` index, and every page costs
  the same. Crawlers and "export everything" scripts hit the deep pages, so this becomes a
  production problem, not a benchmark curiosity.
- **Offset is wrong when rows move.** New orders push every row down, so the next page repeats
  rows the client has already seen (28 duplicates over 5 pages here). Deleted rows pull every row
  up, and the client silently skips rows it never saw (28 here). Skipping is the worse bug because
  nothing looks wrong. The keyset cursor says "rows older than this one", which stays correct
  however the rows before it change.
- **The sort must be unique.** `created` alone has ties (three orders share each second here), so
  the cursor includes `id` as a tiebreaker. A cursor on a non-unique key skips or repeats rows at
  every tie.

What keyset pagination gives up: you can't jump to "page 400", and a total count is a separate,
expensive query. Most APIs don't need either; if yours does, return an approximate count and
offer filters instead of deep page numbers.

## N+1 queries, measured

A feed of 50 posts, each showing its author and 10 comments, each comment with its author. Written
the natural way (each field fetches its own data), that is one query for the posts, 50 for post
authors, 50 for comment lists and 500 for comment authors. Against a database 0.5 ms away:

```python
"""The N+1 problem: a feed of 50 posts, each with its author, 10 comments, and
each comment's author. The database is another machine 0.5 ms away, so every
query costs a round trip on top of its own work."""
import sqlite3, time, random

RTT_MS = 0.5
db = sqlite3.connect(":memory:")
db.executescript("""
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE posts (id INTEGER PRIMARY KEY, author INTEGER, title TEXT);
CREATE TABLE comments (id INTEGER PRIMARY KEY, post INTEGER, author INTEGER, body TEXT);
CREATE INDEX c_post ON comments (post);
""")
rng = random.Random(1)
db.executemany("INSERT INTO users VALUES (?, ?)", ((i, f"user{i}") for i in range(10_000)))
db.executemany("INSERT INTO posts VALUES (?, ?, ?)", ((i, rng.randrange(10_000), f"post {i}") for i in range(5_000)))
db.executemany("INSERT INTO comments VALUES (?, ?, ?, ?)",
               ((i, i // 10, rng.randrange(10_000), "nice") for i in range(50_000)))

queries = 0

def q(sql, args=()):
    global queries
    queries += 1
    return db.execute(sql, args).fetchall()


def naive():
    """One resolver per field, each fetching its own row: the natural first version."""
    feed = []
    for pid, author, title in q("SELECT id, author, title FROM posts ORDER BY id DESC LIMIT 50"):
        a = q("SELECT name FROM users WHERE id = ?", (author,))[0][0]
        cs = [(q("SELECT name FROM users WHERE id = ?", (ca,))[0][0], body)
              for ca, body in q("SELECT author, body FROM comments WHERE post = ?", (pid,))]
        feed.append((title, a, cs))
    return feed


def batched():
    """Collect the ids each level needs, then fetch them in one query (a 'data loader')."""
    posts = q("SELECT id, author, title FROM posts ORDER BY id DESC LIMIT 50")
    pids = [p[0] for p in posts]
    comments = q(f"SELECT post, author, body FROM comments WHERE post IN ({','.join('?' * len(pids))})", pids)
    uids = sorted({p[1] for p in posts} | {c[1] for c in comments})
    names = dict(q(f"SELECT id, name FROM users WHERE id IN ({','.join('?' * len(uids))})", uids))
    by_post = {}
    for post, author, body in comments:
        by_post.setdefault(post, []).append((names[author], body))
    return [(title, names[author], by_post.get(pid, [])) for pid, author, title in posts]


results = []
for name, fn in [("one query per field", naive), ("batched per level", batched)]:
    queries = 0
    t = time.perf_counter()
    results.append(fn())
    local = (time.perf_counter() - t) * 1000
    print(f"{name:20} {queries:4} queries  database work {local:5.1f} ms  "
          f"+ round trips {queries * RTT_MS:6.1f} ms  = {local + queries * RTT_MS:6.1f} ms")
print("same feed from both:", results[0] == results[1])
```

```text
one query per field   601 queries  database work   3.1 ms  + round trips  300.5 ms  =  303.6 ms
batched per level       3 queries  database work   2.6 ms  + round trips    1.5 ms  =    4.1 ms
same feed from both: True
```

The database work is about the same either way; **the difference is almost entirely round trips**:
601 queries at 0.5 ms each is 300 ms, against 1.5 ms for three. Batching per level ("collect every
post ID, fetch all their comments in one query; collect every user ID, fetch all names in one
query") is what GraphQL's DataLoader does, and what an ORM's eager loading
(`select_related`, `includes`, `JOIN FETCH`) does.

Where N+1 appears in API design:

- **GraphQL resolvers** fetching per field: batch with a data loader and bound the query cost
  (depth and breadth limits), or one client query can fan out into thousands of database calls.
- **Chatty REST APIs** that force a client to call `GET /users/{id}` for every item in a list. The
  same problem, but the round trips now cross the internet. Offer embedding
  (`?include=author`) or batch reads (`GET /users?ids=1,2,3`).
- **Service-to-service calls** in a loop. Every internal API that returns a list should have a
  batch-get counterpart.

## Rate limiting, measured

Every public API needs rate limits: they keep one client's bug or scraper from taking capacity
from everyone else. The mechanics of one algorithm (token bucket) and the `429` response are in
[API Design — Low Level](04_api_design_low_level.md). Here are the four common algorithms side by side, each configured
for 100 requests a minute, facing a client that waits until just before a minute boundary and then
sends as fast as it can:

```python
"""Four rate limiters, each meant to allow 100 requests per minute per client.
A client stays idle, then from 0:59 sends a request every 10 ms for two
minutes. How many requests does each limiter let through?"""
from collections import deque


class FixedWindow:                       # one counter per calendar minute
    state = "1 counter"
    def __init__(s): s.window, s.count = -1, 0
    def allow(s, t):
        w = int(t // 60)
        if w != s.window:
            s.window, s.count = w, 0
        s.count += 1
        return s.count <= 100


class SlidingLog:                        # remember every accepted timestamp
    state = "up to 100 timestamps"
    def __init__(s): s.log = deque()
    def allow(s, t):
        while s.log and s.log[0] <= t - 60:
            s.log.popleft()
        if len(s.log) < 100:
            s.log.append(t)
            return True
        return False


class SlidingCounter:                    # this minute + a weighted share of the last
    state = "2 counters"
    def __init__(s): s.window, s.cur, s.prev = 0, 0, 0
    def allow(s, t):
        w = int(t // 60)
        if w != s.window:
            s.prev = s.cur if w == s.window + 1 else 0
            s.window, s.cur = w, 0
        weight = 1 - (t % 60) / 60
        if s.prev * weight + s.cur < 100:
            s.cur += 1
            return True
        return False


class TokenBucket:                       # refill 100/60 tokens per second, up to `burst`
    state = "2 numbers"
    def __init__(s, burst): s.burst, s.tokens, s.last = burst, burst, 0.0
    def allow(s, t):
        s.tokens = min(s.burst, s.tokens + (t - s.last) * 100 / 60)
        s.last = t
        if s.tokens >= 1:
            s.tokens -= 1
            return True
        return False


def most_in_window(times, width):
    best, lo = 0, 0
    for hi in range(len(times)):
        while times[hi] - times[lo] >= width:
            lo += 1
        best = max(best, hi - lo + 1)
    return best


attack = [59 + i / 100 for i in range(100 * 120)]
print(f"{len(attack):,} requests from t = 59 s to t = 179 s\n")
print(f"  {'limiter':26} {'most in any 60 s':>17} {'most in any 2 s':>16}   state per client")
for name, lim in [("fixed window", FixedWindow()), ("sliding log", SlidingLog()),
                  ("sliding window counter", SlidingCounter()),
                  ("token bucket, burst 100", TokenBucket(100)), ("token bucket, burst 10", TokenBucket(10))]:
    ok = [t for t in attack if lim.allow(t)]
    print(f"  {name:26} {most_in_window(ok, 60):17} {most_in_window(ok, 2):16}   {lim.state}")
```

```text
12,000 requests from t = 59 s to t = 179 s

  limiter                     most in any 60 s  most in any 2 s   state per client
  fixed window                             200              200   1 counter
  sliding log                              100              100   up to 100 timestamps
  sliding window counter                   199              102   2 counters
  token bucket, burst 100                  199              103   2 numbers
  token bucket, burst 10                   109               13   2 numbers
```

- **Fixed window** lets 200 requests through in 2 seconds: 100 at the end of one calendar minute
  and 100 at the start of the next. It is the simplest and cheapest, and fine when a 2× burst at the
  boundary doesn't matter.
- **Sliding log** is exact (never more than 100 in any 60 seconds) but stores a timestamp per
  accepted request, which is expensive for high limits across millions of clients.
- **Sliding window counter** estimates the last 60 seconds from two counters, assuming the previous
  minute's requests were spread evenly. This client put them all at the end, so the estimate was
  wrong, and it let 199 through in one 60-second window, though never more than about 100 in any
  2 seconds. It is the usual compromise: cheap, and close to exact for normal traffic.
- **Token bucket** separates the two things you might want to limit: the long-run rate (the refill,
  100 a minute) and the burst (the bucket size). With a burst of 100 it allows 199 in a minute,
  exactly its promise of "up to 100 at once, then 100 a minute". With a burst of 10, traffic is
  smoothed to about 13 in any 2 seconds.

Decisions that matter more than the algorithm:

- **Key.** Limit by API key or user for authenticated traffic, by IP (with care: NAT puts many users
  behind one address) for anonymous traffic, and by endpoint cost: an export can cost 100 tokens
  where a read costs 1.
- **Where the counters live.** A shared store such as Redis gives one exact limit across all
  gateway instances, at the cost of a network call per request and a dependency that must fail
  open or closed deliberately. Local counters (the limit divided by the number of instances) cost
  nothing but are only as accurate as your load balancing is even. Large systems often combine
  local limiting for protection with a shared, slightly delayed count for quotas.
- **What the client sees.** A `429` with `Retry-After` and remaining-quota headers lets well-behaved
  clients slow down instead of retrying blindly (see [Application Resilience Patterns](12_application_resilience_patterns.md)).
- **Rate limits are not overload protection.** They cap each client; they don't stop the sum of
  well-behaved clients from exceeding capacity. That is load shedding
  ([Overload Control and Graceful Degradation](28_overload_control_and_graceful_degradation.md)).

## Compatible and breaking changes

Whether a change breaks callers depends on the direction the data flows. Assuming tolerant readers
(clients ignore unknown fields):

| Change | In a response | In a request |
|---|---|---|
| Add an optional field | Safe | Safe |
| Add a required field | Safe | **Breaking**: old clients don't send it |
| Remove a field | **Breaking**: clients may read it | Safe if the server stops requiring it |
| Rename a field | **Breaking** (it is a remove plus an add) | **Breaking** |
| Change a type (`int` → `string`, cents → dollars) | **Breaking** | **Breaking** |
| Add an enum value | **Breaking for clients with exhaustive switches**; safe only if documented from day one | Safe |
| Tighten validation (shorter max length) | n/a | **Breaking**: requests that worked now fail |
| Loosen validation | Can break clients that relied on the old limit (Hyrum's law) | Safe |
| Change default sort order or page size | **Breaking in practice** | n/a |

The safe way to make a breaking change is **expand, migrate, contract**: add the new field or
endpoint alongside the old one, move callers over (measuring who still uses the old one), then
remove the old one after the announced date. It is the same sequence as a database schema
migration, because it is the same problem.

For binary formats the rules are enforced by tooling: in Protocol Buffers, never reuse a field
number, and use `reserved` for removed ones; schema registries for Avro and Protobuf can reject
incompatible changes before they ship.

## Designing an API end to end: comments

A worked answer to "design the API for comments on posts", in the order an interview expects.

**Use cases.** Show a post's comments newest first, with replies; add a comment; edit or delete
your own comment; report a comment for moderation.

**Resources and operations.**

```text
GET    /v1/posts/{post_id}/comments?limit=20&cursor=...   list top-level comments, newest first
GET    /v1/comments/{id}/replies?limit=20&cursor=...       list replies to one comment
POST   /v1/posts/{post_id}/comments                        add a comment (Idempotency-Key required)
PATCH  /v1/comments/{id}                                   edit body (author only, If-Match: <etag>)
DELETE /v1/comments/{id}                                   delete (author or moderator)
POST   /v1/comments/{id}/reports                           report for moderation (returns 202)
```

**Representation.**

```json
{
  "id": "cmt_8Kq2",
  "post_id": "pst_19",
  "author": { "id": "usr_7", "display_name": "Ana" },
  "body": "Great write-up",
  "created_at": "2026-09-30T10:15:02Z",
  "edited": false,
  "reply_count": 3,
  "status": "visible"
}
```

**The decisions, and why.**

- **Cursor pagination** on `(created_at, id)`, because comments arrive constantly while people
  scroll (measured above).
- **Author embedded** in each comment, so a page of 20 comments is one call, not 21.
- **Idempotency key on create**, so a mobile client on a bad connection can retry without posting a
  duplicate (the pattern above, and [Distributed Systems Fundamentals](../../CSFundamentals/15_distributed_systems_deep_dive.md) §8).
- **`If-Match` on edit** (optimistic concurrency): two edits from two devices can't silently
  overwrite each other; the second gets `412 Precondition Failed`.
- **`status` field is an enum that may grow** (`visible`, `hidden`, `pending_review`, ...), and the
  documentation says so from day one.
- **Reports return `202 Accepted`**: moderation is asynchronous, and the response says only that
  the report was received.
- **Limits**: 20 per page by default, 100 maximum; comment bodies up to 10,000 characters; creates
  rate-limited per user (token bucket, burst 5, 30 per hour) because spam is the main abuse case.
- **Errors**: stable codes such as `COMMENT_TOO_LONG`, `POST_LOCKED` and `RATE_LIMITED` (with
  `Retry-After`), each marked retryable or not.
- **IDs are opaque strings** with a type prefix, not sequential integers, so they can't be
  enumerated and can change their encoding later.

## What each level should know

| Topic | L4 · Mid | L5 · Senior | L6+ · Staff |
|---|---|---|---|
| **Contract design** | Designs CRUD endpoints for resources | Designs from use cases: semantics, errors, limits and idempotency for every call | Sets API standards and review for an organisation (style guide, linting, compatibility checks) |
| **Pagination and N+1** | Paginates lists | Chooses cursors, explains offset's cost and correctness bugs, prevents N+1 with batching | Designs batch and bulk APIs, and query-cost limits for GraphQL |
| **Rate limiting** | Knows `429` exists | Compares the algorithms, chooses the key and store, returns useful headers | Designs quotas, tiers and fairness across tenants; separates rate limits from overload control |
| **Evolution** | Adds optional fields | Classifies changes as breaking or safe; runs expand-migrate-contract | Owns deprecation policy and usage measurement across many consumers |

## Interview checklist

- [ ] I can list what an API contract contains beyond endpoints: semantics, errors, limits and evolution.
- [ ] I can design endpoints from use cases and justify REST vs gRPC vs GraphQL vs events.
- [ ] I can explain, with numbers, why offset pagination is slow and wrong under writes, and design a keyset cursor with a tiebreaker.
- [ ] I can explain the N+1 problem and fix it with batching, embedding or batch-get endpoints.
- [ ] I can compare fixed window, sliding log, sliding counter and token bucket, and say where the counters should live.
- [ ] I can classify a change as breaking or safe, and run expand-migrate-contract.
- [ ] I can design idempotent creates and optimistic-concurrency updates.
- [ ] I can walk through a complete API design (resources, representation, pagination, errors, limits) in an interview.

## Related building blocks

- [Building Blocks of Any System](00_overview.md)
- [Networking](02_networking.md)
- [API Design — Low Level](04_api_design_low_level.md)
- [Messaging and Streaming](09_messaging_and_streaming.md)
- [Application Resilience Patterns](12_application_resilience_patterns.md)
- [Platform and Infrastructure](16_platform_and_infra.md)
- [Overload Control and Graceful Degradation](28_overload_control_and_graceful_degradation.md)
