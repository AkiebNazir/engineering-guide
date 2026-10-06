# Sharding: Shard Keys, Chunks, and the Balancer

Level 10's replica set copies **all** the data to every member. That scales reads (more secondaries) and survives failures, but every member still has to hold the whole dataset and the single primary still takes every write. When the data outgrows one machine's disk or RAM, or the write rate outgrows one primary, MongoDB's answer is **sharding**: split one collection's documents across several replica sets (**shards**), each holding a slice, and put a router in front so the application still sees one collection.

Everything about how well that works comes down to one decision you make up front, the **shard key**: the field(s) MongoDB uses to decide which shard owns each document. A good shard key spreads writes evenly *and* lets most queries go to one shard. A bad one sends every insert to the same shard or turns every query into a broadcast, and it's expensive to change later. This level builds a real two-shard cluster, loads the same data under three different shard keys, and measures where the writes land and how queries are routed.

For the general theory of partitioning (hash vs. range partitioning, rebalancing, hot spots), see [Sharding and Horizontal Scaling](../../SQL/18_sharding_and_horizontal_scaling.md) and [Database Internals: How They Actually Work](../../../interview-core/SystemDesign/building_blocks/06_database_internals.md). This level is the MongoDB-specific mechanics.

## The parts of a sharded cluster

```arch
%% caption: The application talks only to mongos routers. mongos keeps a cached copy of the routing table (which key ranges live on which shard) from the config servers and sends each operation to the shard(s) that own the data.
node app "App servers" at 1,0 icon=server sub="MongoClient"
node m "mongos routers" at 1,1 icon=gateway sub="stateless, one per host"
group cfgrs "Config servers" color=purple
node cfg "Config replica set" at 2.5,1 in cfgrs icon=db sub="chunk ranges, zones"
group sa "Shard A" color=green
node a "shA replica set" at 0,2 in sa icon=db sub="some key ranges"
group sb "Shard B" color=green
node b "shB replica set" at 2,2 in sb icon=db sub="the other ranges"
app -> m
m -> a
m -> b
m ..> cfg : "routing table"
```

- **Shards**: each shard is a full replica set (level 10), so each slice of data is itself replicated and fails over on its own.
- **`mongos`**: the router. It holds no data, just a cached routing table, so you run as many as you like (commonly one per application host). Your driver connects to `mongos` exactly as it would to a replica set, and most application code doesn't change.
- **Config servers**: a replica set holding the cluster metadata: which collections are sharded, their shard keys, which key ranges (**chunks**) live on which shard, and zone definitions. `mongos` reads from them and caches. If the cache is stale (a chunk moved), the shard rejects the request with a stale-config error and `mongos` refreshes and retries transparently.

### What this lab ran on

The module's `docker-compose.databases.yml` gives you a single-node replica set, which can't be sharded. For this level a small **real** sharded cluster was started from the same `mongo:7` image: one config server replica set, two single-member shard replica sets (`shA`, `shB`) and one `mongos` on port 27100. The script (run it inside a `mongo:7` container with `--network host`):

```bash
mkdir -p /data/cfg /data/a /data/b
mongod --configsvr --replSet cfg --port 27101 --dbpath /data/cfg --fork --logpath /data/cfg.log
mongod --shardsvr   --replSet shA --port 27201 --dbpath /data/a   --fork --logpath /data/a.log
mongod --shardsvr   --replSet shB --port 27301 --dbpath /data/b   --fork --logpath /data/b.log
mongosh --port 27101 --eval 'rs.initiate({_id:"cfg",configsvr:true,members:[{_id:0,host:"localhost:27101"}]})'
mongosh --port 27201 --eval 'rs.initiate({_id:"shA",members:[{_id:0,host:"localhost:27201"}]})'
mongosh --port 27301 --eval 'rs.initiate({_id:"shB",members:[{_id:0,host:"localhost:27301"}]})'
mongos --configdb cfg/localhost:27101 --port 27100 --fork --logpath /data/mongos.log
mongosh --port 27100 --eval 'sh.addShard("shA/localhost:27201"); sh.addShard("shB/localhost:27301")'
```

