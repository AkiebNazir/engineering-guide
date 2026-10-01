package apperrors

import (
	"errors"
	"fmt"
	"net/http"
	"testing"

	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

func TestErrorsIsThroughMultipleWrapLayers(t *testing.T) {
	base := ErrNotFound
	layer1 := fmt.Errorf("repo.GetUser: %w", base)
	layer2 := fmt.Errorf("service.FetchAccount: %w", layer1)
	layer3 := Wrap("handler.GetAccount", KindNotFound, layer2)

	if !errors.Is(layer3, ErrNotFound) {
		t.Fatal("errors.Is failed to find ErrNotFound through 3 wrap layers")
	}
}

func TestErrorsAsThroughMultipleWrapLayers(t *testing.T) {
	base := &ValidationError{Field: "email", Reason: "must not be empty"}
	layer1 := fmt.Errorf("service.CreateUser: %w", base)
	layer2 := Wrap("handler.CreateUser", KindInvalidArgument, layer1)

	var ve *ValidationError
	if !errors.As(layer2, &ve) {
		t.Fatal("errors.As failed to find *ValidationError through wrap layers")
	}
	if ve.Field != "email" {
		t.Fatalf("ve.Field = %q, want %q", ve.Field, "email")
	}
}

func TestDomainErrorUnwrap(t *testing.T) {
	base := ErrAlreadyExists
	de := &DomainError{Op: "repo.CreateAccount", Kind: KindAlreadyExists, Err: base}

	if !errors.Is(de, ErrAlreadyExists) {
		t.Fatal("errors.Is failed to see through DomainError.Unwrap")
	}
	if got := errors.Unwrap(de); got != base {
		t.Fatalf("Unwrap() = %v, want %v", got, base)
	}
}

func TestKindOfSentinels(t *testing.T) {
	tests := []struct {
		name string
		err  error
		want Kind
	}{
		{"not found", ErrNotFound, KindNotFound},
		{"already exists", ErrAlreadyExists, KindAlreadyExists},
		{"permission denied", ErrPermissionDenied, KindPermissionDenied},
		{"unavailable", ErrUnavailable, KindUnavailable},
		{"wrapped not found", fmt.Errorf("op: %w", ErrNotFound), KindNotFound},
		{"plain unknown error", errors.New("boom"), KindInternal},
		{"nil", nil, KindUnknown},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := KindOf(tt.err); got != tt.want {
				t.Fatalf("KindOf(%v) = %v, want %v", tt.err, got, tt.want)
			}
		})
	}
}

func TestKindOfValidationError(t *testing.T) {
	err := &ValidationError{Field: "age", Reason: "must be positive"}
	if got := KindOf(err); got != KindInvalidArgument {
		t.Fatalf("KindOf(ValidationError) = %v, want KindInvalidArgument", got)
	}
}

func TestKindOfDomainErrorOverride(t *testing.T) {
	// A DomainError can force a Kind different from what the wrapped
	// sentinel would otherwise resolve to (e.g. mapping a low-level
	// "connection refused" to KindUnavailable at a repo boundary).
	inner := errors.New("dial tcp: connection refused")
	de := &DomainError{Op: "repo.Ping", Kind: KindUnavailable, Err: inner}

	// KindOf must resolve to the DomainError's explicit, forced Kind, not
	// fall through to KindInternal just because the wrapped cause is a
	// plain, unclassified error.
	if got := KindOf(de); got != KindUnavailable {
		t.Fatalf("KindOf(DomainError override) = %v, want KindUnavailable", got)
	}
}

func TestErrorsJoinPreservesKindAndAs(t *testing.T) {
	err1 := &ValidationError{Field: "email", Reason: "invalid format"}
	err2 := &ValidationError{Field: "age", Reason: "must be positive"}
	joined := errors.Join(err1, err2)

	if got := KindOf(joined); got != KindInvalidArgument {
		t.Fatalf("KindOf(joined) = %v, want KindInvalidArgument", got)
	}

	var ve *ValidationError
	if !errors.As(joined, &ve) {
		t.Fatal("errors.As failed to extract a *ValidationError from errors.Join")
	}
	// errors.As returns the first match in traversal order.
	if ve.Field != "email" {
		t.Fatalf("ve.Field = %q, want %q (first joined error)", ve.Field, "email")
	}

	if !errors.Is(joined, err1) || !errors.Is(joined, err2) {
		t.Fatal("errors.Is failed to find a joined member error")
	}
}

