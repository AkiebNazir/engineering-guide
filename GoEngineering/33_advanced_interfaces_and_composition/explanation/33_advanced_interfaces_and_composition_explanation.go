/*
Problem 33 — Advanced Interfaces & Composition (interface internals, the
typed-nil trap, method sets, embedding, decorators, optional interfaces)

WHAT WE'RE BUILDING

A package of small types, each isolating one interface rule that trips up
experienced engineers — with a test that makes the rule visible at run time:

 1. ValidateBad / Validate / IsNil — the "nil error that isn't nil" bug
    and its fix.
 2. Store, MemStore, CountingStore — consumer-side interfaces, compile-time
    implementation assertions, and a decorator that embeds an interface to
    override one method.
 3. StatusRecorder + RecordStatus — HTTP middleware whose wrapper hides
    optional interfaces (http.Flusher), and the Unwrap convention that
    http.ResponseController uses to see through it.
 4. Describe — a type switch where case order matters.
 5. Counter / AsIncrementer — method sets of T vs *T.
 6. Greeter / Service — embedding promotes methods but is not inheritance:
    there is no virtual dispatch.
 7. CountKeys — `any` map keys that compile but panic at run time.

WHY THIS MATTERS IN REAL SYSTEMS

Interfaces are Go's main tool for decoupling — every repository layer,
HTTP middleware chain, test fake and plugin boundary is built on them.
The bugs they cause are subtle because they compile:

  - A handler returns a typed-nil *APIError as `error`; every successful
    request is logged as a failure and returns 500.
  - Logging middleware wraps http.ResponseWriter; server-sent events and
    gzip streaming silently stop flushing in production.
  - A struct embeds an interface field that a constructor forgot to set;
    the service panics on the first call to a method nobody overrode.
  - Someone "overrides" a method on an embedding struct expecting the
    embedded type's other methods to call it, like Java; they don't.

MENTAL MODEL 1 — WHAT AN INTERFACE VALUE IS

    non-empty interface (e.g. error, io.Writer) = iface
    ┌──────────────┬──────────────┐
    │ tab  *itab   │ data pointer │
    └──────┬───────┴──────┬───────┘
           │              └──▶ the concrete value (or a pointer to a copy)
           ▼
    ┌──────────────────────────────────┐
    │ itab: interface type             │
    │       concrete (dynamic) type    │  computed once per (iface, type)
    │       fun[0] = (*T).Write        │  pair and cached
    │       fun[1] = ...               │
    └──────────────────────────────────┘

    empty interface (any) = eface: { _type *type, data pointer }

  - A method call through an interface loads fun[i] and makes an indirect
    call. It cannot be inlined unless the compiler can prove the dynamic
    type (devirtualization, helped by PGO). Measured here (Apple M4 Pro,
    go1.26) with the concrete method marked //go:noinline so only the
    dispatch differs: BenchmarkCallConcrete 1.81 ns/op vs
    BenchmarkCallInterface 1.83 ns/op — the indirect call itself is noise.
    The real cost of interfaces on hot paths is what they PREVENT: inlining,
    and keeping values on the stack (escape analysis must assume a value
    passed through an interface may escape).
  - Storing a non-pointer value in an interface usually copies it to the
    heap (small integers and zero-size values are special-cased).
  - x == y on interfaces compares type words, then values — which panics
    if the dynamic type is not comparable (slices, maps, funcs).

MENTAL MODEL 2 — THE TYPED-NIL TRAP

    var p *ValidationError = nil
    var err error = p

    err ──▶ ┌──────────────────────────┬─────────┐
            │ type: *ValidationError   │ nil     │     err != nil  →  TRUE
            └──────────────────────────┴─────────┘

    var err error = nil

    err ──▶ ┌──────────────────────────┬─────────┐
            │ type: nil                │ nil     │     err == nil  →  true
            └──────────────────────────┴─────────┘

An interface is nil only when BOTH words are nil. Rules:
  - Return the literal `nil` for "no error"; never return a nil concrete
    pointer through an interface-typed result.
  - Don't declare `var err *MyError` and return it. Declare `var err error`.
  - errors.As still recovers the concrete type for callers who need it.

MENTAL MODEL 3 — METHOD SETS

    type Counter struct{ n int }
    func (c *Counter) Inc()        // pointer receiver
    func (c Counter)  Value() int  // value receiver

    ┌─────────────┬───────────────────────┬──────────────────────────────┐
    │ type        │ method set            │ satisfies Incrementer{Inc}?  │
    ├─────────────┼───────────────────────┼──────────────────────────────┤
    │ Counter     │ { Value }             │ no                           │
    │ *Counter    │ { Value, Inc }        │ yes                          │
    └─────────────┴───────────────────────┴──────────────────────────────┘

`c.Inc()` compiles on a Counter VARIABLE because the variable is
addressable and Go rewrites it to (&c).Inc(). A value inside an interface is
not addressable (it may be a private copy), so Go refuses to let Counter
satisfy an interface that needs Inc — otherwise Inc would mutate a hidden copy
and the caller would never see the change.

Guideline: if any method needs a pointer receiver, give all methods pointer
receivers, and pass the type around as *T.

MENTAL MODEL 4 — COMPILE-TIME ASSERTIONS

	var _ Store = (*MemStore)(nil)
	var _ http.Handler = (*API)(nil)
	var _ io.ReadWriteCloser = (*Conn)(nil)

A typed nil pointer converted to the interface, assigned to the blank
identifier: zero run-time cost, and "missing method Delete" is reported at
the type's own definition when someone changes the interface — instead of at
a distant call site, or not at all if the only use is via reflection or DI.

MENTAL MODEL 5 — EMBEDDING IS NOT INHERITANCE

    type Greeter struct{ Prefix string }
    func (Greeter) Name() string          { return "greeter" }
    func (g Greeter) Greet() string       { return g.Prefix + "hello from " + g.Name() }

    type Service struct { Greeter; ID string }
    func (s Service) Name() string        { return "service " + s.ID }

    s.Name()          → Service.Name      "service billing"   (shadows)
    s.Greeter.Name()  → Greeter.Name      "greeter"           (explicit)
    s.Greet()         → Greeter.Greet(s.Greeter)
                          └─ g.Name() → Greeter.Name   "hello from greeter"
                                         NOT Service.Name

Embedding is syntactic sugar for a named field plus automatically generated
forwarding methods. The embedded value doesn't know it is embedded, so its
methods can never call the outer type's methods. When you need that
"template method" behaviour, pass an interface in explicitly.

Selector rules: the shallowest depth wins; two promoted methods with the
same name at the same depth are ambiguous — a compile error only when you
actually USE that selector.

MENTAL MODEL 6 — DECORATING BY EMBEDDING AN INTERFACE

    type CountingStore struct {
        Store                 ◀── interface field: promotes Get/Set/Delete
        gets, misses atomic.Int64
    }
    func (c *CountingStore) Get(k string) (string, error) {   ◀── override one
        c.gets.Add(1)
        return c.Store.Get(k)                                  ◀── delegate
    }

    caller ──Set──▶ CountingStore ──(promoted)──────────▶ MemStore.Set
    caller ──Get──▶ CountingStore.Get ──c.Store.Get──────▶ MemStore.Get

Great for wrappers, test fakes that only care about one method, and
instrumentation. The trap: a zero CountingStore{} has a nil Store, and every
promoted method panics — always construct through a function that checks.

MENTAL MODEL 7 — WRAPPERS HIDE OPTIONAL INTERFACES

Many stdlib APIs check for EXTRA methods with a type assertion:
io.Copy looks for io.WriterTo / io.ReaderFrom; net/http handlers look for
http.Flusher, http.Hijacker. A wrapper's static type only has the methods
it declares or promotes from the embedded INTERFACE type:

    net/http's writer:  { Header, Write, WriteHeader, Flush, Hijack, ReadFrom, ... }
            ▲ embedded as http.ResponseWriter
    StatusRecorder:     { Header, Write, WriteHeader, Unwrap }     ← no Flush

    w.(http.Flusher)                    → false: streaming silently buffers
    http.NewResponseController(w).Flush() → calls Unwrap() repeatedly until it
                                           finds a Flusher → works (Go 1.20+)

Same convention as errors.Unwrap: expose `Unwrap() http.ResponseWriter` on
every ResponseWriter wrapper you write.

TYPE SWITCHES

	switch x := v.(type) {
	case nil:                 // v is a nil interface
	case error:               // interface cases match anything implementing them
	case fmt.Stringer:
	case int, int64:          // multi-type case: x stays `any`
	default:
	}

  - Cases are tried IN ORDER; the first match wins. A type implementing
    both error and fmt.Stringer is handled by whichever case comes first.
  - A typed nil pointer matches its type's cases (and `error`), not
    `case nil` — calling methods on it may then dereference nil.
  - Prefer errors.As over switching on concrete error types: it sees
    through wrapping.

DESIGN GUIDELINES

    | Guideline                                   | Why                                        |
    |---------------------------------------------|--------------------------------------------|
    | Define interfaces where they're CONSUMED    | producer can't know which subset you need  |
    | Keep them small (1-3 methods)               | io.Reader-sized interfaces compose         |
    | Accept interfaces, return concrete types    | callers keep extra methods, pick their own |
    | Don't create an interface for one impl      | "interface pollution"; add it when needed  |
    | Use generics for same-code-any-type         | containers, algorithms: no boxing          |
    | Use interfaces for different-behaviour      | storage backends, transports, strategies   |

SPEC

	type ValidationError struct{ Field string }   // Error() = "invalid " + Field
	func ValidateBad(name string) error           // lesson: returns typed nil on success
	func Validate(name string) error              // returns literal nil on success
	func IsNil(v any) bool                        // nil interface or nil ptr/map/slice/chan/func

	var ErrNotFound error
	type Store interface { Get(key string) (string, error); Set(key, value string) error; Delete(key string) error }
	type MemStore struct{ ... };  func NewMemStore() *MemStore;  var _ Store = (*MemStore)(nil)
	type CountingStore struct{ Store; ... }
	func NewCountingStore(s Store) *CountingStore  // panics on nil
	func (c *CountingStore) Get(key string) (string, error)
	func (c *CountingStore) Stats() (gets, misses int64)

	type StatusRecorder struct{ http.ResponseWriter; Status int }
	    WriteHeader records first status; Write implies 200; Unwrap() http.ResponseWriter
	func RecordStatus(next http.Handler, observe func(status int)) http.Handler
	type CountingWriter struct{ W io.Writer; N int64 }

	func Describe(v any) string
	    nil → "nil"; error → "error: "+msg; fmt.Stringer → "stringer: "+s;
	    string → "string(<bytes>): s"; []byte → "bytes(n)"; signed ints → "int: v";
	    map[string]any → "object{sorted,keys}"; else "other: %T"

	type Counter struct{ n int };  (*Counter).Inc();  (Counter).Value() int
	type Incrementer interface{ Inc() }
	func AsIncrementer(v any) (Incrementer, bool)

	type Greeter struct{ Prefix string };  (Greeter).Name() = "greeter";
	    (Greeter).Greet() = Prefix + "hello from " + g.Name()
	type Service struct{ Greeter; ID string };  (Service).Name() = "service " + ID

	func CountKeys(keys ...any) (map[any]int, error)   // recover unhashable-key panic into error

ACCEPTANCE CRITERIA

  - `go test -v ./33_advanced_interfaces_and_composition/solution/...` passes.
  - A streaming handler behind RecordStatus flushes three events via
    http.ResponseController while `w.(http.Flusher)` reports false.
  - reflect reports 1 method for Counter and 2 for *Counter.

HOW TO RUN

	go test -v ./33_advanced_interfaces_and_composition/solution/...
	go test -run Example -v ./33_advanced_interfaces_and_composition/solution/...
	go test -run '^$' -bench Call -benchmem ./33_advanced_interfaces_and_composition/solution/...

HINTS

  - IsNil: reflect.ValueOf(v).Kind() then IsNil() for nil-able kinds only —
    IsNil panics on an int.
  - CountingStore.Get: errors.Is(err, ErrNotFound) — MemStore wraps it.
  - StatusRecorder.Write: if Status == 0, set 200 before delegating.
  - CountKeys: named results + defer/recover to turn the panic into err.

COMMON PITFALLS

  - Returning a concrete error pointer through an `error` result.
  - Mixing value and pointer receivers on one type, then being surprised
    the value doesn't satisfy an interface.
  - Forgetting `var _ Iface = (*T)(nil)` and finding out from a DI
    container at startup.
  - Wrapping ResponseWriter (or net.Conn, io.Reader) without preserving
    optional capabilities.
  - Type-switching on concrete error types instead of errors.As.
  - Huge "god" interfaces mirroring a struct's whole method list.

STRETCH GOALS

  - Make CountingWriter implement io.ReaderFrom by delegating when W does,
    and measure io.Copy with and without that fast path.
  - Write a middleware that also preserves http.Hijacker via Unwrap and
    test a WebSocket-style upgrade through it.
  - Replace Store with a generic Store[K comparable, V any] and compare the
    ergonomics.
*/

