// Package genutil is a small, dependency-free generics toolkit: slice/map
// utilities parameterized over element type, a hand-written ordering
// constraint, and a generic Result[T]/Option[T] pair modeled on the
// value-or-error / value-or-absent pattern common in languages with sum
// types. See the explanation file's header for the full design rationale
// and the "when generics hurt" discussion.
package genutil

// Ordered is a custom constraint (deliberately hand-rolled instead of
// importing the stdlib's cmp.Ordered, so its shape is visible here): any
// type whose underlying type is one of the built-in ordered kinds. The `~`
// before each term means "or any named type whose underlying type is
// this" — without it, a domain type like `type UserID int` would NOT
// satisfy the constraint, only bare `int` would.
type Ordered interface {
	~int | ~int8 | ~int16 | ~int32 | ~int64 |
		~uint | ~uint8 | ~uint16 | ~uint32 | ~uint64 | ~uintptr |
		~float32 | ~float64 |
		~string
}

// Map applies f to every element of s, returning a new slice of the same
// length. Nil input produces nil output — this mirrors how most stdlib
// slice functions (e.g. slices.Clone) treat nil, and matters to callers
// that branch on `result == nil`.
func Map[T, U any](s []T, f func(T) U) []U {
	if s == nil {
		return nil
	}
	out := make([]U, len(s))
	for i, v := range s {
		out[i] = f(v)
	}
	return out
}

// Filter returns a new slice containing only the elements of s for which
// pred returns true. s itself is never mutated.
func Filter[T any](s []T, pred func(T) bool) []T {
	if s == nil {
		return nil
	}
	out := make([]T, 0, len(s))
	for _, v := range s {
		if pred(v) {
			out = append(out, v)
		}
	}
	return out
}

// Reduce left-folds s into a single accumulated value, starting from init
// and applying f in order. An empty s returns init unchanged — the loop
// naturally handles this without a special case.
func Reduce[T, A any](s []T, init A, f func(A, T) A) A {
	acc := init
	for _, v := range s {
		acc = f(acc, v)
	}
	return acc
}

