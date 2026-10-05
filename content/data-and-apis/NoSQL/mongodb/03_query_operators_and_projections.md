# Query Operators and Projections

Level 02's filters were all equality (`{"done": False}`). MongoDB's filter language grows into a small expression system built from `$`-prefixed operators for comparison, logic, and field existence, plus a separate mini-language for shaping which fields come back. Every result below is real output from `lab_03_query` on the live instance:

```python
db.products.insert_many([
    {"name": "USB Cable",      "price": 4.99,  "category": "accessories", "stock": 50},
    {"name": "Wireless Mouse", "price": 29.99, "category": "accessories", "stock": 12},
    {"name": "Monitor",        "price": 199.0, "category": "displays",    "stock": 0},
    {"name": "Keyboard",       "price": 49.5,  "category": "accessories", "stock": 8},
    {"name": "Webcam",         "price": 59.0,  "category": "accessories"},  # no stock field at all
    {"name": "Laptop Stand",   "price": 35.0,  "category": "accessories", "stock": 20},
])
```

## Comparison operators: `$eq`, `$gt`, `$lt`, `$in`

A bare `{"field": value}` is shorthand for `{"field": {"$eq": value}}` — you almost never write `$eq` explicitly for that reason, but it's the operator underneath every equality filter you've already been writing.

```python
db.products.find({"price": {"$gt": 40}}, {"_id": 0, "name": 1, "price": 1})
```
```
{'name': 'Monitor', 'price': 199.0}
{'name': 'Keyboard', 'price': 49.5}
{'name': 'Webcam', 'price': 59.0}
```

```python
db.products.find({"price": {"$lt": 40}}, {"_id": 0, "name": 1, "price": 1})
```
```
{'name': 'USB Cable', 'price': 4.99}
{'name': 'Wireless Mouse', 'price': 29.99}
{'name': 'Laptop Stand', 'price': 35.0}
```