package ifaces

import (
	"errors"
	"io"
	"net/http"
)

// ============================================================================
// 1. The nil interface trap
// ============================================================================

// ValidationError reports an invalid field.
type ValidationError struct{ Field string }

func (e *ValidationError) Error() string { return "invalid " + e.Field }

// ValidateBad returns a typed nil on success. Lesson only — keep as is.
func ValidateBad(name string) error {
	var verr *ValidationError
	if name == "" {
		verr = &ValidationError{Field: "name"}
	}
	return verr
}

// Validate must return a true nil interface on success.
func Validate(name string) error {
	// TODO
	panic("not implemented")
}

// IsNil reports whether v is nil or holds a nil pointer/map/slice/chan/func.
func IsNil(v any) bool {
	// TODO: v == nil, else reflect.ValueOf(v) Kind switch + IsNil.
	panic("not implemented")
}

// ============================================================================
// 2. Decorators
// ============================================================================

// ErrNotFound is returned by Store.Get for a missing key.
var ErrNotFound = errors.New("ifaces: not found")

// Store is a small consumer-side interface.
type Store interface {
	Get(key string) (string, error)
	Set(key, value string) error
	Delete(key string) error
}

// MemStore is an in-memory Store.
type MemStore struct {
	// TODO: mu sync.RWMutex; m map[string]string
}

