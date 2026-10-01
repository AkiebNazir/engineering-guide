// Package ifaces is the reference solution for Problem 33 — Advanced
// Interfaces & Composition.
package ifaces

import (
	"errors"
	"fmt"
	"io"
	"net/http"
	"reflect"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
)

// ============================================================================
// 1. The nil interface trap
// ============================================================================

// ValidationError reports an invalid field.
type ValidationError struct{ Field string }

func (e *ValidationError) Error() string { return "invalid " + e.Field }

// ValidateBad has the most famous bug in Go. It declares a *ValidationError
// variable, leaves it nil on success, and returns it as an `error`. The
// returned interface holds (type=*ValidationError, value=nil) — its TYPE word
// is set, so `err != nil` is TRUE even though the pointer inside is nil.
func ValidateBad(name string) error {
	var verr *ValidationError
	if name == "" {
		verr = &ValidationError{Field: "name"}
	}
	return verr // BUG: typed nil becomes a non-nil error
}

// Validate is the fix: return the untyped nil literal on the success path,
// and keep concrete error types out of return signatures unless callers
// genuinely need them (they can still use errors.As).
func Validate(name string) error {
	if name == "" {
		return &ValidationError{Field: "name"}
	}
	return nil
}

// IsNil reports whether v is a nil interface OR an interface holding a nil
// pointer, map, slice, channel or func. Needing this in application code is
// a smell — fix the producer instead — but it's handy at API boundaries
// that accept `any` from untrusted callers.
func IsNil(v any) bool {
	if v == nil {
		return true
	}
	rv := reflect.ValueOf(v)
	switch rv.Kind() {
	case reflect.Pointer, reflect.Map, reflect.Slice, reflect.Chan, reflect.Func, reflect.Interface:
		return rv.IsNil()
	}
	return false
}

// ============================================================================
// 2. Decorating an interface by embedding it in a struct
// ============================================================================

// ErrNotFound is returned by Store.Get for a missing key.
var ErrNotFound = errors.New("ifaces: not found")

// Store is a small consumer-side interface: define interfaces where they are
// USED, with only the methods that consumer needs.
type Store interface {
	Get(key string) (string, error)
	Set(key, value string) error
	Delete(key string) error
}

// MemStore is an in-memory Store.
type MemStore struct {
	mu sync.RWMutex
	m  map[string]string
}

// Compile-time proof that *MemStore implements Store. Costs nothing at run
// time (the blank var is never allocated) and turns "forgot a method" or
// "changed a signature" into a compile error at the type's definition rather
// than a confusing error at some distant call site.
var _ Store = (*MemStore)(nil)

// NewMemStore returns an empty store. Returning the concrete *MemStore
// ("accept interfaces, return structs") lets callers use any extra methods
// and lets the CALLER decide which interface they need.
func NewMemStore() *MemStore { return &MemStore{m: map[string]string{}} }

func (s *MemStore) Get(key string) (string, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	v, ok := s.m[key]
	if !ok {
		return "", fmt.Errorf("%w: %q", ErrNotFound, key)
	}
	return v, nil
}

func (s *MemStore) Set(key, value string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.m[key] = value
	return nil
}

func (s *MemStore) Delete(key string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.m, key)
	return nil
}

// CountingStore wraps any Store and counts Get calls and misses.
//
// Embedding the Store INTERFACE promotes all of its methods, so CountingStore
// satisfies Store while only overriding Get. Adding a method to Store later
// requires no change here. The trap: if the embedded Store is nil, every
// non-overridden method panics with a nil pointer dereference — hence the
// constructor.
type CountingStore struct {
	Store
	gets   atomic.Int64
	misses atomic.Int64
}

var _ Store = (*CountingStore)(nil)

// NewCountingStore decorates s.
func NewCountingStore(s Store) *CountingStore {
	if s == nil {
		panic("ifaces: NewCountingStore(nil)")
	}
	return &CountingStore{Store: s}
}

// Get shadows the promoted Store.Get; c.Store.Get reaches the wrapped one.
func (c *CountingStore) Get(key string) (string, error) {
	c.gets.Add(1)
	v, err := c.Store.Get(key)
	if errors.Is(err, ErrNotFound) {
		c.misses.Add(1)
	}
	return v, err
}

// Stats returns (gets, misses).
func (c *CountingStore) Stats() (int64, int64) { return c.gets.Load(), c.misses.Load() }

// ============================================================================
// 3. Wrappers and optional interfaces
// ============================================================================