Production clusters use three-member replica sets for the config servers and for every shard; one member each is enough to observe routing and balancing. The chunk size was also lowered from the default 128 MB to 1 MB (`db.getSiblingDB("config").settings.updateOne({_id: "chunksize"}, {$set: {value: 1}}, {upsert: true})`) so that 40 MB of test data behaves the way 5 GB would at the default.

## Chunks: how a collection is split

MongoDB divides a sharded collection's **shard-key space** into contiguous ranges called **chunks** (the newer docs also say "ranges"). Each chunk `[min, max)` belongs to exactly one shard. For a ranged key, a document with `createdAt = 2026-03-01` belongs to whichever chunk's range contains that value. For a **hashed** key, MongoDB first hashes the field's value to a 64-bit integer and the chunks are ranges of *hash values*.

Chunks move between shards in the background. The **balancer** (a process on the config server primary) compares how much data each shard holds for a collection. When the difference between the most and least loaded shard exceeds about three times the chunk size, it migrates a range from the fuller shard to the emptier one. Since MongoDB 6.0.3 the balancer works from **data size**, not chunk count, and chunks are no longer auto-split as you insert; they're split when they need to move.

A migration copies the documents to the recipient, catches up on writes made during the copy, then commits by updating the config servers. The donor deletes its copies later (after `orphanCleanupDelaySecs`, 15 minutes by default). Until then they're **orphaned documents**: still on disk, not owned. Queries through `mongos` filter them out, but storage statistics (and direct connections to a shard) include them, which is a real source of confusing numbers.

## Three shard keys, one workload

Three collections, identical data, different shard keys:

```javascript
sh.enableSharding("shop");
sh.shardCollection("shop.orders_by_time",  { createdAt: 1 });                 // ranged, monotonic
sh.shardCollection("shop.orders_hashed",   { customerId: "hashed" });         // hashed
sh.shardCollection("shop.orders_compound", { customerId: 1, createdAt: 1 });  // ranged, compound
```

Right after creation, before any data:

```text
orders_by_time  chunks: [{"_id":"shA","n":1}]
orders_hashed   chunks: [{"_id":"shA","n":2},{"_id":"shB","n":2}]
orders_compound chunks: [{"_id":"shA","n":1}]
```

A **ranged** key on an empty collection starts as a single chunk (`MinKey` to `MaxKey`) on one shard. A **hashed** key is pre-split: the hash space is divided up front and spread across the shards (two chunks per shard on this 7.0 cluster), because hash values are uniformly distributed and MongoDB knows where to cut.

The load: 200,000 orders per collection from Python, through `mongos`, with the balancer **stopped** (`sh.stopBalancer()`) so you see where the writes go on their own. 5,000 customers, orders 30 seconds apart:

```python
import datetime as dt, random, time
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27100")          # mongos, not a shard
db = client.shop
random.seed(12)
start = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)

def batch(i0, n):
    return [{
        "customerId": random.randint(1, 5_000),
        "createdAt": start + dt.timedelta(seconds=30 * i),
        "status": random.choice(["paid", "paid", "shipped", "refunded"]),
        "totalCents": random.randint(500, 20_000),
        "note": "x" * 100,
    } for i in range(i0, i0 + n)]

for name in ["orders_by_time", "orders_hashed", "orders_compound"]:
    coll = db[name]
    for i0 in range(0, 200_000, 5_000):
        coll.insert_many(batch(i0, 5_000), ordered=False)
```

Documents per shard afterwards (from `$collStats` through `mongos`):

```text
orders_by_time   [{"shard":"shA","docs":200000,"MB":"38.7"}]
orders_hashed    [{"shard":"shA","docs":100973,"MB":"19.5"},{"shard":"shB","docs":99027,"MB":"19.1"}]
orders_compound  [{"shard":"shA","docs":200000,"MB":"38.7"}]
```

The hashed collection split its writes 50.5 / 49.5 from the first insert. The two ranged collections put **every** document on `shA`: there was one chunk, and it lived there. Then the balancer was switched back on (`sh.startBalancer()`) and polled with `sh.balancerCollectionStatus(ns).balancerCompliant` until all three reported `true`, about 50 seconds. Documents *owned* per shard, computed from the chunk ranges so orphans don't count:

```text
orders_by_time   {"shA":106598,"shB":93402}
orders_hashed    {"shA":100973,"shB":99027}
orders_compound  {"shA":106598,"shB":93402}
```

