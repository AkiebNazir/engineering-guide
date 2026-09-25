# Bonus: How Postgres Executes a Query

> **This level is optional.** It doesn't teach any new SQL or any new <abbr title="Application Programming Interface">API</abbr> — it
> connects the fifteen levels before it into one mental picture of what actually
> happens, end to end, inside Postgres, between you sending a query string and
> getting rows back. Read levels 00-14 first; this is the "so that's how all of that
> was actually happening" level.

**Already covered elsewhere, in more depth:** `CSFundamentals/03_databases_deep_dive.md`
covers storage engines, B-trees, and MVCC internals; `SystemDesign/building_blocks/06_database_internals.md`
covers the WAL, partitioning, and replication in a system-design framing. This level
doesn't re-derive either — it's the connective tissue between the four stages a
single query passes through, pointing to those two files for the deep dive on
storage/durability/MVCC specifically.

## The four stages

```arch
%% caption: A query passes through parser, rewriter, planner and executor; only the executor touches storage.
grid 230x100
node q "SQL text" at 0,0 shape=card icon=code sub="SELECT * FROM accounts_big WHERE email = '...'"
node p "Parser" at 0,1 icon=code
node r "Rewriter" at 0,2 icon=edit
node pl "Planner / Optimizer" at 0,3 icon=speed
node e "Executor" at 0,4 icon=process
node s "Storage" at 0,5 shape=card icon=disk sub="heap pages, indexes, WAL"
node out "Rows returned to client" at 1,4 icon=table
q -> p
p -> r : "parse tree"
r -> pl : "rewritten query"
pl -> e : "chosen plan"
e -> s : "reads/writes"
e -> out
```

### 1. Parser

Turns the SQL text into a **parse tree** — a structured representation of what you
asked for, purely syntactic. This stage catches syntax errors (`SELCT` instead of
`SELECT`) and resolves table/column names against the catalog, but it has no opinion
yet about *how* to execute anything.

### 2. Rewriter

Applies rule-based rewrites before planning — the main one you'll actually run into
is expanding a **view** into its underlying query. `SELECT * FROM active_users`
where `active_users` is `CREATE VIEW active_users AS SELECT * FROM users WHERE
status = 'active'` gets rewritten here into the equivalent query against the real
table, before the planner ever sees it.

### 3. Planner / Optimizer

The stage every level from 04 through 13 was implicitly leaning on. Given the
rewritten query, the planner considers multiple possible **execution plans** —
sequential scan vs index scan, which join algorithm (nested loop, hash join, merge
join), which order to join tables in — and picks the one with the lowest *estimated*
cost, using the table statistics `ANALYZE` maintains (level 10).

This is exactly what `EXPLAIN` shows you *before* execution, and what
`EXPLAIN ANALYZE` shows you *with real numbers* after actually running the chosen
plan. The level 10 measurement bears repeating here specifically because it's the
planner's decision, made visible:

```text
-- no index on email: planner chose a Parallel Seq Scan
Execution Time: 5.865 ms

-- index on email: planner chose an Index Scan instead
Execution Time: 0.024 ms
```

Both plans return the *same rows* — the planner's whole job is choosing which
*path* to those rows costs least, given what indexes and statistics currently exist.
Add an index, and the planner's cost model changes its mind about which plan wins;
you never told it to use the index, you just made a cheaper option exist.

### 4. Executor

Actually runs the chosen plan, node by node (the tree structure you see in
`EXPLAIN`'s output — `Aggregate` on top of `Bitmap Heap Scan` on top of
`Bitmap Index Scan`, from level 10's composite-index example, is literally the
executor's node tree). Each node pulls rows from the node(s) below it — a
demand-pull model, where the top node asks the next node down for one row at a time
rather than materializing everything at once (with some exceptions, like a sort or
hash-build step that must consume all its input before producing any output).

**Go: the executor's node tree isn't just a human-readable string — it's structured
data you can consume.** `EXPLAIN (ANALYZE, FORMAT JSON)` returns the exact same plan
tree as a JSON document instead of the indented text every other level's demos use —
genuinely useful for a service that wants to programmatically watch for a specific
query regressing to a sequential scan, rather than a human reading `EXPLAIN` output by
eye:

```go
type PlanNode struct {
    NodeType        string     `json:"Node Type"`
    RelationName    string     `json:"Relation Name"`
    ActualTotalTime float64    `json:"Actual Total Time"`
    ActualRows      int        `json:"Actual Rows"`
    Plans           []PlanNode `json:"Plans"`   // the executor's node tree, recursively
}

var raw []byte
pool.QueryRow(ctx, `EXPLAIN (ANALYZE, FORMAT JSON) SELECT * FROM bonus_demo_go WHERE email = 'user12345'`).Scan(&raw)

var result []struct {
    Plan          PlanNode `json:"Plan"`
    ExecutionTime float64  `json:"Execution Time"`
}
json.Unmarshal(raw, &result)
```

Real output, walking the parsed tree recursively (`func walk(n PlanNode, depth int)`,
printing each node then recursing into `n.Plans`):

```text
executor node tree, parsed programmatically from EXPLAIN's JSON:
Index Scan on bonus_demo_go -- 0.010ms, 1 rows
total execution time (from the JSON, not re-derived): 0.017ms
```

A single-node tree here because this query is simple (one indexed point lookup) — the
same `PlanNode.Plans` recursion is exactly how you'd walk the multi-level
`Aggregate → Gather → Parallel Bitmap Heap Scan → Bitmap Index Scan` tree from level
10's composite-index example programmatically: each nesting level in that indented
text output is one more entry in `Plans`. This is the real, practical reason
`FORMAT JSON` exists — automated query-plan monitoring reads this, not the text format
meant for a human at a terminal.

### 5. Storage

Where the executor's requests actually land: heap pages (the table's row data) and
index pages (B-trees, by default — level 10), read through Postgres's buffer cache,
with every write also going through the write-ahead log first for durability. This
is the layer `CSFundamentals/03_databases_deep_dive.md` and
`SystemDesign/building_blocks/06_database_internals.md` cover in real depth — WAL
mechanics, MVCC's `xmin`/`xmax` row versioning, page layout, vacuum — none of which
this level re-explains.

<div class="lab" data-viz="flow-pg-query"></div>

## Connecting it to what you already ran

Every level in this module exercised this pipeline without naming it:

- Level 05's constraint violations (`UniqueViolation`, `CheckViolation`,
  `ForeignKeyViolation`) are checked by the executor as it attempts to write a row,
  before the write is allowed to reach storage.
- Level 09's `SELECT ... FOR UPDATE` and `SerializationFailure` are the executor
  interacting with Postgres's lock manager and MVCC snapshot machinery mid-execution.
- Level 10's `EXPLAIN ANALYZE` output *is* a direct, literal printout of the
  planner's chosen node tree plus the executor's real measured timings per node.
- Level 12's `ALTER TABLE` locking behavior is a storage-layer fact (whether the
  statement can be metadata-only or must rewrite heap pages) that has nothing to do
  with the parser, rewriter, or planner at all.

## What's next

That's the ladder. `SQL/README.md` has the full roadmap if you want to revisit an
earlier level with this end-to-end picture in mind — several of them (especially 09,
10, and 12) reward a second read once you know what's actually happening
underneath.
