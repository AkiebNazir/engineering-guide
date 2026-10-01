# Data Modeling: Star Schema & SCDs

When data lands in the warehouse it cannot stay in its OLTP shape (third normal form,
current state only). Analysts and BI tools need tables they can query without
15-way joins, and questions about the past need the past to still be there. This
chapter teaches dimensional modeling from zero: facts and dimensions, choosing the
grain, the kinds of fact and dimension tables, slowly changing dimensions with a
runnable SCD Type 2 example, surrogate keys, late-arriving data, and the
alternatives (Data Vault, one big table) you will be asked to compare.

## Foundations — What shape should analytical data have?

### The problem

An online shop's Postgres database is designed for the app: `orders`, `order_items`,
`customers`, `addresses`, `products`, `categories`, `promotions`, each normalised so
every fact is stored once. To answer *"revenue by product category by customer city by
month"* against that schema you join six or seven tables, remember which address was
the shipping one, and get the wrong answer anyway, because when a customer moved last
year the app overwrote their city and all their old orders now look like they shipped
to the new city.

Analytical modeling fixes three things:

1. **Ease of querying.** Few, predictable joins; human-readable column names; one
   obvious table per question.
2. **Performance.** Columnar warehouses scan and aggregate fast but pay for big
   shuffling joins, so a model with one large table and small lookups suits them.
3. **History.** Keep what was true at the time, not just what is true now.

### The two kinds of table

Ralph Kimball's **dimensional modeling** (from *The Data Warehouse Toolkit*) splits
every business process into:

- **Fact tables**: one row per measurement event. *Something happened, and here are
  its numbers.* A sale, a page view, a payment, a shipment. They are long (billions of
  rows) and narrow: foreign keys to dimensions plus numeric **measures**
  (`quantity`, `revenue_amount`, `discount_amount`).
- **Dimension tables**: the context around the event. *Who, what, where, when, how.*
  The customer, the product, the store, the date. They are short (thousands to
  millions of rows) and wide: many descriptive text columns (`product_name`,
  `category`, `brand`, `customer_city`, `loyalty_tier`) that people filter and group
  by.

An everyday example: a supermarket receipt. Each line on the receipt is a fact row
(product, quantity, price paid). Everything printed at the top (store address, date,
cashier) and everything you could look up about the product (brand, aisle,
category) is dimension data.

### The star schema

Put the fact table in the middle, point it at each dimension, and you get a picture
that looks like a star:

```arch
%% caption: In a star schema a central fact table holds the measures and foreign keys; each surrounding dimension table holds descriptive attributes. Every analytical query is the fact table joined to a few dimensions.
route straight
grid 170x110
node user "dim_customer" at 0,0 icon=user sub="city, segment, tier"
node prod "dim_product" at 2,0 icon=package sub="name, brand, category"
node fact "fact_sales" at 1,1 icon=table sub="qty, revenue, discount"
node store "dim_store" at 0,2 icon=store sub="region, format"
node date "dim_date" at 2,2 icon=time sub="day, week, fiscal qtr"
fact -> user
fact -> prod
fact -> store
fact -> date
```

A typical query then reads like the question:

```sql
SELECT d.year_month, p.category, c.city, SUM(f.revenue_amount) AS revenue
FROM fact_sales f
JOIN dim_date     d ON d.date_sk     = f.date_sk
JOIN dim_product  p ON p.product_sk  = f.product_sk
JOIN dim_customer c ON c.customer_sk = f.customer_sk
WHERE d.year = 2026
GROUP BY 1, 2, 3;
```

### Vocabulary

| Term | Meaning |
|---|---|
| Grain | Exactly what one row of a fact table represents ("one row per order line") |
| Measure | A numeric fact you aggregate (revenue, quantity, duration) |
| Natural key | The identifier from the source system (`customer_id = 42`) |
| Surrogate key | A warehouse-generated key for one *version* of a dimension row (`customer_sk = 101`) |
| Conformed dimension | A dimension shared, with identical meaning, by many fact tables |
| SCD | Slowly changing dimension: the policy for what happens when an attribute changes |
| Degenerate dimension | A dimension value stored on the fact with no table of its own (order number) |

