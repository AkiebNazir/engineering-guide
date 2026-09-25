# Software Engineering & Architecture

A single program is easy to reason about: one memory space, one team, one deploy.
Software engineering at scale is what happens once a system is too big for that —
split across services, teams, and years of change — and almost every idea in this
file is a way to keep that split from turning into chaos. This file starts with why
systems get split up at all, then goes as deep as an L5 interview loop expects: you
are expected to design systems that span multiple teams and evolve safely over
years. Design patterns (Factory, Singleton) are table stakes; this file covers
macro-architecture: boundaries, events, distributed transactions, and <abbr title="Application Programming Interface">API</abbr> evolution.

For the micro level (complexity, deep modules, naming, errors), read `SoftwareDesign/01_philosophy_of_software_design.md`. For <abbr title="Five core design principles intended to make software designs more understandable, flexible, and maintainable (Single responsibility, Open-closed, Liskov substitution, Interface segregation, Dependency inversion).">SOLID</abbr> and patterns, read `SystemDesign/best_practices/`.

## Foundations — Start Here If You're New to Software Architecture

**Monolith vs. services, in one picture.** A **monolith** is one deployable program:
every part of the business logic runs in the same process, calling other parts
through plain function calls. A **service-oriented** (or **microservices**)
architecture splits that logic into multiple independently deployable programs that
talk over the network instead of function calls. Neither is "correct" by default —
a monolith is simpler until a team or a scaling need outgrows it; splitting it badly
(one service per database table, say) creates a **distributed monolith**: all the
network overhead of services, none of the independence. §1 (DDD) is about splitting
along the right lines instead.

**Synchronous request vs. asynchronous event.** When service A calls service B and
*waits* for the answer before continuing, that's a **synchronous** call — simple to
follow, but A is now stuck if B is slow or down (**temporal coupling**). When A
instead publishes "this happened" and moves on, letting any interested service react
whenever it's ready, that's an **asynchronous event** — more resilient to one
service being slow, harder to trace end to end. §2 is entirely about this second
style and its trade-offs.

**What an <abbr title="Application Programming Interface">API</abbr> contract is.** An **<abbr title="Application Programming Interface">API</abbr>** is the agreed-upon shape of a request and
response between two services (or a service and its clients): which fields exist,
what they mean, what's required. Once other teams (or other companies' apps) depend
on that shape, changing it can break them — §4 is about changing an <abbr title="Application Programming Interface">API</abbr> without
breaking the programs that already depend on it.

