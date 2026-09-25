# Low-Level Design (LLD) Interview Playbook

> Also called: **object-oriented design (OOD)**, **machine coding**, **class design**,
> **"design and implement"**, or at Google, a coding round where the problem is a
> stateful system rather than an algorithm.

In an LLD round you're given an open-ended system — *parking lot, elevator, Splitwise,
an in-memory key-value store with transactions, a rate limiter library* — and asked to
design classes, their responsibilities and interactions, and usually **write working
code** for the core. It is scored differently from both algorithm rounds and system
design rounds, and candidates who are strong at both still fail it by over- or
under-designing.

This file is the method. The worked, runnable problems are in `lld/`.

---

## Contents

1. [What LLD is and how it differs from HLD](#1--what-lld-is-and-how-it-differs-from-hld)
2. [What interviewers score](#2--what-interviewers-score)
3. [The 45-minute framework](#3--the-45-minute-framework)
4. [Step 1 — Clarify requirements (5 min)](#4--step-1--clarify-requirements-5-min)
5. [Step 2 — Entities, relationships, invariants (7 min)](#5--step-2--entities-relationships-invariants-7-min)
6. [Step 3 — Public API and key flows (5 min)](#6--step-3--public-api-and-key-flows-5-min)
7. [Step 4 — Code the core (20 min)](#7--step-4--code-the-core-20-min)
8. [Step 5 — Extensibility, concurrency, and tests (8 min)](#8--step-5--extensibility-concurrency-and-tests-8-min)
9. [Concurrency in LLD: the toolkit](#9--concurrency-in-lld-the-toolkit)
10. [The ten classic mistakes](#10--the-ten-classic-mistakes)
11. [Talk tracks — what to say, verbatim](#11--talk-tracks--what-to-say-verbatim)
12. [Machine-coding rounds (90–120 min)](#12--machine-coding-rounds-90120-min)
13. [Question bank with the key design point for each](#13--question-bank-with-the-key-design-point-for-each)
14. [Practice plan](#14--practice-plan)
15. [Self-scoring rubric](#15--self-scoring-rubric)

---

## 1 · What LLD is and how it differs from HLD

| | Low-level design (LLD) | High-level / system design (HLD) |
|---|---|---|
| Scope | One process: classes, interfaces, data structures, concurrency within a service | Many machines: services, storage, caches, queues, replication |
| Unit of design | Class / interface / method | Service / datastore / network call |
| Output | Class diagram + working code for the core | Architecture diagram + APIs + data model + capacity estimates |
| Key concerns | Responsibility assignment, invariants, extensibility, thread safety, testability | Scale, availability, consistency, latency, cost |
| Typical failure | Over-engineering (15 classes, no working code) or procedural spaghetti | Hand-waving, no numbers, no trade-offs |
| Material | `02`–`05` in this folder, `lld/` | `SystemDesign/` |

Some prompts are deliberately ambiguous between the two ("design a rate limiter").
**Ask:** *"Should I focus on the in-process library design and code it, or on a
distributed rate-limiting service?"* Answering the wrong one is a common silent failure.

### Where each company uses it

- **Amazon, Uber, Microsoft, Atlassian, Flipkart, Swiggy, many startups:** explicit OOD /
  machine-coding rounds.
- **Google:** rarely labelled "LLD", but coding rounds frequently are stateful designs
  (implement an LRU/LFU cache, a snapshot array, a file system, a key-value store with
  transactions, an iterator over nested data, a time-based store) and are graded on code
  structure as well as correctness. Follow-ups push on extensibility and concurrency.
- **Senior (L5+/SDE III) loops:** expectations shift from "correct classes" to "clean
  boundaries, justified trade-offs, concurrency handled, and you drove it."

---

## 2 · What interviewers score

Composite of real rubrics. Know it, and give evidence for each line out loud.

| Signal | Weak | Strong |
|---|---|---|
| **Requirement gathering** | Starts coding immediately; invents features | Asks scoped questions, writes down functional + non-functional requirements, agrees what's out of scope |
| **Object modeling** | Nouns → classes mechanically; god class `System` | Right entities (incl. discovered ones like `Ticket`, `Loan`, `Booking`), value objects, clear ownership |
| **Responsibility assignment** | Logic in a manager, entities are bags of fields | Each invariant has exactly one owner; tell-don't-ask |
| **Abstractions / extensibility** | No interfaces, or interfaces for everything | Interfaces exactly where the problem implies variation; explains how a new requirement lands as an addition |
| **Use of patterns** | Name-drops patterns; forces them | Arrives at patterns from forces and names them after |
| **Code quality** | Long methods, magic numbers, primitive obsession | Readable, typed, small cohesive classes, enums, guard clauses |
| **Correctness** | Works only on the happy path | Handles edge cases and illegal operations with clear errors |
| **Concurrency** | Not mentioned, or "add synchronized everywhere" | Identifies shared mutable state and the exact critical sections; picks granularity deliberately |
| **Testability** | Can't be tested without the whole system | Injected clock/IDs/strategies; demonstrates with a few tests or a driver |
| **Communication** | Silent coding | Narrates decisions and trade-offs; checks in at milestones |

**The most common downlevel reason:** a beautiful class diagram and no working code, or
working code with no design. The target is **a small, clean design that runs.**

---

## 3 · The 45-minute framework

```
 0 ─────── 5 ────────── 12 ──────── 17 ─────────────────────── 37 ────────── 45
 │ CLARIFY │  ENTITIES  │  API +    │        CODE THE CORE      │ EXTEND,     │
 │  reqs,  │  relations │  flows    │   (entities → service →   │ CONCURRENCY,│
 │  scope  │  invariants│  sequence │    one full flow working) │ TESTS, Q&A  │
 └─────────┴────────────┴───────────┴───────────────────────────┴─────────────┘
   write      draw        write         write real code             talk +
   bullets    boxes       signatures                                small edits
```

Adjust by format: a 60-minute round gets more coding time; a "design only, pseudo-code
fine" round gets a deeper class diagram and more extensibility discussion. **Ask at the
start:** *"Would you like working code for the core, or is a class-level design with key
method signatures enough?"*

---

## 4 · Step 1 — Clarify requirements (5 min)

Write the requirements as a short numbered list where the interviewer can see it. This
list becomes your acceptance criteria.

### The clarification checklist

| Category | Questions |
|---|---|
| **Actors** | Who uses it? (customer, admin, operator, another system) |
| **Core use cases** | What are the 3–5 must-have operations? What's explicitly out of scope? |
| **Entities & variants** | What kinds of X exist? (vehicle types, spot sizes, room types, split types) Will more be added? |
| **Rules / policies** | Pricing, limits, priorities, expiry, cancellation rules |
| **Scale (in-process)** | How many objects? (10 floors × 200 spots vs 1M keys changes data structures) |
| **Concurrency** | Multiple entry gates / threads / users acting simultaneously? |
| **Persistence** | In memory only, or should the design allow a database later? |
| **Failure cases** | Full lot, invalid ticket, payment failure, double booking |
| **Interface** | Library <abbr title="Application Programming Interface">API</abbr>, CLI, REST? (Usually: plain classes + a driver) |

### Example: parking lot

> 1. Multi-floor lot; spot sizes SMALL, COMPACT, LARGE; vehicles MOTORCYCLE, CAR, TRUCK.
> 2. A vehicle may park in a spot of its size or larger.
> 3. `park(vehicle) -> Ticket`, `unpark(ticket) -> fee`; `available(spot_type)` per floor.
> 4. Fee = hourly rate by vehicle type, rounded up to whole hours; pluggable.
> 5. Multiple entry/exit gates operate concurrently — no two vehicles get the same spot.
> 6. Out of scope: payment processing, reservations, EV charging (mention as extensions).

**Non-functional (LLD flavour):** thread-safe, `O(1)`/`O(log n)` spot lookup, easy to add
vehicle types and pricing rules, testable without real time.

---

## 5 · Step 2 — Entities, relationships, invariants (7 min)

Use the method from `02_oop_and_domain_modeling.md` §11:

1. **Candidate nouns/verbs** from the requirements.
2. **Filter and discover:** split conflated concepts, find the *records the verbs create*
   (`Ticket`, `Booking`, `Loan`, `Expense`, `Transaction`), identify value objects.
3. **Invariants and owners:** write each invariant next to the class that enforces it.
4. **Variation points** → interfaces (only where the requirements say things vary).
5. **Relationships with cardinality.**

### What to put on the board

```
Vehicle (value: plate, type)            «enum» VehicleType, SpotType
ParkingSpot (id, type, occupied_by?)    inv: at most one vehicle
ParkingFloor 1 ◆── * ParkingSpot        inv: free-spot index consistent with spots
ParkingLot 1 ◆── * ParkingFloor         owns: active tickets; inv: one active ticket per plate
Ticket (id, plate, spot_id, entry_time) record created by park()
«interface» SpotAllocator  → NearestFirst, ...     (variation: allocation strategy)
«interface» PricingPolicy  → Hourly, ...           (variation: pricing)
Clock (injected)                                    (testability)
```

This is enough. Resist drawing `Gate`, `Attendant`, `DisplayBoard`, `PaymentProcessor`,
`Address` unless a requirement needs them — mention them as extensions instead.

---

## 6 · Step 3 — Public <abbr title="Application Programming Interface">API</abbr> and key flows (5 min)

Write the **public method signatures** of the main service/facade and trace the one or
two most important flows. This is where the design gets checked before code exists.

```python
class ParkingLot:
    def park(self, vehicle: Vehicle) -> Ticket: ...          # raises LotFull
    def unpark(self, ticket_id: str) -> int: ...             # fee in cents; raises InvalidTicket
    def available(self, spot_type: SpotType) -> int: ...
```

Trace `park`: lot asks allocator for a spot compatible with the vehicle → spot occupied
atomically → ticket created with injected clock → stored by ID. Trace `unpark`: look up
ticket → free spot → pricing policy computes fee from duration → ticket closed.

If a step has no clear owner, or needs data from an object that shouldn't have it, fix the
model *now*.

---

## 7 · Step 4 — Code the core (20 min)

### Order of writing

1. **Enums and value objects** (fast, they fix vocabulary).
2. **Entities with their invariants.**
3. **Interfaces for variation points** + one simple implementation each.
4. **The service/facade** wiring the flow.
5. **A tiny driver or 3–4 asserts** showing a full flow, including one failure case.

### Code conventions that score well (Python)

```python
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, Callable
import threading, itertools
```

- `Enum` for types and states; `@dataclass(frozen=True)` for value objects.
- `Protocol` for strategies; pass collaborators in the constructor.
- Custom exceptions named for the domain (`LotFull`, `SeatUnavailable`).
- Type hints on public methods. Docstring only where the contract isn't obvious.
- Inject `clock: Callable[[], float]` and ID generators.
- No `print` inside domain classes; return values, let the driver print.
- Integer money (cents).

### Stay out of these time sinks

- Getters/setters for every field.
- Full CRUD for every entity.
- Persistence code — a dict-backed repository is enough; say "this becomes a table".
- Input parsing/menus, unless it's a machine-coding round that requires a CLI.

If time is short, **stub a secondary strategy** (`class PeakPricing: ...  # TODO`) and
say how it would work. A running core beats complete-but-broken.

### A minimal worked example (30 seconds to read)

The parking lot above is realistic-sized; here's the same five-step order on a problem
small enough to hold in your head — an in-memory coat check. One entity, one invariant
("a ticket can be claimed at most once"), one variation point (how IDs are generated),
one facade, one driver that exercises the happy path and a failure:

```python
from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol
import itertools

class ItemKind(Enum):                        # 1. enums / value objects
    COAT = auto()
    BAG = auto()

@dataclass(frozen=True)
class Ticket:
    id: int

class IdGenerator(Protocol):                  # 3. interface at the variation point
    def next_id(self) -> int: ...

class SequentialIds:                          # 3. one concrete implementation
    def __init__(self) -> None:
        self._counter = itertools.count(1)
    def next_id(self) -> int:
        return next(self._counter)

class UnknownTicket(Exception): pass

class CoatCheck:                              # 2. entity, owns the invariant
    def __init__(self, ids: IdGenerator) -> None:
        self._ids = ids
        self._claims: dict[int, str] = {}

    def check(self, item: str) -> Ticket:
        ticket = Ticket(self._ids.next_id())
        self._claims[ticket.id] = item
        return ticket

    def claim(self, ticket: Ticket) -> str:
        if ticket.id not in self._claims:
            raise UnknownTicket(f"no such ticket: {ticket.id}")
        return self._claims.pop(ticket.id)

if __name__ == "__main__":                    # 5. tiny driver, happy path + failure
    booth = CoatCheck(SequentialIds())
    t1 = booth.check("blue coat")
    t2 = booth.check("red scarf")
    print(f"issued {t1}, {t2}")
    print("claimed:", booth.claim(t1))
    try:
        booth.claim(t1)
    except UnknownTicket as e:
        print("expected failure:", e)
```

Output:

```text
issued Ticket(id=1), Ticket(id=2)
claimed: blue coat
expected failure: no such ticket: 1
```

Swapping `SequentialIds` for a `RandomIds` later touches nothing but the constructor
call — that's the payoff of putting the interface exactly at the one thing (`item` → ID)
that plausibly varies, and nowhere else.

---

## 8 · Step 5 — Extensibility, concurrency, and tests (8 min)

Pre-empt the follow-ups. For each likely new requirement, say **which class changes and
which don't**:

> "Adding an EV-charging spot type is a new `SpotType` and a compatibility rule — the
> allocator and lot don't change. Weekend pricing is a new `PricingPolicy`
> implementation passed at construction. Reservations would add a `Reservation` entity
> and a `HELD` spot state with an expiry, and `park` would check holds first."

Then concurrency (§9) and how you'd test (FakeClock, contract tests for strategies, a
multithreaded test that parks N vehicles from M threads and asserts no spot is assigned
twice).

### The universal follow-up list — have an answer for each

1. Add a new type/variant (vehicle, payment method, split type, piece).
2. Change a policy at runtime (pricing, dispatch, eviction).
3. Make it thread-safe / handle concurrent users.
4. Persist it / survive restarts.
5. Scale it beyond one machine (bridge to HLD: partition by lot/venue/key, move locks to
   the database or a distributed lock/lease, idempotency keys).
6. Add notifications/observers.
7. Add undo / history / audit.
8. How would you test it?

---

## 9 · Concurrency in LLD: the toolkit

Almost every LLD problem has a **check-then-act race** at its heart: "is the spot free?
→ take it", "is the seat available? → book it", "is the balance enough? → withdraw".

### The race, drawn

```
 Gate A thread                          Gate B thread
 ─────────────                          ─────────────
 spot = find_free()   → S7
                                        spot = find_free()   → S7   (still free!)
 spot.occupant = car1
                                        spot.occupant = car2        ← overwrites car1
 ticket(S7, car1)                       ticket(S7, car2)            ← two tickets, one spot
```

`lld/004_movie_ticket_booking_solution.py` runs exactly this race with real threads
and shows it double-booking without the lock.

### The simplest possible fix, shown running

Same shape as the spot race, boiled down to a shared counter so you can see the fix in
five lines. `time.sleep(0)` between the check and the act widens the race window enough
to actually observe the lost updates on a fast machine — a real check-then-act race
doesn't need help, but a toy one this small does:

```python
import threading, time

class UnsafeCounter:
    def __init__(self) -> None:
        self.value = 0
    def increment(self) -> None:
        current = self.value       # "check"
        time.sleep(0)              # widen the window
        self.value = current + 1   # "act" -- not atomic together

class SafeCounter:
    def __init__(self) -> None:
        self.value = 0
        self._lock = threading.Lock()
    def increment(self) -> None:
        with self._lock:           # check-then-act inside ONE critical section
            current = self.value
            time.sleep(0)
            self.value = current + 1

def hammer(counter, n_threads=8, n_increments=200) -> int:
    def worker():
        for _ in range(n_increments):
            counter.increment()
    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads: t.start()
    for t in threads: t.join()
    return counter.value

expected = 8 * 200
print("unsafe result:", hammer(UnsafeCounter()), f"(expected {expected})")
print("safe result:  ", hammer(SafeCounter()), f"(expected {expected})")
```

Output (the unsafe number is non-deterministic and will differ run to run — that's the
race; the safe number is always exactly right):

```text
unsafe result: 212 (expected 1600)
safe result:   1600 (expected 1600)
```

### Options, from simplest to most scalable

| Technique | How | Good for | Cost |
|---|---|---|---|
| **One coarse lock** | `with self._lock:` around every public mutating method | Interviews by default; low contention | Serialises everything |
| **Lock striping / per-entity locks** | One lock per floor / show / account; lock IDs in a fixed order when taking several | Independent entities (different shows don't contend) | Deadlock risk if order isn't fixed |
| **Read-write lock** | Many readers, one writer | Read-heavy (availability queries) | Python stdlib has none; Go has `sync.RWMutex` |
| **Atomic compare-and-set** | `if spot.state == FREE: spot.state = TAKEN` atomically | Single-field claims | Needs a CAS primitive (Go `atomic`, DB conditional update) |
| **Optimistic concurrency** | Read version, write "where version = v", retry on conflict | Low-conflict writes; maps to databases | Retries under contention |
| **Holds with expiry** | Reserve temporarily (seat hold 10 min), confirm or release | Booking flows with payment in the middle | Expiry sweeper, clock handling |
| **Single-writer / actor** | All mutations go through one thread/goroutine via a queue | State machines (elevator controller) | Throughput of one thread |
| **Immutable snapshots** | Readers see a snapshot; writers swap a reference | Config, routing tables | Copy cost |

### Rules to state

- **Identify the shared mutable state first,** then the invariant it must keep, then the
  smallest critical section that keeps it.
- **Check and act inside the same critical section.**
- **Never call out (I/O, callbacks, other locks) while holding a lock** unless required;
  it's how deadlocks and latency spikes happen.
- **Acquire multiple locks in a global order** (e.g. by ID) — the transfer-between-accounts
  classic.
- **Python's GIL does not make your check-then-act atomic.** Threads switch between
  bytecodes; `x += 1` on a shared attribute is not atomic across threads.
- **Across processes/machines**, the lock moves to the database (conditional update,
  `SELECT … FOR UPDATE`, unique constraints) or a lease-based lock — and every operation
  needs an idempotency key. That's the bridge to HLD.

Deeper theory: `CSFundamentals/05_concurrency_deep_dive.md`,
`PyEngineering/10_transactions_concurrency_control`, `GoEngineering/31_deadlocks_and_sync_primitives`.

---

## 10 · The ten classic mistakes

| # | Mistake | Fix |
|---|---|---|
| 1 | Coding before agreeing requirements | 5 minutes of written requirements; confirm scope |
| 2 | God class (`ParkingLotSystem` does everything) | Assign each invariant to the object owning the data |
| 3 | Anemic entities + `*Manager` classes holding all logic | Tell, don't ask; move behaviour to data |
| 4 | Inheritance for variants that should be data (`class RedCar(Car)`) or strategies | Enums/fields for data variants; composition for behaviour variants |
| 5 | Interface/factory/strategy for everything | Only where the requirements imply variation; say where you'd add more |
| 6 | Money as `float`; time as `datetime.now()` inside logic | Integer minor units; injected clock |
| 7 | Ignoring concurrency until asked, or locking everything wrongly | Name the check-then-act race yourself; choose granularity |
| 8 | Returning mutable internals / exposing setters | Methods that enforce rules; return copies |
| 9 | 25 minutes of diagrams, no running code | Timebox; code the core flow end to end first |
| 10 | Silent failure (`return None` on invalid ticket) | Domain exceptions with clear messages |

---

## 11 · Talk tracks — what to say, verbatim

**Opening:** *"Before designing, I'd like to pin down scope. I'll list what I think the
core use cases are and you can correct me."*

**Scoping out:** *"I'll treat payments as an external interface and keep it out of scope,
but I'll leave a `PaymentGateway` port so it slots in."*

**Modeling:** *"The key invariant is that a spot holds at most one vehicle, so
`ParkingSpot` owns that. The lot owns the rule that a plate has at most one active
ticket."*

**Choosing an abstraction:** *"Pricing is likely to change independently of parking
logic, so I'll make it a strategy. Vehicle types are just data, so an enum is enough —
I don't need a class per vehicle."*

**Choosing NOT to abstract:** *"I could put an interface in front of the floor, but
there's only one kind and nothing in the requirements suggests another, so I'll keep it
concrete."*

**Concurrency:** *"Two gates can race on the same free spot. The check and the claim must
be atomic. For an interview I'll use one lock per floor — different floors don't contend
— and if this were backed by a database I'd use a conditional update on the spot row."*

**Checkpoint:** *"The core flow works end to end. Would you like me to go deeper on
concurrency, add the reservation feature, or write tests?"*

**Out of time:** *"The remaining piece is the peak-hour pricing strategy; it would
implement `PricingPolicy` using the entry and exit times, and nothing else would change."*

---

## 12 · Machine-coding rounds (90–120 min)

Common in India-based and some product companies: you get a written problem, write a
**complete, runnable** program (often with a command-line driver), then walk through it.

**Evaluation focus:** it runs; requirements met; separation of concerns; extensibility;
naming; edge cases; no hardcoding; ideally some tests.

**Plan the time:**

```
  0–10   Read carefully; list requirements and ambiguous points; ask
 10–25   Model + package layout: models/ services/ strategies/ exceptions/ driver
 25–75   Implement bottom-up; run the driver after each service
 75–95   Edge cases, error messages, a handful of tests
 95–120  Clean up names; README of assumptions; demo
```

**Tips:** start from the provided I/O format and build a driver early so you always have
something runnable; keep an "assumptions" list; commit/save often; prefer in-memory
repositories behind interfaces; don't gold-plate.

---

## 13 · Question bank with the key design point for each

The **key point** is what separates a strong answer. ✅ = worked, runnable solution in
`lld/`.

### Tier 1 — asked most often

| Problem | Key design point | |
|---|---|---|
| **Parking lot** | Spot allocation index (not linear scan), size compatibility, pricing strategy, atomic spot claim across gates | ✅ 001 |
| **Elevator system** | Per-car state machine; dispatch strategy (SCAN/LOOK); hall vs. car calls; single-writer controller | ✅ 002 |
| **Vending machine** | State pattern; money handling in cents; change-making with limited coins; cancel/refund | ✅ 003 |
| **Movie / concert ticket booking** | Seat holds with expiry; atomic multi-seat hold; confirm-after-payment; per-show locks | ✅ 004 |
| **Splitwise / expense sharing** | Split strategies (equal/exact/percent) with rounding that sums exactly; balance graph; minimise transactions | ✅ 005 |
| **In-memory KV store with nested transactions** | Stack of write-sets; tombstones for deletes; commit merges into parent; O(1) get via layering | ✅ 006 |
| **Logging framework** | Levels as a chain/threshold; appenders × formatters (composition); hierarchical loggers; async appender | ✅ 007 |
| **Tic-tac-toe (N×N) / board game** | O(1) win detection with row/col/diagonal counters; players as strategies; move validation | ✅ 008 |
| **LRU / LFU cache** | Hash map + doubly linked list (LRU) / frequency buckets (LFU), eviction as a strategy, thread safety | ✅ 009 |
| **Unix `find` / file search** | Composite file tree; Specification filters with AND/OR/NOT; lazy traversal | ✅ 010 |
| **Meeting room / hotel booking** | Half-open intervals; per-room sorted bookings with bisect for O(log n) conflict check; room selection strategy | ✅ 011 |
| **Rate limiter library** | Algorithms as strategies (token bucket, sliding window log/counter); per-key state; injected clock | ✅ 012 |

### Tier 2 — know the key point

✅ = worked, runnable solution in `lld/`; a blank means design it on paper (§14's plan).

| Problem | Key design point | |
|---|---|---|
| **Library management** | `Book` vs. `BookCopy`; `Loan` entity; reservation queue per book; fine policy | ✅ 015 |
| **Hotel management** | `RoomType` inventory by date vs. specific room assignment at check-in; overbooking policy | |
| **Snake and ladder** | Board as a jump map; dice as injected strategy (testability); turn state | |
| **Chess** | Piece move generation per type (polymorphism), board validation, check detection by simulating moves; don't forget castling/en passant/promotion as rule objects | ✅ 019 |
| **ATM** | State machine (idle → card → PIN → transaction); cash dispensing chain; bank as external port; transactional debit then dispense with compensation | ✅ 018 |
| **Online shopping cart / checkout** | Cart vs. Order; price snapshot at order time; discount rules as composable strategies; inventory reservation | |
| **Ride sharing (in-process)** | Driver matching strategy; trip state machine; surge pricing strategy; location index | |
| **Food delivery order lifecycle** | Order state machine with actors per transition; assignment strategy; notifications as observers | ✅ 016 |
| **Pub-sub / message queue (in-process)** | Topics, subscriber offsets, at-least-once with ack, back-pressure (`PyEngineering/16`) | |
| **Task/job scheduler** | Priority queue by run-at time; worker pool; retries with backoff; cancellation; recurring jobs | ✅ 014 |
| **Notification service** | Channel strategy + templates; user preferences; retry decorator; rate limiting per user | ✅ 020 |
| **Text editor with undo/redo** | Command pattern; rope/gap buffer for text; cursor as value object (`04` §8) | ✅ 017 |
| **In-memory file system** | Composite tree; path resolution; `ls`/`mkdir`/`addContent` (`PyDSA/25_design/009`) | |
| **Snapshot array / time-based KV** | Per-key version lists + binary search (`PyDSA/25_design/012`) | |
| **Stack Overflow / Q&A site** | Votes and reputation rules; question/answer/comment Composite; tags; bounty state | |
| **Stock exchange order book** | Price-level maps + FIFO queues per level; match engine; order types as strategies | ✅ 013 |
| **Coupon / discount engine** | Rules as Specifications + actions; stacking and priority rules; idempotent redemption | |
| **Traffic signal controller** | State machine with timed transitions; injected clock; emergency override | |
| **Cricket / sports scoreboard** | Event-sourced ball-by-ball log; derived stats as projections | |
| **Distributed ID generator (class level)** | Snowflake bit layout; clock-moved-backwards handling (`SystemDesign/problems/022`) | |

---

## 14 · Practice plan

**Weeks 1–2 — foundations:** read `02`, `04`. Do `lld/008` (tic-tac-toe), `lld/009`
(cache), `lld/003` (vending) — they're small and exercise invariants, data structures, and
State.

**Weeks 3–4 — the core set:** `lld/001` parking lot, `002` elevator, `004` booking,
`005` Splitwise, `006` KV store. For each: 45-minute timer, attempt the `_question.py`
file cold, run its tests, then compare with the solution and write down the one design
point you missed.

**Weeks 5–6 — breadth and follow-ups:** `007`, `010`, `011`, `012`; then 6 Tier-2 problems
from §13 designed on paper in 20 minutes each; answer the 8 universal follow-ups (§8)
aloud for every problem.

**Ongoing:** one mock LLD round per week with a friend or recorded; re-solve a problem
cold after 7 and 21 days (`REVIEW_LEDGER.md` cadence).

---

## 15 · Self-scoring rubric

Score each 0–2 after a practice run. 16+ is interview-ready.

| # | Criterion | 0 | 1 | 2 |
|---|---|---|---|---|
| 1 | Requirements | None written | Listed, scope unclear | Written, scoped, non-functional included |
| 2 | Entities | God class / missing record entities | Mostly right | Right entities, value objects, discovered records |
| 3 | Invariants | Not identified | Some, owners unclear | Each named with its single owner |
| 4 | Abstractions | None or everywhere | Some justified | Exactly at variation points, justified aloud |
| 5 | <abbr title="Application Programming Interface">API</abbr> | Unclear | Signatures present | Minimal, typed, errors specified |
| 6 | Working code | Doesn't run | Happy path runs | Core flow + a failure path demonstrated |
| 7 | Code quality | Hard to read | OK | Clean names, enums, small methods, no magic numbers |
| 8 | Concurrency | Not mentioned | Mentioned vaguely | Race identified, critical section and granularity chosen |
| 9 | Extensibility | Not discussed | Asked and answered | Pre-empted with "which class changes" answers |
| 10 | Communication | Silent | Some narration | Drove the session with checkpoints |
