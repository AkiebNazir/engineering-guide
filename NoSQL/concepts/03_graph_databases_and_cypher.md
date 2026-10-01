# Graph Databases and Cypher

## What a graph database is, and why it exists

Some data is mostly about the **connections** between things: who follows whom, which
accounts share a device, which services call which, which parts go into which
assemblies. A relational database can store connections (a join table with two foreign
keys), and level 22 of `SQL/` shows it can walk them with recursive CTEs. But every hop
is a join, the query language is built around sets of rows rather than paths, and
questions like "what's the shortest chain between these two accounts?" or "find every
triangle of mutual follows" are awkward to write and expensive to run.

A **graph database** makes the connections first-class. It stores **nodes** (things) and
**relationships** (connections between two nodes), and it's queried by describing a
*pattern* of nodes and relationships to find. The main families:

- **Property graph** databases (Neo4j, Memgraph, Amazon Neptune, TigerGraph, Apache AGE
  inside Postgres): nodes and relationships both carry key/value **properties**, nodes
  have **labels**, relationships have a **type** and a **direction**. This is the model
  most application developers mean by "graph database", and the one this level uses.
- **RDF triple stores** (Neptune also, GraphDB, Apache Jena): everything is a
  `subject–predicate–object` triple, queried with SPARQL. Common for knowledge graphs and
  linked data, rarer in application backends.

The query languages: **Cypher** (Neo4j's, also available as openCypher in Neptune,
Memgraph and AGE), **Gremlin** (a traversal API from Apache TinkerPop, used by Neptune,
JanusGraph, Cosmos DB), and **GQL**, the ISO standard graph query language published in
2024 (ISO/IEC 39075) and heavily based on Cypher. SQL:2023 also added **SQL/PGQ**, a way
to run graph pattern queries over ordinary relational tables; Oracle supports it,
Postgres doesn't yet. Cypher is the one to learn: it's the most widely used and it's
what GQL grew from.

