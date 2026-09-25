# Object-Oriented Design and Domain Modeling

> "The purpose of abstraction is not to be vague, but to create a new semantic level in
> which one can be absolutely precise." — Edsger Dijkstra

`01_philosophy_of_software_design.md` is about **complexity** in general. This file is
about the most common tool people use to manage it: **objects and types that model a
domain.** It is the foundation for every low-level design (LLD / object-oriented design)
interview — "design a parking lot", "design an elevator", "design Splitwise" — and for
most real-world code review arguments about classes.

The goal is not to memorise the four pillars. It is to be able to look at a problem
statement and produce a model where **the invariants live in one place, the objects that
change together sit together, and new requirements land as additions rather than edits.**

Examples are in **Python** (the interview language) with **Go** where its idioms differ.

**Already covered elsewhere — not repeated here:**

| Topic | Where |
|---|---|
| GoF pattern catalog and idiomatic use | `04_design_patterns_in_practice.md` §1 (all 23 at a glance), §3–§18 |
| DRY, KISS, YAGNI, and the other named principles | `01_philosophy_of_software_design.md` §17 (index of where each is treated) |
| Deep modules, information hiding, illegal states | `01_philosophy_of_software_design.md` §3, §4, §8 |
| Bounded contexts and aggregates at service scale | `CSFundamentals/04_software_engineering_deep_dive.md` §1 |
| Python MRO, descriptors, metaclasses | `PyEngineering/31_advanced_oop_and_mro`, `26_metaprogramming_descriptors_decorators` |
| Go interfaces and embedding in depth | `GoEngineering/33_advanced_interfaces_and_composition` |

---

## Contents

