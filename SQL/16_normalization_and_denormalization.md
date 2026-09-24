# Normalization and Denormalization

**Already covered elsewhere:** `SoftwareDesign/09_data_design_and_schema_evolution.md`
covers schema evolution over time (expand/contract migrations). This level is about a
different question — *given a snapshot of requirements, how many tables should this
data live in, and why* — which normal forms answer precisely, not just by taste.

## The mental model

**Normalization** is the process of structuring tables so that each fact is stored in
exactly one place, driven by **functional dependencies** — "column B's value is fully
determined by column A's value" (`email → city` means: knowing the email tells you the
city, unambiguously). A table that stores a fact in more than one row invites the three
classic anomalies below the moment two copies of that fact can drift apart.
**Denormalization** is the deliberate, informed reversal of some of that — duplicating
data on purpose, later, for a read-performance reason you can name.

This is one of the few interview questions that rewards a *precise* answer over a vague
one. "Normalize your database" is not a complete answer; "up to 3NF/BCNF for anything
transactional, then denormalize specific hot read paths with a name for the tradeoff"
is.

## The three normal forms, briefly, then proven wrong when skipped

| Form | Rule | What it rules out |
|---|---|---|
| **1NF** | Every column holds a single, atomic value — no repeating groups, no comma-separated lists in a cell | `products TEXT` holding `"Keyboard,Mouse"` in one row |
| **2NF** | 1NF, and every non-key column depends on the **whole** primary key, not part of it | In a table keyed on `(order_id, product_id)`, a `customer_email` column that only depends on `order_id` violates 2NF |
| **3NF** | 2NF, and every non-key column depends on the key **directly**, not transitively through another non-key column | `customer_city` depending on `customer_email`, which depends on `order_id` — city is two hops from the key |
| **BCNF** | 3NF, and every determinant (left side of a functional dependency) is a candidate key | Rare in practice for the tables you'll design day to day; interviewers mostly want you fluent through 3NF |

## Demo: the three anomalies, live, in a single denormalized table

A single flattened `orders_denorm` table — the shape a junior schema often starts
with, storing the customer's and product's facts directly on every order row:

```sql
DROP TABLE IF EXISTS orders_denorm;
CREATE TABLE orders_denorm (
    order_id       INT PRIMARY KEY,
    customer_name  TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_city  TEXT NOT NULL,
    product_name   TEXT NOT NULL,
    product_price  NUMERIC NOT NULL,
    qty            INT NOT NULL
);

INSERT INTO orders_denorm VALUES
  (1, 'Amara Okafor', 'amara@example.com', 'Lagos',  'Keyboard', 49.99, 1),
  (2, 'Amara Okafor', 'amara@example.com', 'Lagos',  'Mouse',    19.99, 2),
  (3, 'Diego Ramos',  'diego@example.com', 'Madrid', 'Monitor', 199.99, 1);
```

Amara's `customer_name`/`customer_email`/`customer_city` are functionally determined
by *her*, not by the order — they're duplicated across her two rows. That duplication
is the root cause of all three anomalies below.

**1. Update anomaly.** Amara moves to Abuja. Someone updates order 1's city but misses
order 2 (an entirely realistic outcome — nothing in the schema says these two rows must
change together):

```sql
UPDATE orders_denorm SET customer_city = 'Abuja' WHERE order_id = 1;
SELECT order_id, customer_name, customer_city FROM orders_denorm ORDER BY order_id;
```

Real output:

```text
 order_id | customer_name | customer_city
----------+---------------+---------------
        1 | Amara Okafor  | Abuja
        2 | Amara Okafor  | Lagos
        3 | Diego Ramos   | Madrid
```

One customer, two different cities, in the same table, right now. There is no query
that can tell you which one is true — the schema itself has no concept of "Amara's
city" as a single fact.

**Go (native `pgxpool`):** the same update, same query, via `github.com/jackc/pgx/v5/pgxpool`:

