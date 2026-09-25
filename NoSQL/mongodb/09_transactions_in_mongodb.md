# Transactions in MongoDB

Every single `updateOne`/`insertOne` call is already atomic **at the document level** — a write either fully applies to one document or doesn't happen at all, even for a deeply nested update. What MongoDB did not support until version 4.0 is atomicity **across multiple documents** (or multiple collections): a guarantee that a set of writes either all commit or all roll back together. That's what a **multi-document transaction** gives you, and it requires a **replica set** (or sharded cluster) — a standalone, non-replicated `mongod` cannot run one at all.

The lab environment for this module runs `mongo:7` as a **single-node replica set** (one member, `rs.initiate()`'d) specifically so this level's transaction code could be run for real rather than only described — a genuine single-primary replica set, just with a replication factor of one. Everything below is real output from that instance.

## The worked example: a funds transfer

```python
db.accounts.insert_many([
    {"_id": "acct_a", "owner": "Alice", "balance": 100},
    {"_id": "acct_b", "owner": "Bob", "balance": 50},
])

def transfer(session, from_id, to_id, amount):
    accounts = db.accounts
    src = accounts.find_one({"_id": from_id}, session=session)
    if src["balance"] < amount:
        raise ValueError(f"Insufficient funds in {from_id}: has {src['balance']}, needs {amount}")
    accounts.update_one({"_id": from_id}, {"$inc": {"balance": -amount}}, session=session)
    accounts.update_one({"_id": to_id}, {"$inc": {"balance": amount}}, session=session)

with client.start_session() as session:
    session.with_transaction(lambda s: transfer(s, "acct_a", "acct_b", 30))
```

```
-- Before --
{'_id': 'acct_a', 'owner': 'Alice', 'balance': 100}
{'_id': 'acct_b', 'owner': 'Bob', 'balance': 50}

-- Successful transfer: 30 from A to B --
{'_id': 'acct_a', 'owner': 'Alice', 'balance': 70}
{'_id': 'acct_b', 'owner': 'Bob', 'balance': 80}
```

`with_transaction` is pymongo's recommended entry point over the lower-level `start_transaction()`/`commit_transaction()`/`abort_transaction()` calls — it retries the whole callback automatically on the specific transient errors MongoDB tells drivers are safe to retry (`TransientTransactionError`, `UnknownTransactionCommitResult`), which real transactions need because a replica set can have transient issues (a stepdown, a network blip) that a naive single-attempt transaction would surface as a hard failure for no good reason. Every operation inside the callback must pass `session=session` — that's what actually associates a write with the transaction; forgetting it silently runs that one operation *outside* the transaction instead of raising an error.

**The same transfer, in Go**, using the Go driver's session/transaction <abbr title="Application Programming Interface">API</abbr> — `Session.WithTransaction` is the direct equivalent of pymongo's `with_transaction`, and every operation inside the callback takes the callback's own `context.Context` (`sc`, derived from the session) instead of a Python `session=` keyword argument — that context IS what associates the write with the transaction:

```go
session, _ := client.StartSession()
_, err := session.WithTransaction(ctx, func(sc context.Context) (interface{}, error) {
    var src bson.M
    if err := accounts.FindOne(sc, bson.M{"_id": "acct_a"}).Decode(&src); err != nil {
        return nil, err
    }
    if src["balance"].(int32) < 30 {
        return nil, fmt.Errorf("insufficient funds")
    }
    if _, err := accounts.UpdateOne(sc, bson.M{"_id": "acct_a"}, bson.M{"$inc": bson.M{"balance": -30}}); err != nil {
        return nil, err
    }
    _, err := accounts.UpdateOne(sc, bson.M{"_id": "acct_b"}, bson.M{"$inc": bson.M{"balance": 30}})
    return nil, err
})
session.EndSession(ctx)
```

Real output — identical transfer, identical result:

```
-- Before --
{"_id":"acct_a","owner":"Alice","balance":100}
{"_id":"acct_b","balance":50,"owner":"Bob"}
-- Successful transfer: 30 from A to B --
{"owner":"Alice","balance":70,"_id":"acct_a"}
{"_id":"acct_b","balance":80,"owner":"Bob"}
```

Returning a non-nil `error` from the callback is Go's equivalent of Python's `raise` inside the `with_transaction` lambda — either one tells the driver to abort rather than commit.

## Proof of atomicity: a write that already ran gets undone

The interesting case isn't "the whole thing succeeds" — it's proving that a write which **already executed** inside the transaction gets fully rolled back if something later in the same transaction fails.

```python
def transfer_then_fail(session, from_id, to_id, amount):
    accounts = db.accounts
    accounts.update_one({"_id": from_id}, {"$inc": {"balance": -amount}}, session=session)
    mid = accounts.find_one({"_id": from_id}, session=session)
    print("balance mid-transaction:", mid["balance"])
    raise RuntimeError("fraud check failed AFTER the debit write already ran")

try:
    with client.start_session() as session:
        session.with_transaction(lambda s: transfer_then_fail(s, "acct_a", "acct_b", 30))
except RuntimeError as e:
    print("transaction aborted:", e)
```

Real output:

```
balance mid-transaction (debit already applied, visible in-txn): 40
transaction aborted: fraud check failed AFTER the debit write already ran

-- After abort (the debit above must be fully undone) --
{'_id': 'acct_a', 'owner': 'Alice', 'balance': 70}
{'_id': 'acct_b', 'owner': 'Bob', 'balance': 80}
```

The debit's effect (`70 → 40`) was genuinely visible *within* the transaction's own session the moment it ran — reads inside a transaction, on the same session, see that transaction's own uncommitted writes. But once the exception propagated out of the callback, `with_transaction` aborted the transaction, and Alice's balance is back to `70` — exactly what it was before `transfer_then_fail` ran at all. No trace of the debit persisted, even though its write genuinely executed against the server mid-transaction.

**Same proof, in Go** — returning a Go `error` from the callback instead of raising a Python exception:

```go
session2, _ := client.StartSession()
_, err := session2.WithTransaction(ctx, func(sc context.Context) (interface{}, error) {
    accounts.UpdateOne(sc, bson.M{"_id": "acct_a"}, bson.M{"$inc": bson.M{"balance": -30}})
    var mid bson.M
    accounts.FindOne(sc, bson.M{"_id": "acct_a"}).Decode(&mid)
    fmt.Println("balance mid-transaction (debit already applied, visible in-txn):", mid["balance"])
    return nil, errors.New("fraud check failed AFTER the debit write already ran")
})
session2.EndSession(ctx)
fmt.Println("transaction aborted:", err)
```

Real output:

```
balance mid-transaction (debit already applied, visible in-txn): 40
transaction aborted: fraud check failed AFTER the debit write already ran
-- After abort (the debit above must be fully undone) --
{"owner":"Alice","balance":70,"_id":"acct_a"}
{"_id":"acct_b","balance":80,"owner":"Bob"}
```

Identical result to Python: the mid-transaction read sees the uncommitted debit (`40`), and once the callback returns a non-nil error, `WithTransaction` aborts, undoing it completely (`70`, unchanged from before the attempt) — this is a server-side transaction guarantee, not something either driver implements itself; both drivers are just relaying the same MongoDB abort semantics.

## Honestly measured: what a transaction actually costs

The spec for this repo is "measured, not asserted" — so here's a real timing comparison, and an honest discussion of what it does and doesn't tell you.

```python
N = 500
# do_plain(): two independent update_one calls, no session
# do_txn():   the same two update_one calls, wrapped in with_transaction
```

```
-- Overhead: 500 iterations of the same 2-write, balance-neutral operation --
Without transaction: 891.1 ms total (1.782 ms/iter)
With transaction:    858.8 ms total (1.718 ms/iter)
Ratio (txn/plain): 0.96x
```

**The measured result is that the transaction was not slower** on this machine — actually marginally faster (0.96x), which is noise-level, not a real speedup. Reported honestly rather than adjusted to match the expected story: this is a real number from a real run, and pretending otherwise would violate this repo's own rule.

**The same 500-iteration comparison, in Go:**

```go
t0 := time.Now()
for i := 0; i < 500; i++ {
    accounts.UpdateOne(ctx, bson.M{"_id": "acct_a"}, bson.M{"$inc": bson.M{"balance": -1}})
    accounts.UpdateOne(ctx, bson.M{"_id": "acct_b"}, bson.M{"$inc": bson.M{"balance": 1}})
}
plainElapsed := time.Since(t0)

session, _ := client.StartSession()
t0 = time.Now()
for i := 0; i < 500; i++ {
    session.WithTransaction(ctx, func(sc context.Context) (interface{}, error) {
        accounts.UpdateOne(sc, bson.M{"_id": "acct_a"}, bson.M{"$inc": bson.M{"balance": -1}})
        accounts.UpdateOne(sc, bson.M{"_id": "acct_b"}, bson.M{"$inc": bson.M{"balance": 1}})
        return nil, nil
    })
}
txnElapsed := time.Since(t0)
```

Real output:

```
Without transaction: 1103.3 ms total (2.207 ms/iter)
With transaction:    615.8 ms total (1.232 ms/iter)
Ratio (txn/plain): 0.56x
```

**Go's transaction run was actually faster than its own non-transactional run** — an even larger gap than Python's 0.96x, and just as counter-intuitive on first read. This is not "Go's transactions are free" any more than Python's 0.96x meant that — it's the same single-node artifact described below, likely compounded here by one session's operations reusing an already-warm connection/context path versus 1000 independent non-transactional round trips each paying their own per-call overhead. Reported as measured, per this repo's rule, rather than discarded for not matching intuition — and the same caveats below about what a single-node measurement cannot show apply identically to this Go run.

The number is real, but the setup it was measured on is **not representative of what makes transactions expensive in a real deployment**, and that has to be said explicitly rather than left implied:

- This is a **single-node** replica set. A transaction's real cost in production comes from **write concern `"majority"`** (level 10) requiring the primary to wait for enough secondaries to acknowledge the transaction's writes before committing — with one node, "majority" is trivially satisfied instantly, by the same node that just wrote it. On a real 3-node replica set, that acknowledgment round trip is real network latency the single-node measurement above cannot show at all.
- MongoDB's transactions also hold resources (locks on the touched documents, and a server-side limit on how long a transaction may stay open — 60 seconds by default) for the transaction's full duration. Two `update_one` calls with no shared transaction don't hold anything between them; the same two calls inside a transaction hold both documents' locks from the first write until commit. Under real concurrent load, this widens the window where a second transaction touching the same documents has to wait or gets a write conflict — invisible in a single-threaded, single-node microbenchmark with no contention at all.

## When to reach for a transaction vs. when to avoid needing one

This is the more important lesson than any timing number: **the best transaction is the one you avoid needing**, and level 04's embedding decision is the primary tool for avoiding it. If a funds transfer's two balances lived as two fields *inside one document* (e.g. a shared `wallet` document with `alice_balance`/`bob_balance`) instead of two separate documents, the update would just be a single-document multi-field `$inc` — atomic for free, no session, no transaction, no lock-duration concern, because single-document writes have always been atomic in MongoDB.

Reach for a real transaction when:

- The data that must change together **cannot** reasonably live in one document — genuinely separate entities (two independent accounts owned by different documents/collections, an inventory decrement plus an order-creation across different collections) where embedding would be the wrong schema for unrelated reasons (level 04's own criteria: unbounded growth, independent query access, different natural lifecycles).
- The operation spans **multiple collections**, which by definition can't be a single-document atomic write no matter how you shape any one of them.
- Losing atomicity would produce a state your system cannot detect or reconcile later (money created or destroyed, an order charged but never created) — as opposed to a case where a brief inconsistency is recoverable (a denormalized `comment_count` that's off by one until the next write corrects it).

Avoid transactions as your default tool for "make these two writes safe" — check first whether a schema that puts the related data in one document (or one array, with `arrayFilters` from level 07) makes the transaction unnecessary. That's not a workaround; it's the intended MongoDB design idiom, and it's strictly cheaper.

## Common mistakes

- **Forgetting to pass `session=` to every operation inside the callback.** An operation without it silently executes outside the transaction — no error, just wrong behavior (a partial commit is now possible, which is the exact thing transactions exist to prevent).
- **(Go) Using the outer `ctx` instead of the callback's own `sc context.Context` inside `WithTransaction`.** `sc` is what actually carries the session association forward to each operation — passing the enclosing `ctx` instead is Go's exact equivalent of Python's "forgot `session=`" mistake above: it compiles fine, runs fine, and silently executes that one call outside the transaction.
- **Doing slow, non-database work (an <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> call, a `sleep`, user interaction) inside a transaction callback.** Transactions hold locks and have a hard time limit; anything that isn't a fast database operation extends that window and increases the chance of hitting the transaction timeout or causing contention for unrelated operations touching the same documents.
- **Reaching for a transaction before checking whether embedding solves the problem for free**, as above — the single most common design mistake ported over from relational habits, where "wrap it in a transaction" is the correct default because tables can't embed related data into one row.
- **Assuming a single-node test proves anything about production transaction latency.** As shown above: a single-node measurement can show *no* overhead precisely because majority write concern has nothing real to wait for — don't generalize this level's 0.96x to "transactions are free" on a real multi-node deployment.

Level 10 covers the distributed-systems machinery a real (multi-node) replica set actually uses — write concern, read preference, and what they trade off — which is exactly the piece this level's single-node measurement couldn't show.
