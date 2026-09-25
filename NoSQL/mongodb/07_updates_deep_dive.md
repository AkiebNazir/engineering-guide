# Updates Deep Dive

Level 02 introduced `updateOne`/`updateMany` with a single `$set`. This level covers the rest of the update-operator vocabulary you need for anything beyond "replace a scalar field": incrementing counters, appending to arrays, keeping array values unique, removing matching elements, upserting, and — the trickiest one — updating exactly one specific element inside an array, not the whole array.

## Setup

```python
db.carts.insert_one({
    "_id": "cart_1",
    "user": "njasm",
    "views": 0,
    "tags": ["electronics"],
    "items": [
        {"sku": "mouse", "qty": 1},
        {"sku": "cable", "qty": 3},
    ],
})
```

## `$set` — write a field's value

```python
db.carts.update_one({"_id": "cart_1"}, {"$set": {"user": "njasm786"}})
```
```
{'_id': 'cart_1', 'user': 'njasm786', 'views': 0, 'tags': ['electronics'],
 'items': [{'sku': 'mouse', 'qty': 1}, {'sku': 'cable', 'qty': 3}]}
```

Already covered in level 02 — included here as the baseline the rest of this level builds on.

## `$inc` — atomic increment/decrement

```python
db.carts.update_one({"_id": "cart_1"}, {"$inc": {"views": 1}})
db.carts.update_one({"_id": "cart_1"}, {"$inc": {"views": 5}})
```
```
'views': 6
```

`$inc` reads and writes the new value in a single atomic server-side operation — critically different from doing `views = db.carts.find_one(...)["views"]; views += 1; db.carts.update_one(..., {"$set": {"views": views}})` in application code, which has a race condition: two concurrent requests can both read `views: 0`, both compute `1`, and both write `1` — losing an increment. `$inc` never has that race, because the read-modify-write happens inside the server, atomically, per document. A negative value decrements. This is the same category of bug as a non-atomic `counter++` in any concurrent system — always prefer the database's atomic operator over read-then-write-in-app-code when the operation is a pure function of the current value.

## `$push` — append to an array

```python
db.carts.update_one({"_id": "cart_1"}, {"$push": {"items": {"sku": "keyboard", "qty": 1}}})
```
```
'items': [{'sku': 'mouse', 'qty': 1}, {'sku': 'cable', 'qty': 3}, {'sku': 'keyboard', 'qty': 1}]
```

`$push` always appends, even if the value is already present — it's not concerned with uniqueness. Wrapping the value in `{"$each": [...]}` pushes multiple elements in one call instead of one `$push` per element (not shown above, but worth knowing: `{"$push": {"items": {"$each": [item1, item2]}}}`).

## `$addToSet` — append only if not already present

```python
r1 = db.carts.update_one({"_id": "cart_1"}, {"$addToSet": {"tags": "electronics"}})  # already there
r2 = db.carts.update_one({"_id": "cart_1"}, {"$addToSet": {"tags": "office"}})       # new
print(r1.modified_count, r2.modified_count)
```
```
0 1
```
```
'tags': ['electronics', 'office']
```

`modified_count: 0` for the duplicate confirms `$addToSet` genuinely checked membership rather than blindly appending — "electronics" was already in the array, so nothing changed; "office" was not, so it was added. `$addToSet` does an exact-value equality check (including nested document equality field-by-field-and-order for object elements), not a deep semantic comparison — two objects with the same fields in a different key order are NOT treated as equal duplicates.

## `$pull` — remove matching elements

```python
db.carts.update_one({"_id": "cart_1"}, {"$pull": {"items": {"sku": "cable"}}})
```
```
'items': [{'sku': 'mouse', 'qty': 1}, {'sku': 'keyboard', 'qty': 1}]
```

`$pull`'s argument is a query filter (any operator from level 03 works: `{"qty": {"$lt": 2}}`, `{"sku": {"$in": [...]}}`), applied against each array element — every matching element is removed in one call, not just the first.

## `upsert: true` — update-or-insert in one call

```python
r = db.carts.update_one(
    {"_id": "cart_2"},
    {"$set": {"user": "guest"}, "$setOnInsert": {"views": 0, "items": []}},
    upsert=True,
)
print("matched:", r.matched_count, "upserted_id:", r.upserted_id)
```
```
matched: 0   upserted_id: cart_2
```
```
cart_2 after upsert: {'_id': 'cart_2', 'user': 'guest', 'views': 0, 'items': []}
```

No document matched `{"_id": "cart_2"}`, so `upsert=True` told MongoDB to **insert** a new document instead — built from the filter (`_id: "cart_2"`) plus the update's `$set`/`$setOnInsert` fields. `$setOnInsert` is specifically "only apply this on the insert branch of an upsert" — it's how you seed defaults (`views: 0`, empty `items`) without also resetting them back to defaults on a normal update-existing-document call. `matched_count` staying `0` (rather than the driver faking a `1`) is the tell that the upsert branch fired instead of a real match.

Upserts are the standard pattern for "create this record if it doesn't exist, otherwise touch it" — a shopping cart keyed by session ID, a per-day counter document, a user's settings row — anywhere you'd otherwise write an explicit `find_one` + branch in application code with its own race condition (two concurrent requests both seeing "doesn't exist" and both trying to insert). `upsert` avoids that race the same way `$inc` avoids the counter race: the check-and-act happens atomically inside the server. (A duplicate-key race is still possible under concurrent upserts on a *non-`_id`* unique key without careful index/retry handling — worth knowing as a limit, not a blanket guarantee.)

