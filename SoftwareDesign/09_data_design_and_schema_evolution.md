# Data Design and Schema Evolution in Code

> "Show me your flowcharts and conceal your tables, and I shall continue to be mystified.
> Show me your tables, and I won't usually need your flowcharts; they'll be obvious."
> — Fred Brooks, *The Mythical Man-Month*
>
> "Data outlives code."

Code is replaced every few years. **Data is kept for decades** — in databases, queues,
caches, files, backups, analytics warehouses, and in clients running last year's app
version. Every record written today must be readable by code that doesn't exist yet, and
every piece of code deployed today must read records written by code that no longer
exists.

This file is about designing data shapes and changing them safely: compatibility rules,
serialisation, versioning, zero-downtime schema migrations, and the representation choices
(money, time, IDs, nulls) that are cheap to get right on day one and very expensive to fix
later.

Examples are in **Python** with **Go** in §8. Every example was run; outputs are real.

**Already covered elsewhere — not repeated here:**

| Topic | Where |
|---|---|
| Code-level <abbr title="Application Programming Interface">API</abbr> evolution (expand → migrate → contract, semver) | `03_modularity_coupling_and_api_design.md` §10 |
| DTO vs. domain model vs. persistence model | `08_application_architecture_in_code.md` §6 |
| Migration runner implementation (versions table, transactions) | `PyEngineering/11_migrations_schema_management`, `GoEngineering/11_*` |
| JSON/protobuf encoding hands-on | `PyEngineering/23_custom_json_protobuf_encoding`, `GoEngineering/23_*` |
| Serialisation formats compared; REST/gRPC <abbr title="Application Programming Interface">API</abbr> versioning | `SystemDesign/building_blocks/04_api_design_low_level.md`, `SystemDesign/building_blocks/03_api_design_high_level.md` |
| Normalisation, indexes, isolation levels, database internals | `CSFundamentals/03_databases_deep_dive.md`, `SystemDesign/building_blocks/05–06` |
| Event sourcing, outbox, CQRS | `CSFundamentals/04_software_engineering_deep_dive.md` §2 |

---

## Contents

