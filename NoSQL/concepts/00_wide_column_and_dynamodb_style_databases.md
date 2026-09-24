# Wide-Column and DynamoDB-Style Databases

**No lab container for this one** — unlike every other level in `NoSQL/`, this is a
concept-and-design level, not a hands-on one (Cassandra/DynamoDB aren't in this repo's
`docker-compose.databases.yml`). Everything stated here is a factual description of how
these systems work, not a measured number from this machine — the "measured, not
asserted" rule that governs every other level in this repo applies to claims *this repo
can measure*; where it can't, this level says so explicitly instead of fabricating a
number.

**Why this level exists:** wide-column stores are the fourth family named in
`NoSQL/README.md`'s landscape table but deliberately left without a hands-on module
there. They come up constantly in interviews anyway — DynamoDB especially, given how
common it is in real systems — so "recognize and place it" (the README's original bar)
is raised here to "design a schema for it," which is closer to what's actually asked.

## The mental model

A wide-column store looks like a table with rows and columns, but the resemblance to
SQL stops there:

- **Partitioning is a first-class, explicit part of the data model**, not an
  infrastructure decision layered on afterward (contrast `SQL/18`, where sharding is
  bolted onto a model that wasn't designed for it). Every row has a **partition key**
  that decides which physical node owns it — you choose this key at schema design
  time, and it is the single most consequential decision in the design.
- **A composite key is (partition key, sort/clustering key).** All rows sharing a
  partition key are stored together, physically sorted by the sort key — this is what
  makes "give me all of X's events between time A and B" a single, fast,
  single-partition range scan instead of a distributed query.
- **No joins, ever.** The data model expects you to denormalize at write time so every
  read is satisfiable from one partition — the exact opposite instinct from `SQL/16`'s
  "normalize by default." This is a deliberate, load-bearing design choice: at the
  scale these systems target (many terabytes, sustained massive write throughput), a
  cross-partition join would defeat the entire point of partitioning.
- **Writes are append-heavy and LSM-tree-backed** (Cassandra, HBase, and DynamoDB's
  underlying engine all use log-structured merge trees) — the same write-optimized
  structure `CSFundamentals/03_databases_deep_dive.md` already covers for B-tree vs.
  LSM tradeoffs, at the storage-engine level. Writes are cheap (append to an in-memory
  structure, flush to disk in sorted runs); reads may need to check multiple on-disk
  runs, which background **compaction** merges down over time.

## DynamoDB specifically — the one most interviews reach for

| Concept | What it means |
|---|---|
| **Partition key** | Hashed to pick the physical partition. Must be high-cardinality and evenly distributed, or you get a **hot partition** — one node absorbing disproportionate traffic while others sit idle (the same hot-shard problem `SQL/18` names for range-sharded relational data, structurally guaranteed away here only if the key is chosen well) |
| **Sort key** (optional) | Orders items within a partition; enables range queries and "give me the latest N" access patterns without a full scan |
| **Local Secondary Index (LSI)** | Alternate sort key, same partition key — must be created at table creation, shares the base table's partition |
| **Global Secondary Index (GSI)** | Alternate partition+sort key entirely, its own capacity, eventually consistent by default — the mechanism for "I need to query by a field that isn't my primary access pattern" |
| **Tunable consistency** | Reads default to **eventually consistent** (cheaper, may read stale data just after a write) with an opt-in to **strongly consistent** reads (pricier, always reflects the latest successful write, unavailable across regions) |
| **RCU/WCU or on-demand capacity** | Provisioned or on-demand throughput units — the pricing/capacity model directly reflects the "no joins, pay per access pattern" design, unlike a relational database's single compute tier serving arbitrary queries |

## Single-table design — the pattern that surprises people coming from SQL

The idiomatic DynamoDB pattern is to put **multiple, differently-shaped entity types
into one table**, distinguished by a deliberately generic key naming convention, so
that one query against one partition can answer what SQL would need a join for.
A worked example — an e-commerce system's customer and their orders:

```text
Table: AppTable
 PK              | SK              | attributes...
-----------------+-----------------+------------------------------
 CUSTOMER#123    | PROFILE         | name, email, city
 CUSTOMER#123    | ORDER#2026-01-05| total: 69.98, status: shipped
 CUSTOMER#123    | ORDER#2026-02-11| total: 199.99, status: pending
```

**Go — illustrative only, not run against a live table** (there is no DynamoDB
container in this repo's lab stack, so unlike every hands-on level in `NoSQL/`, this
is not a captured real run; it's the shape of the call, using the official
`github.com/aws/aws-sdk-go-v2/service/dynamodb` client):

```go
_, err := client.PutItem(ctx, &dynamodb.PutItemInput{
    TableName: aws.String("AppTable"),
    Item: map[string]types.AttributeValue{
        "PK":     &types.AttributeValueMemberS{Value: "CUSTOMER#123"},
        "SK":     &types.AttributeValueMemberS{Value: "ORDER#2026-02-11"},
        "total":  &types.AttributeValueMemberN{Value: "199.99"},
        "status": &types.AttributeValueMemberS{Value: "pending"},
    },
})

// One query returns the customer's profile AND every order, in one partition:
out, err := client.Query(ctx, &dynamodb.QueryInput{
    TableName:              aws.String("AppTable"),
    KeyConditionExpression: aws.String("PK = :pk"),
    ExpressionAttributeValues: map[string]types.AttributeValue{
        ":pk": &types.AttributeValueMemberS{Value: "CUSTOMER#123"},
    },
})
```

Notice `PutItem`'s `Item` map has no fixed schema in the Go type system either — every
attribute is boxed as a `types.AttributeValue` (a Go interface with one implementation
per DynamoDB type: `...MemberS` for a string, `...MemberN` for a number), which is how
a strongly-typed language like Go still expresses DynamoDB's genuinely schemaless
per-item attributes: the schema flexibility lives in the *data*, not erased by using Go
instead of a dynamically-typed language.

One query — `PK = CUSTOMER#123`, no sort-key condition — returns the customer's
profile *and* every one of their orders in a single request to a single partition, in
sort-key (and therefore chronological, given the `ORDER#<date>` key) order. This is
the direct DynamoDB-native answer to the SQL question "show me this customer and their
order history," which in Postgres would be a join across two normalized tables
(`SQL/16`). The tradeoff is explicit: this table can answer *this specific access
pattern* extremely well and cannot easily answer a pattern it wasn't designed for
("find every order over $150 across all customers" needs a GSI built for it, or a full
scan) — access patterns must be enumerated **before** the schema is designed, the
reverse of the relational default of designing the schema from the entities first and
writing whatever query you need afterward.

## Cassandra, briefly — the same partition+sort model, no vendor lock-in

Cassandra predates DynamoDB and uses the same partition-key/clustering-column model
(`CREATE TABLE events (device_id text, ts timestamp, reading double, PRIMARY KEY
(device_id, ts))` — `device_id` is the partition key, `ts` the clustering column,
identical in spirit to the DynamoDB sort key above). Its headline architectural
difference from DynamoDB is **tunable consistency per-query via replication factor and
consistency level** (`ONE`, `QUORUM`, `ALL`) rather than a binary
eventual/strong toggle — a read/write pair using `QUORUM` on both sides
(`R + W > N`, where `N` is the replication factor) is guaranteed to overlap on at least
one replica that has the latest write, giving strong consistency without needing every
replica to respond. This `R + W > N` formula is the single fact about Cassandra most
worth being able to state precisely in an interview.

## Common mistakes

- **Designing a wide-column schema the way you'd design a relational one** —
  normalizing into many small tables defeats the model; the correct instinct is
  "denormalize for the access pattern," the mirror image of `SQL/16`.
- **Choosing a low-cardinality partition key** (e.g., partitioning by `status` with
  three possible values) — guarantees a hot partition, since all rows sharing a value
  land on the same node.
- **Assuming DynamoDB reads are always strongly consistent.** The default is eventually
  consistent; strong consistency is opt-in, costs more, and isn't available for global
  (cross-region) reads at all.
- **Forgetting that GSIs are eventually consistent by default and have their own
  capacity** — a GSI can throttle independently of the base table.

## What's next

`concepts/01_choosing_a_database_and_cap_theorem.md` ties this family, MongoDB,
Redis, and `SQL/` together into one decision framework — the actual question an
interviewer is usually building toward when they ask "walk me through the database
options here."
