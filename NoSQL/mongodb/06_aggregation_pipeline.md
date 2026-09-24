# The Aggregation Pipeline

`find` answers "which documents match, shaped how." The **aggregation pipeline** answers a bigger question: "transform, group, and combine documents through a sequence of stages," each stage feeding its output to the next — the same mental model as a Unix pipe, applied to documents instead of text lines.

## The problem this level solves

Two collections:

```python
db.customers.insert_many([
    {"_id": "cust_1", "name": "Alice Nguyen", "country": "US"},
    {"_id": "cust_2", "name": "Bruno Silva", "country": "PT"},
    {"_id": "cust_3", "name": "Chidi Okafor", "country": "NG"},
])

db.orders.insert_many([
    {"_id": "order_1", "customer_id": "cust_1", "status": "completed", "placed_at": ISODate("2026-03-01"),
     "items": [{"sku": "mouse", "qty": 2, "price": 29.99}, {"sku": "cable", "qty": 1, "price": 4.99}]},
    {"_id": "order_2", "customer_id": "cust_1", "status": "completed", "placed_at": ISODate("2026-03-15"),
     "items": [{"sku": "keyboard", "qty": 1, "price": 49.5}]},
    {"_id": "order_3", "customer_id": "cust_2", "status": "completed", "placed_at": ISODate("2026-03-10"),
     "items": [{"sku": "monitor", "qty": 2, "price": 199.0}]},
    {"_id": "order_4", "customer_id": "cust_2", "status": "cancelled", "placed_at": ISODate("2026-03-12"),
     "items": [{"sku": "webcam", "qty": 1, "price": 59.0}]},
    {"_id": "order_5", "customer_id": "cust_3", "status": "completed", "placed_at": ISODate("2026-02-20"),
     "items": [{"sku": "mouse", "qty": 1, "price": 29.99}]},
])
```

**The question:** for each customer, total spend on *completed* orders placed in *March 2026*, with the customer's name and country attached, sorted highest spend first. That's a filter, a fan-out over a nested array, a sum grouped by customer, a join to another collection, a reshape, and a sort — six real operations, which is exactly why this needs a pipeline rather than one `find` call.

## Building it stage by stage

### `$match` — filter documents (do this first, always)

```python
{"$match": {
    "status": "completed",
    "placed_at": {"$gte": datetime(2026, 3, 1), "$lt": datetime(2026, 4, 1)},
}}
```

Same filter language as `find` (level 03) — `$match` is just a pipeline stage wrapping it. Putting `$match` first matters: it shrinks the working set before any of the more expensive stages run, and it's the one stage that can use an index the same way `find` would.

### `$unwind` — fan an array field out into one document per element

Each order has an `items` array; to sum spend per line item, we need one pipeline document per item, not per order.

```python
{"$unwind": "$items"}
```

