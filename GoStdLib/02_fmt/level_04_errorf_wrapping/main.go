/*
LEVEL 04 (core) - fmt.Errorf with %w: wrapping a real error and unwrapping it

You will learn
  - %w in Errorf wraps an error so it becomes inspectable via errors.Is/As
  - the resulting error's Error() string still contains the wrapped message
  - errors.Unwrap peels one layer; errors.Is walks the whole chain
  - Go 1.20+ allows more than one %w in a single Errorf call

Run: go run ./GoStdLib/02_fmt/level_04_errorf_wrapping
*/

package main

import (
	"errors"
	"fmt"
	"os"
	"strings"
)

// A real sentinel error, the kind a package exports for callers to check.
var ErrConfigMissing = errors.New("config missing")

func loadConfig(path string) error {
	_, err := os.Open(path)
	if err != nil {
		// Wrap the REAL underlying *fs.PathError together with our own sentinel,
		// using two %w verbs (Go 1.20+) so both are discoverable via errors.Is.
		return fmt.Errorf("loadConfig(%s): %w: %w", path, ErrConfigMissing, err)
	}
	return nil
}

func main() {
	err := loadConfig("/definitely/does/not/exist/config.yaml")
	if err == nil {
		panic("expected loadConfig to fail for a missing path")
	}

	// The message contains everything, human-readable, in order.
	msg := err.Error()
	for _, part := range []string{"loadConfig(", "config missing", "no such file or directory"} {
		if !strings.Contains(msg, part) {
			panic(fmt.Sprintf("wrapped error message missing %q: got %q", part, msg))
		}
	}

	// errors.Is finds OUR sentinel through the wrap.
	if !errors.Is(err, ErrConfigMissing) {
		panic("expected errors.Is to find ErrConfigMissing through the %w chain")
	}

	// errors.Is ALSO finds the real os-level not-exist condition, because the
	// second %w wrapped the *fs.PathError from os.Open directly.
	if !errors.Is(err, os.ErrNotExist) {
		panic("expected errors.Is to find os.ErrNotExist through the %w chain")
	}

	// errors.As extracts the concrete underlying type.
	var pathErr *os.PathError
	if !errors.As(err, &pathErr) {
		panic(fmt.Sprintf("expected errors.As to find *os.PathError, err=%T", err))
	}
	if pathErr.Op != "open" {
		panic(fmt.Sprintf("expected PathError.Op %q, got %q", "open", pathErr.Op))
	}

	// A %v or %s in place of %w keeps the same text but breaks Is/As entirely.
	flatErr := fmt.Errorf("loadConfig failed: %v", ErrConfigMissing)
	if errors.Is(flatErr, ErrConfigMissing) {
		panic("expected %v (not %w) to NOT be discoverable via errors.Is")
	}

	fmt.Printf("wrapped error: %v\n", err)
	fmt.Println("errors.Is(ErrConfigMissing) =", errors.Is(err, ErrConfigMissing))
	fmt.Println("errors.Is(os.ErrNotExist)   =", errors.Is(err, os.ErrNotExist))
	fmt.Println("OK")
}
