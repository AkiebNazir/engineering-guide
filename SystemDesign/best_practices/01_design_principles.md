# Design Principles

These are the principles that decide whether the boxes in a system design actually stay maintainable once real engineers write real code inside them. Each entry follows the same pattern: **rule → why it matters → concrete failure it prevents → short example.** Read this file first; every other file in this module assumes you know SOLID and refers back to it.

## SOLID

### Single Responsibility Principle (SRP)

**Rule:** A module/class should have one reason to change.

**Failure it prevents:** unrelated features get coupled through a shared class, so a change made for reason A silently breaks behavior needed for reason B, and the class becomes a merge-conflict magnet because every team touches it.

```python
# Before: report formatting and persistence share one reason-to-change surface
class Invoice:
    def calculate_total(self): ...
    def print_to_pdf(self): ...       # changes when the print layout changes
    def save_to_database(self): ...   # changes when the schema changes

# After: split by reason to change
class Invoice:
    def calculate_total(self): ...

class InvoicePrinter:
    def print_to_pdf(self, invoice: Invoice): ...

class InvoiceRepository:
    def save(self, invoice: Invoice): ...
```

A PDF-layout tweak now touches only `InvoicePrinter`; the persistence team never reviews it.

### Open/Closed Principle (OCP)

**Rule:** Software entities should be open for extension, closed for modification.

**Failure it prevents:** every new variant requires editing a central `if/elif` block that every other variant also depends on — one bad edit regresses code you never intended to touch, and the blast radius of a new feature grows with the number of existing cases.

```python
# Before: adding a shipping method means editing this function again
def calculate_shipping(order, method):
    if method == "standard":
        return order.weight * 0.5
    elif method == "express":
        return order.weight * 1.5
    # every new carrier edits this function

# After: extend via new classes, don't modify existing ones
class ShippingStrategy(Protocol):
    def cost(self, order) -> float: ...

class StandardShipping:
    def cost(self, order): return order.weight * 0.5

class ExpressShipping:
    def cost(self, order): return order.weight * 1.5

# Adding DroneShipping never touches the two classes above.
```

### Liskov Substitution Principle (LSP)

**Rule:** Subtypes must be substitutable for their base type without altering correctness.

**Failure it prevents:** LSP violations break polymorphic callers *silently* — code that type-checks and passes a quick smoke test throws or misbehaves only when the "wrong" subtype is injected at runtime, often in production, because the caller trusted the base-type contract.

```python
# Before: Square silently violates Rectangle's contract
class Rectangle:
    def set_width(self, w): self.width = w
    def set_height(self, h): self.height = h
    def area(self): return self.width * self.height

class Square(Rectangle):
    def set_width(self, w): self.width = self.height = w   # breaks caller assumptions
    def set_height(self, h): self.width = self.height = h

def resize_to(rect: Rectangle):
    rect.set_width(4)
    rect.set_height(5)
    assert rect.area() == 20   # fails for Square, passes for Rectangle

# After: don't model Square as a Rectangle subtype; share a narrower contract instead
class Shape(Protocol):
    def area(self) -> float: ...
```

Any generic function written against `Rectangle` was implicitly relying on independent width/height mutation — `Square` breaks that invariant without the compiler ever noticing.

### Interface Segregation Principle (ISP)

**Rule:** Clients should not be forced to depend on methods they don't use.

**Failure it prevents:** a fat interface forces every implementer to stub out methods it doesn't support (throwing `NotImplementedError` or silently no-op'ing), which turns a compile-time contract into a runtime landmine and makes the interface lie about what a given implementation can actually do.

```python
# Before: one fat interface
class Worker(Protocol):
    def work(self): ...
    def eat_lunch(self): ...

class RobotWorker(Worker):
    def work(self): ...
    def eat_lunch(self): raise NotImplementedError  # forced, meaningless method

# After: split by what clients actually need
class Workable(Protocol):
    def work(self): ...

class Eatable(Protocol):
    def eat_lunch(self): ...

class RobotWorker(Workable):
    def work(self): ...
```

### Dependency Inversion Principle (DIP)

**Rule:** High-level modules should depend on abstractions, not on low-level concrete modules; abstractions should not depend on details.

**Failure it prevents:** when business logic directly instantiates a concrete infrastructure class (a specific DB driver, a specific HTTP client), unit-testing that logic requires spinning up the real infrastructure — DIP violation is the single most common reason a test suite needs a live database or network call to run at all.