After `$match` + `$unwind`, real output (order_4 is gone — cancelled; order_5 is gone — February; the remaining orders' array items are now separate documents):

```
{'_id': 'order_1', 'customer_id': 'cust_1', 'item': {'sku': 'mouse', 'qty': 2, 'price': 29.99}}
{'_id': 'order_1', 'customer_id': 'cust_1', 'item': {'sku': 'cable', 'qty': 1, 'price': 4.99}}
{'_id': 'order_2', 'customer_id': 'cust_1', 'item': {'sku': 'keyboard', 'qty': 1, 'price': 49.5}}
{'_id': 'order_3', 'customer_id': 'cust_2', 'item': {'sku': 'monitor', 'qty': 2, 'price': 199.0}}
```

`order_1` (two items) produced two documents; every other surviving order (one item each) produced one. This is the concrete meaning of "unwind" — a 1-document-with-an-array-of-3 becomes 3 documents.

### `$group` — aggregate by a key

```python
{"$group": {
    "_id": "$customer_id",
    "total_spent": {"$sum": {"$multiply": ["$items.qty", "$items.price"]}},
    "line_items": {"$sum": 1},
}}
```

Real output after this stage:

```
{'_id': 'cust_2', 'total_spent': 398.0, 'line_items': 1}
{'_id': 'cust_1', 'total_spent': 114.47, 'line_items': 3}
```

`$group`'s `_id` is the grouping key (here, `customer_id`) — every other field is an accumulator (`$sum`, `$avg`, `$max`, `$min`, `$push` to collect values into an array, etc.) computed across all documents sharing that key. `cust_1`'s `114.47` is `2×29.99 + 1×4.99 + 1×49.5` across its 3 surviving line items; `cust_3` doesn't appear at all — it had no line items left after `$match` removed its only (February) order.

### `$lookup` — MongoDB's answer to a SQL JOIN

We have customer IDs, not names. `$lookup` performs a **left outer join** against another collection in the same database — this is the direct, explicit answer to "how do I join in MongoDB":

```python
{"$lookup": {
    "from": "customers",
    "localField": "_id",         # the grouped customer_id, from the previous stage
    "foreignField": "_id",       # customers._id
    "as": "customer",            # result goes into this new array field
}}
```

`$lookup` always attaches its match as an **array** field (`customer`, here holding 0 or more matching documents — 0 if the join found nothing, which is why it's specifically a *left outer* join, not an inner join: unmatched left-side documents are kept, just with an empty array). Since `_id` is unique in `customers`, we know there's at most one match, so we immediately flatten it:

```python
{"$unwind": "$customer"}
```

### `$project` — reshape the output

```python
{"$project": {
    "_id": 0,
    "customer_id": "$_id",
    "name": "$customer.name",
    "country": "$customer.country",
    "total_spent": {"$round": ["$total_spent", 2]},
    "line_items": 1,
}}
```

`$project` in aggregation is a superset of `find`'s projection — it can rename fields, reach into nested paths (`$customer.name`), and apply expressions (`$round`), not just include/exclude.

### `$sort` — order the final result

```python
{"$sort": {"total_spent": -1}}
```

## The full pipeline, real result

```python
pipeline = [
    {"$match": {"status": "completed",
                "placed_at": {"$gte": datetime(2026, 3, 1), "$lt": datetime(2026, 4, 1)}}},
    {"$unwind": "$items"},
    {"$group": {"_id": "$customer_id",
                "total_spent": {"$sum": {"$multiply": ["$items.qty", "$items.price"]}},
                "line_items": {"$sum": 1}}},
    {"$lookup": {"from": "customers", "localField": "_id", "foreignField": "_id", "as": "customer"}},
    {"$unwind": "$customer"},
    {"$project": {"_id": 0, "customer_id": "$_id", "name": "$customer.name",
                  "country": "$customer.country",
                  "total_spent": {"$round": ["$total_spent", 2]}, "line_items": 1}},
    {"$sort": {"total_spent": -1}},
]
results = list(db.orders.aggregate(pipeline))
```

Real output:

```python
[{'country': 'PT', 'customer_id': 'cust_2', 'line_items': 1, 'name': 'Bruno Silva', 'total_spent': 398.0},
 {'country': 'US', 'customer_id': 'cust_1', 'line_items': 3, 'name': 'Alice Nguyen', 'total_spent': 114.47}]
```

`cust_3` (Chidi) correctly does not appear — the only fact that mattered about their one order (placed in February, outside the window) was filtered out in the very first stage, and an empty `$group` input just means "no output row," not an error.

## The full pipeline, in Go

A pipeline is a `mongo.Pipeline` (a `[]bson.D` — an ordered list, since pipeline stage *order* matters, unlike a filter document's keys) of `bson.D` stages, each one the same shape as the Python dicts above with `$`-operators as ordinary map keys:

```go
pipeline := mongo.Pipeline{
    bson.D{{Key: "$match", Value: bson.M{
        "status":    "completed",
        "placed_at": bson.M{"$gte": d("2026-03-01"), "$lt": d("2026-04-01")},
    }}},
    bson.D{{Key: "$unwind", Value: "$items"}},
    bson.D{{Key: "$group", Value: bson.M{
        "_id":         "$customer_id",
        "total_spent": bson.M{"$sum": bson.M{"$multiply": bson.A{"$items.qty", "$items.price"}}},
        "line_items":  bson.M{"$sum": 1},
    }}},
    bson.D{{Key: "$lookup", Value: bson.M{
        "from": "customers", "localField": "_id", "foreignField": "_id", "as": "customer",
    }}},
    bson.D{{Key: "$unwind", Value: "$customer"}},
    bson.D{{Key: "$project", Value: bson.M{
        "_id": 0, "customer_id": "$_id", "name": "$customer.name", "country": "$customer.country",
        "total_spent": bson.M{"$round": bson.A{"$total_spent", 2}}, "line_items": 1,
    }}},
    bson.D{{Key: "$sort", Value: bson.M{"total_spent": -1}}},
}

cur, _ := orders.Aggregate(ctx, pipeline)
var results []bson.M
cur.All(ctx, &results)
```

Real output — identical result to the Python pipeline above:

```
{"line_items":{"$numberInt":"1"},"customer_id":"cust_2","name":"Bruno Silva","country":"PT","total_spent":{"$numberDouble":"398.0"}}
{"line_items":{"$numberInt":"3"},"customer_id":"cust_1","name":"Alice Nguyen","country":"US","total_spent":{"$numberDouble":"114.47"}}
```

**Why `mongo.Pipeline` (`[]bson.D`) and not `bson.A`/`[]bson.M`:** a `bson.M` is a Go map, and Go maps have no guaranteed iteration/marshaling order — irrelevant for a filter document (where key order never matters), but a pipeline's stage order is the entire meaning of the pipeline (`$group` before `$unwind` silently changes the answer, as the "Common mistakes" section below already warns). `mongo.Pipeline` is a thin `type Pipeline []bson.D` alias specifically so the compiler and the driver both treat pipeline stage order as load-bearing, matching the ordered Python list (`pipeline = [...]`) the Python version already relies on for the same reason.

## Common mistakes

- **Putting `$match` late, or not at all before an expensive stage.** `$match` first lets MongoDB use an index and shrinks the pipeline's working set immediately — putting it after `$unwind`/`$lookup` means those expensive stages run over documents you're about to throw away anyway.
- **Forgetting `$lookup` is a *left outer* join, always.** If the foreign collection has no match, `as` becomes an **empty array**, not a missing field and not `null`. Downstream code (or a bare `$unwind` without `preserveNullAndEmptyArrays: true`) that assumes the array always has exactly one element will silently drop those documents at the `$unwind` stage — worth remembering when a `$lookup` result is smaller than expected and the join looked correct.
- **Confusing `$project`'s `1`/`0` inclusion-exclusion mixing rules with `find`'s.** Same rule as level 03 (can't generally mix inclusion and exclusion), but `$project` additionally lets a field be a whole new *expression*, which occasionally leads to writing `{"field": 1}` when what you actually needed was `{"field": "$otherField"}`.
- **Running `$group` before `$unwind` when you meant per-item aggregation.** `$group` operates on whatever the current pipeline documents look like — group before unwinding an array and you're grouping whole orders, not line items, which silently changes the answer rather than erroring.

Level 07 goes deep on the update side: the operators (`$set`, `$inc`, `$push`, `$addToSet`, `$pull`), `upsert`, and `arrayFilters` for updating one specific element inside an array.
