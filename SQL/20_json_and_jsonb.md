# JSON and JSONB

## The mental model

Every level so far has put each fact in its own typed column. That's the right default,
but real systems keep running into data that doesn't fit a fixed set of columns: a
webhook payload from a third party whose shape you don't control, product attributes
that differ per category (shoes have sizes, jackets have a lining), per-tenant custom
fields, feature-flag configs. The pre-2012 answers were all bad — an
entity-attribute-value table (one row per attribute, painful to query), a `TEXT` column
holding serialized JSON (the database can't look inside it), or a separate document
database next to Postgres.

Postgres's answer is to make JSON a real column type the database understands: it can
validate it, reach inside it with operators, index it, and constrain it. That lets one
table be **mostly relational with a flexible part** — typed columns for the fields you
query and join on, a `JSONB` column for the long tail. This level covers the two JSON
types, the operators, how to index them (and which index for which operator), the
generated-column trick for promoting a hot key to a real column, and the honest answer
to the interview question *"when would you use JSONB instead of columns?"*.

## `json` vs `jsonb`: store the text, or store the parsed value

Postgres has two JSON types, and the difference is what's on disk:

- **`json`** stores the **input text verbatim**. It checks the text is valid JSON, then
  keeps it exactly as written — whitespace, key order, even duplicate keys. Every
  operator you apply re-parses the text from scratch.
- **`jsonb`** ("JSON binary") **parses once on write** into a decomposed binary format.
  Whitespace is dropped, keys are stored sorted (shorter keys first, then bytewise),
  and a duplicate key keeps only its **last** value. Reads don't re-parse, and — the
  reason it exists — `jsonb` supports containment/existence operators and GIN indexes.

```sql
SELECT '{"b": 1, "a": 2, "a": 3}'::json  AS as_json,
       '{"b": 1, "a": 2, "a": 3}'::jsonb AS as_jsonb;
```

Real output:

```text
         as_json          |     as_jsonb
--------------------------+------------------
 {"b": 1, "a": 2, "a": 3} | {"a": 3, "b": 1}
```

The `json` value is byte-for-byte what came in; the `jsonb` value has been
normalized — `"a": 2` is gone, and the keys are reordered. **Default to `jsonb`.**
Reach for `json` only when you must preserve the exact input (e.g. storing a signed
webhook body whose signature is computed over the raw bytes — though `TEXT`/`BYTEA`
is often more honest for that) or when you only ever write and read the whole value
back and never look inside it.

## Setup used for this level

A `products` table: typed columns for what every product has, `attrs JSONB` for what
varies per product.

```sql
DROP TABLE IF EXISTS products;
CREATE TABLE products (
    id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name  TEXT NOT NULL,
    attrs JSONB NOT NULL DEFAULT '{}'
);
INSERT INTO products (name, attrs) VALUES
  ('Trail shoe',  '{"brand": "Ridge", "color": "red",  "sizes": [41, 42, 43], "price": 129.00, "specs": {"weight_g": 280, "waterproof": true}}'),
  ('Road shoe',   '{"brand": "Ridge", "color": "blue", "sizes": [42, 44],     "price": 99.50,  "specs": {"weight_g": 240}}'),
  ('Rain jacket', '{"brand": "Nimbus", "color": "red", "price": 180, "specs": {"waterproof": true}, "discontinued": null}'),
  ('Sock 3-pack', '{"brand": "Ridge", "price": 9, "tags": ["sale", "bundle"]}');
```

## Reading values out: `->`, `->>`, `#>`, `#>>`, and subscripts

| Operator | Returns | Meaning |
|---|---|---|
| `attrs -> 'color'` | `jsonb` | value at key (or array index, `-> 0`) |
| `attrs ->> 'color'` | `text` | same, but converted to `text` |
| `attrs #> '{specs,weight_g}'` | `jsonb` | value at a path |
| `attrs #>> '{sizes,0}'` | `text` | value at a path, as `text` |
| `attrs['specs']['waterproof']` | `jsonb` | subscript syntax (Postgres 14+), same as chained `->` |

```sql
SELECT name,
       attrs -> 'color'               AS arrow_jsonb,
       attrs ->> 'color'              AS arrow_text,
       attrs -> 'specs' -> 'weight_g' AS nested,
       attrs #>> '{sizes,0}'          AS first_size,
       attrs['specs']['waterproof']   AS subscript
FROM products ORDER BY id;
```

```text
    name     | arrow_jsonb | arrow_text | nested | first_size | subscript
-------------+-------------+------------+--------+------------+-----------
 Trail shoe  | "red"       | red        | 280    | 41         | true
 Road shoe   | "blue"      | blue       | 240    | 42         |
 Rain jacket | "red"       | red        |        |            | true
 Sock 3-pack |             |            |        |            |
```

Note the quotes: `-> 'color'` returns the **JSON string** `"red"` (type `jsonb`),
`->> 'color'` returns the **SQL text** `red`. A missing key or path is not an error — it
returns SQL `NULL`, which is why the Sock 3-pack row is mostly empty. The one-letter
difference between `->` and `->>` is the single most common JSONB bug; the next two
sections are both consequences of it.

## Filtering: containment (`@>`) and existence (`?`)

These are the operators that make `jsonb` more than a text blob, and — crucially —
the ones GIN indexes can accelerate:

| Operator | Question it answers |
|---|---|
| `a @> b` | Does `a` **contain** `b`? (every key/value in `b` is in `a`, recursively; array elements are matched as a subset) |
| `a <@ b` | Is `a` contained in `b`? |
| `a ? 'k'` | Does top-level key (or array string element) `'k'` exist? |
| `a ?\| array['k1','k2']` | Does **any** of these keys exist? |
| `a ?& array['k1','k2']` | Do **all** of these keys exist? |
| `a @? 'jsonpath'` / `a @@ 'jsonpath'` | Does the SQL/JSON path return any item / evaluate to true? |

```sql
SELECT name FROM products WHERE attrs @> '{"color": "red"}';
--  Trail shoe, Rain jacket

SELECT name FROM products WHERE attrs @> '{"specs": {"waterproof": true}}';
--  Trail shoe, Rain jacket            (containment is recursive into nested objects)

SELECT name FROM products WHERE attrs @> '{"sizes": [44]}';
--  Road shoe                          ([44] is "a subset of the sizes array")

SELECT name FROM products WHERE attrs ? 'tags';
--  Sock 3-pack

SELECT name FROM products WHERE attrs ?| array['tags', 'sizes'];
--  Trail shoe, Road shoe, Sock 3-pack
```

(Results shown as comments to keep the page short; each is real output, rows in `id`
order.)

`@>` is the workhorse: "find rows whose document has at least these key/value pairs"
covers most equality filtering on JSON, and it's index-friendly. The equivalent-looking
`attrs ->> 'color' = 'red'` returns the same rows but, as measured below, **cannot use a
GIN index** — prefer `@>` for equality filters on JSON.

## Two traps: everything from `->>` is text, and there are two kinds of null

**Text comparison.** `->>` always returns `text`, so comparing it to a number compares
**strings**, character by character:

```sql
SELECT name, attrs->>'price' AS price_text FROM products
WHERE attrs->>'price' > '100' ORDER BY id;
```

```text
    name     | price_text
-------------+------------
 Trail shoe  | 129.00
 Road shoe   | 99.50
 Rain jacket | 180
 Sock 3-pack | 9
```

Every row matched — `'99.50' > '100'` and `'9' > '100'` are both true as strings
(`'9'` sorts after `'1'`). Cast explicitly to get numeric comparison:

```sql
SELECT name, (attrs->>'price')::numeric AS price FROM products
WHERE (attrs->>'price')::numeric > 100 ORDER BY id;
```

```text
    name     | price
-------------+--------
 Trail shoe  | 129.00
 Rain jacket |    180
```

(If any row holds a non-numeric `price`, the cast raises an error for the whole query —
a good argument for the `CHECK` constraints further down.)

**JSON `null` vs SQL `NULL`.** A key whose value is JSON `null` is different from a key
that is absent:

```sql
SELECT name,
       attrs -> 'discontinued'              AS arrow,
       (attrs -> 'discontinued') IS NULL    AS arrow_is_sql_null,
       attrs ->> 'discontinued'             AS text_val,
       attrs ? 'discontinued'               AS key_exists
FROM products WHERE name IN ('Rain jacket', 'Road shoe') ORDER BY id;
```

```text
    name     | arrow | arrow_is_sql_null | text_val | key_exists
-------------+-------+-------------------+----------+------------
 Road shoe   |       | t                 |          | f
 Rain jacket | null  | f                 |          | t
```

For Road shoe the key is absent, so `->` gives SQL `NULL`. For Rain jacket the key
exists with JSON `null`, so `->` gives the **non-NULL** `jsonb` value `null` — and
`IS NULL` is false. `->>` flattens both to SQL `NULL`, hiding the difference. If your
application distinguishes "field not sent" from "field explicitly cleared" (PATCH
semantics), use `?` or `->` and `jsonb_typeof()`, never `->>`.

## SQL/JSON path (`jsonpath`)

Postgres 12+ implements the SQL-standard JSON path language — a small query language
for reaching into documents, including filters over arrays:

```sql
SELECT name FROM products WHERE attrs @? '$.sizes[*] ? (@ >= 43)' ORDER BY id;
```

```text
    name
------------
 Trail shoe
 Road shoe
```

```sql
SELECT name, jsonb_path_query_array(attrs, '$.sizes[*] ? (@ >= 42)') AS big_sizes
FROM products WHERE attrs ? 'sizes' ORDER BY id;
```

```text
    name    | big_sizes
------------+-----------
 Trail shoe | [42, 43]
 Road shoe  | [42, 44]
```

`$` is the document root, `[*]` iterates an array, `? (...)` filters, `@` is the current
item. `@?` and `@@` can use a GIN index. Postgres 16 also accepts the standard
`IS JSON [OBJECT|ARRAY|SCALAR]` predicate and the `JSON_OBJECT(...)`/`JSON_ARRAY(...)`
constructors; Postgres 17 adds `JSON_TABLE`, `JSON_VALUE`, `JSON_QUERY` and
`JSON_EXISTS`. The operators above work on every supported version, so this level
sticks to them.

## Modifying documents

`jsonb` values are immutable — every "modification" computes a new value and the
`UPDATE` writes it back:

```sql
UPDATE products SET attrs = attrs || '{"color": "green", "on_sale": true}'
WHERE name = 'Sock 3-pack';                                   -- || : merge / overwrite keys (shallow)
UPDATE products SET attrs = jsonb_set(attrs, '{specs,weight_g}', '250')
WHERE name = 'Road shoe';                                     -- set a value at a path
UPDATE products SET attrs = attrs - 'discontinued'
WHERE name = 'Rain jacket';                                   -- - : remove a top-level key
UPDATE products SET attrs = attrs #- '{specs,waterproof}'
WHERE name = 'Trail shoe';                                    -- #- : remove at a path
UPDATE products SET attrs['specs']['lining'] = '"mesh"'
WHERE name = 'Rain jacket';                                   -- subscript assignment (PG 14+)

SELECT name, attrs FROM products ORDER BY id;
```

```text
    name     |                                                 attrs
-------------+--------------------------------------------------------------------------------------------------------
 Trail shoe  | {"brand": "Ridge", "color": "red", "price": 129.00, "sizes": [41, 42, 43], "specs": {"weight_g": 280}}
 Road shoe   | {"brand": "Ridge", "color": "blue", "price": 99.50, "sizes": [42, 44], "specs": {"weight_g": 250}}
 Rain jacket | {"brand": "Nimbus", "color": "red", "price": 180, "specs": {"lining": "mesh", "waterproof": true}}
 Sock 3-pack | {"tags": ["sale", "bundle"], "brand": "Ridge", "color": "green", "price": 9, "on_sale": true}
```

Two details visible here: `||` is a **shallow** merge (it replaces a whole nested
object rather than merging into it — use `jsonb_set` for nested paths), and the Sock
3-pack's keys came back in `jsonb`'s storage order (`"tags"` first because it's the
shortest key), not insertion order. Never depend on key order in `jsonb`.

## Turning JSON into rows, and rows into JSON

Set-returning functions let you join against the inside of a document:

```sql
SELECT p.name, s.size::int AS size
FROM products p, jsonb_array_elements_text(p.attrs -> 'sizes') AS s(size)
ORDER BY p.id, size;
```

```text
    name    | size
------------+------
 Trail shoe |   41
 Trail shoe |   42
 Trail shoe |   43
 Road shoe  |   42
 Road shoe  |   44
```

```sql
SELECT key, value FROM products, jsonb_each(attrs) WHERE name = 'Road shoe' ORDER BY key;
```

```text
  key  |       value
-------+-------------------
 brand | "Ridge"
 color | "blue"
 price | 99.50
 sizes | [42, 44]
 specs | {"weight_g": 250}
```

`jsonb_to_recordset` turns an array of objects straight into a typed row set — handy for
bulk-loading a JSON payload through one parameter:

```sql
SELECT * FROM jsonb_to_recordset('[{"sku":"A1","qty":2},{"sku":"B7","qty":5}]')
    AS x(sku text, qty int);
```

```text
 sku | qty
-----+-----
 A1  |   2
 B7  |   5
```

The other direction — building a JSON response in the database, which saves a round
of object mapping in the application:

```sql
SELECT attrs->>'brand' AS brand,
       jsonb_agg(jsonb_build_object('name', name, 'price', (attrs->>'price')::numeric)
                 ORDER BY name) AS items
FROM products GROUP BY 1 ORDER BY 1;
```

```text
 brand  |                                                         items
--------+-----------------------------------------------------------------------------------------------------------------------
 Nimbus | [{"name": "Rain jacket", "price": 180}]
 Ridge  | [{"name": "Road shoe", "price": 99.50}, {"name": "Sock 3-pack", "price": 9}, {"name": "Trail shoe", "price": 129.00}]
```

## Putting a schema back: `CHECK` constraints on JSONB

"Schemaless" is a property you opt out of one key at a time. `CHECK` constraints can
enforce the parts of the document shape your code relies on:

```sql
ALTER TABLE products
  ADD CONSTRAINT attrs_is_object    CHECK (jsonb_typeof(attrs) = 'object'),
  ADD CONSTRAINT attrs_has_brand    CHECK (attrs ? 'brand'),
  ADD CONSTRAINT attrs_price_is_num CHECK (jsonb_typeof(attrs -> 'price') = 'number');

INSERT INTO products (name, attrs) VALUES ('Mystery item', '{"price": "cheap", "brand": "X"}');
INSERT INTO products (name, attrs) VALUES ('Mystery item', '[1,2,3]');
```

```text
ERROR:  new row for relation "products" violates check constraint "attrs_price_is_num"
DETAIL:  Failing row contains (5, Mystery item, {"brand": "X", "price": "cheap"}).
ERROR:  new row for relation "products" violates check constraint "attrs_has_brand"
DETAIL:  Failing row contains (6, Mystery item, [1, 2, 3]).
```

(The array hit `attrs_has_brand` rather than `attrs_is_object` because Postgres checks
a table's constraints in name order; either way it's rejected.) What you **cannot** do
is point a foreign key at a value inside a document — if a JSON field references
another table's row, that's a strong signal it should be a real column.

## From Python and Go

**Python (psycopg 3):** wrap a `dict` in `Jsonb(...)` to send it as `jsonb`; `jsonb`
columns come back already parsed into Python objects:

```python
import psycopg
from psycopg.types.json import Jsonb

DSN = "postgresql://dsa:dsa@localhost:5544/dsa"

with psycopg.connect(DSN) as conn:
    attrs = {"brand": "Vela", "color": "black", "price": 64.5, "sizes": [40, 41]}
    new_id = conn.execute(
        "INSERT INTO products (name, attrs) VALUES (%s, %s) RETURNING id",
        ("Approach shoe", Jsonb(attrs)),          # Jsonb(...) = send as jsonb, not text
    ).fetchone()[0]

    row = conn.execute("SELECT attrs FROM products WHERE id = %s", (new_id,)).fetchone()
    print(type(row[0]).__name__, row[0])          # jsonb comes back already parsed

    # containment filter, parameterized: the whole JSON fragment is ONE bind parameter
    names = conn.execute(
        "SELECT name FROM products WHERE attrs @> %s ORDER BY id",
        (Jsonb({"brand": "Ridge"}),),
    ).fetchall()
    print([n for (n,) in names])
```

Real output:

```text
dict {'brand': 'Vela', 'color': 'black', 'price': 64.5, 'sizes': [40, 41]}
['Trail shoe', 'Road shoe', 'Sock 3-pack']
```

The containment filter is fully parameterized — the JSON fragment travels as one bind
value, so level 11's injection rules hold unchanged. One precision note: `jsonb` stores
numbers as `numeric` (exact), but the default Python loader parses them with `json.loads`,
so they arrive as `float`. If you store money in JSON, pass a custom loader
(`json.loads(..., parse_float=Decimal)`) or, better, keep money in a `NUMERIC` column.

**Go (native pgxpool):** pgx encodes any Go value passed for a `jsonb` parameter with
`encoding/json`, and scans a `jsonb` column straight into a struct or `map[string]any`:

```go
type Specs struct {
	WeightG    *int  `json:"weight_g,omitempty"`
	Waterproof *bool `json:"waterproof,omitempty"`
}

type Attrs struct {
	Brand string  `json:"brand"`
	Color string  `json:"color,omitempty"`
	Price float64 `json:"price"`
	Sizes []int   `json:"sizes,omitempty"`
	Specs *Specs  `json:"specs,omitempty"`
}

func main() {
	ctx := context.Background()
	pool, err := pgxpool.New(ctx, "postgresql://dsa:dsa@localhost:5544/dsa")
	if err != nil {
		log.Fatal(err)
	}
	defer pool.Close()

	// A Go struct passed for a jsonb parameter is encoded with encoding/json.
	_, err = pool.Exec(ctx,
		`INSERT INTO products (name, attrs) VALUES ($1, $2)`,
		"Gym shoe", Attrs{Brand: "Alto", Color: "white", Price: 75, Sizes: []int{39, 40}})
	if err != nil {
		log.Fatal(err)
	}

	// ...and a jsonb column scans straight into a struct (or map[string]any).
	rows, err := pool.Query(ctx,
		`SELECT name, attrs FROM products WHERE attrs @> $1 ORDER BY id`,
		map[string]any{"color": "red"})
	if err != nil {
		log.Fatal(err)
	}
	defer rows.Close()
	for rows.Next() {
		var name string
		var a Attrs
		if err := rows.Scan(&name, &a); err != nil {
			log.Fatal(err)
		}
		fmt.Printf("%-12s brand=%s price=%.2f sizes=%v\n", name, a.Brand, a.Price, a.Sizes)
	}
	if err := rows.Err(); err != nil {
		log.Fatal(err)
	}
}
```

Real output:

```text
Trail shoe   brand=Ridge price=129.00 sizes=[41 42 43]
Rain jacket  brand=Nimbus price=180.00 sizes=[]
```

Scanning into a struct is where the "schemaless" column meets a schema again: the Go
type *is* the schema, enforced only at read time. Keys the struct doesn't declare are
silently dropped by `encoding/json`, which is exactly how a field goes missing after a
read-modify-write in application code — prefer server-side `jsonb_set`/`||` updates for
partial changes.

## Indexing JSONB, measured

Four demo rows can't show an index doing anything. A 300,000-row catalog can:

```sql
DROP TABLE IF EXISTS catalog;
CREATE TABLE catalog (
    id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    attrs JSONB NOT NULL
);
INSERT INTO catalog (attrs)
SELECT jsonb_build_object(
    'sku',      'SKU-' || i,
    'brand',    (ARRAY['Ridge','Nimbus','Alto','Kestrel','Vela'])[1 + i % 5],
    'color',    (ARRAY['red','blue','green','black','white','grey','orange','purple'])[1 + (i / 5) % 8],
    'price',    round((5 + random() * 495)::numeric, 2),
    'in_stock', (i % 10) <> 0,
    'tags',     CASE WHEN i % 100 = 0 THEN '["clearance"]'::jsonb ELSE '[]'::jsonb END
)
FROM generate_series(1, 300000) AS i;
ANALYZE catalog;
SELECT pg_size_pretty(pg_table_size('catalog'));   -- 45 MB
```

Every 100th product is tagged `clearance` (3,000 rows). With no index, finding them is
a full scan:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*) FROM catalog WHERE attrs @> '{"tags": ["clearance"]}';
```

```text
Finalize Aggregate  (cost=8332.74..8332.75 rows=1 width=8) (actual time=44.444..48.717 rows=1 loops=1)
  Buffers: shared hit=5770
  ->  Gather  (cost=8332.53..8332.74 rows=2 width=8) (actual time=44.358..48.710 rows=3 loops=1)
        Workers Planned: 2
        Workers Launched: 2
        Buffers: shared hit=5770
        ->  Partial Aggregate  (cost=7332.53..7332.54 rows=1 width=8) (actual time=39.118..39.119 rows=1 loops=3)
              Buffers: shared hit=5770
              ->  Parallel Seq Scan on catalog  (cost=0.00..7332.50 rows=12 width=0) (actual time=0.047..39.011 rows=1000 loops=3)
                    Filter: (attrs @> '{"tags": ["clearance"]}'::jsonb)
                    Rows Removed by Filter: 99000
                    Buffers: shared hit=5770
