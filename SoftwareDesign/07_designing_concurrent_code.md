# Designing Concurrent Code

> "Do not communicate by sharing memory; instead, share memory by communicating."
> — Go Proverbs
>
> "Writing correct programs is hard; writing correct concurrent programs is harder."
> — Brian Goetz, *Java Concurrency in Practice*

`CSFundamentals/05` teaches the **primitives**: mutexes, condition variables,
semaphores, deadlock conditions. This file is about **design**: how to structure
classes, APIs, and programs so that concurrency bugs are hard to write in the first
place — and how to prove the design works.

The central idea: **concurrency bugs come from shared mutable state.** Every technique
here either removes one of those three words — don't *share*, don't *mutate*, or
control *state* access so that only one party changes it at a time — or makes the
unavoidable remainder small, private, and obvious.

Examples are in **Python** (threads and asyncio) and **Go**. Every example was run;
outputs shown are real. The Go example passes `go run -race`.

**Already covered elsewhere — not repeated here:**

| Topic | Where |
|---|---|
| Primitives, Coffman conditions, bounded blocking queue, Go worker pool | `CSFundamentals/05_concurrency_deep_dive.md` |
| Making LRU/rate limiter/hash map thread-safe (table) | `CSFundamentals/05` §7 |
| Concurrency toolkit for LLD interviews (locking options table) | `14_low_level_design_interview_playbook.md` §9 |
| Timeouts, deadlines, cancellation, `CancelledError` | `06_error_handling_and_failure_design.md` §6 |
| Optimistic concurrency and DB-level locking | `PyEngineering/10_transactions_concurrency_control`, `SystemDesign/building_blocks/11` |
| Runnable concurrent cache, pipeline, pub/sub, asyncio internals, GIL | `PyEngineering/12–16`, `26`, `27`, `33`, `34`; `GoEngineering/12–16`, `26`, `31` |

---

## Contents