```python
# Before: OrderService is welded to a concrete Postgres class
class PostgresOrderRepository:
    def save(self, order): ...  # real DB connection required

class OrderService:
    def __init__(self):
        self.repo = PostgresOrderRepository()  # concrete dependency, hardcoded

    def place_order(self, order):
        self.repo.save(order)

# After: depend on an abstraction, inject the implementation
class OrderRepository(Protocol):
    def save(self, order): ...

class OrderService:
    def __init__(self, repo: OrderRepository):
        self.repo = repo

    def place_order(self, order):
        self.repo.save(order)

# Test: OrderService(FakeInMemoryRepository()) — no database needed.
```

## Other core principles

| Principle | Rule | Failure it prevents |
|---|---|---|
| DRY (Don't Repeat Yourself) | Every piece of knowledge has one authoritative representation. | Fixing a bug in one copy but not the other N copies — logic drifts and one path silently keeps the bug. |
| **DRY's trap** | Not all *duplicate-looking code* is duplicate *knowledge* — two functions that happen to look alike today for unrelated reasons should stay separate. | Premature abstraction: merging superficially similar code forces an awkward shared abstraction that must grow flags/branches as the two use cases diverge, coupling unrelated features through one "shared" function. |
| KISS (Keep It Simple) | Prefer the simplest design that satisfies the actual requirement. | Cleverness that only the original author can safely modify — bus-factor risk and slower onboarding/debugging. |
| YAGNI (You Aren't Gonna Need It) | Don't build for a requirement you don't have yet. | Speculative generality: config knobs, plugin systems, and abstraction layers that are never used but must still be maintained, tested, and explained. |
| Separation of concerns | Each part of a system addresses one concern (I/O, business rules, presentation) in isolation. | Business-rule bugs that surface only when combined with a specific UI/DB, because the layers were never actually independent. |
| Single level of abstraction (SLA) | A function's body should read at one conceptual level — don't mix high-level orchestration with low-level bit-twiddling in the same function. | Functions that are hard to skim because the reader must context-switch between "what" and "how" line by line, slowing every future read. |
| Law of Demeter | Only talk to immediate collaborators — avoid `a.b().c().d()` chains. | Fragile chains: a refactor deep inside `b()`'s return type breaks every caller that reached through it, even callers with no logical relationship to that internal detail. |
| Composition over inheritance | Assemble behavior from small composed objects rather than deep inheritance trees. | The fragile base class problem — a change to a base class ripples unpredictably into every subclass several levels down, and multiple-inheritance diamonds become unresolvable. |
| Encapsulation / information hiding | Expose behavior, hide internal representation. | Callers reaching into internal state and depending on an implementation detail, which then can never change without breaking external code. |
| Postel's law | Be liberal in what you accept, conservative in what you send. | A strict producer/consumer pairing that breaks on any minor, harmless variation in message shape. **Caveat:** being too liberal on input can silently accept malformed/invalid data and mask a bug at the source — pair it with validation and explicit schema versioning, not silent coercion. |
| Principle of least astonishment | An <abbr title="Application Programming Interface">API</abbr> should behave the way a reasonable caller expects from its name/shape. | Bugs caused by a function doing something technically documented but behaviorally surprising (`save()` that also sends an email) — callers stop reading docs and start guessing, then guess wrong. |
| Fail-fast vs. defensive programming | Fail-fast: reject invalid state immediately, loudly, near the source. Defensive: absorb/tolerate unexpected input and keep going. | Fail-fast prevents a corrupt state from propagating silently until it surfaces far from its cause, which is hard to debug; over-applied, it makes a system brittle to any input variance. Defensive programming trades that off — pick fail-fast for programmer errors and internal invariants, defensive handling for untrusted external input. |
| Immutability by default | Prefer values that can't change after construction; make mutation opt-in and explicit. | Action-at-a-distance bugs: shared mutable state changed by one part of the system in ways another part didn't expect, especially under concurrency (a classic source of races and stale-read bugs). |

## Related

- [02 — Creational patterns](02_design_patterns_creational.md) — Builder and Factory Method are concrete OCP/SRP applications.
- [05 — Architectural patterns](05_architectural_patterns.md) — clean/hexagonal architecture is DIP applied at the system level.
- [07 — Anti-patterns and code smells](07_anti_patterns_and_code_smells.md) — tight coupling via concrete dependencies is the everyday DIP violation.