Execution Time: 48.808 ms
```

### GIN: an inverted index over the document's contents

A B-tree indexes one sortable value per row. A **GIN** (Generalized Inverted iNdex)
index is built for values that *contain many things* — arrays, full-text documents,
JSON: it breaks each value into **keys**, and for each key stores the list of rows that
contain it, like the index at the back of a book. A containment query looks up each key
of the query document and intersects the row lists. `jsonb` comes with two GIN
**operator classes** that choose what the keys are:

- **`jsonb_ops`** (the default — `USING GIN (attrs)`): one index entry for every key
  **and** every value, separately. Supports `@>`, `?`, `?|`, `?&`, `@?`, `@@`.
- **`jsonb_path_ops`** (`USING GIN (attrs jsonb_path_ops)`): one entry per **path +
  value** pair, hashed (e.g. a hash of `tags → "clearance"`). Supports only `@>`, `@?`,
  `@@` — **no key-existence (`?`) operators**, because keys aren't indexed on their
  own. In exchange it's smaller and more selective: a lookup for
  `{"tags": ["clearance"]}` hits exactly one hashed entry instead of intersecting the
  entries for key `tags` and value `clearance`.

```sql
CREATE INDEX catalog_attrs_gin      ON catalog USING GIN (attrs);
CREATE INDEX catalog_attrs_gin_path ON catalog USING GIN (attrs jsonb_path_ops);

