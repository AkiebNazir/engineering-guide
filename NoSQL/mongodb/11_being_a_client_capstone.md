# Capstone: Being a Good MongoDB Client

Every level so far taught MongoDB's own concepts: documents, queries, indexes, aggregation, transactions, replication. This level is about the other half of production correctness — how your **client code** should behave so that everything above actually holds up under real traffic: reuse connections instead of paying for a fresh one every call, let the driver retry the specific failures that are safe to retry, and never let a network call hang forever. This is a real module, run end to end against the live lab instance.

## The module

```python
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import ServerSelectionTimeoutError


class NotesService:
    """One shared client per process. Construct once, reuse everywhere."""

    def __init__(self, uri: str, db_name: str = "capstone_notes"):
        self._client = MongoClient(
            uri,
            serverSelectionTimeoutMS=3000,   # fail fast if no server is reachable
            connectTimeoutMS=3000,           # cap the TCP+handshake time
            socketTimeoutMS=5000,            # cap any single network op once connected
            retryWrites=True,                # retry safe writes on a transient error
            maxPoolSize=50,                  # cap concurrent connections in the pool
        )
        self._db = self._client[db_name]
        self._notes = self._db.notes
        self._notes.create_index("owner")

    def create_note(self, owner: str, text: str) -> str:
        result = self._notes.insert_one({"owner": owner, "text": text, "archived": False})
        return str(result.inserted_id)

    def get_notes_for(self, owner: str) -> list[dict]:
        return list(self._notes.find({"owner": owner}, {"_id": 0}))

    def archive_note(self, note_id, owner: str) -> dict | None:
        return self._notes.find_one_and_update(
            {"_id": note_id, "owner": owner},
            {"$set": {"archived": True}},
            return_document=ReturnDocument.AFTER,
        )

    def ping(self) -> bool:
        try:
            self._client.admin.command("ping")
            return True
        except ServerSelectionTimeoutError:
            return False

    def close(self):
        self._client.close()
```

Basic usage, run for real against the lab instance:

```python
svc = NotesService("mongodb://localhost:27018")
nid = svc.create_note("njasm", "capstone module works")
print(svc.get_notes_for("njasm"))
print(svc.archive_note(ObjectId(nid), "njasm"))
```
```
[{'owner': 'njasm', 'text': 'capstone module works', 'archived': False}]
{'_id': ObjectId('6ab3b314f8ae0fd8d10248c9'), 'owner': 'njasm', 'text': 'capstone module works', 'archived': True}
```

## The same module, in Go

```go
type NotesService struct {
    client *mongo.Client
    notes  *mongo.Collection
}

func NewNotesService(ctx context.Context, uri string) (*NotesService, error) {
    client, err := mongo.Connect(
        options.Client().ApplyURI(uri).
            SetServerSelectionTimeout(3 * time.Second).
            SetConnectTimeout(3 * time.Second).
            SetTimeout(5 * time.Second).       // see the timeout table below
            SetRetryWrites(true).
            SetMaxPoolSize(50),
    )
    if err != nil {
        return nil, err
    }
    notes := client.Database("capstone_notes_go").Collection("notes")
    if _, err := notes.Indexes().CreateOne(ctx, mongo.IndexModel{Keys: bson.M{"owner": 1}}); err != nil {
        return nil, err
    }
    return &NotesService{client: client, notes: notes}, nil
}

func (s *NotesService) CreateNote(ctx context.Context, owner, text string) (string, error) {
    res, err := s.notes.InsertOne(ctx, bson.M{"owner": owner, "text": text, "archived": false})
    if err != nil {
        return "", err
    }
    return res.InsertedID.(bson.ObjectID).Hex(), nil
}

func (s *NotesService) GetNotesFor(ctx context.Context, owner string) ([]bson.M, error) {
    cur, err := s.notes.Find(ctx, bson.M{"owner": owner}, options.Find().SetProjection(bson.M{"_id": 0}))
    if err != nil {
        return nil, err
    }
    var out []bson.M
    err = cur.All(ctx, &out)
    return out, err
}
```

Real output, basic usage:

```
[{"owner":"njasm","text":"capstone module works","archived":false}]
created note id: 6ab3f83263fa778179e4e243
```

Structurally identical to `NotesService` in Python — a struct instead of a class, methods take `context.Context` as their first argument (Go's idiom for "how long is this call allowed to take and can it be cancelled," in place of pymongo's client-level timeout settings applying implicitly to every call), and errors are returned values checked at each call site rather than caught exceptions.

## Connection pooling: one `MongoClient`, reused, always

`MongoClient` is not a single socket — it's a **connection pool** (default `maxPoolSize=100`, capped to 50 above) plus the driver's server-discovery/monitoring machinery. Constructing it does real work: DNS resolution, an initial handshake, and (for a replica set) discovering every member and which one is primary. **That cost should be paid once per process, not once per request.**