func TestWrapNilReturnsNil(t *testing.T) {
	if err := Wrap("op", KindInternal, nil); err != nil {
		t.Fatalf("Wrap(op, kind, nil) = %v, want nil", err)
	}
}

func TestHTTPStatusMapping(t *testing.T) {
	tests := []struct {
		name string
		err  error
		want int
	}{
		{"not found", ErrNotFound, http.StatusNotFound},
		{"invalid argument", &ValidationError{Field: "x", Reason: "y"}, http.StatusBadRequest},
		{"already exists", ErrAlreadyExists, http.StatusConflict},
		{"permission denied", ErrPermissionDenied, http.StatusForbidden},
		{"unavailable", ErrUnavailable, http.StatusServiceUnavailable},
		{"unknown/internal", errors.New("boom"), http.StatusInternalServerError},
		{"wrapped 3 layers", Wrap("h", KindNotFound, fmt.Errorf("s: %w", fmt.Errorf("r: %w", ErrNotFound))), http.StatusNotFound},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := HTTPStatus(tt.err); got != tt.want {
				t.Fatalf("HTTPStatus(%v) = %d, want %d", tt.err, got, tt.want)
			}
		})
	}
}

func TestGRPCStatusMapping(t *testing.T) {
	tests := []struct {
		name string
		err  error
		want codes.Code
	}{
		{"not found", ErrNotFound, codes.NotFound},
		{"invalid argument", &ValidationError{Field: "x", Reason: "y"}, codes.InvalidArgument},
		{"already exists", ErrAlreadyExists, codes.AlreadyExists},
		{"permission denied", ErrPermissionDenied, codes.PermissionDenied},
		{"unavailable", ErrUnavailable, codes.Unavailable},
		{"unknown/internal", errors.New("boom"), codes.Internal},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := GRPCStatus(tt.err)
			st, ok := status.FromError(got)
			if !ok {
				t.Fatalf("GRPCStatus(%v) did not return a *status.Status-backed error", tt.err)
			}
			if st.Code() != tt.want {
				t.Fatalf("GRPCStatus(%v) code = %v, want %v", tt.err, st.Code(), tt.want)
			}
		})
	}
}

func TestGRPCStatusNilIsNil(t *testing.T) {
	if got := GRPCStatus(nil); got != nil {
		t.Fatalf("GRPCStatus(nil) = %v, want nil", got)
	}
}

func TestHTTPAndGRPCAgreeInSpiritForEveryKind(t *testing.T) {
	// Pins the mapping tables together: adding a Kind to one switch
	// without the other should make this test fail loudly instead of
	// silently defaulting one transport to Internal/500.
	tests := []struct {
		kind     Kind
		wantHTTP int
		wantGRPC codes.Code
	}{
		{KindNotFound, http.StatusNotFound, codes.NotFound},
		{KindInvalidArgument, http.StatusBadRequest, codes.InvalidArgument},
		{KindAlreadyExists, http.StatusConflict, codes.AlreadyExists},
		{KindPermissionDenied, http.StatusForbidden, codes.PermissionDenied},
		{KindUnavailable, http.StatusServiceUnavailable, codes.Unavailable},
		{KindInternal, http.StatusInternalServerError, codes.Internal},
	}
	for _, tt := range tests {
		t.Run(tt.kind.String(), func(t *testing.T) {
			err := &DomainError{Op: "op", Kind: tt.kind, Err: errors.New("cause")}
			if got := HTTPStatus(err); got != tt.wantHTTP {
				t.Fatalf("HTTPStatus = %d, want %d", got, tt.wantHTTP)
			}
			st, _ := status.FromError(GRPCStatus(err))
			if st.Code() != tt.wantGRPC {
				t.Fatalf("GRPCStatus code = %v, want %v", st.Code(), tt.wantGRPC)
			}
		})
	}
}

func TestKindStringUnknownDefault(t *testing.T) {
	var k Kind = 999
	if got := k.String(); got != "unknown" {
		t.Fatalf("Kind(999).String() = %q, want %q", got, "unknown")
	}
}