## 1. The four-step design process

Kimball's process, which is still the right interview answer:

1. **Pick the business process.** Not a department or a report: an activity that
   produces measurements. "Customers place orders", "warehouse ships orders",
   "users view pages".
2. **Declare the grain.** State in one sentence what one fact row is: *one row per
   order line item*. This is the most important decision in the model; everything else
   must agree with it. Choose the **most atomic grain** available, because you can
   always aggregate up, never down.
3. **Identify the dimensions.** Whatever is true about that row: date, customer,
   product, store, promotion, payment method.
4. **Identify the facts (measures).** Numbers true at that grain: quantity, unit
   price, extended amount, discount.

Worked example for an online shop:

| Step | Decision |
|---|---|
| Process | Order placement |
| Grain | One row per order line (order 812, line 3) |
| Dimensions | `dim_date` (order date), `dim_customer`, `dim_product`, `dim_promotion`, `dim_channel`; `order_number` as a degenerate dimension |
| Facts | `quantity`, `unit_price`, `gross_amount`, `discount_amount`, `net_amount` |

```sql
CREATE TABLE fact_order_line (
  order_date_sk     INTEGER       NOT NULL,   -- FK to dim_date, e.g. 20260927
  customer_sk       BIGINT        NOT NULL,   -- FK to the customer version at order time
  product_sk        BIGINT        NOT NULL,
  promotion_sk      BIGINT        NOT NULL,   -- -1 = "no promotion", never NULL
  channel_sk        INTEGER       NOT NULL,
  order_number      VARCHAR(20)   NOT NULL,   -- degenerate dimension
  line_number       SMALLINT      NOT NULL,
  quantity          INTEGER       NOT NULL,
  unit_price        DECIMAL(12,2) NOT NULL,
  gross_amount      DECIMAL(12,2) NOT NULL,
  discount_amount   DECIMAL(12,2) NOT NULL,
  net_amount        DECIMAL(12,2) NOT NULL
);
```

**The grain mistake that breaks totals.** Mixing grains in one table (an
`order_shipping_cost` stored on every line of the order) makes `SUM(shipping_cost)`
count the order's shipping once per line. Either allocate it down to line grain
(split it across lines) or keep it in a separate order-grain fact table.

## 2. Kinds of fact table

| Type | One row per | Example | Updated? |
|---|---|---|---|
| **Transaction** | Event at the atomic grain | Each order line, each click | Insert only |
| **Periodic snapshot** | Entity per period | Account balance per day, inventory per store per week | Insert a new period each run |
| **Accumulating snapshot** | Instance of a process with milestones | One row per order with `ordered_date_sk`, `shipped_date_sk`, `delivered_date_sk` and lag measures | Updated as milestones happen |
| **Factless** | Event with no measure, or coverage | Student attended class; product was on promotion in a store | Insert only; you `COUNT(*)` |

### Additivity

| Measure type | Can you `SUM` it across...? | Example |
|---|---|---|
| Additive | Every dimension | Revenue, quantity |
| Semi-additive | Some dimensions, not time | Account balance: sum across accounts, but average or take the last value across days |
| Non-additive | Nothing | Ratios, percentages, unit price: store the numerator and denominator, compute the ratio after summing |

A classic interview trap: "average order value" stored per row and then averaged
gives the average of averages. Store `net_amount` and count orders; compute
`SUM(net_amount) / COUNT(DISTINCT order_number)`.

## 3. Kinds of dimension

- **Date dimension.** One row per calendar day with every attribute analysts use:
  day of week, ISO week, month name, fiscal quarter, holiday flags. Joining to it
  beats re-deriving fiscal calendars in every query. The key is often a smart integer
  like `20260927`.