SELECT indexrelid::regclass AS index, pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_index WHERE indrelid = 'catalog'::regclass ORDER BY 1;
```

```text
         index          |  size
------------------------+---------
 catalog_pkey           | 6600 kB
 catalog_attrs_gin      | 28 MB
 catalog_attrs_gin_path | 22 MB
```

Then the same queries with only one of the two indexes present at a time (each test
wraps `DROP INDEX` of the other one in a `BEGIN ... ROLLBACK`, so both survive):

| Query | No index | `jsonb_ops` GIN | `jsonb_path_ops` GIN |
|---|---|---|---|
| `attrs @> '{"tags": ["clearance"]}'` (3,000 rows) | 48.8 ms, seq scan | 9.1 ms, 88 index buffers | **3.9 ms, 5 index buffers** |
| `attrs @> '{"brand": "Vela", "color": "red"}'` (7,500 rows) | seq scan | 15.0 ms, 188 index buffers | **9.4 ms, 30 index buffers** |
| `attrs ? 'discontinued'` (0 rows) | seq scan | **0.02 ms, index used** | 22.9 ms, **seq scan — can't use it** |
| `attrs ->> 'color' = 'red'` (37,500 rows) | 23.7 ms, seq scan | seq scan — can't use it | seq scan — can't use it |

The `jsonb_path_ops` plan for the clearance query, for reference:

```text
Aggregate  (cost=131.22..131.23 rows=1 width=8) (actual time=3.909..3.910 rows=1 loops=1)
  Buffers: shared hit=3005
  ->  Bitmap Heap Scan on catalog  (cost=17.25..131.14 rows=30 width=0) (actual time=0.787..3.743 rows=3000 loops=1)
        Recheck Cond: (attrs @> '{"tags": ["clearance"]}'::jsonb)
        Heap Blocks: exact=3000
        Buffers: shared hit=3005
        ->  Bitmap Index Scan on catalog_attrs_gin_path  (cost=0.00..17.25 rows=30 width=0) (actual time=0.398..0.398 rows=3000 loops=1)
              Index Cond: (attrs @> '{"tags": ["clearance"]}'::jsonb)
              Buffers: shared hit=5