1. [What an object is for](#1--what-an-object-is-for)
2. [The four pillars, honestly](#2--the-four-pillars-honestly)
3. [Invariants: the real job of a class](#3--invariants-the-real-job-of-a-class)
4. [Composition over inheritance](#4--composition-over-inheritance)
5. [Interfaces: nominal, structural, and Go's implicit ones](#5--interfaces-nominal-structural-and-gos-implicit-ones)
6. [Relationships between objects](#6--relationships-between-objects)
7. [Entities, value objects, and identity](#7--entities-value-objects-and-identity)
8. [Aggregates and consistency boundaries in code](#8--aggregates-and-consistency-boundaries-in-code)
9. [Tell, don't ask — and the Law of Demeter](#9--tell-dont-ask--and-the-law-of-demeter)
10. [Modeling state and lifecycles](#10--modeling-state-and-lifecycles)
11. [From problem statement to model: noun/verb analysis done right](#11--from-problem-statement-to-model-nounverb-analysis-done-right)
12. [SOLID as questions, not commandments](#12--solid-as-questions-not-commandments)
13. [UML you actually need](#13--uml-you-actually-need)
14. [OOP vs. functional vs. data-oriented](#14--oop-vs-functional-vs-data-oriented)
15. [Red flags](#15--red-flags)
16. [Interview questions and model answers](#16--interview-questions-and-model-answers)
17. [Checklist](#17--checklist)

---

## 1 · What an object is for

An object bundles **data** with **the only code allowed to change that data in ways that
matter.** That is the whole idea. Everything else — inheritance, patterns, UML — is
secondary.

```
    A STRUCT                                AN OBJECT

 ┌────────────────────┐              ┌─────────────────────────────────┐
 │ balance: int       │  anyone can  │ deposit(amount)                 │ ◀─ the only doors
 │ overdraft: int     │  write any   │ withdraw(amount)                │
 │ frozen: bool       │  field, any  ├─────────────────────────────────┤
 └────────────────────┘  time        │ _balance, _overdraft, _frozen   │ ◀─ rule: balance
          ▲                          │                                 │    never below
   rules live in every caller        └─────────────────────────────────┘    -overdraft
                                          rules live here, once
```

Ask of every class: **what rule does this protect?** If the answer is "nothing, it just
holds fields", it should be a plain record (`@dataclass(frozen=True)`, a Go struct) and
not pretend to be an object. Both are fine — the mistake is mixing them up:

- A class with getters and setters for every field and no rules is a struct wearing a
  costume (§3, "anemic model").
- A struct that twelve functions across the codebase mutate, each re-checking the same
  rule, is an object that was never written.

### The idea in 30 seconds

```python
# STRUCT: nothing stops an invalid value from being written in from outside.
class CounterStruct:
    def __init__(self):
        self.count = 0

c = CounterStruct()
c.count = -5                      # meaningless, but nothing prevents it

# OBJECT: the invariant ("count never negative") lives in one place, guarded.
class Counter:
    def __init__(self):
        self._count = 0

    def increment(self) -> None:
        self._count += 1

    def decrement(self) -> None:
        if self._count == 0:
            raise ValueError("count cannot go negative")
        self._count -= 1

    @property
    def count(self) -> int:
        return self._count
```

Every deeper example in this file (`Account`, `Order`, `Money`...) is this same idea
applied to a real domain: find the rule, put it behind a method, remove every other way
in.

---

## 2 · The four pillars, honestly

Interviewers still ask for them. Give the textbook definition in one line, then show you
know what each is actually *for* and where it goes wrong.

| Pillar | One-line definition | What it's really for | How it goes wrong |
|---|---|---|---|
| **Encapsulation** | Hide state behind methods. | Keep an invariant in one place so it cannot be broken from outside. | Getters/setters for every field: the state is hidden syntactically but not semantically. |
| **Abstraction** | Expose *what*, hide *how*. | Let callers reason at a higher level; let the implementation change. | Leaky abstractions (callers must know the "how" anyway), or abstractions with one implementation "for the future". |
| **Inheritance** | A subclass reuses and specialises a parent. | Model a genuine *is-substitutable-for* relationship; share a template of behaviour. | Used for code reuse alone → fragile base class, deep hierarchies, LSP violations. |
| **Polymorphism** | One interface, many implementations. | Replace conditionals on type with dispatch, so new variants are additions. | Polymorphism over things that never vary; or `isinstance` checks that defeat it. |

### Polymorphism in 30 seconds

```python
class Dog:
    def speak(self) -> str:
        return "Woof"

class Cat:
    def speak(self) -> str:
        return "Meow"

for animal in [Dog(), Cat()]:
    print(animal.speak())          # same call, different behavior per type — no if/elif
```

That's the whole idea. The rest of this section is the vocabulary for three different
*mechanisms* that give you this.

### Three kinds of polymorphism

Knowing these separates a textbook answer from a strong one.

```python
from typing import Protocol, TypeVar, Generic
from functools import singledispatch

# 1. SUBTYPE polymorphism — dispatch on the runtime type of the receiver.
class Shape(Protocol):
    def area(self) -> float: ...

class Circle:
    def __init__(self, r: float): self.r = r
    def area(self) -> float: return 3.14159 * self.r ** 2

class Square:
    def __init__(self, s: float): self.s = s
    def area(self) -> float: return self.s ** 2

def total_area(shapes: list[Shape]) -> float:
    return sum(s.area() for s in shapes)          # no isinstance anywhere

# 2. PARAMETRIC polymorphism (generics) — same code for every T.
T = TypeVar("T")

class Stack(Generic[T]):
    def __init__(self) -> None: self._items: list[T] = []
    def push(self, x: T) -> None: self._items.append(x)
    def pop(self) -> T: return self._items.pop()

# 3. AD HOC polymorphism (overloading) — different code per argument type.
@singledispatch
def render(value) -> str: return str(value)

@render.register
def _(value: float) -> str: return f"{value:.2f}"
```

```go
// Go: subtype polymorphism via interfaces (implicit), parametric via generics (1.18+).
type Shape interface{ Area() float64 }

func TotalArea(shapes []Shape) float64 {
	var sum float64
	for _, s := range shapes {
		sum += s.Area()
	}
	return sum
}

func Map[T, U any](xs []T, f func(T) U) []U {
	out := make([]U, 0, len(xs))
	for _, x := range xs {
		out = append(out, f(x))
	}
	return out
}
// Go has no overloading and no inheritance. That is a design choice, not a gap.
```

### Dynamic dispatch replaces conditionals — but only where things vary

```python
# CONDITIONAL ON TYPE: every new payment method edits every function like this one.
def fee(payment):
    if payment.kind == "card":   return payment.amount * 0.029 + 0.30
    if payment.kind == "upi":    return 0
    if payment.kind == "wallet": return payment.amount * 0.01
    raise ValueError(payment.kind)
```

If `kind` is switched on in **one** place, a `match` or dict is simpler than a class
hierarchy. If it is switched on in **five** places (fee, refund rules, settlement delay,
receipt text, fraud checks), that is five edits per new method — the hierarchy wins:

```python
class PaymentMethod(Protocol):
    def fee(self, amount: int) -> int: ...
    def settlement_days(self) -> int: ...
    def refundable(self) -> bool: ...
```

> **Heuristic:** one switch → keep the switch. The same switch repeated → polymorphism.
> This is the "replace conditional with polymorphism" refactoring, applied with judgment.

---

## 3 · Invariants: the real job of a class

An **invariant** is a statement that must be true about an object whenever a caller can
observe it. Designing a class *is* choosing its invariants and making them impossible
to break.

```python
from dataclasses import dataclass, field

class InsufficientFunds(Exception): ...
class AccountFrozen(Exception): ...

class Account:
    """Invariant: balance >= -overdraft_limit, and a frozen account never changes."""

    def __init__(self, account_id: str, overdraft_limit: int = 0) -> None:
        if overdraft_limit < 0:
            raise ValueError("overdraft_limit must be >= 0")
        self._id = account_id
        self._balance = 0                      # integer minor units, never float
        self._overdraft_limit = overdraft_limit
        self._frozen = False

    @property
    def balance(self) -> int:                  # read-only view; no setter exists
        return self._balance

    def deposit(self, amount: int) -> None:
        self._require_active()
        if amount <= 0:
            raise ValueError("deposit must be positive")
        self._balance += amount

    def withdraw(self, amount: int) -> None:
        self._require_active()
        if amount <= 0:
            raise ValueError("withdrawal must be positive")
        if self._balance - amount < -self._overdraft_limit:
            raise InsufficientFunds(self._id)
        self._balance -= amount

    def freeze(self) -> None:
        self._frozen = True

    def _require_active(self) -> None:
        if self._frozen:
            raise AccountFrozen(self._id)
```

Notice what is **absent**: `set_balance()`. A setter would let any caller break the
invariant, and then every reader of `balance` would have to wonder whether it holds.

### Three rules for protecting invariants

1. **Establish in the constructor.** An object that exists is valid. No "call `init()`
   after construction", no half-built objects. If construction can fail, raise (Python)
   or return `(T, error)` from a `NewX` function (Go).
2. **Preserve in every public method.** Check preconditions *before* mutating, so a
   failed call leaves the object unchanged (this is the "strong exception guarantee").
3. **Never leak mutable internals.** Returning `self._items` hands the caller a way to
   bypass every method.

```python
class Order:
    def __init__(self) -> None:
        self._lines: list[tuple[str, int]] = []

    def lines_leaky(self) -> list[tuple[str, int]]:
        return self._lines                     # caller can .append() past your checks

    def lines(self) -> tuple[tuple[str, int], ...]:
        return tuple(self._lines)              # snapshot; the invariant stays yours
```

```go
// Go: unexported fields are the encapsulation boundary — and it is per PACKAGE, not per type.
package account

type Account struct {
	id        string
	balance   int64
	overdraft int64
}

func New(id string, overdraft int64) (*Account, error) {
	if overdraft < 0 {
		return nil, errors.New("overdraft must be >= 0")
	}
	return &Account{id: id, overdraft: overdraft}, nil
}

func (a *Account) Balance() int64 { return a.balance }

// Returning a slice field directly aliases the backing array — same leak as Python.
// Return slices.Clone(x) (Go 1.21+) when the caller must not mutate your state.
```

### The anemic domain model

```python
# ANEMIC: the "object" is a bag of fields; the rules live in a service.
@dataclass
class Order:
    status: str
    items: list
    total: int

class OrderService:
    def add_item(self, order, item):
        if order.status != "draft":          # rule #1, repeated in cancel(), pay()...
            raise ValueError("locked")
        order.items.append(item)
        order.total += item.price            # rule #2: total must match items
```

Nothing stops some other code from doing `order.items.append(x)` and forgetting the
total. Moving `add_item` onto `Order` puts the invariant where the data is. (Services are
still right for logic that spans several aggregates or talks to infrastructure — see §8.)

---

## 4 · Composition over inheritance

"Favor object composition over class inheritance" is from the Gang of Four book itself,
page 20. The reasons are concrete.

### The idea in 30 seconds

```python
class Engine:
    def start(self) -> str:
        return "vroom"

# WRONG: a Car "is an" Engine? No — this reuses code, but the relationship is false.
class CarWrong(Engine):
    pass

# RIGHT: a Car "has an" Engine. Swapping engines later means passing a different one in.
class Car:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def start(self) -> str:
        return self._engine.start()

car = Car(Engine())
car.start()                        # "vroom" — Car delegates, it doesn't inherit
```

The rest of this section is about *why* that matters once the code gets bigger than this.

### Why inheritance is the strongest coupling there is

A subclass depends on its parent's **implementation**, not just its interface: which
methods call which other methods, in what order. The parent cannot change those
internals without risking every subclass. This is the **fragile base class problem.**

```python
class CountingSet(set):
    """Counts how many elements were ever added."""
    def __init__(self, *a):
        super().__init__(*a)
        self.added = 0

    def add(self, x):
        self.added += 1
        super().add(x)

    def update(self, *iterables):
        for it in iterables:
            self.added += len(list(it))       # BUG if the iterable is a generator:
        super().update(*iterables)            # list() consumed it, update() sees nothing
```

The deeper, classic version of this bug (from Java's `HashSet.addAll` calling `add`) is
that you **cannot know** whether the parent's `update` calls your overridden `add` —
which would double count — without reading the parent's source. And the answer can
change between library versions. Composition removes the question:

```python
class CountingSet:
    def __init__(self) -> None:
        self._set: set = set()
        self.added = 0

    def add(self, x) -> None:
        self.added += 1
        self._set.add(x)

    def update(self, iterable) -> None:
        for x in iterable:                    # we control exactly what happens
            self.add(x)

    def __contains__(self, x) -> bool: return x in self._set
    def __len__(self) -> int: return len(self._set)
```

It costs a few forwarding methods. It buys independence from someone else's internals.

### The combinatorial explosion

```
Inheritance for orthogonal features:            Composition:

            Notifier                            Notifier(channel, formatter, retry)
     ┌──────────┼──────────┐
  Email        SMS        Push                  channel   ∈ {Email, SMS, Push}
  ├─ HtmlEmail ├─ Retrying ├─ RetryingPush      formatter ∈ {Plain, Html, Markdown}
  ├─ Retrying  │  SMS      ├─ HtmlPush?         retry     ∈ {None, Exponential}
  │  HtmlEmail ...         ...
  3 × 3 × 2 = 18 classes, and adding one         3 + 3 + 2 = 8 small classes,
  formatter adds 6 more.                          adding one formatter adds 1.
```

Whenever two dimensions vary independently, inheritance multiplies and composition adds.
(This is the Bridge and Decorator patterns' entire reason to exist.)

### When inheritance IS right

- **A true subtype relationship that passes the Liskov test** (§12): every place that
  accepts the parent would be correct with the child, *including* its documented
  behaviour, errors and performance expectations.
- **Framework extension points designed for it:** `unittest.TestCase`,
  `Exception` hierarchies, `abc.ABC` template methods where the parent documents exactly
  which hooks subclasses override.
- **Shallow and stable:** one level, parent owned by the same team.

**Exception hierarchies are the best everyday use of inheritance** — callers catch at
the level of generality they care about:

```python
class PaymentError(Exception): ...
class CardDeclined(PaymentError): ...
class ProviderUnavailable(PaymentError): ...   # retryable
```

### Mixins: the Python middle ground

A mixin adds one narrow capability and is never instantiated alone. Use sparingly; each
mixin is still inheritance, and several together make MRO questions real.

```python
import json

class JsonMixin:
    def to_json(self) -> str:
        return json.dumps(self.__dict__, default=str)

class User(JsonMixin):
    def __init__(self, name: str): self.name = name
```

### Go: embedding is not inheritance

```go
type Logger struct{ prefix string }

func (l *Logger) Log(msg string) { fmt.Println(l.prefix + msg) }

type Server struct {
	*Logger          // embedded: Server gets a promoted Log method
	addr    string
}

// s.Log("x") is sugar for s.Logger.Log("x"). The receiver is still the *Logger.
// There is NO virtual dispatch back into Server: if Logger's methods call l.Other(),
// they call Logger's Other, never a Server "override". So the fragile-base-class
// problem (parent calling an overridden hook) cannot happen.
```

---

## 5 · Interfaces: nominal, structural, and Go's implicit ones

An interface is a **contract**: the set of operations a caller may rely on, plus their
meaning. The syntax matters less than who defines it and how big it is.

| | Declared by | Implementation must name it? | Python | Go |
|---|---|---|---|---|
| **Nominal** | Provider | Yes (`class X(Base)`) | `abc.ABC` | — |
| **Structural** | Anyone | No — matching shape suffices | `typing.Protocol` (checked by mypy/pyright) | every `interface` |
| **Duck typing** | Nobody | No, and nothing is checked until runtime | plain Python | — |

```python
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

class Storage(ABC):                          # nominal: must inherit, instantiation fails
    @abstractmethod                           # if an abstract method is missing
    def get(self, key: str) -> bytes | None: ...

@runtime_checkable
class Clock(Protocol):                        # structural: anything with now() fits
    def now(self) -> float: ...

class FakeClock:                              # never mentions Clock
    def __init__(self, t: float = 0.0): self.t = t
    def now(self) -> float: return self.t

assert isinstance(FakeClock(), Clock)         # runtime_checkable checks names only, not signatures
```

**Use `ABC`** when you own a family of implementations and want instantiation to fail
fast if a method is missing. **Use `Protocol`** at boundaries — the consumer describes
the little it needs, and third-party or test types fit without inheriting anything.

### "Accept interfaces, return structs" — and define interfaces where they are used

This Go proverb is the most useful interface rule in any language:

```go
// package report — the CONSUMER defines the tiny interface it needs.
type userLister interface {
	ListActive(ctx context.Context) ([]User, error)
}

func Build(ctx context.Context, users userLister) (Report, error) { ... }

// package postgres — the PROVIDER returns a concrete type with many methods.
// It never imports package report, and never declares "implements".
func NewUserStore(db *sql.DB) *UserStore { ... }
```

Why this is better than a provider-side `UserRepository` interface with 15 methods:

- The consumer depends on exactly one method — **Interface Segregation for free.**
- A test fake is a three-line struct.
- The provider can add methods without breaking anyone.
- There is no "interface with one implementation, created in case" — the interface
  exists because a consumer needed an abstraction.

### Interface size

```
io.Reader            1 method   — implemented by hundreds of types
sort.Interface       3 methods  — Len, Less, Swap
http.Handler         1 method   — the whole web ecosystem plugs in here
database/sql/driver  many small interfaces, optional capabilities discovered by type assertion
```

> **"The bigger the interface, the weaker the abstraction."** — Rob Pike.
> Design interfaces by what the *caller* needs, not by what the *implementation* can do.

### Interfaces carry semantics, not just signatures

`def withdraw(amount: int) -> None` says nothing about whether it may go negative, what
it raises, whether it is idempotent, or whether it is thread-safe. Those are part of the
contract. Write them in the docstring; test them in a **contract test** that runs
against every implementation (see `05_testability_refactoring_and_legacy_code.md` §4).

---

## 6 · Relationships between objects

The vocabulary appears in every LLD interview and every UML diagram.

| Relationship | Meaning | Lifetime | Example | UML |
|---|---|---|---|---|
| **Dependency** | A *uses* B temporarily (parameter, local). | Independent | `ReportBuilder.build(clock)` | `A ┄┄▷ B` (dashed arrow) |
| **Association** | A *knows* B (field reference). | Independent | `Driver` — `Car` | `A ──── B` |
| **Aggregation** | A *has* B, but B can exist without A. | Independent | `Team` has `Player`s | `A ◇──── B` (hollow diamond) |
| **Composition** | A *owns* B; B dies with A. | B bound to A | `Order` owns `OrderLine`s | `A ◆──── B` (filled diamond) |
| **Inheritance** | A *is a* B. | — | `SavingsAccount` is an `Account` | `A ──▷ B` (hollow triangle) |
| **Realization** | A *implements* interface B. | — | `S3Store` implements `Storage` | `A ┄┄▷ B` (dashed, hollow triangle) |

### Why the aggregation/composition distinction matters in code

It decides **who creates, who deletes, and who may hold a reference**:

```python
class Order:                                   # COMPOSITION: Order creates and owns lines.
    def __init__(self) -> None:
        self._lines: list["OrderLine"] = []

    def add_line(self, sku: str, qty: int, unit_price: int) -> None:
        self._lines.append(OrderLine(sku, qty, unit_price))   # nobody else constructs one

class Team:                                    # AGGREGATION: players exist independently.
    def __init__(self) -> None:
        self._player_ids: set[str] = set()     # hold IDs, not objects, across aggregates

    def sign(self, player_id: str) -> None:
        self._player_ids.add(player_id)
```

### Cardinality and navigability

Always state both in an LLD answer: *"A `ParkingFloor` has many `ParkingSpot`s (1..\*),
navigable from floor to spot. A spot holds at most one `Ticket` (0..1) and we look
tickets up by ID rather than storing back-references."* Bidirectional references double
the invariants you must maintain (both sides must agree) — add them only when a query
really needs them.

---

## 7 · Entities, value objects, and identity

| | Entity | Value object |
|---|---|---|
| Identity | Has an ID that persists across changes | None — defined by its attributes |
| Equality | Same ID ⇒ same thing | All fields equal ⇒ interchangeable |
| Mutability | Usually mutable (through methods) | **Immutable** |
| Examples | `User`, `Order`, `ParkingTicket`, `Elevator` | `Money`, `Email`, `DateRange`, `Coordinates`, `Seat("A", 12)` |

### Value objects are the highest-leverage modeling tool

They kill primitive obsession, centralise validation, and are safe to share because they
cannot change.

```python
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True, slots=True)
class Money:
    amount_minor: int                  # cents/paise: never float for money
    currency: str

    def __post_init__(self) -> None:
        if len(self.currency) != 3 or not self.currency.isupper():
            raise ValueError(f"bad currency {self.currency!r}")

    def __add__(self, other: "Money") -> "Money":
        self._same_currency(other)
        return Money(self.amount_minor + other.amount_minor, self.currency)

    def allocate(self, parts: int) -> list["Money"]:
        """Split without losing a cent: 100 / 3 -> [34, 33, 33]."""
        base, remainder = divmod(self.amount_minor, parts)
        return [Money(base + (1 if i < remainder else 0), self.currency) for i in range(parts)]

    def _same_currency(self, other: "Money") -> None:
        if other.currency != self.currency:
            raise ValueError("currency mismatch")

@dataclass(frozen=True, slots=True)
class DateRange:
    start: int
    end: int                           # half-open [start, end)

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError("empty or inverted range")

    def overlaps(self, other: "DateRange") -> bool:
        return self.start < other.end and other.start < self.end
```

`0.1 + 0.2 != 0.3` in binary floating point, so money in `float` is a classic interview
red flag. `Money.allocate` is the kind of detail (Splitwise, bill splitting) that
interviewers probe. `DateRange.overlaps` with half-open intervals is the core of every
booking system.

### Equality and hashing must agree

```python
@dataclass(eq=False)          # entity: identity equality
class User:
    user_id: str
    name: str

    def __eq__(self, other: object) -> bool:
        return isinstance(other, User) and other.user_id == self.user_id

    def __hash__(self) -> int:
        return hash(self.user_id)   # hash ONLY immutable identity, or dict lookups break
```

If `__hash__` used `name` and the name changed while the user was a dict key, the entry
would become unreachable. Rule: **hash only what never changes.**

---

## 8 · Aggregates and consistency boundaries in code

An **aggregate** is a cluster of objects that must be consistent together, reached only
through its **root**. The service-level view is in `CSFundamentals/04` §1; here is what it
means for classes.

```
          ┌───────────── Order aggregate ─────────────┐
 outside  │                                           │
 code ───▶│  Order (root)                             │
          │   ├── OrderLine ◆ (only via Order)        │
          │   ├── ShippingAddress (value object)      │
          │   └── invariant: total == Σ lines,        │
          │                  ≤ 50 lines, not shipped  │
          └──────────────────┬────────────────────────┘
                             │ customer_id (ID reference, NOT an object reference)
                             ▼
                      Customer aggregate
```

Rules that fall out of this:

1. **External code holds references only to the root.** Nobody outside `Order` gets an
   `OrderLine` they can mutate.
2. **Reference other aggregates by ID.** Holding a `Customer` object inside `Order`
   invites code that mutates both in one method, which then needs one transaction/lock
   across both.
3. **One aggregate per transaction (or per lock).** Cross-aggregate rules ("customer's
   total open orders ≤ 10") are either checked by a service with a coarser lock, or
   accepted as eventually consistent.
4. **Keep aggregates small.** A `Library` aggregate that contains every `Book` means
   every borrow locks the library.

### Rule 2 in code: reference by ID, not by object

```python
class OrderLine:
    def __init__(self, sku: str, qty: int) -> None:
        self.sku = sku
        self.qty = qty

class Order:                                  # the aggregate root
    def __init__(self, order_id: str, customer_id: str) -> None:
        self.order_id = order_id
        self.customer_id = customer_id        # a plain ID, not a Customer object
        self._lines: list[OrderLine] = []

    def add_line(self, sku: str, qty: int) -> None:
        self._lines.append(OrderLine(sku, qty))

order = Order("O-1", customer_id="C-42")
order.add_line("SKU-1", 2)
# To act on the customer: customer_repository.get(order.customer_id) — a separate
# load, in a separate transaction if needed. Order never holds a Customer object, so
# touching one aggregate can never accidentally pull the other one into the same lock.
```

### Domain service vs. application service

| | Domain service | Application service |
|---|---|---|
| Contains | Domain logic that doesn't belong to one entity | Orchestration: load, call domain, save, publish |
| Knows about I/O? | No | Yes (repositories, queues, clocks) |
| Example | `TransferPolicy.transfer(from_acct, to_acct, money)` | `TransferHandler.handle(cmd)` loads both accounts, calls the policy, saves both in a transaction |

This is the object-level version of "functional core, imperative shell" (`01` §9).

---

## 9 · Tell, don't ask — and the Law of Demeter

```python
# ASK: pull data out, decide outside, push the result back in.
if account.balance - amount >= -account.overdraft_limit and not account.frozen:
    account.balance -= amount

# TELL: ask the object to do it; the rule lives with the data.
account.withdraw(amount)
```

"Ask" code is how invariants escape into callers (§3). It is also a smell called
**feature envy**: a method more interested in another object's data than its own.

### Law of Demeter ("talk only to your immediate friends")

A method should call methods on: itself, its parameters, objects it creates, and its own
fields — **not** on objects returned by those.

```python
# Violation: the caller knows the whole object graph.
zip_code = order.customer.address.zip_code

# Better, IF the caller genuinely needs this as an Order concept:
zip_code = order.shipping_zip()
```

**Don't apply it mechanically.** It is about coupling to *structure that might change*,
not about counting dots. `df.groupby("x").sum().reset_index()` is a fluent <abbr title="Application Programming Interface">API</abbr> over one
abstraction and is fine. `Path("a").parent.name` navigates value objects that will never
restructure — also fine. Adding `order.shipping_zip()`, `order.shipping_city()`,
`order.shipping_country()`... to avoid dots creates a shallow, bloated `Order`. Ask:
*"If `Customer` stops owning `Address`, how many call sites break?"*

---

## 10 · Modeling state and lifecycles

Most LLD problems are secretly **state machines**: an order, a ticket, an elevator, a
vending machine, a booking, a ride. Draw the state diagram *before* the classes.

```
              pay()                 ship()               deliver()
  ┌───────┐ ─────────▶ ┌──────┐ ─────────▶ ┌─────────┐ ─────────▶ ┌───────────┐
  │ DRAFT │            │ PAID │            │ SHIPPED │            │ DELIVERED │
  └───┬───┘            └──┬───┘            └─────────┘            └───────────┘
      │ cancel()          │ cancel() → refund
      ▼                   ▼
  ┌───────────────────────────┐
  │         CANCELLED         │   terminal: no transitions out
  └───────────────────────────┘
```

### Three implementations, and when each fits

**1. Transition table** — best when states have little distinct behaviour.

```python
from enum import Enum, auto

class OrderState(Enum):
    DRAFT = auto(); PAID = auto(); SHIPPED = auto(); DELIVERED = auto(); CANCELLED = auto()

TRANSITIONS: dict[tuple[OrderState, str], OrderState] = {
    (OrderState.DRAFT, "pay"): OrderState.PAID,
    (OrderState.DRAFT, "cancel"): OrderState.CANCELLED,
    (OrderState.PAID, "ship"): OrderState.SHIPPED,
    (OrderState.PAID, "cancel"): OrderState.CANCELLED,
    (OrderState.SHIPPED, "deliver"): OrderState.DELIVERED,
}

class IllegalTransition(Exception): ...

class Order:
    def __init__(self) -> None:
        self.state = OrderState.DRAFT

    def apply(self, event: str) -> None:
        try:
            self.state = TRANSITIONS[(self.state, event)]
        except KeyError:
            raise IllegalTransition(f"{event} not allowed in {self.state.name}") from None
```

The whole lifecycle is one readable table; illegal transitions are rejected by default.

**2. State pattern** — best when each state has substantially *different behaviour* for
the same operations (vending machine: `insert_coin` does different things when idle, has
money, is dispensing, is out of stock). Each state is a class; the context delegates.
See `04_design_patterns_in_practice.md` §State and `lld/003_vending_machine_solution.py`.

**3. Typestate (types encode state)** — best when you can make illegal calls fail to
*compile/type-check*:

```python
@dataclass(frozen=True)
class DraftOrder:
    lines: tuple
    def pay(self, payment_id: str) -> "PaidOrder":
        return PaidOrder(self.lines, payment_id)

@dataclass(frozen=True)
class PaidOrder:
    lines: tuple
    payment_id: str
    def ship(self, tracking: str) -> "ShippedOrder": ...

# DraftOrder has no ship() method; mypy rejects draft.ship(...).
```

Typestate is excellent for protocols and builders; awkward when state is persisted and
reloaded (you need a union type on load).

---

## 11 · From problem statement to model: noun/verb analysis done right

The classic advice — "nouns become classes, verbs become methods" — is a starting list,
not an answer. Doing only that produces classitis and anemic models. The full method:

### Step 1 — Extract candidates

> *"A library has books. Members can borrow up to 5 books for 14 days. Late returns
> incur a fine of $1/day. Members can reserve a book that is currently borrowed; when
> it is returned, the first reservation holder is notified and has 2 days to collect."*

Nouns: library, book, member, fine, day, reservation, holder.
Verbs: borrow, return, incur, reserve, notify, collect.

### Step 2 — Filter

| Candidate | Keep as | Why |
|---|---|---|
| Library | Application service / facade | Coordinates; holds no domain invariant of its own |
| Book | **Split: `Book` (title, ISBN) and `BookCopy` (barcode, status)** | "Borrow a book" means a physical copy. Missing this split is the #1 library-design mistake. |
| Member | Entity | Has an invariant: ≤ 5 active loans |
| Loan | **Entity (discovered — not a noun in the text)** | Borrowing creates a record with due date and return date; fines are computed from it |
| Fine | Value object (`Money`) computed from a `Loan` | Has no lifecycle of its own unless payment tracking is required |
| Reservation | Entity with lifecycle: WAITING → NOTIFIED → FULFILLED / EXPIRED | The 2-day window is a state + deadline |
| day, 14, 5, $1 | Policy / configuration (`LoanPolicy`) | Numbers that change by membership tier belong in one place |
| notify | Port (`Notifier` interface) | I/O at the edge |

### Step 3 — Find the invariants and assign each to exactly one owner

- "≤ 5 active loans" → `Member` (or a `LoanService` holding a lock per member).
- "a copy is on at most one active loan" → `BookCopy` status.
- "first reservation wins" → `ReservationQueue` per `Book` (FIFO).
- "fine = max(0, days_late) × rate" → `LoanPolicy.fine(loan, returned_at)` — pure.

### Step 4 — Find what varies → put an interface there

Fine rules by tier, notification channel, and search are the likely extension points.
Everything else stays concrete. **Don't add interfaces for things the prompt gives no
reason to vary.**

### Step 5 — Walk a use case through the model

Trace "member returns a late book that has a reservation" across your objects. If a step
has no obvious owner, or one object reaches through three others, the model is wrong.
This walk-through is also exactly what an LLD interviewer wants to hear (see
`14_low_level_design_interview_playbook.md`).

### Use the domain's own words

Domain-driven design calls this the **ubiquitous language**: the class and method names
are the words the domain experts already use, with no translation layer. If the business
says "reservation" and the code says `HoldRequest`, every conversation needs a mapping
and the mapping breeds wrong logic. In an interview the prompt *is* the domain expert —
reuse its nouns and verbs (`borrow`, `return`, `reserve`), and when you find a concept the
prompt never named (`Loan` above), pick a plain business word for it and say so. The same
word meaning two different things in two parts of a system is a sign of two models; that
boundary is a bounded context (`CSFundamentals/04_software_engineering_deep_dive.md` §1).

---

## 12 · SOLID as questions, not commandments

The five rules are stated, with the failure each prevents, in the subsection below. What
senior engineers add is **knowing the question each principle asks and its failure
mode when over-applied.**

| Principle | The question it asks | Over-applied, it produces |
|---|---|---|
| **S**ingle Responsibility | "Which *people* or forces would ask this module to change?" (Martin's refined wording: one *actor*) | Classitis — one class per method, logic smeared across files |
| **O**pen/Closed | "Is this the axis of change I actually expect?" | Plugin architectures for things that never change; indirection everywhere |
| **L**iskov Substitution | "Would every caller of the parent still be correct with this child — same preconditions or weaker, postconditions or stronger, no new exceptions?" | (Rarely over-applied — violations are the common problem) |
| **I**nterface Segregation | "Does each client depend only on what it uses?" | One-method interfaces nobody needed, when the consumer really uses five |
| **D**ependency Inversion | "Does policy depend on detail, or detail on policy?" | An interface per class, a DI container for a 500-line script |

### The five rules, stated, and the failure each one prevents

| Rule | Statement | The failure it prevents |
|---|---|---|
| **SRP** | A module has one reason to change | Unrelated features coupled through one class: a change for reason A silently breaks reason B, and every team's PR collides in the same file |
| **OCP** | Open for extension, closed for modification: add a variant by adding code, not by editing a shared branchy core | Each new variant edits a central `if/elif` that every other variant also depends on, so one bad edit regresses cases you never meant to touch |
| **LSP** | A subtype must be usable anywhere its base type is, without changing correctness | Polymorphic callers that type-check and pass a smoke test, then misbehave in production when the "wrong" subtype is injected |
| **ISP** | A client shouldn't depend on methods it doesn't use | A fat interface forces implementers to stub methods (`raise NotImplementedError`), turning a compile-time contract into a runtime landmine |
| **DIP** | High-level policy depends on abstractions it owns; details depend on those abstractions | Business logic that instantiates a concrete driver or client, so its tests need a live database or network |

OCP and DIP already have complete worked examples in this track — Strategy and
Specification (`04` §3, §15) are the OCP fix, and `08` §4 and §8 show DIP end to end — so
here are the two whose *before* is easiest to miss:

```python
# SRP — BEFORE: three reasons to change (finance rules, print layout, schema) in one class.
class Invoice:
    def total(self) -> int: ...
    def to_pdf(self) -> bytes: ...            # changes when the layout changes
    def save(self, db) -> None: ...           # changes when the schema changes

# AFTER: split by who asks for the change.
class Invoice:            # the rules
    def total(self) -> int: ...
class InvoicePdf:         # presentation
    def render(self, invoice: Invoice) -> bytes: ...
class InvoiceRepository:  # persistence
    def save(self, invoice: Invoice) -> None: ...
```

```python
# ISP — BEFORE: one contract; read-only implementations must lie about the write half.
class Repository(Protocol):
    def get(self, order_id: str) -> Order: ...
    def save(self, order: Order) -> None: ...

class ReplicaRepository:
    def get(self, order_id): ...
    def save(self, order): raise NotImplementedError   # the interface lies about this class

# AFTER: each client depends on the capability it uses.
class OrderReader(Protocol):
    def get(self, order_id: str) -> Order: ...
class OrderWriter(Protocol):
    def save(self, order: Order) -> None: ...

def render_invoice(orders: OrderReader, order_id: str) -> str: ...   # cannot write by accident
```

A `NotImplementedError` in an override is the shared symptom of an ISP and an LSP
violation (§15) — the cure is the same: split the contract so each type promises only what
it can keep.

### LSP, precisely — the one people get wrong

A subtype must honour the parent's **contract**, not just its signatures:

| Rule | Allowed in subtype | Violation example |
|---|---|---|
| Preconditions | Same or **weaker** | `ReadOnlyList.append` raises — callers of `list` assumed append works |
| Postconditions | Same or **stronger** | `CachedRepo.save` returns before durably writing, where `Repo.save` promised durability |
| Invariants | Preserved | `Square(Rectangle)`: `set_width` also changes height |
| Exceptions | No new *kinds* the caller wasn't told to expect | `S3Storage.get` raises `botocore` errors where `Storage.get` promised `KeyError` |
| History | No new mutation paths the parent forbade | `MutablePoint(ImmutablePoint)` |

Python's own standard library carries a famous exemption: `bool` is a subclass of `int`,
so `True + True == 2`, and `isinstance(True, int)` is `True` — which is why JSON
validators and `sum()`-based code sometimes treat booleans as numbers by accident.

### DIP vs. dependency injection vs. IoC containers

- **Dependency Inversion** is a *design* rule: high-level policy defines the interface;
  low-level detail implements it.
- **Dependency Injection** is a *technique*: pass collaborators in (constructor
  parameters) instead of constructing them inside.
- **IoC container** is a *tool* that automates wiring. Go and Python codebases rarely
  need one; a hand-written `main()` / composition root is clearer. See
  `PyEngineering/18_dependency_injection_layering` and `GoEngineering/18_*`.

---

## 13 · UML you actually need

In an interview, draw **a class diagram with only the important classes and a sequence
diagram for the one tricky flow.** Nobody wants the full spec.

### Class diagram, text form (works on a whiteboard and in a doc)

```
┌─────────────────────────┐         ┌───────────────────────────┐
│ ParkingLot              │ 1    1..*│ ParkingFloor              │
├─────────────────────────┤◆────────├───────────────────────────┤
│ - floors: list[Floor]   │         │ - spots: dict[SpotType,…] │
│ - pricing: PricingPolicy│         ├───────────────────────────┤
├─────────────────────────┤         │ + find_spot(v): Spot|None │
│ + park(v): Ticket       │         └───────────────────────────┘
│ + unpark(t): Money      │
└──────────┬──────────────┘
           │ uses
           ▼
┌─────────────────────────┐        ┌───────────────┐   ┌───────────────┐
│ «interface»             │◁┄┄┄┄┄┄┄│ HourlyPricing │   │ FlatPricing   │
│ PricingPolicy           │◁┄┄┄┄┄┄┄┼───────────────┘   └───────────────┘
│ + price(ticket, now)    │
└─────────────────────────┘

  +  public   -  private   #  protected    «interface»  stereotype
  ◆  composition   ◇ aggregation   ◁┄┄ realization   ◁── inheritance
```

### Sequence diagram for the tricky flow

```
Client        ParkingLot         Floor            Spot          PricingPolicy
  │  park(car)    │                │                │                  │
  │──────────────▶│ find_spot(car) │                │                  │
  │               │───────────────▶│  try_occupy()  │                  │
  │               │                │───────────────▶│ (atomic: CAS or  │
  │               │                │◀───── ok ──────│  lock per floor) │
  │               │◀──── spot ─────│                │                  │
  │◀── Ticket ────│                │                │                  │
  │                                                                    │
  │ unpark(ticket)│                                                    │
  │──────────────▶│───────────── price(ticket, now) ──────────────────▶│
  │◀── Money ─────│◀──────────────────────── amount ───────────────────│
```

---

## 14 · OOP vs. functional vs. data-oriented

Knowing when *not* to use objects is part of design maturity.

| Style | Organises around | Great for | Weak at |
|---|---|---|---|
| **Object-oriented** | Entities with behaviour and invariants | Long-lived domain models with rich rules; plug-in variation by type | Data transformations; operations that cut across many types |
| **Functional** | Pure functions over immutable data | Pipelines, calculations, concurrency, testability | Modeling identity and long-lived mutable state explicitly |
| **Data-oriented** | Arrays of plain records, processed in bulk | Performance (cache locality), analytics, ECS game engines | Enforcing invariants on individual items |

### The expression problem

- With **classes**, adding a new *type* is easy (one new class), adding a new
  *operation* touches every class.
- With **functions + sum types / `match`**, adding an *operation* is easy (one new
  function), adding a *type* touches every function.

Choose based on which axis will grow. A compiler's AST gains operations (passes) more
often than node types → functions + `match` (or Visitor). A payment platform gains
payment methods more often than operations → classes.

### The same task, three ways

```python
items = [("apple", 3, 0.50), ("bread", 1, 2.00)]   # (name, qty, unit_price)

# OOP: behaviour lives on an object.
class LineItem:
    def __init__(self, name: str, qty: int, unit_price: float) -> None:
        self.name, self.qty, self.unit_price = name, qty, unit_price
    def total(self) -> float:
        return self.qty * self.unit_price

oop_total = sum(LineItem(*i).total() for i in items)

# FUNCTIONAL: a pure function over plain, immutable data.
def line_total(item: tuple[str, int, float]) -> float:
    _, qty, unit_price = item
    return qty * unit_price

fn_total = sum(line_total(i) for i in items)

# DATA-ORIENTED: bulk operation over parallel arrays, no per-item object at all.
quantities = [i[1] for i in items]
prices = [i[2] for i in items]
data_total = sum(q * p for q, p in zip(quantities, prices))

assert oop_total == fn_total == data_total == 3.5
```

Same answer, three ways of organising the same handful of lines. At this size it's a
matter of taste; the table above is about which style keeps paying off as the codebase
grows in one direction or the other.

### Most good Python/Go code is a mix

Immutable value objects (functional), a few rich entities guarding invariants (OO), pure
policy functions (functional), and a thin imperative shell doing I/O.

---

## 15 · Red flags

| Red flag | Likely problem | Move |
|---|---|---|
| `set_x()` for every field | Anemic model; invariants live in callers | Replace setters with intention-revealing methods |
| `isinstance` / `type ==` chains repeated across files | Missing polymorphism | Replace conditional with polymorphism (or one `match`) |
| Subclass overrides a method to `raise NotImplementedError` | LSP violation | Split the interface; compose instead |
| Inheritance deeper than 2 levels in app code | Reuse via inheritance | Extract collaborators, compose |
| Class named `*Manager`, `*Helper`, `*Util`, `*Processor` | No clear responsibility | Name the invariant it protects; split or merge |
| Methods returning internal mutable collections | Leaked invariants | Return copies, tuples, or iterators |
| An entity holding object references to other aggregates | Transactions/locks spanning aggregates | Reference by ID |
| `float` for money; `str` for email/currency/status | Primitive obsession | Value objects, enums |
| Boolean flags `is_paid`, `is_shipped`, `is_cancelled` together | Hidden state machine | Explicit `Enum` state + transitions |
| Object must be `init()`-ed after construction | Temporal coupling, half-valid objects | Validate in constructor / factory |
| Interface with exactly one implementation and no test fake | Speculative abstraction | Delete it until a second need appears |
| `__eq__` defined without matching `__hash__` | Broken set/dict behaviour | Hash only immutable identity |

---

## 16 · Interview questions and model answers

**Q: Composition vs. inheritance — when do you use each?**
Inheritance only for a true subtype relationship that satisfies Liskov, ideally shallow
and within one team's code (exception hierarchies, framework hooks). Composition for
reuse and for anything with independently varying dimensions — inheritance couples the
child to the parent's implementation (fragile base class) and multiplies classes (N×M),
composition adds them (N+M).

**Q: Abstract class vs. interface?**
An interface is a pure contract; an abstract class is a partial implementation plus a
contract. Use an abstract class when implementations genuinely share code and a template
(Template Method). Otherwise prefer an interface, because a class can satisfy many
interfaces but inherit implementation from only one line — and in Python/Go, structural
interfaces (`Protocol`, Go interfaces) let consumers define the contract without
touching the provider.

**Q: What's encapsulation *for*?**
Protecting invariants. Private fields are the mechanism; the goal is that there is exactly
one place that can put the object into a given state, so every rule is checked once.

**Q: Give an LSP violation you've seen.**
A read-only collection subclassing a mutable one and raising on `add`; or a caching
repository whose `save` returns before persisting when the base promised durability. The
signature matched; the contract didn't.

**Q: Entity vs. value object?**
Entities have identity that persists across attribute changes and are compared by ID;
value objects are defined by their attributes, are immutable, compared by value, and safe
to share. Money, date ranges, addresses, coordinates are value objects.

**Q: How do you model something with a lifecycle?**
Draw the state diagram first. Explicit enum state + a transition table when behaviour per
state is similar; the State pattern when each state behaves very differently; typestate
when the type system can forbid illegal calls. Reject undefined transitions by default.

**Q: How do you decide what classes to create from a problem statement?**
Nouns/verbs as a candidate list, then: split concepts that the text conflates (book vs.
copy), discover records that the verbs create (loan, ticket, booking), assign each
invariant to one owner, put interfaces only where the problem implies variation, and
walk each use case through the model to check ownership.

**Q: Is the Law of Demeter about counting dots?**
No. It's about not coupling to object-graph structure that might change. Fluent APIs over
one abstraction and navigation through stable value objects are fine.

**Q: Why is Go "object-oriented" without classes?**
It has encapsulation (package-level export), polymorphism (implicit interfaces), and
composition (embedding) — it deliberately omits implementation inheritance, which
removes the fragile base class problem and forces composition.

---

## 17 · Checklist

**Model**
- [ ] Every class protects at least one named invariant — or is a plain record on purpose.
- [ ] Invariants are established in the constructor and preserved by every public method.
- [ ] No setters that bypass rules; no mutable internals returned.
- [ ] Domain primitives (money, IDs, ranges, email) are value objects.
- [ ] Lifecycles are explicit enums/state machines, not boolean flags.

**Relationships**
- [ ] Composition by default; each inheritance edge passes the Liskov test.
- [ ] Aggregates reference each other by ID.
- [ ] Cardinality and ownership (who creates, who deletes) are stated.
- [ ] Bidirectional references exist only where a query needs them.

**Abstractions**
- [ ] Interfaces are small and defined by what the consumer needs.
- [ ] Each interface exists because something varies or a test needs a seam.
- [ ] Contracts (errors, idempotency, thread safety) are documented, not just signatures.

**Interview**
- [ ] I can model a library, parking lot or booking system in 10 minutes, naming the
      invariants and their owners.
- [ ] I can explain the three kinds of polymorphism and the expression problem.
- [ ] I can state LSP's pre/postcondition rules and give a real violation.
