/*
Problem 19 — Generic Utilities (type parameters, constraints, generic
Result/Option, when generics hurt)

WHAT WE'RE BUILDING

A small, dependency-free generics toolkit of the kind that shows up as an
internal "util" or "collections" package in most real Go codebases once
they're past 1.18:

 1. Slice utilities (Map, Filter, Reduce, Keys/Values) parameterized over
    element type, so callers stop hand-writing the same 6-line loop with a
    different element type every time.
 2. A custom numeric/ordering constraint (not just the stdlib's `any` or
    `comparable`) used to write Max/Min/Sum once instead of once per numeric
    type.
 3. A generic Result[T] (success-value-or-error) and Option[T]
    (value-or-absent), the pattern languages like Rust bake into the
    language and Go historically approximated with (T, bool) or (T, error)
    return pairs.

# WHY THIS MATTERS IN REAL SYSTEMS

Before Go 1.18, "generic" code in Go meant either code generation
(`go generate` + text/template stamping out per-type files), `interface{}`
plus type assertions (loses compile-time type safety, costs a heap
allocation to box the value), or duplicating the function per concrete
type. Type parameters (Go 1.18+) let you write the algorithm once, keep
full compile-time type safety, and — for the common case of a concrete
instantiation — pay zero runtime cost beyond what the monomorphized
function would cost anyway (the compiler generates a concrete version per
instantiation, or shares one via GC-shape stenciling when types share an
underlying representation).

Result[T]/Option[T] matter for a different reason: Go's idiomatic
(T, error) and (T, bool) return pairs already express "success or failure"
and "present or absent" — but they don't compose. You can't easily chain
"parse this, then validate it, then transform it, stopping at the first
failure" without a chain of `if err != nil { return err }` at every step.
A Result/Option type gives you `.Map`, `.AndThen` to chain those steps
declaratively — useful in data pipelines and config-loading chains, while
still being avoidable (see the trade-offs note) in ordinary control flow
where a plain `if err != nil` is more idiomatic and more readable to the
next Go engineer who opens the file.

CONCEPTS COVERED

  - Type parameters: `func F[T any](...)`, multiple type parameters,
    inferred vs explicit instantiation (`F[int](...)`)
  - Constraint interfaces: `~int | ~int64 | ...` (the `~` "underlying type"
    approximation element), embedding `comparable`, combining constraints
  - Generic types: `type Result[T any] struct { ... }` and methods on them
    (a generic type's methods may NOT introduce new type parameters — see
    the pitfalls note on Map's signature)
  - Zero values under generics: `var zero T` when T is unknown
  - When generics hurt: monomorphization code bloat, worse error messages,
    reflection/`any`-based alternatives, and cases where a plain interface
    with methods is simply the better tool

# SPEC

Ordered (constraint): approximates the stdlib's `cmp.Ordered` — any type
whose underlying type is one of the built-in ordered kinds (integers,
floats, strings). Defined here by hand (not imported from `cmp`) so the
constraint's shape is visible.

Map[T, U any](s []T, f func(T) U) []U
  - Applies f to every element, returns a new slice of length len(s).
  - Nil input -> nil output (don't allocate an empty non-nil slice for nil
    input — mirrors how most stdlib slice functions treat nil).

Filter[T any](s []T, pred func(T) bool) []T
  - Returns a new slice containing only elements where pred(elem) is true.
  - Must not mutate s.

Reduce[T, A any](s []T, init A, f func(acc A, elem T) A) A
  - Left fold: acc starts at init, f is applied in order.

Keys[K comparable, V any](m map[K]V) []K
Values[K comparable, V any](m map[K]V) []V
  - Order is unspecified (map iteration order) — callers that need order
    must sort.

Max[T Ordered](s []T) (T, bool)
Min[T Ordered](s []T) (T, bool)
  - (zero, false) on empty input, otherwise the extreme value and true.

Sum[T Ordered](s []T) T
  - Sum of all elements; T's zero value for empty input.

Result[T any]
  - Ok(v T) Result[T], Err[T any](err error) Result[T]
  - (r Result[T]) IsOk() bool
  - (r Result[T]) Unwrap() T            — panics if r is an error result
  - (r Result[T]) UnwrapOr(fallback T) T
  - (r Result[T]) Error() error         — nil if IsOk()
  - ResultMap[T, U any](r Result[T], f func(T) U) Result[U] — free function,
    NOT a method (see pitfalls: a generic type's method set can't add a
    new type parameter U that isn't already bound on the receiver).
  - (r Result[T]) AndThen(f func(T) Result[T]) Result[T] — same-type chain,
    CAN be a method since it introduces no new type parameter.

Option[T any]
  - Some(v T) Option[T], None[T any]() Option[T]
  - (o Option[T]) IsSome() bool
  - (o Option[T]) Unwrap() T           — panics if o is None
  - (o Option[T]) UnwrapOr(fallback T) T
  - OptionMap[T, U any](o Option[T], f func(T) U) Option[U] — free function,
    same reason as ResultMap.

ACCEPTANCE CRITERIA

  - `go build ./19_generic_utilities/...` and `go vet ./19_generic_utilities/...`
    are clean.
  - `go test ./19_generic_utilities/solution/...` passes: Map/Filter/Reduce
    over at least two distinct element types (proving genuine
    parametricity, not one type in disguise), Max/Min/Sum over int and
    float64, Result and Option covering both the Ok/Some and Err/None
    branches, plus the documented panic behavior of Unwrap on failure.
*/
package genutil