Execution Time: 3.926 ms
```

What the numbers say (timings are from one laptop run and move ±30% between runs; the
buffer counts and plan shapes are the stable part):

- **GIN plans are always Bitmap Index Scan → Bitmap Heap Scan with a `Recheck Cond`.**
  GIN returns candidate rows; the heap row is re-checked because `jsonb_path_ops`
  hashes can collide and some `jsonb_ops` matches are lossy.
- **`jsonb_path_ops` did the same containment lookups touching 5–15x fewer index
  pages**, and is ~20% smaller here (the gap is bigger on documents with deeper
  nesting and more distinct keys; the Postgres docs describe it as "usually much
  smaller"). If your queries are `@>`, it's the better choice.
- **`jsonb_path_ops` silently can't serve `?`** — the planner falls back to a
  sequential scan, no error. Pick the operator class for the operators you actually
  run.
- **Neither GIN index helps `->>` equality.** `attrs ->> 'color' = 'red'` is an
  expression on a text value, and GIN indexes the document, not that expression.
  Rewrite it as `attrs @> '{"color": "red"}'`, or index the expression (next section).
- **Look at the estimates.** For the clearance query the planner estimated **30 rows**
  and got **3,000**; for brand+color, 3,030 vs 7,500. Postgres keeps no per-key
  statistics inside a `jsonb` column, so containment selectivity is a fixed guess. On a
  query that joins on to other tables, a 100x underestimate is how you get a nested
  loop that runs for minutes. More on fixing that below.
- **GIN is expensive to maintain.** One inserted document creates many index entries.
  GIN softens this with a *pending list* (`fastupdate`, on by default): new entries go
  to an unsorted list merged in bulk later — faster inserts, but lookups must scan the
  pending list too, and the merge happens during a vacuum or when the list outgrows
  `gin_pending_list_limit` (4 MB default), which can stall an unlucky insert. On a
  write-heavy table, measure before adding a whole-document GIN index.

## One hot key: an expression index or a generated column

When the same key is filtered, sorted or range-queried constantly, index **that key**,
not the whole document.

**Expression index** — a B-tree on the extracted value. Equality lookups on a single
key become a normal index scan:

```sql
CREATE INDEX catalog_sku ON catalog ((attrs ->> 'sku'));
ANALYZE catalog;
EXPLAIN (ANALYZE) SELECT id FROM catalog WHERE attrs ->> 'sku' = 'SKU-123456';
```

```text
Index Scan using catalog_sku on catalog  (cost=0.42..8.44 rows=1 width=8) (actual time=0.030..0.030 rows=1 loops=1)
  Index Cond: ((attrs ->> 'sku'::text) = 'SKU-123456'::text)
