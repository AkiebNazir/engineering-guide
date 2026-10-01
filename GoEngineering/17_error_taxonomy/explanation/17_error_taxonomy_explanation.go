/*
Problem 17 — Error Taxonomy (sentinel vs typed errors, wrapping, HTTP/gRPC mapping)

WHAT WE'RE BUILDING

A small domain error taxonomy for a hypothetical "accounts" service, and the
plumbing to move errors cleanly across three boundaries every backend
service has to cross:

 1. Internal call chain — one layer wraps another layer's error with %w,
    adding context without losing the ability to inspect the original
    cause.
 2. HTTP boundary — a domain error becomes an HTTP status code + JSON body.
 3. gRPC boundary — the same domain error becomes a gRPC status code +
    message, using google.golang.org/grpc/codes and .../status.

# WHY THIS MATTERS IN REAL SYSTEMS

Two extremes both fail in production:
  - "Just return errors.New(...) everywhere": callers can't distinguish
    "not found" from "permission denied" from "internal bug" without
    string-matching the message, which breaks the moment the message
    wording changes.
  - "Every error is its own exported type with its own package": every
    caller needs an ever-growing type switch, and errors.Is/As stop being
    useful because nothing shares a common sentinel or common marker
    interface.

A good taxonomy picks a SMALL number of categories (kinds), uses sentinel
errors for singleton conditions (ErrNotFound) and a typed error for
conditions that carry data (ValidationError with a field name), wraps
consistently with %w at each layer boundary so `errors.Is`/`errors.As`
keep working through arbitrarily many layers of wrapping, and maps kinds
(not individual error values) to transport status codes exactly once, at
the transport boundary — never scattered through business logic.

CONCEPTS COVERED

  - Sentinel errors (package-level `var Err... = errors.New(...)`) for
    conditions with no extra data.
  - A typed error (struct implementing `error`) for conditions that carry
    structured data (e.g. which field failed validation).
  - A `Kind` enum that both error flavors expose via a common
    `Kind() Kind` method, so transport-boundary code maps ONE small
    enum, not N concrete error types.
  - Wrapping with `%w` (fmt.Errorf) at each layer, and unwrapping with
    `errors.Is`, `errors.As`, and `errors.Unwrap`.
  - `errors.Join` for aggregating independent errors (e.g. multiple
    validation failures) into one error that still satisfies
    `errors.Is`/`errors.As` for any of its members.
  - Mapping domain Kind -> `net/http` status constant, and Kind ->
    `google.golang.org/grpc/codes.Code` + `status.Error`.

SPEC

	type Kind int
	    KindNotFound, KindInvalidArgument, KindAlreadyExists,
	    KindPermissionDenied, KindUnavailable, KindInternal (at minimum)

	// Sentinel errors for singleton conditions.
	var ErrNotFound = errors.New("...")
	var ErrAlreadyExists = errors.New("...")
	var ErrPermissionDenied = errors.New("...")

	// ValidationError is a typed error carrying which field(s) failed.
	type ValidationError struct { Field string; Reason string }
	func (e *ValidationError) Error() string
	func (e *ValidationError) Kind() Kind { return KindInvalidArgument }

	// DomainError wraps any of the above (or an internal error) with a
	// Kind and an optional wrapped cause, giving every error in the
	// taxonomy a uniform way to expose its Kind regardless of whether it
	// originated as a sentinel or a typed error.
	type DomainError struct { Kind Kind; Op string; Err error }
	func (e *DomainError) Error() string
	func (e *DomainError) Unwrap() error   // enables errors.Is/As through it
	func KindOf(err error) Kind           // walks the chain to find a Kind

	// Transport mapping — exactly one function per transport, called only
	// at the boundary (an HTTP handler / a gRPC interceptor or handler),
	// never from business logic.
	func HTTPStatus(err error) int
	func GRPCStatus(err error) error       // returns a *status.Status-backed
	                                        // error via status.Error(code, msg)

ACCEPTANCE CRITERIA

  - errors.Is(err, ErrNotFound) succeeds even after the sentinel has been
    wrapped through 2+ layers with fmt.Errorf("...: %w", ...) and then
    wrapped again in a *DomainError.
  - errors.As(err, &validationErr) succeeds the same way for the typed
    ValidationError.
  - errors.Join of multiple ValidationErrors still lets errors.As extract
    at least one of them, and KindOf on the joined error reports
    KindInvalidArgument.
  - HTTPStatus and GRPCStatus agree in spirit (e.g. NotFound -> 404 and
    codes.NotFound; InvalidArgument -> 400 and codes.InvalidArgument;
    PermissionDenied -> 403 and codes.PermissionDenied; unknown/internal
    defaults to 500 and codes.Internal) without the business logic that
    produced the error ever importing net/http or grpc/codes.
*/
package apperrors

import "errors"

// Kind classifies a domain error into a small, closed set of categories
// that transport boundaries map to status codes. Add new Kinds sparingly —
// every Kind must be meaningful to a caller deciding how to react (retry?
// surface to the user? page an operator?), not just descriptive.
//
// TODO: define Kind as an int-based enum with a String() method, and the
// constants KindUnknown, KindNotFound, KindInvalidArgument,
// KindAlreadyExists, KindPermissionDenied, KindUnavailable, KindInternal.
type Kind int

