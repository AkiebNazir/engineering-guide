/*
Problem 18 — Dependency Injection & Layering (reference solution)

See explanation/18_dependency_injection_layering_explanation.go for the
full spec and rationale.

Note on package structure: the curriculum's fixed directory contract puts
one Go package per topic folder, so this file cannot demonstrate the
domain/adapter split as two separately-compiled packages the way a real
codebase would (domain package + a separate postgres/ or inmemory/
adapter package). Instead, the file is organized in three clearly labeled
sections — DOMAIN LAYER, ADAPTERS, and COMPOSITION ROOT — and the same
rule real hexagonal code follows still holds structurally: everything in
the DOMAIN LAYER section references only the port interfaces it defines,
never a concrete adapter type from the ADAPTERS section. In a multi-module
or multi-package project you would literally split this file at those
section boundaries into separate packages with no change to the logic.
*/
package layering

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

// ============================================================================
// DOMAIN LAYER — owns its port interfaces; must never import an adapter type.
// ============================================================================

// OrderStatus enumerates the lifecycle states of an Order.
type OrderStatus int

const (
	OrderPending OrderStatus = iota
	OrderConfirmed
	OrderCancelled
)

func (s OrderStatus) String() string {
	switch s {
	case OrderPending:
		return "pending"
	case OrderConfirmed:
		return "confirmed"
	case OrderCancelled:
		return "cancelled"
	default:
		return "unknown"
	}
}

// Order is the core domain entity.
type Order struct {
	ID         string
	CustomerID string
	TotalCents int64
	Status     OrderStatus
	PlacedAt   time.Time
}

// ErrOrderNotFound is the sentinel a repository port implementation should
// return (wrapped, if it adds context) when FindByID/UpdateStatus targets
// an ID that doesn't exist. Domain code and adapters share this sentinel
// via errors.Is instead of a nil-Order convention.
var ErrOrderNotFound = errors.New("order not found")

// OrderRepository is the port the service layer uses for persistence. Any
// adapter — a real database, an in-memory map, a test recorder — implements
// this interface; the domain layer never references an adapter's concrete
// type.
type OrderRepository interface {
	Save(ctx context.Context, o Order) error
	FindByID(ctx context.Context, id string) (Order, error)
	UpdateStatus(ctx context.Context, id string, status OrderStatus) error
}

// Clock is a narrow port for the service's only other external dependency:
// the current time. Injecting this (instead of calling time.Now() directly
// inside the service) makes PlaceOrder's PlacedAt deterministic in tests.
type Clock interface {
	Now() time.Time
}

// OrderService is the use-case/service layer. It depends only on the
// OrderRepository and Clock ports — never on any concrete adapter type.
// This is what makes it unit-testable without a real database and
// storage-agnostic by construction, not by convention.
type OrderService struct {
	repo  OrderRepository
	clock Clock

	mu      sync.Mutex
	nextSeq int64
}

// NewOrderService wires an OrderService against the given port
// implementations. This IS dependency injection in Go: a plain constructor
// accepting interfaces, called explicitly by whoever assembles the
// application — no container, no reflection, no struct tags.
//
// Panics if repo or clock is nil: a missing required dependency is a
// programming error the caller should fix, not a runtime condition to
// propagate as an error value through every subsequent call.
func NewOrderService(repo OrderRepository, clock Clock) *OrderService {
	if repo == nil {
		panic("layering: NewOrderService: repo must not be nil")
	}
	if clock == nil {
		panic("layering: NewOrderService: clock must not be nil")
	}
	return &OrderService{repo: repo, clock: clock}
}

// PlaceOrder creates a new pending Order for customerID and persists it.
func (s *OrderService) PlaceOrder(ctx context.Context, customerID string, totalCents int64) (Order, error) {
	if customerID == "" {
		return Order{}, fmt.Errorf("layering: PlaceOrder: customerID must not be empty")
	}
	if totalCents < 0 {
		return Order{}, fmt.Errorf("layering: PlaceOrder: totalCents must be >= 0, got %d", totalCents)
	}

	o := Order{
		ID:         s.nextID(),
		CustomerID: customerID,
		TotalCents: totalCents,
		Status:     OrderPending,
		PlacedAt:   s.clock.Now(),
	}
	if err := s.repo.Save(ctx, o); err != nil {
		return Order{}, fmt.Errorf("layering: PlaceOrder: save: %w", err)
	}
	return o, nil
}

