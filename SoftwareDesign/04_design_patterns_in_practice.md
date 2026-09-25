# Design Patterns in Practice

> "Design patterns are bug reports against your programming language." — Peter Norvig
> (paraphrasing his 1996 finding that 16 of the 23 GoF patterns are invisible or simpler
> in dynamic languages with first-class functions).

The **catalog** — a one-line intent for each of the 23 GoF patterns and where this file
treats it — is the table in §1. The everyday patterns get a full section each (§3–§18);
the rarely used ones (Abstract Factory, Prototype, Bridge, Mediator, Memento) are short
subsections inside the section they belong beside.

This file is about **using** patterns well:

- recognising the *problem* that calls for a pattern (you should arrive at a pattern, not
  start from one);
- writing the **idiomatic Python and Go** version, which is often a function, a dict, or
  a generator rather than a class hierarchy;
- the handful of non-GoF patterns that dominate real code and LLD interviews
  (Repository, Unit of Work, Specification, Null Object, Registry, Middleware);
- and knowing when a pattern is making things worse.

---

## Contents

1. [How to think about patterns](#1--how-to-think-about-patterns)
2. [Problem → pattern decision table](#2--problem--pattern-decision-table)
3. [Strategy — usually just a function](#3--strategy--usually-just-a-function)
4. [Factory and Registry](#4--factory-and-registry)
5. [Builder — and why Python rarely needs it](#5--builder--and-why-python-rarely-needs-it)
6. [Singleton — and what to do instead](#6--singleton--and-what-to-do-instead)
7. [Observer / Pub-Sub — the details that bite](#7--observer--pub-sub--the-details-that-bite)
8. [Command — undo, redo, queues, and audit](#8--command--undo-redo-queues-and-audit)
9. [State — when each state behaves differently](#9--state--when-each-state-behaves-differently)
10. [Decorator, Proxy, Adapter, Facade — four wrappers, four intents](#10--decorator-proxy-adapter-facade--four-wrappers-four-intents)
11. [Chain of Responsibility and Middleware](#11--chain-of-responsibility-and-middleware)
12. [Composite and Visitor — trees](#12--composite-and-visitor--trees)
13. [Template Method vs. hooks vs. composition](#13--template-method-vs-hooks-vs-composition)
14. [Iterator — generators and Go's range-over-func](#14--iterator--generators-and-gos-range-over-func)
15. [Specification (filter composition)](#15--specification-filter-composition)
16. [Repository and Unit of Work](#16--repository-and-unit-of-work)
17. [Null Object and Special Case](#17--null-object-and-special-case)
18. [Flyweight and Object Pool](#18--flyweight-and-object-pool)
19. [Pattern overuse — how to recognise it](#19--pattern-overuse--how-to-recognise-it)
20. [Which patterns each LLD problem uses](#20--which-patterns-each-lld-problem-uses)
21. [Interview questions and model answers](#21--interview-questions-and-model-answers)

---

## 1 · How to think about patterns

A pattern is **a named solution to a recurring design problem, with known trade-offs.**
Its value is mostly vocabulary: "put a Strategy there" transmits a design in three words.

Three rules:

1. **Start from the force, not the pattern.** "Pricing rules vary by customer tier and
   change monthly" → something must vary independently of the checkout flow → Strategy.
   Never "I should use Strategy somewhere."
2. **Use the lightest form the language allows.** In Python and Go, functions are values;
   many patterns collapse into passing a function.
3. **Every pattern adds indirection.** Indirection is a cost paid on every read. It must
   buy a concrete, current benefit: a second implementation, a test seam, a real
   extension point.

### The three GoF families in one line each

- **Creational** — control *how objects get made* so callers don't depend on concrete classes.
- **Structural** — *compose objects* into larger structures while keeping interfaces simple.
- **Behavioral** — *distribute responsibility and communication* among objects.

### All 23 GoF patterns at a glance

Use this as the definitions table; the last column says where the pattern is worked.

| Family | Pattern | Intent in one line | Here |
|---|---|---|---|
| Creational | **Abstract Factory** | Create a *family* of related objects that must be used together, without naming concrete classes | §4 |
| | **Builder** | Assemble a complex object step by step, and validate it as a whole at the end | §5 |
| | **Factory Method** | Let a subclass (or a passed-in function) choose which concrete class to create | §4 |
| | **Prototype** | Create a new object by copying a configured instance | §4 |
| | **Singleton** | One instance with global access — usually replaced by injection | §6 |
| Structural | **Adapter** | Convert one interface into the one the client expects | §10 |
| | **Bridge** | Separate an abstraction from its implementation so each varies independently | §10 |
| | **Composite** | Treat a leaf and a group of leaves through one interface | §12 |
| | **Decorator** | Add behaviour by wrapping an object that has the same interface | §10 |
| | **Facade** | One simple interface over a complicated subsystem | §10 |
| | **Flyweight** | Share the immutable part of many fine-grained objects | §18 |
| | **Proxy** | A same-interface stand-in that controls access (lazy, remote, protected, cached) | §10 |
| Behavioral | **Chain of Responsibility** | Pass a request along handlers until one handles it (or each wraps the next) | §11 |
| | **Command** | Turn a request into an object so it can be queued, logged, retried, or undone | §8 |
| | **Interpreter** | Model a small grammar as a tree of nodes that evaluate themselves; rarely hand-written (expression ASTs, `find` filters) | §15 |
| | **Iterator** | Walk a collection without exposing how it is stored | §14 |
| | **Mediator** | Route communication among peers through one object instead of all-to-all references | §7 |
| | **Memento** | Capture and later restore an object's state without breaking its encapsulation | §8 |
| | **Observer** | Notify a changing set of dependents when something happens | §7 |
| | **State** | Change behaviour when internal state changes, one class per state | §9 |
| | **Strategy** | Swap an algorithm behind a common interface | §3 |
| | **Template Method** | Fix an algorithm's skeleton; let subclasses fill in steps | §13 |
| | **Visitor** | Add operations over a stable set of types by double dispatch | §12 |

---

## 2 · Problem → pattern decision table

| You notice… | Consider | Lightest idiomatic form |
|---|---|---|
| An algorithm/rule varies and should be swappable | **Strategy** | Pass a function / `Callable` / Go func type |
| A `switch` on a type string to construct objects, repeated | **Factory** + **Registry** | `dict[str, Callable[..., T]]` |
| A constructor with 8 optional parameters | **Builder** | Python: keyword args + dataclass; Go: options struct / functional options |
| "There must be exactly one" | **Singleton** — but usually **dependency injection** | Module-level instance created in the composition root |
| Many parties react to something happening | **Observer** / pub-sub | List of callbacks; an event bus for cross-module |
| Operations must be undoable, queued, logged, or retried | **Command** | Dataclass with `execute`/`undo`, or a (do, undo) function pair |
| An object's behaviour changes completely by state | **State** | Enum + table if behaviour is similar; state classes if it differs |
| Add behaviour (logging, caching, retry) without touching a class | **Decorator** | Python decorator on functions; wrapper struct implementing the same interface in Go |
| Control access to an object (lazy, remote, cached, permission-checked) | **Proxy** | Same-interface wrapper |
| A third-party interface doesn't match what your code expects | **Adapter** | Small wrapper class/function at the boundary |
| A subsystem is complicated to use | **Facade** | One class/function with the common-case operations |
| A request passes through a sequence of optional handlers | **Chain of Responsibility** / **Middleware** | List of functions, each calling `next` |
| Part–whole trees treated uniformly | **Composite** | Recursive dataclass / interface with children |
| Many operations over a fixed tree of types | **Visitor** | `match` statement (Python 3.10+), type switch (Go) |
| Algorithm skeleton fixed, steps vary | **Template Method** | Higher-order function taking the steps |
| Traverse a collection without exposing its structure | **Iterator** | Generator (`yield`); Go 1.23 `iter.Seq` |
| Combinable filtering rules (`size > 5MB and ext == .xml`) | **Specification** | Predicate functions combined with `and_`/`or_` |
| Domain code shouldn't know about the database | **Repository** | Protocol with `get/add/list`; in-memory fake for tests |
| Several changes must commit or roll back together | **Unit of Work** | Context manager wrapping a transaction |
| `if x is None:` checks everywhere | **Null Object** | A do-nothing implementation of the interface |
| Millions of objects sharing identical intrinsic state | **Flyweight** | Interning / cache by key; `__slots__` |
| Objects are expensive to create and reusable | **Object Pool** | `queue.Queue` of instances; Go `sync.Pool` (for <abbr title="Garbage Collection. A form of automatic memory management that attempts to reclaim garbage, or memory occupied by objects that are no longer in use by the program.">GC</abbr> pressure, not connections) |

---

## 3 · Strategy — usually just a function

**Force:** a behaviour varies independently of the code that uses it.

```arch
%% caption: The Context delegates to an abstract Strategy interface, and the exact algorithm is injected at runtime.
node ctx "Context\n(ParkingLot)" at 0,0 icon=app color=blue
node iface "IPricingRule" at 2,0 icon=code color=amber style=dashed
group strat "Concrete Strategies" color=green style=solid
node s1 "HourlyPricing" at 4,-1 in strat icon=function
node s2 "FlatPricing" at 4,1 in strat icon=function

ctx -> iface : "delegates to"
iface ..> s1 : "implements"
iface ..> s2 : "implements"
```


```python
from typing import Callable, Protocol

# Lightest form: the strategy is a function.
PricingRule = Callable[[int], int]          # minutes parked -> price in cents

def hourly(rate_cents: int) -> PricingRule:
    return lambda minutes: -(-minutes // 60) * rate_cents     # ceil to whole hours

def flat(cents: int) -> PricingRule:
    return lambda minutes: cents

def first_hour_free(inner: PricingRule) -> PricingRule:       # strategies compose
    return lambda minutes: 0 if minutes <= 60 else inner(minutes)

class ParkingLot:
    def __init__(self, pricing: PricingRule) -> None:
        self._pricing = pricing

    def charge(self, minutes: int) -> int:
        return self._pricing(minutes)

lot = ParkingLot(first_hour_free(hourly(250)))
assert lot.charge(30) == 0 and lot.charge(61) == 500
```

**Use a Protocol/class instead of a function when** the strategy has several related
methods (`price()` + `describe()` + `max_daily()`), holds configuration you want to
inspect, or needs a name in logs and admin UIs.

```go
type PricingRule func(minutes int) int

func Hourly(rate int) PricingRule {
	return func(m int) int { return (m + 59) / 60 * rate }
}
```

**Strategy vs. State:** same structure, different intent. A Strategy is chosen by the
*client* and rarely changes; a State is changed by the *object itself* as events happen.

---

## 4 · Factory and Registry

**Force:** code needs to create one of several implementations, chosen by data (config,
a request field, a file extension), without every call site knowing the concrete types.

At its smallest, a factory is just a dict from key to constructor:

```python
# The simplest possible factory: a dict from key to constructor function.
SHAPES = {
    "circle": lambda r: 3.14159 * r * r,
    "square": lambda s: s * s,
}

def area(kind: str, *args) -> float:
    return SHAPES[kind](*args)

assert area("square", 3) == 9
assert round(area("circle", 2), 2) == 12.57
```

The `Notifier` factory below is the same dict-dispatch idea with a typed interface,
constructor arguments read from config, and a real error on an unknown key:

```python
from typing import Callable, Protocol

class Notifier(Protocol):
    def send(self, to: str, body: str) -> None: ...

class EmailNotifier:
    def __init__(self, smtp_host: str) -> None: self.host = smtp_host
    def send(self, to: str, body: str) -> None: ...

class SmsNotifier:
    def __init__(self, api_key: str) -> None: self.key = api_key
    def send(self, to: str, body: str) -> None: ...

# Registry: data, not an if/elif ladder. Adding a channel = adding a line.
_FACTORIES: dict[str, Callable[[dict], Notifier]] = {
    "email": lambda cfg: EmailNotifier(cfg["smtp_host"]),
    "sms":   lambda cfg: SmsNotifier(cfg["api_key"]),
}

def make_notifier(kind: str, cfg: dict) -> Notifier:
    try:
        factory = _FACTORIES[kind]
    except KeyError:
        raise ValueError(f"unknown notifier {kind!r}; known: {sorted(_FACTORIES)}") from None
    return factory(cfg)
```

Details that matter:

- **Fail loudly on unknown keys** with the list of valid ones.
- **Explicit registration beats import side effects.** Decorator-based registration
  (`@register("sms")`) only works if the module defining `SmsNotifier` was imported —
  a classic "works locally, missing in prod" bug.
- **Factory Method** (GoF) is the subclass-overrides-a-creation-hook version; **Abstract
  Factory** creates *families* of related objects that must match (e.g. `AwsCloud` makes
  an `S3Store` and an `SqsQueue`; `GcpCloud` makes `GcsStore` and `PubSubQueue`). In
  Python/Go, both are usually just a function or a struct of constructor functions.
- **Go:** `database/sql` is a registry — drivers call `sql.Register("postgres", d)` in
  `init()`, and you blank-import them (`import _ "github.com/lib/pq"`). That is the
  import-side-effect style done deliberately and documented.

### Abstract Factory — a family that must match

**Force:** several objects must come from the *same* family, and mixing families is a bug
(an S3 store paired with a Pub/Sub queue). The rule "the family is chosen once" is
enforced by construction: only matching bundles exist.

```python
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class CloudKit:                 # in Python/Go an "abstract factory" is often just a bundle of constructors
    make_store: Callable[[], "BlobStore"]
    make_queue: Callable[[], "Queue"]

AWS = CloudKit(make_store=S3Store, make_queue=SqsQueue)
GCP = CloudKit(make_store=GcsStore, make_queue=PubSubQueue)

def build_pipeline(cloud: CloudKit):        # `cloud` is picked once, in the composition root
    return cloud.make_store(), cloud.make_queue()
```

Adding a third family is one new `CloudKit` value; adding a third *product* (a secrets
client) touches every family — that is the pattern's cost. **Overkill** when there is one
family, or when the members don't actually need to match; then it's two Factory Methods
with extra ceremony.

### Prototype — copy a configured instance

**Force:** you need many near-identical variants of an object that is expensive or
fiddly to configure (a report template, a test fixture, a game unit's stats).

```python
import copy
from dataclasses import dataclass, field, replace

@dataclass
class ReportTemplate:
    title: str
    sections: list[str] = field(default_factory=list)

base = ReportTemplate("Base", ["summary", "charts"])

shallow = copy.copy(base)
shallow.sections.append("appendix")
assert base.sections == ["summary", "charts", "appendix"]   # the trap: the list is SHARED

base = ReportTemplate("Base", ["summary", "charts"])
q3 = copy.deepcopy(base)                                    # deep copy: independent interior
q3.title = "Q3"
assert base.sections == ["summary", "charts"]

@dataclass(frozen=True)
class FrozenTemplate:                                       # immutable prototype: nothing to clone
    title: str
    sections: tuple[str, ...] = ()

q4 = replace(FrozenTemplate("Base", ("summary", "charts")), title="Q4")
```

The failure mode is always **aliasing**: a shallow copy shares its mutable interior with
the original. Go has the same trap — `clone := *base` copies the struct but not the
backing arrays of its slices and maps (`clone.Tags = slices.Clone(base.Tags)`). The best
fix is to make the prototype immutable so `replace(...)` *is* the pattern. **Overkill**
when construction is cheap: call the constructor.

---

## 5 · Builder — and why Python rarely needs it

**Force:** constructing an object needs many optional parts, or construction is
multi-step and the object must not be observable until valid.

Python's keyword arguments with defaults already solve the "telescoping constructor":

```python
from dataclasses import dataclass, field

@dataclass(frozen=True, kw_only=True)
class HttpRequest:
    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    timeout_s: float = 10.0
    retries: int = 0

req = HttpRequest(method="GET", url="https://x", timeout_s=2.0)
```

**A real Builder is still worth it when:**

- construction is **incremental** across code paths (a query builder assembling clauses
  as filters are applied);
- the product must be **validated as a whole** at the end (`build()` checks cross-field
  rules);
- the result is **immutable** but assembly is naturally mutable.

```python
class QueryBuilder:
    def __init__(self, table: str) -> None:
        self._table, self._wheres, self._params, self._limit = table, [], [], None

    def where(self, column: str, value) -> "QueryBuilder":
        if not column.isidentifier():
            raise ValueError("bad column")           # never interpolate user text into SQL
        self._wheres.append(f"{column} = ?")
        self._params.append(value)
        return self

    def limit(self, n: int) -> "QueryBuilder":
        self._limit = n
        return self

    def build(self) -> tuple[str, tuple]:
        sql = f"SELECT * FROM {self._table}"
        if self._wheres:
            sql += " WHERE " + " AND ".join(self._wheres)
        if self._limit is not None:
            sql += f" LIMIT {int(self._limit)}"
        return sql, tuple(self._params)

assert QueryBuilder("users").where("age", 30).limit(5).build() == \
       ("SELECT * FROM users WHERE age = ? LIMIT 5", (30,))
```

**Go:** `strings.Builder` (incremental assembly) and functional options (see
`03_modularity_coupling_and_api_design.md` §7) cover most cases.

---

## 6 · Singleton — and what to do instead

**Force:** exactly one instance should exist (a connection pool, a config, a metrics
registry).

The GoF Singleton — a class that controls its own instantiation and is fetched through a
global accessor — is the most criticised pattern because it is **global mutable state
with a nice name**:

- **Hidden dependencies:** `OrderService` calls `Database.instance()` inside a method;
  its constructor lies about what it needs.
- **Untestable:** tests can't substitute a fake without monkey-patching, and state leaks
  between tests.
- **Concurrency:** lazy initialisation needs locking (double-checked locking bugs are a
  classic).
- **"Exactly one" rarely stays true** — a second database, a per-tenant config.

### What to do instead

**Create one instance in the composition root and pass it in.** "One instance" is a
decision of the *application*, not of the *class*.

```python
def main() -> None:
    config = load_config()
    pool = ConnectionPool(config.db_url, size=config.pool_size)   # the one instance
    orders = OrderService(OrderRepository(pool))                  # explicit dependency
    serve(orders)
```

**If you truly need a process-wide instance** (logging registry, metrics), Python modules
are already singletons — a module-level object is the idiomatic form. In Go, use a
package-level variable initialised with `sync.OnceValue` (Go 1.21+) or `sync.Once`:

```go
var defaultRegistry = sync.OnceValue(func() *Registry { return newRegistry() })

func Default() *Registry { return defaultRegistry() }
```

**Interview answer:** "I'd avoid a classic Singleton because it hides dependencies and
makes testing hard. I'd create one instance at startup and inject it. If it must be
global — logging, metrics — I'd use a module-level instance or `sync.Once`, and still
allow tests to inject a different one."

---

## 7 · Observer / Pub-Sub — the details that bite

**Force:** when something happens, a changing set of other parties must react, and the
source shouldn't know who they are.

```arch
%% caption: The Subject publishes an event to an abstract bus, keeping the core domain decoupled from the side-effect handlers.
node sub "Subject" at 0,0 icon=server color=blue
node bus "EventBus" at 2,0 icon=queue color=amber
group obs "Observers" style=dashed color=green
node o1 "Logger" at 4,-1 in obs icon=file
node o2 "EmailNotifier" at 4,0 in obs icon=email
node o3 "MetricCounter" at 4,1 in obs icon=metrics

sub -> bus : "change(42)"
bus -> o1 : "notify"
bus -> o2 : "notify"
bus -> o3 : "notify"
```


The core of it is a list of callbacks:

```python
# The simplest possible observer: a list of plain callback functions.
watchers = []

def on_change(fn):
    watchers.append(fn)

def change(value):
    for fn in watchers:
        fn(value)

seen = []
on_change(lambda v: seen.append(v))
change(42)
assert seen == [42]
```

`EventBus` below is the same list-of-callbacks idea, hardened with topics, an
unsubscribe handle, and failure isolation:

```python
from collections import defaultdict
from typing import Callable
import logging

Handler = Callable[[dict], None]

class EventBus:
    """In-process, synchronous. Handlers run in subscription order."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Handler) -> Callable[[], None]:
        self._handlers[topic].append(handler)
        return lambda: self._handlers[topic].remove(handler)   # unsubscribe handle

    def publish(self, topic: str, event: dict) -> None:
        for handler in list(self._handlers[topic]):   # copy: handlers may unsubscribe
            try:
                handler(event)
            except Exception:
                logging.exception("handler failed for %s", topic)   # isolate failures
```

The design decisions you must state explicitly (these are the interview follow-ups):

| Decision | Options and consequences |
|---|---|
| **Sync or async delivery** | Sync: simple, ordered, publisher is slowed and can be broken by a slow handler. Async (queue/thread/goroutine): publisher decoupled, but ordering, back-pressure, and error reporting become questions. |
| **Handler failure** | Propagate (one bad handler breaks the publisher), isolate and log (above), or retry/dead-letter. |
| **Mutation during publish** | Iterate over a copy, or you'll skip handlers or raise "changed size during iteration". |
| **Memory leaks** | Subscribers that never unsubscribe keep objects alive. Return an unsubscribe handle; consider `weakref.WeakMethod` for bound methods. |
| **Re-entrancy** | A handler that publishes can cause infinite loops or out-of-order delivery. |
| **Ordering guarantees** | Per topic? Per key? None? |
| **Push vs. pull** | Push the full event, or notify "something changed" and let observers query (avoids stale/huge payloads). |
| **Delivery semantics** | In-process: at-most-once (lost on crash). Durable: at-least-once → handlers must be idempotent. |

**Observer vs. Pub-Sub:** in Observer, subjects hold direct references to observers. In
Pub-Sub, a broker (bus, topic) sits between them and neither knows the other — the
standard for cross-module and cross-service events. Full implementations:
`PyEngineering/16_pubsub_event_bus`, `GoEngineering/16_pubsub_event_bus`.

**Go:** channels are the natural async observer; beware a slow subscriber blocking the
publisher on an unbuffered channel — decide between blocking, dropping, or buffering.

### Mediator — when peers know too much about each other

**Force:** N collaborators that must coordinate (form widgets, chat participants, aircraft
and a tower) end up holding references to each other — up to N·(N−1) links — so none can
be changed or tested alone. A **Mediator** is the one object every peer knows; peers talk
to it, and the *coordination rules* live in it.

```python
class User:
    def __init__(self, name: str) -> None:
        self.name, self.inbox = name, []
    def receive(self, sender: str, text: str) -> None:
        self.inbox.append((sender, text))

class ChatRoom:                                   # users know the room, never each other
    def __init__(self) -> None:
        self._members: dict[str, User] = {}
    def join(self, user: User) -> None:
        self._members[user.name] = user
    def send(self, sender: User, text: str, to: str | None = None) -> None:
        targets = ([self._members[to]] if to is not None
                   else [m for n, m in self._members.items() if n != sender.name])
        for m in targets:
            m.receive(sender.name, text)
```

**Mediator vs. Observer:** Observer is one-to-many broadcast where the source has no
opinion about who listens. Mediator is many-to-many *coordination with logic* — who
receives what, in what order, under what rules. The cost is that the mediator collects
every interaction rule and can grow into a god object (`05` §6); split it by feature
before that happens. **Overkill** with two or three collaborators — wire them directly.

---

## 8 · Command — undo, redo, queues, and audit

**Force:** operations must be treated as data — undone, redone, queued, retried,
scheduled, logged, or sent across a boundary.

The smallest command is an action paired with its own undo:

```python
# The simplest possible command: an action paired with its own undo.
class ToggleLight:
    def __init__(self, light: dict) -> None:
        self._light = light
    def execute(self) -> None:
        self._light["on"] = not self._light["on"]
    def undo(self) -> None:
        self.execute()          # toggling is its own inverse

light = {"on": False}
cmd = ToggleLight(light)
cmd.execute(); assert light["on"] is True
cmd.undo();    assert light["on"] is False
```

Most real commands aren't self-inverse. The text editor below captures what `undo`
needs *at execute time*, and adds undo/redo stacks:

```python
from dataclasses import dataclass, field
from typing import Protocol

class Command(Protocol):
    def execute(self, doc: "Document") -> None: ...
    def undo(self, doc: "Document") -> None: ...

@dataclass
class Document:
    text: str = ""

@dataclass
class Insert:
    pos: int
    s: str
    def execute(self, doc: Document) -> None:
        doc.text = doc.text[:self.pos] + self.s + doc.text[self.pos:]
    def undo(self, doc: Document) -> None:
        doc.text = doc.text[:self.pos] + doc.text[self.pos + len(self.s):]

@dataclass
class Delete:
    start: int
    end: int
    _removed: str = field(default="", init=False)     # captured at execute time
    def execute(self, doc: Document) -> None:
        self._removed = doc.text[self.start:self.end]
        doc.text = doc.text[:self.start] + doc.text[self.end:]
    def undo(self, doc: Document) -> None:
        doc.text = doc.text[:self.start] + self._removed + doc.text[self.start:]

class Editor:
    def __init__(self) -> None:
        self.doc = Document()
        self._undo: list[Command] = []
        self._redo: list[Command] = []

    def run(self, cmd: Command) -> None:
        cmd.execute(self.doc)
        self._undo.append(cmd)
        self._redo.clear()           # a new action invalidates the redo history

    def undo(self) -> None:
        if self._undo:
            cmd = self._undo.pop()
            cmd.undo(self.doc)
            self._redo.append(cmd)

    def redo(self) -> None:
        if self._redo:
            cmd = self._redo.pop()
            cmd.execute(self.doc)
            self._undo.append(cmd)

ed = Editor()
ed.run(Insert(0, "hello world"))
ed.run(Delete(5, 11))
assert ed.doc.text == "hello"
ed.undo();  assert ed.doc.text == "hello world"
ed.undo();  assert ed.doc.text == ""
ed.redo();  assert ed.doc.text == "hello world"
```

Points that come up:

- **Commands must capture what undo needs at execute time** (`_removed`), not at creation.
- **A new command clears redo.**
- **Undo by inverse operation vs. by snapshot (Memento):** inverse ops are memory-cheap
  but must be exactly right; snapshots are trivially right but cost memory. Real editors
  combine them (periodic snapshots + op log).
- **Collaborative editing** needs commands transformed against concurrent commands
  (operational transformation) or CRDTs — see
  `SystemDesign/building_blocks/22_realtime_and_collaboration.md`.
- Commands as data are the basis of **job queues, event sourcing, CQRS commands, and
  macro recording**.

### Memento — snapshot instead of inverse

**Force:** you need to restore an earlier state (undo, transaction rollback, "try it and
back out") but the object's state is private, or writing an exact inverse for every
operation is harder than copying.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class _Snapshot:                 # opaque to callers: only Editor looks inside
    text: str
    cursor: int

class Editor:
    def __init__(self) -> None:
        self.text, self.cursor = "", 0
    def type(self, s: str) -> None:
        self.text = self.text[:self.cursor] + s + self.text[self.cursor:]
        self.cursor += len(s)
    def snapshot(self) -> _Snapshot:
        return _Snapshot(self.text, self.cursor)
    def restore(self, snap: _Snapshot) -> None:
        self.text, self.cursor = snap.text, snap.cursor

ed, history = Editor(), []          # the caretaker just stores snapshots; it can't read them
ed.type("hello");  history.append(ed.snapshot())
ed.type(" world"); history.append(ed.snapshot())
ed.restore(history[0])
assert (ed.text, ed.cursor) == ("hello", 5)
```

Three roles: the **originator** (`Editor`) makes and consumes snapshots, the **memento**
holds state, the **caretaker** stores mementos without opening them. The trade-off against
Command's inverse operations is memory versus correctness: a snapshot is trivially right
but costs O(state) each time (make it cheap with immutable values that share structure);
an inverse is O(change) but must be exactly right. The transactional key-value store
(`lld/006`) is this trade-off in miniature: snapshotting the whole store on `BEGIN` is the
obvious version; its undo log records only the keys a transaction touched, so rollback
costs O(writes), not O(store). **Overkill** when the object is already an immutable
dataclass — then "the memento" is just the previous value in a list.

---

## 9 · State — when each state behaves differently

**Force:** an object's response to the same operations differs substantially by its
current state, and `if self.state == ...` is spreading into every method.

If behaviour per state is mostly "allowed or not", a **transition table** is simpler
(`02_oop_and_domain_modeling.md` §10). Use the State pattern when states have genuinely
different logic:

```python
class VendingMachine:
    def __init__(self, stock: dict[str, tuple[int, int]]) -> None:   # code -> (price, qty)
        self.stock = stock
        self.balance = 0
        self.state: "State" = Idle()

    def insert(self, cents: int) -> None:      self.state.insert(self, cents)
    def select(self, code: str) -> str | None: return self.state.select(self, code)
    def cancel(self) -> int:                   return self.state.cancel(self)

class State:
    def insert(self, m: VendingMachine, cents: int) -> None:
        raise RuntimeError(f"cannot insert in {type(self).__name__}")
    def select(self, m: VendingMachine, code: str) -> str | None:
        raise RuntimeError(f"cannot select in {type(self).__name__}")
    def cancel(self, m: VendingMachine) -> int:
        return 0

class Idle(State):
    def insert(self, m, cents):
        m.balance += cents
        m.state = HasMoney()

class HasMoney(State):
    def insert(self, m, cents):
        m.balance += cents
    def select(self, m, code):
        price, qty = m.stock.get(code, (0, 0))
        if qty == 0 or m.balance < price:
            return None                         # stay in HasMoney
        m.stock[code] = (price, qty - 1)
        m.balance -= price
        m.state = Idle() if m.balance == 0 else HasMoney()
        return code
    def cancel(self, m):
        refund, m.balance = m.balance, 0
        m.state = Idle()
        return refund
```

Trade-offs to say out loud:

- **Who owns transitions?** States (above — each state knows its successors) or the
  context (a central table). State-owned is more flexible; context-owned is easier to see
  as a whole.
- **Stateless state objects** can be shared singletons (`IDLE = Idle()`); stateful ones
  (e.g. a `Dispensing` state holding a timer) must be created per transition.
- **Persistence:** you store an enum, not a class instance; map enum ↔ state object on load.

The complete, tested version with change-making and out-of-stock handling is
`lld/003_vending_machine_solution.py`.

---

## 10 · Decorator, Proxy, Adapter, Facade — four wrappers, four intents

All four wrap something. They differ by **intent and interface**:

| Pattern | Interface exposed vs. wrapped | Intent | Example |
|---|---|---|---|
| **Decorator** | **Same** | Add behaviour | Retry, logging, metrics, caching around a client |
| **Proxy** | **Same** | Control access | Lazy loading, remote stub, permission check, rate limit |
| **Adapter** | **Different** (converts) | Make an incompatible interface fit | Wrap a vendor <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> to implement your `PaymentGateway` port |
| **Facade** | **Simpler / new** | Hide a complicated subsystem | `VideoConverter.convert(file, fmt)` over codecs, muxers, buffers |

### GoF Decorator vs. Python `@decorator`

Python's `@decorator` syntax wraps **functions**; the GoF Decorator wraps **objects that
implement an interface**. They share an idea (same interface, added behaviour) and are
often used interchangeably in conversation. Both compose:

```python
import functools, time

def retry(times: int, on: tuple[type[Exception], ...]):
    def wrap(fn):
        @functools.wraps(fn)                      # keep name/docstring for debugging
        def inner(*args, **kwargs):
            for attempt in range(times):
                try:
                    return fn(*args, **kwargs)
                except on:
                    if attempt == times - 1:
                        raise
                    time.sleep(0.01 * 2 ** attempt)
        return inner
    return wrap
```

```go
// Object decorator in Go: a struct implementing the same interface.
type Store interface{ Get(ctx context.Context, k string) ([]byte, error) }

type cachedStore struct {
	inner Store
	cache *lru.Cache[string, []byte]
}

func (c *cachedStore) Get(ctx context.Context, k string) ([]byte, error) {
	if v, ok := c.cache.Get(k); ok {
		return v, nil
	}
	v, err := c.inner.Get(ctx, k)
	if err == nil {
		c.cache.Add(k, v)
	}
	return v, err
}
```

**Order matters when stacking:** `retry(cache(fetch))` retries cache misses;
`cache(retry(fetch))` caches the retried result. `metrics(retry(x))` counts one call;
`retry(metrics(x))` counts every attempt. State the order you chose and why.

### Proxy — same interface, controlled access

A Proxy has the identical shape as a Decorator — same interface, wraps a collaborator —
but its intent is **controlling access**, not adding behaviour: lazy loading, a remote
stub, a permission check, rate limiting, or a cache.

```python
class SlowService:
    def fetch(self, key: str) -> str:
        return f"value-for-{key}"        # imagine a slow network call

class CachingProxy:                      # same interface as SlowService
    def __init__(self, real: SlowService) -> None:
        self._real = real
        self._cache: dict[str, str] = {}
    def fetch(self, key: str) -> str:
        if key not in self._cache:
            self._cache[key] = self._real.fetch(key)
        return self._cache[key]

proxy = CachingProxy(SlowService())
assert proxy.fetch("a") == "value-for-a"
assert proxy.fetch("a") == "value-for-a"   # second call hits the cache, not SlowService
```

Swap `CachingProxy` for `RateLimitedProxy`, `ReadOnlyProxy`, or `RemoteStubProxy` and
callers don't change — they still just call `.fetch(key)`. That's the same test as
Decorator vs. Proxy in the table above: ask *why* you're wrapping. Adding behaviour on
top of what's already there is Decorator; deciding whether or how the call reaches the
real thing is Proxy.

### Adapter as an anti-corruption layer

```python
class PaymentGateway(Protocol):                   # OUR port, in OUR vocabulary
    def charge(self, customer_id: str, amount: "Money", idempotency_key: str) -> str: ...

class VendorXAdapter:                             # translates both ways, at the boundary
    def __init__(self, client) -> None:
        self._client = client

    def charge(self, customer_id, amount, idempotency_key):
        try:
            resp = self._client.payments.create(
                cust=customer_id, amt=amount.amount_minor, cur=amount.currency.lower(),
                headers={"Idempotency-Key": idempotency_key})
        except self._client.errors.RateLimited as e:
            raise Transient("vendor rate limited") from e
        return resp["payment"]["id"]
```

Nothing outside `VendorXAdapter` knows the vendor's field names, error types, or casing.
Switching vendors is one new adapter.

### Facade — one simple call over a subsystem

**Force:** getting anything done needs several collaborators used in the right order,
and most callers only ever want the common case.

```python
class Decoder:
    def decode(self, path: str) -> bytes: return b"raw-frames"

class Encoder:
    def encode(self, frames: bytes, fmt: str) -> bytes: return frames + fmt.encode()

class Muxer:
    def package(self, data: bytes) -> bytes: return b"[" + data + b"]"

class VideoConverter:                     # the facade: one call, three collaborators hidden
    def __init__(self) -> None:
        self._decoder, self._encoder, self._muxer = Decoder(), Encoder(), Muxer()
    def convert(self, path: str, fmt: str) -> bytes:
        frames = self._decoder.decode(path)
        encoded = self._encoder.encode(frames, fmt)
        return self._muxer.package(encoded)

assert VideoConverter().convert("movie.avi", "mp4") == b"[raw-framesmp4]"
```

A Facade doesn't hide `Decoder`, `Encoder`, and `Muxer` — code that needs frame-level
control can still use them directly. It only removes the need to know all three, and
the order they run in, for the 95% case. **Overkill** when the subsystem already has one
obvious entry point — then the facade is just a same-named wrapper adding nothing.

### Bridge — two dimensions that vary independently

The fifth structural pattern people confuse with the four above. **Force:** an abstraction
(what a report *is*) and its implementation (how it is *rendered*) each grow their own
variants. As inheritance that is M×N classes (`02` §4); with a Bridge the abstraction
*holds* an implementation object, so it is M+N.

```python
from typing import Protocol

class Renderer(Protocol):                 # implementation side
    def heading(self, text: str) -> str: ...
    def item(self, text: str) -> str: ...

class Markdown:
    def heading(self, text): return f"# {text}"
    def item(self, text): return f"- {text}"

class Html:
    def heading(self, text): return f"<h1>{text}</h1>"
    def item(self, text): return f"<li>{text}</li>"

class SalesReport:                        # abstraction side: knows WHAT, delegates HOW
    def __init__(self, r: Renderer) -> None:
        self.r = r
    def render(self, rows: list[str]) -> list[str]:
        return [self.r.heading("Sales")] + [self.r.item(x) for x in rows]

assert SalesReport(Markdown()).render(["EU 3"]) == ["# Sales", "- EU 3"]
assert SalesReport(Html()).render(["EU 3"]) == ["<h1>Sales</h1>", "<li>EU 3</li>"]
```

**Bridge vs. Adapter vs. Strategy:** the structure is the same "hold a collaborator and
delegate". *Adapter* is applied after the fact to reconcile interfaces that already exist
and don't match; *Bridge* is designed up front so two hierarchies can evolve separately;
*Strategy* swaps one algorithm and usually has a single varying axis. **Overkill** when
only one dimension varies — a plain interface is enough. In Go, `sql.DB` over swappable
`driver.Driver` implementations is a Bridge in spirit.

---

## 11 · Chain of Responsibility and Middleware

**Force:** a request passes through a sequence of handlers, each of which may handle it,
modify it, short-circuit it, or pass it on — and the sequence is configured, not
hard-coded.

Two variants:

1. **Classic CoR:** each handler decides whether to handle *or* pass on; typically one
   handles it. (Logging levels, support-ticket escalation, ATM note dispensing.)
2. **Middleware / pipeline:** every handler runs, wrapping the next. (<abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> middleware,
   <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> interceptors.)

```python
from typing import Callable

Handler = Callable[[dict], dict]
Middleware = Callable[[Handler], Handler]

def auth(next_: Handler) -> Handler:
    def h(req: dict) -> dict:
        if req.get("token") != "secret":
            return {"status": 401}               # short-circuit
        return next_(req)
    return h

def timing(next_: Handler) -> Handler:
    def h(req: dict) -> dict:
        resp = next_(req)
        return {**resp, "timed": True}
    return h

def chain(handler: Handler, *middlewares: Middleware) -> Handler:
    for mw in reversed(middlewares):             # first listed = outermost
        handler = mw(handler)
    return handler

app = chain(lambda req: {"status": 200}, timing, auth)
assert app({"token": "secret"}) == {"status": 200, "timed": True}
assert app({}) == {"status": 401, "timed": True}  # timing is outside auth, so it still ran
```

Go's `func(http.Handler) http.Handler` is exactly this shape. Worked versions:
`PyEngineering/02_middleware_chain`, `GoEngineering/02_middleware_chain`.

**ATM cash dispensing** is the classic interview CoR: a chain of `NoteDispenser(2000) →
(500) → (100)`, each taking as many notes as it can and passing the remainder. (Note the
greedy approach is only correct for "canonical" denomination systems and unlimited
notes; with limited notes it can fail where a solution exists — mention it.)

---

## 12 · Composite and Visitor — trees

**Composite force:** part-whole hierarchies (files/directories, UI widgets, org charts,
expression trees, bundles of products) where clients should treat a leaf and a group the
same way.

```python
from dataclasses import dataclass, field

@dataclass
class File:
    name: str
    size: int
    def total_size(self) -> int: return self.size

@dataclass
class Directory:
    name: str
    children: list["File | Directory"] = field(default_factory=list)
    def total_size(self) -> int: return sum(c.total_size() for c in self.children)
```

**Visitor force:** many different operations over a *stable* set of node types, without
putting every operation into every node class (the expression problem, `02` §14).

In modern Python and Go, **structural pattern matching / type switches replace most
Visitors**:

```python
def render(node: "File | Directory", depth: int = 0) -> list[str]:
    match node:
        case File(name=n, size=s):
            return [f"{'  ' * depth}{n} ({s}B)"]
        case Directory(name=n, children=cs):
            lines = [f"{'  ' * depth}{n}/"]
            for c in cs:
                lines += render(c, depth + 1)
            return lines
```

Keep the classic double-dispatch Visitor for languages without pattern matching, or when
you need the compiler to force every visitor to handle a newly added node type (Go
achieves a weaker version with a type switch plus a linter like `exhaustive`).

---

## 13 · Template Method vs. hooks vs. composition

**Force:** an algorithm's skeleton is fixed; some steps vary.

```python
# TEMPLATE METHOD (inheritance): base defines the skeleton, subclasses fill steps.
class Importer:
    def run(self, path: str) -> int:
        rows = self.parse(open(path).read())
        valid = [r for r in rows if self.validate(r)]
        self.save(valid)
        return len(valid)
    def parse(self, raw: str) -> list[dict]: raise NotImplementedError
    def validate(self, row: dict) -> bool: return True          # hook with default
    def save(self, rows: list[dict]) -> None: raise NotImplementedError

# COMPOSITION: the skeleton is a function; steps are parameters.
def run_import(raw: str, parse, save, validate=lambda r: True) -> int:
    valid = [r for r in parse(raw) if validate(r)]
    save(valid)
    return len(valid)
```

Template Method is fine for a stable framework hook (`unittest.TestCase.setUp`,
`threading.Thread.run`), but it binds step choices together in one subclass: a CSV parser
with a Postgres saver and a <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> parser with a Postgres saver are two subclasses, and
every parser × saver combination is another. Composition lets them vary independently.

---

## 14 · Iterator — generators and Go's range-over-func

The Iterator pattern is built into both languages; you almost never write the class.

```python
def paginate(fetch_page, page_size: int = 100):
    """Hides cursor-based pagination behind a flat iterator."""
    cursor = None
    while True:
        items, cursor = fetch_page(cursor, page_size)
        yield from items
        if cursor is None:
            return
```

Callers write `for user in paginate(api.list_users):` and never see cursors — a deep
module (`01` §3). Laziness also means memory is O(page), and a caller who `break`s early
stops fetching.

```go
// Go 1.23+: iterators are functions; range works over them.
func Paginate[T any](fetch func(cursor string) ([]T, string, error)) iter.Seq2[T, error] {
	return func(yield func(T, error) bool) {
		cursor := ""
		for {
			items, next, err := fetch(cursor)
			if err != nil {
				var zero T
				yield(zero, err)
				return
			}
			for _, it := range items {
				if !yield(it, nil) {
					return // caller broke out of the loop
				}
			}
			if next == "" {
				return
			}
			cursor = next
		}
	}
}
```

**Trap:** a Python generator is single-use; iterating it twice silently yields nothing
the second time. Return a list (or a re-iterable object) when callers may iterate twice.

---

## 15 · Specification (filter composition)

Not in GoF, but the core of the **"design Unix `find`"** and **"design a product search
filter"** interview questions.

**Force:** users combine arbitrary criteria with AND/OR/NOT, and new criteria keep being
added.

At its simplest, a spec is just predicate functions combined by helper functions:

```python
# The simplest possible spec: plain predicate functions combined with helpers.
def and_(*preds): return lambda x: all(p(x) for p in preds)
def or_(*preds):  return lambda x: any(p(x) for p in preds)

is_even = lambda n: n % 2 == 0
is_positive = lambda n: n > 0

check = and_(is_even, is_positive)
assert check(4) is True
assert check(-4) is False
```

The `Spec` class below adds the same composition through `&`/`|`/`~` operators and a
human-readable label — worth the extra ceremony once specs need to be logged, debugged,
or built at runtime from user input:

```python
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class FileInfo:
    name: str
    size: int
    is_dir: bool

@dataclass(frozen=True)
class Spec:
    test: Callable[[FileInfo], bool]
    label: str

    def __call__(self, f: FileInfo) -> bool: return self.test(f)
    def __and__(self, o: "Spec") -> "Spec": return Spec(lambda f: self(f) and o(f), f"({self.label} AND {o.label})")
    def __or__(self, o: "Spec") -> "Spec":  return Spec(lambda f: self(f) or o(f), f"({self.label} OR {o.label})")
    def __invert__(self) -> "Spec":         return Spec(lambda f: not self(f), f"NOT {self.label}")

def larger_than(n: int) -> Spec: return Spec(lambda f: f.size > n, f"size>{n}")
def extension(ext: str) -> Spec: return Spec(lambda f: f.name.endswith(ext), f"ext={ext}")
IS_FILE = Spec(lambda f: not f.is_dir, "file")

query = IS_FILE & (extension(".xml") | larger_than(5_000_000)) & ~extension(".tmp.xml")
```

- Open/closed in practice: a new criterion is one function; no existing code changes.
- The `label` makes queries debuggable and loggable.
- To push filters down to a database or index, keep specs as **data** (an <abbr title="Abstract Syntax Tree. A tree representation of the abstract syntactic structure of source code written in a programming language.">AST</abbr> of
  `And/Or/Not/Leaf`) instead of closures, then translate that <abbr title="Abstract Syntax Tree. A tree representation of the abstract syntactic structure of source code written in a programming language.">AST</abbr> to <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> or evaluate it
  in memory (Composite + Interpreter).

Full tested version: `lld/010_unix_find_solution.py`.

---

## 16 · Repository and Unit of Work

From Fowler's *Patterns of Enterprise Application Architecture* — the two patterns that
make "domain logic doesn't know about the database" real.

**Repository:** a collection-like interface for aggregates, in domain vocabulary.

```python
from typing import Protocol

class OrderRepository(Protocol):
    def get(self, order_id: str) -> "Order": ...          # raises NotFound
    def add(self, order: "Order") -> None: ...
    def list_open_for(self, customer_id: str) -> list["Order"]: ...

class InMemoryOrderRepository:                            # the test fake — a real class, not a mock
    def __init__(self) -> None:
        self._orders: dict[str, "Order"] = {}
    def get(self, order_id):
        try:
            return self._orders[order_id]
        except KeyError:
            raise NotFound(order_id) from None
    def add(self, order):
        self._orders[order.id] = order
    def list_open_for(self, customer_id):
        return [o for o in self._orders.values() if o.customer_id == customer_id and o.is_open]
```

Rules: **one repository per aggregate root** (no `OrderLineRepository`); methods named
for domain queries (`list_open_for`), not generic `query(sql)`; returns domain objects,
never <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> rows or cursors.

**Unit of Work:** tracks changes during a business operation and commits them atomically.

```python
class UnitOfWork(Protocol):
    orders: OrderRepository
    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, *exc) -> None: ...     # rollback unless commit() was called
    def commit(self) -> None: ...

def cancel_order(uow: UnitOfWork, order_id: str) -> None:
    with uow:
        order = uow.orders.get(order_id)
        order.cancel()                         # domain rule lives on the entity
        uow.commit()
```

Worked versions with real SQLite transactions: `PyEngineering/09_database_repository_layer`,
`10_transactions_concurrency_control`.

**Don't** add a Repository over an <abbr title="Object-Relational Mapping - A programming technique for converting data between incompatible type systems using object-oriented programming languages.">ORM</abbr> for a <abbr title="Create, Read, Update, Delete - The four basic functions of persistent storage operations, commonly used in database and <abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr> design.">CRUD</abbr> app with no domain logic — it's a
pass-through layer (`01` §6).

---

## 17 · Null Object and Special Case

**Force:** "no collaborator" is a valid situation, and `if x is not None:` is appearing
at every use.

```python
class Metrics(Protocol):
    def incr(self, name: str, n: int = 1) -> None: ...

class NullMetrics:
    def incr(self, name: str, n: int = 1) -> None:
        pass                                  # deliberately does nothing

class Uploader:
    def __init__(self, metrics: Metrics = NullMetrics()) -> None:   # safe: stateless
        self._metrics = metrics
    def upload(self, blob: bytes) -> None:
        self._metrics.incr("uploads")         # no None check anywhere
```

**Special Case** (Fowler) generalises it: `GuestUser` with `is_authenticated = False`
and sensible defaults instead of `None` users; `UnknownCustomer` with a default billing
plan.

**Don't** use a Null Object where absence is an *error* the caller must notice — that
turns a loud failure into silent wrong behaviour. A missing payment gateway should crash
at startup, not silently not charge.

---

## 18 · Flyweight and Object Pool

**Flyweight:** share immutable intrinsic state among many objects; keep extrinsic state
outside.

- A text editor stores one `Glyph('a', font)` object shared by every 'a'; the position
  is extrinsic.
- A game with 1M trees shares one `TreeModel` (mesh, texture) and stores only
  `(x, y, model_ref)` per tree.
- Python's `sys.intern`, small-int cache, and `__slots__` are flyweight-flavoured
  memory techniques.

```python
class Glyph:                              # intrinsic state: shared, immutable
    def __init__(self, char: str, font: str) -> None:
        self.char, self.font = char, font

_GLYPH_CACHE: dict[tuple[str, str], Glyph] = {}

def glyph(char: str, font: str) -> Glyph:
    key = (char, font)
    if key not in _GLYPH_CACHE:
        _GLYPH_CACHE[key] = Glyph(char, font)
    return _GLYPH_CACHE[key]

# "hello hello" is 11 characters but only 5 distinct ones -> 5 shared Glyph objects.
positions = [(i, glyph(c, "Arial")) for i, c in enumerate("hello hello")]
assert glyph("h", "Arial") is glyph("h", "Arial")             # same object, not a copy
assert len({id(g) for _, g in positions}) == len(set("hello hello"))
```

The extrinsic state — where each glyph is drawn — lives in `positions`, outside the
`Glyph`. Sharing only pays off when there are *many* objects with *few* distinct values
of the expensive part; for a handful of objects it's not worth the cache/lookup cost.

**Object Pool:** reuse expensive-to-create objects (connections, threads, large buffers).

```python
from contextlib import contextmanager

class ConnectionPool:
    def __init__(self, size: int) -> None:
        self._free = [f"conn-{i}" for i in range(size)]

    @contextmanager
    def borrow(self):
        conn = self._free.pop()          # raises IndexError if the pool is exhausted
        try:
            yield conn
        finally:
            self._free.append(conn)      # always returned, even on exception

pool = ConnectionPool(size=2)
with pool.borrow() as c1:
    assert c1 == "conn-1"
assert pool._free == ["conn-0", "conn-1"]     # returned automatically
```

- **Database connection pools** and **thread/worker pools** are pools; use the library's.
- **Go `sync.Pool`** is for reducing <abbr title="Garbage Collection. A form of automatic memory management that attempts to reclaim garbage, or memory occupied by objects that are no longer in use by the program.">GC</abbr> pressure on short-lived temporary objects (e.g.
  `bytes.Buffer`); items can be dropped at any <abbr title="Garbage Collection. A form of automatic memory management that attempts to reclaim garbage, or memory occupied by objects that are no longer in use by the program.">GC</abbr>, so **never** use it for connections.
- Pool pitfalls: returning a dirty object (reset before reuse), leaking (always return in
  `finally`/`defer`), pool exhaustion deadlock (a task holding one connection waits for a
  second). The `@contextmanager` form above returns the connection in `finally` so
  leaking requires bypassing `borrow()` entirely.

---

## 19 · Pattern overuse — how to recognise it

| Symptom | What happened |
|---|---|
| `AbstractFactoryFactory`, `StrategyManagerProvider` | Patterns stacked to satisfy a pattern, not a need |
| An interface + factory + one implementation, for a thing never swapped | Speculative generality |
| To follow one request you open 9 files, each a 5-line delegator | Indirection without depth (`01` §3) |
| Visitor over 2 node types with 1 operation | A function would do |
| Observer where the "observers" are a fixed, known list | A direct call sequence is clearer and debuggable |
| Singleton for something that's just configuration | Global state; inject it |
| Builder for a 3-field object | Keyword arguments |
| Class names that are pattern names (`OrderStrategy`, `UserFactory`) everywhere | The design is described by mechanism, not domain |

> **Name classes for what they do in the domain** (`TieredPricing`, `SmsNotifier`), and
> mention the pattern in a docstring if it helps. Pattern names in type names are a mild
> smell.

---

## 20 · Which patterns each LLD problem uses

| Problem | Patterns that naturally appear | Where |
|---|---|---|
| Parking lot | Strategy (spot allocation, pricing), Factory (spot/vehicle types), Singleton-avoidance | `lld/001` |
| Elevator | State (per car), Strategy (dispatch algorithm), Command (requests), Observer (displays) | `lld/002` |
| Vending machine | State, Chain of Responsibility (change making) | `lld/003` |
| Movie / seat booking | Repository, Strategy (pricing), Specification (search), locking/holds with expiry | `lld/004` |
| Splitwise | Strategy (equal/exact/percent split), Factory | `lld/005` |
| In-memory KV store with transactions | Command / Memento (transaction log), Stack of scopes | `lld/006` |
| Logging framework | Chain of Responsibility (levels), Strategy (formatter), Observer/Composite (appenders), Singleton-avoidance | `lld/007` |
| Tic-tac-toe / board games | Strategy (players, win rules), State (game), Factory | `lld/008` |
| Cache with eviction | Strategy (<abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr>/<abbr title="Least Frequently Used. A cache replacement policy that discards the least frequently used items first.">LFU</abbr>/<abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr>), Decorator (TTL, stats), Proxy | `lld/009` |
| Unix find | Specification, Composite, Iterator | `lld/010` |
| Meeting room / hotel booking | Strategy (room selection), value objects (intervals), Observer (notifications) | `lld/011` |
| Rate limiter library | Strategy (token bucket, sliding window), Decorator / Proxy | `lld/012` |
| Text editor | Command (undo/redo), Memento, Flyweight | §8 above |
| Notification service | Strategy/Factory (channels), Observer, Template Method (retry), Decorator | `PyEngineering/16` |

---

## 21 · Interview questions and model answers

**Q: Strategy vs. State?**
Same structure — an object delegating to a swappable collaborator. Strategy is chosen by
the client and represents *how* to do something; State is changed by the object itself as
events happen and represents *what mode it's in*.

**Q: Decorator vs. Proxy vs. Adapter?**
Decorator and Proxy keep the same interface — Decorator adds behaviour, Proxy controls
access (lazy, remote, cached, authorised). Adapter changes the interface to one clients
expect. Facade provides a new, simpler interface over a subsystem.

**Q: Why is Singleton considered an anti-pattern?**
It's global mutable state: hidden dependencies, hard to substitute in tests, lazy-init
race conditions, and "exactly one" rarely stays true. Create one instance in the
composition root and inject it.

**Q: How would you implement undo/redo?**
Command pattern: each action is an object with `execute` and `undo` that captures what it
needs at execution time; an undo stack and a redo stack; a new command clears redo. For
complex state, combine inverse operations with periodic snapshots (Memento).

**Q: Factory Method vs. Abstract Factory?**
Factory Method: a single overridable creation method (subclass decides the concrete type).
Abstract Factory: an object that creates a *family* of related products that must be used
together (AWS store + AWS queue). In Python/Go both are often a function or a registry.

**Q: Bridge vs. Adapter?**
Both hold a collaborator and delegate. Adapter reconciles two interfaces that already exist
and don't match; Bridge is designed up front so an abstraction and its implementation can
each gain variants without an M×N class explosion.

**Q: Observer vs. Mediator?**
Observer broadcasts one-to-many and the source doesn't care who listens. Mediator
coordinates many-to-many: peers know only the mediator, which holds the interaction rules
— at the risk of becoming a god object.

**Q: Observer pitfalls?**
Sync handlers slowing or breaking the publisher, handler exceptions, mutation during
notification, memory leaks from never-unsubscribed observers, re-entrant publishes,
ordering, and — once delivery is durable — at-least-once semantics requiring idempotent
handlers.

**Q: Which patterns do you actually use most?**
Strategy (as functions), Adapter at every third-party boundary, Decorator/middleware for
cross-cutting concerns, Repository for persistence, Factory/registry for config-driven
construction, Observer/events between modules, Command for jobs and undo, State for
lifecycles, Iterator via generators. Rarely: Visitor, Flyweight, Prototype, Mediator.

**Q: Do patterns matter in Python and Go?**
The problems they solve do; the class-heavy forms mostly don't. First-class functions make
Strategy, Command, Template Method and Factory into functions; generators are Iterator;
modules are Singletons; `match` covers Visitor. Knowing the pattern names still matters
for communicating designs.