Now all three look balanced. The difference shows up on the **next** writes: 50,000 more orders, all newer than anything already stored. New documents per shard:

```text
orders_by_time   {"shA":50000,"shB":0}
orders_hashed    {"shA":25256,"shB":24744}
orders_compound  {"shA":26854,"shB":23146}
```

This is the central result of the level:

- **`{createdAt: 1}`** (ranged on a monotonically increasing value) sends **100% of new inserts to one shard**, whatever the balancer does. New values are always greater than all existing ones, so they all fall into the last chunk, `[latest, MaxKey)`, which lives on one shard. The balancer can move old data away, but the write hot spot stays wherever that top chunk is. Adding shards adds no write capacity. The same applies to `_id` with default `ObjectId`s (which start with a timestamp), auto-increment numbers, and timestamps generally.
- **`{customerId: "hashed"}`** spreads inserts evenly from the start, and would for any key, even a monotonic one; hashing a timestamp is the standard fix for insert hot spots.
- **`{customerId: 1, createdAt: 1}`** starts on one shard (a new ranged collection has one chunk; you can pre-split it with `sh.splitAt` and `sh.moveRange`, or let the balancer catch up), but once balanced, new orders land wherever their customer's range lives: 54 / 46 here. The monotonic `createdAt` is harmless as a *second* field because the first field already spreads the writes.

## How queries are routed: targeted vs. scatter-gather

`mongos` looks at the query filter. If it contains the shard key (or a prefix of it, for ranged keys) it can work out which chunks, and so which shards, can hold matching documents, and send the query only there: a **targeted** query. Otherwise it has to ask every shard and merge the results: **scatter-gather** (also "broadcast").

`explain()` through `mongos` shows which one happened. Real output on the cluster above:

```javascript
function route(c, q) {
  const e = db[c].find(q).explain("executionStats");
  const w = e.queryPlanner.winningPlan;
  print(`${c} ${JSON.stringify(q)} ${w.stage} shards=${JSON.stringify(w.shards.map(s => s.shardName))} ` +
        `returned=${e.executionStats.nReturned} examined=${e.executionStats.totalDocsExamined}`);
}
```

```text
orders_hashed    {"customerId":42}                                 SINGLE_SHARD  shards=["shB"]        returned=56  examined=56
orders_hashed    {"customerId":{"$gte":100,"$lt":110}}             SHARD_MERGE   shards=["shB","shA"]  returned=527 examined=250000
orders_compound  {"customerId":{"$gte":100,"$lt":110}}             SINGLE_SHARD  shards=["shB"]        returned=476 examined=476
orders_hashed    {"status":"refunded","totalCents":{"$gt":19990}}  SHARD_MERGE   shards=["shA","shB"]  returned=17  examined=250000
```

(The two collections got different random customer ids from the same seed, which is why the range returns 527 vs. 476.)

- **Equality on a hashed key** is targeted: hash 42, find the one chunk.
- **A range on a hashed key is scatter-gather.** Neighbouring values hash to unrelated places, so customers 100–109 could be on any shard. Worse, the hashed index can't answer a range at all, so each shard did a **collection scan** (250,000 documents examined across the two shards to return 527). If you need range queries on the key, hashed is the wrong choice, or you need a separate ordinary index on the field.
- **A range on a ranged key is targeted**, often to a single shard, and uses the shard key's index.
- **No shard key in the filter → every shard**, every time. That's acceptable for rare admin or analytics queries. For the hot path it means every query costs *N* shards' work, and the slowest shard sets the latency. Adding shards makes such queries more expensive, not less.

**Python (pymongo)**, checking routing from a test or a CI job, which is a cheap way to catch a query that silently lost its shard key:

```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27100")        # connect to mongos
orders = client.shop.orders_hashed

def routing(filter_):
    plan = orders.find(filter_).explain()["queryPlanner"]["winningPlan"]
    return plan["stage"], [s["shardName"] for s in plan["shards"]]

print("equality on shard key:", routing({"customerId": 42}))
print("range on hashed key:  ", routing({"customerId": {"$gte": 100, "$lt": 110}}))
print("no shard key at all:  ", routing({"status": "refunded"}))
```

Real output:

```text
equality on shard key: ('SINGLE_SHARD', ['shB'])
range on hashed key:   ('SHARD_MERGE', ['shB', 'shA'])
no shard key at all:   ('SHARD_MERGE', ['shB', 'shA'])
```

