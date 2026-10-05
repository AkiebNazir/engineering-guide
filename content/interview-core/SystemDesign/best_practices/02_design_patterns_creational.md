# Design Patterns — Creational

Creational patterns control how objects get constructed so that construction logic doesn't leak into every caller. Each entry: problem solved → short example → when it's overkill.

## Singleton

**Problem solved:** ensure exactly one instance of a class exists and is globally reachable (a logging sink, a hardware-bound connection pool).

```python
class ConnectionPool:
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

**Why it's often an anti-pattern in modern testable code:** it is global mutable state with a design-pattern name. It hides a dependency inside every consumer instead of passing it explicitly (violates DIP — see [01](01_design_principles.md)), makes unit tests order-dependent because state persists across tests, and makes swapping an implementation for a test double require monkeypatching instead of constructor injection.

**Still legitimate when:** the underlying resource is genuinely singular at the process level and expensive to duplicate — a DB connection pool, a metrics registry, a hardware handle. Even then, prefer constructing it once at the composition root and injecting it, rather than letting every consumer reach for a global accessor.

**When NOT to reach for it:** "I only need one of these right now" is not the same as "only one can exist." If nothing stops a second instance from being safe, don't force a Singleton — just construct one instance in `main()` and pass it down.

## Factory Method

**Problem solved:** defer *which concrete class* to instantiate to a subclass or a passed-in creator function, so calling code depends only on an interface.

```python
class Notifier(Protocol):
    def send(self, msg: str) -> None: ...

def create_notifier(channel: str) -> Notifier:
    if channel == "email":
        return EmailNotifier()
    if channel == "sms":
        return SmsNotifier()
    raise ValueError(channel)
```

**When it's overkill:** if there's only one concrete implementation and no credible near-term second one, a factory function around a single constructor is an indirection layer with no payoff — just call `EmailNotifier()` directly (YAGNI).

## Abstract Factory

**Problem solved:** produce *families* of related objects that must be used together (a UI toolkit's buttons + checkboxes + menus per platform), guaranteeing the family stays consistent.

```python
class WidgetFactory(Protocol):
    def create_button(self) -> Button: ...
    def create_checkbox(self) -> Checkbox: ...

class DarkThemeFactory(WidgetFactory):
    def create_button(self): return DarkButton()
    def create_checkbox(self): return DarkCheckbox()
```

**When it's overkill:** when there's only one family, or the "family" members aren't actually required to be used together — you've added two layers of indirection (factory of factories) for a problem a single Factory Method already solves.

## Builder

**Problem solved:** construct a complex object step by step, especially one with many optional parameters, without a constructor that takes ten positional arguments where half are usually defaults.

```python
# Before: telescoping constructor — unreadable at the call site, easy to swap args
http_request = HttpRequest("GET", "https://api.example.com", None, {"Accept": "json"}, 30, True, None, 3)

# After: builder makes each optional field named and readable
request = (
    HttpRequestBuilder("GET", "https://api.example.com")
    .with_header("Accept", "json")
    .with_timeout(30)
    .with_retries(3)
    .build()
)
```

Contrast directly with the telescoping-constructor anti-pattern above: the failure mode it fixes is a caller passing `True` in the wrong positional slot and getting a silently wrong request with no error.

**When it's overkill:** an object with two or three straightforward fields doesn't need a builder — use keyword arguments or a plain dataclass. A builder pays off once you have several optional fields, validation that spans fields, or multiple valid construction paths.

## Prototype

**Problem solved:** create a new object by copying an existing configured instance instead of rebuilding it from scratch — useful when construction is expensive or when you need many near-identical variants of a complex, already-configured object.

```python
import copy

class DocumentTemplate:
    def clone(self):
        return copy.deepcopy(self)

base = DocumentTemplate()  # expensively configured once
variant = base.clone()
variant.title = "Q3 Report"
```

**When it's overkill:** if construction is cheap and objects don't share meaningful pre-configured state, cloning adds a layer (and deep-copy correctness bugs — shared mutable references copied shallow by accident) for no benefit over calling the constructor again.

## Related

- [01 — Design principles](01_design_principles.md) — Singleton's core problem is a DIP violation; Builder's core problem is an OCP/readability problem.
- [03 — Structural patterns](03_design_patterns_structural.md)
- [07 — Anti-patterns and code smells](07_anti_patterns_and_code_smells.md) — cargo-cult pattern overuse applies directly to Singleton and Abstract Factory.
