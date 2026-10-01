# CRUD Basics

Level 01 covered one insert and one read. This level fills out the rest of Create/Read/Update/Delete: inserting several documents at once, `find`'s filter+projection shape, and the four update/delete verbs. Every example below ran against the `lab_02_crud` database on the live `mongo:7` lab instance.

## Setup

```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27018")
db = client["lab_02_crud"]
db.tasks.drop()

result = db.tasks.insert_many([
    {"title": "Write report", "done": False, "priority": 2},
    {"title": "Review PR", "done": False, "priority": 1},
    {"title": "Deploy service", "done": True, "priority": 3},
    {"title": "Update docs", "done": False, "priority": 1},
])
print("inserted_ids count:", len(result.inserted_ids))
```

```
inserted_ids count: 4
```

`insert_many`/`insertMany` sends one round trip for the whole batch instead of four — the same principle as batching writes in any database client, and the difference matters at real volume (thousands of documents), not for four rows.

## `find`: filters and projections

`find` takes two arguments: a **filter** (which documents) and a **projection** (which fields of those documents). Level 03 goes deep on filter operators; here's the shape with equality filters, plus sorting.

```python
for t in db.tasks.find({}, {"_id": 0}).sort("priority", 1):
    print(t)
```

```
{'title': 'Review PR', 'done': False, 'priority': 1}
{'title': 'Update docs', 'done': False, 'priority': 1}
{'title': 'Write report', 'done': False, 'priority': 2}
{'title': 'Deploy service', 'done': True, 'priority': 3}
```

An empty filter `{}` matches every document. `{"_id": 0}` as a projection means "exclude `_id`" — projections are covered fully in level 03, but note here that `find` returns a **cursor**, not a list; iterating it (`for t in ...`) is what actually pulls documents from the server, in batches, as you consume them.

Filtering on a field and projecting to just what you need:

```python
for t in db.tasks.find({"done": False}, {"_id": 0, "title": 1}):
    print(t)
```

```
{'title': 'Write report'}
{'title': 'Review PR'}
{'title': 'Update docs'}
```

## `updateOne` and `updateMany`

Both take a filter and an **update document** — almost always built from update operators like `$set` (level 07 covers the full operator set: `$inc`, `$push`, `arrayFilters`, etc.). `updateOne` stops after the first match; `updateMany` applies to every match.

```python
r = db.tasks.update_one({"title": "Review PR"}, {"$set": {"done": True}})
print("matched:", r.matched_count, "modified:", r.modified_count)

r = db.tasks.update_many({"priority": 1, "done": False}, {"$set": {"priority": 0}})
print("matched:", r.matched_count, "modified:", r.modified_count)
```

```
matched: 1 modified: 1
matched: 1 modified: 1
```

Note `updateMany`'s filter is evaluated **once, up front** — it does not re-scan after each document is modified within the same call, so a filter like `{"priority": 1, "done": False}` matches the set of documents that satisfied it *before* the update started, even though "Review PR" (which now has `done: True` from the previous line) is no longer in that set by the time this runs. State after both updates:

```
{'title': 'Update docs', 'done': False, 'priority': 0}
{'title': 'Review PR', 'done': True, 'priority': 1}
{'title': 'Write report', 'done': False, 'priority': 2}
{'title': 'Deploy service', 'done': True, 'priority': 3}
```

`matched_count` vs `modified_count` can diverge: if the `$set` value equals the existing value, the document matches but MongoDB doesn't consider it modified (`modified_count` would be 0 even though `matched_count` is 1). Always check `matched_count` to know "did my filter find anything," and `modified_count` only tells you "did the write actually change bytes."

## `deleteOne` and `deleteMany`

Same filter-first shape, mirroring the update verbs.

```python
r = db.tasks.delete_one({"done": True})
print("deleted_count:", r.deleted_count)

r = db.tasks.delete_many({"done": False})
print("deleted_count:", r.deleted_count)

print(db.tasks.count_documents({}))
```

```
deleted_count: 1
deleted_count: 2
1
```

`delete_one` removed exactly one of the two `done: True` documents (which one, if several match, is unspecified — same "no order without an explicit sort" rule as `find_one`) — **one `done: True` document always survives** (Review PR and Deploy service are both `done: True` at this point; `delete_one` only ever removes one of them). `delete_many` then cleared out everything still `done: False`, leaving that one surviving `done: True` document behind — hence the final count of `1`, not `0`. The collection still exists either way — `drop()` (used at setup) is the only thing that removes the collection itself, along with its indexes.

## The same CRUD flow in Go