- **Conformed dimensions.** `dim_customer` and `dim_product` mean the same thing in
  `fact_order_line`, `fact_returns` and `fact_web_sessions`, so you can "drill across"
  processes (orders vs. returns by product). The matrix of processes vs. shared
  dimensions is Kimball's **bus matrix**, the backbone of an enterprise warehouse.
- **Role-playing dimensions.** One physical `dim_date` used several times with
  different meanings: order date, ship date, delivery date (as views or aliases).
- **Degenerate dimensions.** Order number, invoice number: useful for grouping, no
  other attributes, stored on the fact.
- **Junk dimensions.** A handful of low-cardinality flags (`is_gift`, `payment_type`,
  `is_first_order`) combined into one small table instead of cluttering the fact.
- **Bridge tables.** For many-to-many: an order with several promotions, a patient
  with several diagnoses. A bridge (`order_sk`, `promotion_sk`, `weight`) sits between
  fact and dimension; weights stop double-counting when totals are split.
- **Unknown and not-applicable members.** Reserve keys like `-1 = Unknown` and
  `-2 = Not applicable` so fact foreign keys are never `NULL` and inner joins never
  silently drop rows.

## 4. Star vs. snowflake

A **snowflake schema** normalises dimensions: `dim_product` points to `dim_category`,
which points to `dim_department`.

| | Star | Snowflake |
|---|---|---|
| Dimension shape | Flat, denormalised (`category` is a column on `dim_product`) | Normalised into sub-tables |
| Joins per query | Fewer | More |
| Storage | Repeats category names (cheap in columnar storage) | Stores each once |
| Usability for analysts and BI | Better | Worse |
| When it helps | Default | A very large dimension with a big, independently maintained sub-part |

In columnar warehouses the storage saving from snowflaking is tiny (repeated strings
compress to almost nothing, as the
[column-store demo in chapter 1](01_oltp_vs_olap.md) shows), so **star is the
default**.

## 5. Slowly changing dimensions (SCD)

A customer moves from New York to London. If you simply `UPDATE dim_customer`, every
sale they made last year now reports as a London sale. Revenue by city for 2025 changes
after the fact, and nobody can reproduce last quarter's board report.

**Slowly changing dimension** types are the menu of policies for this:

| Type | What happens on change | History | Use when |
|---|---|---|---|
| 0 | Never change (retain original) | Original value only | Attributes that must not change: original signup channel, date of birth |
| 1 | Overwrite in place | None | Corrections (typos), attributes whose history nobody needs (phone number) |
| 2 | Expire the current row, insert a new version | Full | You must report facts against the attribute value *at the time* (city, segment, sales territory, price tier) |
| 3 | Add a `previous_city` column | One previous value | Rarely; "compare to before the reorganisation" |
| 4 | Keep current values in the dimension, history in a separate history table | Full, separate | Rapidly changing attributes that would bloat Type 2 |
| 6 (1+2+3) | Type 2 rows plus a `current_city` column overwritten on every version | Full, plus "as of now" | Report both "city at time of sale" and "customer's city today" without a self-join |

Types 1 and 2 cover almost every real case. A single dimension usually mixes them:
Type 2 for `city` and `segment`, Type 1 for `email` and `phone`.

### SCD Type 2, precisely

Each version of a customer is its own row with its own **surrogate key** and a
validity interval:

| customer_sk | customer_id | city | valid_from | valid_to | is_current |
|---|---|---|---|---|---|
| 101 | 42 | New York | 2024-01-01 | 2025-01-01 | false |
| 102 | 42 | London | 2025-01-01 | 9999-12-31 | true |

- Use **half-open intervals**, `valid_from <= t < valid_to`, with the old row's
  `valid_to` equal to the new row's `valid_from`. Closing the old row "the day before"
  (`2024-12-31`) leaves a gap for timestamps during that last day, and inclusive
  intervals at both ends create overlaps.
