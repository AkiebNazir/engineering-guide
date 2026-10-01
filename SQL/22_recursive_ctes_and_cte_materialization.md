# Recursive CTEs in Depth, and CTE Materialization

## The mental model

Level 08 showed one recursive CTE walking a six-person org chart. That example hides
the two things that make recursive SQL hard in real systems. First, **real graphs have
cycles**: a flight network, a "who follows whom" table, a dependency graph with a
mistake in it. A naive recursive query on a cyclic graph never finishes. Second, **size**:
a recursive query on a million-row table is a loop that re-runs a join once per level,
and whether each iteration takes 0.3 ms or 150 ms depends on one index.

The second half of this level is about ordinary (non-recursive) CTEs: when Postgres
**inlines** a CTE into the main query and when it **materializes** it as a temporary
result, what `MATERIALIZED` / `NOT MATERIALIZED` change, and how to see which one
happened in `EXPLAIN`. Level 21 gave you the plan-reading skills this needs.

## How a recursive CTE actually runs

`WITH RECURSIVE name AS (base UNION ALL recursive_term)` is a loop, not recursion in the
function-call sense. Postgres keeps two temporary row sets, the **working table** (rows
produced by the previous iteration) and the **result**:

1. Run the base term. Its rows go into both the result and the working table.
2. Run the recursive term, where every reference to `name` reads **only the working
   table**, i.e. the rows found in the previous step, not everything found so far.
3. Append the new rows to the result; they become the new working table.
4. Repeat from step 2 until an iteration produces no rows.

```arch
%% caption: The recursive term only ever sees the previous iteration's rows (the working table). The loop ends when an iteration adds nothing.
node base "Base term" at 1,0 shape=card icon=start sub="runs once"
node work "Working table" at 1,1 shape=card icon=table sub="last iteration's rows"
node rec "Recursive term" at 1,2 shape=card icon=sync sub="joins working table"
node empty "Any new rows?" at 1,3 shape=diamond color=amber
node result "Result" at 3,1 shape=card icon=layers sub="everything, appended"
node done "Done" at 1,4 shape=pill color=green
base -> work
base -> result : "append"
work -> rec
rec -> empty
empty:L -> work:L : "yes: replace"
empty:R -> result : "yes: append"
empty -> done : "no"
```

`UNION ALL` keeps every row. Plain `UNION` discards any new row that is an exact
duplicate of a row already in the result, which sometimes stops a cycle, but only if
the rows are identical: carry a `depth` or `path` column and every row is new again.

## Setup used for this level

A small flight network **with cycles** (LHR → JFK → LHR, and a loop round the world),
and a million-node category tree for the performance section:

```sql
DROP TABLE IF EXISTS routes;
CREATE TABLE routes (
    src     TEXT NOT NULL,
    dst     TEXT NOT NULL,
    minutes INT  NOT NULL,
    PRIMARY KEY (src, dst)
);
INSERT INTO routes VALUES
    ('LHR','JFK',480), ('JFK','SFO',390), ('SFO','NRT',660), ('NRT','LHR',750),
    ('LHR','CDG', 75), ('CDG','JFK',500), ('JFK','LHR',420), ('CDG','NRT',740);

DROP TABLE IF EXISTS categories;
CREATE TABLE categories (
    id        BIGINT PRIMARY KEY,
    parent_id BIGINT REFERENCES categories(id),
    name      TEXT NOT NULL
);
INSERT INTO categories                           -- node i's parent is i/10: a 10-ary tree
SELECT i, CASE WHEN i = 1 THEN NULL ELSE greatest(i / 10, 1) END, 'cat-' || i
FROM generate_series(1, 1000000) AS i;
ANALYZE categories;
```

## The infinite loop, and why nothing stops it

"Every airport reachable from LHR", written the level-08 way:

```sql
SET statement_timeout = '2s';
WITH RECURSIVE reach AS (
    SELECT 'LHR'::text AS airport, 0 AS hops
    UNION ALL
    SELECT r.dst, reach.hops + 1
    FROM reach JOIN routes r ON r.src = reach.airport
)
SELECT count(*) FROM reach;
```