// nextID generates a simple, monotonically increasing ID. A real service
// would inject an ID-generation port (e.g. backed by a UUID adapter); a
// counter keeps this exercise's domain layer free of any such dependency
// while still demonstrating the service owning its own ID scheme.
func (s *OrderService) nextID() string {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.nextSeq++
	return fmt.Sprintf("order-%d", s.nextSeq)
}

// ConfirmOrder transitions an order to OrderConfirmed. Confirming an
// already-confirmed order is treated as a no-op (idempotent from the
// caller's perspective); confirming a cancelled order is an error, since
// that would silently resurrect a cancelled order.
func (s *OrderService) ConfirmOrder(ctx context.Context, id string) error {
	return s.transition(ctx, id, OrderConfirmed)
}

// CancelOrder transitions an order to OrderCancelled. Symmetric to
// ConfirmOrder: cancelling an already-cancelled order is a no-op;
// cancelling a confirmed order is allowed (confirmed orders can still be
// cancelled, e.g. before fulfillment — a real system would gate this on
// more state, out of scope here).
func (s *OrderService) CancelOrder(ctx context.Context, id string) error {
	return s.transition(ctx, id, OrderCancelled)
}

func (s *OrderService) transition(ctx context.Context, id string, target OrderStatus) error {
	o, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return fmt.Errorf("layering: transition to %s: %w", target, err)
	}
	if o.Status == target {
		return nil // idempotent no-op
	}
	if o.Status == OrderCancelled && target == OrderConfirmed {
		return fmt.Errorf("layering: cannot confirm order %s: already cancelled", id)
	}
	if err := s.repo.UpdateStatus(ctx, id, target); err != nil {
		return fmt.Errorf("layering: transition to %s: %w", target, err)
	}
	return nil
}

// ============================================================================
// ADAPTERS — implement the domain's ports. May freely import the domain
// package's types (Order, OrderStatus, OrderRepository, Clock); the domain
// layer above must never import anything from this section.
// ============================================================================

// InMemoryOrderRepository is the "real" adapter for this exercise: a
// concurrency-safe, in-memory OrderRepository. Structurally, wiring it in
// place of a real *sql.DB-backed adapter is exactly the same shape a
// production Postgres adapter would take — same interface, same
// constructor pattern, different internals.
type InMemoryOrderRepository struct {
	mu     sync.RWMutex
	orders map[string]Order
}

// NewInMemoryOrderRepository constructs a ready-to-use, empty repository.
func NewInMemoryOrderRepository() *InMemoryOrderRepository {
	return &InMemoryOrderRepository{orders: make(map[string]Order)}
}

func (r *InMemoryOrderRepository) Save(ctx context.Context, o Order) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.orders[o.ID] = o
	return nil
}

func (r *InMemoryOrderRepository) FindByID(ctx context.Context, id string) (Order, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	o, ok := r.orders[id]
	if !ok {
		return Order{}, fmt.Errorf("in-memory repo: id %q: %w", id, ErrOrderNotFound)
	}
	return o, nil
}

func (r *InMemoryOrderRepository) UpdateStatus(ctx context.Context, id string, status OrderStatus) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	o, ok := r.orders[id]
	if !ok {
		return fmt.Errorf("in-memory repo: id %q: %w", id, ErrOrderNotFound)
	}
	o.Status = status
	r.orders[id] = o
	return nil
}

// RecordingOrderRepository is a test-only fake that wraps an
// InMemoryOrderRepository and additionally records every call made to it,
// so tests can assert on interaction order/count without a mocking
// framework. This is the second adapter the acceptance criteria require:
// swapping it in for InMemoryOrderRepository at the wiring call site is a
// one-line change (see the tests), and OrderService needs no changes at
// all because both satisfy OrderRepository.
type RecordingOrderRepository struct {
	inner *InMemoryOrderRepository

	mu    sync.Mutex
	calls []string
}

// NewRecordingOrderRepository constructs a fresh recording fake.
func NewRecordingOrderRepository() *RecordingOrderRepository {
	return &RecordingOrderRepository{inner: NewInMemoryOrderRepository()}
}

func (r *RecordingOrderRepository) record(call string) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.calls = append(r.calls, call)
}

// Calls returns a copy of every method call recorded so far, in order.
func (r *RecordingOrderRepository) Calls() []string {
	r.mu.Lock()
	defer r.mu.Unlock()
	out := make([]string, len(r.calls))
	copy(out, r.calls)
	return out
}

