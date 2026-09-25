# The Document Model

MongoDB stores data as **documents** — ordered sets of key/value pairs, structurally like a <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> object — grouped into **collections**. A collection is loosely the analogue of a <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> table, and a document is loosely the analogue of a row, but the shape underneath is different enough that the analogy breaks if you lean on it too hard, so treat it as an orientation aid, not a rulebook.

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
- On the wire and on disk, documents are **BSON** ("Binary <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>") — not literal <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> text. BSON adds types <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> doesn't have (dates, `ObjectId`, distinct `int32`/`int64`/`double`/`decimal128` numeric types, binary blobs) and is length-prefixed for fast field skipping, which is why `typeof qty` printed `number` in JavaScript but the type MongoDB actually stored was a real 32-bit integer, not a float — mongosh's driver hides the BSON/JS type gap by default. This matters most for numbers: `NumberInt(120)` and `120.0` look identical printed back, but they're different wire types, and an aggregation like `$sum` or a schema validator (see level 08) can behave differently depending on which one is actually stored. When it matters, check with `db.products.find().hint(...)` mongosh tricks or, more simply, in a language driver where the type comes back as a real distinct object (Python's `bson` module surfaces `Int64` vs `int` vs `float` explicitly).

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

You already know <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> from the `SQL/` module, so here's the map rather than a re-derivation of relational concepts:

| Relational | MongoDB | Where it actually diverges |
|---|---|---|
| Database | Database | Same idea. |
| Table | Collection | A collection has no declared column list by default. |
| Row | Document | A document can nest arrays and sub-documents; a row cell cannot hold another row. |
| Column | Field | Fields vary per document unless a validator (level 08) is attached. |
| Primary key | `_id` field | Every document gets one automatically if you don't supply it (level 01). |
| `JOIN` | `$lookup`, or embedding | MongoDB's default answer to "related data" is to embed it in one document, not to normalize and join (levels 04, 06). |
| Foreign key constraint | Nothing built in | Referential integrity across documents is the application's job unless you enforce it in code. |
| Schema (`CREATE TABLE`) | Optional <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> Schema validator | Enforced only if you opt in, and only at write time, not retroactively. |
| Multi-row transaction | Multi-document transaction | Supported since 4.0 on replica sets, but positioned as an escape hatch, not the default tool — see level 09. |

The one-sentence version: a relational database starts from "normalize, then join when you need related data back together"; MongoDB starts from "store the aggregate your application actually reads together, in one document, and reach for joins or transactions only when embedding stops making sense." Level 04 is where that decision gets made concretely, with a worked example.

## What's ahead in this ladder

Levels 01–03 build fluency with the basics (connecting, <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr>, query operators). Level 04 is the pivotal schema-design skill. Levels 05–08 cover performance and structure (indexes, aggregation, update operators, validation). Levels 09–10 cover the distributed-systems side (transactions, replication, write/read concern). Level 11 ties it into a small production-shaped service module.