Execution Time: 0.058 ms
```

The query must use the **exact same expression** as the index — `attrs -> 'sku'` (the
`jsonb` version) or `attrs #>> '{sku}'` would not match it. That fragility is the
argument for the next option.

**Generated column** — promote the key to a real, typed column that Postgres keeps in
sync with the document. A numeric range over `price` with no index scans everything:

```sql
EXPLAIN (ANALYZE) SELECT count(*) FROM catalog
WHERE (attrs ->> 'price')::numeric BETWEEN 100 AND 101;
```

```text
...
        ->  Parallel Seq Scan on catalog  (cost=0.00..9520.00 rows=625 width=0) (actual time=0.457..72.913 rows=208 loops=3)
              Filter: ((((attrs ->> 'price'::text))::numeric >= '100'::numeric) AND (((attrs ->> 'price'::text))::numeric <= '101'::numeric))
              Rows Removed by Filter: 99792
Execution Time: 83.812 ms
```

```sql
ALTER TABLE catalog
  ADD COLUMN price NUMERIC(10,2) GENERATED ALWAYS AS ((attrs ->> 'price')::numeric) STORED;
CREATE INDEX catalog_price ON catalog (price);
ANALYZE catalog;

EXPLAIN (ANALYZE) SELECT count(*) FROM catalog WHERE price BETWEEN 100 AND 101;
```

