# Architectural Patterns

These patterns operate at the system/application level — how modules, layers, and services relate — distinct from the object-level GoF patterns in files [02](02_design_patterns_creational.md)-[04](04_design_patterns_behavioral.md). This file assumes familiarity with the request-path building blocks in `../building_blocks/`.

## Layered architecture

Organize code into horizontal layers (presentation → business logic → data access), each depending only on the layer below it.

```text
Presentation  →  Application/Business  →  Data Access  →  Database
```

**Strength:** simple, well-understood, easy to onboard onto. **Cost:** a strict layering can force pass-through code (every field trickles through every layer) and tempts business logic to leak into the layer that's easiest to edit (usually the controller), producing a de facto anemic model (see [07](07_anti_patterns_and_code_smells.md)).

## Hexagonal / ports and adapters

The domain sits in the center, exposing **ports** (interfaces) for what it needs (a repository, a notifier) and what it offers (a use case). **Adapters** implement those ports against real infrastructure (Postgres, SMTP, HTTP).

```text
        ┌───────────────── adapters (infrastructure) ─────────────────┐
        │  REST controller     Postgres repo      SMTP client         │
        │        │                   │                  │             │
        └────────┼───────────────────┼──────────────────┼─────────────┘
                 port                port               port
                  │                   │                  │
              ┌───┴───────────────────┴──────────────────┴───┐
              │            domain / application core          │
              └────────────────────────────────────────────────┘
```

The domain depends on port interfaces it defines; infrastructure depends on the domain, never the reverse. This is DIP ([01](01_design_principles.md)) applied at the architecture level, and it's what makes the domain testable with fake adapters instead of real infrastructure.

## Clean architecture (dependency rule)

Generalizes hexagonal into concentric rings: entities → use cases → interface adapters → frameworks/drivers. The **dependency rule**: source-code dependencies point only inward, toward the domain; nothing in an inner ring knows the name of anything in an outer ring.

