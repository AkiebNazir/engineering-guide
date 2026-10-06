# The Document Model

MongoDB stores data as **documents** — ordered sets of key/value pairs, structurally like a JSON object — grouped into **collections**. A collection is loosely the analogue of a SQL table, and a document is loosely the analogue of a row, but the shape underneath is different enough that the analogy breaks if you lean on it too hard, so treat it as an orientation aid, not a rulebook.

```javascript
// mongosh
db.products.insertOne({
  name: "Wireless Mouse",
  price: 29.99,
  tags: ["electronics", "accessories"],
  in_stock: true,
  added_at: new Date("2026-01-15"),
  dimensions: { width_cm: 6, height_cm: 3.5 },
  qty: NumberInt(120)
});

db.products.findOne();
```

Real output from a running `mongo:7` instance:

```javascript
{
  _id: ObjectId('6ab3b02f35f7d89b4e6e6891'),
  name: 'Wireless Mouse',
  price: 29.99,
  tags: [ 'electronics', 'accessories' ],
  in_stock: true,
  added_at: ISODate('2026-01-15T00:00:00.000Z'),
  dimensions: { width_cm: 6, height_cm: 3.5 },
  qty: 120
}
```

One document holds a string, a float, an array, a boolean, a date, a nested sub-document, and an explicitly-typed 32-bit integer — no `CREATE TABLE` was involved, no column list was declared anywhere, and every field simply exists because the `insertOne` call put it there.

## Documents, collections, BSON

- A **document** is the unit of storage — everything above, from `_id` down to `qty`, is one document.
- A **collection** (`db.products`) is a named group of documents, roughly comparable to a table, but with no requirement that its documents share a shape.
- A **database** (`lab_00_document_model` above) is a group of collections, physically its own set of files on disk.
- On the wire and on disk, documents are **BSON** ("Binary JSON") — not literal JSON text. BSON adds types JSON doesn't have (dates, `ObjectId`, distinct `int32`/`int64`/`double`/`decimal128` numeric types, binary blobs) and is length-prefixed for fast field skipping, which is why `typeof qty` printed `number` in JavaScript but the type MongoDB actually stored was a real 32-bit integer, not a float — mongosh's driver hides the BSON/JS type gap by default. This matters most for numbers: `NumberInt(120)` and `120.0` look identical printed back, but they're different wire types, and an aggregation like `$sum` or a schema validator (see level 08) can behave differently depending on which one is actually stored. When it matters, check with `db.products.find().hint(...)` mongosh tricks or, more simply, in a language driver where the type comes back as a real distinct object (Python's `bson` module surfaces `Int64` vs `int` vs `float` explicitly).

## "Schemaless" is the wrong word

MongoDB is commonly described as "schemaless." That's misleading — there is always a schema, in the sense that your application code somewhere assumes a document has a `price` field of a certain type and a `tags` array. What MongoDB does NOT do is **enforce** that schema at the database layer by default. Two documents in the same `products` collection can have completely different fields:

```javascript
db.products.insertOne({ name: "USB Cable", price: 4.99 });          // no tags, no dimensions
db.products.insertOne({ name: "Monitor", price: 199, refurb: true }); // a field nothing else has
```

Both inserts succeed. The more accurate term is **flexible schema**: the shape lives in your application (and optionally, per level 08, in an opt-in validator attached to the collection) rather than being declared once and enforced unconditionally by the database engine on every write.

This flexibility is a genuine design tool, not just looseness:

- It lets you add a new field to new documents without an `ALTER TABLE`-equivalent migration touching every existing row.
- It lets a single collection hold naturally variant documents (a `payments` collection where a `credit_card` payment and a `paypal` payment have almost nothing in common except a `type` field and a total).
- It pushes the schema-design decision to where it actually belongs in a document database: not "what columns does this table have," but "what shape does one aggregate object need to be so my application can read it in a single fetch" — see level 04, which is the real skill this model is teaching you to develop.

The flip side, covered honestly across this module rather than glossed over: no enforced schema means a typo'd field name (`pryce` instead of `price`) is silently accepted as a brand new field, not rejected. Document databases push that correctness burden onto validation you add deliberately (level 08) or onto application-level discipline — it does not disappear, it moves.

## Compared to the relational model