`$gte`/`$lte`/`$ne` follow the same pattern (not shown — they're the obvious extensions).

`$in` matches if the field equals *any* value in a given array — the equivalent of SQL's `IN (...)`:

```python
db.products.find(
    {"category": {"$in": ["displays", "accessories"]}, "price": {"$gt": 50}},
    {"_id": 0, "name": 1, "price": 1, "category": 1})
```
```
{'name': 'Monitor', 'price': 199.0, 'category': 'displays'}
{'name': 'Webcam', 'price': 59.0, 'category': 'accessories'}
```

Note two conditions in the same filter document (`category` and `price`) are implicitly **AND**ed together — you only need an explicit `$and` when you need multiple conditions *on the same field*, or logical grouping that isn't just "every top-level key must match."

## Logical operators: `$and`, `$or`

```python
db.products.find(
    {"$and": [{"price": {"$gt": 20}}, {"stock": {"$exists": True}}, {"stock": {"$gt": 0}}]},
    {"_id": 0, "name": 1, "price": 1, "stock": 1})
```
```
{'name': 'Wireless Mouse', 'price': 29.99, 'stock': 12}
{'name': 'Keyboard', 'price': 49.5, 'stock': 8}
{'name': 'Laptop Stand', 'price': 35.0, 'stock': 20}
```

That query could actually be written without `$and` (as three implicit top-level ANDs), since none of the conditions repeat a field — `$and` is genuinely required only when you need the same field tested twice (e.g. a price range: `{"$and": [{"price": {"$gt": 10}}, {"price": {"$lt": 50}}]}`, since a single filter document can't have the key `"price"` twice).

`$or` is where it earns its keep — there's no implicit-AND equivalent for "either of these":

```python
db.products.find(
    {"$or": [{"price": {"$lt": 10}}, {"stock": 0}]},
    {"_id": 0, "name": 1, "price": 1, "stock": 1})
```
```
{'name': 'USB Cable', 'price': 4.99, 'stock': 50}
{'name': 'Monitor', 'price': 199.0, 'stock': 0}
```

Cheap, expensive-looking items or out-of-stock items — two unrelated conditions, either one qualifying a document.

## `$exists`: field presence, not value

`$exists` checks whether the field is present in the document at all — it says nothing about the field's value. This matters specifically because of the flexible schema from level 00: "Webcam" has no `stock` field whatsoever (never set, not `0`), which is a different fact from "Monitor" having `stock: 0`.

```python
db.products.find({"stock": {"$exists": False}}, {"_id": 0, "name": 1})
```
```
{'name': 'Webcam'}
```

Only "Webcam" comes back — "Monitor" has `stock: 0`, which is a present field with a falsy value, not a missing field, and `$exists: False` correctly does not match it. This is a common bug source coming from SQL, where every row structurally has every column (possibly `NULL`); in MongoDB, "field is missing" and "field is `null`" and "field is `0`/`false`/`""`" are three genuinely different states, and `$exists` only tests the first one. If you want "missing OR null," write `{"$or": [{"field": {"$exists": False}}, {"field": None}]}` explicitly.

## Projections: shaping what comes back

The second argument to `find` controls which fields are returned. There are two forms, and **you generally cannot mix them** (aside from always being allowed to exclude `_id` alongside an inclusion projection — that's a specific carve-out, not a general rule).

**Inclusion** — list only the fields you want:

```python
db.products.find({"category": "accessories"}, {"_id": 0, "name": 1, "price": 1})
```
```
{'name': 'USB Cable', 'price': 4.99}
{'name': 'Wireless Mouse', 'price': 29.99}
{'name': 'Keyboard', 'price': 49.5}
{'name': 'Webcam', 'price': 59.0}
{'name': 'Laptop Stand', 'price': 35.0}
```

**Exclusion** — list only the fields you want dropped, keep everything else:

```python
db.products.find({"category": "accessories"}, {"category": 0, "stock": 0})
```
```
{'_id': ObjectId('...'), 'name': 'USB Cable', 'price': 4.99}
{'_id': ObjectId('...'), 'name': 'Wireless Mouse', 'price': 29.99}
{'_id': ObjectId('...'), 'name': 'Keyboard', 'price': 49.5}
{'_id': ObjectId('...'), 'name': 'Webcam', 'price': 59.0}
{'_id': ObjectId('...'), 'name': 'Laptop Stand', 'price': 35.0}
```

Notice `_id` came back this time even though it wasn't mentioned — exclusion mode keeps everything not explicitly excluded, and `_id` is included by default unless you say `{"_id": 0}`. That's the one field allowed to appear in an otherwise-inclusion projection (`{"_id": 0, "name": 1}` above is technically mixing inclusion with one exclusion, which MongoDB special-cases just for `_id`).

Projections aren't just cosmetic — a projection that only needs fields already present in an index lets MongoDB answer the query straight from the index without touching the documents at all (a **covered query**). Level 05 shows this concretely with `.explain()`.

## The same filters in Go

Filter documents are `bson.M` either way; the driver has no separate "query builder" type — you write the same `$gt`/`$in`/`$and`/`$or`/`$exists` shapes as literal maps, same as pymongo's dicts:

```go
cur, _ := products.Find(ctx,
    bson.M{"price": bson.M{"$gt": 40}},
    options.Find().SetProjection(bson.M{"_id": 0, "name": 1, "price": 1}))
var docs []bson.M
cur.All(ctx, &docs)
for _, d := range docs { fmt.Println(d) }
```
```
{"name":"Monitor","price":{"$numberDouble":"199.0"}}
{"price":{"$numberDouble":"49.5"},"name":"Keyboard"}
{"name":"Webcam","price":{"$numberDouble":"59.0"}}
```

`$in`, one array-valued operator that needs Go's `bson.A` (a `[]any`, BSON's array type) instead of a plain Go slice literal inside a `bson.M`:

```go
cur, _ = products.Find(ctx,
    bson.M{
        "category": bson.M{"$in": bson.A{"displays", "accessories"}},
        "price":    bson.M{"$gt": 50},
    },
    options.Find().SetProjection(bson.M{"_id": 0, "name": 1, "price": 1, "category": 1}))
```
```
{"price":{"$numberDouble":"199.0"},"category":"displays","name":"Monitor"}
{"name":"Webcam","price":{"$numberDouble":"59.0"},"category":"accessories"}
```

`$and`/`$or` follow the identical shape, also via `bson.A` for their list of sub-filters — a real run of the `$or` (cheap-or-out-of-stock) filter confirms the exact same two matches as the Python version: `USB Cable` (stock 50, price 4.99) and `Monitor` (stock 0). `$exists: false` also matches the same single result, `Webcam` — the flexible-schema distinction from level 00 (missing field vs. `stock: 0`) is a server-side, filter-language fact, not something either driver changes.

**Projections, and the one Go-specific quirk to know:** Go's driver has no `_id: 0`-only special case beyond what the server itself allows — inclusion vs. exclusion mixing rules are enforced server-side, identically regardless of client language, so the same "can't mix inclusion and exclusion, except `_id`" rule from the Python section applies unchanged. What *is* Go-specific: decoding an exclusion projection (where the field set isn't known ahead of time) into `bson.M` prints every surviving field, including `_id`, in **non-deterministic key order** — real output, run twice:

```go
cur, _ = products.Find(ctx, bson.M{"category": "accessories"}, options.Find().SetProjection(bson.M{"category": 0, "stock": 0}))
```
```
{"_id":{"$oid":"6ab3f68c0df7a91b8ced4a2c"},"price":{"$numberDouble":"4.99"},"name":"USB Cable"}
{"name":"Wireless Mouse","price":{"$numberDouble":"29.99"},"_id":{"$oid":"6ab3f68c0df7a91b8ced4a2d"}}
```

Notice `_id`, `price`, and `name` appear in a *different order* between the first and second document — `bson.M` is a Go `map[string]any`, and Go's map iteration order is intentionally randomized. This is purely a display artifact of decoding into a generic map (the actual BSON documents on the wire and on disk have a defined field order); decoding into a typed struct with ordered `bson:"..."` tags instead of `bson.M` avoids it entirely, and is generally the better choice once a document's shape is known ahead of time rather than being discovered ad hoc.

## Common mistakes

- **(Go) Forgetting `bson.A` for array-valued operators.** A plain Go slice (`[]string{"a", "b"}`) inside a `bson.M` for `$in`/`$and`/`$or` will actually still marshal correctly in most cases via reflection, but `bson.A` (`[]any`) is the driver's own explicit BSON array type and is the idiomatic, always-safe choice — especially once the array holds mixed types (a `bson.M` alongside a string, as in `$or` above).
- **Mixing inclusion and exclusion on other fields.** `{"name": 1, "stock": 0}` throws `Projection cannot have a mix of inclusion and exclusion` — pick one mode per query (`_id` is the sole exception).
- **Using `$exists: true` when you meant "not null."** A field can exist and be `null` — `$exists` doesn't filter that case out. Chain `{"$ne": None}` if you specifically mean "present and not null."
- **Forgetting implicit AND across top-level keys.** Writing `{"$or": [...], "category": "accessories"}` is valid and ANDs the `$or` clause with `category` — easy to misread as "OR everything," when actually only the listed `$or` branches are ORed together; the `category` condition is a separate, mandatory AND term.
- **Reaching for `$and`/`$or` where a compound index (level 05) would answer the same query faster.** The operators are correct either way; the cost only shows up under load, which is exactly why the next levels build toward indexes and `.explain()`.

Level 04 shifts from querying to schema *design*: whether related data belongs inside one document or split across a reference — the single most consequential decision in modeling anything in MongoDB.