- A far-future sentinel (`9999-12-31`) for the open row keeps `BETWEEN`-style filters
  simple; some teams use `NULL` and `COALESCE`.
- **Facts store the surrogate key of the version valid when the event happened**
  (`customer_sk = 101` for sales in 2024, `102` after). Grouping by `city` then gives
  the city at the time of sale with a plain equi-join.
- Invariant to test: for each `customer_id`, exactly one current row and no
  overlapping intervals.

Runnable end-to-end with SQLite (standard library only):

```python
import sqlite3

db = sqlite3.connect(":memory:")
db.executescript("""
CREATE TABLE dim_customer (
    customer_sk   INTEGER PRIMARY KEY,          -- surrogate key
    customer_id   INTEGER NOT NULL,             -- natural (business) key
    city          TEXT    NOT NULL,
    valid_from    TEXT    NOT NULL,
    valid_to      TEXT    NOT NULL DEFAULT '9999-12-31',
    is_current    INTEGER NOT NULL DEFAULT 1
);
-- At most one current row per customer.
CREATE UNIQUE INDEX one_current ON dim_customer(customer_id) WHERE is_current = 1;
CREATE TABLE fact_sales (sale_date TEXT, customer_sk INTEGER, amount REAL);
""")

def apply_snapshot(snapshot, as_of):
    """SCD Type 2: close rows whose tracked attribute changed, insert new versions."""
    with db:  # one transaction: readers never see a customer with 0 or 2 current rows
        for customer_id, city in snapshot:
            cur = db.execute(
                "SELECT customer_sk, city FROM dim_customer WHERE customer_id=? AND is_current=1",
                (customer_id,)).fetchone()
            if cur and cur[1] == city:
                continue                                   # unchanged: do nothing
            if cur:                                        # changed: expire old version
                db.execute("UPDATE dim_customer SET valid_to=?, is_current=0 WHERE customer_sk=?",
                           (as_of, cur[0]))
            db.execute("INSERT INTO dim_customer (customer_id, city, valid_from) VALUES (?,?,?)",
                       (customer_id, city, as_of))

def record_sale(sale_date, customer_id, amount):
    """Facts point at the dimension version that was valid when the sale happened."""
    sk = db.execute("""SELECT customer_sk FROM dim_customer
                       WHERE customer_id=? AND valid_from <= ? AND ? < valid_to""",
                    (customer_id, sale_date, sale_date)).fetchone()[0]
    db.execute("INSERT INTO fact_sales VALUES (?,?,?)", (sale_date, sk, amount))

apply_snapshot([(42, "New York"), (7, "Paris")], "2024-01-01")
record_sale("2024-06-10", 42, 120.0)
apply_snapshot([(42, "London"), (7, "Paris")], "2025-01-01")   # customer 42 moved
record_sale("2025-03-02", 42, 80.0)

for row in db.execute("SELECT * FROM dim_customer ORDER BY customer_id, valid_from"):
    print(row)
print("revenue by city at time of sale:")
for row in db.execute("""SELECT d.city, SUM(f.amount) FROM fact_sales f
                         JOIN dim_customer d USING (customer_sk) GROUP BY d.city ORDER BY d.city"""):
    print("  ", row)
```

```text
(2, 7, 'Paris', '2024-01-01', '9999-12-31', 1)
(1, 42, 'New York', '2024-01-01', '2025-01-01', 0)
(3, 42, 'London', '2025-01-01', '9999-12-31', 1)
revenue by city at time of sale:
   ('London', 80.0)
   ('New York', 120.0)
```

The 2024 sale stays in New York after the move. With Type 1 both sales would report
as London.

### SCD Type 2 as one set-based `MERGE`

In a warehouse you do not loop in Python; you run one statement per load. The standard
trick feeds each changed customer into `MERGE` twice: once with its key (to match and
expire the current row) and once with a `NULL` key (which never matches, so it is
inserted as the new version).