```text
Aggregate  (cost=1897.44..1897.45 rows=1 width=8) (actual time=3.396..3.398 rows=1 loops=1)
  ->  Bitmap Heap Scan on catalog  (cost=15.03..1895.83 rows=645 width=0) (actual time=0.175..3.325 rows=623 loops=1)
        Recheck Cond: ((price >= '100'::numeric) AND (price <= '101'::numeric))
        Heap Blocks: exact=585
        ->  Bitmap Index Scan on catalog_price  (cost=0.00..14.87 rows=645 width=0) (actual time=0.102..0.103 rows=623 loops=1)
              Index Cond: ((price >= '100'::numeric) AND (price <= '101'::numeric))
Execution Time: 3.421 ms
```

**83.8 ms → 3.4 ms**, and look at the estimate: **645 predicted, 623 actual**. Before
the generated column, the planner had no statistics for the expression and used a
default guess (625 per worker, ~1,500 total — off by 2.4x). A real column gets real
`ANALYZE` statistics, and application code queries a plain `price` column that reads
like any other. The column stays correct automatically:

```sql
UPDATE catalog SET attrs = jsonb_set(attrs, '{price}', '42.00') WHERE id = 1;
SELECT id, attrs->>'price' AS json_price, price FROM catalog WHERE id = 1;
```

