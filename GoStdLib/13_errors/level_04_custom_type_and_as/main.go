/*
LEVEL 04 (advanced) - a custom error type, extracted through a chain with errors.As

You will learn
  - a custom error type is just a type with an Error() string method - it
    can carry structured fields a plain sentinel cannot (which field, what
    value, what limit)
  - errors.As(err, &target) walks the chain looking for an error whose
    concrete type matches *target, and copies it into target if found
  - Is answers "is this THAT specific value/sentinel"; As answers "is there
    an error of THIS TYPE in the chain, and if so give it to me"

Run: go run ./GoStdLib/13_errors/level_04_custom_type_and_as
*/

package main

import (
	"errors"
	"fmt"
)

// ValidationError carries structured detail a sentinel string never could:
// exactly which field failed and why.
type ValidationError struct {
	Field string
	Value int
	Max   int
}

// Error implements the error interface - this one method is all that's
// required for ValidationError to satisfy `error`.
func (e *ValidationError) Error() string {
	return fmt.Sprintf("field %q = %d exceeds max %d", e.Field, e.Value, e.Max)
}

func validateAge(age int) error {
	const max = 150
	if age > max {
		return &ValidationError{Field: "age", Value: age, Max: max}
	}
	return nil
}

// saveUser wraps whatever validateAge returns with request-level context,
// same pattern as level 3.
func saveUser(age int) error {
	if err := validateAge(age); err != nil {
		return fmt.Errorf("saving user: %w", err)
	}
	return nil
}

func main() {
	err := saveUser(999)
	if err == nil {
		panic("saveUser(999) returned nil, want a wrapped ValidationError")
	}

	// errors.As needs a pointer to the target type (here **ValidationError
	// via &target where target is *ValidationError). It walks the chain and,
	// if it finds a match, copies the concrete value into target.
	var ve *ValidationError
	if !errors.As(err, &ve) {
		panic("errors.As(err, &ve) = false, want true: a *ValidationError is in the chain")
	}

	// Now we have the ORIGINAL structured data back, not just a string.
	if ve.Field != "age" {
		panic(fmt.Sprintf("ve.Field = %q, want %q", ve.Field, "age"))
	}
	if ve.Value != 999 {
		panic(fmt.Sprintf("ve.Value = %d, want %d", ve.Value, 999))
	}
	if ve.Max != 150 {
		panic(fmt.Sprintf("ve.Max = %d, want %d", ve.Max, 150))
	}

	wantMsg := `saving user: field "age" = 999 exceeds max 150`
	if err.Error() != wantMsg {
		panic(fmt.Sprintf("err.Error() = %q, want %q", err.Error(), wantMsg))
	}

	// As on an error chain with no matching type returns false and leaves
	// target untouched (here still nil from a fresh declaration).
	plainErr := errors.New("something else entirely")
	var ve2 *ValidationError
	if errors.As(plainErr, &ve2) {
		panic("errors.As(plainErr, &ve2) = true, want false: no ValidationError in this chain")
	}
	if ve2 != nil {
		panic("errors.As left target non-nil on a failed match")
	}

	// The happy path still validates cleanly.
	if err := saveUser(30); err != nil {
		panic(fmt.Sprintf("saveUser(30) = %v, want nil", err))
	}

	fmt.Printf("extracted: field=%s value=%d max=%d\n", ve.Field, ve.Value, ve.Max)
	fmt.Println("OK")
}
