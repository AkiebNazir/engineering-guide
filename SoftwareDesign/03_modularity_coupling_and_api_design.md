# Modularity, Coupling, and Code-Level API Design

> "The first rule of distributed objects: don't distribute your objects."
> — Martin Fowler. The first rule of modules: know what each one is hiding.

`02_oop_and_domain_modeling.md` works at the scale of classes. This file works one level
up — **packages, modules, libraries, and the interfaces between them** — and covers the
design of APIs that other code calls: function signatures, error contracts, versioning,
and evolution without breaking callers.

This is the material behind interview questions like *"How would you structure this
codebase?"*, *"How do you know if two modules are too coupled?"*, *"How would you change
this function's signature used by 200 call sites?"*, and the "extensibility" follow-ups
in every LLD round.

**Already covered elsewhere — not repeated here:**

| Topic | Where |
|---|---|
| Deep modules, information hiding, pass-through layers | `01_philosophy_of_software_design.md` §3–§6 |
| Layered, hexagonal, clean architecture diagrams | `SystemDesign/best_practices/05_architectural_patterns.md` |
| <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>/<abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr>/<abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> wire-level <abbr title="Application Programming Interface">API</abbr> design | `SystemDesign/building_blocks/03_api_design_high_level.md`, `SystemDesign/building_blocks/04_api_design_low_level.md` |
| Service-level <abbr title="Application Programming Interface">API</abbr> evolution, sagas | `CSFundamentals/04_software_engineering_deep_dive.md` §3–§4 |
| Error taxonomy code | `PyEngineering/17_error_taxonomy`, `GoEngineering/17_error_taxonomy` |
| Monorepos and packaging | `PyEngineering/30_packaging_distribution_monorepos` |

---

## Contents