func (r *RecordingOrderRepository) Save(ctx context.Context, o Order) error {
	r.record("Save:" + o.ID)
	return r.inner.Save(ctx, o)
}

func (r *RecordingOrderRepository) FindByID(ctx context.Context, id string) (Order, error) {
	r.record("FindByID:" + id)
	return r.inner.FindByID(ctx, id)
}

func (r *RecordingOrderRepository) UpdateStatus(ctx context.Context, id string, status OrderStatus) error {
	r.record("UpdateStatus:" + id + ":" + status.String())
	return r.inner.UpdateStatus(ctx, id, status)
}

// SystemClock is the real Clock adapter, backed by time.Now().
type SystemClock struct{}

func (SystemClock) Now() time.Time { return time.Now() }

// FixedClock is a test Clock adapter that always returns the same instant,
// making time-dependent assertions in tests deterministic.
type FixedClock struct {
	At time.Time
}

func (f FixedClock) Now() time.Time { return f.At }

// ============================================================================
// COMPOSITION ROOT — the ONLY place that imports both the domain's ports
// and concrete adapter types together, and performs the actual wiring.
// In a real service this is main() or a small app.go; here it's a plain
// function so it can be called from a test or an example.
// ============================================================================

// RunExample wires a full OrderService against the real (in-memory)
// adapters and walks it through place -> confirm -> cancel, returning the
// final Order and any error encountered. This is the "no DI framework"
// wiring the exercise asks for: three explicit constructor calls, nothing
// implicit.
func RunExample(ctx context.Context) (Order, error) {
	repo := NewInMemoryOrderRepository()
	clock := SystemClock{}
	service := NewOrderService(repo, clock)

	o, err := service.PlaceOrder(ctx, "cust-1", 2599)
	if err != nil {
		return Order{}, fmt.Errorf("RunExample: place: %w", err)
	}
	if err := service.ConfirmOrder(ctx, o.ID); err != nil {
		return Order{}, fmt.Errorf("RunExample: confirm: %w", err)
	}
	final, err := repo.FindByID(ctx, o.ID)
	if err != nil {
		return Order{}, fmt.Errorf("RunExample: find: %w", err)
	}
	return final, nil
}

/*
BEST PRACTICES DEMONSTRATED

  - Ports (OrderRepository, Clock) are owned by the domain section and
    named for what the domain needs, not for what any particular database
    driver happens to offer — 3 methods, not 15.
  - Two structurally different adapters (InMemoryOrderRepository,
    RecordingOrderRepository) satisfy the same port with zero shared base
    type — Go's structural typing means "implements the interface" is the
    only contract, which is exactly what makes swapping them a one-line
    change at the composition root.
  - The service layer never calls time.Now() or generates its own
    wall-clock-dependent state directly — it goes through the Clock port,
    so PlaceOrder is fully deterministic under a FixedClock in tests.
  - Sentinel error (ErrOrderNotFound) shared between domain and adapters,
    wrapped with %w at the adapter boundary — ties directly into Problem
    17's error taxonomy: callers use errors.Is, never a nil-Order check.
  - Exactly one function (RunExample) constructs concrete adapter types;
    everything else in the domain section only ever sees interface types
    in its signatures.

ALTERNATIVE APPROACHES

  - A real multi-package layout would put the DOMAIN LAYER section in
    package `orders` (or `domain`) and each adapter in its own package
    (`orders/postgres`, `orders/inmemory`) importing `orders` — this file
    keeps everything in one package purely because of this curriculum's
    fixed one-package-per-topic directory contract; the dependency
    direction (adapters -> domain, never domain -> adapters) is identical
    either way and is what actually matters, not the file/package
    boundary.
  - Some codebases use a lightweight DI container (e.g. google/wire,
    which generates code at build time rather than using reflection) once
    the dependency graph grows past a handful of services — wire still
    produces the same explicit-constructor-call pattern shown here, just
    generated instead of hand-written, so understanding this manual
    version is a prerequisite either way.
  - RecordingOrderRepository here wraps InMemoryOrderRepository by
    composition; an alternative is a fully independent fake with its own
    minimal storage (e.g. a plain slice) when you want the fake to be
    usable even if InMemoryOrderRepository's behavior changes — a
    trade-off between fake fidelity and fake independence.
*/
