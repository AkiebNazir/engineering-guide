# Indexes in MongoDB

An index is a separate, ordered data structure (a B-tree, same underlying idea as a relational database's index) that lets MongoDB find matching documents without checking every document in a collection. Without one, every query is a **collection scan** — read every document, test the filter against each one. This level measures the difference for real, on 200,000 documents, rather than asserting it.

## Setup: 200,000 documents

```python
db.events.drop()
# insert 200,000 documents shaped like:
{
    "user_id": 150000,
    "email": "user150000@example.com",
    "country": "PT",           # one of 10 countries
    "status": "active",        # one of 3 statuses
    "score": 47213,
    "tags": ["a", "c"],        # 1-3 tags from a set of 6
}
```

## Measured: query with and without an index

```python
def time_query(label, filt, n=5):
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        list(db.events.find(filt))
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000)
    print(f"{label}: min={min(times):.3f}ms avg={sum(times)/len(times):.3f}ms over {n} runs")

time_query("find user_id=150000", {"user_id": 150000})
```

**Before any index on `user_id`:**

```
find user_id=150000: min=29.570ms avg=29.871ms over 5 runs
```

```python
db.events.create_index("user_id")
time_query("find user_id=150000", {"user_id": 150000})
```

**After `db.events.create_index("user_id")`:**

```
find user_id=150000: min=0.360ms avg=0.596ms over 5 runs
```

**~50x faster** on this machine, for a query that returns exactly one document out of 200,000 — the more documents in the collection and the more selective the filter, the bigger this gap gets, because a collection scan's cost is proportional to the collection's total size regardless of how few documents match, while an index lookup's cost is proportional to `log(n)` plus however many documents actually matched.

**The same 200,000-document setup and measurement, in Go:**

```go
_, err := events.Find(ctx, bson.M{"user_id": 150000})
// timed over 5 runs, same shape as the Python loop above
```
```
find user_id=150000 (no index): min=35.473ms avg=36.220ms over 5 runs
find user_id=150000 (indexed): min=0.421ms avg=1.163ms over 5 runs
```

**~84x here** (35.473ms → 0.421ms) — a bigger ratio than Python's ~50x on this same machine, for the identical operation on a freshly-generated 200,000-document collection. Neither number is "the real one" — both are honest measurements of a collection scan vs. an index scan on data with the same shape but different random seeds and processes; the specific multiplier moves, the *fact* that an index turns a linear scan into a near-constant lookup does not.

## `.explain()`: what actually changed underneath

`.explain()` returns the query planner's chosen execution plan plus real execution statistics — the same tool a relational `EXPLAIN ANALYZE` gives you, adapted to MongoDB's plan shapes.

**Before the index:**
```python
plan = db.events.find({"user_id": 150000}).explain()
```
```
stage: COLLSCAN
docsExamined: 200000   nReturned: 1   executionTimeMillis: 30
```

`COLLSCAN` (collection scan) examined all 200,000 documents to find the 1 that matched — that's the entire cost, spelled out in the stats.

**After the index:**
```
stage: FETCH -> IXSCAN (index: user_id_1)
docsExamined: 1   nReturned: 1   executionTimeMillis: 0
```

`IXSCAN` walked the `user_id_1` index straight to the one matching entry; `FETCH` then pulled that single document off disk. `docsExamined` dropped from 200,000 to 1 — that's the whole story, and it's why the wall-clock time dropped by ~50x.

## Compound indexes

A **compound index** covers multiple fields in a fixed order, and answers queries that filter on a prefix of that field list efficiently.

```python
db.events.create_index([("country", 1), ("status", 1)])

plan = db.events.find({"country": "PT", "status": "active"}).explain()
```
```
stage: FETCH, indexName used: country_1_status_1
docsExamined: 6695   nReturned: 6695
```

The index let MongoDB jump directly to the `(PT, active)` range instead of scanning everything — real counts, with 10 countries and 3 statuses roughly evenly distributed across 200,000 documents, ~6,700 matched, which lines up with the expected `200,000 / 10 / 3 ≈ 6,667`.

Go, same compound index, same query, freshly-generated random data:

```go
events.Indexes().CreateOne(ctx, mongo.IndexModel{Keys: bson.D{{Key: "country", Value: 1}, {Key: "status", Value: 1}}})
count, _ := events.CountDocuments(ctx, bson.M{"country": "PT", "status": "active"})
```
```
count country=PT status=active: 6678
```

`6,678` — again right in line with the `≈ 6,667` expectation, from an independently-generated random dataset.

**Field order matters.** A compound index on `(country, status)` can serve a query on `country` alone (a usable prefix) but generally cannot efficiently serve a query on `status` alone — that's not a prefix of the indexed field order. Put the field with the query patterns that filter on it *alone* first, or build a second index if both access patterns matter and don't share a prefix relationship. This is the direct analogue of the ordering rule for relational composite indexes.

## Multikey indexes: indexing an array field

When you index a field whose value is an array, MongoDB creates one index entry **per array element**, not one entry per document. This is automatic — no special syntax is required, and `.explain()` will report `isMultiKey: true` on the plan.

```python
db.events.create_index("tags")   # tags is an array field, 1-3 values per document

plan = db.events.find({"tags": "c"}).explain()
```
```
isMultiKey: True
docsExamined: 67255   nReturned: 67255
```

`{"tags": "c"}` matches any document whose `tags` array *contains* `"c"` — the multikey index makes that a direct index lookup rather than an array scan inside every document. The tradeoff: a multikey index has more entries than documents (one per array element rather than one per document), so it costs more to build and maintain on writes than a single-value index — worth knowing before indexing a field with large arrays.

Go, same multikey index:

```go
events.Indexes().CreateOne(ctx, mongo.IndexModel{Keys: bson.M{"tags": 1}})
count, _ := events.CountDocuments(ctx, bson.M{"tags": "c"})
```
```
count tags=c (multikey): 59632
```

The Go driver has no special <abbr title="Application Programming Interface">API</abbr> for creating a multikey index — it's the exact same `CreateOne` call as any other single-field index; MongoDB decides server-side, purely from the fact that `tags` holds arrays, to build it as multikey. The count differs from the Python section's 67,255 only because both were generated from independent random datasets, not because either language builds or queries the index differently.

## Covered queries

A query is **covered** when every field the query needs — both to filter and to project — exists in the index itself, so MongoDB never has to fetch the actual document from disk at all.

```python
db.events.create_index([("user_id", 1), ("status", 1)])

plan = db.events.find(
    {"user_id": 150000},
    {"_id": 0, "user_id": 1, "status": 1},   # projection only asks for indexed fields
).explain()
```
```
totalDocsExamined: 0    (0 means covered: answered from index alone)
totalKeysExamined: 1
nReturned: 1
```

`totalDocsExamined: 0` is the tell — the answer came entirely from the index's own stored keys. Two conditions have to both hold for this: the projection must exclude `_id` (which isn't part of this compound index) and must only ask for fields that are in the index. Drop either condition (project `_id`, or ask for a field like `email` that isn't indexed) and MongoDB has to `FETCH` the real document, and `totalDocsExamined` goes back to matching `nReturned`.

**Go: same covered-query check**, via the driver's generic `RunCommand` (the Go driver has no typed `Explain()` helper on `Find`, so an explicit `explain` admin command is the direct equivalent of pymongo's `.explain()`):