```text
ERROR:  canceling statement due to statement timeout
```

The graph has a cycle, so every iteration finds more rows (LHR → JFK → LHR → JFK ...)
and the working table never empties. **Postgres has no recursion limit.** SQL Server
stops at 100 levels by default (`MAXRECURSION`); Postgres keeps going until the query is
cancelled, the client disconnects, or the growing result fills the temp-file disk. The
only thing that stopped it here was `statement_timeout`, which is one more reason to set
one for every application role (level 21).

A `LIMIT` in the outer query also stops it, because Postgres produces recursive rows
lazily and stops asking once it has enough:

```sql
WITH RECURSIVE reach AS (
    SELECT 'LHR'::text AS airport, 0 AS hops
    UNION ALL
    SELECT r.dst, reach.hops + 1 FROM reach JOIN routes r ON r.src = reach.airport
)
SELECT * FROM reach LIMIT 8;
```

```text
 airport | hops
---------+------
 LHR     |    0
 JFK     |    1
 CDG     |    1
 SFO     |    2
 JFK     |    2
 LHR     |    2
 NRT     |    2
 JFK     |    3
```

LHR shows up again at hop 2: the query has walked the cycle. That's fine for peeking at
a query while you debug it, but it's not a way to write one (it relies on the outer query
not sorting or aggregating, which would force it to read everything).

There are three real fixes: a **depth bound**, **cycle detection**, or **`UNION`** when
rows can be made identical. `UNION` works for plain reachability because the row is just
the airport:

```sql
WITH RECURSIVE reach AS (
    SELECT 'LHR'::text AS airport
    UNION
    SELECT r.dst FROM reach JOIN routes r ON r.src = reach.airport
)
SELECT airport FROM reach;
```

```text
 airport
---------
 LHR
 JFK
 CDG
 SFO
 NRT
```

As soon as you want the route or the number of hops, the rows differ and `UNION` can't
help. That needs cycle detection.

## Cycle detection by hand: carry the path

Carry the path as an array and refuse to extend it to an airport that's already on it.
This works on every Postgres version:

```sql
WITH RECURSIVE trip AS (
    SELECT 'LHR'::text AS airport, ARRAY['LHR'] AS path, 0 AS total_min
    UNION ALL
    SELECT r.dst, t.path || r.dst, t.total_min + r.minutes
    FROM trip t JOIN routes r ON r.src = t.airport
    WHERE r.dst <> ALL (t.path)                 -- not visited on THIS path
)
SELECT array_to_string(path, ' > ') AS itinerary, total_min
FROM trip WHERE airport = 'NRT' ORDER BY total_min;
```

```text
          itinerary          | total_min
-----------------------------+-----------
 LHR > CDG > NRT             |       815
 LHR > JFK > SFO > NRT       |      1530
 LHR > CDG > JFK > SFO > NRT |      1625
```

Every simple path from LHR to NRT, cheapest first. Note what the check means: "not
already on this path", not "never visited by anyone". Two different paths may both pass
through JFK, and that's what lets the query enumerate alternatives. It's also why path
enumeration explodes on dense graphs: the number of simple paths can grow exponentially
with the number of nodes.

## `CYCLE` and `SEARCH`: the standard clauses (Postgres 14+)

Postgres 14 implemented the SQL-standard clauses that generate the path bookkeeping for
you.

**`CYCLE col SET is_cycle USING path`** adds two columns: `path`, an array of the `col`
values seen so far on this branch, and `is_cycle`, set to true on the row that revisits
one. Postgres stops extending a branch after its cycle row:

```sql
WITH RECURSIVE trip(airport, total_min) AS (
    SELECT 'LHR'::text, 0
    UNION ALL
    SELECT r.dst, t.total_min + r.minutes
    FROM trip t JOIN routes r ON r.src = t.airport
) CYCLE airport SET is_cycle USING path
SELECT airport, total_min, is_cycle, path FROM trip ORDER BY path;
```