1. [Why data design is different from code design](#1--why-data-design-is-different-from-code-design)
2. [Compatibility: backward, forward, full](#2--compatibility-backward-forward-full)
3. [The rules of safe schema change](#3--the-rules-of-safe-schema-change)
4. [Tolerant readers, versioning, and upcasters](#4--tolerant-readers-versioning-and-upcasters)
5. [Zero-downtime database migrations](#5--zero-downtime-database-migrations)
6. [Representation choices: money, time, IDs, text](#6--representation-choices-money-time-ids-text)
7. [Nulls, optionality, defaults, and deletion](#7--nulls-optionality-defaults-and-deletion)
8. [Serialisation in Go: tolerant messages, strict config](#8--serialisation-in-go-tolerant-messages-strict-config)
9. [Protobuf and schema-first formats](#9--protobuf-and-schema-first-formats)
10. [Everything that stores data has a schema](#10--everything-that-stores-data-has-a-schema)
11. [Testing compatibility](#11--testing-compatibility)
12. [Red flags](#12--red-flags)
13. [Interview questions and model answers](#13--interview-questions-and-model-answers)
14. [Checklist](#14--checklist)

---

## 1 · Why data design is different from code design

| | Code | Data |
|---|---|---|
| Lifetime | Months to years | Years to decades (plus backups) |
| Changing it | Deploy a new version; old version is gone | Old records remain; must be migrated or read forever |
| Rollback | Redeploy the previous version | New-format data written in the meantime may be unreadable by the old version |
| Who reads it | This service | This service's old and new versions, other services, analytics jobs, <abbr title="Machine Learning">ML</abbr> pipelines, support tooling, auditors |
| Mistakes | Fixed by the next deploy | Corrupted or lost data is often permanent |

Three consequences shape everything else in this file:

1. **During every deploy, two versions of the code run at once** (rolling deploys, canaries,
   multi-region rollouts, mobile clients that never update). Every change must work with
   both.
2. **Rollback must be possible**, so the new version cannot write data the old version
   can't read — at least until the new version is proven.
3. **Data has consumers you don't know about.** A column rename breaks the finance team's
   nightly SQL report, which nobody told you exists. Treat stored and published data as a
   public <abbr title="Application Programming Interface">API</abbr>.

---

## 2 · Compatibility: backward, forward, full

Name the direction precisely — people use "backward compatible" to mean both.

```
                 writes with             reads with
 BACKWARD   :    OLD schema     ───▶     NEW code        "new code reads old data"
 FORWARD    :    NEW schema     ───▶     OLD code        "old code reads new data"
 FULL       :    both directions
```

| Compatibility | Needed when | Example |
|---|---|---|
| **Backward** | New code must read existing data: database rows, stored files, queued messages from before the deploy | A v3 service reading orders written in 2019 |
| **Forward** | Old code must read data written by new code: during a rolling deploy, after a rollback, old mobile clients reading new <abbr title="Application Programming Interface">API</abbr> responses, old consumers of a topic | v2 instances still running while v3 instances publish events |
| **Full** | Both, which is the practical requirement for most shared data | Kafka topics with independent producer/consumer deploys |

In ten lines, before the field-by-field rules in §3 and the full worked example in §4:

```python
# BACKWARD vs FORWARD compatibility, minimally.
old_record = {"name": "Ada"}
new_record = {"first_name": "Ada", "last_name": "Lovelace"}

def old_reader(rec):        # only knows "name"
    return rec.get("name", "unknown")

def new_reader(rec):        # knows "name" is gone; falls back for records written before the change
    return rec.get("first_name") or rec.get("name", "unknown")

print(new_reader(old_record))   # BACKWARD: new code reads data written by old code
print(old_reader(new_record))   # FORWARD: old code reads data written by new code — degrades, doesn't crash
```

Output:

```
Ada
unknown
```

Neither reader crashes on the other version's shape. `old_reader` degrades to
`"unknown"` rather than raising `KeyError` — that degradation, not an exception, is what
forward compatibility buys you.

**Deployment ordering follows from it:**

| Change | Safe order |
|---|---|
| Reader must understand a new field before anyone writes it | Deploy **readers first**, then writers |
| Writer stops writing a field readers depend on | Deploy **readers first** (stop depending), then writers |
| New required field | Don't. Add as optional with a default → deploy writers → backfill → then enforce |

Schema registries (Confluent Schema Registry, Buf) enforce a chosen compatibility mode
automatically on every schema change — reject the change at CI time rather than at 2 a.m.

---

## 3 · The rules of safe schema change

These rules apply to JSON documents, protobuf messages, Avro records, database tables, and
cache entries alike.

| Change | Safe? | Why / how |
|---|---|---|
| **Add an optional field with a default** | ✅ | Old readers ignore it (if tolerant); new readers default it on old data |
| **Add a required field** | ❌ | Old data doesn't have it; old writers don't send it. Add optional → backfill → enforce in code |
| **Remove a field** | ⚠️ | Only after no reader uses it. Stop reading → stop writing → remove. In protobuf, `reserved` the number and name forever |
| **Rename a field** | ❌ as a single step | It's add + remove. Use expand/contract (§5) or keep the wire name and rename only in code |
| **Change a field's type** | ❌ | `int` → `string`, dollars float → cents int. Add a new field; migrate; remove the old |
| **Change a field's meaning** | ❌ — the most dangerous | Same name, same type, different semantics (`amount` now includes tax). No parser catches it. Always a new field |
| **Add an enum value** | ⚠️ | Old readers must handle unknown values (§4). Deploy readers first |
| **Remove an enum value** | ⚠️ | Old data still contains it. Keep it readable forever |
| **Widen a numeric type** (int32 → int64) | ⚠️ | Readers of the narrow type overflow on large values. Deploy readers first |
| **Tighten validation** (max length 255 → 100) | ⚠️ | Existing data violates it. Apply to new writes only; clean up old data separately |
| **Relax validation** | ⚠️ | Old readers may reject newly valid values (a longer string, a new character set) |

The general principle: **every change is either additive, or split into additive steps
separated by deploys.**

---

## 4 · Tolerant readers, versioning, and upcasters

### Tolerant reader (Postel's law applied to data)

A **tolerant reader** reads only the fields it needs, ignores fields it doesn't know,
defaults fields that are missing, and maps unknown enum values to an explicit "unknown"
rather than crashing. It is the single most important habit for forward compatibility.

```python
# TOLERANT READING in miniature, before the full upcaster example below.
def parse_job(d: dict) -> dict:
    return {
        "id": d["id"],                          # required: crash loudly if truly missing
        "retries": d.get("retries", 0),          # unknown/missing field: default it
        "priority": d.get("priority", "normal"), # a field this reader has never heard of has no effect
    }

print(parse_job({"id": "j1", "retries": 3, "region": "eu-west-1"}))   # "region" is silently ignored
print(parse_job({"id": "j2"}))                                        # missing fields get defaults
```

Output:

```
{'id': 'j1', 'retries': 3, 'priority': 'normal'}
{'id': 'j2', 'retries': 0, 'priority': 'normal'}
```

`region` is dropped rather than raising `TypeError: unexpected keyword argument` — a
future writer can add fields without coordinating a deploy with every reader.

Two caveats keep tolerance from becoming sloppiness:

- **Be strict about what you write.** Emit exactly the documented schema.
- **Be strict with configuration and user input**, where an unknown field is almost
  always a typo (§8).

### Versioning stored records

When a change can't be purely additive, stamp records with a `schema_version` and
**upgrade on read** with a chain of small functions — **upcasters** — each converting
version N to N+1. Old data is never rewritten in bulk unless you choose to.

```python
# Evolving a stored/transmitted record: tolerant reader + upcasters + round-tripping unknowns.
import json
from dataclasses import dataclass, field
from enum import Enum


class Status(Enum):
    PENDING = "pending"
    PAID = "paid"
    UNKNOWN = "unknown"                    # a value from the future lands here, not in a crash

    @classmethod
    def parse(cls, raw: str) -> "Status":
        try:
            return cls(raw)
        except ValueError:
            return cls.UNKNOWN


CURRENT_VERSION = 3


# Each upcaster turns version N into N+1. Old data is never rewritten in place;
# it's upgraded on read, one small, testable step at a time.
def v1_to_v2(d: dict) -> dict:
    # v2 split "name" into first/last.
    first, _, last = d.pop("name").partition(" ")
    return {**d, "first_name": first, "last_name": last, "schema_version": 2}


def v2_to_v3(d: dict) -> dict:
    # v3 changed "total" (float dollars) to "total_cents" (int) — see §6 on money.
    return {**{k: v for k, v in d.items() if k != "total"},
            "total_cents": round(d["total"] * 100), "schema_version": 3}


UPCASTERS = {1: v1_to_v2, 2: v2_to_v3}


@dataclass
class OrderRecord:
    order_id: str
    first_name: str
    last_name: str
    total_cents: int
    status: Status
    extra: dict = field(default_factory=dict)        # fields this version doesn't understand
    raw_status: str = ""                             # original enum text, kept for UNKNOWN
    source_version: int = CURRENT_VERSION

    KNOWN = {"schema_version", "order_id", "first_name", "last_name", "total_cents", "status"}

    @classmethod
    def from_json(cls, raw: str) -> "OrderRecord":
        d = json.loads(raw)
        version = source_version = d.get("schema_version", 1)   # absent → oldest format
        # version > CURRENT_VERSION: a newer writer. Read what we know (forward compatibility).
        while version < CURRENT_VERSION:
            d = UPCASTERS[version](d)
            version = d["schema_version"]
        return cls(
            order_id=d["order_id"],
            first_name=d["first_name"],
            last_name=d["last_name"],
            total_cents=int(d["total_cents"]),
            status=Status.parse(d.get("status", "pending")),   # new optional field: default
            extra={k: v for k, v in d.items() if k not in cls.KNOWN},
            raw_status=d.get("status", "pending"),
            source_version=source_version,
        )

    def to_json(self) -> str:
        return json.dumps({
            **self.extra,                              # preserve what we didn't understand
            "schema_version": max(CURRENT_VERSION, self.source_version),   # never downgrade
            "order_id": self.order_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "total_cents": self.total_cents,
            "status": self.raw_status if self.status is Status.UNKNOWN else self.status.value,
        }, sort_keys=True)


if __name__ == "__main__":
    v1 = '{"order_id": "o-1", "name": "Ada Lovelace", "total": 19.99}'
    v2 = '{"schema_version": 2, "order_id": "o-2", "first_name": "Alan", "last_name": "Turing", "total": 5.1, "status": "paid"}'
    v4 = ('{"schema_version": 4, "order_id": "o-3", "first_name": "Grace", "last_name": "Hopper",'
          ' "total_cents": 700, "status": "refunded", "loyalty_tier": "gold"}')

    for raw in (v1, v2, v4):
        rec = OrderRecord.from_json(raw)
        print(rec.order_id, rec.first_name, rec.last_name, rec.total_cents, rec.status, rec.extra)

    old, older, newer = (OrderRecord.from_json(r) for r in (v1, v2, v4))
    assert old.total_cents == 1999 and old.status is Status.PENDING
    assert older.total_cents == 510                   # round(), not int(): 5.1*100 = 509.99999999999994
    assert newer.status is Status.UNKNOWN and newer.extra == {"loyalty_tier": "gold"}

    rewritten = json.loads(newer.to_json())
    print(rewritten)
    assert rewritten["loyalty_tier"] == "gold"         # unknown field survived a read-modify-write
    assert rewritten["status"] == "refunded" and rewritten["schema_version"] == 4   # and nothing was downgraded
    print("ALL PASSED")
```

Output:

```
o-1 Ada Lovelace 1999 Status.PENDING {}
o-2 Alan Turing 510 Status.PAID {}
o-3 Grace Hopper 700 Status.UNKNOWN {'loyalty_tier': 'gold'}
{'first_name': 'Grace', 'last_name': 'Hopper', 'loyalty_tier': 'gold', 'order_id': 'o-3', 'schema_version': 4, 'status': 'refunded', 'total_cents': 700}
ALL PASSED
```

What the example handles, and why each matters:

| Situation | Handling | Failure if you don't |
|---|---|---|
| v1 record with no version field | Absent → version 1 | `KeyError` on every pre-versioning record |
| v1 → v3 | Two upcasters chained | One giant `if version == 1 … elif …` that grows forever |
| Float dollars → int cents | `round(total * 100)` | `int(5.1 * 100)` = **509**: a cent lost on some records |
| v4 record from a newer writer | Read known fields, keep the rest | Crash during a rolling deploy or after rollback |
| Unknown enum `"refunded"` | `Status.UNKNOWN`, raw text kept | `ValueError` crash, or worse, silently treated as `PENDING` |
| Read-modify-write of a v4 record by v3 code | Unknown fields, raw enum text, and version are written back unchanged | **Silent data loss**: old code deletes fields it didn't understand |

The last row is the subtle one, and it bites in production: an old service instance loads
a record, changes one field, and saves it — dropping every field added by the newer
version. Preserving unknowns (protobuf does this automatically since 3.5; hand-written
JSON code must do it explicitly) or refusing to write records with a newer version are the
two safe options.

### Versioning strategies compared

| Strategy | How | Good for | Cost |
|---|---|---|---|
| **Additive only, no version** | Only ever add optional fields | Most JSON APIs and events | Accumulated optional fields; no breaking changes ever |
| **Version field + upcasters** | Upgrade on read (above) | Event stores, documents, files | Upcaster chain must be maintained and tested |
| **Migrate in place** | Rewrite all records to the new version | Databases you control completely | Big batch job; must coexist with live traffic (§5) |
| **New type / topic / endpoint** | `orders.v2` alongside `orders.v1` | Truly incompatible redesigns | Dual publishing; consumer migration; long tail |

---

## 5 · Zero-downtime database migrations

A migration that runs as `ALTER TABLE users RENAME COLUMN fullname TO display_name`
during a rolling deploy breaks every instance of the old version instantly — they're still
running queries against `fullname`. The fix is **expand → migrate → contract**, with each
step deployed separately so that **every adjacent pair of app versions works against every
schema state they overlap with.**

```
 schema:    fullname              + display_name (nullable)                       display_name only
            ─────────┬────────────────────────────────────────────────────────┬─────────────────
 step:               1 EXPAND     2 DUAL-WRITE     3 BACKFILL     4 SWITCH READS   5 CONTRACT
 app:       V1       V1           V1 → V2          V2             V2 → V3          V3 → V4
 writes:    old      old          old + new        old + new      old + new        new
 reads:     old      old          old              old            new              new
```

```python
# Renaming a column with zero downtime: expand → dual-write → backfill → switch reads → contract.
# Two app versions run side by side during every step of a rolling deploy.
import sqlite3


def setup() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, fullname TEXT NOT NULL)")
    db.executemany("INSERT INTO users (fullname) VALUES (?)", [(f"user {i}",) for i in range(2_500)])
    db.commit()
    return db


# ---- application versions ----
class AppV1:                                       # original: knows only `fullname`
    def __init__(self, db): self.db = db
    def create(self, name):
        return self.db.execute("INSERT INTO users (fullname) VALUES (?)", (name,)).lastrowid
    def read(self, uid):
        return self.db.execute("SELECT fullname FROM users WHERE id=?", (uid,)).fetchone()[0]


class AppV2:                                       # dual-writes; still READS the old column
    def __init__(self, db): self.db = db
    def create(self, name):
        return self.db.execute("INSERT INTO users (fullname, display_name) VALUES (?, ?)",
                               (name, name)).lastrowid
    def read(self, uid):
        return self.db.execute("SELECT fullname FROM users WHERE id=?", (uid,)).fetchone()[0]


class AppV3:                                       # reads the new column; still dual-writes
    def __init__(self, db): self.db = db
    def create(self, name):
        return self.db.execute("INSERT INTO users (fullname, display_name) VALUES (?, ?)",
                               (name, name)).lastrowid
    def read(self, uid):
        return self.db.execute("SELECT display_name FROM users WHERE id=?", (uid,)).fetchone()[0]


class AppV4:                                       # new column only
    def __init__(self, db): self.db = db
    def create(self, name):
        return self.db.execute("INSERT INTO users (display_name) VALUES (?)", (name,)).lastrowid
    def read(self, uid):
        return self.db.execute("SELECT display_name FROM users WHERE id=?", (uid,)).fetchone()[0]


def backfill(db: sqlite3.Connection, batch: int = 1_000) -> int:
    """Small batches, each its own transaction, resumable, idempotent."""
    total, last_id = 0, 0
    while True:
        ids = [r[0] for r in db.execute(
            "SELECT id FROM users WHERE id > ? AND display_name IS NULL ORDER BY id LIMIT ?",
            (last_id, batch))]
        if not ids:
            return total
        db.execute(f"UPDATE users SET display_name = fullname WHERE id IN ({','.join('?' * len(ids))})"
                   " AND display_name IS NULL", ids)
        db.commit()                                # short transactions: no long locks
        total, last_id = total + len(ids), ids[-1]


if __name__ == "__main__":
    db = setup()

    # Step 1 EXPAND: additive, nullable → old code (V1) is unaffected.
    db.execute("ALTER TABLE users ADD COLUMN display_name TEXT")
    v1, v2 = AppV1(db), AppV2(db)
    a = v1.create("written by v1 during deploy")        # V1 and V2 both live
    b = v2.create("written by v2")
    assert v1.read(b) == "written by v2" and v2.read(a) == "written by v1 during deploy"

    # Step 2 BACKFILL old rows (V1 may still be writing NULLs until it's fully drained).
    print("backfilled:", backfill(db))
    assert db.execute("SELECT count(*) FROM users WHERE display_name IS NULL").fetchone()[0] == 0

    # Step 3 SWITCH READS: V3 reads the new column; V2 still running is fine (it dual-writes).
    v3 = AppV3(db)
    c = v2.create("v2 during v3 rollout")
    assert v3.read(c) == "v2 during v3 rollout" and v3.read(a) == "written by v1 during deploy"

    # Step 4 CONTRACT, only after no V2/V3 remains: stop writing, then drop the old column.
    #   (V4 can't insert while fullname is NOT NULL — the drop must come first, or relax the
    #   constraint in the expand step. Ordering constraints are the whole game.)
    db.execute("ALTER TABLE users DROP COLUMN fullname")    # SQLite ≥ 3.35
    v4 = AppV4(db)
    d = v4.create("v4 only")
    print(v4.read(a), "|", v4.read(d))
    assert v4.read(a) == "written by v1 during deploy"
    print("ALL PASSED")
```

Output:

```
backfilled: 2501
written by v1 during deploy | v4 only
ALL PASSED
```

Rules the example encodes:

1. **Expand with additive, nullable changes** so the old version is unaffected. Adding a
   `NOT NULL` column without a default breaks old writers immediately.
2. **Dual-write before backfill.** Otherwise rows created during the backfill are missed.
   Note the backfill still found V1's row: V1 instances keep writing only the old column
   until the rollout completes — which is why the backfill runs **after** V2 is fully
   deployed, and is idempotent so it can be re-run.
3. **Backfill in small batches, each its own transaction**, keyed by primary-key ranges.
   One `UPDATE users SET …` over 500 million rows holds locks for hours, bloats the
   transaction log, and lags replicas.
4. **Switch reads only when the new column is complete**, and keep dual-writing so V2 (still
   running during V3's rollout) and a rollback to V2 both keep working.
5. **Contract last, and separately**: stop writing the old column, wait until nothing reads
   it (check query logs), then drop it. Dropping is the one irreversible step — do it days
   later, after backups have captured the transition.
6. **Constraints are ordering constraints.** The old column was `NOT NULL`, so V4 couldn't
   insert without it; the drop (or a `DROP NOT NULL` during expand) must precede V4.

### Operational hazards of DDL itself

| Hazard | Example | Mitigation |
|---|---|---|
| **Table rewrite** | Changing a column type in PostgreSQL rewrites the table under an exclusive lock | New column + backfill instead |
| **Lock queueing** | `ALTER TABLE` waits for a long-running query; every later query queues behind the `ALTER` — outage | Set `lock_timeout` (e.g. 2 s) and retry; kill long transactions first |
| **Index builds** | `CREATE INDEX` blocks writes | `CREATE INDEX CONCURRENTLY` (PostgreSQL); online DDL (MySQL `ALGORITHM=INPLACE`, gh-ost, pt-online-schema-change) |
| **Adding a foreign key / check** | Validates every existing row under lock | Add as `NOT VALID`, then `VALIDATE CONSTRAINT` separately |
| **Backfill load** | Saturates I/O, lags replicas | Throttle between batches; watch replica lag |
| **Migrations coupled to app deploys** | App V2 fails to start because migration hasn't run | Migrations are their own step; app code tolerates both schema states |

Spanner, CockroachDB, and similar systems run schema changes online in the background,
but the **application-level** rules (expand/contract, two versions live) still apply.

---

## 6 · Representation choices: money, time, IDs, text

```python
# Representation choices that are cheap to get right on day one and very expensive later.
import time
import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from zoneinfo import ZoneInfo

# ---- 1. Money: never binary floats ----
balance = 0.0
for _ in range(10):
    balance += 0.10                                           # ten 10-cent deposits
print(0.1 + 0.2 == 0.3, balance, balance == 1.0)              # False 0.9999999999999999 False
cents = sum([10] * 10)                                        # integer minor units
print(cents == 100)
share = (Decimal("100.00") / 3).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
print(share, share * 3)                                       # 33.33 99.99 → a cent must go somewhere

def split_evenly(total_cents: int, n: int) -> list[int]:
    base, remainder = divmod(total_cents, n)
    return [base + 1 if i < remainder else base for i in range(n)]   # sums exactly
parts = split_evenly(10_000, 3)
print(parts, sum(parts))
assert sum(parts) == 10_000

# ---- 2. Time: store instants in UTC; keep the zone for civil times ----
naive = datetime(2026, 3, 29, 1, 30)                         # which timezone? nobody knows
instant = datetime(2026, 3, 29, 0, 30, tzinfo=timezone.utc)
lisbon = instant.astimezone(ZoneInfo("Europe/Lisbon"))
print(naive.tzinfo, instant.isoformat(), lisbon.isoformat())

# "Every day at 09:00 local" is a CIVIL time: adding 24h across a DST change is wrong.
meeting = datetime(2026, 3, 28, 9, 0, tzinfo=ZoneInfo("Europe/Lisbon"))
by_duration = (meeting.astimezone(timezone.utc) + timedelta(hours=24)).astimezone(ZoneInfo("Europe/Lisbon"))
by_calendar = meeting + timedelta(days=1)                    # aware arithmetic keeps wall time
print(by_duration.time(), by_calendar.time())
assert by_duration.hour == 10 and by_calendar.hour == 9

# ---- 3. IDs: random vs time-ordered ----
def uuid7() -> uuid.UUID:
    """RFC 9562 UUIDv7: 48-bit Unix ms timestamp + random bits → sortable by creation time.
    (Python 3.14 adds uuid.uuid7(); this is the same layout, minus monotonic tie-breaking.)"""
    ms = time.time_ns() // 1_000_000
    b = bytearray(ms.to_bytes(6, "big") + os.urandom(10))
    b[6] = (b[6] & 0x0F) | 0x70                              # version 7
    b[8] = (b[8] & 0x3F) | 0x80                              # RFC variant
    return uuid.UUID(bytes=bytes(b))

ids = []
for _ in range(3):
    ids.append(uuid7())
    time.sleep(0.002)
print([str(i)[:13] for i in ids], ids == sorted(ids))
assert ids == sorted(ids) and all(i.version == 7 for i in ids)
print("ALL PASSED")
```

Output:

```
False 0.9999999999999999 False
True
33.33 99.99
[3334, 3333, 3333] 10000
None 2026-03-29T00:30:00+00:00 2026-03-29T00:30:00+00:00
10:00:00 09:00:00
['01a0af58-8cac', '01a0af58-8cae', '01a0af58-8cb1'] True
ALL PASSED
```

(The UUID prefixes change every run; that they sort in creation order does not.)

### Money

| Do | Don't |
|---|---|
| Integer **minor units** (cents) + ISO 4217 currency code, or `Decimal` with explicit rounding | Binary floats (`float`, `double`, JSON numbers parsed as float) |
| Store the currency **with every amount** | Assume a global currency |
| Decide rounding rules (banker's rounding, when to round) explicitly | Round at display time only |
| Allocate remainders explicitly when splitting (`split_evenly`) | `total / n` and hope it sums |
| Know that minor units vary: JPY has 0 decimals, BHD has 3 | Hard-code `/ 100` |

### Time

| Kind of time | Store as | Example |
|---|---|---|
| **An instant** — when something happened | UTC timestamp (`TIMESTAMPTZ`, RFC 3339 with `Z`) | `created_at`, `paid_at`, log timestamps |
| **A civil / wall-clock time** — what a human scheduled | Local date-time **plus IANA zone name** | "Every day at 09:00 Europe/Lisbon", store opening hours |
| **A date without time** | `DATE` | Birthdays, invoice dates — don't store as midnight UTC (shifts a day in the Americas) |
| **A duration** | Integer seconds/ms, or ISO 8601 duration | Timeouts, subscription length |

The example shows why the zone name matters: "09:00 tomorrow" computed as "+24 hours"
lands at 10:00 across a daylight-saving change. Store `Europe/Lisbon`, not `+00:00` — the
offset changes with DST and with governments' decisions; the zone name doesn't.

Other rules: never store naive datetimes; measure durations with a monotonic clock, not
wall-clock subtraction; timezone rules change (update `tzdata`); and never trust client
clocks for ordering.

### Identifiers

| Kind | Pros | Cons |
|---|---|---|
| **Auto-increment integer** | Compact, fast index, human-friendly | Leaks volume ("order 1041 → we have ~1,000 orders"), guessable (enumeration attacks), needs a central allocator — hard to generate offline or across shards |
| **UUIDv4 (random)** | Generate anywhere, unguessable | 16 bytes; random inserts scatter across a B-tree (page splits, cache misses) |
| **UUIDv7 / ULID (time-ordered + random)** | Generate anywhere; roughly sortable by creation; B-tree friendly | Reveals creation time; not a security token |
| **Snowflake-style (timestamp + machine + sequence, 64-bit)** | Compact, sortable | Needs machine-ID coordination; clock-skew handling |
| **Natural key** (email, ISBN) | Meaningful | Real-world "unique, immutable" values change (people change email). Use as a unique constraint, not the primary key |

Also: **don't expose internal sequential IDs publicly** when enumeration matters; prefix
public IDs by type (`ord_…`, `cus_…` — Stripe's convention) so a mis-pasted ID is
detectable; and treat IDs as **opaque strings** in APIs, so the format can change.

### Text

- **UTF-8 everywhere**; in MySQL that means `utf8mb4` (MySQL's legacy `utf8` can't store emoji).
- **Length limits in characters vs. bytes vs. grapheme clusters** differ: "👩‍👩‍👧" is 1
  grapheme, 5 code points, 18 UTF-8 bytes.
- **Normalise before comparing** (Unicode NFC; case-folding with `str.casefold()` for
  case-insensitive matching) — "é" can be one or two code points.
- **Email addresses and usernames**: store as entered, compare on a normalised form with a
  unique index on that form.

```python
# The claims above, checked: one grapheme cluster, several code points, more bytes still.
import unicodedata

zwj = "\u200D"                                            # zero-width joiner
family = "\U0001F469" + zwj + "\U0001F469" + zwj + "\U0001F467"   # woman + ZWJ + woman + ZWJ + girl
print(len(family), len(family.encode("utf-8")))          # code points, UTF-8 bytes

cafe_nfc = "caf" + "\u00E9"          # precomposed é: one code point
cafe_nfd = "cafe" + "\u0301"         # "e" + combining acute accent: two code points
print(cafe_nfc == cafe_nfd, len(cafe_nfc), len(cafe_nfd))
print(unicodedata.normalize("NFC", cafe_nfd) == cafe_nfc)
```

Output:

```
5 18
False 4 5
True
```

`len()` counts code points, not grapheme clusters or bytes — a length-limit check in
Python that uses `len()` alone is already lying about what it's limiting. And
`cafe_nfc == cafe_nfd` is `False`: two strings that render identically and mean the same
thing compare unequal until normalised, which is why a unique index or an `==` check on
raw user input needs `unicodedata.normalize` first.

---

## 7 · Nulls, optionality, defaults, and deletion

### "Absent", "null", and "zero" are three different facts

```
{"discount": 0}       the discount is zero
{"discount": null}    the discount is explicitly unknown / cleared
{}                    the sender didn't say (old client? partial update?)
```

For a **PATCH** endpoint these must be distinguishable: `{}` means "don't touch the
discount", `{"discount": null}` means "remove it". Plain Python dataclasses with `None`
defaults and Go structs with zero values both collapse them. Options: a sentinel
(`UNSET = object()`), `pydantic`'s `model_fields_set`, pointers or `omitzero`/wrapper
types in Go (§8), protobuf `optional` / field masks.

The sentinel in code:

```python
# Distinguishing "not sent" from "sent null" in a PATCH body, with a sentinel object.
UNSET = object()

def apply_patch(order: dict, discount=UNSET) -> dict:
    if discount is not UNSET:               # only touch the field if the client actually sent it
        order["discount"] = discount        # None here means "explicitly cleared"
    return order

print(apply_patch({"id": "o-1", "discount": 500}))                 # {}                  -> unchanged
print(apply_patch({"id": "o-1", "discount": 500}, discount=None))  # {"discount": null}  -> cleared
print(apply_patch({"id": "o-1", "discount": 500}, discount=0))     # {"discount": 0}     -> zero
```

Output:

```
{'id': 'o-1', 'discount': 500}
{'id': 'o-1', 'discount': None}
{'id': 'o-1', 'discount': 0}
```

A default of `discount=None` instead of `discount=UNSET` cannot make this distinction —
every call that omits the argument would look identical to a call that explicitly clears
it.

### Defaults are part of the schema

When a new field is added, its default decides how **all existing data** is interpreted.
Choose the default that preserves existing behaviour:

```python
# New feature: orders can opt out of marketing emails.
marketing_opt_in: bool = True     # ✗ silently opts in every historic customer who never saw the option
marketing_opt_in: bool = False    # ✓ existing records keep behaving as before
```

### Deletion

| Approach | How | Use when | Watch out |
|---|---|---|---|
| **Hard delete** | `DELETE` | Data must really be gone (GDPR erasure, security) | Foreign keys, caches, search indexes, backups, analytics copies |
| **Soft delete** | `deleted_at` timestamp | Undo, audit, referential history | Every query must filter it (use views / default scopes); unique constraints must account for it; **it is not erasure** |
| **Archive / move** | Copy to an archive table or cold storage, then delete | Old data rarely read | Two places to query when it is needed |
| **Tombstone** | Keep ID + deletion marker | Replicated/event-driven systems, so consumers learn about the deletion | Tombstone retention |

Soft delete's most common bug: a unique constraint on `email` means a deleted user blocks
anyone re-registering with that email. Use a partial unique index
(`WHERE deleted_at IS NULL`).

---

## 8 · Serialisation in Go: tolerant messages, strict config

```go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
)

// Version 1 of a message. A newer producer adds "priority"; an older one omits "retries".
type JobV1 struct {
	ID      string `json:"id"`
	Retries int    `json:"retries"`           // 0 means "absent" OR "explicitly zero" — ambiguous
	Timeout *int   `json:"timeout,omitempty"` // pointer: nil = absent, &0 = explicitly zero
}

func main() {
	fromNewer := []byte(`{"id":"j1","retries":3,"timeout":0,"priority":"high"}`)
	fromOlder := []byte(`{"id":"j2"}`)

	// Messages between services: TOLERANT. Unknown fields are ignored by default.
	var a, b JobV1
	fmt.Println(json.Unmarshal(fromNewer, &a), a.ID, a.Retries, *a.Timeout)
	fmt.Println(json.Unmarshal(fromOlder, &b), b.ID, b.Retries, b.Timeout == nil)

	// Config files: STRICT. A typo like "retires" should fail loudly, not silently default.
	dec := json.NewDecoder(bytes.NewReader([]byte(`{"id":"j3","retires":5}`)))
	dec.DisallowUnknownFields()
	var c JobV1
	fmt.Println("strict:", dec.Decode(&c))

	// Round-tripping a message you don't fully understand: keep the raw bytes of unknowns.
	var raw map[string]json.RawMessage
	_ = json.Unmarshal(fromNewer, &raw)
	raw["retries"] = json.RawMessage(`4`) // modify one known field
	out, _ := json.Marshal(raw)           // "priority" survives
	fmt.Println(string(out))
}
```

Output:

```
<nil> j1 3 0
<nil> j2 0 true
strict: json: unknown field "retires"
{"id":"j1","priority":"high","retries":4,"timeout":0}
```

- **Messages: tolerant.** `encoding/json` ignores unknown fields by default — correct for
  inter-service messages during rolling deploys.
- **Config: strict.** `DisallowUnknownFields` turns a typo into a startup failure instead of
  a silently defaulted setting (`06` §10, fail fast).
- **Zero value vs. absent:** `Retries` is `0` both when sent as `0` and when missing. When
  the difference matters, use a pointer (`*int`), a wrapper type, or Go 1.24's `omitzero`
  tag option for output.
- **Round-tripping unknowns** requires keeping the raw form (`map[string]json.RawMessage`
  or a struct with a catch-all). Decoding into a struct and re-encoding drops `priority`
  silently — the same data-loss bug as §4.

Python equivalents: Pydantic `model_config = ConfigDict(extra="ignore")` for messages,
`extra="forbid"` for config, `extra="allow"` to preserve unknowns.

### Never deserialise untrusted data into arbitrary objects

`pickle`, Java native serialization, YAML's full loader (`yaml.load` without `SafeLoader`),
and .NET `BinaryFormatter` can **execute code** while deserialising. Never use them for
anything that crosses a trust boundary — network, queue, uploaded file, even a cache that
another service writes. They also tie the data format to class names in code, so a rename
breaks stored data. Use explicit schemas: JSON with validation, protobuf, Avro, MessagePack.

---

## 9 · Protobuf and schema-first formats

Protobuf (and Avro, Thrift) put the compatibility rules into the tooling.

```protobuf
syntax = "proto3";

message Order {
  string id = 1;
  int64 total_cents = 2;
  string currency = 3;
  Status status = 4;

  // Field 5 was `double total = 5;` — removed. Never reuse the number or the name.
  reserved 5;
  reserved "total";

  optional string coupon_code = 6;     // `optional` gives explicit presence: absent ≠ ""
  repeated LineItem items = 7;

  enum Status {
    STATUS_UNSPECIFIED = 0;            // zero value must mean "not set", never a real state
    STATUS_PENDING = 1;
    STATUS_PAID = 2;
    STATUS_REFUNDED = 3;               // added later: old readers see the numeric value 3
  }
}
```

| Rule | Why |
|---|---|
| **Field numbers are the identity on the wire**, not names | Renaming a field is wire-compatible; renumbering is not |
| **Never reuse a field number or name** — `reserved` them | An old writer's `double total = 5` bytes would be parsed as the new field 5's type → corrupt data |
| **Enum zero is `UNSPECIFIED`** | Proto3 defaults to 0 when absent; a real value there makes "absent" look like a deliberate choice |
| **Prefix enum values** (`STATUS_PAID`) | Proto enum values share the enclosing scope; prevents collisions |
| **Unknown enum values are preserved** as their number (open enums in proto3) | Old readers can round-trip new states — but code must handle "none of the known cases" |
| **Unknown fields are preserved** on re-serialise (proto3 ≥ 3.5) | Middlemen don't drop newer fields |
| **Don't change types** — few are wire-compatible (`int32`/`int64`/`bool` partly are, with truncation) | Silent corruption |
| **Use `buf breaking`** in CI | Catches all of the above automatically against the previous version |
| **Avoid `required`** (proto2) | Once required, can never be removed without breaking old readers — why proto3 dropped it |

Google's internal style leans on the same rules at enormous scale: protocol buffers were
created precisely so that services could evolve independently.

---

## 10 · Everything that stores data has a schema

"Schemaless" stores just move the schema into code — where it's implicit, unversioned,
and enforced by nobody. Apply §3–§4 to all of these:

| Store | Hidden schema | Evolution hazard | Mitigation |
|---|---|---|---|
| **Caches** (Redis, memcached) | The serialised value format | V2 reads a V1 entry → crash, or V1 reads V2's → wrong data, for the TTL duration | **Version in the key** (`user:v3:{id}`), or tolerant decoding; old entries expire naturally |
| **Queues / topics** | Message format | Messages written before the deploy are consumed after it; poison messages block the partition | Full compatibility, versioned messages, dead-letter queue |
| **Document DBs** (MongoDB, Firestore, DynamoDB) | Field names/types each code path expects | Documents of many generations coexist forever | `schema_version` + upcasters (§4), or scheduled migrations |
| **Files and object storage** | File format, path layout | Old files re-processed by new code (backfills, reprocessing) | Format version header; immutable, versioned paths |
| **Feature flags / remote config** | Keys, value types | Malformed value pushed → every instance fails at once | Validate on publish and on read; fall back to last known good |
| **Client local storage** (mobile, browser) | Stored JSON shape | App update reads last version's data; can't migrate server-side | Versioned storage + client migrations |
| **Analytics tables / data lake** | Column meanings downstream teams depend on | Renames and semantic changes break reports silently | Data contracts; announce deprecations; add, don't change |
| **Logs** (when parsed) | Field names | Dashboards and alerts break on rename | §11 of `10_designing_observable_code.md`: consistent names |

The cache row is worth an example, because it breaks rollbacks:

```python
CACHE_SCHEMA = 3

def cache_key(user_id: str) -> str:
    return f"user:v{CACHE_SCHEMA}:{user_id}"     # bump when the cached shape changes

# Deploy V3: it reads/writes user:v3:*, ignoring V2's user:v2:* entries (cache miss → load).
# Roll back to V2: it reads its own user:v2:* entries, never V3's shape.
# Cost: a cold cache after each bump — warm gradually or bump rarely.
```

---

## 11 · Testing compatibility

Compatibility bugs appear only when two versions meet, so tests must deliberately create
that meeting.

| Test | How |
|---|---|
| **Golden files of old formats** | Commit real serialised examples of every historical version (`fixtures/order_v1.json`, `_v2`, …). Test that current code reads all of them. Never edit old fixtures. |
| **Round-trip preserves unknowns** | Decode a record with extra fields, modify, encode; assert extras survive (as §4's example does) |
| **Forward-compat fixture** | A hand-written "future" record with unknown fields and enum values; assert the current reader doesn't crash |
| **Schema diff in CI** | `buf breaking`, schema-registry compatibility checks, `openapi-diff` for HTTP APIs |
| **Migration tests against realistic data** | Run migrations on a copy of production-sized, anonymised data; measure lock time and duration |
| **Two-version integration test** | Run version N and N+1 against one database/topic; exercise reads and writes in both directions |
| **Rollback rehearsal** | Deploy N+1 to staging, write data, roll back to N, verify N works |
| **Property tests for upcasters** | Generate random v1 records; assert upcasting yields valid v3 records and preserves invariants (totals, IDs) |

```python
import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures" / "orders"

def test_every_historical_order_format_still_reads():
    files = sorted(FIXTURES.glob("order_v*.json"))
    assert files, "fixtures missing"
    for f in files:
        rec = OrderRecord.from_json(f.read_text())
        assert rec.order_id and rec.total_cents >= 0, f.name
```

---

## 12 · Red flags

| Red flag | Consequence | Fix |
|---|---|---|
| `float` for money | Cents lost or created | Integer minor units / `Decimal` |
| Naive datetimes, or local time stored without zone | Ambiguous instants; DST bugs | UTC instants; zone names for civil times |
| "Just rename the column" in one migration | Old instances break mid-deploy | Expand → migrate → contract |
| Adding `NOT NULL` without default to a live table | Old writers fail; possible table rewrite | Nullable → backfill → enforce |
| One-statement backfill of a huge table | Long locks, replica lag | Batched, throttled, resumable |
| Migration and app deploy in one atomic step | Can't roll back either independently | Separate steps; code tolerates both schemas |
| Strict deserialisation of inter-service messages | Rolling deploy crashes consumers | Tolerant reader |
| Lenient parsing of config | Typos silently ignored | Reject unknown keys |
| Enum parsing that raises on unknown values | New producer value crashes old consumers | Map to `UNKNOWN`, keep raw |
| Decode → modify → encode through a struct | Newer fields silently dropped | Preserve unknowns, or refuse to write newer versions |
| Reusing a protobuf field number or a column name with new meaning | Silent corruption of old data | `reserved`; always new names for new meanings |
| Changing what an existing field means | Every consumer silently wrong | New field |
| `pickle` / unsafe YAML across a trust boundary | Remote code execution | Schema-based formats |
| Cache values without versioned keys | Crashes after deploys and rollbacks | Version in key |
| Soft delete with plain unique constraints | Deleted rows block re-creation | Partial unique index |
| Auto-increment IDs in public URLs | Enumeration and volume leaks | Opaque/random public IDs |

---

## 13 · Interview questions and model answers

**Q: Backward vs. forward compatibility?**
Backward: new code reads data written by old code. Forward: old code reads data written by
new code. Rolling deploys, rollbacks, independent consumers, and old mobile clients mean
most shared data needs both. Additive optional fields with defaults, tolerant readers, and
never changing a field's meaning give you full compatibility.

**Q: How do you rename a column in a live database with no downtime?**
Expand–migrate–contract. Add the new nullable column; deploy code that writes both; backfill
old rows in small batches; deploy code that reads the new column while still dual-writing;
once no old version runs, stop writing the old column; later, drop it. Each step is a
separate deploy so any two adjacent versions work with the schema, and every step except the
final drop can be rolled back.

**Q: How would you store money? Time?**
Money as integer minor units with a currency code, or a decimal type with explicit rounding —
never binary floats — and explicit remainder allocation when splitting. Time: instants in
UTC with a timezone-aware type; user-scheduled wall-clock times as local time plus an IANA
zone name, because offsets change with daylight saving; dates as dates.

**Q: Auto-increment vs. UUID primary keys?**
Auto-increment is compact and index-friendly but needs a central allocator and leaks
volume and guessability if exposed. Random UUIDs can be generated anywhere but scatter
B-tree inserts. Time-ordered IDs like UUIDv7 or ULID give decentralised generation with
good index locality. I'd often use a time-ordered ID internally and never expose sequential
IDs publicly.

**Q: What can go wrong when an old service instance updates a record?**
If it decodes into a struct that doesn't know newer fields and writes the record back, it
silently deletes those fields. Preserve unknown fields on round-trip (protobuf does), keep
raw values of unknown enums, or have old code refuse to write records with a newer schema
version.

**Q: What are the rules for evolving protobuf messages?**
Field numbers are identity: never change or reuse them — reserve removed numbers and names.
Add fields rather than changing types or meanings. Make enum zero `UNSPECIFIED` and handle
unknown enum values. Use `optional` where presence matters. Enforce with `buf breaking` in
CI.

**Q: Soft delete or hard delete?**
Soft delete when you need undo, audit, or referential history — with default-filtered
queries and partial unique indexes. Hard delete (propagated to caches, indexes, and
backups' retention windows) when data must truly be erased, as for GDPR. Soft delete is not
erasure.

---

## 14 · Checklist

**Shapes**
- [ ] Money: integer minor units or decimal, with currency; explicit rounding and remainder allocation.
- [ ] Time: UTC instants; civil times with IANA zones; dates as dates; no naive datetimes.
- [ ] IDs: generated without coordination where needed; opaque in public APIs.
- [ ] Absent vs. null vs. zero is distinguishable where it matters.
- [ ] Defaults for new fields preserve existing behaviour.

**Evolution**
- [ ] Every change is additive or split into additive steps with deploys between them.
- [ ] Readers are tolerant (ignore unknown fields, map unknown enums); config parsing is strict.
- [ ] Unknown fields survive read-modify-write.
- [ ] Stored records carry a version when non-additive changes are possible; upcasters are small and tested.
- [ ] No field ever changes meaning; removed names/numbers are reserved.
- [ ] Cache keys and message types carry versions.

**Migrations**
- [ ] Expand → dual-write → backfill → switch reads → contract.
- [ ] Backfills are batched, throttled, idempotent, and resumable.
- [ ] DDL uses lock timeouts and online variants; no table rewrites on hot tables.
- [ ] Migrations deploy separately from code; both schema states are supported.

**Verification**
- [ ] Golden fixtures of every historical format are read in tests.
- [ ] Schema compatibility is checked in CI.
- [ ] Rollback has been rehearsed.
