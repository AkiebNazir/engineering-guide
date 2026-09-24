# Performance-Aware Design

> "Premature optimization is the root of all evil." — Donald Knuth
>
> The full sentence: "We should forget about small efficiencies, say about 97% of the time:
> premature optimization is the root of all evil. **Yet we should not pass up our
> opportunities in that critical 3%.**"

Knuth's quote is usually used to postpone performance thinking entirely. That's a
misreading. **Micro-optimisation** — hand-tuning loops before profiling — is premature.
**Design decisions** that fix a program's performance ceiling are not: the shape of an
interface (one call per item, or one call per batch), whether data is streamed or loaded,
which data structure backs a hot path, where the cache sits. Those are cheap to get right
while designing and expensive to change once a hundred callers depend on them.

This file is about that 3%: performance as a **design property**, how to reason about it
before measuring, and how to measure it honestly once code exists.

Examples are in **Python** with a **Go** benchmark in §9. Every example was run; timings
are from an Apple-silicon laptop and **will differ on your machine** — the ratios are the
point.

**Already covered elsewhere — not repeated here:**

| Topic | Where |
|---|---|
| Big-O, amortised analysis, hidden costs | `CSFundamentals/07_complexity_analysis_deep_dive.md` |
| Cost of built-in operations per data structure | `CSFundamentals/06_data_structure_internals_deep_dive.md` §9 |
| Profiling tools hands-on (cProfile, pprof, tracing) | `PyEngineering/22_profiling_optimization`, `GoEngineering/22_*`, `35_profiling_and_tracing` |
| GC tuning, GIL, subinterpreters | `GoEngineering/28_scheduler_and_gc_tuning`, `PyEngineering/34_the_gil_and_subinterpreters` |
| Caching tiers, CDN, load balancing, back-of-envelope estimation | `SystemDesign/building_blocks/07`, `11`, `18` |
| Bounded concurrency, single-flight | `07_designing_concurrent_code.md` §9–§10 |
| Latency histograms and percentiles | `10_designing_observable_code.md` §4 |

---

## Contents