Measured, 200 inserts each way, same instance:

```python
# ONE shared client, reused for all 200 calls
for i in range(200):
    svc.create_note("bulk_user", f"note {i}")
```
```
200 inserts through ONE shared MongoClient: 144.6 ms total (0.723 ms/insert)
```

```python
# A NEW MongoClient constructed on every single call (the anti-pattern)
for i in range(200):
    c = MongoClient("mongodb://localhost:27018", serverSelectionTimeoutMS=3000)
    c["capstone_notes"].notes.insert_one({"owner": "bulk_user_fresh", "text": f"note {i}", "archived": False})
    c.close()
```
```
200 inserts, NEW MongoClient constructed per call: 747.4 ms total (3.737 ms/insert)
Per-call-client overhead: 5.2x slower than pooling
```

**5.2x slower**, measured on this machine, purely from throwing away the connection pool and paying discovery/handshake overhead on every single call — and this is a *local* Docker container with near-zero network latency; the gap would be considerably larger against a real remote cluster, where each fresh handshake also pays real round-trip-time cost. The practical rule: construct one `MongoClient` at application startup (or one per process in a worker-pool architecture) and hand it — or a module-level singleton wrapping it, as `NotesService` does — to every request handler. `MongoClient` is explicitly documented as thread-safe for exactly this reason; you're meant to share it.

**Same comparison, in Go** — a shared `*mongo.Client` (Go's driver is explicitly documented as safe for concurrent use by multiple goroutines, the direct equivalent of pymongo's thread-safety guarantee) vs. a fresh `mongo.Connect` call per insert:

```go
t0 := time.Now()
for i := 0; i < 200; i++ {
    svc.CreateNote(ctx, "bulk_user", fmt.Sprintf("note %d", i))
}
sharedElapsed := time.Since(t0)

t0 = time.Now()
for i := 0; i < 200; i++ {
    c, _ := mongo.Connect(options.Client().ApplyURI("mongodb://localhost:27018"))
    c.Database("capstone_notes_go").Collection("notes").InsertOne(ctx,
        bson.M{"owner": "bulk_user_fresh", "text": fmt.Sprintf("note %d", i), "archived": false})
    c.Disconnect(ctx)
}
freshElapsed := time.Since(t0)
```

Real output:

```
200 inserts through ONE shared Client: 231.6 ms total (1.158 ms/insert)
200 inserts, NEW Client constructed per call: 543.5 ms total (2.717 ms/insert)
Per-call-client overhead: 2.3x slower than pooling
```

**2.3x here, vs. Python's 5.2x** — both real, and the direction of the effect (pooling wins, decisively) is what matters and is stable across languages; the exact multiplier is a function of how expensive connection setup happens to be in each runtime, which is exactly the kind of number this repo's "measured, not asserted" rule says to report as-is rather than force into agreement.

## Retryable writes

`retryWrites=True` (the pymongo/MongoDB driver default since MongoDB 3.6+, made explicit above for clarity) tells the driver: if a single write operation (`insert_one`, `update_one`, `delete_one`, `find_one_and_update`, and their "one document" siblings) fails due to a **transient** network error or a "not primary" error (e.g. the primary just stepped down mid-write during an election), automatically retry it **exactly once** against the newly-discovered primary, rather than surfacing the error to your code immediately.

This works safely because the driver attaches a unique transaction number to the write and the server uses it to detect and dedupe a retried write that actually did land the first time (the network failed on the *acknowledgment*, not the write itself — the same category of ambiguity write concern deals with in level 10) — so a retry cannot silently double-apply an insert or double-decrement a counter. It does **not** cover multi-document unordered bulk writes (where "retry the whole batch" could re-apply already-succeeded operations) or reads (reads have their own separate retry setting, `retryReads`, on by default).

This lab's single-node replica set can't safely demonstrate a live mid-write failover (stepping down the only member removes the primary entirely, with nothing to fail over to) without destabilizing the shared lab environment other levels in this module depend on — consistent with level 09/10's honesty about single-node limits, this is documented, standard driver behavior rather than a claim measured on this instance. What *is* true and worth internalizing: retryable writes handle the "primary just changed" class of failure that a real replica set will genuinely experience during normal operation (planned maintenance, an election after a transient primary issue) — without it, your application code would need to catch `AutoReconnect`/`NotPrimaryError` and hand-roll the same retry-once-with-the-same-idempotency-key logic yourself.

## Timeouts: fail fast, don't hang

Every network call to a database needs a bound on how long it's allowed to take — an unbounded wait turns one slow/unreachable dependency into a pile of stuck request threads in your application.