```go
var raw bson.M
db.RunCommand(ctx, bson.D{
    {Key: "explain", Value: bson.D{
        {Key: "find", Value: "events"},
        {Key: "filter", Value: bson.M{"user_id": 150000}},
        {Key: "projection", Value: bson.M{"_id": 0, "user_id": 1, "status": 1}},
    }},
    {Key: "verbosity", Value: "executionStats"},
}).Decode(&raw)
```
```
totalDocsExamined: 0 totalKeysExamined: 1 nReturned: 1
```

Same result: the index alone answered the query, zero documents fetched. One Go-specific wrinkle worth naming: decoding `explain`'s nested `executionStats` sub-document into a generic `bson.M` field yields a **`bson.D`** (an ordered list of key/value pairs), not another `bson.M` — the driver's default decoding of a nested document inside a `bson.M`/`interface{}` context is `bson.D`, not recursively `bson.M`. Reading a field back out requires walking the `bson.D` (or converting it) rather than a second map index — a real, easy-to-hit surprise the first time you decode a multi-level nested command reply generically instead of into a typed struct.

## Common mistakes

- **Indexing every field "just in case."** Every index speeds up matching reads but slows down every write to the collection (each insert/update has to update every index too) and costs memory (indexes are ideally kept in RAM). Index for the queries you actually run, not defensively.
- **Wrong field order in a compound index.** `{status: 1, country: 1}` and `{country: 1, status: 1}` are different indexes with different prefixes — one serves "just give me `status`" efficiently, the other doesn't. Order by your actual query shapes, most selective/most commonly filtered-alone field first, as a starting heuristic.
- **Assuming an index is used just because it exists.** MongoDB's query planner picks a plan based on cost estimation; a bad or redundant index can be ignored, or in rare cases a stale cached plan can pick a worse one. Always check with `.explain()` rather than assuming — this repo's whole "measured, not asserted" rule applies here directly.
- **(Go) Assuming a decoded nested document is always `bson.M`.** As shown above, a sub-document inside a generically-decoded `bson.M`/`interface{}` field comes back as `bson.D`, not `bson.M` — a blind type assertion to `bson.M` panics at runtime. Either assert to `bson.D` and walk it, or decode into a concrete struct once the shape is known.
- **Not noticing a query needs a compound index for both a filter and a sort.** `find({"country": "PT"}).sort("score")` benefits from an index on `(country, score)` specifically — a single-field index on `country` alone still has to sort 6,700-ish matching documents in memory after the fetch.

Level 06 moves from single queries into MongoDB's aggregation pipeline — multi-stage transformations, and `$lookup`, which is MongoDB's answer to a SQL join.
