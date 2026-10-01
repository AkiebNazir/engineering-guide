/*
LEVEL 05 (advanced) - errors.Join: combining independent errors (Go 1.20+)

You will learn
  - errors.Join(errs...) merges several errors into one, skipping any nils,
    for the case where you don't want to stop at the FIRST failure (e.g.
    validating every field of a form)
  - the joined error's Error() string lists every non-nil error's message,
    one per line
  - errors.Is and errors.As both see THROUGH a Join: they check every leaf
    error, not just the first

Run: go run ./GoStdLib/13_errors/level_05_join_multiple_errors
*/

package main

import (
	"errors"
	"fmt"
	"strings"
)

var (
	ErrRequired = errors.New("field is required")
	ErrTooLong  = errors.New("field is too long")
)

type field struct {
	name  string
	value string
}

// validateAll checks every field and joins every failure together, instead
// of returning on the first one - the whole point of errors.Join.
func validateAll(fields []field) error {
	var errs []error
	for _, f := range fields {
		if f.value == "" {
			errs = append(errs, fmt.Errorf("%s: %w", f.name, ErrRequired))
			continue
		}
		if len(f.value) > 10 {
			errs = append(errs, fmt.Errorf("%s: %w", f.name, ErrTooLong))
		}
	}
	// errors.Join(nil, nil, ...) returns nil if every argument is nil, and
	// filters out nils from a mixed slice - no need to check len(errs) first.
	return errors.Join(errs...)
}

func main() {
	fields := []field{
		{"username", ""},                   // triggers ErrRequired
		{"bio", "way more than ten chars"}, // triggers ErrTooLong
		{"email", "a@b.com"},               // fine
	}

	err := validateAll(fields)
	if err == nil {
		panic("validateAll returned nil, want a joined error with 2 failures")
	}

	msg := err.Error()
	if !strings.Contains(msg, "username: field is required") {
		panic(fmt.Sprintf("joined message missing username failure: %q", msg))
	}
	if !strings.Contains(msg, "bio: field is too long") {
		panic(fmt.Sprintf("joined message missing bio failure: %q", msg))
	}
	if strings.Contains(msg, "email") {
		panic(fmt.Sprintf("joined message unexpectedly mentions email: %q", msg))
	}

	// errors.Is looks at EVERY leaf of the join tree, not just the first.
	if !errors.Is(err, ErrRequired) {
		panic("errors.Is(err, ErrRequired) = false, want true: username failed with it")
	}
	if !errors.Is(err, ErrTooLong) {
		panic("errors.Is(err, ErrTooLong) = false, want true: bio failed with it")
	}

	// A sentinel that never occurred is correctly absent.
	var ErrUnused = errors.New("never triggered")
	if errors.Is(err, ErrUnused) {
		panic("errors.Is(err, ErrUnused) = true, want false")
	}

	// A fully-passing validation joins zero errors -> nil, not an empty join.
	clean := validateAll([]field{{"email", "a@b.com"}})
	if clean != nil {
		panic(fmt.Sprintf("validateAll on all-valid fields = %v, want nil", clean))
	}

	// errors.Join exposes Unwrap() []error for anyone who wants the raw list.
	type multiUnwrapper interface{ Unwrap() []error }
	mu, ok := err.(multiUnwrapper)
	if !ok {
		panic("joined error does not implement Unwrap() []error")
	}
	if got := len(mu.Unwrap()); got != 2 {
		panic(fmt.Sprintf("len(joined.Unwrap()) = %d, want 2", got))
	}

	fmt.Printf("joined validation errors:\n%s\n", msg)
	fmt.Println("OK")
}