**Go (official v2 driver)**: the Go driver has no `Find(...).Explain()` helper, so send the `explain` command directly with `RunCommand` and decode only the fields you need:

```go
package main

import (
	"context"
	"fmt"
	"log"
	"time"

	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"
)

// explainRoute asks mongos how it would route a find, without running it.
func explainRoute(ctx context.Context, db *mongo.Database, coll string, filter bson.D) (string, []string, error) {
	var out struct {
		QueryPlanner struct {
			WinningPlan struct {
				Stage  string `bson:"stage"`
				Shards []struct {
					ShardName string `bson:"shardName"`
				} `bson:"shards"`
			} `bson:"winningPlan"`
		} `bson:"queryPlanner"`
	}
	cmd := bson.D{
		{Key: "explain", Value: bson.D{{Key: "find", Value: coll}, {Key: "filter", Value: filter}}},
		{Key: "verbosity", Value: "queryPlanner"},
	}
	if err := db.RunCommand(ctx, cmd).Decode(&out); err != nil {
		return "", nil, err
	}
	var shards []string
	for _, s := range out.QueryPlanner.WinningPlan.Shards {
		shards = append(shards, s.ShardName)
	}
	return out.QueryPlanner.WinningPlan.Stage, shards, nil
}

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	client, err := mongo.Connect(options.Client().ApplyURI("mongodb://localhost:27100"))
	if err != nil {
		log.Fatal(err)
	}
	defer client.Disconnect(ctx)
	db := client.Database("shop")

	for _, q := range []struct {
		label  string
		coll   string
		filter bson.D
	}{
		{"hashed, equality", "orders_hashed", bson.D{{Key: "customerId", Value: 42}}},
		{"hashed, range", "orders_hashed", bson.D{{Key: "customerId", Value: bson.D{{Key: "$gte", Value: 100}, {Key: "$lt", Value: 110}}}}},
		{"ranged, range", "orders_compound", bson.D{{Key: "customerId", Value: bson.D{{Key: "$gte", Value: 100}, {Key: "$lt", Value: 110}}}}},
	} {
		stage, shards, err := explainRoute(ctx, db, q.coll, q.filter)
		if err != nil {
			log.Fatal(err)
		}
		fmt.Printf("%-17s %-13s %v\n", q.label, stage, shards)
	}
}
```

Real output:

```text
hashed, equality  SINGLE_SHARD  [shB]
hashed, range     SHARD_MERGE   [shA shB]
ranged, range     SINGLE_SHARD  [shB]
```

## Choosing a shard key

The three properties to check, in this order:

| Property | Question | Bad example | Good example |
|---|---|---|---|
| **Cardinality** | How many distinct values can the key have? A chunk can't be split below one key value, so this caps how finely data can be spread | `country` (~200 values), `status` (4) | `customerId`, `deviceId`, `{tenantId, userId}` |
| **Frequency** | Are the values roughly equally common? One huge value makes one huge, unsplittable chunk | `country` when 85% of users are `US` | a key where no single value dominates |
| **Monotonicity** | Does the key always increase? Then all inserts hit the last chunk | `createdAt`, `ObjectId` `_id`, sequence numbers | hashed version of those, or a compound key whose first field isn't monotonic |