// TODO: sentinel errors for singleton, data-free conditions.
// var (
// 	ErrNotFound         = errors.New("...")
// 	ErrAlreadyExists    = errors.New("...")
// 	ErrPermissionDenied = errors.New("...")
// )

// ValidationError is a typed error for a condition that carries data (which
// field, why). TODO: add fields Field, Reason string; implement Error()
// string and Kind() Kind (should return KindInvalidArgument).
type ValidationError struct {
	// TODO: fields
}

func (e *ValidationError) Error() string {
	panic("TODO: implement ValidationError.Error")
}

// DomainError is the uniform wrapper every layer should produce when
// crossing a package boundary with an error: it pins down a Kind
// (defaulting sensibly if the wrapped error doesn't declare one) and an Op
// describing what was being attempted, while preserving the original error
// via Unwrap so errors.Is/As keep working through it.
//
// TODO: fields Kind Kind, Op string, Err error.
type DomainError struct {
	// TODO: fields
}

func (e *DomainError) Error() string {
	panic("TODO: implement DomainError.Error")
}

// TODO: implement Unwrap() error returning e.Err, so errors.Is/As recurse
// through a *DomainError automatically.
func (e *DomainError) Unwrap() error {
	panic("TODO: implement DomainError.Unwrap")
}

// KindOf walks err's chain (via errors.As against an interface with a
// Kind() Kind method, and via type assertion against *DomainError) to
// determine its Kind, defaulting to KindInternal if none is found.
//
// TODO: implement. Hint: define a local interface
//
//	type kinder interface{ Kind() Kind }
//
// and use errors.As(err, &someKinder) — but errors.As needs a concrete
// or interface *pointer* whose pointed-to type implements error; for an
// interface target the idiom is a bit different, see errors.As docs
// ("target must be a non-nil pointer... or implement error").
func KindOf(err error) Kind {
	panic("TODO: implement KindOf")
}

// HTTPStatus maps err's Kind to a net/http status constant. TODO:
// implement using KindOf and a switch; default to http.StatusInternalServerError.
func HTTPStatus(err error) int {
	panic("TODO: implement HTTPStatus")
}

// GRPCStatus maps err's Kind to a gRPC status error via
// google.golang.org/grpc/codes and .../status. TODO: implement using
// KindOf and a switch; default to codes.Internal. Use status.Error(code,
// err.Error()) (or status.Errorf) to build the returned error.
func GRPCStatus(err error) error {
	panic("TODO: implement GRPCStatus")
}

var _ = errors.New // keep errors imported for the stub; remove once used directly

/*
HINTS

  - Keep Kind a plain `int` enum, not a string — string enums invite
    accidental typos that compile fine and silently fall through to a
    default case; int enums plus `go vet`'s exhaustive-switch-adjacent
    tooling (or a manual "default: panic" during development) catch
    unhandled cases earlier.
  - `errors.As` needs a pointer to a type that implements `error`, OR
    (since Go's errors.As also supports it) a pointer to an interface
    type. `var k kinder; errors.As(err, &k)` works when `kinder` is an
    interface — that's the cleanest way to ask "does anything in this
    chain expose a Kind() Kind method" without hardcoding every concrete
    type.
  - `fmt.Errorf("op: %w", err)` wraps exactly one error per call. To wrap
    two independent causes, use `errors.Join(err1, err2)` (Go 1.20+) —
    note %w with Join wraps ALL its arguments so errors.Is/As checks
    against ANY of them.
  - Never let net/http or grpc/codes/status types leak into your domain
    or business-logic packages — only the HTTP handler package and the
    gRPC service package should import HTTPStatus/GRPCStatus's targets.
    This file's own package (apperrors) importing grpc/codes is the ONE
    sanctioned exception, because mapping IS this package's job.

COMMON PITFALLS

  - Comparing errors with `==` or string-matching `err.Error()` instead of
    `errors.Is`/`errors.As` — breaks the instant a message wording changes
    or another layer adds a wrap.
  - Forgetting `Unwrap() error` on a wrapping type — without it,
    errors.Is/As stop at that type and never see the sentinel or typed
    error underneath, even though the wrapping type holds a reference to
    it.
  - Mapping status codes from the error's *string message* instead of its
    Kind — fragile and gets out of sync the moment someone tweaks wording.
  - Re-wrapping the same error multiple times with the same Op at every
    layer ("repo: repo: service: get user: not found") instead of adding
    distinct context per layer — makes logs noisy without adding
    information.

STRETCH GOALS

  - Add a `StackTrace() []uintptr` (via `runtime.Callers`) to DomainError,
    captured only for KindInternal errors (the ones worth debugging;
    NotFound/InvalidArgument stack traces are usually noise).
  - Add an `As`-friendly `MultiValidationError` built on top of
    errors.Join specifically for aggregating N ValidationErrors from a
    single request, with a helper to extract all of them (errors.As only
    gives you one at a time from a Join).
  - Write a table-driven test asserting HTTPStatus/GRPCStatus agree for
    every Kind, so adding a Kind without updating both mappings fails CI.
*/
