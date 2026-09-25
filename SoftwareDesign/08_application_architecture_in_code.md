# Application Architecture in Code: Layers, Ports & Adapters, and Wiring

> "The goal of software architecture is to minimize the human resources required to build
> and maintain the required system." — Robert C. Martin
>
> "Architecture is the decisions that you wish you could get right early in a project."
> — Ralph Johnson

Files `01`–`04` work at the level of a function, a class, or a module. This file goes one
level up: **how the code inside one service or application is arranged** — what depends
on what, where the business rules live, where I/O happens, and how the pieces get wired
together at startup.

Get this right and a codebase stays changeable for years: the database can be swapped
in a test for a dictionary, a new <abbr title="Application Programming Interface">API</abbr> (<abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> next to <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr>) is a new adapter rather than
a rewrite, and business rules can be read without wading through <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>. Get it wrong and
every change touches controllers, models, and <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> at once.

Examples are in **Python** with a **Go** translation in §12. The worked example in §4 is
a complete program: concatenate its code blocks in order and it runs.

**Already covered elsewhere — not repeated here:**

| Topic | Where |
|---|---|
| Short survey: layered, hexagonal, clean, MVC, CQRS, event sourcing | `SystemDesign/best_practices/05_architectural_patterns.md` |
| Bounded contexts, events, outbox, sagas (service scale) | `CSFundamentals/04_software_engineering_deep_dive.md` |
| Functional core / imperative shell | `01_philosophy_of_software_design.md` §9 |
| Entities, value objects, aggregates | `02_oop_and_domain_modeling.md` §7–§8 |
| Dependency direction, package metrics, modular monolith seams | `03_modularity_coupling_and_api_design.md` §4, §12 |
| Repository and Unit of Work patterns | `04_design_patterns_in_practice.md` §16 |
| Test doubles and fakes | `05_testability_refactoring_and_legacy_code.md` §4 |
| Runnable DI/layering projects | `PyEngineering/18_dependency_injection_layering`, `GoEngineering/18_*`, `25_production_service_capstone` |

---

## Contents

