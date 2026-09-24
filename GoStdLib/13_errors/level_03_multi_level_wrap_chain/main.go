/*
LEVEL 03 (advanced) - a realistic multi-level wrap chain, checked with errors.Is

You will learn
  - a three-layer call stack (repository -> service -> handler), each layer
    adding its own %w context, is the normal shape of errors in a real
    program
  - errors.Is(err, target) does not care how many layers deep target is -
    it walks Unwrap() until it finds a match or runs out of chain
  - the printed error message reads top-to-bottom like a stack trace of
    intent ("handling request: loading user: querying db: sql: no rows"),
    even though only the bottom value is the sentinel being checked

Run: go run ./GoStdLib/13_errors/level_03_multi_level_wrap_chain
*/

package main

import (
	"errors"
	"fmt"
)

// ErrNoRows plays the role of a driver-level sentinel, e.g. sql.ErrNoRows.
var ErrNoRows = errors.New("sql: no rows in result set")

// Layer 1: repository - closest to the "hardware".
func queryDB(userID int) error {
	if userID == 404 {
		return ErrNoRows
	}
	return nil
}

// Layer 2: service - adds business-level context.
func loadUser(userID int) error {
	if err := queryDB(userID); err != nil {
		return fmt.Errorf("loading user %d: %w", userID, err)
	}
	return nil
}

// Layer 3: handler - adds request-level context.
func handleRequest(userID int) error {
	if err := loadUser(userID); err != nil {
		return fmt.Errorf("handling request: %w", err)
	}
	return nil
}

func main() {
	err := handleRequest(404)
	if err == nil {
		panic("handleRequest(404) returned nil, want a wrapped ErrNoRows")
	}

	wantMsg := "handling request: loading user 404: sql: no rows in result set"
	if err.Error() != wantMsg {
		panic(fmt.Sprintf("err.Error() = %q, want %q", err.Error(), wantMsg))
	}

	// Three layers deep, errors.Is still finds the sentinel.
	if !errors.Is(err, ErrNoRows) {
		panic("errors.Is(err, ErrNoRows) = false, want true through 3 layers of wrapping")
	}

	// Manually walking confirms exactly 3 Unwrap steps reach the sentinel.
	steps := 0
	cur := err
	for cur != nil {
		if cur == ErrNoRows {
			break
		}
		cur = errors.Unwrap(cur)
		steps++
	}
	if steps != 2 {
		panic(fmt.Sprintf("manual unwrap took %d steps to reach the sentinel, want 2", steps))
	}
	if cur != ErrNoRows {
		panic("manual unwrap loop did not reach ErrNoRows")
	}

	// A successful call produces no error and errors.Is on nil is always false.
	if err := handleRequest(1); err != nil {
		panic(fmt.Sprintf("handleRequest(1) = %v, want nil", err))
	}
	if errors.Is(nil, ErrNoRows) {
		panic("errors.Is(nil, ErrNoRows) = true, want false")
	}

	fmt.Printf("full chain: %v\n", err)
	fmt.Println("OK")
}
