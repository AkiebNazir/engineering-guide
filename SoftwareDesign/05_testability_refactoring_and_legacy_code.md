# Testability, Refactoring, and Legacy Code

> "Legacy code is simply code without tests." — Michael Feathers
>
> "Refactoring is a controlled technique for improving the design of an existing code
> base... small behavior-preserving transformations." — Martin Fowler

Designs are rarely written fresh. Most of an engineer's design work is **changing
existing code safely**, and the single best predictor of whether a design is good is
whether it is **easy to test**. Hard-to-test code is almost always badly coupled code;
the test is just where the coupling becomes visible.

This file covers designing for testability, choosing test doubles, the refactoring
catalog as smell → move, and techniques for code that has no tests yet.

**Already covered elsewhere — not repeated here:**

| Topic | Where |
|---|---|
| Functional core / imperative shell | `01_philosophy_of_software_design.md` §9 |
| Table-driven tests and fakes (runnable) | `PyEngineering/20_table_driven_tests_fakes`, `GoEngineering/20_*` |
| Fuzzing and property-based testing (runnable) | `PyEngineering/21_fuzzing_property_testing`, `GoEngineering/21_*` |
| A worked refactor end to end | `01_philosophy_of_software_design.md` §16 |

---

## Contents

1. [Why testability is a design property](#1--why-testability-is-a-design-property)
2. [The four things that make code hard to test](#2--the-four-things-that-make-code-hard-to-test)
3. [Seams: where behaviour can be changed without editing code](#3--seams-where-behaviour-can-be-changed-without-editing-code)
4. [Test doubles: dummy, stub, spy, mock, fake](#4--test-doubles-dummy-stub-spy-mock-fake)
5. [What to test: behaviour, not implementation](#5--what-to-test-behaviour-not-implementation)
6. [The refactoring loop and the catalog as smell → move](#6--the-refactoring-loop-and-the-catalog-as-smell--move)
7. [Working with legacy code](#7--working-with-legacy-code)
8. [Large-scale change: strangler fig, branch by abstraction, flags](#8--large-scale-change-strangler-fig-branch-by-abstraction-flags)
9. [Technical debt as a design decision](#9--technical-debt-as-a-design-decision)
10. [Code review as design review](#10--code-review-as-design-review)
11. [Interview questions and model answers](#11--interview-questions-and-model-answers)
12. [Checklist](#12--checklist)

---

## 1 · Why testability is a design property

A unit is easy to test when you can:

1. **construct it** without building the world,
2. **control its inputs** — including time, randomness, and collaborators' responses,
3. **observe its outputs** — return values or recorded effects,
4. **run it fast and deterministically.**

Every one of those is a design property:

| Test difficulty | Underlying design problem |
|---|---|
| Constructor needs a DB, a network client, and a config file | Dependencies created internally, not injected (DIP) |
| Result depends on the current time or random numbers | Hidden inputs; non-determinism inside logic |
| Need to inspect private fields to know if it worked | No observable output; command/query mixed |
| 40 lines of mock setup per test | Too many collaborators; low cohesion; stamp coupling |
| Test breaks whenever internals are refactored | Test coupled to implementation, or the unit has no stable interface |
| Tests pass alone, fail together | Shared global/singleton state |

**The rule:** if a test is painful, fix the design, not the test. Mocking frameworks that
can patch anything (`unittest.mock.patch` on module internals) let you test badly
designed code — which removes the pressure that would have improved it.

### TDD: what writing the test first actually buys

**Test-driven development** is a loop — write a failing test (red), make it pass with the
simplest code (green), clean up with the tests as a safety net (refactor) — repeated in
minutes-long cycles. What it buys is *not* "tests exist"; you can retrofit those. Writing
the test first makes you the **first caller of an <abbr title="Application Programming Interface">API</abbr> that doesn't exist yet**, so you
design it from the outside in:

```python
# Written before Coupon exists. The caller's view already decides the API.
def test_expired_coupon_gives_no_discount():
    clock = FakeClock("2026-01-02")
    assert Coupon("SAVE10", expires="2026-01-01").apply(100, clock) == 100
```

That one test forced time to be an input (the seam from §2), the method to be a pure-ish
function of its arguments, and the unit to be constructible without a database. Code
written test-first tends to have narrower, injected, single-purpose units, because a
tangled unit is painful to call from a test *before* you've built it.

Where it is weak: exploratory spikes where you don't yet know the interface (spike, throw
it away, then test-drive the real one); UI layout; and mock-heavy styles that pin tests to
the implementation (§5). TDD applies design pressure, but it doesn't supply the design —
you still need the ideas from `01`–`03`. In an interview, the cheap version is to write
two or three example calls with expected results *first*: it is a spec you can check the
finished code against.

---

## 2 · The four things that make code hard to test

### 1. Hidden dependencies created inside

```python
# HARD: the class builds its own collaborators.
class ReportService:
    def __init__(self) -> None:
        self.db = PostgresClient(os.environ["DB_URL"])
        self.mailer = SmtpMailer("smtp.internal")

# EASY: dependencies are parameters; production wiring happens in main().
class ReportService:
    def __init__(self, db: "ReportQueries", mailer: "Mailer") -> None:
        self.db, self.mailer = db, mailer
```

### 2. Non-determinism: time, randomness, UUIDs, concurrency

```python
# HARD: can't test "expired" without waiting or patching datetime.
def is_expired(token) -> bool:
    return token.expires_at < datetime.now(timezone.utc)

# EASY: time is an input.
def is_expired(token, now: datetime) -> bool:
    return token.expires_at < now
```

For objects that need time repeatedly, inject a `Clock` (a `Callable[[], float]` is
enough) and use a `FakeClock` that tests advance manually. Same for `random.Random(seed)`
and ID generators. Every LLD solution in `lld/` takes a clock for this reason — rate
limiters, seat holds, and parking fees are otherwise untestable.

```go
// Go: accept a func() time.Time or a small Clock interface.
type Limiter struct {
	now func() time.Time
}
```

### 3. Logic tangled with I/O

The functional core / imperative shell split (`01` §9): compute decisions in pure
functions, perform effects at the edges. The pure part needs no doubles at all.

### 4. Global and static state

Singletons, module-level caches, class variables mutated at runtime, environment
variables read deep inside code. Tests interfere with each other and ordering matters.
Pass state in; if a global must exist, give it a reset hook used only by tests — and
treat needing that hook as a smell.

---

## 3 · Seams: where behaviour can be changed without editing code

Feathers' definition: a **seam** is a place where you can alter behaviour without editing
in that place. Every seam has an **enabling point** where you choose which behaviour.

| Seam type | Enabling point | Python | Go |
|---|---|---|---|
| **Object seam** | Constructor/parameter | Pass a fake object | Pass a fake implementing the interface |
| **Function seam** | Parameter / attribute | Pass a callable; default to the real one | `var now = time.Now` package var (test swaps it) or a func field |
| **Module/link seam** | Import / build | `unittest.mock.patch("pkg.mod.name")` | Build tags; `internal` test packages |
| **Configuration seam** | Config / env | `STORAGE=memory` | Same |

**Prefer object and function seams** — they're explicit in the signature and survive
refactoring. `mock.patch` by import path is a module seam; it's the right tool for legacy
code you can't yet change, and a smell in code you're designing now, because it couples
the test to *where* a name is imported (patching `requests.get` does nothing if the code
did `from requests import get` — you must patch `mymodule.get`).

The `ReportService` in §2 is already an object seam — the constructor parameter is the
enabling point. A function seam is the same idea for a single call, not a whole object:

```python
from dataclasses import dataclass

@dataclass
class Order:
    customer_email: str

def real_send_email(to: str, body: str) -> None:
    ...                                    # actually talks to an SMTP server

def send_receipt(order: Order, send=real_send_email) -> None:   # `send` is the seam
    send(order.customer_email, "Thanks for your order")

sent = []
send_receipt(Order("a@b.com"), send=lambda to, body: sent.append((to, body)))
assert sent == [("a@b.com", "Thanks for your order")]
```

Production calls `send_receipt(order)` and gets the default, real sender; the test
passes a different function. Nothing was patched, and the seam is visible in the
signature.

---

## 4 · Test doubles: dummy, stub, spy, mock, fake

The vocabulary is Gerard Meszaros'; interviewers expect you to use it precisely.

| Double | What it does | Verifies | Use for |
|---|---|---|---|
| **Dummy** | Passed but never used | — | Filling a required parameter |
| **Stub** | Returns canned answers | Nothing — you assert on the SUT's output | Controlling indirect *inputs* ("repo returns this user") |
| **Spy** | Records how it was called | Afterwards, by the test | Checking indirect *outputs* ("an email was sent to X") |
| **Mock** | Pre-programmed with expectations; fails if not met | Itself, during/after the call | Interaction protocols that *are* the behaviour |
| **Fake** | A working, simplified implementation | Behaviour via real state | Repositories, queues, clocks, file systems |

```python
class FakeClock:                                 # FAKE: real behaviour, controllable
    def __init__(self, t: float = 0.0) -> None: self.t = t
    def __call__(self) -> float: return self.t
    def advance(self, s: float) -> None: self.t += s

class SpyMailer:                                 # SPY: records calls for later assertions
    def __init__(self) -> None: self.sent: list[tuple[str, str]] = []
    def send(self, to: str, body: str) -> None: self.sent.append((to, body))

def test_overdue_reminder():
    clock, mailer, loans = FakeClock(), SpyMailer(), InMemoryLoans()
    loans.add(Loan("m1", "book-1", due=10.0))
    clock.advance(11.0)
    send_overdue_reminders(loans, mailer, clock)
    assert mailer.sent == [("m1", "book-1 is overdue")]    # state-based assertion
```

`FakeClock` above is a **fake** and `SpyMailer` a **spy**. The other three in one place:

```python
from unittest.mock import Mock

class DummyLogger:                                 # DUMMY: required by the signature, never called
    def log(self, msg: str) -> None:
        raise AssertionError("should never be called")

class StubUserRepo:                                 # STUB: canned answer, controls the input
    def get(self, user_id: str) -> dict:
        return {"id": user_id, "plan": "pro"}

def test_pro_users_get_priority_support():
    repo = StubUserRepo()
    assert routes_to_priority_queue(repo.get("u1")) is True

def test_gateway_charged_exactly_once():
    gateway = Mock()                                # MOCK: the expectation IS the behaviour under test
    checkout(gateway, order_total=1999, idempotency_key="k1")
    gateway.charge.assert_called_once_with(1999, idempotency_key="k1")
```

`DummyLogger` never has `.log()` called in this test — it's only there because the
constructor requires *a* logger. `StubUserRepo` controls an indirect input without
caring how it's called. `Mock` verifies an indirect output *as an expectation*, which is
why mocks belong where the call itself is the behaviour under test (below).

### Fakes over mocks — why

- **Mocks couple tests to implementation.** `repo.get.assert_called_once_with(42)` fails
  if you add a cache or batch the lookup, although behaviour is identical.
- **Mocks can drift from reality.** A mock happily returns a value the real dependency
  never would; fakes, with a **contract test** run against both fake and real
  implementation, cannot drift silently.
- **Fakes are reusable** across hundreds of tests; mock setup is re-written in each.

Use mocks when **the interaction is the behaviour** — "the payment gateway is called
exactly once with this idempotency key", "we never call the external <abbr title="Application Programming Interface">API</abbr> when the cache
is warm."

### Contract tests keep fakes honest

```python
import pytest

@pytest.fixture(params=["memory", "sqlite"])
def repo(request, tmp_path):
    if request.param == "memory":
        return InMemoryOrderRepository()
    return SqliteOrderRepository(tmp_path / "t.db")

def test_get_missing_raises_not_found(repo):       # runs against BOTH implementations
    with pytest.raises(NotFound):
        repo.get("nope")
```

**Don't mock what you don't own.** Wrap third-party clients in an adapter you own
(`04_design_patterns_in_practice.md` §10), fake *your* adapter interface in unit tests,
and test the adapter itself against the real service (or its official emulator) in a
small number of integration tests.

---

## 5 · What to test: behaviour, not implementation

A good test fails when **behaviour** breaks and passes through any **refactoring**.

```python
# IMPLEMENTATION-COUPLED: breaks if we switch the internal list to a deque.
def test_push():
    s = Stack(); s.push(1)
    assert s._items == [1]

# BEHAVIOURAL: survives any internal change.
def test_push_then_pop_returns_last_pushed():
    s = Stack(); s.push(1); s.push(2)
    assert s.pop() == 2 and s.pop() == 1
```

Guidelines:

- **Test through the public interface.** If a private helper seems to need direct tests,
  it's probably a missing module — extract it and test *that* public interface.
- **One behaviour per test,** named as a sentence: `test_withdraw_beyond_overdraft_raises_and_leaves_balance_unchanged`.
- **Arrange–Act–Assert** (Given–When–Then). A second Act means a second test.
- **Test invariants and edge cases,** not just the happy path: empty, one, boundary,
  duplicate, concurrent, failure halfway.
- **Property-based tests** for invariants: "for any sequence of deposits/withdrawals, the
  balance never drops below −overdraft", "decode(encode(x)) == x".
- **Determinism is non-negotiable.** A flaky test is worse than no test — it trains
  people to ignore red builds.

The property holds for *every* input, so instead of picking examples by hand, generate
many and check it holds:

```python
import random

def encode(x: int) -> str: return f"n:{x}"
def decode(s: str) -> int: return int(s.split(":", 1)[1])

def test_decode_encode_roundtrips_for_any_int():
    for _ in range(200):
        x = random.randint(-10_000, 10_000)
        assert decode(encode(x)) == x
```

A real property-based library (Hypothesis for Python, `testing/quick` for Go) does the
same thing but also shrinks a failing case to the smallest input that still fails, and
replays known-bad inputs across runs — worth adopting once you're writing these by hand
more than occasionally. Runnable versions: `PyEngineering/21_fuzzing_property_testing`,
`GoEngineering/21_*`.

### The test-size model (Google's terminology)

Google classifies tests by **size** (resources allowed), not by the ambiguous
"unit/integration" labels:

| Size | Constraints | Typical content |
|---|---|---|
| **Small** | Single process, single thread, no I/O, no sleep | Logic with fakes; milliseconds |
| **Medium** | Single machine; localhost network, local DB/containers | Adapters against real dependencies |
| **Large** | Multiple machines / real environments | End-to-end, few in number |

The design goal is that **most behaviour is testable with small tests** — which is only
possible if the code has seams and a functional core.

### The shape of a suite: pyramid vs. ice-cream cone

The same idea is usually drawn as the **testing pyramid**: many fast tests at the base,
fewer at each slower, broader layer above.

```
        /\         few  — end-to-end: the whole stack; slow, flaky, high confidence per test
       /  \
      /----\       some — integration: real boundaries (DB, HTTP contract); moderate speed
     /------\
    /--------\     many — unit: isolated logic, fast and cheap to rerun
```

Each step up costs more to write, runs slower, fails for more unrelated reasons, and tells
you less about *where* the bug is. Google's testing blog ("Just Say No to More End-to-End
Tests", 2015) suggests roughly a 70 / 20 / 10 split of small / medium / large tests as a
starting point — a proportion to sanity-check against, not a quota.

**The inverted shape — the "ice-cream cone"** — is mostly end-to-end tests with few unit
tests. Consequences: the suite takes minutes to hours instead of seconds; it is flaky,
because end-to-end tests depend on timing, the network, and shared environments; locating
one logic bug means standing up the whole stack; and engineers stop running tests before
they push, so feedback moves from seconds to CI turnaround. It is usually a *design*
symptom: logic is tangled with I/O, so nothing can be tested below the top.

---

## 6 · The refactoring loop and the catalog as smell → move

**Refactoring** means changing structure *without changing behaviour*, in small steps,
with tests passing after each step. If behaviour changes, it's not a refactoring — it's a
feature or a fix, and it goes in a separate commit.

```
      ┌──────────────────────────────────────────────┐
      │ 1. Tests green (add characterization tests   │
      │    first if coverage is missing — §7)        │
      └───────────────┬──────────────────────────────┘
                      ▼
      ┌──────────────────────────────────────────────┐
      │ 2. Make ONE small structural change          │◀──┐
      └───────────────┬──────────────────────────────┘   │
                      ▼                                  │
      ┌──────────────────────────────────────────────┐   │
      │ 3. Run tests. Red? Revert, take a smaller    │   │
      │    step. Green? Commit.                      │───┘
      └──────────────────────────────────────────────┘
```

Kent Beck: **"Make the change easy (warning: this may be hard), then make the easy
change."** Refactor *toward* the feature you're about to add — "preparatory refactoring" —
rather than refactoring for its own sake.

### Smell → move table

The most useful subset of Fowler's catalog, organised by what you notice.

| Smell | Refactoring moves |
|---|---|
| **Long function** | Extract Function (name the idea); Replace Temp with Query; Decompose Conditional; Split Loop |
| **Long parameter list** | Introduce Parameter Object (value object); Preserve Whole Object; Replace Parameter with Query |
| **Duplicated code** | Extract Function; Pull Up Method; Slide Statements to align, then extract |
| **Divergent change** (one class changes for many reasons) | Split Phase; Extract Class; Move Function |
| **Shotgun surgery** (one change touches many classes) | Move Function/Field to gather the knowledge; Combine Functions into Class; Inline Class |
| **Feature envy** | Move Function to the data it uses |
| **Data clumps** (same 3 fields travel together) | Introduce Parameter Object / Extract Class |
| **Primitive obsession** | Replace Primitive with Object (value object); Replace Type Code with Subclasses / enum |
| **Repeated switches on type** | Replace Conditional with Polymorphism |
| **Loops that filter/map/accumulate** | Replace Loop with Pipeline (comprehensions, generators) |
| **Speculative generality** | Collapse Hierarchy; Inline Function/Class; Remove unused parameters |
| **Temporary field** (set only in some code paths) | Extract Class; Introduce Special Case (Null Object) |
| **Message chains** `a.b().c().d()` | Hide Delegate — *or* leave it (`02` §9) |
| **Middle man** (class that only delegates) | Remove Middle Man; Inline Function |
| **Refused bequest** (subclass ignores parent behaviour) | Replace Subclass with Delegate; Replace Superclass with Delegate |
| **Mutable data shared widely** | Encapsulate Variable; Split Variable; Change Reference to Value |
| **Flag arguments** | Remove Flag Argument (separate functions) |
| **Comments explaining what a block does** | Extract Function named by the comment |
| **Nested conditionals** | Replace Nested Conditional with Guard Clauses |
| **Error codes / sentinel returns** | Replace Error Code with Exception (Python) / typed errors (Go) |

### Named anti-patterns — the vocabulary reviewers use

The table above is organised by what you *notice*. These are the bigger, named failures
people say out loud in reviews and interviews; each is mostly a principle violated far
enough to earn its own name.

| Anti-pattern | What it is | The move | Where |
|---|---|---|---|
| **God object** (blob) | One class that knows and controls most of the system — `OrderManager` creating orders, emailing, taxing, discounting, persisting, rendering PDFs. Every unrelated change and every team's PR lands in the same file | Extract Class along reasons to change (Divergent change, above); name the invariant each new class protects | `02` §12 (SRP), §15 |
| **Spaghetti code** | Control flow with no discernible structure: deep nesting, side effects interleaved with logic, so answering "what happens when X" means reading the whole function | Guard clauses; Extract Function named by intent; separate logic from I/O | `01` §9, §10 |
| **Anemic domain model** | Data classes with no behaviour plus "service" classes holding all the rules, so any code can set `order.status = "shipped"` and bypass the rule | Move the behaviour onto the entity that owns the data | `02` §3 |
| **Shotgun surgery** | One conceptual change edits many unrelated files because ownership of the concept is scattered — the opposite failure to a god object. Adding a payment method touching twelve files is the usual case | Gather the knowledge (Move Function/Field); the missing piece is often a Strategy or registry | `04` §3, §4 |
| **Feature envy** | A method that spends its body reaching into another object's data: `Invoice.total_with_tax(customer)` reading `customer.region.tax_rate` | Move Function to the data it uses, or pass the value in | `02` §9 |
| **Magic numbers / strings** | Unexplained literals (`status == 3`, `price * 0.15`); the same literal in two places drifts apart | Named constant or `Enum` (connascence of meaning) | `01` §11; `03` §3 |
| **Premature optimization** | Optimizing before a profile shows the path matters, spending clarity or flexibility on an unmeasured gain | Measure first; optimise the one hot path behind a stable interface | `01` §17; `11` §8, §11 |
| **Big ball of mud** | No recognisable architecture: dependencies point every direction and no boundary is left to reason about. Usually the end state of accumulated shotgun surgery and unrepaid debt, not one bad decision (the name is from Foote and Yoder's 1997 paper) | No rewrite: draw one boundary at a time, strangle old paths, enforce with import checks | §8, §9; `03` §12; `08` §13 |
| **Cargo-cult pattern use** | A named pattern applied because it looks properly engineered, not because its force is present: a Singleton for something never singular, a Strategy with one implementation. The tell is indirection with no flexibility payoff | Delete the indirection until a second case appears | `04` §19 |
| **Tight coupling to concrete classes** | A class instantiates its own Postgres connection or HTTP client, so tests need the real thing and swapping it means editing the class | Take an interface the *consumer* owns and inject the implementation (DIP) | §2; `08` §8 |

One habit covers most of the table: when you name an anti-pattern in review, name the
**move** too — "this is shotgun surgery; the payment logic should live in one strategy" is
a suggestion, "this is a mess" is not.

### Mechanics matter: two examples done safely

**Extract Function**

1. Create the new function, named by *intent*.
2. Copy the fragment in. Variables it reads become parameters; variables it assigns and
   the caller uses become return values.
3. Replace the fragment with a call. Run tests.

```python
# Before: the fragment is buried in a longer function.
def invoice_total_v1(invoice) -> float:
    total = 0
    for item in invoice.items:
        total += item.price * item.quantity
    return total

# After: the fragment is a function named by intent; behaviour is unchanged.
def invoice_total(invoice) -> float:
    return sum(item.price * item.quantity for item in invoice.items)
```

Both compute the same result for the same input — that's the whole point of a
refactoring — which is exactly what a characterization test (§7) would catch if they
didn't.

**Change Function Declaration (migration style)** — when callers are many or outside your
control:

1. Extract the body into a new function with the new signature.
2. Make the old function call the new one (and deprecate it).
3. Migrate callers one by one, testing each.
4. Remove the old function when it has no callers.

```python
def send_email(to: str, subject: str, body: str) -> None:  # step 1: the new signature
    ...

def send(to: str, body: str) -> None:                       # step 2: old name forwards
    send_email(to, subject="", body=body)

# step 3: callers migrate one at a time from send(to, body) to send_email(to, "", body)
# step 4: once nothing calls send(...), delete it
```

That second one is expand → migrate → contract (`03` §10) applied inside a codebase.

### Tooling

Use the IDE's automated refactorings (rename, extract, move, change signature) —
they're semantics-aware and much safer than hand edits. In Go, `gopls` rename and
`gofmt -r 'pattern -> replacement'`; `eg`/`gopatch` for larger rewrites. In Python,
PyCharm / rope / LibCST codemods.

---

## 7 · Working with legacy code

**Legacy code dilemma** (Feathers): *to change code safely you need tests; to add tests
you need to change the code.* The escape is a small set of minimally invasive techniques.

### The legacy change algorithm

1. **Identify change points.**
2. **Find test points** — where you can observe the effect.
3. **Break dependencies** — the minimum, most mechanical edits to get the code into a test.
4. **Write characterization tests.**
5. **Make the change and refactor.**

### Characterization tests (a.k.a. golden master / approval tests)

A characterization test records **what the code currently does**, not what it should do.

```python
def test_characterize_invoice_total():
    # Step 1: write the call with an obviously wrong expectation.
    # Step 2: run it; the failure message tells you the actual value.
    # Step 3: paste the actual value in. You've pinned current behaviour.
    assert legacy_invoice_total(customer="acme", items=SAMPLE_ITEMS, region="EU") == 1187.46
```

For big outputs (reports, HTML, JSON), snapshot the whole output to a file and diff
against it; generate many input combinations to cover branches. If you find a bug while
characterising, **pin the buggy behaviour first**, and fix it as a separate, visible
change — someone may depend on it (Hyrum's law).

### Dependency-breaking techniques (the safe, mechanical ones)

| Technique | Move | Example |
|---|---|---|
| **Parameterize Constructor** | Add a constructor param with the old value as default | `def __init__(self, db=None): self.db = db or PostgresClient(...)` |
| **Parameterize Method** | Same for a method | `def run(self, now=None): now = now or time.time()` |
| **Extract and Override Call** | Move the hard call into a method; subclass it in the test | `def _send(self, msg): smtp.send(msg)` → `class TestableX(X): def _send(self, msg): self.sent.append(msg)` |
| **Extract Interface** | Define a Protocol with just the used methods; depend on that | Real class unchanged; fake implements the Protocol |
| **Adapt Parameter** | Wrap an awkward parameter type (e.g. a framework request) in a thin interface | `RequestLike` with `.args`, `.json` |
| **Introduce Static Setter** | Last resort for singletons: a test-only way to replace the instance | `Config._instance = FakeConfig()` |

### Adding new code into untested code: sprout and wrap

**Sprout Method / Sprout Class:** write the new logic as a *new*, fully tested function
or class, and call it from the legacy code with a one-line change.

```python
def legacy_process_orders(orders):        # 400 untested lines
    ...
    eligible = select_loyalty_eligible(orders, today())   # ← the only edit: one call
    ...

def select_loyalty_eligible(orders, today):               # new, pure, fully tested
    return [o for o in orders if o.total >= 100_00 and (today - o.placed).days <= 30]
```

**Wrap Method / Wrap Class:** rename the old method, create a new method with the old
name that calls the old one plus the new behaviour (Decorator).

```python
class Payroll:
    def pay(self, employee):                # new wrapper, same name callers use
        self._pay_legacy(employee)
        self._audit.record(employee.id)     # new behaviour, tested separately

    def _pay_legacy(self, employee):        # the untouched original
        ...
```

Both keep new code clean and testable without first rewriting the old code.

---

## 8 · Large-scale change: strangler fig, branch by abstraction, flags

### Don't rewrite from scratch

Big-bang rewrites fail predictably: the old system keeps changing, the new one must
re-discover years of undocumented edge cases, and nothing ships until everything ships.
Replace **incrementally**, keeping the system releasable at every step.

### Strangler fig

```
 Phase 1                      Phase 2                        Phase 3
 ┌─────────┐                  ┌─────────┐                    ┌─────────┐
 │ facade  │                  │ facade  │                    │ facade  │
 └────┬────┘                  └──┬───┬──┘                    └────┬────┘
      ▼                          ▼   ▼                            ▼
 ┌─────────┐               ┌───────┐ ┌─────┐                  ┌─────┐
 │ legacy  │               │legacy │ │ new │  /invoices → new │ new │
 └─────────┘               └───────┘ └─────┘                  └─────┘
```

Put a routing facade in front (a proxy, <abbr title="Application Programming Interface">API</abbr> gateway, or an in-code interface), move one
capability at a time to the new implementation, and retire the legacy piece when it
receives no traffic.

### Branch by abstraction (inside one codebase)

1. Introduce an interface in front of the component to replace; switch all callers to it.
2. Build the new implementation behind the interface, merged to main continuously
   (disabled).
3. Switch over gradually with a flag (per request, per tenant, percentage).
4. Delete the old implementation and, if it no longer earns its keep, the flag.

This is how Google-scale codebases do migrations without long-lived branches.

### Verifying the new implementation

- **Dark launch / shadow traffic:** run new alongside old on real input; compare outputs;
  serve old. (GitHub's `Scientist` library formalised this.)
- **Parallel run for data:** dual-write, backfill, compare, then switch reads.
- **Feature flags with a kill switch** and gradual ramp, watching error rates and
  latency.
- **Flags are debt:** give each an owner and removal date; stale flags multiply code paths.

---

## 9 · Technical debt as a design decision

Ward Cunningham's metaphor: shipping imperfect design is like borrowing — useful if you
repay, ruinous if the interest compounds.

Martin Fowler's **debt quadrant**:

|  | Reckless | Prudent |
|---|---|---|
| **Deliberate** | "We don't have time for design." | "We must ship now and will deal with the consequences." |
| **Inadvertent** | "What's layering?" | "Now we know how we should have done it." |

Senior behaviour:

- **Take debt deliberately and write it down** (ticket, `TODO(owner, date, link)`, design
  doc section), with the trigger for repaying it.
- **Prioritise by interest, not principal:** debt in a hotspot you change weekly costs
  far more than ugly code nobody touches. Use churn × complexity (`03` §13).
- **Repay continuously** — boy-scout rule, preparatory refactoring before features in
  that area — rather than "refactoring sprints" that never get scheduled.
- **Make the cost visible in business terms:** "every change to billing takes 3 days and
  has caused 4 incidents this quarter" gets prioritised; "the code is messy" doesn't.

---

## 10 · Code review as design review

Most design happens in code review. What to look at, in priority order:

1. **Design & fit:** Does this belong here? Does it respect module boundaries and the
   dependency direction? Is there a simpler design?
2. **Correctness:** edge cases, error paths, concurrency, resource cleanup.
3. **Interface:** names, signatures, error contracts, backwards compatibility.
4. **Tests:** do they test behaviour, cover the edge cases, and would they catch a
   regression?
5. **Readability:** will the next person understand it without the author?
6. **Style:** leave to linters and formatters.

Good review comments are **specific, explain why, and distinguish must-fix from
preference** ("nit:", "optional:"). Ask questions rather than issue verdicts. Keep
changes small — reviewers find design problems in a 200-line change; they rubber-stamp a
2,000-line one. Google's guidance is to approve a change once it **definitely improves
overall code health**, even if it isn't perfect.

---

## 11 · Interview questions and model answers

**Q: How do you make code testable?**
Inject dependencies instead of creating them, make time/randomness/IDs inputs, separate
pure logic from I/O, avoid global state, and give units small public interfaces with
observable outputs. If a test is painful, that's design feedback.

**Q: Mocks vs. fakes vs. stubs?**
A stub returns canned data to control inputs; a spy records calls; a mock carries
expectations and verifies interactions; a fake is a working lightweight implementation.
I prefer fakes with contract tests for things like repositories and clocks, because mocks
couple tests to implementation; I use mocks when the interaction itself is the behaviour.

**Q: How would you safely refactor a 2,000-line untested class?**
Add characterization tests at the class's public boundary first (golden master if the
output is big), break the minimum dependencies needed to run it in a test (parameterize
constructor, extract interface), then refactor in small verified steps — extracting
cohesive classes along the lines of change. New behaviour goes in sprouted, fully tested
code. No big-bang rewrite.

**Q: Rewrite or refactor?**
Almost always refactor incrementally: strangler fig or branch by abstraction, releasable
at every step, validated with shadow traffic. A rewrite is only defensible when the
platform itself is dead (unsupported language/runtime) and even then it should be
incremental by capability.

**Q: How do you handle technical debt?**
Take it deliberately and record it with a repay trigger; prioritise by interest (hotspots
you change often); repay continuously alongside feature work; and explain its cost in
delivery speed and incidents.

**Q: What do you look for in code review?**
Design and boundaries first, then correctness and error handling, then interface and
compatibility, then tests, then readability; style is for tools. Comments are specific,
give reasons, and label nits.

---

## 12 · Checklist

**Testability**
- [ ] Every collaborator with I/O, time, or randomness is injected.
- [ ] Core logic can be tested with small tests and no mocking framework.
- [ ] Fakes exist for repositories/clocks/queues and pass the same contract tests as the real ones.
- [ ] Tests assert behaviour through public interfaces, not private state or call counts.
- [ ] No test depends on order, wall-clock time, sleeps, or the network.

**Refactoring**
- [ ] Structural and behavioural changes are in separate commits.
- [ ] Each step is small, tested, and revertible.
- [ ] I refactor toward the next feature, not for its own sake.

**Legacy and migration**
- [ ] Characterization tests pin behaviour before changes.
- [ ] New logic is sprouted or wrapped, not buried in the legacy method.
- [ ] Replacements go behind an abstraction/facade with a flag, shadow-verified, then the old path is deleted.
- [ ] Every feature flag has an owner and a removal plan.