```go
pool, err := pgxpool.New(ctx, "postgresql://dsa:dsa@localhost:5544/dsa")
// ... (error handling omitted for brevity, see levels 01/13 for the full pattern)

pool.Exec(ctx, `UPDATE orders_denorm SET customer_city = 'Abuja' WHERE order_id = 1`)

rows, _ := pool.Query(ctx, `SELECT order_id, customer_name, customer_city FROM orders_denorm ORDER BY order_id`)
for rows.Next() {
    var id int
    var name, city string
    rows.Scan(&id, &name, &city)
    fmt.Printf("order_id=%d customer_name=%s customer_city=%s\n", id, name, city)
}
```

Real output — identical inconsistency, reached from Go instead of `psql`:

```text
order_id=1 customer_name=Amara Okafor customer_city=Abuja
order_id=2 customer_name=Amara Okafor customer_city=Lagos
order_id=3 customer_name=Diego Ramos customer_city=Madrid
```

The anomaly isn't a Python or Go artifact of either client library — it's a property
of the *schema*, which is the whole point: no client language can query its way out of
data that was never associated in the first place.

**2. Deletion anomaly.** Diego has exactly one order. Delete it — meaning to delete
*that order* — and every fact about Diego as a customer (his name, his email) is gone
too, because nothing else in the table remembers him:

```sql
DELETE FROM orders_denorm WHERE order_id = 3;
SELECT * FROM orders_denorm;
```

```text
 order_id | customer_name | customer_email     | customer_city | product_name | product_price | qty
----------+---------------+--------------------+---------------+--------------+---------------+-----
        1 | Amara Okafor  | amara@example.com  | Abuja         | Keyboard     |         49.99 |   1
        2 | Amara Okafor  | amara@example.com  | Lagos         | Mouse        |         19.99 |   2
```

Diego no longer exists anywhere in the database. "Delete an order" and "forget a
customer ever existed" were two different intents that this schema cannot separate.

**3. Insertion anomaly.** You cannot record a new customer, Priya, who hasn't ordered
anything yet — `order_id`, `product_name`, `product_price`, and `qty` are all
`NOT NULL`, so registering a customer with no order forces either a schema change or a
row full of placeholder values that mean nothing (`product_name = ''`, `qty = 0`).
There is no clean insert for "a customer exists" alone.

## The normalized fix

Split by functional dependency: customer facts depend on the customer, product facts
depend on the product, and only order-specific facts (which product, how many) belong
on the order row itself.

```sql
DROP TABLE IF EXISTS orders_norm, products_norm, customers_norm;

CREATE TABLE customers_norm (
    customer_id INT PRIMARY KEY,
    name        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    city        TEXT NOT NULL
);

CREATE TABLE products_norm (
    product_id INT PRIMARY KEY,
    name       TEXT NOT NULL,
    price      NUMERIC NOT NULL
);

CREATE TABLE orders_norm (
    order_id    INT PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers_norm(customer_id),
    product_id  INT NOT NULL REFERENCES products_norm(product_id),
    qty         INT NOT NULL
);
```

All three anomalies are now structurally impossible, not just avoided by discipline:

```sql
-- Insertion: a customer with zero orders is a normal row, no placeholders needed.
INSERT INTO customers_norm VALUES (3, 'Priya Nair', 'priya@example.com', 'Pune');

-- Update: ONE row changes; every order referencing that customer reflects it
-- automatically, because the city is stored exactly once.
UPDATE customers_norm SET city = 'Abuja' WHERE customer_id = 1;
SELECT o.order_id, c.name, c.city
FROM orders_norm o JOIN customers_norm c ON c.customer_id = o.customer_id
ORDER BY o.order_id;
```

Real output — both of Amara's orders agree, from a single update:

```text
 order_id |     name     |  city
----------+--------------+--------
        1 | Amara Okafor | Abuja
        2 | Amara Okafor | Abuja
        3 | Diego Ramos  | Madrid
```

