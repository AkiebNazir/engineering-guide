# Anti-Patterns and Code Smells

Recognizing these is as important as knowing the patterns in [02](02_design_patterns_creational.md)-[04](04_design_patterns_behavioral.md) — most of them are what you get when a reasonable pattern or principle is applied poorly, ignored, or overused.

## God object

One class that knows about and controls most of the system — order processing, notifications, pricing, and persistence all live in `OrderManager`. Violates SRP ([01](01_design_principles.md)) at the extreme. Every unrelated change touches the same file, every team's PRs collide there, and no one can reason about it locally because "local" no longer exists.

```python
class OrderManager:
    def create_order(self): ...
    def send_email(self): ...
    def calculate_tax(self): ...
    def apply_discount(self): ...
    def save_to_db(self): ...
    def generate_invoice_pdf(self): ...
    # 40 more methods, each a different reason to change
```

## Spaghetti code

Control flow with no discernible structure — deep nesting, gotos or their equivalent (deeply nested conditionals, early returns scattered without pattern), logic and side effects interleaved so tightly that tracing "what happens when X" requires reading the entire function line by line rather than following names.

## Anemic domain model

Data classes with no behavior, paired with separate "service" classes that contain all the logic operating on that data.

```python
# Anemic: Order is a bag of fields
class Order:
    def __init__(self):
        self.items = []
        self.status = "pending"

class OrderService:
    def add_item(self, order, item): order.items.append(item)
    def can_ship(self, order): return order.status == "paid" and order.items
    def mark_shipped(self, order): order.status = "shipped"
```

```python
# Rich: Order owns its own invariants
class Order:
    def __init__(self):
        self.items = []
        self.status = "pending"

    def add_item(self, item):
        if self.status != "pending":
            raise InvalidState("cannot modify a non-pending order")
        self.items.append(item)

    def mark_shipped(self):
        if self.status != "paid" or not self.items:
            raise InvalidState("order is not ready to ship")
        self.status = "shipped"
```

The anemic version lets *any* service call `order.status = "shipped"` directly, bypassing the invariant — the rule "can't ship an empty or unpaid order" only holds if every caller remembers to check it. The rich version makes the invariant impossible to bypass because `Order` itself enforces it.

## Premature optimization

Spending effort optimizing a code path before profiling shows it matters — usually trading away readability or flexibility for a performance gain that's never measured and often doesn't exist on the real hot path. The fix is always: measure first, optimize the path the profiler actually points to.

## Magic numbers / strings

Unexplained literal values embedded in logic (`if status == 3`, `discount = price * 0.15`). The reader has no way to know what `3` means without hunting for where it's set elsewhere, and a second occurrence of the same literal can silently drift out of sync with the first.

```python
if status == 3:          # what is 3?
    ...
# vs.
if status == OrderStatus.SHIPPED:
    ...
```

## Shotgun surgery

One conceptual change requires touching many unrelated files/classes because responsibility for that concept is scattered instead of centralized — the opposite failure mode from a God object, but caused by the same missing question: "who owns this concern?" Adding a new payment method that requires edits in twelve unrelated files is shotgun surgery; it's usually the sign of a missing abstraction (Strategy or Factory Method, see [02](02_design_patterns_creational.md)/[04](04_design_patterns_behavioral.md)) or a violated OCP ([01](01_design_principles.md)).

## Feature envy

A method that spends most of its logic reaching into another object's data/methods rather than its own — a sign the method is defined on the wrong class.

```python
class Invoice:
    def total_with_tax(self, customer):
        return self.subtotal * (1 + customer.region.tax_rate)  # envies Customer/Region
```

This method cares more about `customer.region.tax_rate` than about anything belonging to `Invoice` — it's a candidate to move onto `Customer`/`Region`, or to have the tax rate passed in directly.

## Big ball of mud

A system with no recognizable architecture at all — layers, modules, and responsibilities that were never enforced, so dependencies point in every direction and there is no boundary left to reason about. Usually the end state of accumulated shotgun surgery and unmanaged technical debt (see [06](06_code_quality_and_practices.md)) rather than a single bad decision.

## Cargo-cult design-pattern overuse

Using a named pattern because it looks "properly engineered," not because it solves a problem actually present in this code. This is the single most important smell to watch for after learning files [02](02_design_patterns_creational.md)-[04](04_design_patterns_behavioral.md): a `Singleton` for something that's never actually singular, a `Strategy` interface with exactly one implementation and no second one on the horizon, an `AbstractFactory` for a system with one product family. The tell is indirection with no corresponding flexibility payoff — extra interfaces, extra classes, an extra hop through an abstraction, none of which is ever exercised by more than one concrete case. Every "when it's overkill" note in files 02-04 exists specifically to guard against this.

## Tight coupling via concrete-class dependencies

A module that instantiates or references concrete infrastructure classes directly, instead of depending on an interface/abstraction — the everyday form of a DIP violation ([01](01_design_principles.md)).

```python
class ReportGenerator:
    def __init__(self):
        self.db = PostgresConnection()   # concrete, hardcoded — can't swap or fake
```

The failure mode is identical to the DIP section in [01](01_design_principles.md): testing `ReportGenerator` now requires a real Postgres instance, and swapping databases means editing `ReportGenerator` itself rather than injecting a different implementation of an interface it already depends on.

## Related

- [01 — Design principles](01_design_principles.md) — most smells here are a named principle's violation given a name of its own.
- [06 — Code quality and practices](06_code_quality_and_practices.md) — technical debt framing, refactoring discipline as the remedy.
- [02](02_design_patterns_creational.md) / [03](03_design_patterns_structural.md) / [04](04_design_patterns_behavioral.md) — the patterns cargo-cult overuse misapplies.