```python
t0 = time.perf_counter()
try:
    bad = MongoClient("mongodb://localhost:19999", serverSelectionTimeoutMS=1000)
    bad.admin.command("ping")
except ServerSelectionTimeoutError as e:
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"Unreachable host: failed after {elapsed:.0f} ms (bounded), not a hang")
```
```
Unreachable host: failed after 1008 ms (bounded by serverSelectionTimeoutMS=1000), not a hang
```

Real measured result: pointed at a port nothing is listening on, the call failed in **~1 second**, matching the configured `serverSelectionTimeoutMS=1000` almost exactly — not an indefinite hang, and not an immediate failure either (the driver genuinely spends the configured budget trying before giving up). The three timeouts used in `NotesService` cover three different failure windows:

| Timeout | Governs |
|---|---|
| `serverSelectionTimeoutMS` | How long to search for *any* usable server (right host but nothing listening, DNS resolves but unreachable, entire replica set down). |
| `connectTimeoutMS` | How long a single TCP connection attempt to a server that *is* reachable may take to establish. |
| `socketTimeoutMS` | How long any individual already-connected network operation (a query, an insert) may take before being abandoned. |

Leaving these at driver defaults (`serverSelectionTimeoutMS` defaults to 30 seconds) is a common production surprise: a struggling or partitioned database can leave application request threads blocked for 30 real seconds each before failing, which is often far longer than the timeout the calling HTTP request itself is willing to tolerate — set these deliberately, shorter than whatever timeout wraps the code calling them.

## Same timeout demo, and a genuine driver-design difference, in Go

```go
t0 := time.Now()
badCtx, cancel := context.WithTimeout(ctx, 1*time.Second)
defer cancel()
bad, _ := mongo.Connect(options.Client().ApplyURI("mongodb://localhost:19999").SetServerSelectionTimeout(1 * time.Second))
err := bad.Ping(badCtx, nil)
fmt.Printf("Unreachable host: failed after %.0f ms (bounded), not a hang -- %v\n", time.Since(t0).Seconds()*1000, err)
```
```
Unreachable host: failed after 1000 ms (bounded), not a hang -- server selection error: context deadline exceeded, current topology: { Type: Unknown, Servers: [{ Addr: localhost:19999, ... Last error: dial tcp [::1]:19999: connect: connection refused }] }
```

Same bounded-failure result as pymongo — **~1000ms**, matching the configured 1-second budget almost exactly, not a hang. The error message is also genuinely more informative by default: the Go driver's `server selection error` includes the actual topology it discovered (or failed to) and the underlying `connect: connection refused`, in one structured error value.

**The real, worth-knowing driver difference:** the Go v2 driver has **no `SetSocketTimeout`** — trying to set one is a compile error, not a missing feature accidentally left out. It's been replaced by a single **`SetTimeout`** (Go's driver calls this **CSOT — Client-Side Operation Timeout**, a newer cross-driver MongoDB spec), which bounds an *entire operation* — connection checkout, server selection, and the operation itself — with one deadline, composed naturally with Go's own `context.Context` cancellation, rather than pymongo's three separately-configured windows (`serverSelectionTimeoutMS`/`connectTimeoutMS`/`socketTimeoutMS`) that each cover one phase. Both approaches solve "don't hang forever," but Go's is the direction newer official MongoDB drivers (including pymongo's own newer `timeoutMS` option) are converging toward — worth knowing which style a given driver version actually supports rather than assuming the three-timeout model is universal.

## Common mistakes

- **Constructing a `MongoClient` per request handler.** The single most common real-world pymongo mistake — throws away pooling entirely, and under load can also exhaust available file descriptors/ports as each short-lived client opens and tears down its own connections. Construct once, store it (module-level, dependency-injected, or on an app/request-context object), reuse.
- **Assuming `retryWrites` covers everything.** It covers single-document write operations against a replica set specifically — an unordered bulk write, a standalone (non-replica-set) deployment, or a read, are outside its scope; each has its own handling (`retryReads`, or your own retry logic for bulk ops).
- **Leaving every timeout at its default "just in case."** A generous default timeout feels safer but just delays discovering a real outage — by the time a 30-second `serverSelectionTimeoutMS` gives up, whatever called your code has probably already timed out and moved on, so the extra wait bought nothing and just held a thread/connection hostage the whole time.
- **Not calling `.close()` on a client you're actually done with** (a script, a one-off job, a test's teardown) — for a long-lived service process this doesn't matter since the client lives for the process's whole lifetime, but leaked clients in short-lived scripts/tests accumulate open connections across a test suite.

That closes the MongoDB ladder: level 00's document model and flexible schema, levels 01–03's connection and query fluency, level 04's embedding-vs-referencing design skill, levels 05–08's performance and structure (indexes, aggregation, updates, validation), levels 09–10's distributed-systems behavior (transactions, write/read concern), and this level's client-side discipline for making all of it safe to run in production.