1. [Coupling: the kinds, from worst to best](#1--coupling-the-kinds-from-worst-to-best)
2. [Cohesion: the kinds, from worst to best](#2--cohesion-the-kinds-from-worst-to-best)
3. [Connascence: a sharper vocabulary for coupling](#3--connascence-a-sharper-vocabulary-for-coupling)
4. [Dependency direction and the stable-abstractions rule](#4--dependency-direction-and-the-stable-abstractions-rule)
5. [Package principles: what goes together](#5--package-principles-what-goes-together)
6. [Structuring a codebase](#6--structuring-a-codebase)
7. [Designing function and method signatures](#7--designing-function-and-method-signatures)
8. [Error contracts](#8--error-contracts)
9. [Designing library APIs people can't misuse](#9--designing-library-apis-people-cant-misuse)
10. [Evolving an API without breaking callers](#10--evolving-an-api-without-breaking-callers)
11. [Configuration and extension points](#11--configuration-and-extension-points)
12. [Modular monolith → services: where the seams go](#12--modular-monolith--services-where-the-seams-go)
13. [Measuring design health](#13--measuring-design-health)
14. [Interview questions and model answers](#14--interview-questions-and-model-answers)
15. [Checklist](#15--checklist)

---

## 1 · Coupling: the kinds, from worst to best

**Coupling** is the degree to which a change in one module forces a change in another.
You can't eliminate it — modules that don't talk to each other aren't a system. The goal
is the *weakest kind that works*, pointing in the *right direction*.

The classic structured-design scale (Myers, Constantine), adapted to modern code:

| Kind | What it looks like | Why it hurts |
|---|---|---|
| **Content** (worst) | A reaches into B's private fields, monkey-patches B, depends on B's internal ordering | Any internal change in B breaks A |
| **Common / global** | Both read and write a global, a singleton, a shared mutable config dict, the same DB table | No single owner; a write anywhere can break a read anywhere; tests interfere |
| **External** | Both depend on the same external format/protocol they don't own (a CSV layout, a vendor payload shape) | A third party's change breaks both at once |
| **Control** | A passes a flag telling B *how* to work: `process(data, mode="fast_no_validate")` | A must know B's internals; B does two jobs |
| **Stamp** | A passes a whole big record when B needs two fields | B is coupled to fields it doesn't use; hard to call in tests |
| **Data** | A passes exactly the primitive/value data B needs | Minimal and explicit |
| **Message** (best) | A sends an event/message; B's identity isn't even known to A | Only the message schema is shared |

```python
# CONTROL COUPLING: the caller decides B's algorithm through a flag.
def export(rows, fmt: str, include_header: bool, excel_compat: bool): ...

# DATA COUPLING: separate operations; each takes what it needs.
def to_csv(rows, *, header: bool = True) -> str: ...
def to_excel_csv(rows) -> bytes: ...          # BOM + CRLF live here, once
```

```python
# STAMP COUPLING: to test shipping_cost you need a whole Order, Customer, Cart...
def shipping_cost(order: "Order") -> int:
    return rate(order.customer.address.country, order.cart.total_weight_g)

# DATA COUPLING: callable from anywhere, trivially testable.
def shipping_cost(country: str, weight_g: int) -> int:
    return rate(country, weight_g)
```

Stamp coupling isn't always wrong — passing a value object like `Address` is better than
five loose strings. The smell is passing a *large mutable entity* to use one field.

```python
# MESSAGE COUPLING: A doesn't know B exists — only the event's shape is shared.
class OrderPlaced:
    def __init__(self, order_id: str) -> None:
        self.order_id = order_id

def place_order(order_id: str, publish) -> None:
    publish(OrderPlaced(order_id))          # publish() is a callback/bus; A never imports B

def send_confirmation_email(event: OrderPlaced) -> None:
    print(f"emailing about {event.order_id}")

# wiring happens elsewhere, e.g.: bus.subscribe(OrderPlaced, send_confirmation_email)
```

### Temporal coupling

Also important and often missed: **A must be called before B, but nothing enforces it.**

```python
conn = Connection()
conn.configure(host)    # forget this and connect() fails at runtime, far away
conn.connect()

# Fix: make the valid order the only possible order.
conn = Connection.open(host)      # constructor/factory does both
```

---

## 2 · Cohesion: the kinds, from worst to best

**Cohesion** is how strongly the contents of a module belong together. High cohesion +
low coupling is the target; they reinforce each other, because putting related things
together is what stops them needing to reach across boundaries.

| Kind | The module's contents are grouped because… | Example |
|---|---|---|
| **Coincidental** (worst) | …no reason | `utils.py`, `helpers/`, `common/` |
| **Logical** | …they're the same *category* of thing | `validators.py` holding email, IBAN, and password validators used by unrelated features |
| **Temporal** | …they run at the same time | `startup.py` that loads config, warms caches, seeds DB, registers metrics |
| **Procedural** | …they're steps in one sequence | `checkout_step1..5` |
| **Communicational** | …they operate on the same data | Everything that reads the `orders` table |
| **Sequential** | …the output of one is the input to the next | A parse → normalize → enrich pipeline |
| **Functional** (best) | …together they do one well-defined job, and nothing else | `money/` package: `Money`, `allocate`, currency rules, rounding |

### The `utils` graveyard

`utils.py` starts with two functions and becomes the most imported, least owned file in
the repo, with every package depending on it and it depending on half of them. Rules:

- A helper used by **one** module lives in that module (private).
- A helper used by **several** modules belongs to a *named concept*: `money.round_half_even`,
  `textnorm.fold_case` — not `utils.round2`.
- If you can't name the concept, it probably isn't one; duplicate the three lines.

### Package by feature, not by layer

```
BY LAYER (low cohesion per directory)       BY FEATURE (high cohesion per directory)

app/                                        app/
  controllers/                                orders/
    order_controller.py                         api.py         ← HTTP handlers
    payment_controller.py                       service.py     ← use cases
    user_controller.py                          domain.py      ← Order, invariants
  services/                                     repository.py  ← persistence
    order_service.py                          payments/
    payment_service.py                          api.py  service.py  domain.py  gateway.py
  repositories/                               users/
    order_repository.py                         ...
    ...                                       platform/        ← genuinely shared infra
                                                db.py  http.py  clock.py
```

A feature change in the by-layer layout touches three directories and every directory
contains unrelated features. By feature, a change usually stays inside one directory,
and the package boundary can enforce that `payments` never imports `orders.domain`
internals. Layers still exist — *inside* each feature.

---

## 3 · Connascence: a sharper vocabulary for coupling

**Connascence** (Meilir Page-Jones) — two pieces of code are connascent if changing one
requires changing the other to keep the system correct. Its value is that it gives
coupling *names*, ranks them, and tells you which way to refactor.

### Static (visible in source), weakest to strongest

| Kind | Two places must agree on… | Example | Refactor toward weaker |
|---|---|---|---|
| **Name** | a name | calling `send_email` | (weakest; unavoidable) |
| **Type** | a type | `f(x: Money)` | fine |
| **Meaning** | what a value *means* | `status == 3` means "shipped" in both places | named constant / `Enum` → CoN |
| **Position** | argument order | `transfer(a, b, 100)` — which is from? | keyword-only args / value objects → CoN |
| **Algorithm** | the same algorithm | client and server both compute the same checksum/hash/encoding by hand | one shared function → CoN |

### Dynamic (only visible at runtime), stronger still

| Kind | Must agree on… | Example |
|---|---|---|
| **Execution order** | call order | `configure()` before `connect()` (temporal coupling, §1) |
| **Timing** | when things happen | a test that `sleep(0.1)`s for a background thread; a cache TTL racing a writer |
| **Value** | related values changing together | `start` and `end`, or the retry count in client and server config |
| **Identity** | the *same object instance* | two components must share one lock/registry instance |

**Three rules:**

1. **Degree** — connascence across many places is worse than across two.
2. **Locality** — strong connascence *inside* one function or class is fine; the same
   connascence across a package or service boundary is dangerous. **Strength should
   decrease as distance increases.**
3. **Refactor strong → weak.** Meaning → Name (enums), Position → Name (keyword args),
   Algorithm → Name (one shared function), Execution order → Type (factories, typestate).

```python
# Connascence of Position + Meaning, across a module boundary:
book(room_id, 20260917, 3, True)

# Connascence of Name + Type only:
book(room_id, stay=DateRange(date(2026, 9, 17), nights=3), breakfast=Breakfast.INCLUDED)
```

---

## 4 · Dependency direction and the stable-abstractions rule

Coupling kind is one axis; **direction** is the other. The rule that organises every
good architecture (hexagonal, clean, onion):

> **Depend in the direction of stability.** Things that change often should depend on
> things that change rarely — never the reverse.

```
   volatile ─────────────────────────────────────────▶ stable

   HTTP handlers      Use cases /           Domain model        Interfaces the
   CLI, DB adapters   application services  (entities, rules)   domain defines
   vendor SDK glue                                              (ports)

   changes weekly     changes with features changes with the    changes rarely
                                            business
```

The problem: domain logic often *needs* volatile things (a database, an email sender).
**Dependency inversion** flips the source-code arrow while leaving the runtime call
direction unchanged:

```
 WITHOUT INVERSION                          WITH INVERSION

 ┌────────────┐     imports    ┌────────┐   ┌────────────┐  defines  ┌─────────────────┐
 │  Billing   │ ──────────────▶│ Stripe │   │  Billing   │ ────────▶ │ «port»          │
 │  (policy)  │                │  SDK   │   │  (policy)  │           │ PaymentGateway  │
 └────────────┘                └────────┘   └────────────┘           └────────▲────────┘
                                                                              │ implements
   policy changes whenever the vendor does                           ┌────────┴────────┐
                                                                     │ StripeAdapter   │
                                                                     └─────────────────┘
                                             the vendor-specific code depends on the policy
```

### Martin's package metrics (useful vocabulary, not a scoreboard)

For a package: **Ce** = efferent (outgoing) dependencies, **Ca** = afferent (incoming).

- **Instability** `I = Ce / (Ca + Ce)` — 0 means everything depends on it and it depends
  on nothing (hard to change); 1 means nothing depends on it (free to change).
- **Abstractness** `A` = abstract types / total types.
- **Stable Dependencies Principle:** depend toward lower `I`.
- **Stable Abstractions Principle:** stable packages should be abstract (so they can be
  extended without modification); unstable packages concrete.
- **Main sequence:** `A + I ≈ 1`. The two failure corners:
  - **Zone of pain** (`A≈0, I≈0`): concrete *and* depended on by everything — e.g. a
    shared `models.py` with concrete <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> classes all features import. Every change hurts.
    (Genuinely stable concrete things like the stdlib are fine here — they don't change.)
  - **Zone of uselessness** (`A≈1, I≈1`): abstract interfaces nobody uses.

### Acyclic Dependencies Principle

**No cycles between packages.** A cycle `orders → payments → orders` means the two
packages are really one: you can't build, test, release, or reason about either alone.
Go refuses to compile import cycles; Python allows them and fails at import time in
confusing ways (partially initialised modules). Break a cycle by:

1. **Dependency inversion** — the lower package defines an interface the upper implements.
2. **Extract the shared piece** into a third package both depend on.
3. **Events** — `orders` publishes `OrderPaid`; `payments` doesn't import `orders`.
4. **Merge** — if they always change together, they were one package.

---

## 5 · Package principles: what goes together

From Robert Martin's component principles. Three about **cohesion**, which pull against
each other:

| Principle | Rule | Pulls toward |
|---|---|---|
| **REP** Reuse/Release Equivalence | What you release together, you version together; a reusable package is a coherent releasable unit | Larger, documented units |
| **CCP** Common Closure | Group things that **change for the same reason at the same time** (SRP for packages) | Grouping by feature |
| **CRP** Common Reuse | Don't force users to depend on things they don't use (ISP for packages) | Smaller packages |

Early in a project, favour **CCP** (changes stay local, so iteration is fast). As a
package becomes a shared library used by many teams, **REP/CRP** grow in importance.

### Go-specific package design

- **Name packages for what they provide, not what they contain:** `package http`, not
  `package httputils`. Callers read `http.Get`, `json.Marshal` — the package name is part
  of every identifier, so avoid stutter: `user.User` → `user.Account` or keep it but
  never `user.UserService`.
- **`internal/`** directories are import-restricted by the compiler to the parent tree —
  a real, enforced module boundary. Use it.
- **Small interfaces live with consumers** (see `02` §5); don't create a `interfaces`
  package.
- **No `models`, `types`, `common`, `util` packages** — they become the zone of pain.

### Python-specific

- `_private` names and `__all__` are conventions, not enforcement. Enforce boundaries with
  a tool: **import-linter** contracts (e.g. "`orders.domain` may not import
  `orders.api`"; "`payments` and `orders` are independent") in <abbr title="Continuous Integration. The practice of merging all developers' working copies to a shared mainline several times a day.">CI</abbr>.
- Keep `__init__.py` light; heavy imports there create cycles and slow startup.
- Import cycles typically surface as `ImportError: cannot import name X (most likely due
  to a circular import)`. Fixing with a function-local import hides the design problem.

---

## 6 · Structuring a codebase

A layout that scales from one service to a large codebase, in either language:

```
service/
  cmd/ or __main__.py        composition root: read config, construct everything, wire, run
  <feature_a>/
    domain                   entities, value objects, policies — imports nothing internal but stdlib
    app (service/usecases)   orchestrates domain + ports; defines port interfaces
    adapters                 http handlers, db repositories, queue consumers, vendor clients
  <feature_b>/ ...
  platform/                  cross-cutting infra: logging, metrics, db pool, clock, ids
```

The **dependency rule** inside a feature: `adapters → app → domain`. `domain` never
imports `adapters`. The **composition root** is the only place that knows every concrete
type — it constructs `PostgresOrderRepo` and hands it to `OrderService` as an
`OrderRepository`.

Worked, runnable versions of this exist: `PyEngineering/18_dependency_injection_layering`,
`PyEngineering/25_production_service_capstone`, and the Go equivalents.

### How big should a module be?

There's no line count. Use these tests instead:

- Can you state its responsibility in one sentence without "and"?
- Is the interface much smaller than the implementation (`01` §3)?
- When a typical feature changes, does it change **one** module rather than five
  (shotgun surgery) — and does it avoid changing a module shared with unrelated features
  (divergent change)?
- Could a new engineer own it without learning the rest of the system?

---

## 7 · Designing function and method signatures

A signature is the smallest <abbr title="Application Programming Interface">API</abbr> you design, and you design hundreds a week.

### Parameters

```python
# BAD: positional booleans and primitives — connascence of position and meaning.
def create_user(name, email, True, False, 3): ...

# GOOD: required essentials positional; options keyword-only with safe defaults.
def create_user(name: str, email: Email, *, admin: bool = False,
                send_welcome: bool = True, max_sessions: int = 3) -> User: ...
```

Rules of thumb:

1. **Required things positional (≤ 3), optional things keyword-only** (`*` in Python,
   an options struct or functional options in Go).
2. **Accept the most general type you need** (`Iterable[T]`, `io.Reader`, `Mapping`),
   **return the most specific useful type** (`list[T]`, `*os.File`). (Postel's law applied
   to types; Go's "accept interfaces, return structs".)
3. **No mutable default arguments** in Python (`def f(x=[])` shares one list across calls).
4. **Don't take ownership silently.** If you keep a reference to a passed-in list, copy
   it or document it — the caller may mutate it later.
5. **Group parameters that travel together** into a value object (`DateRange`,
   `Pagination`) — this also removes connascence of value between them.
6. **A boolean parameter often means two functions** (`01` §10).

Rule 4, in code — the bug is invisible at the call site:

```python
class Roster:
    def __init__(self, names: list[str]) -> None:
        self.names = names                 # aliases the caller's list, doesn't copy it

source = ["Ann", "Bo"]
roster = Roster(source)
source.append("Cy")                        # roster.names silently has 3 names too

# Fix: copy on the way in, or document that ownership transfers.
class Roster:
    def __init__(self, names: list[str]) -> None:
        self.names = list(names)           # defensive copy — caller's list is now independent
```

### Go: options structs vs. functional options

```go
// Options struct: simple, discoverable, zero value = defaults.
type ServerOptions struct {
	ReadTimeout  time.Duration // 0 means 30s
	MaxBodyBytes int64         // 0 means 1 MiB
}
func NewServer(addr string, opts ServerOptions) *Server

// Functional options: extensible without breaking callers, good for libraries.
type Option func(*config)
func WithReadTimeout(d time.Duration) Option { return func(c *config) { c.readTimeout = d } }
func NewClient(addr string, opts ...Option) *Client
```

Prefer the options struct for application code; reach for functional options in public
libraries where you'll add many options over years and want validation per option.

### Return values

- **Return a result, not an out-parameter.** Mutating arguments to return data couples
  the caller to your mutation.
- **Don't return `None`/`nil` to mean three different things** ("not found", "error",
  "empty"). Distinguish: `Optional[T]` for absent, an exception/error for failure, an
  empty collection for empty.
- **Return empty collections, not `None`.** Callers can always iterate.
- **Go:** return `(T, error)`; `(T, bool)` for "found?" (the comma-ok idiom).

### Command-query separation

A method either **changes state** (command, returns nothing or an ID) or **answers a
question** (query, no side effects) — not both. `stack.pop()` is the accepted pragmatic
exception. A `get_user()` that also updates `last_seen` will one day be called in a loop
by someone who didn't know.

```python
# VIOLATION: looks like a query; a side effect is hidden inside a "getter".
def get_user(user_id: str, db) -> "User":
    user = db.load(user_id)
    user.last_seen = now()
    db.save(user)
    return user

# FIXED: split the query from the command. Callers opt into the side effect.
def get_user(user_id: str, db) -> "User":
    return db.load(user_id)

def record_seen(user_id: str, db) -> None:
    user = db.load(user_id)
    user.last_seen = now()
    db.save(user)
```

---

## 8 · Error contracts

An error is part of the <abbr title="Application Programming Interface">API</abbr>. Design it as carefully as the success path.

### Decide what callers can do about it

Every error you expose should map to a caller **action**. Classify by action, not by
where it came from:

| Category | Caller should… | Python | Go | <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> analogue |
|---|---|---|---|---|
| Invalid input | fix the request; don't retry | `ValueError` subclass | sentinel / typed error | 400 / 422 |
| Not found | handle absence | `KeyError` subclass or `Optional` | `ErrNotFound` | 404 |
| Conflict / precondition | re-read and decide | `ConflictError` | `ErrConflict` | 409 / 412 |
| Transient | retry with backoff | `TransientError` | error with `Temporary()`/`errors.Is(err, ErrUnavailable)` | 503 / 429 |
| Bug / invariant broken | crash loudly, alert | `AssertionError`, let it propagate | `panic` (rarely) | 500 |

```python
class DomainError(Exception):
    """Base for errors callers are expected to handle."""

class NotFound(DomainError): ...
class Conflict(DomainError): ...
class Transient(DomainError):
    retry_after_s: float | None = None
```

```go
var ErrNotFound = errors.New("not found")

type ConflictError struct{ Current int64 }
func (e *ConflictError) Error() string { return fmt.Sprintf("conflict: current version %d", e.Current) }

// Callers: errors.Is(err, ErrNotFound); var ce *ConflictError; errors.As(err, &ce)
// Wrap with context, preserving the chain: fmt.Errorf("load order %s: %w", id, err)
```

### Rules

1. **Don't leak implementation errors across a boundary.** A repository that raises
   `psycopg.errors.UniqueViolation` couples every caller to Postgres. Translate to
   `Conflict` at the adapter. (But keep the cause: `raise Conflict(...) from e`.)
2. **Wrap with context, don't replace.** `%w` in Go, `raise ... from e` in Python.
3. **`%w` makes an error part of your <abbr title="Application Programming Interface">API</abbr>.** In Go, wrapping with `%w` lets callers
   `errors.Is` against the inner error — so you can never change that inner error
   without breaking them. Use `%v` when the cause is an implementation detail.
4. **Don't use exceptions for expected control flow** in hot paths, and don't use
   `bool` returns for failures a caller must not ignore.
5. **Define errors out of existence where possible** (`01` §7): idempotent deletes,
   `min(len, n)` slicing, empty-result queries.
6. **Document** which errors each public function can produce. Undocumented errors
   are how LSP violations sneak in (`02` §12).

---

## 9 · Designing library APIs people can't misuse

Joshua Bloch's standard: **"APIs should be easy to use and hard to misuse."** The best
test is to write the calling code *first*.

### Principles

| Principle | Meaning | Example |
|---|---|---|
| **Pit of success** | The easiest thing to write is correct | `with open(...)` closes the file; `subprocess.run([...])` avoids shell injection by default |
| **Common case trivial, rare case possible** | Defaults for 90%, options for 10% | `requests.get(url)` vs. sessions, adapters, retries |
| **Least astonishment** | Behaviour matches the name and platform conventions | `len()` never mutates; `sorted()` returns new, `.sort()` mutates and returns `None` |
| **Symmetry and consistency** | Parallel operations look parallel | `encode`/`decode`, `Marshal`/`Unmarshal`, same argument order everywhere |
| **Fail fast** | Reject misuse at the call, not three layers later | Validate in constructor; `ValueError` on bad args immediately |
| **Minimise surface** | Every public name is a forever promise | When in doubt, leave it out — you can add, you can't remove |
| **Make wrong code look wrong** | Types that don't mix | `UserId` vs `OrderId` NewTypes; `Duration` instead of `int` seconds |
| **No surprising side effects** | Importing a module doesn't open connections | Lazy init; explicit `connect()` or factory |

### Units and types

```python
# Classic misuse: is it seconds or milliseconds?
cache.set(key, value, 300)

# Unmisusable: the type carries the unit.
from datetime import timedelta
cache.set(key, value, ttl=timedelta(minutes=5))
```

Go does this in the standard library: `time.Sleep(5 * time.Second)`.
`time.Sleep(5)` compiles, but sleeps 5 *nanoseconds* — which is exactly why the typed
`time.Duration` constants exist and why linters flag untyped constants there.

### Resources and lifecycles

- Anything that must be released → context manager (`__enter__/__exit__`) in Python,
  `Close()` + `defer` in Go, and document whether `Close` is idempotent (make it so).
- Anything with background goroutines/threads → an explicit `Stop()`/`close()` that
  waits for them. A library that leaks goroutines is a library people stop using.

```python
class TempWorkspace:
    def __enter__(self) -> "TempWorkspace":
        self._dir = make_temp_dir()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        remove_dir(self._dir)              # always runs, even if the block raised

with TempWorkspace() as ws:
    do_work(ws)
# the directory is gone here, whether do_work() succeeded or raised — the pit of success
```

### Thread safety is part of the contract

State it in the doc: *"Safe for concurrent use by multiple goroutines"* (like
`http.Client`) or *"Not thread-safe; use one per thread"*. Undocumented thread safety
means callers either over-lock or race.

---

## 10 · Evolving an <abbr title="Application Programming Interface">API</abbr> without breaking callers

Once code is published — to other teams, other services, or the public — its
**observable behaviour** is the contract, not just its signature.

> **Hyrum's Law:** "With a sufficient number of users of an <abbr title="Application Programming Interface">API</abbr>, it does not matter what
> you promise in the contract: all observable behaviors of your system will be depended
> on by somebody."

Iteration order, error message text, timing, the exact float formatting — someone
depends on it. Google's response is to **randomise what isn't promised** (Go randomises
map iteration order; Abseil's hash tables randomise hashing per process) so nobody can
accidentally depend on it.

### Compatible vs. breaking changes (code APIs)

| Usually safe (additive) | Breaking |
|---|---|
| Add a new function/type/module | Remove or rename anything public |
| Add an optional keyword parameter with a default | Add a required parameter; reorder positional parameters |
| Add a field to a returned struct/dataclass (if callers don't construct/unpack it positionally) | Change a return type, or `None` → exception, or vice versa |
| Add a method to a concrete type | **Add a method to an interface/Protocol** (every implementer breaks) |
| Widen accepted input | Narrow accepted input; tighten validation |
| Narrow possible output | Widen output (new enum value callers `match` exhaustively on; new exception type) |
| Performance improvements | Performance regressions callers relied on (Hyrum) |

The subtle ones interviewers like:
- **Adding a method to an interface breaks implementers**, not callers. Go's workaround:
  define a *new* interface and check with a type assertion (`if f, ok := w.(Flusher)`).
- **Adding an enum value** breaks exhaustive `match`/`switch` statements downstream.
- **Positional unpacking** of a returned tuple breaks when you add an element — return a
  dataclass/NamedTuple from day one.

### The safe-change playbook: expand → migrate → contract

```
 1. EXPAND     Add the new thing alongside the old.          new_fn() exists, old_fn() unchanged
               Old delegates to new where possible.
 2. MIGRATE    Move callers. Emit deprecation warnings;       warnings.warn(..., DeprecationWarning,
               measure remaining usage (logs, code search).                 stacklevel=2)
 3. CONTRACT   Remove the old thing when usage is zero        // Deprecated: use NewFn. (Go doc convention)
               (or at a major version).
```

The same three steps apply to database schemas (parallel change /
expand-contract migrations, `PyEngineering/11_migrations_schema_management`), wire
protocols, and config formats. In a monorepo you can often do the migration in one
atomic change with automated refactoring (Google uses large-scale changes, "LSCs");
across repositories or public users you need the deprecation window.

### Semantic versioning, properly

`MAJOR.MINOR.PATCH`: MAJOR breaks, MINOR adds compatibly, PATCH fixes compatibly.
Go makes MAJOR ≥ 2 part of the **import path** (`example.com/lib/v2`) so v1 and v2 can
coexist in one build. Python has no equivalent — two majors can't coexist in one
environment, which is why breaking a popular Python library is so painful.

---

## 11 · Configuration and extension points

Every configuration option and extension point is an <abbr title="Application Programming Interface">API</abbr> with a maintenance cost.

### Configuration

- **Config is for things that vary between deployments** (hosts, credentials, pool
  sizes) — not for business rules that should be code with tests.
- **Parse config once at startup into a typed, validated object**; pass that object (or
  the pieces each module needs) down. Don't read `os.environ` deep inside business logic.
- **Fail at startup on invalid config**, not at the first request that needs it.
- Every option doubles the states to test. Default well; expose little.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    db_host: str
    db_pool_size: int
    request_timeout_s: float

def load_config(env: dict[str, str]) -> AppConfig:
    return AppConfig(
        db_host=env["DB_HOST"],
        db_pool_size=int(env.get("DB_POOL_SIZE", "10")),
        request_timeout_s=float(env.get("REQUEST_TIMEOUT_S", "5.0")),
    )                                        # missing/bad values raise here, at startup
```

### Extension points (plugins, hooks, strategies)

- Add them where the problem **demonstrably** varies (second customer, second vendor) —
  not in anticipation. <abbr title="You Aren't Gonna Need It - A principle of extreme programming that states a programmer should not add functionality until deemed necessary.">YAGNI</abbr> applies (`01` §14).
- Prefer **passing a function or small interface** over a plugin registry.
- If you do need a registry (e.g. discovered at runtime), make registration explicit
  (`register("s3", S3Store)`) rather than import side effects.
- Define the extension's contract: what it may call, which thread it runs on, what
  happens if it raises, whether its output is trusted.

```python
# The smallest extension point: pass a function. No registry, no base class.
def apply_discount(total: float, discount_fn) -> float:
    return discount_fn(total)

def ten_percent_off(total: float) -> float:
    return total * 0.9

apply_discount(100.0, ten_percent_off)      # 90.0 — a new discount is just a new function
```

---

## 12 · Modular monolith → services: where the seams go

A **modular monolith** — one deployable, strictly enforced internal module boundaries —
is the right starting architecture for most products, and the prerequisite for ever
extracting services cleanly. A codebase with poor module boundaries, split into
services, becomes a **distributed monolith**: all the coupling, plus network failures.

```
 MODULAR MONOLITH                            DISTRIBUTED MONOLITH
 one deployable, boundaries enforced         same coupling, split anyway

 ┌───────────────────────────────┐           ┌─────────┐  network  ┌──────────┐
 │  orders │ payments │ catalog  │           │ orders  │─────────▶ │ payments │
 │  (each reachable only         │           └────┬────┘   call    └────┬─────┘
 │   through its own API)        │                │ still reaches   │
 └───────────────────────────────┘                ▼ into catalog's  ▼
     one deploy, one transaction              ┌─────────┐  tables  (the same
                                               │ catalog │◀─────────  coupling —
                                               └─────────┘  now with latency
                                                             and partial failure)
```

Good seams (where a module/service boundary should go):

- **Business capability / bounded context** — payments, catalog, identity.
- **Different rate of change** — the pricing rules team ships daily; the ledger rarely.
- **Different non-functional needs** — the image pipeline needs GPUs and scales
  independently; the admin UI doesn't.
- **Different consistency requirements** — where eventual consistency is acceptable to
  the business, a boundary can exist; where it isn't, keep things together.
- **Team ownership** — **Conway's Law**: systems mirror the communication structure of
  the organisations that build them. Design boundaries that match (or deliberately
  reshape — the "inverse Conway manoeuvre") the teams.

Bad seams: one service per database table or noun (entity services), or splitting along
technical layers (a "validation service").

Migration from monolith: the **strangler fig** pattern — route one capability at a time
to the new implementation behind a stable facade; see
`05_testability_refactoring_and_legacy_code.md` §8.

---

## 13 · Measuring design health

Numbers don't decide design, but they point at where to look.

| Signal | What it suggests | Tooling |
|---|---|---|
| **Change coupling** — files that always change in the same commits but live in different modules | Hidden coupling; boundary in the wrong place | `git log` mining; CodeScene-style analysis |
| **Hotspots** — high churn × high complexity files | Where refactoring pays back most | churn from git + cyclomatic complexity (`radon`, `gocyclo`) |
| **Fan-in / fan-out** per package | Zone of pain candidates (high fan-in + concrete + volatile) | `pydeps`, `go list -deps`, import graphs |
| **Import cycles** | Two packages that are really one | Go compiler; `import-linter` / `pylint cyclic-import` |
| **Cyclomatic / cognitive complexity** per function | Functions hard to test and read | `radon cc`, `gocognit` |
| **Test setup size** | A unit needing 20 lines of fakes is too coupled | code review |
| **Lead time for a typical change** | The ultimate design metric: how fast can you change it safely | DORA metrics |

A quick change-coupling query you can actually run on any repo:

```bash
# Pairs of files most often committed together (last 500 commits).
git log -500 --name-only --pretty=format:'--' \
 | awk '/^--$/{ if (n) for (i=1;i<=n;i++) for (j=i+1;j<=n;j++) print f[i] " | " f[j]; n=0; next }
        NF { f[++n]=$0 }' \
 | sort | uniq -c | sort -rn | head -20
```

---

## 14 · Interview questions and model answers

**Q: What's the difference between coupling and cohesion?**
Coupling is between modules — how much a change in one forces a change in another.
Cohesion is within a module — how strongly its contents belong together. You want low
coupling and high cohesion, and they reinforce each other: grouping things that change
together is what stops them reaching across boundaries.

**Q: How would you break a circular dependency between two packages?**
First ask whether they're really one package (always change together → merge). Otherwise:
invert a dependency (the lower package defines an interface the higher one implements),
extract the shared concept into a third package, or decouple with events.

**Q: Package by layer or by feature?**
By feature at the top level, layers inside each feature. It keeps typical changes inside
one directory and lets the boundary be enforced; package-by-layer spreads every feature
across every directory.

**Q: You need to change a function signature used by 300 call sites across teams.**
Expand–migrate–contract: add the new signature alongside the old (old delegates to new),
deprecate with warnings and measure usage, migrate callers (automated refactoring where
possible, one atomic change if it's a monorepo), remove the old one when usage is zero.
Never a flag day across repositories.

**Q: Which changes to a library are breaking?**
Removing/renaming, adding required params, changing return types or error behaviour,
narrowing accepted inputs, and the subtle ones: adding a method to an interface (breaks
implementers), adding an enum value (breaks exhaustive matches), and — by Hyrum's Law —
any observable behaviour change with enough users.

**Q: How do you design errors for an <abbr title="Application Programming Interface">API</abbr>?**
By what the caller can do: invalid input (don't retry), not found, conflict (re-read),
transient (retry with backoff), and bugs (crash). Translate implementation errors at the
boundary so callers don't depend on your database driver; wrap to keep context and
cause; document them as part of the contract.

**Q: What's Hyrum's Law and what do you do about it?**
All observable behaviour gets depended on. Keep the surface minimal, document what's
promised, and deliberately randomise or vary what isn't (iteration order, hash seeds) so
nobody builds on it.

**Q: When would you split a monolith into services?**
When a boundary is already clean inside the monolith and there's a concrete driver:
independent scaling, a different rate of change or ownership, fault isolation, or a
different tech need. Split by business capability, not by entity or layer; otherwise you
get a distributed monolith.

---

## 15 · Checklist

**Boundaries**
- [ ] Top-level structure is by feature/capability; layers live inside.
- [ ] No import cycles; the dependency rule (`adapters → app → domain`) is enforced by a tool.
- [ ] No `utils`/`common`/`models` dumping grounds.
- [ ] Volatile code depends on stable code; the domain defines the ports.

**Coupling**
- [ ] Modules exchange data/values, not flags that steer internals or whole entities.
- [ ] Strong connascence (meaning, position, algorithm, order) is local; only name/type crosses boundaries.
- [ ] No hidden call-order requirements; factories establish valid state.

**APIs**
- [ ] Required args positional (≤3), options keyword-only / options struct.
- [ ] Units and IDs are types, not raw ints and strings.
- [ ] Every exposed error maps to a caller action and hides the implementation.
- [ ] Thread safety and resource ownership are documented.
- [ ] Return types are dataclasses/structs, not positional tuples, when they might grow.

**Evolution**
- [ ] I know which of my changes are breaking, including interface methods and enum values.
- [ ] Breaking changes go through expand → migrate → contract with usage measured.
