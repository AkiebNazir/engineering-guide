/*
Problem 18 — Dependency Injection & Layering (ports and adapters, no DI framework)

# WHAT WE'RE BUILDING

A small "orders" service laid out with hexagonal (ports-and-adapters)
architecture: a domain layer that defines what it needs as interfaces
("ports"), one real adapter implementing a port against a fake in-memory
store, one fake/in-memory adapter usable in tests, and explicit
constructor-based wiring in a main-style example — no reflection-based DI
container, no struct tags, no framework magic.

# WHY THIS MATTERS IN REAL SYSTEMS

"Dependency injection" in Go rarely means a framework (unlike Java/Spring
or .NET). It means a discipline:

  - Accept interfaces, return structs — a constructor's parameters should
    be the narrowest interfaces the function needs (not concrete types,
    not a giant "AllRepositories" god-interface), and it should return a
    concrete struct type (callers that need an interface define their own
    narrow one at the point of use — see Go proverb: "the bigger the
    interface, the weaker the abstraction").
  - The domain layer OWNS its port interfaces. The adapter package depends
    on the domain package to implement the domain's interface — never the
    other way around. This is what makes it "hexagonal": business logic
    has zero import-time dependency on any specific database driver, HTTP
    client, or message queue; swapping Postgres for an in-memory fake
    means writing a new adapter, touching zero domain code.
  - Wiring (constructing the real adapters and injecting them into the
    domain/service layer) happens in exactly one place — typically `main`
    or a small `wire.go`/`app.go` — and is the ONLY place that imports
    both the domain interfaces and the concrete adapters together.

Get this wrong (concrete types threaded through business logic, or
services reaching into a global database handle) and every unit test for
business logic needs a real database; get it right and testing the domain
layer needs zero I/O.

# CONCEPTS COVERED

  - A domain port interface (`OrderRepository`) owned by the domain
    package, expressing exactly the operations the service layer needs.
  - A real adapter (`InMemoryOrderRepository` — stands in for "the real
    Postgres/SQL adapter" without requiring an actual DB for this
    exercise; structurally identical to how a real `*sql.DB`-backed
    adapter would be wired) implementing the port.
  - A second, deliberately different fake adapter
    (`RecordingOrderRepository`) used only in tests, demonstrating why
    "accept an interface" makes substituting test doubles trivial without
    a mocking framework.
  - A service/use-case layer (`OrderService`) that depends only on the
    port interface, never on either adapter's concrete type.
  - Explicit constructor wiring (`NewOrderService(repo OrderRepository, ...)
    `) assembled in a `main`-style `RunExample` function — no DI container.

# SPEC

	// domain.go — owned by the domain layer.
	type Order struct { ID string; CustomerID string; TotalCents int64; Status OrderStatus }
	type OrderStatus int // OrderPending, OrderConfirmed, OrderCancelled

	// OrderRepository is the port: the ONLY way the service layer talks to
	// storage. Domain package owns this interface; adapters implement it.
	type OrderRepository interface {
	    Save(ctx context.Context, o Order) error
	    FindByID(ctx context.Context, id string) (Order, error)
	    UpdateStatus(ctx context.Context, id string, status OrderStatus) error
	}

	// Clock is a second, tiny port — demonstrates that ports aren't only
	// for storage; anything the domain needs from the outside world
	// (time, IDs, external APIs) should be a narrow interface too, so
	// tests can inject a fixed clock instead of depending on time.Now().
	type Clock interface { Now() time.Time }

	// OrderService is the use-case layer: depends on ports only.
	type OrderService struct { /* unexported fields: repo OrderRepository, clock Clock
	func NewOrderService(repo OrderRepository, clock Clock) *OrderService
	func (s *OrderService) PlaceOrder(ctx context.Context, customerID string, totalCents int64) (Order, error)
	func (s *OrderService) ConfirmOrder(ctx context.Context, id string) error
	func (s *OrderService) CancelOrder(ctx context.Context, id string) error

	// adapters (solution file):
	//   InMemoryOrderRepository   — the "real" adapter for this exercise
	//   RecordingOrderRepository  — a test-only fake that also records
	//                               every call made to it, for asserting
	//                               interaction order/count in tests
	//   SystemClock               — real Clock using time.Now()
	//   FixedClock                — test Clock returning a fixed time

# ACCEPTANCE CRITERIA

  - The domain/service package imports NEITHER adapter's package (compile
    this as separate packages and verify: domain has zero knowledge of
    "in-memory" or "recording" adapters).
  - OrderService's exported surface takes/returns only domain types and
    the port interfaces — no adapter-specific type appears in any exported
    signature.
  - Swapping InMemoryOrderRepository for RecordingOrderRepository in the
    wiring code requires changing exactly one line (the constructor call),
    nothing in OrderService.
  - A RunExample-style function demonstrates wiring a full OrderService
    with real adapters, placing/confirming/cancelling an order, with
    explicit constructor calls (no globals, no init()-based registration).
*/
package layering

import (
	"context"
)

// OrderStatus enumerates the lifecycle states of an Order.
// TODO: define as an int-based enum: OrderPending, OrderConfirmed,
// OrderCancelled, with a String() method.
type OrderStatus int

// Order is the core domain entity. TODO: fields ID, CustomerID string;
// TotalCents int64; Status OrderStatus; PlacedAt time.Time.
type Order struct {
	// TODO: fields
}

