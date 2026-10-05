/*
Problem 17 — Error Taxonomy (reference solution)

See explanation/17_error_taxonomy_explanation.go for the full spec and
rationale. This file implements it.
*/
package apperrors

import (
	"errors"
	"fmt"
	"net/http"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// Kind classifies a domain error into a small, closed set of categories.
// Transport boundaries map Kind (never a concrete error type or message
// string) to a status code.
type Kind int

const (
	KindUnknown Kind = iota
	KindNotFound
	KindInvalidArgument
	KindAlreadyExists
	KindPermissionDenied
	KindUnavailable
	KindInternal
)

func (k Kind) String() string {
	switch k {
	case KindNotFound:
		return "not_found"
	case KindInvalidArgument:
		return "invalid_argument"
	case KindAlreadyExists:
		return "already_exists"
	case KindPermissionDenied:
		return "permission_denied"
	case KindUnavailable:
		return "unavailable"
	case KindInternal:
		return "internal"
	default:
		return "unknown"
	}
}

// Sentinel errors for singleton, data-free conditions. Use errors.Is to
// test for these anywhere in a wrapped chain.
var (
	ErrNotFound         = errors.New("resource not found")
	ErrAlreadyExists    = errors.New("resource already exists")
	ErrPermissionDenied = errors.New("permission denied")
	ErrUnavailable      = errors.New("dependency unavailable")
)

// ValidationError is a typed error for a condition that carries structured
// data: which field failed, and why. Use errors.As to extract it from a
// wrapped chain when a caller needs the field name (e.g. to build a
// field-level error response), not just "something was invalid".
type ValidationError struct {
	Field  string
	Reason string
}

func (e *ValidationError) Error() string {
	return fmt.Sprintf("validation: field %q: %s", e.Field, e.Reason)
}

// Kind reports this error's taxonomy Kind. Implementing this method (not
// just Error()) is what lets KindOf recognize ValidationError without a
// type switch over every concrete error type in the codebase.
func (e *ValidationError) Kind() Kind { return KindInvalidArgument }

// kinder is the interface KindOf looks for via errors.As. Any error type —
// sentinel-wrapping or typed — that implements it participates in the
// taxonomy without KindOf needing to know its concrete type.
type kinder interface {
	Kind() Kind
}

// DomainError is the uniform wrapper a layer produces when crossing a
// package boundary with an error it wants to annotate: which operation was
// being attempted (Op), what Kind it is, and the original error (Err) is
// preserved via Unwrap so errors.Is/As keep working through it.
type DomainError struct {
	Kind Kind
	Op   string
	Err  error
}

func (e *DomainError) Error() string {
	if e.Err == nil {
		return fmt.Sprintf("%s: %s", e.Op, e.Kind)
	}
	return fmt.Sprintf("%s: %v", e.Op, e.Err)
}

// Unwrap exposes the wrapped cause so errors.Is/errors.As recurse through
// a *DomainError automatically — without this method, an errors.Is check
// for a sentinel wrapped inside e.Err would stop here and always fail.
func (e *DomainError) Unwrap() error { return e.Err }

// Note: DomainError intentionally does NOT implement `kinder` (it can't —
// its exported field is itself named Kind, and Go forbids a field and a
// method sharing one name on the same type). KindOf below special-cases
// *DomainError directly instead, which also gives a *DomainError's Kind
// priority over any Kind the wrapped cause might separately report — the
// layer that built the DomainError gets the final say (e.g. forcing
// KindUnavailable over a raw "connection refused" error that itself
// reports nothing, or overriding a lower layer's classification).

// Wrap builds a *DomainError, recording which operation failed and why.
// This is the one function business logic should call at a package
// boundary instead of bare fmt.Errorf("...: %w", err) when the error
// needs a Kind attached (fmt.Errorf is still fine for pure context
// annotation that doesn't change the Kind, since KindOf walks through it).
func Wrap(op string, kind Kind, err error) error {
	if err == nil {
		return nil
	}
	return &DomainError{Op: op, Kind: kind, Err: err}
}

// KindOf walks err's chain to determine its Kind:
//  1. If a *DomainError is anywhere in the chain, use its explicit Kind —
//     the layer that built it gets the final say, even overriding a
//     Kind the wrapped cause would otherwise report.
//  2. Otherwise, if anything in the chain implements `kinder`
//     (ValidationError), use the Kind it reports.
//  3. Otherwise, fall back to matching well-known sentinels with
//     errors.Is.
//  4. Otherwise, KindInternal — an error nobody classified is exactly the
//     kind of error worth surfacing as 500/Internal rather than guessing.
func KindOf(err error) Kind {
	if err == nil {
		return KindUnknown
	}

	var de *DomainError
	if errors.As(err, &de) {
		return de.Kind
	}

	var k kinder
	if errors.As(err, &k) {
		return k.Kind()
	}

	switch {
	case errors.Is(err, ErrNotFound):
		return KindNotFound
	case errors.Is(err, ErrAlreadyExists):
		return KindAlreadyExists
	case errors.Is(err, ErrPermissionDenied):
		return KindPermissionDenied
	case errors.Is(err, ErrUnavailable):
		return KindUnavailable
	default:
		return KindInternal
	}
}

// HTTPStatus maps err's Kind to a net/http status constant. This is the
// ONLY place in the taxonomy that imports net/http — business logic and
// the domain/repository layers must never import it.
func HTTPStatus(err error) int {
	switch KindOf(err) {
	case KindNotFound:
		return http.StatusNotFound
	case KindInvalidArgument:
		return http.StatusBadRequest
	case KindAlreadyExists:
		return http.StatusConflict
	case KindPermissionDenied:
		return http.StatusForbidden
	case KindUnavailable:
		return http.StatusServiceUnavailable
	default:
		return http.StatusInternalServerError
	}
}

// GRPCStatus maps err's Kind to a gRPC status error. This is the ONLY
// place in the taxonomy that imports grpc/codes and grpc/status.
func GRPCStatus(err error) error {
	if err == nil {
		return nil
	}
	var code codes.Code
	switch KindOf(err) {
	case KindNotFound:
		code = codes.NotFound
	case KindInvalidArgument:
		code = codes.InvalidArgument
	case KindAlreadyExists:
		code = codes.AlreadyExists
	case KindPermissionDenied:
		code = codes.PermissionDenied
	case KindUnavailable:
		code = codes.Unavailable
	default:
		code = codes.Internal
	}
	return status.Error(code, err.Error())
}

/*
BEST PRACTICES DEMONSTRATED

  - Small, closed Kind enum with a String() method — every switch over Kind
    in this file has an explicit default, so a new Kind added later
    degrades safely (falls to Internal/500) rather than compiling into a
    zero-value branch nobody noticed.
  - Sentinels for data-free conditions, a typed struct for data-carrying
    conditions, and a single `kinder` interface bridging both to the same
    dispatch mechanism (KindOf) — callers never need to know which flavor
    produced a given error.
  - Wrapping preserves the chain: DomainError.Unwrap + fmt.Errorf's %w
    both compose with errors.Is/As arbitrarily deep, verified by the
    accompanying tests wrapping 3+ layers deep.
  - Transport mapping isolated to exactly two functions, each importing
    exactly one transport-specific package — grep for "net/http" or
    "grpc/codes" outside HTTPStatus/GRPCStatus in a real codebase and you
    should find nothing in business logic.

ALTERNATIVE APPROACHES

  - Some codebases skip the Kind enum and map straight from concrete error
    type to status code via a type switch in HTTPStatus/GRPCStatus. That
    couples the mapping function to every concrete error type in the
    codebase and duplicates the switch across every transport; the Kind
    indirection here means adding a transport (e.g. a third, CLI exit-code
    mapping) is one more small switch over the same 6-7 Kinds, not a new
    type switch over N error types.
  - A richer taxonomy might attach machine-readable metadata (e.g.
    key-value pairs for structured logging) directly on DomainError rather
    than relying on Op + Error() string parsing; omitted here to keep the
    core mechanism (Kind dispatch through wrapping) clear.
  - go-errors-style stack-trace-capturing wrapper types are a common
    production addition (see stretch goals in the explanation file) but
    add allocation cost on every wrap, so many teams capture a stack trace
    only for KindInternal.
*/