```text
 airport | total_min | is_cycle |                 path
---------+-----------+----------+---------------------------------------
 LHR     |         0 | f        | {(LHR)}
 CDG     |        75 | f        | {(LHR),(CDG)}
 JFK     |       575 | f        | {(LHR),(CDG),(JFK)}
 LHR     |       995 | t        | {(LHR),(CDG),(JFK),(LHR)}
 SFO     |       965 | f        | {(LHR),(CDG),(JFK),(SFO)}
 NRT     |      1625 | f        | {(LHR),(CDG),(JFK),(SFO),(NRT)}
 LHR     |      2375 | t        | {(LHR),(CDG),(JFK),(SFO),(NRT),(LHR)}
 NRT     |       815 | f        | {(LHR),(CDG),(NRT)}
 LHR     |      1565 | t        | {(LHR),(CDG),(NRT),(LHR)}
 JFK     |       480 | f        | {(LHR),(JFK)}
 LHR     |       900 | t        | {(LHR),(JFK),(LHR)}
 SFO     |       870 | f        | {(LHR),(JFK),(SFO)}
 NRT     |      1530 | f        | {(LHR),(JFK),(SFO),(NRT)}
 LHR     |      2280 | t        | {(LHR),(JFK),(SFO),(NRT),(LHR)}
(14 rows)
```

The query terminates with no depth limit and no hand-written array logic. The cycle rows
(`is_cycle = t`) are kept in the output, which is useful: "which dependency chains loop
back?" is often the question. Filter them with `WHERE NOT is_cycle` when you only want
the valid paths. The path elements are row values (`(LHR)`) because you can list several
columns (`CYCLE src, dst SET ...` detects a repeated *edge* rather than a repeated node).

**`SEARCH BREADTH FIRST BY col SET ord`** or **`SEARCH DEPTH FIRST BY col SET ord`** adds
an ordering column; `ORDER BY ord` then returns the rows in BFS or DFS order. Without it,
the order of a recursive CTE's output is not guaranteed.

```sql
WITH RECURSIVE trip(airport, hops) AS (
    SELECT 'LHR'::text, 0
    UNION ALL
    SELECT r.dst, t.hops + 1 FROM trip t JOIN routes r ON r.src = t.airport
    WHERE t.hops < 2
) SEARCH DEPTH FIRST BY airport SET ord
SELECT repeat('  ', hops) || airport AS tree, ord FROM trip ORDER BY ord;
```

```text
  tree   |         ord
---------+---------------------
 LHR     | {(LHR)}
   CDG   | {(LHR),(CDG)}
     JFK | {(LHR),(CDG),(JFK)}
     NRT | {(LHR),(CDG),(NRT)}
   JFK   | {(LHR),(JFK)}
     LHR | {(LHR),(JFK),(LHR)}
     SFO | {(LHR),(JFK),(SFO)}
```

Depth-first order is what you want for printing a tree (each node directly above its
children). `BREADTH FIRST` gives `ord = (depth, value)`: all of level 1, then level 2,
which is what "nearest first" and shortest-hop queries want:

```text
 airport | hops |   ord
---------+------+---------
 LHR     |    0 | (0,LHR)
 CDG     |    1 | (1,CDG)
 JFK     |    1 | (1,JFK)
 JFK     |    2 | (2,JFK)
 LHR     |    2 | (2,LHR)
 NRT     |    2 | (2,NRT)
 SFO     |    2 | (2,SFO)
```

Two limits to know. `SEARCH` only defines the output order; the engine still computes
level by level. And neither clause makes graph search cheap: a BFS "shortest path" in SQL
still enumerates paths until the depth bound, and there's no "stop this branch because
another branch already reached this node more cheaply" (a `UNION` can't do that either,
because the rows differ in their cost column). For weighted shortest paths on big graphs
you want an algorithm, whether pgRouting's Dijkstra, application code, or a graph
database (see [Graph Databases and Cypher](../NoSQL/concepts/03_graph_databases_and_cypher.md)).

