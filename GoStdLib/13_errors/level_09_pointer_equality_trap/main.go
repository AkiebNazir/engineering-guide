/*
LEVEL 09 (advanced) - correctness trap: comparing errors with == or by message

You will learn
  - errors.New returns a pointer to a freshly allocated struct EVERY call -
    two calls with the identical text are never == to each other
  - code that "looks fine" comparing errors with == (or comparing
    err.Error() strings) breaks the moment either side gets wrapped, or the
    moment someone changes the message text as a "harmless" refactor
  - the fix is always errors.Is against a shared sentinel - it is wrapper-safe
    and does not depend on message text at all

Run: go run ./GoStdLib/13_errors/level_09_pointer_equality_trap
*/

package main

import (
	"errors"
	"fmt"
)

// Two independently constructed errors with IDENTICAL text. In real code
// this happens when two packages (or two functions in the same package)
// each call errors.New with the same message instead of sharing one
// sentinel.
var (
	errA = errors.New("connection refused")
	errB = errors.New("connection refused")
)

func main() {
	// Trap #1: they look identical when printed...
	if errA.Error() != errB.Error() {
		panic("test setup broken: errA and errB should have identical text")
	}
	// ...but == compares pointer identity, and these are different allocations.
	if errA == errB {
		panic("errA == errB, want false: errors.New never makes comparable-by-content values")
	}

	// Trap #2: string-comparing messages "works" until wording drifts.
	sameTextButWrong := errA.Error() == errB.Error() // true today...
	if !sameTextButWrong {
		panic("expected the fragile string comparison to currently read true")
	}
	// ...but the moment one side gets wrapped, message-string comparison
	// silently stops matching, with no compile-time or panic-time warning:
	wrapped := fmt.Errorf("dial tcp: %w", errA)
	if wrapped.Error() == errB.Error() {
		panic("wrapped.Error() unexpectedly still equals errB.Error() - trap setup is wrong")
	}
	// This is the actual production bug shape: a refactor that adds context
	// via %w silently breaks a caller that was comparing raw strings.

	// The fix: share ONE sentinel, and compare with errors.Is - both before
	// and after wrapping.
	var ErrConnRefused = errors.New("connection refused")
	direct := ErrConnRefused
	wrappedFixed := fmt.Errorf("dial tcp: %w", ErrConnRefused)

	if !errors.Is(direct, ErrConnRefused) {
		panic("errors.Is(direct, ErrConnRefused) = false, want true")
	}
	if !errors.Is(wrappedFixed, ErrConnRefused) {
		panic("errors.Is(wrappedFixed, ErrConnRefused) = false, want true: wrapping must not break the fixed comparison")
	}

	// And errA/errB remain correctly distinguishable from the shared sentinel:
	// they are a different failure that happens to share wording, not the
	// same failure - errors.Is agrees they are NOT the same value.
	if errors.Is(errA, ErrConnRefused) {
		panic("errors.Is(errA, ErrConnRefused) = true, want false: errA is a separate sentinel despite identical text")
	}

	fmt.Println("== on separately-constructed errors.New values is unreliable; errors.Is against a shared sentinel is not")
	fmt.Println("OK")
}
