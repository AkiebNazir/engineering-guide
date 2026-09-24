# Extended Principles and the Field Reference

> "Everything should be made as simple as possible, but no simpler." — attributed to
> Albert Einstein

`01`–`14` are the track. This file is what's left after them: two named toolkits that
come up often enough in interviews and design reviews to deserve their own vocabulary —
**GRASP** (the sibling of SOLID that nobody defines precisely) and the **C4 model** (for
drawing architecture at the right zoom level, instead of one diagram that tries to be
every zoom level at once) — followed by a compact **field reference**: an index from
every term this track has used to the exact section that teaches it, and a one-screen
version of the LLD framework to glance at right before you walk in.

Nothing here is a prerequisite for anything else. Read the two toolkits once; use the
reference whenever you need to find something fast.

**Already covered elsewhere — not repeated here:**

| Topic | Where |
|---|---|
| SOLID | `02_oop_and_domain_modeling.md` §12 |
| UML class and sequence diagrams | `02_oop_and_domain_modeling.md` §13 |
| Fuzzing and property-based testing (runnable labs) | `PyEngineering/21_fuzzing_property_testing`, `GoEngineering/21_*` — §3 below says why this file doesn't re-teach it |
| The full 45-minute LLD framework | `14_low_level_design_interview_playbook.md` §3–§9 |
| Named-principle index (DRY, KISS, Law of Demeter, ...) | `01_philosophy_of_software_design.md` §17 |

---

## Contents

