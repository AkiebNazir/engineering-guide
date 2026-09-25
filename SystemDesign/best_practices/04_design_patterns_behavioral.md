# Design Patterns — Behavioral

Behavioral patterns organize how objects communicate and share responsibility for a behavior. Each entry: problem solved → short example → when it's overkill.

## Strategy

**Problem solved:** select an algorithm's behavior at runtime by swapping an interchangeable strategy object, instead of branching on a type flag inside one function.

```python
class PricingStrategy(Protocol):
    def price(self, cart) -> float: ...

class RegularPricing(PricingStrategy):
    def price(self, cart): return cart.subtotal()

class BlackFridayPricing(PricingStrategy):
    def price(self, cart): return cart.subtotal() * 0.7

checkout = Checkout(strategy=BlackFridayPricing())
```

**When it's overkill:** one algorithm, no foreseeable second one — a plain function is simpler than an interface plus a class per variant.

## Observer

**Problem solved:** let a subject notify a dynamic set of dependents of state changes without the subject knowing their concrete types.

```python
class EventBus:
    def __init__(self): self._subscribers = []
    def subscribe(self, fn): self._subscribers.append(fn)
    def publish(self, event): 
        for fn in self._subscribers: fn(event)
```

**Relationship to pub/sub:** Observer is the in-process, synchronous, same-address-space version of the pub/sub messaging pattern. Pub/sub over a broker (Kafka, SNS/SQS) is the same idea decoupled across processes/services, with durability, backpressure, and delivery-guarantee concerns that in-memory Observer doesn't have. See `../building_blocks/09_messaging_and_streaming.md` for the distributed version.

**When it's overkill:** if there's exactly one listener and it will stay that way, a direct method call is clearer than a subscribe/notify indirection.

## Command

**Problem solved:** encapsulate a request (receiver + action + arguments) as an object, so it can be queued, logged, retried, or undone independently of the code that triggered it.

```python
class Command(Protocol):
    def execute(self) -> None: ...
    def undo(self) -> None: ...

class MoveCommand(Command):
    def __init__(self, shape, dx, dy):
        self._shape, self._dx, self._dy = shape, dx, dy
    def execute(self): self._shape.move(self._dx, self._dy)
    def undo(self): self._shape.move(-self._dx, -self._dy)
```

**Relationship to job queues and undo/redo:** a job queue's message is a serialized Command — "do this action later, possibly on another worker." Undo/redo stacks are literally a history of Command objects with a required inverse operation, which is why undo support forces every command to define `undo()` up front rather than bolting it on later.

**When it's overkill:** if you never need to queue, log, retry, or undo the action, wrapping a single function call in a command object is ceremony with no payoff — just call the function.

## State

**Problem solved:** let an object change its behavior when its internal state changes, by giving each state its own class with its own allowed transitions, instead of `if/elif` chains keyed off boolean flags.

```python
# Before: a pile of booleans that can enter invalid combinations
class Order:
    def __init__(self):
        self.is_paid = False
        self.is_shipped = False
        self.is_cancelled = False   # nothing stops is_shipped=True, is_cancelled=True

# After: an explicit state machine
class OrderState(Protocol):
    def pay(self, order) -> "OrderState": ...
    def ship(self, order) -> "OrderState": ...

class Pending(OrderState):
    def pay(self, order): return Paid()
    def ship(self, order): raise InvalidTransition

class Paid(OrderState):
    def ship(self, order): return Shipped()
```

The state-machine version makes illegal transitions (`ship()` before `pay()`) a raised error at the transition boundary instead of a silently inconsistent set of flags discovered later.

**When it's overkill:** two states and one transition don't need a class hierarchy — a single boolean is fine until a third state or a transition rule actually appears.

## Template Method

**Problem solved:** define the skeleton of an algorithm in a base class, deferring specific steps to subclasses, so the overall sequence can't be reordered incorrectly by a subclass.

```python
class DataImporter(ABC):
    def run(self):               # the fixed skeleton
        raw = self.fetch()
        parsed = self.parse(raw)
        self.save(parsed)

    @abstractmethod
    def fetch(self): ...
    @abstractmethod
    def parse(self, raw): ...
    def save(self, parsed): ...  # default, overridable
```

**When it's overkill:** if subclasses need to reorder or skip steps, Template Method's fixed skeleton fights them — Strategy (composing steps as objects) is more flexible when the sequence itself varies.

## Chain of Responsibility

**Problem solved:** pass a request along a chain of handlers, each deciding to handle it, pass it on, or short-circuit, without the sender knowing which handler will act.

```python
class Middleware(Protocol):
    def handle(self, request, next_handler): ...

class AuthMiddleware(Middleware):
    def handle(self, request, next_handler):
        if not request.is_authenticated():
            raise Unauthorized
        return next_handler(request)
```

**Name it directly:** an <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> middleware pipeline (auth → rate-limit → logging → handler) *is* Chain of Responsibility — recognizing this means you already understand how to reason about ordering, short-circuiting, and per-link failure handling in any middleware stack you build or review.

**When it's overkill:** a fixed, short sequence of two steps that will never grow is simpler as two direct function calls than as a generalized chain.

## Iterator

**Problem solved:** provide sequential access to a collection's elements without exposing its internal representation.

```python
class TreeIterator:
    def __iter__(self): return self
    def __next__(self):
        # walks the tree, yields next node
        ...
```

**When it's overkill:** in languages with built-in iteration protocols (Python's `for`, generators), hand-rolling an Iterator class instead of a generator function is usually unnecessary boilerplate.

## Mediator

**Problem solved:** centralize communication between a set of objects so they don't hold direct references to each other, reducing an all-to-all reference graph to a star topology through one mediator.

```python
class DialogMediator:
    def notify(self, sender, event):
        if event == "text_changed":
            self.submit_button.enable()
```

**When it's overkill:** with only two or three collaborators, a mediator is an extra hop for a relationship simple enough to wire directly.

## Memento

**Problem solved:** capture and externalize an object's internal state so it can be restored later, without violating its encapsulation (the memento is opaque to everyone but its originator).

```python
class EditorMemento:
    def __init__(self, content): self._content = content  # opaque outside Editor

class Editor:
    def save(self) -> EditorMemento: return EditorMemento(self._content)
    def restore(self, memento: EditorMemento): self._content = memento._content
```

**When it's overkill:** if snapshotting the whole object is cheap and encapsulation isn't actually at risk (e.g., a plain immutable dataclass), just keep a list of copies — Memento's ceremony buys you nothing extra.

## Visitor

**Problem solved:** add new operations over a stable set of object types without modifying those types, by having each type accept a visitor and double-dispatch to the right operation.

```python
class ShapeVisitor(Protocol):
    def visit_circle(self, c): ...
    def visit_square(self, s): ...

class Circle:
    def accept(self, visitor): return visitor.visit_circle(self)

class AreaVisitor(ShapeVisitor):
    def visit_circle(self, c): return 3.14159 * c.r ** 2
```

**When it's overkill:** if the set of types changes more often than the set of operations, Visitor inverts the pain in the wrong direction — every new type requires updating every visitor. Prefer a plain method on each type instead.

## Related

- [03 — Structural patterns](03_design_patterns_structural.md) — Decorator vs. Chain of Responsibility for pipeline-shaped problems.
- `../building_blocks/09_messaging_and_streaming.md` — Observer's distributed counterpart, pub/sub.
- [07 — Anti-patterns and code smells](07_anti_patterns_and_code_smells.md) — cargo-cult pattern overuse: the biggest risk after reading this file is reaching for a named pattern where a function would do.