You already know SQL from the `content/data-and-apis/SQL/` module, so here's the map rather than a re-derivation of relational concepts:

| Relational | MongoDB | Where it actually diverges |
|---|---|---|
| Database | Database | Same idea. |
| Table | Collection | A collection has no declared column list by default. |
| Row | Document | A document can nest arrays and sub-documents; a row cell cannot hold another row. |
| Column | Field | Fields vary per document unless a validator (level 08) is attached. |
| Primary key | `_id` field | Every document gets one automatically if you don't supply it (level 01). |
| `JOIN` | `$lookup`, or embedding | MongoDB's default answer to "related data" is to embed it in one document, not to normalize and join (levels 04, 06). |
| Foreign key constraint | Nothing built in | Referential integrity across documents is the application's job unless you enforce it in code. |
| Schema (`CREATE TABLE`) | Optional JSON Schema validator | Enforced only if you opt in, and only at write time, not retroactively. |
| Multi-row transaction | Multi-document transaction | Supported since 4.0 on replica sets, but positioned as an escape hatch, not the default tool — see level 09. |

The one-sentence version: a relational database starts from "normalize, then join when you need related data back together"; MongoDB starts from "store the aggregate your application actually reads together, in one document, and reach for joins or transactions only when embedding stops making sense." Level 04 is where that decision gets made concretely, with a worked example.

## Try it in the browser

The ▶ Run buttons on this page run a mongosh-like shell in your browser, over the Query Lab's shop data: `customers`, `products`, `orders` and `reviews` (shapes in [the datasets README](../lab/datasets/README.md)). Writes stay in this page's session, and pressing Run on a block first runs the earlier blocks on the page, so the inserts above have already happened by the time you get here.

Start with one real order. Notice how much of it is not a flat row: `customer` is a sub-document, `items` is an array of sub-documents, `status_history` is an array of `{ status, at }` pairs with real dates, and `coupon` is just there (other orders don't have one).

```js
db.orders.findOne({ _id: 10001 })
```

Flexible schema in real data: a phone, a pair of trousers and a foam roller all live in `products`, and each one's `attributes` sub-document has whatever fields make sense for that kind of product.

```js
db.products.find(
  { _id: { $in: [101, 161, 204] } },
  { _id: 0, name: 1, category: 1, attributes: 1 }
)
```

Every document still has a BSON type per field, even with no schema declared. `$type` reports it: `_id` was stored as an `int`, `total` as a `double`, `ordered_at` as a real `date` (not a string), and a field the document doesn't have (`gift_wrap`) is `"missing"`, which is a different thing from `null`.

```js
db.orders.aggregate([
  { $match: { _id: 10001 } },
  { $project: {
      _id: { $type: "$_id" }, total: { $type: "$total" }, ordered_at: { $type: "$ordered_at" },
      customer: { $type: "$customer" }, items: { $type: "$items" }, gift_wrap: { $type: "$gift_wrap" }
  } }
])
```

Optional fields in this dataset are left out rather than set to `null`. Count how many customers have a phone number and how many simply don't have the field:

```js
({
  withPhone: db.customers.countDocuments({ phone: { $exists: true } }),
  withoutPhone: db.customers.countDocuments({ phone: { $exists: false } }),
  total: db.customers.countDocuments({})
})
```

The cost of "nothing is enforced": a typo is a new field, not an error. The insert succeeds, and the lamp then silently drops out of every query that filters or sorts on `price`. Only a query for the missing field finds it.

```js
db.products.insertOne({ name: "Desk Lamp", pryce: 39 });
db.products.find({ price: { $exists: false } }, { _id: 0, name: 1, pryce: 1 })
```

Because the order is the aggregate your application reads, one query can reach into its embedded parts with dot notation: orders from Japan that contain a pair of headphones, returning just the customer's name and the item names.

```js
db.orders.find(
  { "customer.country": "Japan", "items.category": "Headphones" },
  { "customer.name": 1, "items.name": 1 }
).limit(3)
```

## What's ahead in this ladder

Levels 01–03 build fluency with the basics (connecting, CRUD, query operators). Level 04 is the pivotal schema-design skill. Levels 05–08 cover performance and structure (indexes, aggregation, update operators, validation). Levels 09–10 cover the distributed-systems side (transactions, replication, write/read concern). Level 11 ties it into a small production-shaped service module.
