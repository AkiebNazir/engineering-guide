# Schema Migrations

**Already covered elsewhere:** `SoftwareDesign/09_data_design_and_schema_evolution.md`
§5 already covers the general expand/contract pattern (rename a column with zero
downtime, dual-write, backfill, switch reads, contract) in depth, with a worked
example spanning two app versions running side by side during a rolling deploy. This
level does not re-derive that pattern — follow the link there for the general shape
— and instead focuses on the **Postgres-specific mechanics** underneath it: exactly
what `ALTER TABLE` locks, for how long, and why a `DEFAULT` value's *type* changes
the answer.

## The mental model

A migration is a **versioned script** that changes the schema, paired with a way to
undo it. The two things that make migrations safe in production rather than
terrifying are (1) never combining a schema change with a backfill of existing data
in the same step, and (2) knowing exactly what lock each `ALTER TABLE` variant takes
and for how long — a lock held for milliseconds is invisible; the same lock held for
the seconds a full-table rewrite takes can queue up every other query against that
table behind it.

## Up/down migration scripts

A minimal versioned migration, in the shape most migration tools (Alembic, Flyway,
golang-migrate, raw numbered `.sql` files) converge on:

```sql
-- 0007_add_plan_tier.up.sql
ALTER TABLE accounts ADD COLUMN plan_tier TEXT NOT NULL DEFAULT 'free';

-- 0007_add_plan_tier.down.sql
ALTER TABLE accounts DROP COLUMN plan_tier;
```

Every migration having a `down` script isn't optional ceremony — it's what makes a
bad deploy reversible without a manual, ad-hoc, under-pressure `ALTER TABLE` written
at 2am. Even when you don't expect to ever run it, write it as if you will.

## `ALTER TABLE ... ADD COLUMN` locking behavior — measured

All three variants below take an `ACCESS EXCLUSIVE` lock on the table for the
duration of the statement (nothing else can read *or* write the table while it
holds) — the difference that matters is **how long** that lock is held, which
depends entirely on whether Postgres can add the column as a pure metadata change or
has to rewrite every existing row.

**A constant `DEFAULT`** — since Postgres 11, this is a metadata-only change: the
new column's default value is recorded in the table's catalog entry, and existing
rows are treated as having that value logically without Postgres actually writing it
into every row on disk.

```sql
ALTER TABLE accounts_big ADD COLUMN plan_tier TEXT NOT NULL DEFAULT 'free';
```

Measured on the 300,000-row `accounts_big` table from level 10:

```text
ADD COLUMN ... DEFAULT 'free' (constant default): 0.64 ms
```

Well under a millisecond, regardless of table size — the lock is held so briefly it
would be very unlikely to even be noticed in production.

**A volatile `DEFAULT`** (any function whose result isn't a fixed constant — `now()`,
`random()`, `gen_random_uuid()`) cannot use the metadata-only path, because each row
genuinely needs its *own* computed value, not one shared constant. Postgres has to
rewrite the entire table:

```sql
ALTER TABLE accounts_big ADD COLUMN signup_token UUID NOT NULL DEFAULT gen_random_uuid();
```

Measured on the same table:

```text
ADD COLUMN ... DEFAULT gen_random_uuid() (volatile default): 720.39 ms
```

**~1,125x slower than the constant-default case**, and — critically — that entire
720 ms is spent holding the `ACCESS EXCLUSIVE` lock. On a table under real
production load, 720 ms of every query queuing up behind a table lock is a visible
outage, not a rounding error. This is precisely why "just add a column with a
default" is not a universally safe statement — whether the default is volatile is
the deciding factor.

**Go (native `pgxpool`), the same two `ALTER TABLE`s, timed with `time.Since`:**

```go
func timeIt(ctx context.Context, pool *pgxpool.Pool, label, sql string) {
    t0 := time.Now()
    if _, err := pool.Exec(ctx, sql); err != nil {
        log.Fatalf("%s: %v", label, err)
    }
    fmt.Printf("%s: %.2f ms\n", label, float64(time.Since(t0).Microseconds())/1000.0)
}

timeIt(ctx, pool, "ADD COLUMN ... DEFAULT 'free' (constant default)",
    `ALTER TABLE accounts_big ADD COLUMN plan_tier_go TEXT NOT NULL DEFAULT 'free'`)
timeIt(ctx, pool, "ADD COLUMN ... DEFAULT gen_random_uuid() (volatile default)",
    `ALTER TABLE accounts_big ADD COLUMN signup_token_go UUID NOT NULL DEFAULT gen_random_uuid()`)
```

Real output, same 300,000-row table, columns added under different names to avoid
colliding with the ones the Python demo above already left in place:

```text
ADD COLUMN ... DEFAULT 'free' (constant default): 0.82 ms
ADD COLUMN ... DEFAULT gen_random_uuid() (volatile default): 795.42 ms
```

Same ~970x order of magnitude as the Python measurement (0.82ms vs 795.42ms here) —
the cost is Postgres rewriting every row on disk, which happens identically no matter
which client issued the `ALTER TABLE`.

## The expand/contract pattern, Postgres-specific version

For a genuinely required column that needs a *per-row computed or backfilled* value
(not a shared constant), the safe path is exactly the general expand/contract shape
from `SoftwareDesign/09_data_design_and_schema_evolution.md` §5, with the Postgres
mechanics spelled out:

```sql
-- 1. EXPAND: add the column as NULLABLE. This is a metadata-only change,
--    just like the constant-default case above -- fast regardless of table size.
ALTER TABLE accounts_big ADD COLUMN region_code TEXT;

-- 2. BACKFILL: populate it in the background, ideally in small batches
--    (not one giant UPDATE on a real production table -- see note below).
UPDATE accounts_big SET region_code = left(country, 2);

-- 3. CONTRACT: once every row has a value, enforce it.
ALTER TABLE accounts_big ALTER COLUMN region_code SET NOT NULL;
```

Measured on the 300,000-row table:

```text
expand (ADD nullable column):          0.38 ms
backfill (UPDATE all rows):         1879.76 ms
contract (SET NOT NULL, after backfill):  30.37 ms
```

Three observations from these real numbers:

- **The expand step is as cheap as the constant-default `ADD COLUMN`** — adding a
  nullable column with no default is also metadata-only, for the same reason.
- **The backfill is the expensive step** (1.88 seconds here), but it's a plain
  `UPDATE`, not a schema-locking DDL statement — it takes ordinary row locks as it
  goes, not one blocking table-wide lock for its whole duration, and (more
  importantly) it can be broken into smaller batched `UPDATE ... WHERE id BETWEEN
  ...` transactions in production so no single statement holds anything for 1.88
  seconds at once.
- **`SET NOT NULL` still costs something (30.37 ms here)** — Postgres has to scan
  the whole table once to verify no `NULL`s remain before it can add the constraint.
  This scan holds a lock for its duration, but it's a fraction of the volatile-default
  rewrite's cost, and (since Postgres 12) `SET NOT NULL` can use an existing `CHECK
  (col IS NOT NULL)` constraint already validated as `NOT VALID`/`VALIDATE
  CONSTRAINT` to skip the scan entirely — the fully zero-downtime version of this
  step for large tables.

**Go, the same three-step expand/backfill/contract, timed the same way:**

```go
timeIt(ctx, pool, "expand (ADD nullable column)",
    `ALTER TABLE accounts_big ADD COLUMN region_code_go TEXT`)
timeIt(ctx, pool, "backfill (UPDATE all rows)",
    `UPDATE accounts_big SET region_code_go = left(country, 2)`)
timeIt(ctx, pool, "contract (SET NOT NULL, after backfill)",
    `ALTER TABLE accounts_big ALTER COLUMN region_code_go SET NOT NULL`)
```

Real output:

```text
expand (ADD nullable column): 0.49 ms
backfill (UPDATE all rows): 2059.05 ms
contract (SET NOT NULL, after backfill): 32.66 ms
```

Same shape as the Python numbers (0.38 / 1879.76 / 30.37 ms): expand and contract are
cheap, the backfill is where the real cost lives, regardless of client language — the
three-step split matters because it turns one lock held for ~2 seconds into two locks
held for under a millisecond each, plus a plain `UPDATE` in between that only takes
ordinary row locks.

## Common mistakes

- **Adding a `NOT NULL` column with no default in one step, on a table with existing
  rows.** Postgres has no value to backfill existing rows with and the statement is
  simply rejected — this forces you into an expand/contract shape whether you
  planned for it or not.
- **Running the backfill `UPDATE` as one giant statement on a large, live production
  table.** As measured above, this is where the real time goes — and one huge
  `UPDATE` also generates one huge burst of WAL and holds row locks on everything it
  touches for the whole statement's duration, competing with live traffic. Batch it.
- **Not noticing a default is volatile.** `DEFAULT now()` looks as innocuous as
  `DEFAULT 'free'` in a migration file; only one of them triggers a full table
  rewrite, and the difference measured above (0.64 ms vs 720 ms) is the entire
  reason to know it before running it on a production-sized table, not after.

## What's next

Level 13 covers connection pooling and the N+1 query problem — the client-side
patterns that determine how much load your application actually puts on this
database in the first place.
