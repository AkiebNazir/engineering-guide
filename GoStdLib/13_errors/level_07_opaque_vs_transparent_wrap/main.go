/*
LEVEL 07 (advanced) - design concern: opaque vs. transparent error wrapping

You will learn
  - "transparent" wrapping (%w) lets callers see and check the underlying
    error - the right default for internal layers of your own program
  - "opaque" wrapping (%v, or a brand-new errors.New) deliberately HIDES the
    underlying error - the right call at a real API boundary, where you do
    not want callers depending on a private implementation detail
  - this is a design choice you make on purpose, not a mistake - level 9
    covers the version of this that IS a mistake (comparing with ==)

Run: go run ./GoStdLib/13_errors/level_07_opaque_vs_transparent_wrap
*/

package main

import (
	"errors"
	"fmt"
)

// pqDuplicateKey plays the role of a database-driver-specific sentinel: an
// implementation detail of the storage layer, not something the rest of the
// program should ever need to know about.
var pqDuplicateKey = errors.New("pq: duplicate key value violates unique constraint")

// ErrAlreadyExists is the PUBLIC contract of the repository package: any
// caller anywhere can depend on this without knowing what database is
// behind it.
var ErrAlreadyExists = errors.New("already exists")

// insertRow simulates the low-level driver call.
func insertRow(email string) error {
	if email == "taken@example.com" {
		return pqDuplicateKey
	}
	return nil
}

// createUserOpaque is the RIGHT boundary design: it translates the private
// driver error into the package's own public sentinel, deliberately
// dropping the original from the chain. Callers depend on ErrAlreadyExists,
// never on the fact that Postgres is involved.
func createUserOpaque(email string) error {
	if err := insertRow(email); err != nil {
		if errors.Is(err, pqDuplicateKey) {
			return fmt.Errorf("create user %q: %w", email, ErrAlreadyExists)
		}
		return fmt.Errorf("create user %q: %w", email, err)
	}
	return nil
}

// createUserLeaky is the WRONG boundary design for comparison: it wraps the
// driver error directly, so callers who check errors.Is(err, ErrAlreadyExists)
// get false even though "already exists" is exactly what happened - they
// would have to know about pqDuplicateKey, a private detail, to react to it.
func createUserLeaky(email string) error {
	if err := insertRow(email); err != nil {
		return fmt.Errorf("create user %q: %w", email, err)
	}
	return nil
}

func main() {
	// Opaque boundary: the caller's check against the PUBLIC sentinel works.
	err := createUserOpaque("taken@example.com")
	if !errors.Is(err, ErrAlreadyExists) {
		panic("errors.Is(err, ErrAlreadyExists) = false, want true: opaque boundary should expose the public sentinel")
	}
	// And the private detail is exactly that: private. Callers can't reach it.
	if errors.Is(err, pqDuplicateKey) {
		panic("errors.Is(err, pqDuplicateKey) = true, want false: opaque boundary must not leak the driver error")
	}

	// Leaky design: the caller's check against the PUBLIC sentinel fails,
	// even though the underlying condition (duplicate key) is identical.
	leaky := createUserLeaky("taken@example.com")
	if errors.Is(leaky, ErrAlreadyExists) {
		panic("errors.Is(leaky, ErrAlreadyExists) = true, want false: this demonstrates the design gap, it should NOT match")
	}
	if !errors.Is(leaky, pqDuplicateKey) {
		panic("errors.Is(leaky, pqDuplicateKey) = false, want true: leaky design exposes the private driver error instead")
	}

	// The lesson: neither %v nor %w is universally "correct" - what matters
	// is which sentinel you choose to preserve (or translate to) at the
	// boundary you're designing.
	fmt.Printf("opaque boundary error: %v\n", err)
	fmt.Printf("leaky boundary error:  %v\n", leaky)
	fmt.Println("OK")
}