// TODO: add the compile-time assertion that *MemStore implements Store.

// NewMemStore returns an empty store.
func NewMemStore() *MemStore {
	// TODO
	panic("not implemented")
}

func (s *MemStore) Get(key string) (string, error) {
	// TODO: wrap ErrNotFound with the key using %w.
	panic("not implemented")
}

func (s *MemStore) Set(key, value string) error {
	// TODO
	panic("not implemented")
}

func (s *MemStore) Delete(key string) error {
	// TODO
	panic("not implemented")
}

// CountingStore wraps a Store and counts Get calls and misses.
type CountingStore struct {
	Store
	// TODO: gets, misses atomic.Int64
}

// NewCountingStore decorates s.
func NewCountingStore(s Store) *CountingStore {
	// TODO: panic on nil.
	panic("not implemented")
}

// Get overrides the promoted Get.
func (c *CountingStore) Get(key string) (string, error) {
	// TODO
	panic("not implemented")
}

// Stats returns (gets, misses).
func (c *CountingStore) Stats() (int64, int64) {
	// TODO
	panic("not implemented")
}

// ============================================================================
// 3. Wrappers and optional interfaces
// ============================================================================

// StatusRecorder captures the status code written by a handler.
type StatusRecorder struct {
	http.ResponseWriter
	Status int
}