1. [GRASP: the names SOLID doesn't cover](#1--grasp-the-names-solid-doesnt-cover)
2. [Seeing architecture at the right zoom level: the C4 model](#2--seeing-architecture-at-the-right-zoom-level-the-c4-model)
3. [What this track deliberately doesn't re-teach](#3--what-this-track-deliberately-doesnt-re-teach)
4. [The complete topic index](#4--the-complete-topic-index)
5. [The LLD framework, one screen](#5--the-lld-framework-one-screen)
6. [Checklist](#6--checklist)

---

## 1 · GRASP: the names SOLID doesn't cover

GRASP (*General Responsibility Assignment Software Patterns*, Craig Larman) answers a
narrower question than SOLID: **given a job that needs doing, which class should do it?**
It's asked as nine questions. Five of them are this track's existing ideas under a
different name — worth knowing so you recognise the word when a book or an interviewer
uses it, but not worth re-teaching:

| GRASP name | The question | This track already covers it as |
|---|---|---|
| **Low Coupling** | Does this design minimise how much classes need to know about each other? | `03_modularity_coupling_and_api_design.md` §1, §3 |
| **High Cohesion** | Does everything inside this class share one reason to exist? | `03_modularity_coupling_and_api_design.md` §2 |
| **Polymorphism** | Does behaviour that varies by type dispatch through an interface, instead of an `if`/`elif` on type? | `02_oop_and_domain_modeling.md` §2 |
| **Protected Variations** | Is the part that's likely to change wrapped behind a stable interface, so the change can't ripple outward? | `01_philosophy_of_software_design.md` §4 (information hiding), `03` §4 (dependency direction) |
| **Indirection** | Is there a layer between two things that shouldn't depend on each other directly? | `08_application_architecture_in_code.md` §3 (ports and adapters) |

The other four name something this track hasn't given a word to yet. These are worth
learning properly.

### Creator: who should build a B?

**Question: who should be responsible for creating an instance of B?**

Larman's original heuristic: **A** should create **B** if A aggregates B, A contains B,
A records B, A closely uses B, or A has the data needed to initialize B. In short:
creation goes next to the data and the relationship, not wherever the code happened to
need a new object first.

```python
# WRONG: a standalone factory with no relationship to Order or its data,
# just because "factories create things."
class OrderLineFactory:
    @staticmethod
    def create(product: Product, qty: int) -> "OrderLine":
        return OrderLine(product, qty, product.price)

order.lines.append(OrderLineFactory.create(product, 2))   # Order had nothing to do with it

# RIGHT: Order AGGREGATES its lines and HAS the data (the product's current
# price) to build one correctly — Creator says Order should do it.
class Order:
    def add_line(self, product: Product, qty: int) -> None:
        self._lines.append(OrderLine(product, qty, product.price))
```

The payoff is the same one `02_oop_and_domain_modeling.md` §8 makes about aggregates:
`OrderLine` can never exist half-built or with a stale price, because the only door to
create one is a method on the object that owns the invariant.

### Information Expert: put the behaviour next to the data

**Question: which class already has the data needed to do this?** Give it the job,
instead of pulling the data out to wherever the job is being done.

```python
# WRONG: ReportService reaches into Invoice's data to do Invoice's arithmetic.
class ReportService:
    def total_for(self, invoice: "Invoice") -> Decimal:
        return sum(line.amount for line in invoice.lines)

# RIGHT: Invoice is the expert on its own lines.
class Invoice:
    def total(self) -> Decimal:
        return sum(line.amount for line in self._lines)
```

This is the general principle behind "Tell, don't ask" (`02` §9) — Tell-don't-ask is
Information Expert applied specifically to the moment you're tempted to pull data out of
an object to make a decision about it outside.

### Pure Fabrication: inventing a class that isn't in the business's vocabulary

**Question: is there a class here that doesn't model anything a domain expert would
recognise, invented purely to keep coupling low or cohesion high?**

Nobody at the company says "go check the repository." `OrderRepository` isn't a business
concept — it's a **pure fabrication**, invented so that `Order` (a real domain concept)
doesn't have to import a database driver to save itself. Without it, you'd face a direct
trade-off: either `Order` knows how to talk to Postgres (low cohesion — business rules
and SQL in one class) or nothing does (nowhere for persistence logic to live at all).

```python
# Order stays a pure domain concept: no imports below the line a
# domain expert could reasonably be shown.
class Order:
    def add_line(self, product: Product, qty: int) -> None: ...
    def total(self) -> Decimal: ...

# OrderRepository is a pure fabrication: it exists ONLY to keep the
# persistence concern (a real, necessary job) out of Order.
class OrderRepository(Protocol):
    def save(self, order: Order) -> None: ...
    def get(self, order_id: str) -> Order: ...
```

Most of the Design Patterns catalog is pure fabrications: `Repository`, `Factory`,
`Adapter`, `Strategy` — none of them are domain nouns. That's not a flaw; it's what the
principle predicts. `04_design_patterns_in_practice.md` §16 covers Repository in depth.

### Controller: the first stop after the UI

**Question: what's the first non-UI object that receives a system event and coordinates
the response?**

This predates, and is broader than, "the Controller in MVC" — a web framework's
controller is one instance of GRASP's Controller, not the definition of it. The point is
narrower and stricter than "wherever the request lands": a Controller **receives and
delegates**; it does not contain business rules itself.

`08_application_architecture_in_code.md`'s worked example already draws this line
precisely, just without this name: `adapters/http.py` (parses the HTTP request, calls the
use case, maps the result to a response) is the Controller; `application/place_order.py`
(the actual use case) is where the orchestration — and only the orchestration, no SQL, no
HTTP — happens. Confusing the two is the "pass-through method" smell from `01` §6 in one
direction, and a fat, untestable HTTP handler in the other.

```python
# WRONG: the controller contains the business rule itself — it can't be
# reached from a CLI or a queue consumer, and it can't be tested without HTTP.
class OrderController:
    def handle_place_order(self, request: dict) -> dict:
        if request["quantity"] <= 0:
            raise ValueError("quantity must be positive")
        total = request["quantity"] * request["unit_price"]
        if total > request["account_credit_limit"]:
            raise ValueError("over credit limit")
        # ... the actual order-placing logic lives here too ...
        return {"status": "placed", "total": total}

# RIGHT: the controller only translates HTTP <-> domain calls; PlaceOrder
# owns the rule, and is reachable — and testable — from anywhere.
class OrderController:
    def __init__(self, place_order: "PlaceOrder") -> None:
        self._place_order = place_order

    def handle_place_order(self, request: dict) -> dict:
        result = self._place_order.execute(
            quantity=request["quantity"], unit_price=request["unit_price"]
        )
        return {"status": "placed", "total": result.total}
```

---

## 2 · Seeing architecture at the right zoom level: the C4 model

"Draw the architecture" is an underspecified request. A diagram that mixes an AWS region
boundary, three microservices, and "this class calls that method" in one picture isn't
wrong so much as **answering three different questions at once**, at a zoom level nobody
asked for. The C4 model (Simon Brown) fixes this the way a map fixes it: **pick a zoom
level, draw only what belongs at that level, label the level.**

```
 zoom OUT ─────────────────────────────────────────────────────────  zoom IN

 1. SYSTEM CONTEXT    2. CONTAINER          3. COMPONENT      4. CODE
 your system as        the deployable        one container's   class diagram
 one box, plus the     units inside it        internal          (`02` §13) —
 people and other      and how they talk      building blocks   for the one
 systems around it     (this is usually        and their calls   tricky part,
                        what "draw the                           not the whole
                        architecture" means                      system
                        in an interview)
```

### Level 1 — System Context

One box for your whole system, the people who use it, and the other systems it talks to.
No internals — if you can see a database or a service boundary, you've zoomed in too far.
This is the diagram you'd show someone who needs to understand *what the system is and
what touches it*, not how it's built.

```
                 ┌──────────────┐
                 │   Customer   │
                 └──────┬───────┘
                        │ places orders
                        ▼
   ┌──────────┐   ┌───────────────────┐   ┌──────────────┐
   │  Support │──▶│   Ordering System │──▶│ Payment       │
   │  Agent   │   │   (this system)    │   │ Provider      │
   └──────────┘   └─────────┬──────────┘   └──────────────┘
                             │ sends confirmation
                             ▼
                       ┌──────────┐
                       │  Email   │
                       │ Provider │
                       └──────────┘
```

### Level 2 — Container

Zoom into the one box from Level 1. Each **container** here is a separately
deployable/runnable thing — a service, a web app, a mobile app, a database, a queue —
with the protocol connecting them. **This is what most system-design interviews mean**
when they say "draw the architecture," and what `SystemDesign/` is about in depth.

```
   ┌────────────┐  HTTPS  ┌──────────────────┐   SQL   ┌─────────────┐
   │  Web App   │────────▶│  Ordering API     │────────▶│  Postgres    │
   └────────────┘         │  (this repo's     │         └─────────────┘
                          │  worked example)  │
                          └─────────┬─────────┘
                                    │ publishes OrderPlaced
                                    ▼
                             ┌────────────┐
                             │   Queue    │
                             └────────────┘
```

### Level 3 — Component

Zoom into ONE container. The boxes are the major internal building blocks — roughly,
top-level packages — and the arrows are calls between them. `08`'s worked "place order"
example already draws exactly this level, just without the C4 name: `domain/`,
`application/`, `adapters/sqlite_orders.py`, `adapters/http.py` as boxes, the dependency
rule from `08` §3 as the arrows. Don't redraw it here — see `08` §4.

### Level 4 — Code

Class diagrams: `02` §13's "UML you actually need." Draw this for the one tricky flow,
never for the whole system — a class diagram of everything is the "shallow module" smell
(`01` §3) applied to a picture instead of code: technically complete, not actually useful.

### Using this in an interview or a design doc

- When someone says "draw the architecture" and it's ambiguous which level they want,
  **ask** — "container-level, or are you asking about one service's internals?" This is
  itself a strong signal (`14` §4's "clarify first" habit, applied to diagrams).
  `13_design_docs_and_technical_leadership.md` §3's design-doc structure implicitly wants
  a Container-level diagram in the "Overview" and reserves Component/Code detail for the
  sections that need it.
- **Never mix levels in one diagram.** A box for "the database" next to a box for "the
  `OrderRepository` class" is two zoom levels colliding — split them.
- You don't need the official C4 notation or tooling. The value is the **discipline of
  one level per diagram**; ASCII boxes on a whiteboard or in a doc, like every diagram in
  this track, carry the idea fine.

---

## 3 · What this track deliberately doesn't re-teach

Two topics that belong conceptually in a "software design" track already have a full,
runnable treatment elsewhere in this repo, and repeating them here would mean two places
to keep in sync — this track's own standing rule against duplication:

- **Property-based and fuzz testing** — generating random inputs from a spec instead of
  writing individual examples, and shrinking a failing case down to a minimal one. Fully
  covered, runnable, in `PyEngineering/21_fuzzing_property_testing` (Hypothesis) and
  `GoEngineering/21_*` (`testing/quick`, `go test -fuzz`). `05_testability_refactoring_and_legacy_code.md`
  §2 already points there instead of repeating it, and `07` §12 and `12` §13 reference the
  same labs for concurrency and parser-fuzzing specifically.
- **Mutation testing** (deliberately breaking your code to check your tests actually
  fail) is the natural next question after property-based testing — not yet a dedicated
  lab in this repo. If you're using it: run it after your test suite is green, not
  instead of writing tests deliberately (`05` §5's "behaviour, not implementation" still
  decides what a good test looks like; a mutation score just tells you where you have
  none).

If you came here looking for either, that's genuinely the right next stop — this
section exists so the index in §4 doesn't send you in circles looking for a copy of it
in this file.

---

## 4 · The complete topic index

Every term this track uses more than once, alphabetically, with exactly where it's
taught. Use this the way you'd use the index at the back of a book — you know the word,
you don't remember which chapter.

| Term | Where |
|---|---|
| Actor model / single writer | `07` §7 |
| Aggregate | `02` §8 |
| Anemic model | `02` §3 |
| Async races / structured concurrency | `07` §8–§9 |
| Backward / forward compatibility | `09` §2 |
| C4 model | `15` §2 (this file) |
| Chain of Responsibility | `04` §11 |
| Circuit breaker (fleet-scale; this track covers retries, not breakers) | `06` §7; `SystemDesign/building_blocks/12_application_resilience_patterns.md` |
| Cohesion | `03` §2 |
| Compensation / saga | `06` §9 |
| Composite / Visitor | `04` §12 |
| Composition over inheritance | `02` §4 |
| Connascence | `03` §3 |
| Controller (GRASP) | `15` §1 (this file) |
| Coupling | `03` §1 |
| CQRS-lite | `08` §10 |
| Creator (GRASP) | `15` §1 (this file) |
| Deep module | `01` §3 |
| Dependency injection | `08` §8 |
| Design doc structure / ADR | `13` §3, §7 |
| Design it twice | `01` §15 |
| Fail fast vs. defensive | `06` §10–§11; `12` §1 |
| Functional core, imperative shell | `01` §9 |
| GRASP | `15` §1 (this file) |
| Hexagonal / ports and adapters | `08` §3 |
| Idempotency | `06` §8 |
| Illegal states unrepresentable / parse don't validate | `01` §8 |
| Information Expert (GRASP) | `15` §1 (this file) |
| Information hiding / leakage | `01` §4 |
| Invariant | `02` §3 |
| Law of Demeter / tell don't ask | `02` §9 |
| Observability: logs, metrics, traces | `10` §2, §4, §5 |
| Observer / Pub-Sub | `04` §7 |
| Optimistic concurrency | `14` §9; `PyEngineering/10_transactions_concurrency_control`, `SystemDesign/building_blocks/11` |
| Package principles / dependency direction | `03` §4–§5 |
| Pattern overuse | `04` §19 |
| Performance: batch-shaped APIs, streaming | `11` §3, §5 |
| Protected Variations (GRASP) | `15` §1 (this file) |
| Pull complexity downward | `01` §5 |
| Pure Fabrication (GRASP) | `15` §1 (this file) |
| Rate limiting | `lld/012_rate_limiter`; `12` §6 (resource exhaustion) |
| Repository / Unit of Work | `04` §16 |
| Retries and backoff | `06` §7 |
| Reversibility: one-way vs. two-way doors | `13` §10 |
| SOLID | `02` §12 |
| Specification (filter composition) | `04` §15 |
| State pattern | `04` §9 |
| Strategy | `04` §3 |
| Structured logging | `10` §2 |
| Tail latency / hedging | `11` §7 |
| Testability seams / test doubles | `05` §3–§4 |
| Threat modeling / trust boundaries | `12` §1, §12 |
| Tolerant reader / upcaster | `09` §4 |
| UML (class + sequence) | `02` §13 |
| Value object vs. entity | `02` §7 |
| Zero-downtime migration (expand/contract) | `09` §5 |

---

## 5 · The LLD framework, one screen

Full teaching, talk tracks, and the question bank are in `14_low_level_design_interview_playbook.md`.
This is the compressed version — read it in the elevator, not instead of `14`.

```
 0 ──── 5 ──────── 12 ────── 17 ──────────────────────── 37 ──────── 45  (minutes)
 │      │           │         │                            │          │
 start  clarify     model     API                          code       extend
        done        done      agreed                       done       done
```

| Step | Minutes | Do this | If you skip it |
|---|---|---|---|
| 1. Clarify | 0–5 | Functional AND non-functional requirements (`00` §7). State what's out of scope out loud. | You design the wrong thing confidently. |
| 2. Model | 5–12 | Entities, relationships, invariants, who owns each one. | A god class, or invariants enforced nowhere. |
| 3. API | 12–17 | Public methods and the key flows, in words or a quick class diagram (`02` §13). | You start typing before you know the shape. |
| 4. Code | 17–37 | The core, with the ONE thing that varies behind an interface (`04` §1–§2). | Everything hardcoded; the first follow-up breaks it. |
| 5. Extend | 37–45 | Concurrency, a follow-up requirement, tests out loud. | Looks like you never think past the happy path. |

**The ten-second self-check, any time you're stuck:** *what rule does this class
protect, and is there exactly one door it's enforced through?* (`00` §3). If you can
answer that for every class on the board, you have a design, not just a diagram.

---

## 6 · Checklist

- [ ] Can you name the four GRASP principles this track hadn't already covered, and
      give one example of each without looking back?
- [ ] Given "draw the architecture," can you say which C4 level answers it, and why the
      other three would be the wrong answer to that question?
- [ ] Could you find any term from `01`–`14` in under ten seconds using §4, without
      re-opening the chapter you think it's in?
- [ ] Do you know where property-based testing already lives in this repo, so you're not
      tempted to look for a second copy of it?