```text
 id | json_price | price
----+------------+-------
  1 | 42.00      | 42.00
```

```sql
UPDATE catalog SET price = 1 WHERE id = 1;
```

```text
ERROR:  column "price" can only be updated to DEFAULT
DETAIL:  Column "price" is a generated column.
```

Generated-column facts worth knowing precisely:

- **`STORED` is the only kind in Postgres 12–17** — the value is computed on write and
  occupies disk. **Postgres 18** (released September 2025) adds `VIRTUAL` generated
  columns, computed on read, and makes `VIRTUAL` the default when neither keyword is
  given; Postgres 18 cannot index a virtual column, so for an *indexed* promoted key
  you still write `STORED`.
- The expression must be **immutable** (same input, same output forever) — `now()` or
  a lookup into another table isn't allowed.
- **`ADD COLUMN ... GENERATED ... STORED` rewrites the whole table** under an
  `ACCESS EXCLUSIVE` lock, because every existing row needs the value computed. On a
  big live table, that's an outage — use level 12's expand/contract approach instead
  (add a plain nullable column, backfill in batches, keep it in sync with a trigger,
  then swap).

### Fixing the estimates without a column: expression statistics

If you can't add a column, Postgres 14+ can collect statistics on an expression
directly:

```sql
EXPLAIN SELECT * FROM catalog WHERE attrs ->> 'color' = 'red';
--  Gather ... rows=1500               (default guess: 0.5% of the table)

CREATE STATISTICS catalog_color_stats ON (attrs ->> 'color') FROM catalog;
ANALYZE catalog;

EXPLAIN SELECT * FROM catalog WHERE attrs ->> 'color' = 'red';
--  Seq Scan on catalog ... rows=37860  (actual count: 37500)
```

A 25x underestimate became a 1% error. (An expression *index* also makes `ANALYZE`
gather statistics for its expression, so `catalog_sku` above had this as a side effect.)

## The hidden cost: a JSONB update rewrites the whole document

MVCC (level 09) writes a whole new row version on every `UPDATE`, and a `jsonb` value
is one atomic column: there's no in-place "change one key". Big documents (roughly
2 KB+ after compression) are moved out of line into the table's **TOAST** storage, and
changing *any* key means writing a new copy of the entire TOASTed value. Measured on
one row with a ~530 KB JSON document (≈ 233 KB stored after compression), incrementing
a counter two ways and reading the WAL generated with `pg_current_wal_lsn()`:

```sql
DROP TABLE IF EXISTS profiles;
CREATE TABLE profiles (id INT PRIMARY KEY, login_count INT NOT NULL DEFAULT 0, doc JSONB NOT NULL);
INSERT INTO profiles (id, doc)
SELECT 1, jsonb_build_object('login_count', 0, 'history',
         (SELECT jsonb_agg(jsonb_build_object('ts', now() - g * interval '1 minute',
                                              'ip', '10.0.' || (g % 255) || '.' || (g*7 % 255),
                                              'agent', md5(g::text)))
          FROM generate_series(1, 5000) g));

-- in psql: \gset stores a query's result in a variable
SELECT pg_current_wal_lsn() AS l0 \gset
UPDATE profiles SET login_count = login_count + 1 WHERE id = 1;
SELECT pg_current_wal_lsn() AS l1 \gset
UPDATE profiles SET doc = jsonb_set(doc, '{login_count}', to_jsonb((doc->>'login_count')::int + 1))
WHERE id = 1;
SELECT pg_current_wal_lsn() AS l2 \gset
SELECT pg_size_pretty(pg_wal_lsn_diff(:'l1', :'l0')) AS wal_plain_column,
       pg_size_pretty(pg_wal_lsn_diff(:'l2', :'l1')) AS wal_jsonb_key;
```