// Keys returns the keys of m. Order is unspecified (Go map iteration
// order) — callers needing a stable order must sort the result themselves.
func Keys[K comparable, V any](m map[K]V) []K {
	out := make([]K, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	return out
}

// Values returns the values of m. Order is unspecified, same caveat as
// Keys.
func Values[K comparable, V any](m map[K]V) []V {
	out := make([]V, 0, len(m))
	for _, v := range m {
		out = append(out, v)
	}
	return out
}

// Max returns the largest element of s and true, or the zero value and
// false if s is empty.
func Max[T Ordered](s []T) (T, bool) {
	var zero T
	if len(s) == 0 {
		return zero, false
	}
	max := s[0]
	for _, v := range s[1:] {
		if v > max {
			max = v
		}
	}
	return max, true
}

// Min mirrors Max.
func Min[T Ordered](s []T) (T, bool) {
	var zero T
	if len(s) == 0 {
		return zero, false
	}
	min := s[0]
	for _, v := range s[1:] {
		if v < min {
			min = v
		}
	}
	return min, true
}

// Sum returns the sum of all elements of s; the zero value for empty
// input. Built directly rather than via Reduce to avoid the closure
// allocation Reduce's function-value argument would otherwise cost on
// this hot a primitive (see problem 22 for when that overhead actually
// matters in practice — here it's cheap insurance, not a measured fix).
func Sum[T Ordered](s []T) T {
	var total T
	for _, v := range s {
		total += v
	}
	return total
}

// Result represents either a successful value of type T or an error. The
// zero value of Result[T] is an error result with a nil error (treat it as
// "not ok, no error set" — always construct via Ok/Err rather than a bare
// Result[T]{}).
type Result[T any] struct {
	val T
	err error
}

// Ok constructs a successful Result holding v.
func Ok[T any](v T) Result[T] {
	return Result[T]{val: v}
}

// Err constructs a failed Result holding err. err must not be nil — a nil
// err here would make IsOk() report false while Error() returns nil,
// silently breaking the "IsOk() == (Error() == nil)" invariant callers
// rely on.
func Err[T any](err error) Result[T] {
	return Result[T]{err: err}
}

// IsOk reports whether r holds a value rather than an error.
func (r Result[T]) IsOk() bool {
	return r.err == nil
}

// Unwrap returns the held value. It panics if r is an error result — this
// is a deliberate, documented "trust me" escape hatch (mirroring Rust's
// .unwrap()) for call sites that have already checked IsOk(), or for
// tests/prototypes; production request-handling code should prefer
// UnwrapOr or an explicit IsOk check instead of risking the panic.
func (r Result[T]) Unwrap() T {
	if r.err != nil {
		panic("genutil: Unwrap called on error Result: " + r.err.Error())
	}
	return r.val
}

// UnwrapOr returns the held value, or fallback if r is an error result.
func (r Result[T]) UnwrapOr(fallback T) T {
	if r.err != nil {
		return fallback
	}
	return r.val
}

// Error returns the held error, or nil if r is Ok.
func (r Result[T]) Error() error {
	return r.err
}

// ResultMap transforms a successful Result[T] into a Result[U] via f,
// propagating an error result unchanged. This is a free function, not a
// method on Result[T], because a generic type's method set cannot
// introduce a type parameter beyond those already bound on the receiver
// (T) — U is new, so `func (r Result[T]) Map[U any](...)` is simply not
// legal Go. AndThen below, by contrast, stays same-type (T -> T) and so
// can be a method.
func ResultMap[T, U any](r Result[T], f func(T) U) Result[U] {
	if r.err != nil {
		return Err[U](r.err)
	}
	return Ok(f(r.val))
}

// AndThen chains a same-type-producing step: if r is Ok, f is applied to
// the held value and its Result returned; otherwise r's error propagates
// unchanged and f is never called. Unlike ResultMap, this can be a method
// because it introduces no new type parameter (T -> T).
func (r Result[T]) AndThen(f func(T) Result[T]) Result[T] {
	if r.err != nil {
		return r
	}
	return f(r.val)
}

// Option represents an optionally-present value of type T. The zero value
// of Option[T] is None (present == false), which is a genuinely useful
// property — unlike Result[T], a bare Option[T]{} is safe and meaningful.
type Option[T any] struct {
	val     T
	present bool
}

// Some constructs a present Option holding v.
func Some[T any](v T) Option[T] {
	return Option[T]{val: v, present: true}
}

// None constructs an absent Option. T must be given explicitly at call
// sites where it can't be inferred, e.g. `None[int]()`.
func None[T any]() Option[T] {
	return Option[T]{}
}

// IsSome reports whether o holds a value.
func (o Option[T]) IsSome() bool {
	return o.present
}

// Unwrap returns the held value. It panics if o is None — same contract
// and same caveats as Result.Unwrap.
func (o Option[T]) Unwrap() T {
	if !o.present {
		panic("genutil: Unwrap called on None Option")
	}
	return o.val
}

// UnwrapOr returns the held value, or fallback if o is None.
func (o Option[T]) UnwrapOr(fallback T) T {
	if !o.present {
		return fallback
	}
	return o.val
}

// OptionMap transforms a present Option[T] into an Option[U] via f,
// propagating None unchanged. Free function for the same reason as
// ResultMap: U is a type parameter Option[T]'s method set cannot host.
func OptionMap[T, U any](o Option[T], f func(T) U) Option[U] {
	if !o.present {
		return None[U]()
	}
	return Some(f(o.val))
}

/*
BEST PRACTICES

  - Default to `any` for type parameters that don't need operations beyond
    "store and return this value" (Map, Filter, Result, Option) — only
    reach for a real constraint (Ordered, comparable) when the function
    body actually needs an operator (`<`, `==`) the constraint provides.
    An over-constrained generic function is less reusable for no benefit.
  - Keep Result/Option's fields unexported and construct only through
    Ok/Err/Some/None — this preserves the "IsOk() == (Error() == nil)" and
    "IsSome() == present" invariants that Unwrap/UnwrapOr rely on; a caller
    building a Result[T]{} literal directly could violate them.
  - Prefer UnwrapOr / AndThen / ResultMap / OptionMap over Unwrap in
    non-test code — Unwrap's panic is meant for cases you've already proven
    can't fail (post-IsOk-check) or genuinely-fatal startup paths, not
    routine request handling where an idiomatic `if err != nil` is clearer
    to the next reader anyway.
  - Nil-in/nil-out for Map/Filter, not "always allocate" — matches the
    convention slices.Clone and friends already established, and avoids
    surprising callers that branch on `x == nil`.

ALTERNATIVE APPROACHES / TRADE-OFFS

  - The stdlib's `cmp.Ordered` (Go 1.21+, package `cmp`) and `slices`/
    `maps` packages (Map/Filter/Reduce aren't in stdlib, but Keys/Values-
    equivalents and Max/Min-equivalents via `slices.Max`/`slices.Min` are)
    already cover a good chunk of this file in production code — this
    package reimplements the shape for the learning value of writing the
    constraint and the generic functions yourself; in a real codebase,
    prefer the stdlib versions where they exist and only add local
    generics for what's missing (Map/Filter/Reduce, Result/Option).
  - Result[T]/Option[T] vs plain (T, error)/(T, bool): the plain pair is
    more idiomatic Go and is what the standard library uses everywhere —
    reach for Result/Option only when you're building an actual chain of
    fallible steps (a small parsing/validation pipeline, a config-loading
    chain) where `.AndThen`/`.Map` composition earns its keep; for a single
    fallible call, `v, err := f()` remains clearer to the next reader.
  - `any` + type assertions/reflection instead of generics: still the
    right tool when the set of concrete types truly isn't known at compile
    time (JSON unmarshaling into arbitrary shapes, a plugin system) —
    generics require every instantiation's type to be known at compile
    time, reflection doesn't.

TESTING / FAILURE MODES

  - The test file exercises Map/Filter/Reduce over two distinct element
    types (int and a custom string-based type) to prove genuine
    parametricity rather than "generic in name, monomorphic in practice."
  - Max/Min/Sum are tested over both int and float64 to exercise the
    Ordered constraint across integer and floating-point underlying kinds,
    plus the empty-slice (zero value, false) path.
  - Result and Option are tested on both branches (Ok/Err, Some/None)
    including that Unwrap panics on the failure branch — verified via
    a recover()-based subtest rather than skipped, since "panics on
    misuse" is part of the documented contract, not an oversight.
*/