1. [What architecture means inside one service](#1--what-architecture-means-inside-one-service)
2. [Layered architecture and its one big flaw](#2--layered-architecture-and-its-one-big-flaw)
3. [The dependency rule: hexagonal, onion, clean are one idea](#3--the-dependency-rule-hexagonal-onion-clean-are-one-idea)
4. [Worked example: "place order", every layer, runnable](#4--worked-example-place-order-every-layer-runnable)
5. [Where does each concern go?](#5--where-does-each-concern-go)
6. [Data shapes across boundaries: DTO, domain model, persistence model](#6--data-shapes-across-boundaries-dto-domain-model-persistence-model)
7. [Transactions belong to the use case](#7--transactions-belong-to-the-use-case)
8. [Dependency injection without a framework](#8--dependency-injection-without-a-framework)
9. [Cross-cutting concerns: keep them at the edges](#9--cross-cutting-concerns-keep-them-at-the-edges)
10. [Reads are different: CQRS-lite](#10--reads-are-different-cqrs-lite)
11. [How much architecture? Transaction script vs. domain model](#11--how-much-architecture-transaction-script-vs-domain-model)
12. [The same design in Go](#12--the-same-design-in-go)
13. [Package layout and enforcing boundaries](#13--package-layout-and-enforcing-boundaries)
14. [Anti-patterns](#14--anti-patterns)
15. [Interview questions and model answers](#15--interview-questions-and-model-answers)
16. [Checklist](#16--checklist)

---

## 1 · What architecture means inside one service

Inside one deployable, "architecture" comes down to answers to four questions:

| Question | Bad answer | Good answer |
|---|---|---|
| **Where do business rules live?** | Scattered across <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> handlers, <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> models, <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>, and cron scripts | In one place (domain objects / pure functions), each rule once |
| **What depends on what?** | Everything imports everything; the domain imports the <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> | Dependencies point **toward** the business rules, never away from them |
| **Where does I/O happen?** | Anywhere, including deep inside calculations | At the edges: adapters called by a thin orchestration layer |
| **Who decides which implementation is used?** | Each class constructs its own collaborators | One composition root (`main`) wires everything |

The reason these matter is **rate of change**. Business rules change when the business
changes. Frameworks, databases, and transports change on a completely different
schedule and for different reasons. An architecture separates things that change for
different reasons so that each kind of change touches one area.

A useful test: **could you run your core business logic from a unit test with no
database, no network, no web framework, and no clock?** If yes, the architecture is
doing its job. If no, find out which import makes it impossible — that import is the
architectural problem.

---

## 2 · Layered architecture and its one big flaw

The classic arrangement (also called n-tier):

```
 ┌──────────────────────────────┐
 │ Presentation (HTTP, CLI, UI) │
 └──────────────┬───────────────┘
                │ depends on
 ┌──────────────▼───────────────┐
 │ Business / service layer     │
 └──────────────┬───────────────┘
                │ depends on
 ┌──────────────▼───────────────┐
 │ Data access (ORM, SQL)       │
 └──────────────┬───────────────┘
                ▼
            Database
```

- **Strict layering:** each layer may call only the one directly below. Safe, but
  creates pass-through methods (`01` §6) when a layer has nothing to add.
- **Relaxed layering:** a layer may call any layer below. Less boilerplate, weaker
  guarantees.

**What it gets right:** presentation code does not contain <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>; there is a place for
business logic.

**The flaw:** the arrows point **down toward the database**. The business layer
depends on the data-access layer, so:

1. You cannot test business rules without a database (or mocking the <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr>).
2. Data-access types (`OrderRow`, `SQLAlchemy Model`) leak upward into business code,
   and then into <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> responses.
3. The database schema becomes the de facto domain model — "design the tables first,
   then write services that shuffle rows" — producing an anemic model (`02` §3).

```python
# LAYERED, DB-CENTRIC: the business rule imports the persistence technology.
from sqlalchemy.orm import Session
from app.models import OrderRow          # ORM model = domain model = API shape

class OrderService:
    def __init__(self, session: Session):
        self.session = session

    def cancel(self, order_id: str) -> None:
        row = self.session.get(OrderRow, order_id)
        if row.status == "shipped":       # the rule...
            raise ValueError("already shipped")
        row.status = "cancelled"          # ...is tangled with row mutation and a session
        self.session.commit()
```

Nothing here is terrible in a small app. The problem appears when the rule gets harder,
when a second entry point (a queue consumer) needs the same rule, or when tests take
minutes because every one of them needs a database.

---

## 3 · The dependency rule: hexagonal, onion, clean are one idea

Hexagonal architecture (Alistair Cockburn, "ports and adapters"), onion architecture
(Jeffrey Palermo), and clean architecture (Robert Martin) differ in diagrams and
vocabulary. They share **one rule**:

> **Source-code dependencies point inward, toward the business rules. Inner code knows
> nothing about outer code.**

The trick that makes it possible is **dependency inversion**: when the core needs
something from the outside (store an order, charge a card), the core **defines an
interface in its own vocabulary**, and the outside **implements** it.

```
                 DRIVING side                                  DRIVEN side
            (things that call us)                         (things we call)

  ┌────────────┐   ┌────────────┐                     ┌────────────┐   ┌────────────┐
  │ HTTP       │   │ Queue      │                     │ SQLite /   │   │ Stripe     │
  │ handler    │   │ consumer   │                     │ Postgres   │   │ client     │
  └─────┬──────┘   └─────┬──────┘                     └─────▲──────┘   └─────▲──────┘
        │ calls          │ calls                 implements │    implements  │
  ══════╪════════════════╪══════ ADAPTERS ═════════════════╪════════════════╪═══════
        ▼                ▼                                  │                │
  ┌──────────────────────────────┐          ┌──────────────┴────────────────┴─────┐
  │ Driving port: the use case   │ ───uses─▶│ Driven ports: OrderRepository,      │
  │ PlaceOrder(cmd) -> order_id  │          │ PaymentGateway, Clock  (interfaces) │
  └──────────────┬───────────────┘          └─────────────────────────────────────┘
                 │ uses
         ┌───────▼────────┐
         │ DOMAIN         │   Order, Money, Line, rules, domain errors
         │ (pure Python)  │   imports nothing outside the standard library
         └────────────────┘
```

Vocabulary:

| Term | Meaning | Example |
|---|---|---|
| **Domain** | Entities, value objects, rules. No I/O. | `Order.place`, `Money.__add__` |
| **Application / use case** | Orchestrates one user intention: load, call domain, save, notify. No rules of its own. | `PlaceOrder`, `CancelOrder` |
| **Port** | An interface owned by the core | `OrderRepository`, `PaymentGateway` |
| **Driving (primary) port** | How the outside invokes the core | The `PlaceOrder` callable |
| **Driven (secondary) port** | What the core needs from the outside | `OrderRepository` |
| **Adapter** | Technology-specific code that implements or calls a port | `SqliteOrderRepository`, <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> handler |
| **Composition root** | The one place concrete adapters are chosen and wired | `main.py` / `cmd/server/main.go` |

In miniature, before the full worked example in §4 — the whole idea is dependency
inversion: the core declares the port it needs, in its own vocabulary, and an adapter
implements it.

```python
# THE IDEA IN FIFTEEN LINES, before the full worked example in §4.
from typing import Protocol

class GreetingRepository(Protocol):      # port: owned by the core, in the core's vocabulary
    def name_for(self, user_id: str) -> str: ...

class GreetUser:                         # core: the use case. Knows nothing about storage.
    def __init__(self, repo: GreetingRepository):
        self._repo = repo
    def __call__(self, user_id: str) -> str:
        return f"Hello, {self._repo.name_for(user_id)}!"

class InMemoryUsers:                     # adapter: implements the port, no "implements" keyword needed
    def __init__(self, names: dict[str, str]):
        self._names = names
    def name_for(self, user_id: str) -> str:
        return self._names[user_id]

greet = GreetUser(InMemoryUsers({"u1": "Ada"}))
print(greet("u1"))
```

Output:

```
Hello, Ada!
```

Swap `InMemoryUsers` for a `SqlUsers` that queries a database and `GreetUser` does not
change one line — that swap is the entire payoff of §3, scaled up in §4.

**Clean architecture's** concentric rings are the same thing with one more split:
Entities (enterprise rules) → Use Cases (application rules) → Interface Adapters
(controllers, presenters, gateways) → Frameworks & Drivers (web, DB). **Onion** says the
same with "domain model / domain services / application services / infrastructure".
In an interview, name the rule, not the diagram.

**Why the direction matters, concretely:**

| Change | Layered (DB-centric) | Ports & adapters |
|---|---|---|
| Unit-test a business rule | Needs a DB or <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> mocks | Plain objects, milliseconds |
| Add a queue consumer entry point | Copy logic from the controller, or call the controller | New driving adapter calling the same use case |
| Move from <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> to <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> | Rules tangled with request objects must be untangled | New driving adapter |
| Swap Postgres → DynamoDB | Every service touching `Session` changes | New repository adapter; core untouched |
| Upgrade the <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> major version | Touches business code | Touches adapters only |

Be honest about the last two rows: swapping databases is **rare**, and a repository
interface does not magically hide transactional or query-capability differences. The
real, everyday payoff is rows one and two: **fast tests and multiple entry points.**

---

## 4 · Worked example: "place order", every layer, runnable

Requirement: a customer places an order for some SKUs. Prices come from a catalog. The
order must have 1–50 lines with positive quantities. The card is charged; if it is
declined, the order is cancelled. Once paid, an `OrderPaid` event is published.

The blocks below are one file split by the module they would live in. Concatenated in
order, they run and print `ALL PASSED`.

### 4.1 Domain — rules, no I/O

```python
# ───────────────────────── domain/ ─────────────────────────
# Pure Python. Imports nothing from the application, adapters, or any library.
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Protocol
import uuid


class DomainError(Exception): ...
class NotFound(DomainError): ...
class InvalidOrder(DomainError): ...
class PaymentDeclined(DomainError): ...


@dataclass(frozen=True)
class Money:
    cents: int
    currency: str = "USD"

    def __post_init__(self):
        if self.cents < 0:
            raise InvalidOrder("money cannot be negative")

    def __add__(self, other: Money) -> Money:
        if other.currency != self.currency:
            raise InvalidOrder("currency mismatch")
        return Money(self.cents + other.cents, self.currency)

    def times(self, n: int) -> Money:
        return Money(self.cents * n, self.currency)


@dataclass(frozen=True)
class Line:
    sku: str
    unit_price: Money
    qty: int


class Status(Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"


@dataclass
class Order:
    id: str
    customer_id: str
    lines: tuple[Line, ...]
    status: Status = Status.PENDING
    placed_at: datetime | None = None
    events: list[object] = field(default_factory=list, repr=False, compare=False)

    MAX_LINES = 50

    @classmethod
    def place(cls, order_id: str, customer_id: str, lines: list[Line], now: datetime) -> Order:
        if not lines:
            raise InvalidOrder("order needs at least one line")
        if len(lines) > cls.MAX_LINES:
            raise InvalidOrder(f"at most {cls.MAX_LINES} lines")
        if any(l.qty <= 0 for l in lines):
            raise InvalidOrder("quantities must be positive")
        return cls(order_id, customer_id, tuple(lines), Status.PENDING, now)

    def total(self) -> Money:
        total = Money(0, self.lines[0].unit_price.currency)
        for line in self.lines:
            total = total + line.unit_price.times(line.qty)
        return total

    def mark_paid(self) -> None:
        if self.status is not Status.PENDING:
            raise InvalidOrder(f"cannot pay an order that is {self.status.value}")
        self.status = Status.PAID
        self.events.append(OrderPaid(self.id, self.total()))

    def cancel(self) -> None:
        if self.status is Status.PAID:
            raise InvalidOrder("paid orders are refunded, not cancelled")
        self.status = Status.CANCELLED


@dataclass(frozen=True)
class OrderPaid:
    order_id: str
    amount: Money
```

Notice what is **absent**: no `sqlite3`, no `json`, no request objects, no
`datetime.now()`. Time comes in as a parameter. The order **records** a domain event
instead of publishing it — publishing is I/O, and the domain does not do I/O.

### 4.2 Ports — interfaces owned by the core

```python
# ───────────────────────── application/ports.py ─────────────────────────
# Interfaces the use cases NEED, written in domain vocabulary. Owned by the core.
class OrderRepository(Protocol):
    def get(self, order_id: str) -> Order: ...
    def save(self, order: Order) -> None: ...      # insert or update


class PaymentGateway(Protocol):
    def charge(self, customer_id: str, amount: Money, idempotency_key: str) -> str: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class EventPublisher(Protocol):
    def publish(self, event: object) -> None: ...


class UnitOfWork(Protocol):
    orders: OrderRepository
    def __enter__(self) -> UnitOfWork: ...
    def __exit__(self, *exc) -> None: ...
    def commit(self) -> None: ...
```

The port is named for **what the core needs** (`PaymentGateway.charge`), not for the
vendor (`StripeClient.create_payment_intent`). If the interface mentions Stripe, the
core depends on Stripe no matter which file the interface sits in.

### 4.3 Use case — orchestration, not rules

```python
# ───────────────────────── application/place_order.py ─────────────────────────
# The use case: orchestration only. No SQL, no HTTP, no business rules.
@dataclass(frozen=True)
class PlaceOrderCommand:            # input DTO — plain data, already syntactically valid
    customer_id: str
    items: list[tuple[str, int]]    # (sku, qty)


class PriceCatalog(Protocol):
    def price_of(self, sku: str) -> Money: ...


class PlaceOrder:
    def __init__(self, uow: UnitOfWork, catalog: PriceCatalog, payments: PaymentGateway,
                 publisher: EventPublisher, clock: Clock, new_id=lambda: uuid.uuid4().hex):
        self._uow, self._catalog, self._payments = uow, catalog, payments
        self._publisher, self._clock, self._new_id = publisher, clock, new_id

    def __call__(self, cmd: PlaceOrderCommand) -> str:
        lines = [Line(sku, self._catalog.price_of(sku), qty) for sku, qty in cmd.items]
        order = Order.place(self._new_id(), cmd.customer_id, lines, self._clock.now())

        with self._uow as uow:              # step 1: record intent BEFORE the irreversible call
            uow.orders.save(order)
            uow.commit()

        try:                                # step 2: order id doubles as the idempotency key,
            self._payments.charge(          #         so retrying this use case never double-charges
                order.customer_id, order.total(), idempotency_key=order.id)
        except PaymentDeclined:
            with self._uow as uow:
                order.cancel()
                uow.orders.save(order)
                uow.commit()
            raise

        with self._uow as uow:              # step 3: record the outcome
            order.mark_paid()
            uow.orders.save(order)
            uow.commit()

        for event in order.events:          # publish only AFTER the commit succeeded
            self._publisher.publish(event)
        return order.id
```

**The order of the steps is the most important design decision in this file.** Why not
"charge, then save" in one transaction?

```
 charge card ──✓──▶ save order ──✗ (DB down / process killed)
                    → customer charged, no order exists, nobody knows. Unrecoverable.

 save PENDING ──✓──▶ charge (key = order id) ──✗ (timeout: did it charge?)
                    → a PENDING order exists. A retry or a reconciliation job
                      charges again with the SAME key; the provider dedupes it.
```

Rule: **you cannot put a database and a remote payment <abbr title="Application Programming Interface">API</abbr> in one atomic
transaction.** So record intent first, make the external call idempotent, record the
outcome second, and make sure something (a retry or a sweeper for old `PENDING`
orders) finishes interrupted work. Publishing the event after commit has the same shape
— if publishing must be guaranteed, write the event to an outbox table in the same
transaction instead (`CSFundamentals/04` §2).

### 4.4 Driven adapters — the database

```python
# ───────────────────────── adapters/sqlite_orders.py ─────────────────────────
import json
import sqlite3


class SqliteUnitOfWork:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self.orders = SqliteOrderRepository(conn)
        self._committed = False

    def __enter__(self):
        self._committed = False
        return self

    def commit(self):
        self._conn.commit()
        self._committed = True

    def __exit__(self, *exc):
        if not self._committed:
            self._conn.rollback()


class SqliteOrderRepository:
    """Persistence model (a row) is mapped to/from the domain model HERE and nowhere else."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def save(self, order: Order) -> None:
        lines = [[l.sku, l.unit_price.cents, l.unit_price.currency, l.qty] for l in order.lines]
        self._conn.execute(
            "INSERT OR REPLACE INTO orders (id, customer_id, status, placed_at, lines_json) VALUES (?,?,?,?,?)",
            (order.id, order.customer_id, order.status.value,
             order.placed_at.isoformat(), json.dumps(lines)))

    def get(self, order_id: str) -> Order:
        row = self._conn.execute(
            "SELECT id, customer_id, status, placed_at, lines_json FROM orders WHERE id = ?",
            (order_id,)).fetchone()
        if row is None:
            raise NotFound(order_id)
        lines = tuple(Line(sku, Money(c, cur), q) for sku, c, cur, q in json.loads(row[4]))
        return Order(row[0], row[1], lines, Status(row[2]), datetime.fromisoformat(row[3]))


SCHEMA = """CREATE TABLE orders (
  id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, status TEXT NOT NULL,
  placed_at TEXT NOT NULL, lines_json TEXT NOT NULL)"""
```

Storing lines as <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> is a persistence decision (fine for a demo, and sometimes for
real). The domain does not know or care; changing to a `order_lines` table changes
this file only.

### 4.5 Fakes — real in-memory implementations of the ports

```python
# ───────────────────────── adapters/fakes.py (also used by tests) ─────────────────────────
class InMemoryUnitOfWork:
    def __init__(self):
        self.orders = InMemoryOrderRepository()
        self.committed = False
    def __enter__(self):
        self._snapshot = dict(self.orders._rows)
        self.committed = False
        return self
    def commit(self):
        self.committed = True
    def __exit__(self, *exc):
        if not self.committed:
            self.orders._rows = self._snapshot


class InMemoryOrderRepository:
    def __init__(self):
        self._rows: dict[str, Order] = {}
    def save(self, order):
        self._rows[order.id] = order
    def get(self, order_id):
        try:
            return self._rows[order_id]
        except KeyError:
            raise NotFound(order_id) from None


class FakePayments:
    def __init__(self, decline_over_cents: int | None = None):
        self.charges: dict[str, Money] = {}
        self._limit = decline_over_cents
    def charge(self, customer_id, amount, idempotency_key):
        if idempotency_key in self.charges:              # idempotent: same key, same result
            return f"ch_{idempotency_key}"
        if self._limit is not None and amount.cents > self._limit:
            raise PaymentDeclined(customer_id)
        self.charges[idempotency_key] = amount
        return f"ch_{idempotency_key}"


class DictCatalog:
    def __init__(self, prices: dict[str, int]):
        self._prices = prices
    def price_of(self, sku):
        if sku not in self._prices:
            raise InvalidOrder(f"unknown sku {sku!r}")
        return Money(self._prices[sku])


class FixedClock:
    def __init__(self, at: datetime):
        self.at = at
    def now(self):
        return self.at


class ListPublisher:
    def __init__(self):
        self.published: list[object] = []
    def publish(self, event):
        self.published.append(event)
```

These are **fakes, not mocks** (`05` §4): working implementations with simplified
internals. Tests using them assert on outcomes ("the order is stored as cancelled"),
not on call sequences ("`save` was called twice"), so they survive refactoring. To keep
a fake honest, run the same contract tests against the fake and the real adapter.

### 4.6 Driving adapter — <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>

```python
# ───────────────────────── adapters/http.py (driving adapter) ─────────────────────────
# Framework-shaped: request dict in, (status, body) out. Parses, calls, maps errors.
def post_orders_handler(place_order: PlaceOrder, body: dict) -> tuple[int, dict]:
    try:                                                    # 1. syntactic validation at the edge
        cmd = PlaceOrderCommand(
            customer_id=str(body["customer_id"]),
            items=[(str(i["sku"]), int(i["qty"])) for i in body["items"]])
    except (KeyError, TypeError, ValueError) as e:
        return 400, {"error": f"malformed request: {e}"}
    try:                                                    # 2. call the use case
        order_id = place_order(cmd)
    except InvalidOrder as e:                               # 3. map domain errors → protocol
        return 422, {"error": str(e)}
    except PaymentDeclined:
        return 402, {"error": "payment declined"}
    return 201, {"order_id": order_id}
```

A controller has exactly three jobs: **parse, call, translate.** If a handler contains an
`if` about business state ("if the order is shipped…"), a rule has leaked out of the
domain. In FastAPI/Flask/Django the shape is identical; the framework just supplies
`body` and serialises the return value.

### 4.7 Composition root and tests

```python
# ───────────────────────── main.py (composition root) ─────────────────────────
class SystemClock:
    def now(self):
        return datetime.now()


def build_app(conn: sqlite3.Connection) -> PlaceOrder:
    """The ONLY place that knows which concrete adapter implements each port."""
    return PlaceOrder(
        uow=SqliteUnitOfWork(conn),
        catalog=DictCatalog({"apple": 120, "pear": 90}),
        payments=FakePayments(),            # production: StripeGateway(api_key=...)
        publisher=ListPublisher(),          # production: KafkaPublisher(...)
        clock=SystemClock())


if __name__ == "__main__":
    # --- production-ish wiring against a real SQLite database ---
    conn = sqlite3.connect(":memory:")
    conn.execute(SCHEMA)
    app = build_app(conn)
    status, body = post_orders_handler(app, {"customer_id": "c1",
                                              "items": [{"sku": "apple", "qty": 3}]})
    print(status, body)
    stored = SqliteOrderRepository(conn).get(body["order_id"])
    print(stored.status, stored.total())
    assert status == 201 and stored.status is Status.PAID and stored.total() == Money(360)

    print(post_orders_handler(app, {"customer_id": "c1", "items": [{"sku": "kiwi", "qty": 1}]}))
    print(post_orders_handler(app, {"customer_id": "c1", "items": "oops"}))

    # --- unit test of the use case: no database, no network, no real clock ---
    uow, pay, pub = InMemoryUnitOfWork(), FakePayments(decline_over_cents=500), ListPublisher()
    use_case = PlaceOrder(uow, DictCatalog({"apple": 120}), pay, pub,
                          FixedClock(datetime(2026, 1, 1)), new_id=lambda: "o-1")
    assert use_case(PlaceOrderCommand("c9", [("apple", 2)])) == "o-1"
    assert uow.orders.get("o-1").placed_at == datetime(2026, 1, 1)
    assert pub.published == [OrderPaid("o-1", Money(240))]
    try:
        PlaceOrder(uow, DictCatalog({"apple": 120}), pay, pub, FixedClock(datetime(2026, 1, 1)),
                   new_id=lambda: "o-2")(PlaceOrderCommand("c9", [("apple", 10)]))
    except PaymentDeclined:
        pass
    assert uow.orders.get("o-2").status is Status.CANCELLED   # declined orders are kept, cancelled
    assert "o-2" not in pay.charges
    assert len(pub.published) == 1          # nothing published for the declined order
    print("ALL PASSED")
```

Output:

```
201 {'order_id': '…32 hex chars…'}
Status.PAID Money(cents=360, currency='USD')
(422, {'error': "unknown sku 'kiwi'"})
(400, {'error': "malformed request: string indices must be integers, not 'str'"})
ALL PASSED
```

### 4.8 The dependency graph you just built

```
 main.py ──────────────┬──────────────┬──────────────────┐
                       ▼              ▼                  ▼
               adapters/http   adapters/sqlite    adapters/fakes
                       │              │                  │
                       ▼              ▼                  ▼
               application/place_order ──▶ application/ports
                       │                           │
                       └────────────▶ domain ◀─────┘
```

Every arrow points toward `domain`. `domain` has no outgoing arrows. That is the whole
architecture; everything else is detail.

<div class="lab" data-viz="flow-place-order"></div>

---

## 5 · Where does each concern go?

The most frequent code-review argument in a layered codebase is "this doesn't belong
here". A default placement for each concern:

| Concern | Put it in | Not in | Why |
|---|---|---|---|
| **Syntactic validation** (field present, is an int, valid <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>, string length) | Driving adapter / request schema (Pydantic, protobuf) | Domain | It is about the transport format |
| **Semantic validation / invariants** (qty > 0, ≤ 50 lines, can't cancel shipped) | Domain objects, constructors, value objects | Controllers | Every entry point must obey it |
| **Rules needing other data** (SKU exists, customer credit limit) | Use case fetches data, domain decides | Domain calling a repository | Keeps the domain free of I/O |
| **Authentication** (who are you) | Edge middleware | Use case | Transport-specific (cookie, <abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr>, mTLS) |
| **Authorization** (may *this* user do *this* to *this* order) | Use case (or a policy object it calls) | Only in middleware | Needs the loaded resource; must hold for every entry point |
| **Transactions** | Use case (Unit of Work) | Repository methods, controllers | One business operation = one consistency boundary (§7) |
| **Mapping to/from rows** | Repository adapter | Domain, use case | Only the adapter knows the schema |
| **Mapping errors to <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> codes** | Driving adapter | Domain | `422` is an <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> concept |
| **Retries of remote calls** | Driven adapter (one layer only) | Everywhere | Retries at several layers multiply (3×3×3 = 27 attempts) |
| **Caching** | Decorator adapter around a port (`CachingCatalog(DictCatalog)`) | Inside domain logic | Invalidation is an infrastructure concern |
| **Logging, metrics, tracing** | Middleware + adapters; domain events for business-significant facts | `print` in domain methods | §9 |
| **Current time, IDs, randomness** | Injected (`Clock`, `new_id`) | `datetime.now()` in the domain | Determinism, testability |
| **Feature flags** | Composition root or use case choosing a strategy | `if flags.x:` scattered in domain code | Flags are temporary; keep their blast radius small |
| **Configuration** | Parsed once at startup into typed objects, injected | `os.environ` reads deep in code | `03` §11 |

The **authorization** row deserves emphasis: checking "is logged in" in middleware and
forgetting "owns this order" in the use case is how insecure direct object references
(IDOR) happen. The resource-level check belongs where the resource is loaded.

```python
class CancelOrder:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def __call__(self, actor_id: str, order_id: str) -> None:
        with self._uow as uow:
            order = uow.orders.get(order_id)
            if order.customer_id != actor_id:          # authorization: needs the loaded order
                raise NotFound(order_id)                # don't reveal that the order exists
            order.cancel()                              # business rule: lives on the entity
            uow.orders.save(order)
            uow.commit()
```

---

## 6 · Data shapes across boundaries: DTO, domain model, persistence model

There are three natural shapes for "an order":

| Shape | Lives in | Optimised for | Example |
|---|---|---|---|
| **Request/response DTO** | Driving adapter | Wire format, versioning, public contract | `{"order_id": "...", "total": "3.60"}` |
| **Domain model** | Domain | Enforcing rules, expressing behaviour | `Order` with `Money`, `Status` enum, methods |
| **Persistence model** | Driven adapter | Storage layout, indexes, migrations | a row with `lines_json`, or an <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> class |

The same order as three shapes, in code:

```python
# THE SAME "ORDER" AS THREE SHAPES — minimal illustration of the table above.
from dataclasses import dataclass

@dataclass
class OrderResponseDTO:      # wire shape: whatever the public API promises to keep stable
    order_id: str
    total: str                # "3.60" as a string — JSON numbers would round-trip through float

@dataclass
class Order:                  # domain shape: fields plus behaviour
    id: str
    total_cents: int
    def total_display(self) -> str:
        return f"{self.total_cents / 100:.2f}"

@dataclass
class OrderRow:               # persistence shape: matches the table, includes internal-only columns
    id: str
    total_cents: int
    customer_id: str          # exists in storage; never appears in the DTO

order = Order(id="o-1", total_cents=360)
row = OrderRow(id=order.id, total_cents=order.total_cents, customer_id="c-1")
dto = OrderResponseDTO(order_id=order.id, total=order.total_display())
print(row)
print(dto)
```

Output:

```
OrderRow(id='o-1', total_cents=360, customer_id='c-1')
OrderResponseDTO(order_id='o-1', total='3.60')
```

`customer_id` lives on the row because the database needs it for a foreign key; it has
no reason to exist on the DTO at all, which is the point of keeping the shapes separate.

**Why keep them separate?** Each changes for different reasons:

- Renaming a DB column must not change the public <abbr title="Application Programming Interface">API</abbr> (breaking clients).
- Adding an internal field (`fraud_score`) must not leak it to <abbr title="Application Programming Interface">API</abbr> responses.
- A public <abbr title="Application Programming Interface">API</abbr> must keep `total` as a string for five years; the domain can change freely.

A real incident shape: an endpoint returns `jsonify(user.__dict__)` from the <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> model.
Someone adds `password_hash` to the model. It is now in the <abbr title="Application Programming Interface">API</abbr> response.

**The cost — the mapping tax.** Three shapes means two mappings per boundary to write,
test, and keep in sync. For a <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr> endpoint with no rules, that is pure boilerplate.

| Situation | Recommendation |
|---|---|
| Public/external <abbr title="Application Programming Interface">API</abbr> | **Always** a separate DTO. Your <abbr title="Application Programming Interface">API</abbr> is a contract (`03` §10). |
| Rich domain with real invariants | Separate domain model from persistence model |
| Internal <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr> admin screen | One shape (e.g., an <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> model) is fine |
| Read-only listing/report | Query straight into a DTO; skip the domain model (§10) |

**Active Record vs. Data Mapper** (Fowler) is the same choice at the <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> level:

- **Active Record** (Django <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr>, Rails, Peewee): the object *is* a row and saves itself
  (`order.save()`). Minimal mapping; domain and persistence are fused. Excellent for
  <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr>-heavy apps.
- **Data Mapper** (SQLAlchemy classical/imperative mapping, the repository in §4): domain
  objects know nothing about storage; a separate mapper moves data. More code; the
  domain stays pure.

Neither is "correct". Choose Active Record for simple domains and Data Mapper when rules
are rich enough that you want them tested without a database.

---

## 7 · Transactions belong to the use case

**One use case = one business operation = one transaction boundary** (for local state).

```python
# WRONG: each repository method commits on its own.
class Repo:
    def debit(self, acct, amt):  ...; self.conn.commit()
    def credit(self, acct, amt): ...; self.conn.commit()

def transfer(repo, a, b, amt):
    repo.debit(a, amt)
    repo.credit(b, amt)      # crash here → money vanished
```

```python
# RIGHT: the use case owns the boundary; repositories never commit.
def transfer(uow: UnitOfWork, a: str, b: str, amt: Money) -> None:
    with uow:
        src, dst = uow.accounts.get(a), uow.accounts.get(b)
        src.withdraw(amt)                  # rule: raises if insufficient funds
        dst.deposit(amt)
        uow.commit()                       # both or neither
```

Rules:

1. **Repositories don't commit.** The Unit of Work (or the use case holding a
   connection) does.
2. **Controllers don't open transactions.** A second entry point (queue consumer) would
   have to remember to do the same.
3. **Keep network calls out of open transactions.** A 30-second payment timeout holding
   row locks stalls everyone else. That is why §4.3 commits, calls, then commits again.
4. **One aggregate per transaction is the ideal**; when a use case must change two
   aggregates, either accept one transaction (inside one service, this is often fine)
   or change one and react to its event for the other (eventual consistency).
5. **Side effects after commit.** Emails, events, cache invalidations run after the
   commit succeeds — or go through an outbox if they must not be lost.

---

## 8 · Dependency injection without a framework

**Dependency injection** is just: *objects receive their collaborators instead of
creating them.* It needs no framework.

```python
# NOT INJECTED: hidden dependencies, untestable without monkeypatching.
class PlaceOrder:
    def __init__(self):
        self.repo = PostgresOrderRepo(os.environ["DB_URL"])
        self.payments = StripeGateway(os.environ["STRIPE_KEY"])

# INJECTED (constructor injection): dependencies are visible in the signature.
class PlaceOrder:
    def __init__(self, repo: OrderRepository, payments: PaymentGateway): ...
```

### The composition root

All wiring happens in **one place** near the program's entry point (§4.7 `build_app`).
Consequences:

- Only `main` imports concrete adapters; everything else imports ports.
- A test builds its own graph with fakes; nothing is patched.
- Reading `main` tells you the whole runtime shape of the system.

### Lifetimes

| Lifetime | Examples | How, without a framework |
|---|---|---|
| **Process (singleton)** | Connection pool, <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> client, config, catalog cache | Create once in `main`, pass down |
| **Request / unit of work** | DB transaction, per-request logger with request ID | Create per request in the adapter or a factory passed in |
| **Transient** | Value objects, commands | Just construct them |

A common need: a process-lifetime use case needs a request-lifetime transaction. Inject
a **factory**, not the instance:

```python
class PlaceOrder:
    def __init__(self, uow_factory: Callable[[], UnitOfWork], ...):
        self._uow_factory = uow_factory
    def __call__(self, cmd):
        with self._uow_factory() as uow:    # new transaction per call; safe under concurrency
            ...

# main.py
place_order = PlaceOrder(uow_factory=lambda: SqliteUnitOfWork(pool.connection()), ...)
```

(§4 shares one `SqliteUnitOfWork` for brevity; a real multi-threaded server must use a
factory, because a single connection/transaction is not safe to share across requests.)

### Anti-patterns

| Anti-pattern | What it looks like | Problem |
|---|---|---|
| **Service locator** | `Registry.get(PaymentGateway)` inside methods | Dependencies hidden; fails at runtime, not construction |
| **Injecting the container** | `def __init__(self, container)` | Same as service locator |
| **Constructor with 12 dependencies** | — | Not a DI problem: the class does too much. Split the use case. |
| **Interface for every class** | `IOrderService`, `IPriceCalculator` with one impl, no fake | Speculative abstraction (`01` §14). Interfaces go at ports: where I/O or real variation is. |
| **Module-level globals as DI** | `db = connect()` at import time | Import side effects; can't build two instances; tests share state |

**DI frameworks** (`dependency-injector`, `injector` in Python; `wire`/`fx` in Go; Spring,
Guice, Dagger in Java) help when a graph has hundreds of nodes. Below that, a plain
`build_app()` function is clearer, type-checked, and debuggable. Google's Go and Java
codebases use Wire/Guice/Dagger at scale — you can say that, and still write manual
wiring in an interview.

---

## 9 · Cross-cutting concerns: keep them at the edges

Logging, metrics, tracing, auth, rate limiting, request IDs, and deadlines apply to
*everything*. Sprinkled through business code, they bury the logic. Three mechanisms
keep them out:

**1. Middleware at the driving edge** — wraps every request once.

```python
def with_request_context(handler):
    def wrapped(request):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        token = current_request_id.set(request_id)       # contextvars.ContextVar
        start = time.perf_counter()
        try:
            return handler(request)
        finally:
            metrics.observe("http_latency_s", time.perf_counter() - start, route=request.route)
            current_request_id.reset(token)
    return wrapped
```

**2. Decorators around ports** — add behaviour to a driven adapter without touching it
(GoF Decorator, `04` §10).

```python
class InstrumentedPayments:                 # implements PaymentGateway
    def __init__(self, inner: PaymentGateway, metrics):
        self._inner, self._metrics = inner, metrics

    def charge(self, customer_id, amount, idempotency_key):
        with self._metrics.timer("payments.charge"):
            return self._inner.charge(customer_id, amount, idempotency_key)

# main.py: payments = InstrumentedPayments(RetryingPayments(StripeGateway(key)), metrics)
```

The wrapping order is itself a design decision: metrics *outside* retries measure what
the caller experiences; *inside* measures each attempt.

**3. Domain events** — for facts the business cares about ("order paid"), the domain
records an event and an outer handler logs, emails, or updates analytics. The domain
never imports a logger to say something business-significant.

**Context propagation** (request ID, deadline, trace span, auth principal) travels
implicitly via `contextvars` in Python and **explicitly** as the first
`ctx context.Context` parameter in Go — Go's explicitness is deliberate: you can see
which functions can be cancelled.

---

## 10 · Reads are different: CQRS-lite

Writes need the domain model: invariants, transactions, events. **Reads usually
don't** — a "my orders" page needs a flat list, joined with product names, paginated,
and it breaks no rules.

Loading full aggregates to render a list causes N+1 queries, pointless object
construction, and pressure to add display-only getters to domain objects.

**CQRS-lite:** keep one database, but split the code path.

```
 Commands (writes)                         Queries (reads)
 ─────────────────                         ───────────────
 HTTP ─▶ use case ─▶ domain ─▶ repository  HTTP ─▶ query service ─▶ SQL ─▶ DTO
          (rules, UoW, events)                     (no domain objects, no UoW)
```

```python
@dataclass(frozen=True)
class OrderSummary:                 # read DTO, shaped for the screen
    order_id: str
    status: str
    total_cents: int
    placed_at: str

class OrderQueries:
    def __init__(self, conn):
        self._conn = conn

    def recent_for(self, customer_id: str, limit: int = 20) -> list[OrderSummary]:
        rows = self._conn.execute(
            """SELECT id, status, lines_json, placed_at FROM orders
               WHERE customer_id = ? ORDER BY placed_at DESC LIMIT ?""",
            (customer_id, limit)).fetchall()
        return [OrderSummary(r[0], r[1], sum(c * q for _, c, _, q in json.loads(r[2])), r[3])
                for r in rows]
```

This is not full CQRS (separate read database kept in sync by events, `CSFundamentals/04`
§2). It is the cheap version that removes most of the pain, and it is almost always
worth it.

---

## 11 · How much architecture? Transaction script vs. domain model

Fowler names two ends of a spectrum for organising business logic:

- **Transaction script:** one procedure per request that does everything in order
  (validate, query, compute, update). Simple, direct, no indirection.
- **Domain model:** objects that hold data and the rules for it; use cases orchestrate.

```python
# TRANSACTION SCRIPT — perfectly good for simple logic.
def rename_project(db, user_id, project_id, new_name):
    if not 1 <= len(new_name) <= 100:
        raise ValueError("name length")
    with db.transaction():
        n = db.execute("UPDATE projects SET name=? WHERE id=? AND owner_id=?",
                       (new_name, project_id, user_id)).rowcount
    if n == 0:
        raise NotFound(project_id)
```

Transaction scripts degrade when rules multiply: the same "can this order be
modified?" check gets copied into eight scripts, each slightly different.

| Signal | Lean toward |
|---|---|
| <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr> over forms; rules are "field required" | Transaction script, Active Record, framework defaults |
| Few rules, one entry point, small team | Layered with a service layer; don't add ports yet |
| Rules that span several fields/objects, state machines, money | Domain model with value objects |
| Multiple entry points (<abbr title="Application Programming Interface">API</abbr> + queue + cron) run the same logic | Use cases as the shared driving port |
| Slow tests because everything needs a DB | Ports for driven dependencies |
| Integration with volatile or external systems | Adapter + anti-corruption layer at that boundary |

Architecture can be **uneven on purpose**: the billing module gets a full domain model
and ports; the admin <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr> module next to it uses the <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> directly. Consistency matters
within a module; forcing every module into the heaviest style is a known way to drown a
codebase in pass-through layers.

**Evolve toward it.** Start simple, and introduce a port when a test or a second
implementation needs one. Moving a rule from a script into a domain object, or
extracting a repository interface, are small refactors (`05` §6) — not rewrites.

---

## 12 · The same design in Go

Go idioms change the surface, not the idea:

- **Ports are declared by the consumer** (`order` package), and adapters satisfy them
  implicitly — no `implements` keyword, so the adapter package need not import the core
  for the type relationship (it usually does for the domain types).
- **"Accept interfaces, return structs"** (`02` §5): `NewService(repo Repository)`
  returns `*Service`.
- **`context.Context` is the first parameter** of anything that does I/O.
- **Errors are values:** sentinel errors for categories, `%w` wrapping, `errors.Is` at
  the edge to map to <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> status.

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

// ── internal/order/domain.go ── no imports beyond the standard library.

var (
	ErrInvalidOrder    = errors.New("invalid order")
	ErrNotFound        = errors.New("not found")
	ErrPaymentDeclined = errors.New("payment declined")
)

type Status string

const (
	Pending   Status = "pending"
	Paid      Status = "paid"
	Cancelled Status = "cancelled"
)

type Line struct {
	SKU       string
	UnitCents int64
	Qty       int
}

type Order struct {
	ID, CustomerID string
	Lines          []Line
	Status         Status
	PlacedAt       time.Time
}

func NewOrder(id, customerID string, lines []Line, now time.Time) (*Order, error) {
	if len(lines) == 0 {
		return nil, fmt.Errorf("%w: needs at least one line", ErrInvalidOrder)
	}
	for _, l := range lines {
		if l.Qty <= 0 {
			return nil, fmt.Errorf("%w: sku %s has qty %d", ErrInvalidOrder, l.SKU, l.Qty)
		}
	}
	return &Order{ID: id, CustomerID: customerID, Lines: lines, Status: Pending, PlacedAt: now}, nil
}

func (o *Order) TotalCents() int64 {
	var t int64
	for _, l := range o.Lines {
		t += l.UnitCents * int64(l.Qty)
	}
	return t
}

func (o *Order) MarkPaid() error {
	if o.Status != Pending {
		return fmt.Errorf("%w: cannot pay a %s order", ErrInvalidOrder, o.Status)
	}
	o.Status = Paid
	return nil
}

// ── internal/order/service.go ── ports are declared where they are CONSUMED.

type Repository interface {
	Save(ctx context.Context, o *Order) error
	Get(ctx context.Context, id string) (*Order, error)
}

type Payments interface {
	Charge(ctx context.Context, customerID string, cents int64, idempotencyKey string) error
}

type Service struct {
	repo     Repository
	payments Payments
	now      func() time.Time
	newID    func() string
}

func NewService(repo Repository, payments Payments, now func() time.Time, newID func() string) *Service {
	return &Service{repo: repo, payments: payments, now: now, newID: newID}
}

func (s *Service) PlaceOrder(ctx context.Context, customerID string, lines []Line) (string, error) {
	o, err := NewOrder(s.newID(), customerID, lines, s.now())
	if err != nil {
		return "", err
	}
	if err := s.repo.Save(ctx, o); err != nil {
		return "", fmt.Errorf("save pending order: %w", err)
	}
	if err := s.payments.Charge(ctx, customerID, o.TotalCents(), o.ID); err != nil {
		return "", fmt.Errorf("charge order %s: %w", o.ID, err)
	}
	if err := o.MarkPaid(); err != nil {
		return "", err
	}
	if err := s.repo.Save(ctx, o); err != nil {
		return "", fmt.Errorf("save paid order: %w", err)
	}
	return o.ID, nil
}

// ── internal/order/memrepo.go ── an adapter (and the test fake).

type MemRepo struct {
	mu     sync.Mutex
	orders map[string]Order
}

func NewMemRepo() *MemRepo { return &MemRepo{orders: map[string]Order{}} }

func (r *MemRepo) Save(_ context.Context, o *Order) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.orders[o.ID] = *o // store a copy: callers can't mutate stored state behind our back
	return nil
}

func (r *MemRepo) Get(_ context.Context, id string) (*Order, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	o, ok := r.orders[id]
	if !ok {
		return nil, fmt.Errorf("order %s: %w", id, ErrNotFound)
	}
	return &o, nil
}

type fakePayments struct{ limit int64 }

func (p fakePayments) Charge(_ context.Context, _ string, cents int64, _ string) error {
	if cents > p.limit {
		return ErrPaymentDeclined
	}
	return nil
}

// ── cmd/orders/main.go ── the composition root.

func main() {
	repo := NewMemRepo() // production: postgres.NewOrderRepo(db)
	n := 0
	svc := NewService(repo, fakePayments{limit: 1000}, time.Now,
		func() string { n++; return fmt.Sprintf("o-%d", n) })

	id, err := svc.PlaceOrder(context.Background(), "c1", []Line{{"apple", 120, 3}})
	fmt.Println(id, err)
	stored, _ := repo.Get(context.Background(), id)
	fmt.Println(stored.Status, stored.TotalCents())

	_, err = svc.PlaceOrder(context.Background(), "c1", []Line{{"apple", 120, 0}})
	fmt.Println(errors.Is(err, ErrInvalidOrder), err)

	_, err = svc.PlaceOrder(context.Background(), "c1", []Line{{"tv", 99900, 1}})
	fmt.Println(errors.Is(err, ErrPaymentDeclined), err)
}
```

Output:

```
o-1 <nil>
paid 360
true invalid order: sku apple has qty 0
true charge order o-3: payment declined
```

(Condensed to one file so it runs with `go run`; the cancellation-on-decline step from
§4.3 is left out. In a real repo each `──` section is its own file in the named package.)

The <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> adapter maps errors with `errors.Is`, keeping <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> out of the domain:

```go
func statusFor(err error) int {
	switch {
	case errors.Is(err, order.ErrInvalidOrder):
		return http.StatusUnprocessableEntity
	case errors.Is(err, order.ErrNotFound):
		return http.StatusNotFound
	case errors.Is(err, order.ErrPaymentDeclined):
		return http.StatusPaymentRequired
	default:
		return http.StatusInternalServerError // log it; don't leak err.Error() to clients
	}
}
```

---

## 13 · Package layout and enforcing boundaries

### Package by feature, layers inside (`03` §2)

```
Python                                   Go
──────                                   ──
orders_service/                          orders/
├── main.py            ← composition root├── cmd/orders/main.go        ← composition root
├── ordering/          ← one feature     ├── internal/
│   ├── domain.py                        │   ├── order/                ← one feature
│   ├── ports.py                         │   │   ├── domain.go
│   ├── use_cases.py                     │   │   ├── service.go        (ports declared here)
│   ├── queries.py     ← read side       │   │   └── service_test.go
│   └── adapters/                        │   ├── postgres/             ← driven adapters
│       ├── sqlite_repo.py               │   │   └── order_repo.go
│       └── http.py                      │   ├── httpapi/              ← driving adapter
├── catalog/                             │   │   └── handlers.go
│   └── ...                              │   └── stripe/
└── tests/                               │       └── payments.go
    ├── unit/          ← fakes only      └── go.mod
    └── integration/   ← real SQLite
```

Two styles are common and both are fine: adapters **inside** each feature (above, left),
or adapters grouped by **technology** in their own packages (above, right — idiomatic in
Go, where a `postgres` package holds all <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>). What matters is the import direction.

### Enforce it, or it will erode

A boundary that is only a convention is gone within a year. Make the build check it:

| Tool | What it enforces |
|---|---|
| Go `internal/` directories | The compiler rejects imports of `internal/` from outside the parent tree |
| Go import cycles | The compiler rejects cycles outright |
| `import-linter` (Python) | Contracts like "`ordering.domain` may not import `sqlite3`, `ordering.adapters`" in <abbr title="Continuous Integration. The practice of merging all developers' working copies to a shared mainline several times a day.">CI</abbr> |
| `depguard` (golangci-lint) | Deny lists: `internal/order` may not import `database/sql` |
| Bazel `visibility` (Google) | Per-target allow lists of who may depend on a package |
| ArchUnit (Java), a pytest that walks imports | Arbitrary architecture rules as tests |

```ini
# .importlinter
[importlinter:contract:domain-is-pure]
name = Domain imports nothing from outer layers
type = forbidden
source_modules = ordering.domain
forbidden_modules =
    ordering.adapters
    ordering.use_cases
    sqlite3
    sqlalchemy
    fastapi
```

What a tool like that does under the hood is not magic — it walks the import statements
in each file and checks them against a deny list:

```python
# A MINIMAL VERSION OF WHAT import-linter/depguard DO: walk imports, fail the build on a forbidden one.
import ast

FORBIDDEN_IN_DOMAIN = {"sqlite3", "requests", "flask"}

def imports_of(source: str) -> set[str]:
    tree = ast.parse(source)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names

def check(modules: dict[str, str]) -> list[str]:
    return [f"{name}: imports {sorted(bad)}"
            for name, src in modules.items()
            if (bad := imports_of(src) & FORBIDDEN_IN_DOMAIN)]

modules = {
    "domain/order.py": "from dataclasses import dataclass\nclass Order: ...",
    "domain/pricing.py": "import sqlite3\ndef price():\n    return sqlite3.connect(':memory:')",
}
for violation in check(modules):
    print(violation)
assert check(modules) == ["domain/pricing.py: imports ['sqlite3']"]
print("ALL PASSED")
```

Output:

```
domain/pricing.py: imports ['sqlite3']
ALL PASSED
```

Run this over every file in `domain/` in a <abbr title="Continuous Integration. The practice of merging all developers' working copies to a shared mainline several times a day.">CI</abbr> step and the boundary is enforced by a
machine, not by a reviewer's memory.

---

## 14 · Anti-patterns

| Anti-pattern | Symptom | Fix |
|---|---|---|
| **Fat controller** | Handlers with business `if`s, <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>, and email sending | Parse → call use case → translate; move rules to domain |
| **Anemic domain + god service** | `OrderService` 2,000 lines; `Order` has only fields | Move each rule onto the object that owns the data (`02` §3) |
| **Leaky repository** | Repo returns <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> rows, query builders, or cursors; takes <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> fragments | Return domain objects; name methods for domain queries |
| **Ports named after vendors** | `StripePort`, `S3Interface` in the core | Name by need: `PaymentGateway`, `BlobStore` |
| **Pass-through layers** | Controller → Service → Manager → Repository, each forwarding the same call | Collapse layers that add nothing; not every module needs every layer |
| **Interface for everything** | `IFoo` + `FooImpl` for pure logic with one impl | Interfaces at I/O boundaries and real variation points only |
| **Transactions in repositories** | Each `save()` commits | Unit of Work owned by the use case (§7) |
| **Network call inside a DB transaction** | Lock wait timeouts correlate with a slow dependency | Commit, call, commit (§4.3) |
| **Shared `common`/`core` package** | Every feature imports it; it imports half of them back | Move code to the feature that owns it; share only stable primitives |
| **Domain importing framework** | `from django.db import models` in rule code; Pydantic validators holding business rules | Keep framework types in adapters (fine to relax for simple <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr>, §11) |
| **One model for everything** | <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> class used as <abbr title="Application Programming Interface">API</abbr> response and domain object | Separate DTOs at public boundaries at minimum (§6) |
| **Architecture astronautics** | Hexagonal + CQRS + event sourcing for a to-do app | Match weight to domain complexity (§11) |

---

## 15 · Interview questions and model answers

**Q: What is hexagonal architecture, and why would you use it?**
The core (domain + use cases) defines interfaces — ports — for what it needs from the
outside, and technology-specific adapters implement them; source dependencies point
inward. The main practical benefits are that business logic is testable in milliseconds
without infrastructure, and that new entry points (<abbr title="Application Programming Interface">API</abbr>, queue consumer, <abbr title="Command-Line Interface. A text-based user interface used to view and manage computer files.">CLI</abbr>) reuse the
same use cases. I'd use it when there are real business rules; for <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr> I'd keep a
simple layered or framework-default design.

**Q: Layered vs. clean architecture — what's the actual difference?**
The direction of one dependency. In classic layering the business layer depends on data
access, so persistence types leak into rules and tests need a database. Clean/hexagonal
inverts that one edge: the business layer owns a repository interface and the data layer
implements it.

**Q: Where does validation go?**
Syntactic validation (types, presence, format) at the edge, in request parsing — it's
about the wire format. Business invariants in the domain, in constructors and value
objects, so every entry point obeys them. Checks that need other data are fetched by
the use case and decided by the domain.

**Q: Where does the transaction boundary go?**
In the use case: one business operation, one unit of work. Not in repositories (partial
commits) and not in controllers (every entry point must remember). Keep external calls
out of open transactions, and run side effects after commit or via an outbox.

**Q: How do you charge a card and save an order safely?**
They can't share an atomic transaction. Save the order as pending first, charge with the
order ID as an idempotency key, then record the outcome. Crashes leave a pending order
that a retry or sweeper can complete; the idempotency key prevents double charges.

**Q: Do you use a DI framework?**
Not by default. Constructor injection plus a single composition root in `main` makes
dependencies explicit and type-checked. Frameworks earn their cost with very large
object graphs or scoped lifetimes across many modules. What I avoid is the service
locator pattern, which hides dependencies.

**Q: Isn't mapping between DTOs, domain objects, and rows a waste?**
It's a cost, so pay it where it buys something. Public APIs always get their own DTOs
because they're contracts. Rich domains get separate persistence models so rules are
testable and schema changes stay local. Internal <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr> and read-only queries can use one
shape.

**Q: How do you stop the architecture from eroding?**
Make boundaries machine-checked: Go `internal/` and no import cycles, `import-linter`
or depguard contracts in <abbr title="Continuous Integration. The practice of merging all developers' working copies to a shared mainline several times a day.">CI</abbr>, Bazel visibility. Plus code review against the dependency
rule and keeping `main` as the only place that imports concrete adapters.

**Q: Tell me about an architecture decision you'd make differently.**
(Behavioral framing.) A strong answer names the forces: "We put business rules in
Django models and views because it was fast. When we added a Kafka consumer that needed
the same pricing rules, we duplicated them and they drifted. I extracted a pricing
module with no Django imports behind a use-case function, both entry points called it,
and its tests went from needing a DB to running in 200 ms."

---

## 16 · Checklist

**Dependencies**
- [ ] The domain imports no framework, <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr>, <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>, or I/O library.
- [ ] Every source dependency points toward the domain.
- [ ] Ports are named for the core's needs, not for vendors.
- [ ] Only the composition root imports concrete adapters.
- [ ] Boundaries are enforced by the compiler or a <abbr title="Continuous Integration. The practice of merging all developers' working copies to a shared mainline several times a day.">CI</abbr> check.

**Placement**
- [ ] Controllers only parse, call a use case, and translate results/errors.
- [ ] Invariants live in domain objects; authorization checks live in use cases.
- [ ] Transactions are opened and committed by use cases; repositories never commit.
- [ ] No network calls inside an open DB transaction.
- [ ] Side effects run after commit (or via an outbox).
- [ ] Time, IDs, and randomness are injected.

**Shapes**
- [ ] Public <abbr title="Application Programming Interface">API</abbr> responses use DTOs, never <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> or domain objects directly.
- [ ] Reads that don't enforce rules bypass the domain model.

**Proportion**
- [ ] The weight of the architecture matches the complexity of each module.
- [ ] Every layer adds something; pass-through layers are collapsed.

**Interview**
- [ ] I can draw ports and adapters for a feature and say which way each arrow points.
- [ ] I can explain "save pending → idempotent call → save outcome" and why.
- [ ] I can say when I would *not* use hexagonal architecture.