This is a concepts level (the module's lab stack has no graph container), but every
query and number below was run for real against **Neo4j 5.26 Community Edition** in a
throwaway container:

```bash
docker run -d --name neo4j-lab -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/labpassword neo4j:5-community
docker exec -it neo4j-lab cypher-shell -u neo4j -p labpassword
```

## The property graph model

```arch
%% caption: A small property graph. Nodes have labels (Person, Product, Category) and properties; relationships have a type, a direction and their own properties (since, at, qty).
route straight
grid 120x100
node ana "Ana\n:Person" at 0,0 shape=circle color=blue
node ben "Ben\n:Person" at 1,1 shape=circle color=blue
node cy "Cy\n:Person" at 0,2 shape=circle color=blue
node dee "Dee\n:Person" at 2,2 shape=circle color=blue
node tent "Tent\n:Product" at 3,0 shape=circle color=green
node camp "Camping\n:Category" at 4,1 shape=circle color=amber
ana -> ben : "FOLLOWS since"
ana -> cy : "FOLLOWS"
ben -> dee : "FOLLOWS"
cy -> dee : "FOLLOWS"
ben -> tent : "PURCHASED qty"
dee -> tent : "PURCHASED"
tent -> camp : "IN_CATEGORY"
```

The modelling rules that come out of this:

- **Nouns become nodes, verbs become relationships.** `(:Person)-[:PURCHASED]->(:Product)`
  reads as a sentence, and so does the query.
- **Facts about a connection go on the relationship.** When Ana started following Ben
  (`since`), how many tents Ben bought (`qty`). In SQL these would be extra columns on
  the join table; here the relationship *is* the join-table row.
- **Use specific relationship types.** `:FOLLOWS`, `:PURCHASED`, `:IN_CATEGORY`, not one
  generic `:RELATED_TO {kind: 'follows'}`. The type is what the database indexes
  traversal by; a query for `:FOLLOWS` never touches purchase relationships.
- **Promote a relationship to a node when it connects more than two things or needs its
  own relationships.** A purchase that involves a buyer, several products, a card and a
  shipping address is better as an `(:Order)` node with relationships to each. Otherwise
  you can't say "this order was paid with this card".
- **Every relationship has a direction, but you can query it either way.** Store the
  natural direction (`FOLLOWS` points from follower to followed) and use `-[:FOLLOWS]-`
  (no arrow) when direction doesn't matter.
- **Labels and property keys are free-form**, as in a document store. Enforce what matters
  with constraints: `CREATE CONSTRAINT person_id FOR (p:Person) REQUIRE p.id IS UNIQUE`
  (which also creates the index used to find starting nodes).

### Why traversal is cheap: index-free adjacency

In a relational database, going from a row to its related rows means an index lookup:
`O(log n)` in the size of the table, on every hop, for every row. Native graph stores
like Neo4j keep, on each node, direct pointers to its relationship records, and each
relationship points to its two nodes. Following a relationship is a pointer dereference,
so a traversal's cost depends on **how many relationships it touches**, not on how big
the whole graph is. That's the claim to remember, with the honest caveat: B-tree lookups
are also fast, and the difference only dominates when a query touches many hops or
explores many alternative paths. The measurements below show both sides.

## Cypher in one page

Cypher draws the pattern with ASCII art: `()` is a node, `-[]->` is a relationship.

```cypher
CREATE (ana:Person {id: 1, name: 'Ana'}), (ben:Person {id: 2, name: 'Ben'}),
       (tent:Product {sku: 'TENT-2', name: 'Two-person tent'}),
       (ana)-[:FOLLOWS {since: date('2024-02-01')}]->(ben),
       (ben)-[:PURCHASED {at: datetime('2026-05-01T10:00Z'), qty: 1}]->(tent);

MERGE (p:Person {id: 7}) ON CREATE SET p.name = 'Gus';   // create only if it doesn't exist (upsert)

MATCH (p:Person {name: 'Ben'})-[r:PURCHASED]->(item:Product)   // find a pattern
WHERE r.qty >= 1
RETURN p.name, item.name, r.at
ORDER BY r.at DESC LIMIT 10;
```

| Cypher | Meaning |
|---|---|
| `(p:Person {name: $name})` | a node labelled `Person` with that property (`$name` is a parameter) |
| `-[:FOLLOWS]->`, `<-[:FOLLOWS]-`, `-[:FOLLOWS]-` | outgoing, incoming, either direction |
| `-[:FOLLOWS*1..3]->` | a variable-length path of 1 to 3 `FOLLOWS` hops |
| `-[:A\|B\|C]-` | any of these relationship types |
| `shortestPath((a)-[*]-(b))` | one shortest path between two nodes |
| `OPTIONAL MATCH` | like a `LEFT JOIN`: keep the row with `null`s if the pattern isn't found |
| `count()`, `collect()` | aggregation; grouping is implicit by the non-aggregated `RETURN` columns |
| `DETACH DELETE n` | delete a node and its relationships |

Always pass values as **parameters** (`$name`), never by building the query string, for
the same injection reason as `SQL/11`, and so the database can cache the query plan.

## Worked queries on a small graph

The graph above, extended to six people (Ana, Ben, Cy, Dee, Eli, Fay), four camping
products and one category. Real output from each query.

**"People you may know"**: people my follows follow, whom I don't follow yet, ranked by
how many of my follows lead to them:

```cypher
MATCH (me:Person {name: 'Ana'})-[:FOLLOWS]->(friend)-[:FOLLOWS]->(fof)
WHERE fof <> me AND NOT (me)-[:FOLLOWS]->(fof)
RETURN fof.name AS suggestion, count(friend) AS mutual, collect(friend.name) AS via
ORDER BY mutual DESC, suggestion;
```

```text
suggestion, mutual, via
"Dee", 2, ["Cy", "Ben"]
"Eli", 1, ["Cy"]
```

**"Customers who bought what you bought also bought"**:

```cypher
MATCH (me:Person {name: 'Ana'})-[:PURCHASED]->(:Product)<-[:PURCHASED]-(other:Person)
      -[:PURCHASED]->(rec:Product)
WHERE NOT (me)-[:PURCHASED]->(rec)
RETURN rec.name AS recommendation, count(DISTINCT other) AS buyers
ORDER BY buyers DESC, recommendation;
```

```text
recommendation, buyers
"Camp stove", 1
"Head lamp", 1
"Sleeping bag", 1
```

**Every route, and the shortest one**:

```cypher
MATCH path = (:Person {name: 'Ana'})-[:FOLLOWS*1..4]->(:Person {name: 'Fay'})
RETURN [n IN nodes(path) | n.name] AS route, length(path) AS hops ORDER BY hops;

MATCH p = shortestPath((:Person {name: 'Ana'})-[:FOLLOWS*]->(:Person {name: 'Fay'}))
RETURN [n IN nodes(p) | n.name] AS route;
```

```text
route, hops
["Ana", "Ben", "Dee", "Fay"], 3
["Ana", "Cy", "Dee", "Fay"], 3
route
["Ana", "Cy", "Dee", "Fay"]
```

Cypher doesn't revisit a relationship within one path, so a variable-length pattern
terminates on cyclic data, which is the problem `SQL/22` spends a section on.

### The fraud-ring query: where graphs are the natural fit

Fraud teams look for accounts that are secretly the same actor: they share a device, a
card, or a shipping address, possibly through a chain (A1 shares a device with A2, which
shares a card with A3, which ships to the same address as A4). The model:

```cypher
CREATE (a1:Account {id: 'A1'}), (a2:Account {id: 'A2'}), (a3:Account {id: 'A3'}),
       (a4:Account {id: 'A4'}), (a5:Account {id: 'A5'}), (a6:Account {id: 'A6'}),
       (d1:Device {fingerprint: 'dev-9f2'}), (d2:Device {fingerprint: 'dev-41c'}),
       (d3:Device {fingerprint: 'dev-77a'}),
       (c1:Card {last4: '4242'}), (c2:Card {last4: '1881'}),
       (ad1:Address {line: '12 Elm St'}),
       (a1)-[:USED_DEVICE]->(d1), (a2)-[:USED_DEVICE]->(d1),
       (a2)-[:PAID_WITH]->(c1),   (a3)-[:PAID_WITH]->(c1),
       (a3)-[:SHIPS_TO]->(ad1),   (a4)-[:SHIPS_TO]->(ad1),
       (a5)-[:USED_DEVICE]->(d2), (a5)-[:PAID_WITH]->(c2),
       (a6)-[:USED_DEVICE]->(d3);
```

Devices, cards and addresses are **nodes**, not properties on the account. That's the
modelling decision that makes the question answerable: two accounts that share a card
are connected through the card node. The chain linking A1 to A4, and the rings:

```cypher
MATCH p = shortestPath((:Account {id: 'A1'})-[:USED_DEVICE|PAID_WITH|SHIPS_TO*]-(:Account {id: 'A4'}))
RETURN [n IN nodes(p) | coalesce(n.id, n.fingerprint, n.last4, n.line)] AS chain;

MATCH (a:Account)
OPTIONAL MATCH (a)-[:USED_DEVICE|PAID_WITH|SHIPS_TO*1..6]-(b:Account)
WITH a, collect(DISTINCT b.id) + [a.id] AS ids
UNWIND ids AS id
WITH a, id ORDER BY id
WITH a, collect(id) AS ring
RETURN DISTINCT ring, size(ring) AS accounts ORDER BY accounts DESC;
```

```text
chain
["A1", "dev-9f2", "A2", "4242", "A3", "12 Elm St", "A4"]
ring, accounts
["A1", "A2", "A3", "A4"], 4
["A5"], 1
["A6"], 1
```

A1–A4 are one ring, found through three *different kinds* of shared identifier. In SQL
this is a recursive CTE over a union of three join tables with cycle detection, and it
has to be rewritten each time a new identifier type (phone number, IP) is added. In
Cypher, adding `|USED_PHONE` to the relationship list is the whole change. (At scale you'd
run a connected-components algorithm over the whole graph, e.g. Neo4j's Graph Data
Science library or a batch job, rather than a variable-length match per account.)

## When a graph database beats joins, measured

Same data in both systems: 100,000 users, each following 20 random others (2,000,000
relationships). In Postgres 16: `follows(src, dst)` with a primary key on `(src, dst)` and
an index on `dst`. In Neo4j: `(:User)-[:FOLLOWS]->(:User)` with a uniqueness constraint
on `User.id`. Warm-cache times (the second or third run of each):

| Question | Postgres | Neo4j |
|---|---|---|
| Distinct users exactly 3 hops from user 1 (7,674) | **~5 ms** (3 joins) | ~25 ms (`[:FOLLOWS*3]`) |
| Distinct users exactly 4 hops from user 1 (78,542) | **~50 ms** (4 joins) | ~190 ms |
| Shortest path user 1 → 99999 (3 hops) | ~240 ms (recursive CTE BFS) | **~10 ms** (`shortestPath`) |
| Shortest path user 1 → 325 (5 hops) | ~1,000 ms | **~4 ms** |

Timings are from one machine and a single container each; treat them as approximate. The
point is the shape, which is the honest answer to the interview question:

- **Fixed-depth joins on good indexes are not where graph databases win.** Postgres ran
  the 3- and 4-hop fan-out 4–5x *faster*, because it's a plain join pipeline on B-tree
  indexes with hash aggregation, which relational engines are very good at.
- **Path finding is.** Neo4j's `shortestPath` runs a **bidirectional** breadth-first
  search: it expands from both ends and stops the moment the frontiers meet, touching a
  few thousand relationships. The SQL version expands level by level from one end,
  can't stop early per branch, and deduplicates with `UNION` over a growing result;
  the 5-hop case explored most of the graph. The gap grows with path length and graph size.
- **Pattern queries** (triangles, "A→B→C where C→A", chains through mixed relationship
  types like the fraud ring) and **variable-length paths** are where the query *language*
  wins even before performance: the Cypher is short and the SQL is a page.

So a graph database is the better tool when the core workload is traversal: variable or
unknown depth, shortest paths, pattern matching across many relationship types, and
queries that start from one node and explore its neighbourhood (recommendations, fraud,
network/IT dependency analysis, access-control graphs, knowledge graphs). It's the worse
tool for:

- **Whole-dataset aggregates and reporting** ("revenue by month"): that's a scan, and
  relational or columnar engines do it far better.
- **Simple CRUD by id**, where a key-value or relational store is simpler and cheaper.
- **Horizontal write scaling.** Graphs are hard to partition: every relationship that
  crosses a partition turns a pointer hop into a network call. Neo4j scales reads with
  replicas and offers sharding through composite databases where the application
  defines the split; Neptune scales reads with replicas over one shared storage volume.
  Plan for one writer.
- **Supernodes**: a node with millions of relationships (a celebrity account, the
  "United States" node) makes every traversal through it expensive. Model around it
  (specific relationship types, bucketing by time, not traversing through it).

A common production shape is both: the system of record stays relational, and a graph
database (or Apache AGE, Cypher inside Postgres) holds a projection of the relationship
data for the traversal-heavy features, fed by change-data capture.

## From Python and Go

**Python** (`pip install neo4j`, the official driver):

```python
from neo4j import GraphDatabase

URI, AUTH = "bolt://localhost:7687", ("neo4j", "labpassword")

SUGGEST = """
MATCH (me:Person {name: $name})-[:FOLLOWS]->(friend)-[:FOLLOWS]->(fof)
WHERE fof <> me AND NOT (me)-[:FOLLOWS]->(fof)
RETURN fof.name AS suggestion, count(friend) AS mutual
ORDER BY mutual DESC, suggestion
"""

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    records, summary, _ = driver.execute_query(SUGGEST, name="Ana", database_="neo4j")
    for r in records:
        print(r["suggestion"], r["mutual"])
```

Real output:

```text
Dee 2
Eli 1
```

**Go** (`go get github.com/neo4j/neo4j-go-driver/v5`):

```go
package main

import (
	"context"
	"fmt"
	"log"

	"github.com/neo4j/neo4j-go-driver/v5/neo4j"
)

func main() {
	ctx := context.Background()
	driver, err := neo4j.NewDriverWithContext("bolt://localhost:7687",
		neo4j.BasicAuth("neo4j", "labpassword", ""))
	if err != nil {
		log.Fatal(err)
	}
	defer driver.Close(ctx)

	// How is A1 linked to A4 through shared devices, cards or addresses?
	result, err := neo4j.ExecuteQuery(ctx, driver, `
		MATCH p = shortestPath((a:Account {id: $from})-[:USED_DEVICE|PAID_WITH|SHIPS_TO*]-(b:Account {id: $to}))
		RETURN [n IN nodes(p) | coalesce(n.id, n.fingerprint, n.last4, n.line)] AS chain`,
		map[string]any{"from": "A1", "to": "A4"},
		neo4j.EagerResultTransformer, neo4j.ExecuteQueryWithDatabase("neo4j"))
	if err != nil {
		log.Fatal(err)
	}
	for _, rec := range result.Records {
		chain, _ := rec.Get("chain")
		fmt.Println(chain)
	}
}
```

Real output:

```text
[A1 dev-9f2 A2 4242 A3 12 Elm St A4]
```

## Common mistakes

- **Modelling shared identifiers as properties.** If the card number is a property on
  each account, "which accounts share a card" is a scan-and-group, not a traversal. Make
  it a node.
- **One generic relationship type with a `kind` property.** The database can't narrow a
  traversal by a property as cheaply as by type. Use specific types.
- **Unbounded variable-length patterns** (`-[*]-`) on a large, dense graph. The number of
  paths explodes. Bound the length (`*1..4`) and the relationship types, or use
  `shortestPath` / graph algorithms.
- **No constraint or index on the lookup property.** Every query starts by finding its
  anchor nodes; without an index on `Person.id` that's a label scan.
- **Choosing a graph database for tabular reporting**, or because the domain "has
  relationships". Every domain has relationships; the question is whether the hot queries
  *traverse* them.
- **Ignoring supernodes** until a traversal through one takes seconds.

## Interview questions

**"When would you use a graph database instead of a relational one?"** When the main
queries traverse relationships to variable or unknown depth: shortest paths, recommendations
from the neighbourhood, fraud rings through shared identifiers, dependency and permission
graphs. Relational engines handle fixed, shallow joins on indexes very well (measured
above, faster); graph engines win on path finding and pattern queries, where they touch
only the relationships they walk and the query language expresses paths directly.

**"What's index-free adjacency?"** Each node stores direct references to its
relationships, so following a relationship costs a pointer hop rather than an index
lookup in a table whose size grows with the whole dataset. Traversal cost scales with the
part of the graph you touch.

**"Model a social network / fraud detection / recommendation graph."** Nodes for
entities (people, accounts, devices, products), specific relationship types for verbs,
properties on relationships for facts about the connection, promote multi-party events
(an order) to nodes, uniqueness constraints on lookup keys. Then write the key query in
Cypher to show the model answers it.

**"Why are graph databases hard to shard?"** A good partition keeps related data
together, but in a well-connected graph most nodes are a few hops from everything, so
any partitioning cuts many relationships, and every cut relationship crossed by a
traversal becomes a network round trip. Most graph deployments scale reads with replicas
and keep a single writer, or partition by a natural boundary such as tenant.

**"Cypher vs. Gremlin vs. SQL?"** Cypher is declarative pattern matching (describe the
shape, the engine finds it) and is the basis of the ISO GQL standard. Gremlin is an
imperative traversal API (step by step: `g.V().has('name','Ana').out('FOLLOWS')`). SQL
can do it with recursive CTEs, and SQL:2023's SQL/PGQ adds graph patterns to SQL itself,
though support is still limited.

## What's next

[Interview Playbook: NoSQL](02_interview_playbook.md) collects the NoSQL modelling
questions across all the stores. For the relational side of the comparison, see
[Recursive CTEs in Depth, and CTE Materialization](../../SQL/22_recursive_ctes_and_cte_materialization.md).