// TODO: define Ordered as a constraint interface covering the built-in
// signed/unsigned integer kinds, floats, and strings, using `~kind` for
// each so that named types with these underlying types (e.g.
// `type Celsius float64`) still satisfy it.
type Ordered interface {
	~int
}

// TODO: implement Map — apply f to every element of s, returning a new
// slice. Nil input must produce nil output.
func Map[T, U any](s []T, f func(T) U) []U {
	panic("TODO: implement Map")
}

// TODO: implement Filter — keep only elements where pred returns true.
func Filter[T any](s []T, pred func(T) bool) []T {
	panic("TODO: implement Filter")
}

// TODO: implement Reduce — left fold over s starting from init.
func Reduce[T, A any](s []T, init A, f func(A, T) A) A {
	panic("TODO: implement Reduce")
}

// TODO: implement Keys — return the keys of m in unspecified order.
func Keys[K comparable, V any](m map[K]V) []K {
	panic("TODO: implement Keys")
}

// TODO: implement Values — return the values of m in unspecified order.
func Values[K comparable, V any](m map[K]V) []V {
	panic("TODO: implement Values")
}

// TODO: implement Max — return the largest element and true, or the zero
// value and false for an empty slice.
func Max[T Ordered](s []T) (T, bool) {
	panic("TODO: implement Max")
}

// TODO: implement Min — mirror Max.
func Min[T Ordered](s []T) (T, bool) {
	panic("TODO: implement Min")
}

// TODO: implement Sum — sum all elements; zero value for empty input.
func Sum[T Ordered](s []T) T {
	panic("TODO: implement Sum")
}

// Result represents either a successful value of type T or an error.
//
// TODO: give Result an unexported value T and error field.
type Result[T any] struct {
	// TODO: add fields
}

// TODO: implement Ok — construct a successful Result.
func Ok[T any](v T) Result[T] {
	panic("TODO: implement Ok")
}

// TODO: implement Err — construct a failed Result.
func Err[T any](err error) Result[T] {
	panic("TODO: implement Err")
}

// TODO: implement IsOk.
func (r Result[T]) IsOk() bool {
	panic("TODO: implement IsOk")
}

// TODO: implement Unwrap — panic if r is an error result.
func (r Result[T]) Unwrap() T {
	panic("TODO: implement Unwrap")
}

// TODO: implement UnwrapOr — return the held value, or fallback if r is an
// error result.
func (r Result[T]) UnwrapOr(fallback T) T {
	panic("TODO: implement UnwrapOr")
}

// TODO: implement Error — return the held error, or nil if r is Ok.
func (r Result[T]) Error() error {
	panic("TODO: implement Error")
}

// TODO: implement ResultMap as a free function (see the spec note on why
// this cannot be a method on Result[T]).
func ResultMap[T, U any](r Result[T], f func(T) U) Result[U] {
	panic("TODO: implement ResultMap")
}

// TODO: implement AndThen — if r is Ok, apply f and return its Result;
// otherwise propagate r's error unchanged.
func (r Result[T]) AndThen(f func(T) Result[T]) Result[T] {
	panic("TODO: implement AndThen")
}

// Option represents an optionally-present value of type T.
//
// TODO: give Option an unexported value T and present bool field.
type Option[T any] struct {
	// TODO: add fields
}

// TODO: implement Some.
func Some[T any](v T) Option[T] {
	panic("TODO: implement Some")
}

// TODO: implement None.
func None[T any]() Option[T] {
	panic("TODO: implement None")
}

// TODO: implement IsSome.
func (o Option[T]) IsSome() bool {
	panic("TODO: implement IsSome")
}