```text
┌─────────────────────────────────────────┐
│  Frameworks & Drivers (DB, web, UI)      │
│  ┌─────────────────────────────────┐    │
│  │  Interface Adapters (controllers) │   │
│  │  ┌───────────────────────────┐  │    │
│  │  │  Use Cases (application)  │  │    │
│  │  │  ┌─────────────────┐     │  │    │
│  │  │  │   Entities        │     │  │    │
│  │  │  │   (domain)         │◄───┼──┼────┼── dependencies point inward
│  │  │  └─────────────────┘     │  │    │
│  │  └───────────────────────────┘  │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**Cost:** more files, more interfaces, more indirection than a layered CRUD app needs — earns its keep when domain logic is genuinely complex and must outlive specific frameworks/DB choices, not for a thin CRUD wrapper.

## MVC and MVVM

| Pattern | Split | Fits |
|---|---|---|
| MVC | Model (state/logic), View (render), Controller (input → model mutation, selects view). | Server-rendered web apps, most web frameworks' default shape. |
| MVVM | Model, View (declarative, data-bound), ViewModel (exposes view state/commands, no direct view reference). | Rich client/mobile UIs with two-way data binding (WPF, SwiftUI-adjacent, some SPA frameworks). |

MVVM's payoff is data-binding-driven UI testability (test the ViewModel with no UI rendered); it's overkill for a thin server-rendered page where MVC's controller already does the job in three lines.

## Monolith vs. microservices

The real trade-off is not "microservices are better." It is deployment/ownership boundaries versus operational/network complexity.

| Dimension | Monolith | Microservices |
|---|---|---|
| Deployment | One unit; simpler pipeline. | Independent deploys per service; more pipelines to maintain. |
| Team ownership | Contention on shared codebase as team grows. | Clear ownership boundary per service, enables independent teams. |
| Transactions | In-process ACID transactions across modules. | Cross-service transactions require sagas/eventual consistency (see [08 — checkout solution](../solutions/008_checkout_solution.md) for a worked example). |
| Failure isolation | One bug can crash the whole process. | A failing service degrades gracefully if callers have timeouts/circuit breakers — but now failure is distributed and harder to trace. |
| Operational cost | One thing to deploy, monitor, scale. | N services × (deploy pipeline, on-call surface, service discovery, network hop latency, distributed tracing needs). |
| Refactoring | Easy — compiler/IDE sees the whole codebase. | A cross-service refactor requires coordinated multi-repo/multi-team changes. |

Default to a monolith until a real organizational boundary (independent scaling needs, independent deploy cadence, independent team ownership) justifies paying the network/operational tax of splitting it. Splitting too early produces a "distributed monolith" — all the network cost, none of the independence, because services still deploy in lockstep.

## Event-driven architecture

Services communicate by publishing and reacting to events instead of direct synchronous calls. Decouples producer from consumer (the producer doesn't know or care who's listening) and naturally buffers load spikes. Cost: causality becomes harder to trace (no linear call stack across services), and every event needs an ordering story, a retry/DLQ story, and a schema-evolution story. See `../building_blocks/09_messaging_and_streaming.md` for the delivery-guarantee and ordering mechanics.

## CQRS (command/query responsibility segregation)

Split the write model (commands, enforces invariants) from the read model (queries, optimized for retrieval), potentially backed by different schemas or even different databases kept in sync via replication or events.

**Earns its complexity when:** read and write access patterns diverge sharply (e.g., writes are narrow and transactional, reads need denormalized, highly indexed, differently-shaped views for many different UI screens), or when read and write load need independent scaling. Ties directly to replication trade-offs in `../building_blocks/06_database_internals.md` — the read model is usually a replica or a materialized projection, and staleness between write and read model is the cost you're accepting.

**Don't use it as:** a default for a simple CRUD screen with one reasonable read shape — a single model with one repository already does the job, and CQRS adds a synchronization pipeline you now have to operate and debug when the two sides disagree.

## Event sourcing

Persist state as an append-only log of domain events (`OrderPlaced`, `OrderShipped`) rather than persisting current state directly; current state is derived by replaying events.

**Real cost, not just "more auditable":**

- **Replay complexity:** rebuilding current state means replaying the full event log (or a snapshot + tail), which gets slow as history grows.
- **Schema evolution of events:** an event schema, once emitted, is effectively permanent — old events must still be replayable years later, so changing an event's shape requires versioning/upcasting logic, not just editing a class.
- **Snapshotting:** required once replay-from-zero is too slow, which adds its own consistency concerns (snapshot must correspond to an exact event offset).

Choose it when audit trail, temporal queries ("what did this look like last Tuesday"), or the ability to derive new read models retroactively from history are real product requirements — not as a default persistence strategy.

## Domain-driven design basics

The essentials that matter in an interview or a real design review:

| Concept | Definition | Why it matters |
|---|---|---|
| Bounded context | An explicit boundary within which a model and its terms have one consistent meaning. | The same word ("Customer") can mean different things in Billing vs. Support — DDD says don't force one shared model across both; define the boundary and translate at the edge. |
| Aggregate | A cluster of entities/value objects treated as one consistency boundary, with one aggregate root that enforces invariants for the whole cluster. | Tells you where a transaction boundary should be: mutate one aggregate per transaction; cross-aggregate consistency is eventual, not enforced by a DB constraint. |
| Entity | Has a persistent identity that outlives attribute changes (a `User` is still the same user after a name change). | Identity, not attribute equality, is what you compare and reference. |
| Value object | Defined entirely by its attributes, immutable, no identity (`Money(amount, currency)`). | Safe to freely copy/compare/share — no aliasing bugs, no lifecycle to track. |
| Ubiquitous language | The team and the code use the same vocabulary as the domain experts, with no translation layer. | A mismatch between what the business calls something and what the code calls it is a standing source of miscommunication and subtly wrong logic. |

## Related

- [01 — Design principles](01_design_principles.md) — DIP is the principle behind hexagonal/clean architecture.
- `../building_blocks/06_database_internals.md` — replication mechanics behind CQRS read models.
- `../building_blocks/09_messaging_and_streaming.md` — delivery/ordering guarantees behind event-driven architecture and event sourcing.
- [../solutions/008_checkout_solution.md](../solutions/008_checkout_solution.md) — a worked saga example for the monolith-vs-microservices cross-service transaction trade-off.