And then the question that decides between the candidates that pass: **what do your most frequent queries filter on?** The ideal key is in the filter of nearly every hot query (so they're targeted) and has high cardinality and low frequency (so data and writes spread). Common patterns:

- **Hashed `_id` or hashed user/device id**: even writes, no range queries on the key. Good default for "look up by id" workloads.
- **Compound `{tenantId: 1, <something unique>: 1}`**: keeps each tenant's data together (targeted per-tenant queries) while the second field lets a big tenant span several chunks. Typical for SaaS.
- **Compound hashed** (MongoDB 4.4+), e.g. `{region: 1, deviceId: "hashed"}`: group by the first field (useful for zones, below), spread evenly within it.

Hard limits worth knowing: every document must be routable, so a **unique index** on a sharded collection must include the shard key as a prefix (MongoDB can only enforce uniqueness within one shard); `_id` is unique per shard only, unless it's the shard key. Transactions across shards work (4.2+) but pay a two-phase commit across the involved shards.

## Jumbo chunks: when a chunk can't be split

A chunk can only be split between two *different* shard-key values. If a huge number of documents share one value, that value's chunk grows past the chunk size and can't be split or, if it's too big, moved. MongoDB flags it **`jumbo`**, and the balancer skips it from then on. Demonstrated with a low-cardinality key where 85% of documents share one value:

```text
sh.shardCollection("shop.users_by_country", { country: 1 });
const docs = [];
for (let i = 0; i < 40000; i++)
  docs.push({ country: i < 34000 ? "US" : (i % 2 ? "DE" : "FR"), name: "user" + i, bio: "y".repeat(150) });
db.users_by_country.insertMany(docs);
sh.splitFind("shop.users_by_country", { country: "US" });
```

The chunks afterwards (`config.chunks`):

```text
{"min":{"country":MinKey},"max":{"country":"US"},"shard":"shB","jumbo":false}
{"min":{"country":"US"},"max":{"country":MaxKey},"shard":"shA","jumbo":true}
```

All 34,000 US documents (about 6 MB, six times the 1 MB chunk size) are in one chunk, now marked `jumbo`. Asking MongoDB to split it further fails:

```text
> sh.splitAt("shop.users_by_country", {country: "US"})
new split key { country: "US" } is a boundary key of existing chunk [{ country: "US" },{ country: MaxKey })
> sh.splitFind("shop.users_by_country", {country: "US"})
Unable to find median in chunk because chunk is indivisible.
```

This is what the cardinality/frequency rows of the table mean in practice: one shard ends up holding all the US data and all the US traffic, and no amount of adding shards changes that. At production chunk sizes the same thing happens to "the one customer who is 100x bigger than the rest" under a `{customerId: 1}` key.

The fix is to add a field to the shard key that makes the key finer. **Refining** a shard key (MongoDB 4.4+) appends suffix fields to the existing key without moving any data; it needs an index on the new full key first:

```text
db.users_by_country.createIndex({ country: 1, _id: 1 });
db.adminCommand({ refineCollectionShardKey: "shop.users_by_country", key: { country: 1, _id: 1 } });
```

Refining also cleared the jumbo flag. Within a minute the balancer had split the US range on `_id` and moved part of it:

```text
{"min":{"country":MinKey,"_id":MinKey},"max":{"country":"US","_id":MinKey},"shard":"shB"}
{"min":{"country":"US","_id":MinKey},"max":{"country":"US","_id":"6abb82cc83a060cd8d36724c"},"shard":"shB"}
{"min":{"country":"US","_id":"6abb82cc83a060cd8d36724c"},"max":{"country":"US","_id":"6abb82cc83a060cd8d36852b"},"shard":"shB"}
{"min":{"country":"US","_id":"6abb82cc83a060cd8d36852b"},"max":{"country":MaxKey,"_id":MaxKey},"shard":"shA"}
```

(`_id` values shown as their hex string; `mongosh` prints them as `ObjectId(...)`.) If the key is wrong in a way refining can't fix, e.g. you picked `createdAt` and need `customerId`, **`reshardCollection`** (MongoDB 5.0+) rewrites the whole collection under a new key online. It copies every document (MongoDB's docs ask for free storage of about 1.2x the collection's size), and blocks writes for up to about two seconds at the end. It works, but it's a large operation you schedule, not a quick fix. For a flag that was set by a migration failing for some other reason, `clearJumboFlag` resets it.

## Zone sharding: pinning data to shards

**Zones** let you say "documents in this shard-key range must live on these shards". The balancer then moves chunks to honour that. The usual reasons are data residency (EU users' data stays on EU hardware), tiered storage (recent data on fast shards), or isolating a large tenant. The zone ranges have to be expressed in terms of the shard key, so the key must start with the field you zone by:

```text
sh.addShardToZone("shA", "EU");
sh.addShardToZone("shB", "US");
sh.updateZoneKeyRange("shop.users", { region: "EU", userId: MinKey }, { region: "EU", userId: MaxKey }, "EU");
sh.updateZoneKeyRange("shop.users", { region: "US", userId: MinKey }, { region: "US", userId: MaxKey }, "US");
sh.shardCollection("shop.users", { region: 1, userId: 1 });

// 10,000 users, two thirds EU
db.users.insertMany(Array.from({ length: 10000 }, (_, k) =>
  ({ region: (k + 1) % 3 ? "EU" : "US", userId: k + 1, email: `u${k + 1}@example.com` })));
```

Because the zones were defined before `shardCollection`, MongoDB created the initial chunks on the right shards straight away:

```text
EU  SINGLE_SHARD ["shA"] 6667
US  SINGLE_SHARD ["shB"] 3333
```

Every EU user is on `shA`, every US user on `shB`, and a query for one region is targeted to that region's shard. For residency that's the whole point. For capacity it's a trade-off: the EU shard now carries two thirds of the data and load, and the balancer will not move EU chunks to a US shard to even it out. The fix is more shards in the EU zone, not a different balancer setting.

## Operating it

- **Check balance**: `sh.status()` (overview), `db.coll.getShardDistribution()` (data per shard, including orphans), `sh.balancerCollectionStatus("db.coll")` (is this collection balanced, and if not, why).
- **Migrations cost I/O** on both shards and are throttled one per shard at a time. On a busy cluster, set a balancing window (`config.settings` `activeWindow`) to keep them off peak hours.
- **Pre-split** a new ranged collection before a bulk load (`sh.splitAt`, then `sh.moveRange` in 6.0+), or you get the single-shard insert pattern measured above until the balancer catches up.
- **Know when not to shard.** A sharded cluster is at least three replica sets plus routers, with more to monitor, back up and upgrade. A single replica set on a bigger machine, with good indexes (level 05) and secondaries for reads (level 10), handles more than most applications need. Shard when the working set no longer fits in one primary's RAM, the data no longer fits comfortably on its disks, or the write rate has outgrown it, and you've measured that, not guessed it.

## Try it in the browser

The ▶ Run buttons on this page run a mongosh-like shell in your browser over the Query Lab's shop data, on a single in-memory node. There is no cluster: `sh.*` helpers, chunks, the balancer, `mongos` routing, jumbo flags and zones can't run here, which is why the cluster commands above have no Run button. What does run is the analysis you do *before* `sh.shardCollection`: measuring a candidate key's cardinality, frequency and monotonicity on real data, and checking which queries would be targeted.

Cardinality: how many distinct values each candidate key for `orders` has. `status` can never be split into more than 5 chunks, `customer.country` into more than 18; `customer._id` and `_id` leave plenty of room.

```js
({
  status: db.orders.distinct("status").length,
  country: db.orders.distinct("customer.country").length,
  customerId: db.orders.distinct("customer._id").length,
  orderId: db.orders.estimatedDocumentCount()
})
```

Frequency: the share of orders held by each key's most common value. Under `{ "customer.country": 1 }`, India alone is about a third of all orders, one value that can't be split (the jumbo-chunk demo above, on real-looking data). The busiest customer holds well under 1%.

```js
const total = db.orders.estimatedDocumentCount();
const top = field => db.orders.aggregate([{ $sortByCount: "$" + field }, { $limit: 1 }]).toArray()[0];
const share = field => { const t = top(field); return { value: t._id, orders: t.count, pct: Math.round(1000 * t.count / total) / 10 }; };
({ country: share("customer.country"), status: share("status"), customerId: share("customer._id") })
```

Monotonicity: the five highest `_id`s are all from the last day in the data, because ids and order times both only grow. A ranged key on either sends every new insert to the last chunk, the `orders_by_time` result above.

```js
db.orders.find({}, { _id: 1, ordered_at: 1 }).sort({ _id: -1 }).limit(5)
```

Where the next writes would land, simulated on the 500 newest orders. Pretend each key's collection has been split into two chunks at its median value and see which chunk each new order falls in: by time, every one hits the upper chunk; by customer, they spread across both.

```js
db.orders.aggregate([
  { $sort: { ordered_at: -1 } },
  { $limit: 500 },
  { $facet: {
      byOrderedAt: [{ $group: {
        _id: { $cond: [{ $gte: ["$ordered_at", ISODate("2025-05-09")] }, "upper chunk", "lower chunk"] },
        newOrders: { $sum: 1 } } }],
      byCustomerId: [{ $group: {
        _id: { $cond: [{ $gte: ["$customer._id", 1051] }, "upper chunk", "lower chunk"] },
        newOrders: { $sum: 1 } } }]
  } }
])
```

Targeted vs. scatter-gather is decided by the filter. With a `{ "customer._id": 1, ordered_at: 1 }` key, the "my orders" query below names the key's first field, so `mongos` would send it to one shard; the second has no shard-key field and would go to every shard. Both return the same documents here; only the routing differs on a cluster.

```js
({
  targeted: db.orders.find({ "customer._id": 917, ordered_at: { $gte: ISODate("2025-01-01") } }, { total: 1 }).limit(3).toArray(),
  scatterGather: db.orders.find({ status: "returned", total: { $gt: 3000 } }, { total: 1 }).limit(3).toArray()
})
```

Sizing zones before you define them: if EU customers' orders had to stay on EU shards, this is how the load would split between zones (Germany, France, Spain and the Netherlands count as `"EU"` here). Whatever share the EU zone gets, it needs enough shards of its own, because the balancer never moves data across zones.

```js
db.orders.aggregate([
  { $group: {
      _id: { $cond: [{ $in: ["$customer.country", ["Germany", "France", "Spain", "Netherlands"]] }, "EU", "rest"] },
      orders: { $sum: 1 }
  } },
  { $sort: { orders: -1 } }
])
```

## Common mistakes

- **Sharding on a monotonically increasing key** (`createdAt`, default `ObjectId` `_id`, counters) with a ranged index. All inserts hit one shard forever, as measured above. Hash it, or put a well-distributed field first.
- **Choosing a low-cardinality or skewed key** (`country`, `status`, `type`). Chunks can't be split below one value; you get jumbo chunks and a permanently hot shard.
- **A shard key your hot queries don't filter on.** Every one of those queries goes to every shard. Design the key from the query patterns, the same way level 04 designs documents from access patterns.
- **Hashed key, then range queries on it.** Hashing destroys order: ranges become scatter-gather, and the hashed index can't serve them.
- **Trusting `getShardDistribution()` right after a migration.** It includes orphaned documents still waiting for cleanup (15 minutes by default). Query through `mongos` for real counts.
- **Connecting the application directly to a shard.** You bypass routing and see orphans and only one slice of the data. Applications always connect to `mongos`.
- **Sharding too early.** It adds operational weight and constraints (unique indexes, cross-shard transactions) that a single well-indexed replica set doesn't have.

## Interview questions

**"How do you choose a shard key?"** Start from the hot queries: the key should appear in their filters so they're targeted to one shard. Then check it has high cardinality, no dominant values, and isn't monotonically increasing. If the natural key is monotonic (a timestamp, an ObjectId), hash it; if you need locality plus spread, use a compound key like `{tenantId, userId}`.

**"Hashed or ranged sharding?"** Hashed spreads writes evenly even for monotonic values and pre-splits the collection, but range queries on the key become scatter-gather. Ranged keeps nearby values together so range queries are targeted, but a monotonic ranged key concentrates all inserts on one shard, and a new ranged collection starts as one chunk on one shard.

**"What's a jumbo chunk, and how do you fix one?"** A chunk that has grown beyond the chunk size and can't be split because all its documents share one shard-key value (or that failed to migrate). The balancer skips it, so that shard stays overloaded. Fix the key's granularity: refine the shard key with an extra suffix field (4.4+), or reshard (5.0+) if the key is fundamentally wrong.

**"What does mongos do, and what happens when a chunk moves?"** It's a stateless router that caches the routing table (chunk ranges → shards) from the config servers, targets each query to the shards that can hold matching data, and merges results. After a migration, a request with an outdated routing version is rejected by the shard with a stale-config error; `mongos` refreshes its cache from the config servers and retries, invisibly to the application.

**"When would you use zone sharding?"** Data residency (EU data on EU shards), tiered hardware (recent data on faster shards), or isolating a large tenant. It requires the shard key to start with the zoning field, and the balancer will never move data out of its zone, so each zone needs enough shards for its own load.

## What's next

That closes the MongoDB ladder. The same three shard-key properties (cardinality, frequency, monotonicity) are the partition-key rules for Cassandra and DynamoDB in [Wide-Column and DynamoDB-Style Databases](../concepts/00_wide_column_and_dynamodb_style_databases.md); [Interview Playbook: NoSQL](../concepts/02_interview_playbook.md) has the interview drill.
