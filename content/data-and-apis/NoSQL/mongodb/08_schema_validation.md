# Schema Validation

Level 00 called flexible schema a genuine design tool, but also flagged the cost honestly: nothing stops a typo'd field or a wrong type from being silently accepted. **Schema validation** is the opt-in mechanism for taking some of that structure back — at the collection level, enforced by the server on writes, without giving up the flexibility everywhere you don't need it.

## Defining a validator

Validators are attached to a collection at creation time (or added later with `collMod`), written as a **JSON Schema** wrapped in `$jsonSchema`:

```python
schema = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["email", "balance", "status"],
        "properties": {
            "email": {
                "bsonType": "string",
                "pattern": "^.+@.+\\..+$",
                "description": "must be a string matching an email pattern",
            },
            "balance": {
                "bsonType": ["double", "int"],
                "minimum": 0,
                "description": "must be a non-negative number",
            },
            "status": {
                "enum": ["active", "suspended", "closed"],
                "description": "must be one of the enum values",
            },
        },
    }
}

db.create_collection("accounts", validator=schema, validationLevel="strict", validationAction="error")
```

This says: every document in `accounts` must have `email`, `balance`, and `status`; `email` must be a string matching a basic email shape; `balance` must be a non-negative number; `status` must be one of three fixed strings. Nothing else is constrained — a document could still carry any additional field the schema doesn't mention, because JSON Schema's default is to allow unlisted properties unless you explicitly set `additionalProperties: false`.

## What gets rejected, and how

```python
db.accounts.insert_one({"email": "a@example.com", "balance": 100.0, "status": "active"})
# succeeds
```

```python
db.accounts.insert_one({"email": "b@example.com", "balance": 50.0})  # missing "status"
```
```
WriteError: Document failed validation
code: 121
```