// OrderRepository is the port the service layer uses for persistence. The
// domain package owns this interface — adapters (in a different package,
// in the solution) implement it; domain code never imports an adapter
// package.
//
// TODO: define methods:
//
//	Save(ctx context.Context, o Order) error
//	FindByID(ctx context.Context, id string) (Order, error)
//	UpdateStatus(ctx context.Context, id string, status OrderStatus) error
type OrderRepository interface {
	// TODO: methods
}

// Clock is a narrow port for the service's only other external dependency:
// the current time. Narrow ports like this make tests deterministic
// (inject a FixedClock) without needing a mocking framework.
//
// TODO: method Now() time.Time.
type Clock interface {
	// TODO: methods
}

// OrderService is the use-case/service layer. It depends only on ports
// (OrderRepository, Clock), never on any concrete adapter type — that's
// what makes it independently unit-testable and storage-agnostic.
//
// TODO: unexported fields repo OrderRepository, clock Clock.
type OrderService struct {
	// TODO: fields
}

// NewOrderService wires an OrderService against the given port
// implementations. This is "dependency injection" in Go: a plain
// constructor accepting interfaces, called explicitly by whoever assembles
// the application (see solution's RunExample) — no container, no
// reflection.
//
// TODO: implement. Consider validating repo/clock are non-nil and
// panicking (a nil dependency is a programming error, not a runtime
// condition to recover from) — document that choice either way.
func NewOrderService(repo OrderRepository, clock Clock) *OrderService {
	panic("TODO: implement NewOrderService")
}

// PlaceOrder creates a new pending Order for customerID and persists it via
// the repository port.
// TODO: implement: build an Order (generate/derive an ID — TODO: decide
// how without importing a UUID adapter into the domain layer; a monotonic
// counter or the Clock port's Now().UnixNano() are acceptable within this
// exercise's scope), set Status to OrderPending, PlacedAt from s.clock,
// call s.repo.Save.
func (s *OrderService) PlaceOrder(ctx context.Context, customerID string, totalCents int64) (Order, error) {
	panic("TODO: implement OrderService.PlaceOrder")
}

// ConfirmOrder transitions an order to OrderConfirmed.
// TODO: implement via s.repo.UpdateStatus, after checking current state
// with FindByID (decide and document: is confirming an already-confirmed
// order an error or a no-op?).
func (s *OrderService) ConfirmOrder(ctx context.Context, id string) error {
	panic("TODO: implement OrderService.ConfirmOrder")
}

// CancelOrder transitions an order to OrderCancelled.
// TODO: implement, symmetric to ConfirmOrder.
func (s *OrderService) CancelOrder(ctx context.Context, id string) error {
	panic("TODO: implement OrderService.CancelOrder")
}

/*
HINTS

  - Put OrderRepository and Clock in the SAME package as OrderService
    (this file's package, `layering`) — the domain package owning its
    ports is the entire point of hexagonal architecture; adapters live in
    a separate package (or, for this exercise, lower in the same
    solution.go file but still logically "the adapter side") and import
    `layering` to implement its interfaces, never the reverse.
  - Resist the urge to make OrderRepository return `(*Order, error)` with
    a nil-on-not-found convention — prefer returning a zero Order plus a
    sentinel/typed "not found" error (tie-in to Problem 17's error
    taxonomy) so callers use errors.Is/As instead of nil checks.
  - A constructor panicking on a nil required dependency (vs. returning an
    error) is a legitimate, common Go choice for "this is a programming
    error, not a recoverable runtime condition" — document whichever you
    pick and be consistent across constructors in the same codebase.

COMMON PITFALLS

  - Defining the port interface in the ADAPTER's package instead of the
    domain's — inverts the dependency direction (now domain must import
    the adapter package to reference the interface type), defeating the
    entire purpose of ports-and-adapters.
  - A "fat" repository interface with 15 methods because it mirrors every
    SQL query the real database happens to support, instead of the 3-4
    operations THIS service actually calls — makes every fake/mock
    implementation of the port far larger than necessary and signals the
    interface was designed adapter-first instead of consumer-first.
  - Wiring logic (constructing adapters, calling NewOrderService) leaking
    into business-logic files instead of staying isolated in one
    composition root (main/RunExample) — makes it impossible to tell, at a
    glance, what the full dependency graph of the app is.
  - Using a global/package-level `var db *sql.DB` instead of injecting it —
    works fine until you need two instances (tests running in parallel,
    multi-tenant configs) and discover everything secretly shares state.

STRETCH GOALS

  - Add a second port, `EventPublisher`, and have PlaceOrder publish a
    "order placed" event (wire it, for the exercise, to Problem 16's
    Bus[T] as one implementation and a no-op adapter as another) —
    demonstrates a service depending on two independent ports at once.
  - Add a `Decorator` adapter that wraps any OrderRepository and adds
    structured logging around every call, without OrderService or the
    wrapped adapter knowing it's there — shows ports-and-adapters
    composing (an adapter can itself depend on the same port it
    implements).
  - Write a table-driven test suite for OrderService that runs unchanged
    against BOTH adapters (InMemory and Recording) by taking the
    repository as a table field — proves the service is adapter-agnostic
    by construction, not just by convention.
*/