1. [Thread safety is a property of a contract](#1--thread-safety-is-a-property-of-a-contract)
2. [The four strategies: confine, freeze, guard, serialise](#2--the-four-strategies-confine-freeze-guard-serialise)
3. [Designing a thread-safe class](#3--designing-a-thread-safe-class)
4. [APIs that make races impossible to write](#4--apis-that-make-races-impossible-to-write)
5. [Never call unknown code while holding a lock](#5--never-call-unknown-code-while-holding-a-lock)
6. [Immutability and snapshots](#6--immutability-and-snapshots)
7. [Single writer: the actor model](#7--single-writer-the-actor-model)
8. [async/await is concurrency too](#8--asyncawait-is-concurrency-too)
9. [Structured concurrency](#9--structured-concurrency)
10. [Single-flight: collapsing duplicate work](#10--single-flight-collapsing-duplicate-work)
11. [The same design choices in Go](#11--the-same-design-choices-in-go)
12. [Testing concurrent code](#12--testing-concurrent-code)
13. [Choosing a model: threads, processes, asyncio, goroutines](#13--choosing-a-model-threads-processes-asyncio-goroutines)
14. [Red flags](#14--red-flags)
15. [Interview questions and model answers](#15--interview-questions-and-model-answers)
16. [Checklist](#16--checklist)

---

## 1 · Thread safety is a property of a contract

"Is this class thread-safe?" has no yes/no answer without saying **which operations,
used how**. A `dict` in CPython won't corrupt itself under concurrent `d[k] = v`, yet this
is still a race:

```python
if key not in cache:          # thread A checks: absent     thread B checks: absent
    cache[key] = compute()    # A computes and stores       B computes and overwrites
```

Every individual operation was "safe". The **sequence** was not, because the invariant
("compute each key once") spans two operations.

Definitions to use precisely:

| Term | Meaning |
|---|---|
| **Race condition** | Correctness depends on the relative timing of threads |
| **Data race** | Two threads access the same memory concurrently, at least one writes, no synchronisation. Undefined behaviour in Go/C++; Go's `-race` detects it |
| **Atomic** | Indivisible from the point of view of other threads — they see before or after, never in between |
| **Invariant** | A condition over the state that must hold whenever another thread can observe it |
| **Critical section** | Code that must run without interference to keep an invariant |

So a thread-safety contract is stated as: **"these operations are atomic; these
invariants hold between them; these combinations are *not* atomic."** Document it —
`Go`'s standard library does ("A Map is safe for concurrent use by multiple goroutines
without additional locking"), and Python's `queue.Queue` does.

Levels worth naming (from Goetz / Bloch):

| Level | Meaning | Examples |
|---|---|---|
| **Immutable** | No synchronisation needed, ever | `str`, `tuple`, `frozenset`, frozen dataclasses of immutables |
| **Thread-safe** | Every public method is atomic; no external locking needed for single calls | `queue.Queue`, Go `sync.Map`, `atomic.Int64` |
| **Conditionally thread-safe** | Some sequences need external locking | Iterating a synchronised collection while others modify it |
| **Not thread-safe** | Caller must synchronise all access | `list`, `dict` for compound use, Go `map`, most classes |
| **Thread-confined** | Must only be used from one thread | Tkinter/GUI objects, `sqlite3.Connection` by default, asyncio objects outside their loop |

---

## 2 · The four strategies: confine, freeze, guard, serialise

Ordered from "fewest bugs" to "most bugs". Reach for the earliest one that fits.

| Strategy | Idea | Python | Go | Cost |
|---|---|---|---|---|
| **1. Confine** — don't share | Each thread/task owns its own data; results are merged at the end | Per-task local variables; pass copies; `threading.local` | Data stays in one goroutine; pass ownership via channel | Merge step; copying |
| **2. Freeze** — don't mutate | Share only immutable values; "change" by building a new value and swapping a reference | frozen dataclasses, tuples, `MappingProxyType` | Values not pointers; copy-on-write + `atomic.Pointer` | Allocation per change |
| **3. Guard** — synchronise | Mutable shared state behind a lock that protects the invariant | `threading.Lock`, `asyncio.Lock` | `sync.Mutex`, `RWMutex`, `atomic` | Contention, deadlock risk, easy to forget |
| **4. Serialise** — single writer | One thread/goroutine owns the state; everyone else sends it messages | a thread + `queue.Queue` | goroutine + channels | Throughput of one worker; request/reply plumbing |

```
                 Is the data shared between threads at all?
                  │
          no ─────┴───── yes
          │               │
      CONFINE      Does it change after creation?
                          │
                  no ─────┴───── yes
                  │               │
               FREEZE     Is it read far more often than written,
                          and is copying it cheap?
                                  │
                          yes ────┴──── no
                          │              │
                   FREEZE + swap   Is the logic a state machine / sequence
                   (§6)            of steps, or does it own I/O?
                                         │
                                 yes ────┴──── no
                                 │              │
                            SERIALISE        GUARD
                            (actor, §7)      (lock, §3)
```

Two observations:

- **Most concurrency in well-designed services is strategy 1.** A web request's
  objects are created, used, and discarded inside one request. Shared state is a small
  set of long-lived objects — pools, caches, counters, config — and each gets an explicit
  strategy.
- **Mixing strategies is normal**: a cache that is guarded by a lock, whose *values*
  are immutable, whose loading is single-flighted (§10).

---

## 3 · Designing a thread-safe class

The smallest version of the problem: a counter incremented by several threads.

```python
# Simplest on-ramp: read-then-write on shared state loses updates unless it's one atomic step.
import threading, time

def bump_many(counter, key, n, lock=None):
    for _ in range(n):
        if lock:
            with lock:
                v = counter[key]
                time.sleep(0)          # force a thread switch between read and write
                counter[key] = v + 1
        else:
            v = counter[key]
            time.sleep(0)
            counter[key] = v + 1

counter = {"n": 0}
threads = [threading.Thread(target=bump_many, args=(counter, "n", 2_000)) for _ in range(4)]
for t in threads: t.start()
for t in threads: t.join()
print("without a lock:", counter["n"], "(expected 8000)")

counter = {"n": 0}
lock = threading.Lock()
threads = [threading.Thread(target=bump_many, args=(counter, "n", 2_000, lock)) for _ in range(4)]
for t in threads: t.start()
for t in threads: t.join()
print("with a lock:", counter["n"])
```

Output:

```
without a lock: 2002 (expected 8000)
with a lock: 8000
```

Without a lock, "read the value, then write value+1" is two separate steps, and the
forced switch between them loses most updates. With the lock, the read and the write
happen as one step as far as any other thread can see, and the count comes out exact.
(The exact number without a lock varies slightly between runs; that it's far short of
8000 does not. This example forces the interleaving with `time.sleep(0)` to make it fail
every time — the *natural* version of this race is much harder to trigger reliably, which
is exactly why §12 builds a deterministic reproduction technique instead of just running
threads and hoping.)

The **monitor** pattern scales this to a real object: private state, a private lock, and
every public method acquires the lock for its whole critical section.

```python
# A thread-safe class: one private lock guards one invariant; compound actions are methods.
import threading
from concurrent.futures import ThreadPoolExecutor


class InsufficientFunds(Exception): ...


class Account:
    def __init__(self, account_id: int, balance: int):
        self.id = account_id
        self._balance = balance
        self._lock = threading.Lock()          # private: nobody else can hold it (or forget to)

    @property
    def balance(self) -> int:
        with self._lock:                       # reads of multi-word state need the lock too
            return self._balance

    def withdraw(self, amount: int) -> None:
        with self._lock:                       # check AND act inside one critical section
            if amount > self._balance:
                raise InsufficientFunds(self.id)
            self._balance -= amount

    def deposit(self, amount: int) -> None:
        with self._lock:
            self._balance += amount


def transfer(src: Account, dst: Account, amount: int) -> None:
    if src is dst:
        return
    first, second = sorted((src, dst), key=lambda a: a.id)   # global lock order → no deadlock
    with first._lock, second._lock:            # both locks: no moment where money is "in flight"
        if amount > src._balance:
            raise InsufficientFunds(src.id)
        src._balance -= amount
        dst._balance += amount


if __name__ == "__main__":
    a, b = Account(1, 1_000), Account(2, 1_000)

    def churn(i: int):
        # Half the transfers go a→b, half b→a: opposite lock orders WITHOUT the sort → deadlock.
        for _ in range(2_000):
            try:
                transfer(a, b, 3) if i % 2 else transfer(b, a, 3)
            except InsufficientFunds:
                pass

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(churn, range(8)))

    print("total after 16,000 concurrent transfers:", a.balance + b.balance)
    assert a.balance + b.balance == 2_000        # conservation holds under contention
    print("ALL PASSED")
```

Output:

```
total after 16,000 concurrent transfers: 2000
ALL PASSED
```

Design rules the example encodes:

1. **One lock per invariant, owned by the object that owns the invariant.** `Account`'s
   lock protects `_balance >= 0`. The lock is private (`_lock`) so no outside code can
   forget to take it or hold it too long.
2. **Check and act in the same critical section.** `withdraw` checks the balance and
   subtracts under one `with`.
3. **Reads take the lock too** when the value is not a single atomic reference or when
   they must see a consistent state across fields. In Go, *any* unsynchronised read of a
   concurrently written variable is a data race.
4. **Invariants across objects need all their locks** — `transfer` holds both, so no
   observer ever sees money that has left `a` but not arrived in `b` (sum ≠ 2000).
5. **Acquire multiple locks in a global order** (here, by account ID). Without the
   `sorted`, one thread does a→b (locks 1 then 2) while another does b→a (locks 2 then 1)
   — the classic deadlock.
6. **Keep critical sections short and free of I/O** (§5).
7. **Don't leak references to guarded state.** Returning `self._items` (a live list) lets
   callers mutate it without the lock. Return a copy, a tuple, or an immutable view.

**Python-specific:** the GIL does not make your code thread-safe. It makes single
bytecodes atomic, and switches threads *between* them; `self.value += 1` is several
bytecodes (load, add, store). Free-threaded CPython (PEP 703, `python3.13t`) removes the
GIL entirely, so code that "worked because of the GIL" will break there first.

**Granularity**, when one lock becomes a bottleneck:

| Technique | When | Watch out |
|---|---|---|
| One coarse lock | Default. Measure before changing. | Contention under load |
| Lock striping (N shards, hash key → shard lock) | Independent keys, e.g. per-user state | Cross-shard operations need ordered multi-locking |
| Read-write lock | Reads vastly outnumber writes *and* read sections are long | Often *slower* than a mutex for short sections; writer starvation |
| Per-entity locks | Entities are independent (seats per show) | Lock table itself needs protection; memory for idle locks |
| Lock-free / atomics | Single counters/flags; measured hot spots | Hard to extend beyond one variable; ABA problems |

---

## 4 · APIs that make races impossible to write

The best fix for a check-then-act race is an <abbr title="Application Programming Interface">API</abbr> that **doesn't let callers write the
check and the act separately**. Give them the compound operation.

| Racy <abbr title="Application Programming Interface">API</abbr> (caller composes) | Atomic <abbr title="Application Programming Interface">API</abbr> (object composes) |
|---|---|
| `if k not in m: m[k] = v` | `m.setdefault(k, v)`, Go `sync.Map.LoadOrStore` |
| `v = m.get(k); m[k] = v + 1` | `counter.increment(k)`, `atomic.AddInt64` |
| `if q.size() > 0: q.pop()` | `q.get(timeout=…)` / `q.get_nowait()` raising `Empty` |
| `if seat.is_free(): seat.book(u)` | `seat.try_book(u) -> bool` |
| `if balance >= x: withdraw(x)` | `withdraw(x)` raising `InsufficientFunds` |
| `if not os.path.exists(p): open(p, "w")` | `open(p, "x")` (exclusive create; the OS does it atomically) |
| `SELECT … ; UPDATE … ` | `UPDATE … WHERE version = ?` / `INSERT … ON CONFLICT DO NOTHING` |

**Rule: a thread-safe object's methods should be whole business operations, not
getters and setters.** Getters+setters on a shared object push the invariant — and the
race — into every caller. This is "tell, don't ask" (`02` §9) with correctness stakes.

The last two rows are the same idea outside your process: filesystems and databases
offer atomic compound operations; use them instead of checking first.

---

## 5 · Never call unknown code while holding a lock

"Unknown code" (Goetz calls it *alien* methods): callbacks, listeners, overridable methods,
anything passed in, logging handlers, and any I/O.

Why:

- **Deadlock:** the callback may try to take a lock that another thread holds while
  waiting for *your* lock — or call back into your object (`threading.Lock` is not
  re-entrant; a re-entrant call deadlocks the thread against itself).
- **Latency:** a slow listener or network call holds everyone else up.
- **Invariants exposed mid-update:** the callback observes (or mutates) state while it
  is inconsistent.

```python
# ✗ BAD: listeners run while holding the lock.
class Observable:
    def set(self, value):
        with self._lock:
            self._value = value
            for listener in self._listeners:
                listener(value)            # may block, raise, or call self.set() → deadlock

# ✓ GOOD: change state and snapshot the listeners under the lock; call them outside it.
class Observable:
    def __init__(self):
        self._lock = threading.Lock()
        self._value = None
        self._listeners: tuple = ()        # immutable: replaced, never mutated

    def subscribe(self, fn):
        with self._lock:
            self._listeners = self._listeners + (fn,)

    def set(self, value):
        with self._lock:
            self._value = value
            listeners = self._listeners    # snapshot
        for listener in listeners:         # outside the lock
            listener(value)
```

**Open calls** — calls made with no locks held — are the single most effective
deadlock-prevention habit. If a design requires calling out under a lock, that's a signal
to switch to an actor (§7), where the "lock" is a queue and callbacks become messages.

---

## 6 · Immutability and snapshots

Immutable objects need no synchronisation: every thread can read them forever — there is
nothing to protect, because nothing can change.

```python
# Simplest on-ramp: an immutable value literally cannot be corrupted by concurrent code.
point = (3, 4)
try:
    point[0] = 99
except TypeError as e:
    print("tuples are immutable:", e)

from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: int
    y: int

p = Point(3, 4)
try:
    p.x = 99
except Exception as e:
    print("frozen dataclass is immutable:", type(e).__name__, e)
```

Output:

```
tuples are immutable: 'tuple' object does not support item assignment
frozen dataclass is immutable: FrozenInstanceError cannot assign to field 'x'
```

No thread can ever observe `point` or `p` half-updated, because there is no operation
that updates them at all — "changing" one means building a new value. For data that is
**read constantly and changed rarely** — configuration, feature flags, routing tables,
permission sets — scale that idea up with **copy-on-write and a reference swap**:

```python
# Immutable snapshot + atomic reference swap: lock-free reads of hot, rarely-changing data.
import threading
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class RoutingTable:
    version: int
    routes: MappingProxyType          # read-only view: the snapshot cannot be mutated


class Router:
    def __init__(self):
        self._table = RoutingTable(0, MappingProxyType({}))
        self._write_lock = threading.Lock()          # serialises WRITERS only

    def lookup(self, prefix: str) -> str | None:
        table = self._table                          # one reference read: a consistent snapshot
        return table.routes.get(prefix)

    def update(self, changes: dict[str, str]) -> int:
        with self._write_lock:
            old = self._table
            new_routes = dict(old.routes)            # copy
            new_routes.update(changes)               # modify the copy
            self._table = RoutingTable(old.version + 1, MappingProxyType(new_routes))  # publish
            return self._table.version


if __name__ == "__main__":
    r = Router()
    r.update({"/api": "svc-a", "/img": "svc-b"})
    snapshot = r._table
    r.update({"/api": "svc-c"})
    print(r.lookup("/api"), snapshot.routes["/api"], r._table.version)
    assert r.lookup("/api") == "svc-c" and snapshot.routes["/api"] == "svc-a"
    try:
        snapshot.routes["/api"] = "hacked"
    except TypeError as e:
        print("snapshot is read-only:", e)
    print("ALL PASSED")
```

Output:

```
svc-c svc-a 2
snapshot is read-only: 'mappingproxy' object does not support item assignment
ALL PASSED
```

How it works:

- **Readers take no lock.** Reading `self._table` is a single reference load; each
  reader gets a complete, consistent table — never half an update.
- **Writers copy, modify the copy, then publish** by assigning the reference. The write
  lock only stops two writers from losing each other's updates.
- **Old snapshots stay valid** for whoever holds them (the in-flight request routed with
  version 1 finishes with version 1).
- In Go, use `atomic.Pointer[RoutingTable]` for the swap: an unsynchronised pointer write
  is a data race there, even though it "works" most of the time.
- The immutability must be **deep**. A frozen dataclass holding a regular `dict` is not
  immutable — anyone can mutate the dict.

Cost: a full copy per write. Fine for a table changed a few times a minute; wrong for a
counter incremented a thousand times a second. (Persistent data structures — structural
sharing, as in Clojure or `pyrsistent` — reduce the copy to O(log n).)

---

## 7 · Single writer: the actor model

Instead of many threads locking shared state, **one thread owns the state and processes
messages one at a time.** No locks around the state at all — sequential code, sequentially
correct.

The smallest version: one thread owns a plain list, everyone else sends it messages
through a queue instead of touching the list directly.

```python
# Simplest on-ramp: one thread owns a plain list; everyone else sends it messages through a queue.
import queue, threading

inbox = queue.Queue()
log = []

def owner():
    while (msg := inbox.get()) is not None:
        log.append(msg)          # only this thread ever touches `log`

t = threading.Thread(target=owner)
t.start()
for i in range(5):
    inbox.put(f"event-{i}")
inbox.put(None)                  # poison pill: stop
t.join()
print(log)
```

Output:

```
['event-0', 'event-1', 'event-2', 'event-3', 'event-4']
```

No lock guards `log` because nothing needs to: only `owner` ever reads or writes it, so
there is no concurrent access to synchronise. Scaled up, the same idea gives callers
replies and the actor a richer internal state instead of a bare list:

```python
# Single writer (actor): one thread owns the state; others send messages and get futures back.
import queue
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass


@dataclass
class Reserve:
    seat: str
    user: str
    reply: Future


@dataclass
class Snapshot:
    reply: Future


class SeatMapActor:
    def __init__(self, seats: list[str]):
        self._owner: dict[str, str | None] = {s: None for s in seats}   # touched ONLY by _run
        self._inbox: queue.Queue = queue.Queue(maxsize=1_000)          # bounded: backpressure
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    # ---- public API: any thread may call; nothing here touches self._owner ----
    def reserve(self, seat: str, user: str) -> Future:
        fut: Future = Future()
        self._inbox.put(Reserve(seat, user, fut))
        return fut

    def snapshot(self) -> dict[str, str | None]:
        fut: Future = Future()
        self._inbox.put(Snapshot(fut))
        return fut.result()

    def stop(self) -> None:
        self._inbox.put(None)
        self._thread.join()

    # ---- the only code that reads or writes state: sequential, so no locks ----
    def _run(self) -> None:
        while (msg := self._inbox.get()) is not None:
            match msg:
                case Reserve(seat, user, reply):
                    if seat not in self._owner:
                        reply.set_exception(KeyError(seat))
                    elif self._owner[seat] is None:
                        self._owner[seat] = user
                        reply.set_result(True)
                    else:
                        reply.set_result(False)
                case Snapshot(reply):
                    reply.set_result(dict(self._owner))           # a copy, never the live dict


if __name__ == "__main__":
    actor = SeatMapActor(["A1", "A2"])
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(lambda u=u: actor.reserve("A1", f"user{u}").result())
                   for u in range(50)]
        wins = sum(f.result() for f in futures)
    snap = actor.snapshot()
    actor.stop()
    print("winners:", wins, snap)
    assert wins == 1 and snap["A1"] is not None and snap["A2"] is None
    print("ALL PASSED")
```

Output:

```
winners: 1 {'A1': 'user0', 'A2': None}
ALL PASSED
```

(Which user wins varies between runs; that exactly one wins does not.)

Properties:

| Aspect | Actor | Lock |
|---|---|---|
| Correctness reasoning | Sequential: the handler is ordinary single-threaded code | Must reason about every interleaving of every method |
| Deadlock | Not from state access; can still deadlock if actors wait synchronously on each other in a cycle | Lock ordering required |
| Throughput | One worker per actor — shard into several actors (per show, per user) to scale | Parallel readers/writers possible |
| Latency | Queueing delay | Contention delay |
| Backpressure | Natural: bounded inbox (`maxsize`) blocks or rejects senders | None built in |
| Fits | State machines (elevator controller, order matching engine, game loop), anything owning a connection or device | Small shared structures (counters, caches) |

Design details in the example:

- **The public <abbr title="Application Programming Interface">API</abbr> never touches state** — it only enqueues messages. That makes the
  thread-safety contract trivial to audit.
- **Replies travel back through a `Future`**, so callers can wait with a timeout.
- **Snapshots are copies**, never the live dict.
- **The inbox is bounded** — an unbounded queue in front of a slow actor is an
  out-of-memory incident waiting to happen.
- **Shutdown is a message** (`None` poison pill), processed in order after pending work.

This is the design behind Erlang/Akka actors, Go's "share memory by communicating",
Redis's single-threaded command loop, Node.js's event loop, and LMAX Disruptor's single
business-logic thread — all of which get high throughput precisely *because* the core has
no locks.

---

## 8 · async/await is concurrency too

A single-threaded asyncio program has no data races — but it still has **race
conditions**. Every `await` is a point where other coroutines run, so any check-then-act
spanning an `await` is racy:

```python
# A race that needs no threads: every `await` is a point where other coroutines run.
import asyncio


class Wallet:
    def __init__(self, balance: int):
        self.balance = balance
        self._lock = asyncio.Lock()

    async def _fraud_check(self) -> None:
        await asyncio.sleep(0)                 # any await: a DB call, an HTTP call, a log flush

    async def pay_racy(self, amount: int) -> bool:
        if self.balance >= amount:             # check
            await self._fraud_check()          # ← other coroutines run here
            self.balance -= amount             # act on a stale check
            return True
        return False

    async def pay_safe(self, amount: int) -> bool:
        async with self._lock:                 # held across the await
            if self.balance >= amount:
                await self._fraud_check()
                self.balance -= amount
                return True
            return False


async def main():
    w = Wallet(100)
    results = await asyncio.gather(*(w.pay_racy(80) for _ in range(3)))
    print("racy:", results, "balance:", w.balance)
    assert w.balance == -140                   # three payments of 80 from 100, deterministically

    w = Wallet(100)
    results = await asyncio.gather(*(w.pay_safe(80) for _ in range(3)))
    print("safe:", results, "balance:", w.balance)
    assert w.balance == 20 and results.count(True) == 1
    print("ALL PASSED")


asyncio.run(main())
```

Output:

```
racy: [True, True, True] balance: -140
safe: [True, False, False] balance: 20
ALL PASSED
```

The racy version fails **deterministically** — all three coroutines check `100 >= 80`
before any of them resumes to subtract. Rules for async code:

1. **State only changes between `await`s atomically.** Code with no `await` between the
   check and the act is safe on one event loop. Put an `await` in between and you need an
   `asyncio.Lock` (or restructure so the await comes before the check).
2. **`asyncio.Lock` is not `threading.Lock`.** Asyncio primitives are not thread-safe;
   threading locks block the whole event loop. Use each only in its own world.
3. **Never block the event loop.** `time.sleep`, `requests.get`, a CPU-heavy loop, or a
   synchronous DB driver inside `async def` freezes *every* coroutine. Offload with
   `await asyncio.to_thread(fn)` (I/O) or a process pool (CPU).
4. **Function colour is a design boundary.** `async` functions can only be awaited from
   async code, so async-ness spreads up the call stack. Keep the domain core
   **synchronous and pure** (`01` §9, `08` §4) and make only the I/O shell async; then
   the same core serves sync and async entry points.
5. **Don't create fire-and-forget tasks.** `asyncio.create_task(x())` with no reference
   kept can be garbage-collected mid-flight, and its exception is lost. Use a `TaskGroup`
   (§9).

---

## 9 · Structured concurrency

**Unstructured:** start a thread/task/goroutine and hope someone waits for it, cancels
it, and sees its errors. **Structured:** concurrent work lives inside a scope, and **the
scope does not exit until all its children have finished** — like a function call that
can't return while its callees are still running.

Guarantees you get:

- No leaked tasks after the scope exits.
- Errors in children propagate to the parent.
- A failure (or cancellation, or timeout) of the parent cancels the children.

Python 3.11+ has `asyncio.TaskGroup`; Go has `golang.org/x/sync/errgroup`; Java 21+ has
`StructuredTaskScope`; Kotlin has coroutine scopes; Trio pioneered "nurseries".

The simplest use: run two things concurrently and wait for both.

```python
# Simplest on-ramp: run two things concurrently and wait for both.
import asyncio

async def say(msg, delay):
    await asyncio.sleep(delay)
    return msg

async def main():
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(say("hello", 0.02))
        t2 = tg.create_task(say("world", 0.01))
    print(t1.result(), t2.result())

asyncio.run(main())
```

Output:

```
hello world
```

The `async with` block doesn't exit — and `main` doesn't move past it — until both tasks
finish, in either order. Scaled up, the same block adds a concurrency limit and turns a
failure into cancellation of the sibling tasks instead of a leak:

```python
# Structured, bounded fan-out: at most N in flight, all-or-nothing, nothing leaks.
import asyncio


async def fetch(url: str, stats: dict) -> str:
    stats["in_flight"] += 1
    stats["peak"] = max(stats["peak"], stats["in_flight"])
    try:
        await asyncio.sleep(0.01)
        if url.endswith("/bad"):
            raise ConnectionError(url)
        return f"<html {url}>"
    finally:
        stats["in_flight"] -= 1


async def crawl(urls: list[str], limit: int, stats: dict) -> list[str]:
    sem = asyncio.Semaphore(limit)

    async def bounded(url: str) -> str:
        async with sem:
            return await fetch(url, stats)

    async with asyncio.TaskGroup() as tg:          # waits for all; first failure cancels the rest
        tasks = [tg.create_task(bounded(u)) for u in urls]
    return [t.result() for t in tasks]


async def main():
    stats = {"in_flight": 0, "peak": 0}
    pages = await crawl([f"https://x/{i}" for i in range(100)], limit=10, stats=stats)
    print(len(pages), "pages, peak concurrency", stats["peak"])
    assert len(pages) == 100 and stats["peak"] == 10

    stats = {"in_flight": 0, "peak": 0}
    try:
        await crawl([f"https://x/{i}" for i in range(50)] + ["https://x/bad"], 10, stats)
    except* ConnectionError as eg:
        print("failed:", [str(e) for e in eg.exceptions], "still running:", stats["in_flight"])
    assert stats["in_flight"] == 0                 # no orphaned tasks
    print("ALL PASSED")


asyncio.run(main())
```

Output:

```
100 pages, peak concurrency 10
failed: ['https://x/bad'] still running: 0
ALL PASSED
```

Two design points:

- **Bound fan-out.** `gather` over 10,000 URLs opens 10,000 connections at once and gets
  you rate-limited or exhausts file descriptors. A semaphore caps in-flight work; peak
  concurrency was exactly 10.
- **All-or-nothing vs. best-effort is a choice.** `TaskGroup` cancels siblings on the
  first failure (right for "build this page from 5 required parts"). For "crawl what you
  can", catch errors *inside* each task and return a result-or-error per URL
  (`gather(..., return_exceptions=True)` is the unstructured version of this).

---

## 10 · Single-flight: collapsing duplicate work

When a popular cache key expires, 1,000 concurrent requests all miss and all query the
database — a **cache stampede** (thundering herd). Single-flight makes concurrent callers
for the same key share one in-flight load.

```python
# Single-flight: N concurrent requests for the same key trigger ONE backend call.
import asyncio


class SingleFlightCache:
    def __init__(self, loader):
        self._loader = loader
        self._values: dict[str, object] = {}
        self._inflight: dict[str, asyncio.Future] = {}

    async def get(self, key: str):
        if key in self._values:
            return self._values[key]
        fut = self._inflight.get(key)
        if fut is None:                                    # first caller: start the load
            fut = asyncio.get_running_loop().create_future()
            self._inflight[key] = fut
            try:
                value = await self._loader(key)
            except BaseException as e:                     # incl. cancellation of the leader
                fut.set_exception(e if isinstance(e, Exception) else RuntimeError("load cancelled"))
                fut.exception()                            # mark retrieved: no "never retrieved" warning
                raise
            else:
                self._values[key] = value
                fut.set_result(value)
            finally:
                del self._inflight[key]                    # failures are not cached
            return value
        return await asyncio.shield(fut)                   # followers share the leader's result


async def main():
    calls = 0

    async def slow_db(key):
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.05)
        return f"row:{key}"

    cache = SingleFlightCache(slow_db)
    results = await asyncio.gather(*(cache.get("user:7") for _ in range(100)))
    print(len(results), set(results), "backend calls:", calls)
    assert calls == 1 and set(results) == {"row:user:7"}

    attempts = 0
    async def flaky(key):
        nonlocal attempts
        attempts += 1
        await asyncio.sleep(0.01)
        if attempts == 1:
            raise ConnectionError("db blip")
        return "ok"

    cache = SingleFlightCache(flaky)
    first = await asyncio.gather(*(cache.get("k") for _ in range(5)), return_exceptions=True)
    print([type(r).__name__ for r in first])
    assert all(isinstance(r, ConnectionError) for r in first)
    assert await cache.get("k") == "ok"                    # the error was not cached

    lone = SingleFlightCache(flaky)
    attempts = 0
    try:
        await lone.get("solo")                             # a leader with no followers
    except ConnectionError:
        pass
    print("ALL PASSED")


asyncio.run(main())
```

Output:

```
100 {'row:user:7'} backend calls: 1
['ConnectionError', 'ConnectionError', 'ConnectionError', 'ConnectionError', 'ConnectionError']
ALL PASSED
```

Design decisions:

- **The in-flight registry holds futures, not values.** The first caller (leader) does the
  work; followers await the leader's future.
- **Failures are shared but not cached.** All five concurrent callers saw the blip; the
  next call retried and succeeded. Caching the error would turn a 10 ms blip into a
  TTL-long outage.
- **`asyncio.shield`** stops a follower's own cancellation (its client disconnected) from
  cancelling the shared future everyone else is waiting on.
- **Registration and lookup happen with no `await` between them**, which is what makes
  them atomic on one event loop (§8 rule 1). The threaded version needs a lock around
  "check registry / insert future", and must do the load itself *outside* that lock.

Go's `golang.org/x/sync/singleflight` is the canonical implementation. Related stampede
defences: jittered TTLs (keys don't all expire together) and serving stale while one
request refreshes.

---

## 11 · The same design choices in Go

Go offers both styles natively; the proverb recommends channels, but the Go team's own
guidance is pragmatic: **use a mutex for protecting state, channels for transferring
ownership or coordinating work.**

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

// ── Style 1: share memory, protect it with a mutex. Best for simple state + short sections.

type Inventory struct {
	mu    sync.Mutex // guards stock; the comment IS part of the design
	stock map[string]int
}

// Reserve is the compound action: callers cannot write check-then-act themselves.
func (inv *Inventory) Reserve(sku string, qty int) bool {
	inv.mu.Lock()
	defer inv.mu.Unlock()
	if inv.stock[sku] < qty {
		return false
	}
	inv.stock[sku] -= qty
	return true
}

// ── Style 2: "share memory by communicating". One goroutine owns the state (an actor).

type reserveReq struct {
	sku   string
	qty   int
	reply chan bool
}

type InventoryActor struct {
	reqs chan reserveReq
}

func NewInventoryActor(ctx context.Context, stock map[string]int) *InventoryActor {
	a := &InventoryActor{reqs: make(chan reserveReq)}
	go func() { // the ONLY goroutine that touches stock
		for {
			select {
			case r := <-a.reqs:
				ok := stock[r.sku] >= r.qty
				if ok {
					stock[r.sku] -= r.qty
				}
				r.reply <- ok
			case <-ctx.Done():
				return
			}
		}
	}()
	return a
}

func (a *InventoryActor) Reserve(ctx context.Context, sku string, qty int) (bool, error) {
	reply := make(chan bool, 1) // buffered: the actor never blocks on a caller who gave up
	select {
	case a.reqs <- reserveReq{sku, qty, reply}:
	case <-ctx.Done():
		return false, ctx.Err()
	}
	select {
	case ok := <-reply:
		return ok, nil
	case <-ctx.Done():
		return false, ctx.Err()
	}
}

// ── Structured, bounded fan-out: limit concurrency, first error cancels the rest, no leaks.
// (golang.org/x/sync/errgroup with SetLimit does this; written out here with the stdlib.)

func fetchAll(ctx context.Context, urls []string, limit int,
	fetch func(context.Context, string) (string, error)) ([]string, error) {
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]string, len(urls)) // each goroutine writes its own index: no lock needed
	sem := make(chan struct{}, limit)
	var wg sync.WaitGroup
	var once sync.Once
	var firstErr error

	for i, u := range urls {
		wg.Add(1)
		go func() {
			defer wg.Done()
			select {
			case sem <- struct{}{}:
				defer func() { <-sem }()
			case <-ctx.Done():
				return
			}
			body, err := fetch(ctx, u)
			if err != nil {
				once.Do(func() { firstErr = err; cancel() })
				return
			}
			results[i] = body
		}()
	}
	wg.Wait() // never return while goroutines are still running
	return results, firstErr
}

func main() {
	// Mutex style under contention: exactly 100 reservations succeed.
	inv := &Inventory{stock: map[string]int{"widget": 100}}
	var wg sync.WaitGroup
	var mu sync.Mutex
	wins := 0
	for range 1000 {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if inv.Reserve("widget", 1) {
				mu.Lock()
				wins++
				mu.Unlock()
			}
		}()
	}
	wg.Wait()
	fmt.Println("mutex wins:", wins)

	// Actor style: same guarantee, no locks around the state.
	ctx, cancel := context.WithCancel(context.Background())
	actor := NewInventoryActor(ctx, map[string]int{"widget": 100})
	var actorWins int64
	var cmu sync.Mutex
	for range 1000 {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if ok, _ := actor.Reserve(ctx, "widget", 1); ok {
				cmu.Lock()
				actorWins++
				cmu.Unlock()
			}
		}()
	}
	wg.Wait()
	cancel()
	fmt.Println("actor wins:", actorWins)

	// Bounded fan-out with fail-fast cancellation.
	var inFlight, peak int
	var pmu sync.Mutex
	fetch := func(ctx context.Context, u string) (string, error) {
		pmu.Lock()
		inFlight++
		peak = max(peak, inFlight)
		pmu.Unlock()
		defer func() { pmu.Lock(); inFlight--; pmu.Unlock() }()
		if u == "bad" {
			return "", errors.New("fetch bad: 500")
		}
		select {
		case <-time.After(10 * time.Millisecond):
			return "page:" + u, nil
		case <-ctx.Done():
			return "", ctx.Err()
		}
	}
	urls := make([]string, 50)
	for i := range urls {
		urls[i] = fmt.Sprint(i)
	}
	res, err := fetchAll(context.Background(), urls, 5, fetch)
	fmt.Println("ok:", len(res), res[0], err, "peak:", peak)

	urls[7] = "bad"
	_, err = fetchAll(context.Background(), urls, 5, fetch)
	fmt.Println("with failure:", err, "in flight after return:", inFlight)
}
```

Output (`go run -race .` — no races reported):

```
mutex wins: 100
actor wins: 100
ok: 50 page:0 <nil> peak: 5
with failure: fetch bad: 500 in flight after return: 0
```

What to notice:

- **Mutex style** is shorter for a map with a compound operation. The `// guards stock`
  comment is a convention (and a linter hint) documenting which lock protects which
  field.
- **Actor style** needs request/reply plumbing and a context for shutdown — more code, but
  the state-handling goroutine is plain sequential logic. It shines when the state logic
  is complex or must own I/O.
- **The reply channel is buffered (size 1)** so the actor never blocks forever on a
  caller whose context was cancelled — an unbuffered reply would leak the actor.
- **`fetchAll` never returns while goroutines run** (`wg.Wait()`), cancels the rest on the
  first error, and caps concurrency with a buffered-channel semaphore. In production use
  `errgroup.WithContext` + `g.SetLimit(n)`.
- **Each goroutine writes its own slice index**, so `results` needs no lock — confinement
  by index.
- Since Go 1.22, each loop iteration has its own `i`/`u`, so the closures capture the right
  values without the old `i := i` copy.

---

## 12 · Testing concurrent code

Concurrency bugs are timing-dependent, so a test that passes 1,000 times proves little.
Layer the techniques:

| Technique | What it catches | Tooling |
|---|---|---|
| **Keep logic sequential and test it sequentially** | Most bugs — if the concurrent part is a thin shell (actor, TaskGroup) around pure logic | Plain unit tests |
| **Force interleavings deterministically** | A specific race, reproduced every run | `threading.Barrier`/`Event` hooks, fake schedulers |
| **Race detector** | Unsynchronised memory access (not logic races) | `go test -race`; ThreadSanitizer for C/C++ |
| **Stress tests** | Races, deadlocks, lost updates under contention | Many threads × many iterations, checking an invariant (e.g. conservation of money, §3) |
| **Deadlock timeouts** | Tests that hang | `pytest-timeout`, `go test -timeout`, `faulthandler.dump_traceback_later` |
| **Model checking / systematic exploration** | Rare interleavings | TLA+, Go's `-race` + `GOMAXPROCS` variation, Loom (Rust), CHESS |
| **Property tests over operation sequences** | State-machine bugs | Hypothesis `RuleBasedStateMachine`, linearizability checkers (Porcupine, Jepsen's Knossos) |

### Making a race reproducible

A barrier placed between the read and the write forces both threads to read before
either writes — the lost update happens on **every** run, and the fix is verified
against the exact interleaving that broke it:

```python
# Forcing an interleaving deterministically: make the race happen every run, then prove the fix.
import threading


class RacyCounter:
    def __init__(self, gate=None):
        self.value = 0
        self._gate = gate
    def increment(self):
        v = self.value                     # read
        if self._gate:
            self._gate()                   # test hook: pause between read and write
        self.value = v + 1                 # write


class SafeCounter(RacyCounter):
    def __init__(self, gate=None):
        super().__init__(gate)
        self._lock = threading.Lock()
    def increment(self):
        with self._lock:
            super().increment()


def run_two(counter_cls):
    barrier = threading.Barrier(2, timeout=0.2)
    def gate():
        try:
            barrier.wait()                 # both threads have READ before either WRITES
        except threading.BrokenBarrierError:
            pass                           # the lock prevented the second thread from arriving
    c = counter_cls(gate)
    ts = [threading.Thread(target=c.increment) for _ in range(2)]
    for t in ts: t.start()
    for t in ts: t.join()
    return c.value


if __name__ == "__main__":
    racy, safe = run_two(RacyCounter), run_two(SafeCounter)
    print("racy:", racy, "safe:", safe)
    assert racy == 1 and safe == 2         # lost update reproduced 100% of the time; fix verified
    print("ALL PASSED")
```

Output:

```
racy: 1 safe: 2
ALL PASSED
```

The test hook (`gate`) is injected like any other dependency (`05` §3) — production code
passes `None`. In Go the same trick uses channels to pause a goroutine at a chosen point.

### Designs that are easier to test

- **Inject the executor / clock / scheduler** so tests can run tasks synchronously or in a
  chosen order.
- **Actors are testable without threads:** call the handler function directly with a
  sequence of messages and assert on state.
- **Invariants are the assertions.** "Sum of balances is constant", "at most one owner per
  seat", "every submitted job completes exactly once" — check them after a stress run.

---

## 13 · Choosing a model: threads, processes, asyncio, goroutines

| Workload | Python | Go |
|---|---|---|
| Many concurrent network calls (I/O-bound, high fan-out) | **asyncio** (thousands of tasks cheaply) or threads (tens–hundreds) | Goroutines |
| Blocking libraries with no async version | Threads (`ThreadPoolExecutor`, `asyncio.to_thread`) | Goroutines |
| CPU-bound work (parsing, image processing, numerics) | **Processes** (`ProcessPoolExecutor`), native extensions releasing the GIL (NumPy), or free-threaded 3.13t | Goroutines (uses all cores) |
| Shared state machine with strict ordering | Single-writer actor (thread or task) | Goroutine owning state |
| Pipeline of stages | Queues between workers | Channels between goroutines |

Process pools copy (pickle) arguments and results — pass small inputs, or shared memory,
not giant objects. Goroutines are cheap (a few KB of initial stack) but not free: an
unbounded `go` per request item is still an unbounded resource.

---

## 14 · Red flags

| Red flag | Problem | Fix |
|---|---|---|
| Public getters/setters on a shared object | Callers compose check-then-act; the race moves into every caller | Atomic business methods (§4) |
| `if x not in d: d[x] = …` on shared state | Check-then-act | `setdefault`, lock, or single-flight |
| Lock is public / passed around / `global` | Nobody can reason about who holds it | Private lock inside the owner |
| Callback, log handler, or I/O inside `with lock:` | Deadlock and latency | Open calls (§5) |
| Taking two locks without a global order | Deadlock | Order by ID; or one coarser lock |
| Returning internal list/dict from a guarded object | Mutated without the lock | Return copies/tuples/immutable views |
| `await` between a check and an act | Async race | `asyncio.Lock`, or re-check after the await |
| `time.sleep` / sync HTTP / sync DB inside `async def` | Freezes the event loop | `asyncio.to_thread`, async client |
| `create_task` without keeping a reference or awaiting | Lost tasks and swallowed exceptions | `TaskGroup` |
| `gather` over an unbounded list | Resource exhaustion, rate limiting | Semaphore / worker pool |
| Unbounded queue in front of a slow consumer | Memory grows until OOM | Bounded queue + backpressure |
| "Works because of the GIL" | Breaks on free-threaded Python and in any refactor | Explicit synchronisation |
| `RWMutex` everywhere "for performance" | Often slower; writer starvation | Plain mutex until profiling says otherwise |
| Goroutine with no exit path (`for { <-ch }` with no ctx/close) | Goroutine leak | `select` on `ctx.Done()`; close channels from the sender |
| Tests that "usually pass" | Hidden race | Force the interleaving; run `-race`; stress with invariants |

---

## 15 · Interview questions and model answers

**Q: How do you make a class thread-safe?**
First, try not to share it — confine it to one thread, or make it immutable. If it must
be shared and mutable, identify its invariants, protect each with a private lock held for
the whole check-and-update, expose atomic business operations instead of getters and
setters, never call out to unknown code while holding the lock, and don't leak references
to internal state. Then document which operations are atomic.

**Q: Mutex vs. channels in Go?**
Mutex to protect state — a cache, a counter, a map with compound operations. Channels to
transfer ownership of data or coordinate work between goroutines — pipelines, worker
pools, an actor owning complex state. Using channels as a mutex adds code without adding
safety.

**Q: Can asyncio code have race conditions? It's single-threaded.**
Yes. No data races, but every `await` yields to other coroutines, so a check-then-act that
spans an `await` can interleave — for example checking a balance, awaiting a fraud check,
then subtracting. Fix it with an `asyncio.Lock` around the whole sequence or by
restructuring so nothing awaits between check and act.

**Q: What is the actor model and when would you use it?**
One thread or goroutine owns the state and processes messages sequentially; others
communicate by sending messages and awaiting replies. There are no locks on the state, so
the logic is ordinary sequential code, and a bounded inbox gives backpressure. I'd use it
for state machines — an elevator controller, a matching engine, a game loop — or anything
owning a connection. To scale, shard into many actors by key.

**Q: How do you prevent deadlocks by design?**
Avoid holding more than one lock; when you must, acquire them in a global order. Don't call
unknown code or do I/O while holding a lock. Prefer designs without locks on shared state —
immutability with reference swaps, or a single-writer actor. Use timeouts on lock
acquisition in places where a hang is worse than an error.

**Q: What is structured concurrency?**
Concurrent tasks are started inside a scope that can't exit until they all finish; errors
propagate to the parent, and the parent's failure or cancellation cancels the children. It
eliminates leaked tasks and lost errors. `asyncio.TaskGroup`, Go's `errgroup`, Java's
`StructuredTaskScope`.

**Q: Your cache's hot key expires and the database falls over. What happened and how do
you fix it?**
A cache stampede: every concurrent request missed and queried the DB. Single-flight the
loads per key so one request loads and the rest wait on its result; add jitter to TTLs so
keys don't expire together; serve stale data while refreshing in the background.

**Q: How do you test concurrent code?**
Keep the logic sequential and test it directly; make the concurrent shell thin. Reproduce
specific races deterministically with barriers or channels at injected hook points. Run
Go's race detector in CI. Stress test with many threads and assert invariants like
conservation of money. Put timeouts on tests so deadlocks fail instead of hanging.

---

## 16 · Checklist

**Strategy**
- [ ] Every piece of shared mutable state is listed, with its strategy: confine, freeze, guard, or serialise.
- [ ] Per-request objects are confined; nothing request-scoped leaks into globals.
- [ ] Read-mostly data is immutable and swapped by reference.

**Guarded state**
- [ ] Each lock is private and protects a named invariant.
- [ ] Check and act happen in one critical section; public methods are business operations.
- [ ] Multiple locks are acquired in a global order.
- [ ] No I/O, callbacks, or unknown code runs while a lock is held.
- [ ] No references to guarded internals escape.

**Async and tasks**
- [ ] No check-then-act spans an `await` without a lock.
- [ ] Nothing blocking runs on the event loop.
- [ ] All tasks/goroutines live in a scope that waits for them and propagates errors.
- [ ] Fan-out is bounded; queues are bounded.
- [ ] Every goroutine/task has a way to stop (context, close, poison pill).

**Verification**
- [ ] The thread-safety contract is documented.
- [ ] Known races have deterministic reproduction tests.
- [ ] `go test -race` (or equivalent) runs in CI; stress tests assert invariants.