## Performance: the index that decides everything

On the million-node tree, count everything below category 42 (11,111 nodes, 4 levels
down). Without an index on `parent_id`:

```sql
EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)
WITH RECURSIVE subtree AS (
    SELECT id, 0 AS depth FROM categories WHERE id = 42
    UNION ALL
    SELECT c.id, s.depth + 1
    FROM categories c JOIN subtree s ON c.parent_id = s.id
)
SELECT count(*), max(depth) FROM subtree;
```

```text
 Aggregate (actual time=731.729..731.736 rows=1 loops=1)
   Buffers: shared hit=36767
   CTE subtree
     ->  Recursive Union (actual time=14.032..728.639 rows=11111 loops=1)
           ->  Index Only Scan using categories_pkey on categories (actual time=14.025..14.034 rows=1 loops=1)
                 Index Cond: (id = 42)
           ->  Hash Join (actual time=43.538..142.628 rows=2222 loops=5)
                 Hash Cond: (c.parent_id = s.id)
                 ->  Seq Scan on categories c (actual time=0.008..72.961 rows=1000000 loops=5)
                 ->  Hash (actual time=0.741..0.741 rows=2222 loops=5)
                       ->  WorkTable Scan on subtree s (actual time=0.289..0.429 rows=2222 loops=5)
   ->  CTE Scan on subtree (actual time=14.038..730.916 rows=11111 loops=1)
 Execution Time: 759.686 ms
```

Read it with level 21's rules: `loops=5` on the Hash Join means the recursive term ran
5 times (4 levels that found rows, plus the last, empty one), and **each run was a full
sequential scan** of 1,000,000 rows to find a few thousand children. 5 million rows
scanned to return 11,111. It's the same missing foreign-key index as level 21, with the
cost multiplied by the depth of the tree.

```sql
CREATE INDEX categories_parent_id ON categories (parent_id);
ANALYZE categories;
```

Same query:

```text
 Aggregate (actual time=13.959..13.962 rows=1 loops=1)
   Buffers: shared hit=34493 read=22
   CTE subtree
     ->  Recursive Union (actual time=0.017..11.576 rows=11111 loops=1)
           ->  Index Only Scan using categories_pkey on categories (actual time=0.015..0.017 rows=1 loops=1)
                 Index Cond: (id = 42)
           ->  Nested Loop (actual time=1.370..2.092 rows=2222 loops=5)
                 ->  WorkTable Scan on subtree s (actual time=0.000..0.118 rows=2222 loops=5)
                 ->  Index Scan using categories_parent_id on categories c (actual time=0.001..0.001 rows=1 loops=11111)
                       Index Cond: (parent_id = s.id)
   ->  CTE Scan on subtree (actual time=0.017..13.235 rows=11111 loops=1)
 Execution Time: 14.116 ms
```

**759.7 ms → 14.1 ms, about 54x.** The plan now does one index probe per node found
(`loops=11111`), so its cost grows with the size of the *subtree*, not the size of the
*table*. That's the property you want from any hierarchical query. Note that the buffer
count barely changed (36,767 vs 34,515): the index version touches roughly 3 pages per
probe. Buffers measure work, not wasted work; the 5 million discarded rows are what the
first plan paid for.

Other things that matter at scale:

- **Bound the depth** (`WHERE s.depth < N`) whenever the domain has a natural maximum.
  It's a guard against bad data as much as an optimization.
- **The working table lives in memory up to `work_mem`**, then spills to temp files.
  Path arrays make every row bigger at every level; carry only what you need.
- **Only the recursive term's join is repeated.** Put filters that don't depend on the
  recursion (e.g. `c.active`) in the recursive term so dead branches are cut early,
  rather than filtering the final result.