// TODO: implement Unwrap — panic if o is None.
func (o Option[T]) Unwrap() T {
	panic("TODO: implement Unwrap")
}

// TODO: implement UnwrapOr.
func (o Option[T]) UnwrapOr(fallback T) T {
	panic("TODO: implement UnwrapOr")
}

// TODO: implement OptionMap as a free function (same reason as ResultMap).
func OptionMap[T, U any](o Option[T], f func(T) U) Option[U] {
	panic("TODO: implement OptionMap")
}

/*
HINTS

  - The `~` in a constraint term means "any type whose *underlying* type is
    this one", not just the type itself — this is what lets a constraint
    satisfy named types like `type UserID int`, not only bare `int`.
  - `var zero T` is the idiomatic way to get T's zero value when T is a
    type parameter — you cannot write `T(0)` or `nil` generically since T
    might not be numeric or nilable.
  - A method on a generic type can only use the receiver's own type
    parameters — it cannot introduce a *new* one. `func (r Result[T]) Map[U any](...)`
    is not legal Go. That's exactly why ResultMap/OptionMap are free
    functions instead of methods: Map needs an independent U.
  - For Reduce, resist the urge to special-case an empty slice — the loop
    body naturally handles it (zero iterations, returns init unchanged).

COMMON PITFALLS

  - Forgetting the nil-in/nil-out contract for Map/Filter and instead
    always allocating with `make([]U, 0, len(s))` — this makes a nil input
    produce a non-nil empty slice, which breaks callers doing
    `if result == nil`-style checks and differs from how `slices.SortFunc`
    and friends treat nil.
  - Writing `type Ordered interface { int | float64 | string }` (no `~`)
    and then being surprised a domain type like `type Meters float64`
    doesn't satisfy it — without `~`, the constraint only matches the
    exact listed types, not types with that underlying type.
  - Calling `.Unwrap()` without checking `.IsOk()`/`.IsSome()` first in
    code that isn't a test/prototype — Unwrap panicking is a deliberate,
    documented contract (like Rust's `.unwrap()`), not something
    production request-handling code should reach for; prefer
    `UnwrapOr`/`AndThen` or an explicit `IsOk` check there.
  - Comparing Result[T] or Option[T] values with `==` when T isn't
    comparable (e.g. T is a slice or a func) — the struct itself may still
    be comparable or not depending on T, so don't rely on `==` on these
    types in generic code; add an explicit `Equals` if needed.

STRETCH GOALS

  - Add `ResultAndThen[T, U any](r Result[T], f func(T) Result[U]) Result[U]`
    as a free function alongside the same-type method AndThen, and notice
    it's strictly more general — the method only exists for ergonomic
    same-type chaining without needing a type argument at the call site.
  - Add a constraint `Numeric` that's `Ordered` minus `~string`, and
    implement `Average[T Numeric](s []T) float64`.
  - Add `Must[T any](r Result[T]) T` as sugar for `r.Unwrap()`.

WHEN GENERICS HURT (read this even if you implement everything above)

  - Monomorphization cost: the compiler generates a separate specialized
    version of a generic function per distinct instantiation shape
    (roughly, per distinct memory layout of the type arguments) — heavy
    generic code across many concrete types can measurably increase binary
    size and compile time compared to one `any`/interface-based
    implementation, though Go's GC-shape stenciling shares code across
    types with identical underlying representation (e.g. all pointer
    types) to limit this.
  - Worse error messages: a constraint violation three levels deep in a
    generic call chain produces a compiler error naming the instantiated
    types at every level, which is meaningfully harder to read than a
    concrete-type type error — this gets worse, not better, as you nest
    generic helpers calling generic helpers.
  - Not everything should be generic: if a function's logic genuinely
    differs per type (not just the type name), you want an interface with
    methods (dynamic dispatch), not a type parameter (static dispatch) —
    generics are for "same code, different type", interfaces are for
    "different code, same shape". Reaching for generics when you actually
    need polymorphic *behavior* is the most common generics misuse.
  - A generic type's methods can't add new type parameters (see the
    ResultMap/AndThen split above) — this pushes some APIs toward free
    functions, which reads less fluently at the call site
    (`ResultMap(r, f)` vs `r.Map(f)`) and is a real ergonomic cost, not
    just a rule to memorize.
  - Reflection-based or `any`-based code is still sometimes the right
    choice: e.g. `encoding/json` cannot be generic over "any struct" in a
    way that helps — it needs runtime type information for arbitrary,
    unknown-at-compile-time struct shapes, which is exactly what
    reflection is for and generics are not.
*/