```sql
-- Snowflake / Databricks SQL. stg_customers holds today's extract.
MERGE INTO dim_customer AS t
USING (
  SELECT s.customer_id AS merge_key, s.*
  FROM stg_customers s
  UNION ALL
  SELECT NULL AS merge_key, s.*                -- second copy: becomes the new version
  FROM stg_customers s
  JOIN dim_customer d
    ON d.customer_id = s.customer_id AND d.is_current
  WHERE d.city IS DISTINCT FROM s.city         -- NULL-safe "changed"
) AS src
ON t.customer_id = src.merge_key AND t.is_current
WHEN MATCHED AND t.city IS DISTINCT FROM src.city THEN
  UPDATE SET is_current = FALSE, valid_to = src.extracted_at
WHEN NOT MATCHED THEN
  INSERT (customer_sk, customer_id, city, valid_from, valid_to, is_current)
  VALUES (MD5(src.customer_id || '|' || src.extracted_at),
          src.customer_id, src.city, src.extracted_at, '9999-12-31', TRUE);
```

Brand-new customers come through the first branch with a key that matches nothing, so
they are inserted too. In practice most teams let **dbt snapshots** generate this
logic ([chapter 6](06_data_transformation_dbt.md)), or build Type 2 history from a CDC
change log ([chapter 1](01_oltp_vs_olap.md)), where every change already carries its
commit time.

### Point-in-time joins without surrogate keys

When facts carry only the natural key (common in ELT, where facts and dimensions load
independently), join on the interval at query time:

```sql
SELECT f.order_id, f.net_amount, c.city
FROM fact_order f
JOIN dim_customer c
  ON  c.customer_id = f.customer_id
  AND f.ordered_at >= c.valid_from
  AND f.ordered_at <  c.valid_to;
```

This is also exactly how ML feature stores build training sets without leaking future
values ([Feature Stores and Data Leakage](../MLOps/02_feature_stores.md)).

## 6. Surrogate keys

Why the warehouse makes its own keys instead of reusing `customer_id`:

1. **Type 2 needs one key per version.** `customer_id = 42` now appears twice.
2. **Sources collide.** Customer 42 in the web shop and customer 42 in the acquired
   company's CRM are different people.
3. **Sources change.** A source system re-keys or is replaced; the warehouse keys stay.
4. **Special members.** `-1 = Unknown` has no natural key.

| Surrogate key style | How | Pros | Cons |
|---|---|---|---|
| Sequence / identity integer | `IDENTITY`, `AUTOINCREMENT`, sequences | Small, fast joins | Needs a lookup at load time to find the key; order-dependent, so reloads can renumber |
| Hash key | `MD5(source || '|' || natural_key || '|' || valid_from)` | Deterministic: same input gives the same key in any environment, parallel loads need no lookup | 16–32 bytes; collisions are astronomically unlikely but not impossible |