// WriteHeader records the status.
func (s *StatusRecorder) WriteHeader(code int) {
	// TODO
	panic("not implemented")
}

// Write records an implicit 200.
func (s *StatusRecorder) Write(p []byte) (int, error) {
	// TODO
	panic("not implemented")
}

// TODO: add Unwrap() http.ResponseWriter so http.ResponseController can find Flush.

// RecordStatus reports each response's status to observe.
func RecordStatus(next http.Handler, observe func(status int)) http.Handler {
	// TODO
	panic("not implemented")
}

// CountingWriter counts bytes written through it.
type CountingWriter struct {
	W io.Writer
	N int64
}

func (c *CountingWriter) Write(p []byte) (int, error) {
	// TODO
	panic("not implemented")
}

// ============================================================================
// 4. Type switches
// ============================================================================

// Describe renders v for logs. See SPEC for the exact formats and case order.
func Describe(v any) string {
	// TODO
	panic("not implemented")
}

// ============================================================================
// 5. Method sets
// ============================================================================

// Counter has one pointer-receiver and one value-receiver method.
type Counter struct{ n int }

// Inc increments.
func (c *Counter) Inc() { c.n++ }

// Value reads.
func (c Counter) Value() int { return c.n }

// Incrementer is satisfied by *Counter but not Counter.
type Incrementer interface{ Inc() }

// AsIncrementer reports whether v implements Incrementer.
func AsIncrementer(v any) (Incrementer, bool) {
	// TODO: comma-ok type assertion.
	panic("not implemented")
}

// ============================================================================
// 6. Embedding is not inheritance
// ============================================================================

// Greeter formats greetings.
type Greeter struct{ Prefix string }

// Name is what Greeter thinks it is called.
func (Greeter) Name() string { return "greeter" }

// Greet calls g.Name().
func (g Greeter) Greet() string { return g.Prefix + "hello from " + g.Name() }

// Service embeds Greeter and shadows Name.
type Service struct {
	Greeter
	ID string
}

// Name shadows Greeter.Name.
func (s Service) Name() string {
	// TODO: return "service " + s.ID
	panic("not implemented")
}

// ============================================================================
// 7. Interfaces as map keys
// ============================================================================

// CountKeys counts keys, converting an unhashable-key panic into an error.
func CountKeys(keys ...any) (counts map[any]int, err error) {
	// TODO
	panic("not implemented")
}
