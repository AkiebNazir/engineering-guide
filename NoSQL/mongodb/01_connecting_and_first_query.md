# Connecting and Your First Query

Before touching any query language, get comfortable with two connection paths to the same server: `mongosh` (the interactive/scripting shell you'll reach for constantly) and `pymongo` (what your application code actually uses). Everything in this level was run against a real `mongo:7` container — the lab environment described in this module's README, reachable at `mongodb://localhost:27018`.

## Connecting with mongosh

```javascript
// From a terminal:
//   mongosh "mongodb://localhost:27018"
// You land in a REPL already connected, default database "test".

use lab_01_connecting        // switches (and lazily creates) a database
db.users.drop();             // start clean — collections are created on first write anyway

var result = db.users.insertOne({ name: "Ada Lovelace", role: "engineer", age: 28 });
printjson(result);

var doc = db.users.findOne({ name: "Ada Lovelace" });
printjson(doc);
```

Real output:

```javascript
{
  acknowledged: true,
  insertedId: ObjectId('6ab3afaadfc1927f875071af')
}
{
  _id: ObjectId('6ab3afaadfc1927f875071af'),
  name: 'Ada Lovelace',
  role: 'engineer',
  age: 28
}
```

A few things to notice immediately:

- `use lab_01_connecting` does not create the database on disk yet — MongoDB creates a database (and a collection) lazily, on the first write. If you `use somedb` and never write to it, `show dbs` won't list it.
- `insertOne` returns an acknowledgment object, not the document itself. `acknowledged: true` means the write was confirmed by the server under the connection's write concern (level 10 goes deep on what "confirmed" actually means and how to tune it).
- Nobody supplied `_id`. MongoDB generated one — a 12-byte `ObjectId` — and injected it into the document before storing it.

## Connecting with pymongo

The Python driver mirrors the shell's shape closely. `MongoClient` is the connection handle; indexing it like a dict gets you a database, and indexing that gets you a collection.

```python
from pymongo import MongoClient
from bson import ObjectId

client = MongoClient("mongodb://localhost:27018")
db = client["lab_01_connecting"]
db.users.drop()

result = db.users.insert_one({"name": "Ada Lovelace", "role": "engineer", "age": 28})
print("inserted_id:", result.inserted_id, type(result.inserted_id))

doc = db.users.find_one({"name": "Ada Lovelace"})
print("found:", doc)
print("is ObjectId:", isinstance(doc["_id"], ObjectId))

client.close()
```

Real output, run against the same container:

```
inserted_id: 6ab3afb50f508c39008ab2d6 <class 'bson.objectid.ObjectId'>
found: {'_id': ObjectId('6ab3afb50f508c39008ab2d6'), 'name': 'Ada Lovelace', 'role': 'engineer', 'age': 28}
is ObjectId: True
```

Naming note: mongosh uses `camelCase` (`insertOne`, `findOne`); pymongo uses `snake_case` (`insert_one`, `find_one`) to match Python convention, but the operations and the wire protocol underneath are identical. If you can do it in one, you can name the pymongo equivalent by snake-casing it — this holds for nearly the entire <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr> and aggregation <abbr title="Application Programming Interface">API</abbr> across both.

## Connecting with Go (`mongo-driver/v2`)

The official Go driver keeps the same document-oriented shape — a `Client` wraps a connection pool, `Database`/`Collection` are thin handles, and every call takes a `context.Context` explicitly (Go has no implicit default timeout the way a bare pymongo call does — you decide the deadline at the call site).

```go
import (
    "context"
    "fmt"

    "go.mongodb.org/mongo-driver/v2/bson"
    "go.mongodb.org/mongo-driver/v2/mongo"
    "go.mongodb.org/mongo-driver/v2/mongo/options"
)

ctx := context.Background()
client, err := mongo.Connect(options.Client().ApplyURI("mongodb://localhost:27018"))
// handle err
defer client.Disconnect(ctx)

users := client.Database("lab_01_connecting").Collection("users")
users.Drop(ctx)

res, err := users.InsertOne(ctx, bson.M{"name": "Ada Lovelace", "role": "engineer", "age": 28})
fmt.Printf("inserted_id: %s %T\n", res.InsertedID.(bson.ObjectID).Hex(), res.InsertedID)

var doc bson.M
users.FindOne(ctx, bson.M{"name": "Ada Lovelace"}).Decode(&doc)
fmt.Println("found:", doc)
_, isOID := doc["_id"].(bson.ObjectID)
fmt.Println("is ObjectID:", isOID)
```

Real output, run against the same container:

```
inserted_id: 6ab3f61ee8073888878995f8 bson.ObjectID
found: {"_id":{"$oid":"6ab3f61ee8073888878995f8"},"name":"Ada Lovelace","role":"engineer","age":{"$numberInt":"28"}}
is ObjectID: true
```

Two things worth noticing immediately against the Python version above:

- **`bson.M` (a `map[string]any`) prints as Extended <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>, not Go's normal `map[...]` syntax** — the driver gives `bson.M` a `String()`/<abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> marshaler so a printed document is still human-readable, but every scalar comes back tagged with its BSON type (`{"$numberInt":"28"}`, not bare `28`) unless you decode into a concrete Go struct instead of a generic map. Decoding into a typed struct with `bson:"age"` tags avoids this entirely and is the more idiomatic approach for real application code — `bson.M` is mainly for ad hoc/exploratory code, exactly like this level's demo.
- **`InsertedID` comes back as `any`**, requiring a type assertion (`res.InsertedID.(bson.ObjectID)`) to get the concrete `bson.ObjectID` — pymongo's `result.inserted_id` is already the concrete `ObjectId` Python type with no cast needed, one of the small frictions of Go's static typing meeting a dynamically-shaped document model.

Duplicate `_id`, same enforced-uniqueness behavior as pymongo, surfaced as a Go `error` instead of a Python exception:

```go
_, err = users.InsertOne(ctx, bson.M{"_id": "ada_lovelace", "role": "engineer"})
_, err = users.InsertOne(ctx, bson.M{"_id": "ada_lovelace", "role": "duplicate"})
fmt.Println("duplicate _id insert error:", err)
```
```
duplicate _id insert error: write exception: write errors: [E11000 duplicate key error collection: lab_01_connecting.users index: _id_ dup key: { _id: "ada_lovelace" }]
```

Go has no exceptions — every driver call that can fail returns an `error` as its last return value, checked explicitly at the call site, rather than pymongo's `DuplicateKeyError` being raised and caught. The underlying server-side error code (`E11000`) is identical either way — it's a MongoDB server behavior, not a driver one.

## `_id` and `ObjectId`, precisely

Every document in a MongoDB collection has an `_id` field, and MongoDB **enforces uniqueness of `_id` within a collection** with an index it creates automatically (`_id_`) — this is the one piece of implicit schema/index every collection always has, even a totally validator-free one.

If you don't supply `_id` yourself, the driver generates an `ObjectId`: a 12-byte value, not a random <abbr title="Universally Unique Identifier - A 128-bit label used for information in computer systems to ensure uniqueness across distributed systems.">UUID</abbr>, structured as:

```
| 4 bytes: unix timestamp (seconds) | 5 bytes: random, per-process | 3 bytes: incrementing counter |
```

Two consequences worth internalizing:

1. **`ObjectId`s are roughly time-ordered.** Sorting a collection by `_id` ascending is (loosely) sorting by insertion time — genuinely useful for "recently created" queries without a separate `created_at` field, though not a substitute for one when you need real timestamp semantics (clock skew across a replica set, explicit timezone handling).
2. **You can supply your own `_id`.** It doesn't have to be an `ObjectId` — a string, a number, even a compound sub-document works, as long as it's unique in the collection. This is common when your document has a natural key already (e.g. a username, or an ID from an upstream system you're mirroring) and you want the uniqueness constraint enforced for free rather than adding a second unique index.

```python
db.users.insert_one({"_id": "ada_lovelace", "role": "engineer"})
# db.users.insert_one({"_id": "ada_lovelace", "role": "duplicate"})  # would raise DuplicateKeyError
```

## Common mistakes

- **Assuming `find_one`/`findOne` with no filter returns "the first inserted document."** It returns *a* document matching the (empty) filter with no guaranteed order unless you sort. Don't rely on insertion order without an explicit `sort()`.
- **Forgetting a write only fully lands once acknowledged.** `insert_one` under default settings waits for acknowledgment before returning, but that default is a write-concern choice, not a law of nature — level 10 covers what changes when you loosen or tighten it.
- **Treating `ObjectId` as a random <abbr title="Universally Unique Identifier - A 128-bit label used for information in computer systems to ensure uniqueness across distributed systems.">UUID</abbr>.** It's structured and leaks a creation timestamp (`ObjectId.generation_time` in pymongo, or decode the first 4 bytes yourself) — don't expose raw `_id` values somewhere that timestamp leak matters (e.g. as a public <abbr title="Application Programming Interface">API</abbr>'s opaque identifier if you want to hide creation order/volume from competitors).

The next level builds outward from `insertOne`/`findOne` into the rest of <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr>.