**Why "it works with one service" gets hard with several.** A single database gives
you a transaction: multiple writes that all succeed or all fail together (see
`03_databases_deep_dive.md`'s <abbr title="Atomicity, Consistency, Isolation, Durability - A set of properties of database transactions intended to guarantee data validity despite errors.">ACID</abbr>). Once "reserve inventory" and "charge a card" are
two *different* services with two different databases, there's no single transaction
that covers both — §3 is entirely about how to still make that operation safe.

**Vocabulary you'll meet below, in one table:**

| Term | One-line meaning |
|---|---|
| Service / microservice | An independently deployable unit talking to others over the network |
| Distributed monolith | Services split along the wrong lines: all the network cost, none of the independence |
| Synchronous call | Caller waits for the response before continuing |
| Event | A published fact ("this happened"); publisher doesn't know or wait for consumers |
| <abbr title="Application Programming Interface">API</abbr> contract | The agreed shape of a request/response between two systems |
| Breaking change | An <abbr title="Application Programming Interface">API</abbr> change that an existing client can no longer handle correctly |

With that vocabulary, the rest of this file is the precise, L5-depth version of how
to draw those service boundaries, coordinate them safely, and evolve them over time.

## 1. Domain-Driven Design (DDD)

When a monolith becomes too complex, teams often split it into microservices arbitrarily (a service per noun). The result is a **distributed monolith**: every simple change touches five services, deployed in lockstep, with network calls where function calls used to be.

**DDD prevents this by drawing boundaries around business capabilities:**

```arch
%% caption: One real-world "Product", three bounded contexts, three different models; each context keeps only what it needs.
grid 240x110
group inv "Bounded Context: Inventory" color=blue icon=store
node p1 "Product" at 0,0 in inv shape=card icon=package sub="weight, warehouse, stock_count"
group cart "Bounded Context: Shopping Cart" color=orange icon=cart
node p2 "Product" at 0,1 in cart shape=card icon=package sub="id, price, image_url"
group ship "Bounded Context: Shipping" color=green icon=delivery
node p3 "Product" at 0,2 in ship shape=card icon=package sub="dimensions, fragile_flag"
p1 ..> p2 : "same entity, different models"
p2 ..> p3 : "same entity, different models"
```
*   **Ubiquitous Language:** Engineers and domain experts use the same terms in conversation and in code. If the business says "Client" and the code says "User", every conversation needs a translation, and translations breed bugs.
*   **Bounded Contexts:** A boundary within which a model is consistent. A "Product" in Inventory has weight and warehouse location; in Cart it has price and image. *Don't force one `Product` class to serve every context.* Contexts communicate through explicit contracts (APIs, events) and translation at the edge (an **anti-corruption layer** when integrating a legacy or external model).
*   **Aggregates:** A cluster of objects changed together as one consistency unit, accessed through its **Aggregate Root** (e.g., `Order` owns its `OrderItem`s). Invariants ("total equals the sum of items", "no more than 10 items") are enforced inside one aggregate within one transaction. Across aggregates, accept eventual consistency. Keep aggregates small; a huge aggregate becomes a lock-contention hotspot.
*   **Heuristic for service boundaries:** things that change together and must be consistent together belong together. Split along lines where eventual consistency is acceptable to the business.

## 2. Event-Driven Architectures

Synchronous request chains create **temporal coupling**: if service B is down or slow, A fails or slows too, and availability multiplies (three 99.9% services in series ≈ 99.7%).

### Events vs commands
*   **Command:** "ChargeCard" — addressed to one handler, expects it to happen, can be rejected.
*   **Event:** "OrderPlaced" — a fact that already happened, published to anyone interested; the publisher doesn't know the consumers.

Events decouple teams but make flows harder to see. Use them where the publisher genuinely shouldn't care who reacts.

### The Transactional Outbox
The classic bug: write to the database, then publish to Kafka. If the process crashes between the two, the event is lost (or published without the write). Fix: write the business change **and** an outbox row in the **same local transaction**; a relay (polling or change data capture) publishes outbox rows and marks them sent. Delivery becomes at-least-once, so consumers must be **idempotent** (dedupe by event ID).

### Event Sourcing
Instead of storing current state (`UPDATE account SET balance = 50`), store an append-only log of events (`AccountOpened`, `Deposited 100`, `Withdrew 50`) and derive state by replay.
*   **Pros:** Complete audit trail; reconstruct state at any past time; rebuild or add read models by replaying.
*   **Cons:** Schema evolution of events over years (upcasting), snapshotting for long streams, GDPR deletion in an immutable log (crypto-shredding: encrypt per-subject data and delete the key), and a steep learning curve. Use it where the history *is* the product (ledgers, audit-heavy domains), not by default.

### CQRS (Command Query Responsibility Segregation)
Often paired with event sourcing, but independent of it.

```arch
%% caption: CQRS: writes go through the command side to a normalized store; events build a denormalized read model the query side serves.
grid 190x120
node client "Client" at 0,0 icon=client
node client2 "Client" at 0,1 icon=client
group cs "Command side" color=orange icon=edit
node cmd "Command Side" at 1,0 in cs icon=service
node wdb "Write DB" at 2,0 in cs icon=db sub="normalized"
node bus "Event Bus" at 2,1 icon=event
group qs_g "Query side" color=blue icon=search
node qs "Query Side" at 1,1 in qs_g icon=service
node rdb "Read DB" at 1,2 in qs_g icon=db sub="denormalized"
client -> cmd : "POST /orders (write)"
cmd -> wdb
wdb -> bus : "emit OrderCreated"
bus -> qs
qs -> rdb
client2 -> qs : "GET /orders (read)"
```
*   **The Problem:** The model that enforces write invariants is rarely the shape that serves UI reads fast.
*   **CQRS:** The command side validates and writes to the write store and emits events; the query side consumes them into denormalized read models (search index, cache, materialized views).
*   **Cost:** read models are eventually consistent. The UI must handle "I just placed an order and it isn't in my list yet" (read-your-writes via the command response, or wait for projection offset).

## 3. Distributed Transactions: 2PC and Sagas

An order needs to reserve inventory (Inventory service) and charge a card (Payment service). They don't share a database, so one local `BEGIN ... COMMIT` can't cover both.

### Two-Phase Commit (2PC)
A coordinator asks every participant to **prepare** (durably promise it can commit, holding locks), then tells all to **commit** (or abort).
*   **Weaknesses:** locks are held across network round-trips; if the coordinator fails after prepare, participants **block** holding locks until it recovers; every participant must support the protocol (many message brokers and third-party APIs don't); availability is the product of all participants'.
*   **Precision note:** 2PC is not "never use." It's the right tool *inside* a database system that controls all participants and makes the coordinator highly available. **Spanner** runs 2PC across shards where each participant and the coordinator are Paxos-replicated groups, removing the blocking failure. The rule of thumb is: **avoid 2PC across independently owned microservices and external APIs**, where you can't make every participant replicated and protocol-aware.

### The Saga Pattern
A saga is a sequence of local transactions. Each step commits locally and triggers the next; if a step fails, **compensating transactions** semantically undo earlier steps.

```arch
node o "Order Service" at 0,0 icon=server color=blue
node p "Payment Service" at 1,0 icon=server color=purple
node i "Inventory Service" at 2,0 icon=server color=teal
o -> p : "Charge card"
p -> o : "PaymentSucceeded"
o -> i : "Reserve inventory"
i -> o : "InventoryFailed!"
node saga "Saga compensation begins" at 0,1 shape=card color=amber
o -> saga -> o
o -> p : "Refund card"
p -> o : "RefundComplete"
```

<div class="lab" data-viz="saga-pattern"></div>

*   **Choreography (decentralized):** Order emits `OrderCreated`; Payment reacts and emits `PaymentSucceeded`; Inventory reacts. *Pros:* no central component. *Cons:* flow logic is spread across services; hard to see and change past a few steps; cyclic dependencies creep in.
*   **Orchestration (centralized):** An orchestrator (a workflow engine such as Temporal, Cadence, Google Cloud Workflows, AWS Step Functions) calls each step and runs compensations on failure. *Pros:* the flow is explicit and observable. *Cons:* the orchestrator is a critical dependency and can become a "god service".
*   **Design rules:** order steps so the hardest-to-compensate step runs **last** (charge the card after reserving inventory, not before); make every step and compensation **idempotent** (retries happen); compensations can fail too, so they need retries and alerts; sagas give no isolation — other requests can see intermediate states, so use semantic locks (a `PENDING` status) where it matters.

## 4. <abbr title="Application Programming Interface">API</abbr> Evolution (Backward Compatibility)

L5 engineers don't break their clients, and they remember that mobile apps may run a years-old version.
*   **Additive changes are safe:** new optional fields, new endpoints, new enum values *if* clients tolerate unknown values.
*   **Breaking changes:** removing or renaming a field, changing a type or meaning, making an optional field required, tightening validation.
*   **Tolerant Reader:** clients ignore fields they don't recognize and don't depend on field order.
*   **Protocol Buffers rules:** never reuse or renumber a field tag; mark removed fields `reserved`; renaming is wire-safe but breaks <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> mappings and generated code; changing `int32` to `string` is breaking. Google publishes these practices as the **<abbr title="Application Programming Interface">API</abbr> Improvement Proposals (aip.dev)**.
*   **Deprecation cycle:** when a break is unavoidable, add `v2` alongside `v1`, measure who still calls `v1`, migrate them, announce a sunset date, and delete `v1` only when traffic is zero (or contractually allowed).
*   **Expand-and-contract for schema changes:** add the new column/field → dual-write → backfill → switch reads → stop writing the old one → drop it. Every step is independently deployable and reversible.

## 5. Engineering Practices That Signal Seniority

| Practice | What an L5 does |
|---|---|
| Design docs | Writes one before significant work: context, goals/non-goals, alternatives considered, trade-offs, rollout, risks. See `SoftwareDesign/13_design_docs_and_technical_leadership.md` |
| Code review | Reviews for correctness, design, and readability; keeps changes small; explains *why* |
| Testing | Unit tests for logic, a few integration tests for boundaries, contract tests between services; tests that fail for the right reason |
| Rollout | Feature flags, canaries, gradual percentage rollout, fast rollback, backward-compatible data changes |
| Monorepo and trunk-based development | Small frequent merges behind flags instead of long-lived branches (Google's model) |
| Dependency hygiene | Pin, update regularly, minimize transitive dependencies |
| Reliability ownership | SLOs for your service, runbooks, blameless postmortems with tracked action items |

## Interview checklist

- [ ] I can explain bounded contexts and aggregates and use them to justify a service split.
- [ ] I can explain the outbox pattern and why consumers must be idempotent.
- [ ] I can say when event sourcing and CQRS are worth their cost.
- [ ] I can compare 2PC and sagas precisely, including how Spanner makes 2PC safe.
- [ ] I can list breaking vs non-breaking <abbr title="Application Programming Interface">API</abbr> changes and the expand-and-contract migration.

Related: `SystemDesign/best_practices/05_architectural_patterns.md`, `SystemDesign/building_blocks/09_messaging_and_streaming.md`, `11_transactions_and_concurrency.md`; GoEngineering/PyEngineering topics 16-18.