- **For read-heavy trees, consider a different model.** A materialized path (`ltree`
  extension, or a `path TEXT` like `/1/4/42/`) or a closure table (one row per
  ancestor–descendant pair) turns "whole subtree" into one indexed range or equality
  lookup, at the cost of more work on moves and inserts. Adjacency list + recursive CTE
  is the simplest to write to; the others are faster to read.

## Non-recursive CTEs: inlined or materialized?

Before Postgres 12, every CTE was an **optimization fence**: it was computed once, in
full, into a temporary result, and the main query read that result. Filters in the main
query were never pushed into the CTE. People used CTEs as a planner hint for this reason,
and were surprised by slow queries for the same reason.

Since Postgres 12, a non-recursive CTE is **inlined** (treated like a subquery, so the
planner optimizes it together with the rest of the query) when all of these hold:

- it's referenced **exactly once**,
- it's **side-effect free**: a plain `SELECT`, no `INSERT/UPDATE/DELETE ... RETURNING`,
  no volatile functions like `random()` or `nextval()`,
- it isn't recursive.

Otherwise it's **materialized**. You can override either way with `AS MATERIALIZED` or
`AS NOT MATERIALIZED`. Recursive CTEs and data-modifying CTEs are always materialized,
whatever you write.

**Referenced once: inlined, and the filter reaches the index.**

```sql
EXPLAIN (ANALYZE, COSTS OFF)
WITH c AS (SELECT * FROM categories)
SELECT * FROM c WHERE id = 4242;
```

```text
 Index Scan using categories_pkey on categories (actual time=0.047..0.048 rows=1 loops=1)
   Index Cond: (id = 4242)
 Execution Time: 0.095 ms
```

No trace of the CTE in the plan: it was merged into the query. Force the old behaviour:

```sql
EXPLAIN (ANALYZE, COSTS OFF)
WITH c AS MATERIALIZED (SELECT * FROM categories)
SELECT * FROM c WHERE id = 4242;
```

```text
 CTE Scan on c (actual time=0.881..225.681 rows=1 loops=1)
   Filter: (id = 4242)
   Rows Removed by Filter: 999999
   CTE c
     ->  Seq Scan on categories (actual time=0.022..88.391 rows=1000000 loops=1)
 Execution Time: 229.934 ms
```

`CTE c` computed all million rows first; `CTE Scan` then filtered them. **0.095 ms →
229.9 ms.** How to recognize materialization in any plan: a `CTE name` subplan plus
`CTE Scan on name` nodes.

**Referenced twice: materialized by default, which can be a disaster.** A self-join
through a CTE:

```sql
EXPLAIN (ANALYZE, COSTS OFF)
WITH c AS (SELECT id, parent_id, name FROM categories)
SELECT a.name, p.name AS parent FROM c a JOIN c p ON p.id = a.parent_id WHERE a.id = 4242;
```

```text
 Merge Join (actual time=1956.091..1956.099 rows=1 loops=1)
   Merge Cond: (a.parent_id = p.id)
   CTE c
     ->  Seq Scan on categories (actual time=0.015..88.500 rows=1000000 loops=1)
   ->  Sort (actual time=1048.684..1048.687 rows=1 loops=1)
         Sort Key: a.parent_id
         ->  CTE Scan on c a (actual time=268.695..1048.637 rows=1 loops=1)
               Filter: (id = 4242)
               Rows Removed by Filter: 999999
   ->  Materialize (actual time=907.188..907.257 rows=425 loops=1)
         ->  Sort (actual time=907.178..907.208 rows=425 loops=1)
               Sort Key: p.id
               Sort Method: external merge  Disk: 33352kB
               ->  CTE Scan on c p (actual time=0.124..130.510 rows=1000000 loops=1)
 Execution Time: 1983.752 ms
```

Two references, so Postgres materialized the whole table and then sorted a million rows
(spilling 33 MB to disk) to find one parent. The CTE result has no indexes, so nothing
can use `categories_pkey`. With `NOT MATERIALIZED`, each reference is inlined separately:

```sql
EXPLAIN (ANALYZE, COSTS OFF)
WITH c AS NOT MATERIALIZED (SELECT id, parent_id, name FROM categories)
SELECT a.name, p.name AS parent FROM c a JOIN c p ON p.id = a.parent_id WHERE a.id = 4242;
```

```text
 Nested Loop (actual time=0.024..0.026 rows=1 loops=1)
   ->  Index Scan using categories_pkey on categories (actual time=0.012..0.013 rows=1 loops=1)
         Index Cond: (id = 4242)
   ->  Index Scan using categories_pkey on categories categories_1 (actual time=0.006..0.007 rows=1 loops=1)
         Index Cond: (id = categories.parent_id)
 Execution Time: 0.047 ms
```

**1,983.8 ms → 0.047 ms.** Same query text apart from two words.

**When materializing is the right call.** If the CTE is expensive and used several times,
computing it once is exactly what you want. Statistics about the fan-out of the tree,
used twice:

```sql
WITH fanout AS (SELECT parent_id, count(*) AS n FROM categories GROUP BY parent_id)
SELECT (SELECT max(n) FROM fanout) AS max_children,
       (SELECT avg(n) FROM fanout) AS avg_children;
```

| Variant | Plan | Execution time |
|---|---|---|
| default (materialized: 2 references) | aggregate over 1M rows **once**, both subqueries read the `CTE Scan` | 271.6 ms |
| `AS NOT MATERIALIZED` | the `GroupAggregate` over 1M rows appears **twice**, once per reference | 416.8 ms |

The rule of thumb:

- **Small result from an expensive computation, used more than once** → materialize (the
  default does this).
- **Large result, filtered or joined selectively by the outer query** → don't materialize.
  If it's referenced twice, write `NOT MATERIALIZED`.
- **Volatile functions** (`random()`, `clock_timestamp()`) in the CTE → it's materialized,
  which guarantees one evaluation. If you depend on "computed once", say
  `MATERIALIZED` explicitly so a later edit can't change it silently.
- **`MATERIALIZED` as a planner hint** is a legitimate last resort when the planner makes
  a bad choice because of a bad estimate (materialization stops it from pushing a
  predicate into the CTE). Fix the statistics first; leave a comment when you use it.
- On another database the rules differ: MySQL 8 merges or materializes derived tables and
  CTEs by its own heuristics, and SQL Server always inlines CTEs (it never materializes
  them). Don't assume Postgres behaviour elsewhere.

## From Python and Go

**Python (psycopg 3):** a parameterized itinerary search with `CYCLE` and a depth bound.
The `path` column is an array of row values, which psycopg returns as a list of tuples:

```python
import psycopg

DSN = "postgresql://dsa:dsa@localhost:5544/dsa"

ITINERARIES = """
WITH RECURSIVE trip(airport, total_min, hops) AS (
    SELECT %(origin)s::text, 0, 0
    UNION ALL
    SELECT r.dst, t.total_min + r.minutes, t.hops + 1
    FROM trip t JOIN routes r ON r.src = t.airport
    WHERE t.hops < %(max_hops)s
) CYCLE airport SET is_cycle USING path
SELECT path, total_min FROM trip
WHERE airport = %(dest)s AND NOT is_cycle
ORDER BY total_min
"""

with psycopg.connect(DSN) as conn:
    rows = conn.execute(ITINERARIES, {"origin": "LHR", "dest": "SFO", "max_hops": 4}).fetchall()
    for path, minutes in rows:
        print(minutes, path)
```

Real output:

```text
870 [('LHR',), ('JFK',), ('SFO',)]
965 [('LHR',), ('CDG',), ('JFK',), ('SFO',)]
```

**Go (native pgxpool):** a depth-bounded subtree printed as an indented tree, ordered by
`SEARCH DEPTH FIRST`:

```go
package main

import (
	"context"
	"fmt"
	"log"
	"strings"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Everything below category $1, depth-first, at most $2 levels down.
const subtree = `
WITH RECURSIVE sub(id, name, depth) AS (
    SELECT id, name, 0 FROM categories WHERE id = $1
    UNION ALL
    SELECT c.id, c.name, s.depth + 1
    FROM categories c JOIN sub s ON c.parent_id = s.id
    WHERE s.depth < $2
) SEARCH DEPTH FIRST BY id SET ord
SELECT name, depth FROM sub ORDER BY ord LIMIT 8`

func main() {
	ctx := context.Background()
	pool, err := pgxpool.New(ctx, "postgresql://dsa:dsa@localhost:5544/dsa")
	if err != nil {
		log.Fatal(err)
	}
	defer pool.Close()

	rows, err := pool.Query(ctx, subtree, 42, 2)
	if err != nil {
		log.Fatal(err)
	}
	defer rows.Close()
	for rows.Next() {
		var name string
		var depth int
		if err := rows.Scan(&name, &depth); err != nil {
			log.Fatal(err)
		}
		fmt.Println(strings.Repeat("  ", depth) + name)
	}
	if err := rows.Err(); err != nil {
		log.Fatal(err)
	}
}
```

Real output:

```text
cat-42
  cat-420
    cat-4200
    cat-4201
    cat-4202
    cat-4203
    cat-4204
    cat-4205
```

## Common mistakes

- **No termination guarantee on data that can have cycles.** Postgres will not stop a
  runaway recursive CTE for you. Use `CYCLE`, a path check, a depth bound, or all three,
  plus a `statement_timeout`.
- **Expecting `UNION` to stop cycles when rows carry a depth or path.** It only removes
  exact duplicates.
- **No index on the column the recursive term joins on** (`parent_id`, `src`). Every
  iteration becomes a full scan; the cost is multiplied by the depth.
- **Relying on output order without `ORDER BY`.** Use `SEARCH DEPTH/BREADTH FIRST` and
  order by its column.
- **Using a CTE twice on a large set and wondering why the index isn't used.** It was
  materialized. Look for `CTE Scan` in the plan; add `NOT MATERIALIZED`.
- **Relying on the pre-12 "CTE is a fence" behaviour after an upgrade.** Queries that
  were tuned around it can change plans. Write `MATERIALIZED` where you meant it.

## Interview questions

**"How does a recursive CTE execute?"** As a loop: run the base term, then repeatedly
run the recursive term against only the previous iteration's rows (the working table),
appending to the result, until an iteration produces nothing. With `UNION` instead of
`UNION ALL`, exact duplicate rows are dropped as they're found.

**"How do you stop a recursive query on a graph with cycles?"** Track the path and refuse
to revisit a node on it: by hand with an array and `<> ALL(path)`, or with the standard
`CYCLE col SET is_cycle USING path` clause (Postgres 14+). Add a depth bound where the
domain has one, and a `statement_timeout` as the backstop, because Postgres has no
built-in recursion limit.

**"Find all descendants of a node in a tree with a million rows. What makes it fast?"**
A recursive CTE joining on `parent_id`, with an index on `parent_id`; the plan should be a
nested loop with an index scan per found node, so cost scales with the subtree size. If
the tree is read far more than it's changed, a materialized path (`ltree`) or a closure
table makes it a single indexed lookup.

**"Is a CTE an optimization fence in Postgres?"** Not since 12. A side-effect-free,
non-recursive CTE referenced once is inlined. One referenced more than once, or with side
effects or volatile functions, is materialized. `MATERIALIZED` / `NOT MATERIALIZED`
override the choice. You can see it in `EXPLAIN`: a `CTE Scan` node means it was
materialized.

**"When would you choose a graph database over recursive SQL?"** When traversals are the
main workload: many hops, variable-length paths, shortest-path or pattern queries over
large, densely connected data. Recursive CTEs are fine for trees and shallow traversals
on data that lives in Postgres anyway. See [Graph Databases and Cypher](../NoSQL/concepts/03_graph_databases_and_cypher.md).

## What's next

That's the end of the SQL ladder. Level 19 is the interview summary of all of it;
`NoSQL/` covers the document, key-value, wide-column and graph side.