Modern ELT stacks (dbt's `generate_surrogate_key` macro, Data Vault) lean towards hash
keys because they make loads idempotent and parallel.

## 7. Late-arriving data

- **Late-arriving facts.** An order from three days ago arrives today (a mobile client
  was offline). Look up the dimension version valid at the *event* time, not the load
  time, and write it into the correct date partition. Aggregates for that day must be
  recomputed, which is why incremental models reprocess a lookback window.
- **Early-arriving facts / late-arriving dimensions.** A sale references
  `customer_id = 9001`, but the customer row has not arrived yet. Options: insert an
  **inferred member** (a placeholder dimension row with the natural key and
  "Unknown" attributes, flagged `is_inferred`) and update it in place when the real
  row arrives; or point the fact at `-1 Unknown` and re-key it later. Never drop the
  fact.

## 8. Other modeling approaches

| Approach | Core idea | Strength | Weakness | Typical use |
|---|---|---|---|---|
| **Kimball dimensional** | Star schemas per business process, conformed dimensions | Easy to query, fast in BI | Rework when sources change a lot | Marts, the presentation layer |
| **Inmon (CIF)** | A normalised (3NF) enterprise warehouse first, marts derived from it | Single integrated truth | Slow to build; heavy up-front design | Large enterprises, regulated industries |
| **Data Vault 2.0** | Hubs (business keys), links (relationships), satellites (attributes over time), insert-only | Auditable, absorbs new sources and changes without rework, parallel loads | Many joins; needs a star layer on top for users | Integration layer with many changing sources |
| **One Big Table (OBT)** | Pre-join everything into one very wide table | Simplest possible queries, fast in columnar engines | Duplicated logic across OBTs, painful Type 2 history, huge rebuilds | Specific dashboards, real-time OLAP (ClickHouse, Pinot) |
| **Activity schema** | One narrow stream of `(entity, activity, ts, features)` | Very flexible for customer-journey questions | Unfamiliar; needs tooling | Product analytics |

```arch
%% caption: Data Vault separates keys, relationships and changing attributes. Hubs hold business keys, links join hubs, satellites hold attribute history; everything is insert-only.
grid 170x105
node hc "hub_customer" at 0,0 icon=id color=blue sub="customer_hk, customer_id"
node lo "link_order" at 1,0 icon=link color=purple sub="order_hk, customer_hk, product_hk"
node hp "hub_product" at 2,0 icon=id color=blue sub="product_hk, sku"
node sc "sat_customer" at 0,1 icon=time color=green sub="city, tier, load_ts"
node so "sat_order" at 1,1 icon=time color=green sub="status, amount, load_ts"
node sp "sat_product" at 2,1 icon=time color=green sub="name, price, load_ts"
lo -> hc
lo -> hp
sc -> hc
so -> lo
sp -> hp
```

The common 2026 layering combines them: raw (bronze) → cleaned staging (silver) →
optionally a vault or normalised integration layer → **Kimball stars or wide tables
for consumers** (gold).

### Modeling for columnar engines

- Denormalising is cheaper than it was on row stores: repeated strings compress well,
  and joins to small dimensions become broadcast joins.
- **Nested and repeated fields** (BigQuery `ARRAY<STRUCT<...>>`, Parquet lists and
  structs) can store an order and its lines in one row, avoiding a join for
  order-level questions. Querying lines then needs `UNNEST`.
- Very large dimension-to-fact joins still shuffle; if a dimension is huge (hundreds
  of millions of users), consider storing the needed attributes on the fact.
- A **semantic layer** (dbt Semantic Layer / MetricFlow, LookML, Cube) defines
  measures, dimensions and joins once, so "revenue" means the same thing in every
  dashboard. It sits on top of the star schema, it does not replace it.

## 9. Modeling failure modes seen in production

| Symptom | Root cause | Fix |
|---|---|---|
| Revenue is higher than finance's number | Fan-out: joined a fact to a table at a finer grain (order → order lines) before summing an order-level measure | Aggregate to the right grain first, or allocate the measure down |
| Numbers for last year changed | Type 1 overwrite of an attribute used for grouping | Type 2 for reported attributes |
| Rows disappear in some reports | Fact FKs are `NULL`, inner join drops them | Unknown member `-1`; not-null tests |
| Customer has two current rows | Non-atomic Type 2 load, or duplicate extract rows | One transaction/`MERGE`; dedupe staging; uniqueness test on `(customer_id) WHERE is_current` |
| Dashboards slow and expensive | Snowflaked dimensions, or `SELECT *` on wide facts | Star schema, projected columns, partition/cluster on date |
| "Active users" differs by team | Metric defined in each dashboard | Semantic layer or one certified metrics model |

## Common interview questions

**What is the grain of a fact table and why declare it first?**
The exact meaning of one row. Every dimension and measure must be true at that grain;
choosing it first prevents mixed-grain tables that double-count. Choose the most
atomic grain available so any aggregation is possible later.

**Facts vs. dimensions?**
Facts are events with numeric measures, long and narrow, mostly inserted. Dimensions
are descriptive context (who, what, where, when), short and wide, used to filter and
group.

**Explain SCD Type 1 vs. Type 2. When would you use each?**
Type 1 overwrites and loses history, for corrections and attributes nobody reports
historically. Type 2 expires the current row and inserts a new version with its own
surrogate key and a validity interval, so facts keep pointing at the version true at
event time. Use Type 2 for attributes that group reported numbers (city, segment,
territory).

**Why surrogate keys?**
Type 2 needs a key per version, sources collide and change, and special members
(`Unknown`) need keys. Hash keys make loads deterministic and parallel.

**Star vs. snowflake in a columnar warehouse?**
Star by default: fewer joins, simpler for analysts and BI, and the storage saved by
snowflaking is negligible after columnar compression.

**How do you handle a fact that arrives before its dimension row?**
Insert an inferred member with the natural key and placeholder attributes, link the
fact to it, and update it in place when the real row arrives. Never drop the fact.

**How would you model order fulfilment (ordered, packed, shipped, delivered)?**
An accumulating snapshot: one row per order, one date key per milestone, lag measures
(days from order to ship), updated as milestones happen. Keep a transaction fact of
status events alongside it if you need every transition.

**Kimball vs. Data Vault vs. one big table?**
Kimball for consumption (easy, fast). Data Vault for integrating many changing sources
with full auditability, insert-only, then stars on top. One big table for a specific
high-traffic dashboard or real-time OLAP, accepting duplicated logic.

**How do you compute a ratio correctly across groups?**
Store additive numerator and denominator, sum both, divide at the end. Never average
per-row ratios.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student / Intern | Intern, new learner | — | Facts vs. dimensions; draws a star schema for a simple business; knows why history matters |
| Junior | Data Engineer I / Analytics Engineer | L3 | Declares grain; writes star-schema queries; knows SCD 1 vs. 2; uses surrogate keys and unknown members; spots a fan-out join |
| Mid | Data Engineer II | L4 | Designs a mart end to end (bus matrix, conformed dimensions, fact types, additivity); implements Type 2 with `MERGE` or dbt snapshots; handles late-arriving facts and inferred members |
| Senior | Senior Data / Analytics Engineer | L5 | Chooses Kimball, vault or wide tables per layer with reasons; models for columnar engines (nesting, denormalisation, partitioning); writes invariant tests (one current row, no overlaps); owns metric definitions in a semantic layer |
| Staff+ | Staff Data Engineer, Data Architect | L6+ | Sets company-wide modeling standards and conformed dimensions across domains; designs data contracts with producing teams; balances self-serve flexibility against governed, certified metrics |

## Interview checklist

- [ ] I can run the four-step design (process, grain, dimensions, facts) on a new business in five minutes.
- [ ] I can name the four fact table types and give an example of each.
- [ ] I can explain additive, semi-additive and non-additive measures and compute a ratio correctly.
- [ ] I can explain conformed, role-playing, degenerate and junk dimensions and bridge tables.
- [ ] I can compare star and snowflake schemas for a columnar warehouse.
- [ ] I can list SCD types 0–4 and 6 and implement Type 2 with half-open intervals.
- [ ] I can write a set-based SCD2 `MERGE` or explain dbt snapshots.
- [ ] I can justify surrogate keys and choose sequence vs. hash keys.
- [ ] I can handle late-arriving facts and early-arriving facts (inferred members).
- [ ] I can compare Kimball, Inmon, Data Vault and one-big-table.

Related: [Normalization and Denormalization](../SQL/16_normalization_and_denormalization.md),
[Joins](../SQL/06_joins.md),
[Aggregation and Grouping](../SQL/07_aggregation_and_grouping.md),
[Embedding vs. Referencing](../NoSQL/mongodb/04_embedding_vs_referencing.md)
(the same embed-vs-join trade-off in a document store),
[Wide-Column and DynamoDB-Style Databases](../NoSQL/concepts/00_wide_column_and_dynamodb_style_databases.md).
