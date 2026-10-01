/*
LEVEL 02 (core) - fmt.Errorf("...: %w", err) and errors.Unwrap

You will learn
  - fmt.Errorf with the %w verb wraps an existing error inside a new one,
    adding context while keeping the original reachable
  - the wrapping error's Error() string is just the formatted text - the
    ORIGINAL error is a separate value, reached via Unwrap()
  - errors.Unwrap(err) is the one-step-at-a-time primitive that errors.Is
    and errors.As use internally to walk a chain

Run: go run ./GoStdLib/13_errors/level_02_errorf_wrap_and_unwrap
*/

package main

import (
	"errors"
	"fmt"
)

var ErrPermission = errors.New("permission denied")

// openFile simulates a lower-level operation that fails with a sentinel.
func openFile(path string) error {
	return ErrPermission
}

// readConfig calls openFile and adds context via %w - the standard way to
// say "this operation failed, and here is what caused it" without losing
// the underlying error's identity.
func readConfig(path string) error {
	if err := openFile(path); err != nil {
		return fmt.Errorf("read config %q: %w", path, err)
	}
	return nil
}

func main() {
	err := readConfig("/etc/app.conf")
	if err == nil {
		panic("readConfig returned nil error, want a wrapped ErrPermission")
	}

	wantMsg := `read config "/etc/app.conf": permission denied`
	if err.Error() != wantMsg {
		panic(fmt.Sprintf("err.Error() = %q, want %q", err.Error(), wantMsg))
	}

	// The wrapping error is a distinct value from the sentinel...
	if err == ErrPermission {
		panic("err == ErrPermission, want a distinct wrapping value")
	}

	// ...but errors.Unwrap peels one layer off and gets it back exactly.
	inner := errors.Unwrap(err)
	if inner != ErrPermission {
		panic(fmt.Sprintf("errors.Unwrap(err) = %v, want ErrPermission", inner))
	}

	// Unwrap again: the sentinel itself wraps nothing further.
	if errors.Unwrap(inner) != nil {
		panic(fmt.Sprintf("errors.Unwrap(inner) = %v, want nil", errors.Unwrap(inner)))
	}

	// errors.Is does exactly this walk (Unwrap, compare, repeat) for you.
	if !errors.Is(err, ErrPermission) {
		panic("errors.Is(err, ErrPermission) = false, want true")
	}

	// A %v verb instead of %w would have produced the same visible text...
	vErr := fmt.Errorf("read config %q: %v", "/etc/app.conf", ErrPermission)
	if vErr.Error() != err.Error() {
		panic(fmt.Sprintf("%%v and %%w text differ: %q vs %q", vErr.Error(), err.Error()))
	}
	// ...but %v does NOT implement Unwrap, so the chain is severed.
	if errors.Unwrap(vErr) != nil {
		panic(fmt.Sprintf("errors.Unwrap(vErr) = %v, want nil (%%v must not wrap)", errors.Unwrap(vErr)))
	}
	if errors.Is(vErr, ErrPermission) {
		panic("errors.Is(vErr, ErrPermission) = true, want false: %v must not preserve identity")
	}

	fmt.Printf("wrapped error: %v\n", err)
	fmt.Println("OK")
}