## `arrayFilters` — update one specific element inside an array

`$set`/`$inc` on a bare array path like `"items.qty"` would apply to every element, or none — it has no way to say "only the mouse one." **`arrayFilters`** plus the `$[identifier]` positional syntax solves exactly this: update the one element (or subset) matching a condition, leave the rest of the array untouched.

```python
db.carts.update_one(
    {"_id": "cart_1"},
    {"$inc": {"items.$[elem].qty": 10}},
    array_filters=[{"elem.sku": "mouse"}],
)
```
```
'items': [{'sku': 'mouse', 'qty': 11}, {'sku': 'keyboard', 'qty': 1}]
```

`items.$[elem]` is a placeholder — `elem` is bound by `array_filters` to whichever array element(s) satisfy `{"elem.sku": "mouse"}`. Only the mouse item's `qty` went from 1 to 11; the keyboard item, also in the array, was untouched. Without `arrayFilters` you'd either need to know the array *index* up front (`items.0.qty` — fragile, breaks the moment the array's order changes) or fetch the whole document, mutate it in application code, and write the entire array back (throwing away the atomicity `$inc` gives you, and racing with any concurrent update to a *different* element of the same array).

## The full operator set, in Go

Every operator here is the identical `$`-prefixed map key as Python — the only real difference is `arrayFilters`, which Go sets through an options struct rather than a keyword argument:

```go
carts.UpdateOne(ctx, bson.M{"_id": "cart_1"}, bson.M{"$set": bson.M{"user": "njasm786"}})
carts.UpdateOne(ctx, bson.M{"_id": "cart_1"}, bson.M{"$inc": bson.M{"views": 1}})
carts.UpdateOne(ctx, bson.M{"_id": "cart_1"}, bson.M{"$inc": bson.M{"views": 5}})
```
```
views: 6
```

```go
carts.UpdateOne(ctx, bson.M{"_id": "cart_1"}, bson.M{"$push": bson.M{"items": bson.M{"sku": "keyboard", "qty": 1}}})

r1, _ := carts.UpdateOne(ctx, bson.M{"_id": "cart_1"}, bson.M{"$addToSet": bson.M{"tags": "electronics"}})
r2, _ := carts.UpdateOne(ctx, bson.M{"_id": "cart_1"}, bson.M{"$addToSet": bson.M{"tags": "office"}})
fmt.Println(r1.ModifiedCount, r2.ModifiedCount)
```
```
0 1
```

```go
carts.UpdateOne(ctx, bson.M{"_id": "cart_1"}, bson.M{"$pull": bson.M{"items": bson.M{"sku": "cable"}}})
```
```
items after pull: [{"sku":"mouse","qty":1} {"sku":"keyboard","qty":1}]
```

Upsert, via `options.UpdateOne().SetUpsert(true)` instead of a keyword argument:

```go
opts := options.UpdateOne().SetUpsert(true)
r3, _ := carts.UpdateOne(ctx, bson.M{"_id": "cart_2"},
    bson.M{"$set": bson.M{"user": "guest"}, "$setOnInsert": bson.M{"views": 0, "items": bson.A{}}}, opts)
fmt.Println("matched:", r3.MatchedCount, "upserted_id:", r3.UpsertedID)
```
```
matched: 0 upserted_id: cart_2
```

`arrayFilters`, via `options.UpdateOne().SetArrayFilters(...)`:

```go
afOpts := options.UpdateOne().SetArrayFilters([]interface{}{bson.M{"elem.sku": "mouse"}})
carts.UpdateOne(ctx, bson.M{"_id": "cart_1"}, bson.M{"$inc": bson.M{"items.$[elem].qty": 10}}, afOpts)
```
```
items after arrayFilters: [{"sku":"mouse","qty":11} {"sku":"keyboard","qty":1}]
```

Every result above is identical to the corresponding Python result — `arrayFilters` is a server-side feature; Go's `options.UpdateOne()` builder pattern (chainable `Set*` methods) is simply this driver's idiomatic way of expressing what pymongo passes as `array_filters=[...]`/`upsert=True` keyword arguments.

## Common mistakes

- **Reaching for read-then-write in application code instead of `$inc`/`$push`/`$addToSet`.** Every one of these operators exists specifically to make a read-modify-write atomic on the server. If you find yourself calling `find_one` immediately before a `$set` that only depends on the value you just read, there's almost always an atomic operator that does the same thing without the race.
- **Using `$push` when you meant `$addToSet`.** `$push` doesn't check for duplicates — a "tags" array can silently accumulate the same tag five times if the wrong operator was used in a retry path.
- **Trying to update an array element with a plain field path instead of `arrayFilters`.** `{"$set": {"items.qty": 99}}` is not "set every item's qty to 99" — MongoDB rejects a positional-less path into an array of sub-documents like that outright, precisely because it's ambiguous which element you meant.
- **Forgetting `$setOnInsert` and reusing `$set` for upsert defaults.** Fields under a bare `$set` get applied on *every* upsert call, matched or not — using `$set` where you meant `$setOnInsert` will reset a field back to its default on every subsequent "touch" call, not just the first insert.

Level 08 covers the opposite instinct from this whole level's flexibility: how to opt back into enforced structure with a <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> Schema validator, and when that tradeoff is worth making.