Real, structured detail from the same failure (pymongo's `WriteError.details["errInfo"]`) — this is what actually comes back, not a generic message:

```json
{
  "failingDocumentId": "6ab3b1f763c11f9e9da6f6ad",
  "details": {
    "operatorName": "$jsonSchema",
    "schemaRulesNotSatisfied": [
      {
        "operatorName": "properties",
        "propertiesNotSatisfied": [
          {
            "propertyName": "email",
            "description": "must be a string matching an email pattern",
            "details": [
              {
                "operatorName": "pattern",
                "specifiedAs": {"pattern": "^.+@.+\\..+$"},
                "reason": "regular expression did not match",
                "consideredValue": "not-an-email"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

(this particular capture is from the `"not-an-email"` case — MongoDB's error tells you exactly which sub-rule failed and what value it saw, which is far more actionable than a bare "validation failed.")

All four ways to violate this schema were tested live and all four were rejected the same way (`code: 121`, `"Document failed validation"`):

| Bad input | Rule violated |
|---|---|
| `{"email": "b@x.com", "balance": 50.0}` | missing required `status` |
| `{"email": "not-an-email", ...}` | `email` fails the `pattern` regex |
| `{"balance": -5, ...}` | `balance` fails `minimum: 0` |
| `{"status": "vip", ...}` | `status` not in the `enum` list |

Final count in the collection after all five attempts (1 valid + 4 rejected): **1**.

## The same validator, defined and exercised from Go

The `$jsonSchema` document is identical BSON either way — Go builds it as nested `bson.M`/`bson.A` instead of a Python dict/list, and attaches it via `options.CreateCollection().SetValidator(...)` rather than a `create_collection` keyword argument:

```go
schema := bson.M{
    "$jsonSchema": bson.M{
        "bsonType": "object",
        "required": bson.A{"email", "balance", "status"},
        "properties": bson.M{
            "email":   bson.M{"bsonType": "string", "pattern": `^.+@.+\..+$`},
            "balance": bson.M{"bsonType": bson.A{"double", "int"}, "minimum": 0},
            "status":  bson.M{"enum": bson.A{"active", "suspended", "closed"}},
        },
    },
}

db.CreateCollection(ctx, "accounts",
    options.CreateCollection().SetValidator(schema).SetValidationLevel("strict").SetValidationAction("error"))
```

Running the identical valid insert plus the same four bad documents:

```go
_, err := accounts.InsertOne(ctx, bson.M{"email": "a@example.com", "balance": 100.0, "status": "active"})
// err is nil

_, err = accounts.InsertOne(ctx, bson.M{"email": "b@example.com", "balance": 50.0})   // missing status
fmt.Println(err)
```

Real output — all four rejections, same rules, same server-side detail (the Go driver's write error wraps the identical structured `errInfo` the Python section shows, just formatted as Go's default error string instead of pymongo's `WriteError.details`):

```
valid insert error: <nil>
rejected: true -> write exception: write errors: [Document failed validation: {"failingDocumentId": ...,
  "details": {"operatorName": "$jsonSchema", "schemaRulesNotSatisfied": [
    {"operatorName": "required", "missingProperties": ["status"]}]}}]
rejected: true -> ... "propertyName": "email", "operatorName": "pattern", "consideredValue": "not-an-email" ...
rejected: true -> ... "propertyName": "balance", "operatorName": "minimum", "consideredValue": -5 ...
rejected: true -> ... "propertyName": "status", "operatorName": "enum", "consideredValue": "vip" ...
final count: 1
```

Same 1-valid-plus-4-rejected outcome as the Python run. The validator itself is a server-side artifact of the collection — it rejects (or, in `warn` mode below, lets through and logs) a bad document identically regardless of which driver or language sent the `insertOne` call; only the shape of the returned `error`/exception differs per language.

Warn mode, same `accounts_warn` behavior:

```go
db.CreateCollection(ctx, "accounts_warn",
    options.CreateCollection().SetValidator(schema).SetValidationLevel("strict").SetValidationAction("warn"))
_, err = db.Collection("accounts_warn").InsertOne(ctx, bson.M{"email": "bad", "balance": -1, "status": "not-valid"})
```
```
warn-mode insert error: <nil>
warn collection count: 1
```

The insert succeeded (`err` is `nil`) despite violating every rule in the schema — identical to the Python section's "Insert SUCCEEDED despite violating schema."

## `validationAction`: `error` vs `warn`

`validationAction` controls what happens when a document *fails* validation — `"error"` (the default, used above) rejects the write outright. `"warn"` logs the violation to the server log but **lets the write through anyway**:

```python
db.create_collection("accounts_warn", validator=schema, validationLevel="strict", validationAction="warn")
db.accounts_warn.insert_one({"email": "bad", "balance": -1, "status": "not-valid"})
```
```
Insert SUCCEEDED despite violating schema (logged as a warning server-side, not rejected).
count: 1
```

`"warn"` is a **rollout tool**, not a real enforcement mode: it's how you introduce a new validator against a collection that already has non-conforming documents in production, watch the logs to see how much real traffic would actually be rejected, fix the offending write paths, and only then flip to `"error"` once the log goes quiet. Shipping straight to `"error"` on an existing collection with unknown data risks rejecting legitimate traffic you didn't anticipate.

## `validationLevel`: `strict` vs `moderate`

`validationLevel` controls which writes get checked at all:

- **`strict`** (used above, and the default): every insert and every update is validated.
- **`moderate`**: only validates inserts and updates to documents that **already pass** the validator. A pre-existing document that doesn't conform is left alone on updates that don't otherwise touch its invalid fields — useful for the same "we're mid-rollout, don't break old data further" reason `warn` exists, but applied to already-invalid documents rather than new writes.

## When and why to add this back

Reach for a validator when:

- **A collection is written from multiple places** (several services, or a service plus ad-hoc scripts/migrations) and you want one enforced contract instead of trusting every writer's application-level checks to stay correct forever.
- **A field's correctness matters enough that a typo should be loud, not silent** — a `status` enum, a currency code, anything where an unexpected value would cause a downstream bug that's hard to trace back to "someone inserted a bad document six weeks ago."
- **You want the schema itself documented somewhere machine-readable**, not just implied by whatever the application code happens to do — the validator is inspectable with `db.getCollectionInfos()`, independent of any one service's source code.

Don't reach for it as a default on every collection — the entire value proposition of level 00's flexible schema (add a field to new documents without a migration) is undermined the moment `additionalProperties: false` or an overly strict `required` list is bolted onto a collection whose shape is still evolving. Validate the fields that are load-bearing for correctness; leave everything else free.

## Common mistakes

- **Setting `validationAction: "error"` on day one against an existing, unaudited collection.** You will reject writes you didn't know existed. Roll out with `"warn"` first.
- **Forgetting `additionalProperties` defaults to allowed.** A schema with a `required` and `properties` list does *not* by itself reject documents with extra fields — you must set `additionalProperties: false` explicitly if that's the intent, and doing so re-introduces exactly the migration-on-every-new-field cost that flexible schema was meant to avoid, so do it deliberately.
- **Validating a type too loosely.** `"balance": {"bsonType": ["double", "int"]}` above intentionally accepts both BSON numeric types, because a naive `bsonType: "double"` alone would reject a perfectly valid integer `50` inserted from a language driver that sends whole numbers as `int32`/`int64` — a very common false rejection if you don't test with a real driver, not just `mongosh` literals.
- **Assuming the validator is retroactive.** Attaching a validator to a collection does **not** check documents already in it — only future writes. Existing bad data stays exactly as it is until something writes to it again.

Level 09 moves to the other structural safety net MongoDB offers: multi-document ACID transactions — what they cost, and, just as importantly, when embedding (level 04) means you never needed one in the first place.