// StatusRecorder captures the status code written by a handler — the most
// common piece of HTTP middleware there is.
//
// Embedding http.ResponseWriter promotes Header/Write/WriteHeader, but ONLY
// those: the static type StatusRecorder does not have Flush, Hijack or
// ReadFrom even when the wrapped writer does. So `w.(http.Flusher)` in a
// streaming handler silently fails behind this middleware. Since Go 1.20,
// http.ResponseController looks for an Unwrap() http.ResponseWriter method
// and walks through wrappers to find those capabilities.
type StatusRecorder struct {
	http.ResponseWriter
	Status int
}

// WriteHeader records the status before passing it on.
func (s *StatusRecorder) WriteHeader(code int) {
	if s.Status == 0 {
		s.Status = code
	}
	s.ResponseWriter.WriteHeader(code)
}

// Write records an implicit 200 if WriteHeader was never called.
func (s *StatusRecorder) Write(p []byte) (int, error) {
	if s.Status == 0 {
		s.Status = http.StatusOK
	}
	return s.ResponseWriter.Write(p)
}

// Unwrap exposes the wrapped writer to http.ResponseController.
func (s *StatusRecorder) Unwrap() http.ResponseWriter { return s.ResponseWriter }

// RecordStatus is middleware that reports each response's status to observe.
func RecordStatus(next http.Handler, observe func(status int)) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		rec := &StatusRecorder{ResponseWriter: w}
		next.ServeHTTP(rec, r)
		observe(rec.Status)
	})
}

// CountingWriter counts bytes written through it.
type CountingWriter struct {
	W io.Writer
	N int64
}

func (c *CountingWriter) Write(p []byte) (int, error) {
	n, err := c.W.Write(p)
	c.N += int64(n)
	return n, err
}

// ============================================================================
// 4. Type switches
// ============================================================================

// Describe renders v for logs. Case ORDER matters: the first matching case
// wins, so a type implementing both error and fmt.Stringer is described by
// whichever case comes first. Errors go first because their message is what
// an operator needs.
func Describe(v any) string {
	switch x := v.(type) {
	case nil:
		return "nil"
	case error:
		return "error: " + x.Error()
	case fmt.Stringer:
		return "stringer: " + x.String()
	case string:
		return fmt.Sprintf("string(%d): %s", len(x), x)
	case []byte:
		return fmt.Sprintf("bytes(%d)", len(x))
	case int, int8, int16, int32, int64:
		// In a multi-type case x keeps the interface type (any), not int.
		return fmt.Sprintf("int: %v", x)
	case map[string]any:
		keys := make([]string, 0, len(x))
		for k := range x {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		return "object{" + strings.Join(keys, ",") + "}"
	default:
		return fmt.Sprintf("other: %T", x)
	}
}

// ============================================================================
// 5. Method sets
// ============================================================================

// Counter has one pointer-receiver method and one value-receiver method.
type Counter struct{ n int }

// Inc must mutate, so it has a pointer receiver.
func (c *Counter) Inc() { c.n++ }

// Value only reads.
func (c Counter) Value() int { return c.n }

// Incrementer is satisfied by *Counter but NOT by Counter.
type Incrementer interface{ Inc() }

// AsIncrementer reports whether v's dynamic type has Inc in its method set.
//
//	method set of Counter  = { Value }            (value receivers only)
//	method set of *Counter = { Value, Inc }       (value + pointer receivers)
//
// A value stored in an interface is not addressable, so Go cannot take its
// address to call a pointer method on it — that's why Counter{} doesn't
// satisfy Incrementer even though `c.Inc()` compiles on an addressable
// variable c.
func AsIncrementer(v any) (Incrementer, bool) {
	i, ok := v.(Incrementer)
	return i, ok
}

// ============================================================================
// 6. Embedding is not inheritance
// ============================================================================

// Greeter formats greetings.
type Greeter struct{ Prefix string }

// Name is what Greeter thinks it is called.
func (Greeter) Name() string { return "greeter" }

// Greet calls g.Name(). Because Go has no virtual dispatch on embedded
// structs, this ALWAYS calls Greeter.Name, even when Greeter is embedded in a
// type that defines its own Name.
func (g Greeter) Greet() string { return g.Prefix + "hello from " + g.Name() }

// Service embeds Greeter, promoting Greet and Name, and shadows Name.
type Service struct {
	Greeter
	ID string
}

// Name shadows the promoted Greeter.Name for callers of Service.
func (s Service) Name() string { return "service " + s.ID }

// ============================================================================
// 7. Interfaces as map keys
// ============================================================================

// CountKeys counts occurrences of each key. The map key type is `any`, which
// compiles for anything — but hashing a key whose DYNAMIC type is not
// comparable (slice, map, func) panics at run time. CountKeys converts that
// panic into an error.
func CountKeys(keys ...any) (counts map[any]int, err error) {
	counts = map[any]int{}
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("ifaces: unhashable key: %v", r)
		}
	}()
	for _, k := range keys {
		counts[k]++
	}
	return counts, nil
}