1. [Performance is a requirement with a number](#1--performance-is-a-requirement-with-a-number)
2. [Know the cost of things](#2--know-the-cost-of-things)
3. [Interfaces decide performance: chatty vs. batch](#3--interfaces-decide-performance-chatty-vs-batch)
4. [Hidden complexity in innocent lines](#4--hidden-complexity-in-innocent-lines)
5. [Stream, don't load](#5--stream-dont-load)
6. [Caching inside a process](#6--caching-inside-a-process)
7. [Latency is a distribution: tails, fan-out, hedging](#7--latency-is-a-distribution-tails-fan-out-hedging)
8. [Measure honestly: benchmarks and profiles](#8--measure-honestly-benchmarks-and-profiles)
9. [Allocation-aware Go](#9--allocation-aware-go)
10. [Python-specific performance design](#10--python-specific-performance-design)
11. [Trade-offs: when not to optimise](#11--trade-offs-when-not-to-optimise)
12. [Red flags](#12--red-flags)
13. [Interview questions and model answers](#13--interview-questions-and-model-answers)
14. [Checklist](#14--checklist)

---

## 1 · Performance is a requirement with a number

"Make it fast" is not a requirement. A performance requirement names:

| Part | Example |
|---|---|
| **Metric** | Server-side latency of `GET /feed` |
| **Percentile** | p99 (not the mean — §7) |
| **Target** | ≤ 300 ms |
| **Load** | At 5,000 requests/s with 20% cache miss rate |
| **Resources** | On 10 instances of 4 vCPU |

Without a number, optimisation has no stopping point and no priority. With one, you can:

- **Budget latency across components** before writing code:

  ```
  GET /feed   p99 budget 300 ms
  ├── auth token check (local verify)     5 ms
  ├── load follow graph (cache)          20 ms
  ├── fetch candidate posts (fan-out)   150 ms   ← biggest; design this first
  ├── rank (in-process model)            60 ms
  ├── hydrate + serialise                40 ms
  └── headroom                           25 ms
  ```

- **Choose where to spend effort:** optimising the 5 ms auth check is pointless while
  candidate fetch takes 150 ms (Amdahl's law: speeding up a part that takes fraction *p* of
  the time by any amount saves at most *p*).
- **Detect regressions in CI** with benchmark thresholds.

Throughput and latency are different goals and sometimes conflict: batching raises
throughput and adds latency to the first item in the batch; more concurrency raises
throughput until contention makes latency explode (`SystemDesign/building_blocks/12`,
Little's law).

---

## 2 · Know the cost of things

Design-time reasoning needs orders of magnitude, not precision. The classic "latency
numbers every programmer should know" (Jeff Dean, updated for current hardware), rounded:

| Operation | Time | Relative to 1 ns |
|---|---|---|
| L1 cache reference | ~1 ns | 1 |
| Branch mispredict | ~3 ns | 3 |
| Main memory reference | ~100 ns | 100 |
| Python function call / attribute lookup | ~50–100 ns | ~100 |
| Mutex lock/unlock (uncontended) | ~20 ns | 20 |
| Compress 1 KB (Snappy/zstd fast) | ~2 µs | 2,000 |
| Read 1 MB sequentially from memory | ~50 µs | 50,000 |
| SSD random read | ~20–100 µs | 100,000 |
| Round trip within a datacenter | ~500 µs | 500,000 |
| Read 1 MB sequentially from SSD | ~1 ms | 1,000,000 |
| Round trip same region, different zone | ~1–2 ms | 2,000,000 |
| Disk (HDD) seek | ~5–10 ms | 10,000,000 |
| Round trip across a continent | ~50–80 ms | 80,000,000 |
| Round trip transatlantic / transpacific | ~100–150 ms | 150,000,000 |

What to take from it:

- **A network round trip costs as much as ~5,000 in-memory function calls.** The number of
  round trips dominates most service latency. That makes interface shape (§3) the most
  important performance decision in most business code.
- **Memory access patterns matter within a process:** a cache-friendly array scan beats a
  pointer-chasing linked list by large constant factors even at the same Big-O.
- **Python's per-operation overhead is ~50–100× native code.** Pure-Python inner loops over
  millions of items are the wrong design; push the loop into C (built-ins, NumPy, SQL) (§10).

---

## 3 · Interfaces decide performance: chatty vs. batch

An interface that takes **one item per call** forces every caller into a loop of calls. When
that interface is backed by a network or database, the loop becomes **N+1 round trips** — the
most common performance bug in business software.

```python
# The chatty interface: N+1 queries vs. a batch-shaped API. Same result, different design.
import sqlite3
import time


class CountingConnection:
    """Wraps a connection to count round trips — each would be a network hop in production."""
    def __init__(self, conn, latency_s: float = 0.0005):
        self._conn, self.queries, self._latency = conn, 0, latency_s
    def execute(self, sql, params=()):
        self.queries += 1
        time.sleep(self._latency)                      # simulate 0.5 ms network RTT
        return self._conn.execute(sql, params)


def setup() -> CountingConnection:
    raw = sqlite3.connect(":memory:")
    raw.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, total_cents INTEGER)")
    raw.execute("CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT)")
    raw.executemany("INSERT INTO customers VALUES (?, ?)", [(i, f"customer {i}") for i in range(200)])
    raw.executemany("INSERT INTO orders (customer_id, total_cents) VALUES (?, ?)",
                    [(i % 200, 100 + i) for i in range(500)])
    return CountingConnection(raw)


# ---- chatty port: one entity per call ----
class CustomerRepo:
    def __init__(self, db): self.db = db
    def get(self, customer_id: int) -> str:
        return self.db.execute("SELECT name FROM customers WHERE id = ?", (customer_id,)).fetchone()[0]
    def get_many(self, ids: set[int]) -> dict[int, str]:          # batch-shaped port
        if not ids:
            return {}
        marks = ",".join("?" * len(ids))
        rows = self.db.execute(f"SELECT id, name FROM customers WHERE id IN ({marks})", tuple(ids))
        return dict(rows.fetchall())


def report_n_plus_one(db) -> list[tuple[int, str, int]]:
    repo = CustomerRepo(db)
    orders = db.execute("SELECT id, customer_id, total_cents FROM orders ORDER BY id").fetchall()
    return [(oid, repo.get(cid), total) for oid, cid, total in orders]          # 1 + N queries


def report_batched(db) -> list[tuple[int, str, int]]:
    repo = CustomerRepo(db)
    orders = db.execute("SELECT id, customer_id, total_cents FROM orders ORDER BY id").fetchall()
    names = repo.get_many({cid for _, cid, _ in orders})                         # 2 queries
    return [(oid, names[cid], total) for oid, cid, total in orders]


if __name__ == "__main__":
    for fn in (report_n_plus_one, report_batched):
        db = setup()
        t = time.perf_counter()
        rows = fn(db)
        print(f"{fn.__name__:<18} rows={len(rows)} queries={db.queries:<4} {1000 * (time.perf_counter() - t):7.1f} ms")
    a, b = report_n_plus_one(setup()), report_batched(setup())
    assert a == b
    print("ALL PASSED")
```

Output:

```
report_n_plus_one  rows=500 queries=501    386.3 ms
report_batched     rows=500 queries=2        3.5 ms
ALL PASSED
```

Same result, **250× fewer round trips, ~100× faster** — with only 0.5 ms of simulated
latency per query. With a real cross-zone database at 2 ms, the N+1 version takes over a
second.

Design rules:

1. **Offer batch-shaped ports** (`get_many(ids)`, `prices(skus)`, `GetUsers(ids)`) from the
   start — even if the first implementation loops internally. The batch shape can be
   optimised later without touching callers; the single-item shape can't.
2. **Collect, then fetch, then join in memory.** The pattern in `report_batched`.
3. **ORMs hide N+1 behind attribute access** (`order.customer.name` in a loop). Use eager
   loading (`selectinload`/`joinedload` in SQLAlchemy, `select_related`/`prefetch_related`
   in Django) and assert query counts in tests.
4. **Across services, the same rule:** batch endpoints, or a **DataLoader** that coalesces
   individual `load(id)` calls made in the same tick into one batch request (the GraphQL
   solution).
5. **Bound the batch size** (`IN` lists of 100k parameters hit limits and blow query plans):
   chunk into pages of a few hundred to a few thousand.

Other interface shapes that fix performance ceilings:

| Shape | Ceiling it avoids |
|---|---|
| Pagination / cursors on every list endpoint | Unbounded responses, O(n) memory per request |
| Iterators/streams instead of returning lists (§5) | Loading everything before processing anything |
| Field selection / projections (`fields=id,name`, protobuf field masks) | Serialising data nobody reads |
| Async submission + status polling for slow work | Holding a request open for minutes |
| Bulk write APIs (`insert_many`, `COPY`) | One transaction per row |

---

## 4 · Hidden complexity in innocent lines

Most accidental O(n²) algorithms in production are one line that looks O(1).

```python
# Complexity hiding inside innocent-looking lines.
import timeit

n = 20_000
ids = list(range(n))
lookups = list(range(0, n, 7))

as_list, as_set = ids, set(ids)
t_list = timeit.timeit(lambda: sum(x in as_list for x in lookups), number=1)
t_set = timeit.timeit(lambda: sum(x in as_set for x in lookups), number=1)
print(f"membership  list: {t_list * 1000:8.1f} ms   set: {t_set * 1000:6.2f} ms")

emails = [f"user{i % 5000}@x.com" for i in range(n)]
def dedupe_quadratic(items):
    out = []
    for e in items:
        if e not in out:                   # O(len(out)) each time → O(n²)
            out.append(e)
    return out
def dedupe_linear(items):
    return list(dict.fromkeys(items))      # O(n), keeps first-seen order
t_q = timeit.timeit(lambda: dedupe_quadratic(emails), number=1)
t_l = timeit.timeit(lambda: dedupe_linear(emails), number=1)
print(f"dedupe      quadratic: {t_q * 1000:6.1f} ms   linear: {t_l * 1000:6.2f} ms")
assert dedupe_quadratic(emails) == dedupe_linear(emails)

queue = list(range(n))
def drain_list(q):
    q = list(q)
    while q:
        q.pop(0)                           # shifts every element: O(n) per pop
def drain_deque(q):
    from collections import deque
    d = deque(q)
    while d:
        d.popleft()                        # O(1)
t_pop0 = timeit.timeit(lambda: drain_list(queue), number=1)
t_deq = timeit.timeit(lambda: drain_deque(queue), number=1)
print(f"FIFO drain  list.pop(0): {t_pop0 * 1000:6.1f} ms   deque.popleft: {t_deq * 1000:5.2f} ms")
assert t_set < t_list and t_l < t_q and t_deq < t_pop0
print("ALL PASSED")
```

Output:

```
membership  list:     62.6 ms   set:   0.07 ms
dedupe      quadratic:  161.8 ms   linear:   0.44 ms
FIFO drain  list.pop(0):   16.8 ms   deque.popleft:  1.06 ms
ALL PASSED
```

At n = 20,000 these are milliseconds. They're found in production when n reaches a million
and the request takes an hour. A catalogue:

| Innocent line | Actual cost | Replace with |
|---|---|---|
| `x in some_list` inside a loop | O(n) per check | `set` / `dict` |
| `list.pop(0)`, `list.insert(0, x)` | O(n) shift | `collections.deque` |
| `if e not in out: out.append(e)` | O(n²) dedupe | `dict.fromkeys(items)` or a `seen` set |
| `s += piece` in a loop (Python strings, Go strings) | O(n²) copying in general | `"".join(parts)`, `strings.Builder` |
| `sorted(xs)[0]` or `sorted(xs)[:k]` | O(n log n) | `min(xs)`, `heapq.nsmallest(k, xs)` |
| `list(dict.keys())[i]` / `len(list(generator))` | Materialises everything | Iterate once; keep a counter |
| `re.compile` / `json` schema build inside a hot function | Rebuilt per call | Module-level constant |
| `copy.deepcopy(big)` per request "to be safe" | O(size) allocation | Immutable data (`07` §6) |
| `SELECT *` then filtering in Python | Transfers and parses every row | `WHERE` / `LIMIT` in SQL |
| Query in a loop | N round trips | Batch (§3) |
| `COUNT(*)` on a huge table for a badge | Full scan per page view | Maintained counter, approximate count |
| `OFFSET 100000 LIMIT 20` pagination | Database walks and discards 100,000 rows | Keyset/cursor pagination (`WHERE id > last_seen`) |
| Regex with nested quantifiers on user input `(a+)+$` | Exponential backtracking (ReDoS) | Linear-time engine (RE2, Go `regexp`), input limits |

---

## 5 · Stream, don't load

Loading an entire input into memory couples memory use to input size: fine for 10 MB,
an out-of-memory crash at 10 GB. **Streaming** processes one item at a time, so memory is
constant and the first result arrives immediately.

```python
# Streaming vs. loading: same answer, memory O(1) instead of O(n).
import tracemalloc


def lines(n: int):
    for i in range(n):
        yield f"2026-09-17T10:{i % 60:02d}:00Z GET /orders/{i} {200 if i % 50 else 500} {i % 997}ms\n"


def p_errors_loaded(n: int) -> int:
    all_lines = list(lines(n))                              # whole "file" in memory
    parsed = [l.split() for l in all_lines]                 # and a second copy
    return sum(1 for p in parsed if p[3].startswith("5"))


def p_errors_streamed(n: int) -> int:
    parsed = (l.split() for l in lines(n))                  # generator pipeline: one line at a time
    return sum(1 for p in parsed if p[3].startswith("5"))


if __name__ == "__main__":
    n = 200_000
    for fn in (p_errors_loaded, p_errors_streamed):
        tracemalloc.start()
        result = fn(n)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"{fn.__name__:<18} result={result}  peak={peak / 1024:10,.0f} KB")
    assert p_errors_loaded(n) == p_errors_streamed(n) == n // 50
    print("ALL PASSED")
```

Output:

```
p_errors_loaded    result=4000  peak=    99,200 KB
p_errors_streamed  result=4000  peak=         2 KB
ALL PASSED
```

~100 MB versus ~2 KB for 200,000 lines — and the loaded version's memory doubles with each
intermediate list.

Streaming by layer:

| Layer | Loading | Streaming |
|---|---|---|
| Python pipeline | `[f(x) for x in xs]` chained | Generator expressions, `itertools`, `yield` |
| Files | `f.read()`, `f.readlines()` | `for line in f:` |
| CSV / JSON Lines | `list(csv.reader(f))` | Iterate the reader; JSON Lines instead of one huge JSON array |
| Database | `fetchall()` | Server-side cursors, `fetchmany(1000)`, keyset pages |
| HTTP responses | Build full body | Chunked streaming responses, server-sent events |
| HTTP clients | `resp.content` | `resp.iter_content()` / Go `io.Copy` |
| Go | `io.ReadAll`, `os.ReadFile` | `bufio.Scanner`, `io.Reader` composition, `json.Decoder` |

Design implication: **accept iterables / `io.Reader`, not lists / `[]byte`**, in functions
that process collections of unknown size. A function taking `Iterable[Row]` works with a
list in tests and a 50 GB file in production; a function taking `list[Row]` forces loading.

Trade-offs: a stream can be consumed only once, errors can surface midway after partial
output, and some operations (sorting, grouping) need everything in memory or an external
algorithm (external merge sort, a database).

---

## 6 · Caching inside a process

A cache trades memory and staleness for speed. Before adding one, answer: **what is the hit
rate, how stale may data be, how is it invalidated, and what bounds its size?** If any answer
is "not sure", the cache is a future incident.

```python
# Caching pitfalls that turn a speed-up into a leak or a correctness bug.
import gc
import weakref
from functools import lru_cache, cache


# Pitfall 1: lru_cache on a method caches `self` in the key → instances are never freed.
class PriceService:
    def __init__(self, name): self.name = name
    @lru_cache(maxsize=None)
    def price(self, sku: str) -> int:
        return len(sku) * 100

svc = PriceService("request-scoped")
svc.price("A-17")
ref = weakref.ref(svc)
del svc
gc.collect()
print("instance freed after del?", ref() is None)               # False: the cache holds it
assert ref() is not None


# Fix: cache a module-level function of plain values, or a per-instance dict.
class PriceServiceFixed:
    def __init__(self, name):
        self.name = name
        self._prices: dict[str, int] = {}
    def price(self, sku: str) -> int:
        if sku not in self._prices:
            self._prices[sku] = len(sku) * 100
        return self._prices[sku]

svc2 = PriceServiceFixed("request-scoped")
svc2.price("A-17")
ref2 = weakref.ref(svc2)
del svc2
gc.collect()
print("fixed instance freed?   ", ref2() is None)
assert ref2() is None


# Pitfall 2: returning a cached MUTABLE object → one caller's mutation corrupts everyone.
@cache
def default_settings(tenant: str) -> dict:
    return {"currency": "USD", "features": ["search"]}

s = default_settings("t1")
s["features"].append("beta-checkout")                          # caller "customises" its copy...
print("another caller now sees:", default_settings("t1")["features"])
assert "beta-checkout" in default_settings("t1")["features"]


# Fix: cache immutable values.
@cache
def default_settings_fixed(tenant: str) -> tuple[tuple[str, object], ...]:
    return (("currency", "USD"), ("features", ("search",)))


# Pitfall 3: unbounded cache keyed by user input → memory grows without limit.
@lru_cache(maxsize=None)
def render_greeting(name: str) -> str:
    return f"Hello, {name}!"

for i in range(50_000):
    render_greeting(f"visitor-{i}")
print("unbounded cache entries:", render_greeting.cache_info().currsize)
render_greeting.cache_clear()

@lru_cache(maxsize=1024)                                        # bounded: evicts least recently used
def render_greeting_bounded(name: str) -> str:
    return f"Hello, {name}!"
for i in range(50_000):
    render_greeting_bounded(f"visitor-{i}")
print("bounded cache entries:  ", render_greeting_bounded.cache_info().currsize)
assert render_greeting_bounded.cache_info().currsize == 1024
print("ALL PASSED")
```

Output:

```
instance freed after del? False
fixed instance freed?    True
another caller now sees: ['search', 'beta-checkout']
unbounded cache entries: 50000
bounded cache entries:   1024
ALL PASSED
```

Three pitfalls, each common in real code:

1. **`@lru_cache` on a method** puts `self` in the cache key, so every instance ever used
   stays alive for the life of the process — a memory leak for request-scoped objects — and
   instances that compare unequal never share entries. Cache module-level functions of
   plain arguments, or keep a per-instance dict (or `functools.cached_property` for
   zero-argument values).
2. **Returning a cached mutable object** shares it between all callers; one caller's
   modification silently corrupts everyone else's results. Cache immutable values (tuples,
   frozen dataclasses, `MappingProxyType`), or copy on return.
3. **Unbounded caches keyed by user input** grow without limit. Always set `maxsize` (or a
   TTL cache such as `cachetools.TTLCache`), and remember that attacker-controlled keys can
   evict useful entries.

Further rules:

| Rule | Why |
|---|---|
| **Cache at the boundary of expensive work**, as a decorator around a port (`CachingCatalog(catalog)`, `08` §5) | Business logic doesn't know it's cached; tests use the uncached version |
| **Include everything the result depends on in the key** — tenant, locale, feature flags, permissions, schema version (`09` §10) | Otherwise user A sees user B's data |
| **Choose invalidation deliberately:** TTL (simple, bounded staleness), explicit invalidation on write (fresh, easy to miss a path), versioned keys (no deletes needed) | "Two hard things in computer science" |
| **Cache negative results briefly** ("not found") | Otherwise repeated lookups for missing keys bypass the cache |
| **Protect against stampedes:** single-flight, jittered TTLs, serve-stale-while-revalidate (`07` §10) | Synchronised expiry overloads the backend |
| **Measure hit rate** (`10` §4) | A 5% hit-rate cache costs memory and adds a failure mode for nothing |
| **Per-process caches diverge across instances** | Instance A shows the new price, instance B the old one until TTL |

---

## 7 · Latency is a distribution: tails, fan-out, hedging

Users experience the **slow requests**, and systems that fan out experience them far more
often than a single call suggests ("The Tail at Scale", Dean & Barroso, 2013).

```python
# Tail latency: fan-out amplifies it; hedged requests cut it. Deterministic simulation.
import random
import statistics

rng = random.Random(7)


def backend_latency_ms() -> float:
    # 98% fast (~10 ms), 2% slow (GC pause, cold cache, noisy neighbour: ~500 ms)
    return rng.gauss(10, 2) if rng.random() < 0.98 else rng.gauss(500, 100)


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p / 100 * len(xs)))]


def single_call() -> float:
    return backend_latency_ms()


def fan_out(n: int) -> float:
    return max(backend_latency_ms() for _ in range(n))          # page waits for the slowest


def hedged(hedge_after_ms: float = 20) -> float:
    first = backend_latency_ms()
    if first <= hedge_after_ms:
        return first
    second = hedge_after_ms + backend_latency_ms()              # send a backup request at 20 ms
    return min(first, second)


def fan_out_hedged(n: int) -> float:
    return max(hedged() for _ in range(n))


if __name__ == "__main__":
    trials = 20_000
    for name, fn in [("1 call", single_call), ("fan-out 50", lambda: fan_out(50)),
                     ("fan-out 50, hedged", lambda: fan_out_hedged(50))]:
        xs = [fn() for _ in range(trials)]
        print(f"{name:<20} p50={pct(xs, 50):6.1f} ms  p95={pct(xs, 95):6.1f} ms  p99={pct(xs, 99):6.1f} ms  "
              f"mean={statistics.fmean(xs):6.1f} ms")
    slow_share = 1 - 0.98 ** 50
    print(f"P(at least one of 50 calls is slow) = {slow_share:.0%}")
    extra = 0.02                                                # hedges fire only for the slow 2%
    print(f"extra backend load from hedging ≈ {extra:.0%}")
    print("ALL PASSED")
```

Output:

```
1 call               p50=  10.1 ms  p95=  13.7 ms  p99= 501.1 ms  mean=  20.0 ms
fan-out 50           p50= 453.6 ms  p95= 663.5 ms  p99= 731.9 ms  mean= 342.9 ms
fan-out 50, hedged   p50=  29.1 ms  p95=  33.7 ms  p99= 450.3 ms  mean=  33.0 ms
P(at least one of 50 calls is slow) = 64%
extra backend load from hedging ≈ 2%
ALL PASSED
```

Read the numbers:

- A single backend call is fast 98% of the time; its p99 is slow.
- A page that waits for **50** such calls is slow **most** of the time: `1 − 0.98⁵⁰ ≈ 64%`.
  The backend's *p98* has become the page's *median*. At scale, **the tail of the
  component is the typical case of the system.**
- **Hedged requests** — send a backup request if the first hasn't answered within about the
  component's p95 (20 ms here), use whichever returns first — cut the page's median from
  454 ms to 29 ms for ~2% extra backend load. The page p99 is still slow, because in ~2% of
  pages some call is unlucky twice; further gains need other techniques.

Tail-tolerant design techniques:

| Technique | How | Caveat |
|---|---|---|
| **Hedged requests** | Backup request after ~p95 delay; cancel the loser | Only for idempotent reads; adds load |
| **Tied requests** | Send to two replicas; the first to start processing cancels the other | Needs server-side cancellation |
| **Reduce fan-out** | Precompute, denormalise, cache aggregate results | Staleness |
| **Partial results / deadlines** | Return what arrived within the budget (search omits a slow shard) | Product must accept "good enough" |
| **Remove variance at the source** | Separate batch from interactive workloads; tune GC; avoid cold caches (warm up); limit request size | Often the most effective |
| **Timeout budgets** | Per-call timeouts derived from the overall deadline (`06` §6) | Too tight → false failures |

---

## 8 · Measure honestly: benchmarks and profiles

Reasoning chooses the design; **measurement** chooses the optimisation. Intuition about
*where* time goes in existing code is wrong often enough that optimising without a profile
is guessing.

### The loop

```
 1. Define the goal (metric, percentile, load)  ──▶  2. Reproduce with a benchmark or load test
                                                                │
 6. Keep the benchmark as a regression test  ◀──  5. Re-measure  ◀──  4. Change ONE thing
                                                                ▲
                                                3. Profile to find where time/memory actually goes
```

### Tools

| Question | Python | Go |
|---|---|---|
| How long does this function take? | `timeit`, `pyperf`, `pytest-benchmark` | `go test -bench`, `benchstat` |
| Where does CPU time go? | `cProfile` + `snakeviz`; **`py-spy`** (sampling, attach to a live process) | `pprof` CPU profile |
| Where does memory go? | `tracemalloc`, `memray` | `pprof` heap/allocs profile, `-benchmem` |
| Why is it waiting? | `py-spy dump`, asyncio debug mode | `pprof` block/mutex profiles, `go tool trace` |
| Production, continuously | Continuous profilers (Pyroscope, Parca, Google Cloud Profiler) | Same; pprof endpoints |
| Under realistic load? | `locust`, `k6`, `wrk` | Same |

### Benchmarking pitfalls

| Pitfall | Result | Do instead |
|---|---|---|
| One run | Noise mistaken for signal | Many runs; report median and spread; `benchstat` for significance |
| No warm-up | Measures imports, JIT, cold caches | Warm up; discard first iterations |
| Laptop on battery / other apps running | CPU throttling, noisy neighbours | Quiet machine; pin CPU; compare on the same host |
| Tiny inputs | O(n²) looks fine at n = 100 | Benchmark at production sizes, and at 10× |
| Benchmarking the wrong layer | 3× faster function, 0.1% faster request | Profile the whole request first |
| Result unused | Compiler/runtime optimises the work away | Keep results alive (`sink` in §9) |
| Mean only | Tail regressions hidden | Percentiles / distributions |
| Microbenchmark confirms a guess | Confirmation bias | Measure the end-to-end effect too |

---

## 9 · Allocation-aware Go

In Go (and Java, and to a lesser degree Python), **allocation is a hidden cost**: each heap
allocation costs the allocation itself plus garbage-collector work later. Hot paths that
avoid needless allocation are often several times faster.

```go
package main

import (
	"fmt"
	"strconv"
	"strings"
	"testing"
)

// testing.Benchmark runs a benchmark function from main, so this file is self-contained.
// In a real repo these are BenchmarkXxx functions in _test.go files, run with
// `go test -bench=. -benchmem -count=10 | tee new.txt` and compared with benchstat.

const n = 10_000

var sink any // keeps results alive so the compiler can't optimise the work away

func appendGrow(b *testing.B) {
	for b.Loop() {
		var s []int
		for i := range n {
			s = append(s, i)
		}
		sink = s
	}
}

func appendPrealloc(b *testing.B) {
	for b.Loop() {
		s := make([]int, 0, n) // size is known: allocate once
		for i := range n {
			s = append(s, i)
		}
		sink = s
	}
}

func concatPlus(b *testing.B) {
	for b.Loop() {
		s := ""
		for i := range 1_000 {
			s += strconv.Itoa(i) // new string every iteration: O(n²) bytes copied
		}
		sink = s
	}
}

func concatBuilder(b *testing.B) {
	for b.Loop() {
		var sb strings.Builder
		for i := range 1_000 {
			sb.WriteString(strconv.Itoa(i))
		}
		sink = sb.String()
	}
}

func mapGrow(b *testing.B) {
	for b.Loop() {
		m := map[int]int{}
		for i := range n {
			m[i] = i
		}
		sink = m
	}
}

func mapPresized(b *testing.B) {
	for b.Loop() {
		m := make(map[int]int, n)
		for i := range n {
			m[i] = i
		}
		sink = m
	}
}

func main() {
	pairs := []struct {
		name       string
		slow, fast func(*testing.B)
	}{
		{"slice append", appendGrow, appendPrealloc},
		{"string build", concatPlus, concatBuilder},
		{"map insert", mapGrow, mapPresized},
	}
	for _, p := range pairs {
		s, f := testing.Benchmark(p.slow), testing.Benchmark(p.fast)
		fmt.Printf("%-13s %9d ns/op %6d allocs/op  →  %9d ns/op %4d allocs/op  (%.1fx faster)\n",
			p.name, s.NsPerOp(), s.AllocsPerOp(), f.NsPerOp(), f.AllocsPerOp(),
			float64(s.NsPerOp())/float64(f.NsPerOp()))
	}
}
```

Output (Apple silicon, Go 1.24; numbers vary by machine and run):

```
slice append      24349 ns/op     20 allocs/op  →       6303 ns/op    2 allocs/op  (3.9x faster)
string build     126605 ns/op   1900 allocs/op  →      12227 ns/op  912 allocs/op  (10.4x faster)
map insert       251522 ns/op     81 allocs/op  →      78293 ns/op   34 allocs/op  (3.2x faster)
```

What the allocation counts reveal:

- **Slices grow by reallocating and copying** (roughly doubling, then ~1.25× for large
  slices). Pre-sizing when the length is known removes ~18 of 20 allocations; the remaining
  2 are the backing array and boxing the slice into the `any` sink.
- **`s += x` on strings allocates a new string every time.** `strings.Builder` removes most
  of that; the ~900 remaining allocations come from `strconv.Itoa` itself (Go caches small
  integers below 100 only) — a profile would point there next, and `strconv.AppendInt` into
  a reused `[]byte` removes them too.
- **Maps grow in steps** that rehash; a size hint avoids most of them.

Other Go allocation sources to recognise:

| Source | Example | Avoid when hot |
|---|---|---|
| **Escape to heap** | Returning a pointer to a local; storing it in an interface or closure | `go build -gcflags=-m` shows escape decisions |
| **Interface boxing** | Passing a non-pointer value as `any` (e.g. `fmt.Sprintf("%d", n)` args) | Concrete types / `strconv` on hot paths |
| **`[]byte` ↔ `string` conversions** | `string(buf)` per line | Work in `[]byte`; compiler optimises some map lookups `m[string(b)]` |
| **Closures capturing variables** | Goroutine per item capturing large state | Pass values explicitly |
| **`defer` in tight loops** | (Cheap since Go 1.14, but per-iteration defers accumulate until return) | Extract the loop body into a function |
| **Temporary buffers per request** | `make([]byte, 64<<10)` per call | `sync.Pool` for large, short-lived, frequently allocated buffers — after profiling |

Rule: **don't write allocation-golfed code by default.** Pre-size slices when the size is
obviously known (it's free clarity), use `strings.Builder` for loops, and leave the rest
until `pprof -alloc_space` says a path is hot.

---

## 10 · Python-specific performance design

Python's interpreter overhead per bytecode is large; its built-ins and C-backed libraries
are fast. Performance design in Python is mostly about **moving loops out of Python**.

| Instead of | Use | Typical speed-up |
|---|---|---|
| Python loop summing/filtering numbers | `sum`, `min`, `max`, `any`, `sorted` with `key`, comprehensions | 2–10× |
| Python loops over numeric arrays | NumPy vectorised operations | 10–100× |
| Row-by-row data processing in Python | Polars / pandas / DuckDB, or SQL in the database | 10–100× |
| Manual counting / grouping | `collections.Counter`, `defaultdict`, `itertools.groupby` | 2–5× |
| Repeated attribute/global lookups in a hot loop | Local variable binding (only after profiling) | 10–30% |
| Many small objects | `__slots__` / `@dataclass(slots=True)` — less memory, faster attribute access | Memory 40–60% less |
| `json` for large payloads | `orjson` / `msgspec` | 3–10× |
| CPU-bound work in threads | Processes, native extensions that release the GIL, or free-threaded 3.13t (`07` §13) | Scales with cores |
| Hot inner algorithm in pure Python | Cython, mypyc, Rust via PyO3 — as a last step | 10–100× |

Design rules:

- **Data-oriented shapes beat object graphs for bulk data.** A million `Point` objects cost
  ~100+ bytes each and pointer-chasing; two NumPy arrays of floats cost 8 bytes per value
  and are processed in C.
- **Let the database do set operations.** Joins, aggregates, and filters in SQL avoid moving
  data into Python at all.
- **asyncio helps I/O concurrency, not CPU.** Async code is not faster per request; it
  handles more concurrent waiting requests per process.
- **Import time is latency** for CLIs and serverless cold starts: `python -X importtime`;
  import heavy modules lazily.

---

## 11 · Trade-offs: when not to optimise

Every optimisation costs something. Name the cost before paying it.

| Optimisation | Usually costs |
|---|---|
| Caching | Staleness, memory, invalidation bugs, cross-tenant leak risk |
| Batching | Latency for the first item; partial-failure handling |
| Denormalisation / precomputation | Write-path complexity; consistency between copies |
| Concurrency / parallelism | Races, harder debugging (`07`) |
| Hand-written low-level code | Readability; portability; correctness risk |
| Specialised data structures | Maintenance; fewer people understand them |
| Removing abstraction layers | Coupling (`01`, `03`) |

**Don't optimise** when:

- There is no number it needs to meet, or it already meets it.
- A profile hasn't shown it's significant (it's < 5% of the time).
- It's a one-off script, a rarely used admin path, or a prototype.
- A higher-level change (better algorithm, batching, a cache in front, removing the work) is
  available — those beat micro-tuning by orders of magnitude.

**Do design for performance up front** when:

- The interface shape determines round trips (§3).
- Data volume will grow by orders of magnitude (streaming, pagination, indexes).
- The code is a shared library or hot core path used by many teams.
- The decision is expensive to reverse (data model, storage engine, sync vs. async API).

Readable code that is fast enough beats clever code that is slightly faster. When an
optimisation does make code harder to read, **leave a comment with the measurement** that
justified it — so the next engineer doesn't "simplify" it back.

---

## 12 · Red flags

| Red flag | Problem | Fix |
|---|---|---|
| Database/HTTP call inside a loop | N+1 round trips | Batch-shaped port (§3) |
| Single-item-only repository/client interfaces | Forces N+1 on every caller | Add `get_many` |
| `fetchall()` / `readlines()` / `io.ReadAll` on unbounded input | Memory proportional to input | Stream (§5) |
| List endpoints without pagination | Unbounded response size and time | Cursor pagination |
| `in list`, `pop(0)`, dedupe-by-scan in hot code | Accidental O(n²) | Sets, deques, dicts (§4) |
| `@lru_cache` on methods | Leaks instances | Module-level function or per-instance dict |
| Cache with no size bound, TTL, or hit-rate metric | Memory leak; unknown value | §6 |
| Cache key missing tenant/locale/permissions | Data leaks between users | Include every input |
| Mean latency as the target | Tails ignored | p95/p99 targets (§7) |
| "Optimised" code with no benchmark or comment | Unverifiable; later reverted | Keep the benchmark; comment the measurement |
| Benchmark run once on a laptop | Noise | Repeated runs + `benchstat` / `pyperf` |
| `OFFSET` pagination on large tables | Linear scan per page | Keyset pagination |
| CPU-bound work in asyncio or Python threads | No speed-up; blocked event loop | Processes / native code |
| Micro-optimising before profiling | Effort in the wrong 97% | Profile first |

---

## 13 · Interview questions and model answers

**Q: What does "premature optimisation" mean to you?**
Tuning code for speed before knowing it matters — without a target or a profile. It doesn't
mean ignoring performance in design: interface shape, data model, streaming versus loading,
and algorithmic complexity set the ceiling and are expensive to change later, so I decide
those deliberately up front and micro-optimise only what profiles show is hot.

**Q: What is the N+1 query problem and how do you prevent it?**
Fetching a list with one query and then related data with one query per item — N+1 round
trips. Prevent it with batch-shaped interfaces (`get_many`), eager loading in the ORM, a
DataLoader that coalesces lookups, and tests that assert query counts.

**Q: Your service's p99 latency is bad but the mean is fine. What do you do?**
Look at what the slow requests have in common with traces and exemplars — a specific
dependency, request size, tenant, instance, or GC pauses. If the service fans out, tail
amplification is likely: reduce fan-out, set per-call deadlines, return partial results, or
hedge idempotent reads after about the p95. Also remove variance at the source: separate
batch traffic, warm caches, and tune GC.

**Q: How do you benchmark correctly?**
Define the metric and workload, warm up, run many iterations on a quiet machine, compare
distributions with a statistical tool like benchstat or pyperf, use production-sized inputs,
make sure results are used so they aren't optimised away, and verify that the micro gain
shows up end to end. Keep the benchmark to catch regressions.

**Q: When would you add a cache, and what could go wrong?**
When a read is expensive, repeated, and can tolerate some staleness — after measuring the
cost and the likely hit rate. Things that go wrong: stale data without clear invalidation,
unbounded growth, keys that omit tenant or permissions and leak data, stampedes on expiry,
caching mutable objects, and inconsistency between instances. I'd bound it, add TTL or
explicit invalidation, single-flight loads, and monitor the hit rate.

**Q: Why does a function accepting `Iterable` instead of `list` matter?**
It lets the same code process a small in-memory list in tests and a stream larger than memory
in production, with constant memory and the first results available immediately. Accepting a
list forces every caller to load everything first.

**Q: How would you speed up a slow Python data-processing job?**
Profile first. Usually the fix is moving loops out of Python: push filtering and aggregation
into SQL or a columnar engine like Polars or DuckDB, vectorise numerics with NumPy, stream
instead of loading, and batch I/O. For CPU-bound Python that remains, use multiple processes;
compile the hottest kernel with Cython or Rust only as a last step.

---

## 14 · Checklist

**Requirements**
- [ ] Performance targets name a metric, percentile, number, and load.
- [ ] A latency budget exists for multi-step requests.

**Design**
- [ ] Ports that may be backed by I/O offer batch operations.
- [ ] Collections of unknown size are streamed; list endpoints are paginated with cursors.
- [ ] Hot paths use appropriate data structures; no accidental O(n²).
- [ ] Fan-out is bounded, deadlines propagate, and tail-latency techniques are considered.
- [ ] Heavy numeric/data work runs in native code or the database, not Python loops.

**Caching**
- [ ] Each cache has a size bound, invalidation strategy, complete key, and hit-rate metric.
- [ ] Cached values are immutable; stampede protection is in place for hot keys.

**Measurement**
- [ ] Optimisations are driven by profiles, not intuition.
- [ ] Benchmarks use realistic sizes, repeated runs, and statistical comparison.
- [ ] Justifying measurements are recorded in comments or benchmarks kept in the repo.
- [ ] Query counts and key benchmarks are guarded in tests/CI.