```go
tasks := client.Database("lab_02_crud").Collection("tasks")
tasks.Drop(ctx)

res, _ := tasks.InsertMany(ctx, []interface{}{
    bson.M{"title": "Write report", "done": false, "priority": 2},
    bson.M{"title": "Review PR", "done": false, "priority": 1},
    bson.M{"title": "Deploy service", "done": true, "priority": 3},
    bson.M{"title": "Update docs", "done": false, "priority": 1},
})
fmt.Println("inserted_ids count:", len(res.InsertedIDs))

opts := options.Find().SetProjection(bson.M{"_id": 0}).SetSort(bson.D{{Key: "priority", Value: 1}})
cur, _ := tasks.Find(ctx, bson.M{}, opts)
var all []bson.M
cur.All(ctx, &all)
for _, t := range all {
    fmt.Println(t)
}
```
```
inserted_ids count: 4
{"title":"Review PR","done":false,"priority":{"$numberInt":"1"}}
{"title":"Update docs","done":false,"priority":{"$numberInt":"1"}}
{"done":false,"priority":{"$numberInt":"2"},"title":"Write report"}
{"title":"Deploy service","done":true,"priority":{"$numberInt":"3"}}
```

`Find` returns a `*mongo.Cursor`, Go's equivalent of pymongo's cursor — `cur.All(ctx, &all)` materializes it into a slice in one call (convenient for a demo/small result set), or you can iterate with `for cur.Next(ctx)` for large result sets you don't want fully in memory at once, checking `cur.Err()` after the loop (a real Go-specific pitfall — see "Common mistakes" below).

`updateOne`/`updateMany`, same "filter evaluated once, up front" behavior as pymongo:

```go
ur, _ := tasks.UpdateOne(ctx, bson.M{"title": "Review PR"}, bson.M{"$set": bson.M{"done": true}})
fmt.Println("matched:", ur.MatchedCount, "modified:", ur.ModifiedCount)

ur2, _ := tasks.UpdateMany(ctx, bson.M{"priority": 1, "done": false}, bson.M{"$set": bson.M{"priority": 0}})
fmt.Println("matched:", ur2.MatchedCount, "modified:", ur2.ModifiedCount)
```
```
matched: 1 modified: 1
matched: 1 modified: 1
```

Delete, and the actual document count at the end:

```go
dr, _ := tasks.DeleteOne(ctx, bson.M{"done": true})
fmt.Println("deleted_count:", dr.DeletedCount)

dr2, _ := tasks.DeleteMany(ctx, bson.M{"done": false})
fmt.Println("deleted_count:", dr2.DeletedCount)

count, _ := tasks.CountDocuments(ctx, bson.M{})
fmt.Println(count)
```
```
deleted_count: 1
deleted_count: 2
1
```

Same result as pymongo: `1`, for the same reason traced above — one `done: true` document always survives `DeleteOne`, and `DeleteMany({done: false})` never touches it.

## The mongosh mirror

Same operations, shell syntax, for reference:

```javascript
db.tasks.insertMany([...]);
db.tasks.find({ done: false }, { _id: 0, title: 1 });
db.tasks.updateOne({ title: "Review PR" }, { $set: { done: true } });
db.tasks.updateMany({ priority: 1, done: false }, { $set: { priority: 0 } });
db.tasks.deleteOne({ done: true });
db.tasks.deleteMany({ done: false });
db.tasks.countDocuments({});
```

## Common mistakes

- **Passing a raw replacement instead of an update document.** `update_one({"title": "x"}, {"done": True})` (no `$set`) doesn't merge `done` into the document — MongoDB rejects it, because a top-level key with no `$` operator is treated as a full **replacement** document, and `updateOne`'s replacement form requires the entire target document to be replaced. Always use an operator (`$set`, etc.) unless you genuinely intend to replace the whole document.
- **Assuming `updateMany`'s filter re-evaluates per document as the batch runs.** It doesn't (see above) — this occasionally surprises people writing "propagate a status change" logic that assumes each update sees the effects of the one before it within the same `updateMany` call.
- **Forgetting `find` returns a cursor.** `db.tasks.find({})` on its own does nothing observable until you iterate, call `.to_list()`, or otherwise consume it — a common "why did nothing happen" moment for people used to a call that returns a materialized list immediately.
- **(Go) Not checking `cur.Err()` after manually iterating a cursor with `for cur.Next(ctx)`.** A network error mid-iteration stops `Next` from returning `true` — silently identical to "no more documents" unless you check `cur.Err()` once the loop ends. `cur.All(ctx, &slice)` (used above) checks this for you internally, which is part of why it's the default choice for anything that fits in memory.
- **Confusing `deleteMany({})` with `drop()`.** `deleteMany({})` empties the collection but keeps it (and its indexes) registered; `drop()` removes the collection entirely, indexes included. If you're about to rebuild indexes anyway, `drop()` is usually what you want in a demo/reset script — that's exactly why every level in this module starts with a `drop()`.

Level 03 goes deeper into the filter half of this picture: the comparison/logical/existence operators that make "find everything matching X" expressive.
