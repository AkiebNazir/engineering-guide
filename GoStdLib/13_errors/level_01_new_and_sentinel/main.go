/*
LEVEL 01 (basic) - errors.New: making an error value and comparing it

You will learn
  - errors.New(text) makes the simplest possible error: a value whose
    Error() method returns that text
  - a package-level "sentinel" error (a predeclared errors.New value, the
    same pattern as io.EOF) lets callers compare against a known failure
  - errors.Is(err, target) is the idiomatic comparison - for an unwrapped
    error it behaves like err == target, but stays correct once wrapping
    enters the picture (see later levels)

Run: go run ./GoStdLib/13_errors/level_01_new_and_sentinel
*/

package main

import (
	"errors"
	"fmt"
)

// A sentinel error: a package-level value callers can compare against by
// identity, exactly like io.EOF or sql.ErrNoRows in the standard library.
var ErrNotFound = errors.New("item not found")

// lookup simulates a small store. Returning the sentinel directly (no
// wrapping yet) is the simplest possible error-producing function.
func lookup(id int) (string, error) {
	store := map[int]string{1: "pen", 2: "notebook"}
	name, ok := store[id]
	if !ok {
		return "", ErrNotFound
	}
	return name, nil
}

func main() {
	// The happy path: no error.
	name, err := lookup(1)
	if err != nil {
		panic(fmt.Sprintf("lookup(1) returned unexpected error: %v", err))
	}
	if name != "pen" {
		panic(fmt.Sprintf("lookup(1) = %q, want %q", name, "pen"))
	}

	// The failure path: the sentinel comes back unchanged.
	_, err = lookup(99)
	if err == nil {
		panic("lookup(99) returned nil error, want ErrNotFound")
	}

	// errors.Is is the idiomatic check, even though a plain == would also
	// work here (nothing has wrapped the sentinel yet).
	if !errors.Is(err, ErrNotFound) {
		panic(fmt.Sprintf("errors.Is(err, ErrNotFound) = false, want true (err=%v)", err))
	}

	// err.Error() gives the human-readable text; it is NOT the thing to
	// compare programmatically (see level 9 for why that trap bites).
	if err.Error() != "item not found" {
		panic(fmt.Sprintf("err.Error() = %q, want %q", err.Error(), "item not found"))
	}

	// A second, textually identical error made with errors.New is a
	// DIFFERENT value: errors.New carries no notion of equality by content.
	other := errors.New("item not found")
	if errors.Is(err, other) {
		panic("errors.Is(err, other) = true, want false: two separate errors.New calls must not compare equal")
	}

	fmt.Printf("lookup(99) failed as expected: %v\n", err)
	fmt.Println("OK")
}