```sql
-- Deletion: Diego's only order is deleted; his customer row is untouched.
DELETE FROM orders_norm WHERE order_id = 3;
SELECT * FROM customers_norm ORDER BY customer_id;
```

```text
 customer_id |     name     |       email        |  city
-------------+--------------+---------------------+--------
           1 | Amara Okafor | amara@example.com   | Abuja
           2 | Diego Ramos  | diego@example.com   | Madrid
           3 | Priya Nair   | priya@example.com   | Pune
```

Diego's customer row survives the deletion of his only order — deleting the order and
forgetting the customer are now two separate, explicit actions.

**Go, the fix's key proof — one `UPDATE`, both orders agree:**

```go
pool.Exec(ctx, `UPDATE customers_norm SET city = 'Abuja' WHERE customer_id = 1`)

rows, _ := pool.Query(ctx, `
    SELECT o.order_id, c.name, c.city
    FROM orders_norm o JOIN customers_norm c ON c.customer_id = o.customer_id
    ORDER BY o.order_id`)
for rows.Next() {
    var id int
    var name, city string
    rows.Scan(&id, &name, &city)
    fmt.Printf("order_id=%d name=%s city=%s\n", id, name, city)
}
```

Real output:

```text
order_id=1 name=Amara Okafor city=Abuja
order_id=2 name=Amara Okafor city=Abuja
order_id=3 name=Diego Ramos city=Madrid
```

Same guarantee, same result, regardless of which language issued the `UPDATE` — again,
because the guarantee lives in the schema, not the client.

## Denormalization: the informed reversal

Normalization optimizes for **write correctness** (one fact, one place) at the cost of
**read cost** (assembling a full picture means joining several tables). Denormalization
trades back the other way, on purpose, for a specific measured reason:

- **Read-heavy reporting/analytics.** A dashboard querying `orders_norm` joined to
  `customers_norm` and `products_norm` millions of times a day may be cheaper to serve
  from a periodically-refreshed flat table or **materialized view** that already has
  the join done — `CREATE MATERIALIZED VIEW`, refreshed on a schedule, trades
  freshness for read speed.
- **A hot, narrow read path.** Caching a computed or joined value (order count on the
  customer row, updated by trigger or application code on write) avoids a join on
  every read of a page that's viewed far more often than it's written.
- **Deliberate redundancy in NoSQL document design.** `NoSQL/mongodb/04_embedding_vs_referencing.md`
  covers the document-model version of exactly this tradeoff — embedding is
  denormalization by another name, chosen because MongoDB has no cheap join.

The failure mode to name in an interview isn't "normalization good, denormalization
bad" — it's: **normalize first, by default, because it makes correctness free; then
denormalize specific, measured hot paths, with an explicit plan for how the duplicated
copy stays consistent** (a trigger, a background job, an event, or an accepted staleness
window). Denormalizing everything up front, "for performance," before you have a
measured read-heavy path, just re-introduces the three anomalies above for no proven
benefit.

## Common mistakes

- **Stopping at 1NF and calling it done.** Atomic columns alone don't prevent the
  update/delete anomalies shown above — those come from 2NF/3NF violations.
- **Over-normalizing a reporting table.** A star-schema fact table joined to a dozen
  dimension tables for every dashboard query is technically normalized and practically
  unusable — analytics workloads often denormalize on purpose (see above).
- **Denormalizing without a plan for staying consistent.** Copying a customer's city
  onto every order "for speed" recreates the exact update anomaly demonstrated above,
  unless something (a trigger, an application-level write path) keeps every copy in
  sync.
- **Treating BCNF as a target for every table.** Most real schemas stop at 3NF; chasing
  BCNF on tables with no problematic candidate-key overlap is effort spent on a rule
  that isn't actually protecting you from anything.

## What's next

Level 17 covers replication — how a second copy of this same normalized data stays in
sync across two separate database instances, and what "in sync" actually guarantees.