```text
 wal_plain_column | wal_jsonb_key
------------------+---------------
 168 bytes        | 256 kB
```

The same logical change — add 1 to a counter — cost **~1,500x more WAL** when the
counter lived inside a large document (repeatable run to run; the first run right
after a `CHECKPOINT` was higher still, ~500 kB, because of full-page images). That
WAL is also what replicas (level 17) must ship and replay, and the old 256 kB version
becomes dead space for vacuum. **Rule: frequently-updated fields don't belong inside
large JSON documents.** Keep documents small, or keep hot counters and statuses in
columns.

## When to use JSONB, and when to use columns

| Use a **column** when the field… | **JSONB** is reasonable when the data… |
|---|---|
| Is present on (nearly) every row | Is sparse — most keys are absent on most rows |
| Is joined on, or referenced by a foreign key | Is never joined on |
| Needs a type, `NOT NULL`, `UNIQUE`, `FK` enforced | Has a shape you don't control (third-party payload, raw event) |
| Is filtered/sorted/aggregated routinely (needs accurate statistics) | Is mostly written and read back whole, filtered by a few containment predicates |
| Is updated frequently | Is updated rarely, or is small |
| Has a stable, known set of values | Genuinely varies per row (per-category attributes, per-tenant custom fields) |

The pattern that holds up in production is **hybrid**: stable, queried fields as
columns; a `JSONB` column for the variable tail; and when a key inside the JSON turns
out to be hot, promote it (generated column, or a real column plus a backfill). The
anti-pattern is a table that's `id` + `data JSONB` with everything inside —
that throws away types, constraints, foreign keys, statistics and cheap updates to
avoid writing migrations, and the migrations come back as application code that has to
handle every historical document shape.

## Common mistakes

- **Using `json` instead of `jsonb`.** No containment operators, no GIN index,
  re-parsed on every access. Default to `jsonb`.
- **Comparing `->>` output as if it were a number or boolean.** It's `text`; cast it
  (`(attrs->>'price')::numeric`) or you get string comparison, silently.
- **Filtering with `attrs->>'k' = 'v'` and expecting the GIN index to help.** It can't;
  use `attrs @> '{"k": "v"}'` or an expression index.
- **Creating `jsonb_path_ops` and then querying with `?`.** The planner quietly falls
  back to a sequential scan. Choose the operator class for the operators you run.
- **Confusing JSON `null` with SQL `NULL`.** A key holding `null` is present; `->>`
  hides the difference, `?` and `->` don't.
- **Putting hot, frequently-updated fields inside big documents.** Each update rewrites
  the whole TOASTed value — measured above at ~1,500x the WAL of a plain column.
- **Relying on key order or duplicate keys in `jsonb`.** Both are normalized away on
  write.
- **Using JSONB to dodge schema design.** It moves the schema into every piece of
  code that reads the column, without the database enforcing any of it.

## Interview questions

**"`json` or `jsonb`?"** `jsonb` almost always: parsed once on write, supports
containment/existence operators and GIN indexing. `json` keeps the exact input text
(whitespace, key order, duplicate keys), which matters only if you need the original
bytes back.

**"How do you index a JSONB column?"** Depends on the query. Containment (`@>`) across
arbitrary keys → GIN with `jsonb_path_ops` (smaller, more selective); if you also need
key existence (`?`, `?|`, `?&`) → GIN with the default `jsonb_ops`. One key used for
equality, ranges or sorting → a B-tree expression index on `(attrs->>'k')`, or better,
a generated column with a normal index. Then verify with `EXPLAIN ANALYZE`, because
the wrong operator silently gets a sequential scan.

**"Why is the planner's row estimate wrong on my JSONB query?"** Postgres keeps no
statistics on keys inside a `jsonb` value, so it uses fixed default selectivities. Fix
with a generated column (real statistics), an expression index, or
`CREATE STATISTICS ... ON (expr)` (Postgres 14+).

**"When would you choose JSONB over normalized columns?"** For sparse, variable or
externally-defined attributes that aren't joined on or constrained — and with the
known costs named: no FKs, weaker statistics, whole-document rewrite on update. Keep
the hot and relational fields as columns (hybrid model), and promote JSON keys to
columns once they become hot.

**"Postgres JSONB vs MongoDB?"** JSONB gives document flexibility inside a
transactional relational database — joins, FKs to the relational parts, one backup,
one consistency model. A document database is built for documents from the ground up
(update operators like `$set`/`$inc` that change one field and replicate only that
change through the oplog, native sharding by document key, a document-shaped query
language). If most of your data is relational with some flexible attributes, JSONB;
if the whole domain is documents and you need horizontal write scaling, see
[Choosing a Database, and CAP Theorem Applied](../NoSQL/concepts/01_choosing_a_database_and_cap_theorem.md).

## What's next

Level 21 turns from writing good queries to finding the bad ones: how to discover which
queries are slow in a running production database, before you can `EXPLAIN` anything.
