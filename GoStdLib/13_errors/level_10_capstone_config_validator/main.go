/*
LEVEL 10 (advanced) - capstone: a config validator using sentinels, a typed
error, wrapping, and errors.Join together

You will learn
  - nothing new - this wires up levels 1-9 into one small realistic program:
    a config validator that collects EVERY problem (errors.Join, level 5),
    reports which ones are a specific known condition (errors.Is, levels 1-3)
    and which carry structured detail (errors.As on a custom type, level 4),
    all wrapped with operation context (%w, level 2) at a clean boundary
    (level 7's opaque/transparent distinction)

Run: go run ./GoStdLib/13_errors/level_10_capstone_config_validator
*/

package main

import (
	"errors"
	"fmt"
)

// Public sentinels: the validator package's contract with its callers.
var (
	ErrMissingField = errors.New("missing required field")
	ErrOutOfRange   = errors.New("value out of range")
)

// RangeError is the structured counterpart to ErrOutOfRange: callers that
// only need "was something out of range" use errors.Is(err, ErrOutOfRange);
// callers that need WHICH field and by how much use errors.As on this type.
type RangeError struct {
	Field    string
	Value    int
	Min, Max int
}

func (e *RangeError) Error() string {
	return fmt.Sprintf("%s=%d not in [%d,%d]", e.Field, e.Value, e.Min, e.Max)
}

// RangeError participates in errors.Is checks against ErrOutOfRange by
// implementing Is - this lets a single concrete error answer to BOTH the
// generic sentinel check and the specific errors.As extraction.
func (e *RangeError) Is(target error) bool {
	return target == ErrOutOfRange
}

type Config struct {
	Name    string
	Workers int
	Timeout int
}

// validate returns every problem at once via errors.Join, each one wrapped
// with which field it concerns.
func validate(c Config) error {
	var errs []error

	if c.Name == "" {
		errs = append(errs, fmt.Errorf("config.Name: %w", ErrMissingField))
	}
	if c.Workers < 1 || c.Workers > 64 {
		errs = append(errs, fmt.Errorf("config.Workers: %w",
			&RangeError{Field: "Workers", Value: c.Workers, Min: 1, Max: 64}))
	}
	if c.Timeout < 1 || c.Timeout > 300 {
		errs = append(errs, fmt.Errorf("config.Timeout: %w",
			&RangeError{Field: "Timeout", Value: c.Timeout, Min: 1, Max: 300}))
	}

	return errors.Join(errs...)
}

func main() {
	bad := Config{Name: "", Workers: 0, Timeout: 30}
	err := validate(bad)
	if err == nil {
		panic("validate(bad) returned nil, want joined errors for Name and Workers")
	}

	// errors.Is finds the missing-field sentinel among the joined errors.
	if !errors.Is(err, ErrMissingField) {
		panic("errors.Is(err, ErrMissingField) = false, want true")
	}

	// errors.Is ALSO finds ErrOutOfRange, via RangeError's own Is method,
	// even though ErrOutOfRange itself was never directly wrapped anywhere.
	if !errors.Is(err, ErrOutOfRange) {
		panic("errors.Is(err, ErrOutOfRange) = false, want true (via RangeError.Is)")
	}

	// errors.As pulls out the concrete RangeError to inspect its fields.
	var re *RangeError
	if !errors.As(err, &re) {
		panic("errors.As(err, &re) = false, want true: a *RangeError is in the chain")
	}
	if re.Field != "Workers" {
		panic(fmt.Sprintf("re.Field = %q, want %q", re.Field, "Workers"))
	}
	if re.Value != 0 || re.Min != 1 || re.Max != 64 {
		panic(fmt.Sprintf("re = %+v, want Value=0 Min=1 Max=64", re))
	}

	// Timeout was valid, so no RangeError for it should be findable by
	// checking there is exactly one RangeError-carrying failure (Workers) -
	// count every joined error whose message mentions "Timeout".
	joinedCount := 0
	if uw, ok := err.(interface{ Unwrap() []error }); ok {
		for _, child := range uw.Unwrap() {
			joinedCount++
			_ = child
		}
	}
	if joinedCount != 2 {
		panic(fmt.Sprintf("joined error count = %d, want 2 (Name + Workers)", joinedCount))
	}

	// A fully valid config joins zero errors -> nil.
	good := Config{Name: "worker-pool", Workers: 8, Timeout: 30}
	if err := validate(good); err != nil {
		panic(fmt.Sprintf("validate(good) = %v, want nil", err))
	}

	fmt.Printf("validation failures:\n%v\n", err)
	fmt.Printf("extracted range error: field=%s value=%d range=[%d,%d]\n", re.Field, re.Value, re.Min, re.Max)
	fmt.Println("OK")
}
