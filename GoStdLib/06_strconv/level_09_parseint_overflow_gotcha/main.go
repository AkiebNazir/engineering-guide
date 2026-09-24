/*
LEVEL 09 (advanced) - production trap: an out-of-range ParseInt still returns a value

You will learn
  - on ErrRange, ParseInt does NOT return 0 - it returns the closest
    representable value for the requested bit size (the min or max)
  - code that forgets to check the error can silently accept a clamped,
    plausible-looking number instead of the one that was actually in the input
  - the fix: always check the error before trusting the returned value

Run: go run ./GoStdLib/06_strconv/level_09_parseint_overflow_gotcha
*/

package main

import (
	"errors"
	"fmt"
	"strconv"
)

// readInt8Unsafe is the BUGGY version: it ignores the error entirely, the
// way code that's only ever been tested with valid input tends to.
func readInt8Unsafe(s string) int8 {
	v, _ := strconv.ParseInt(s, 10, 8)
	return int8(v)
}

// readInt8Checked is the FIXED version: the error is checked before the
// value is trusted.
func readInt8Checked(s string) (int8, error) {
	v, err := strconv.ParseInt(s, 10, 8)
	if err != nil {
		return 0, err
	}
	return int8(v), nil
}

func main() {
	const overflowing = "500" // out of int8's range (-128..127)

	// --- BROKEN: the ignored error hides that this "worked" only by clamping. ---
	got := readInt8Unsafe(overflowing)
	if got != 127 {
		panic(fmt.Sprintf("expected the clamped value 127, got %d (environment differs from what this level assumes)", got))
	}
	fmt.Printf("BROKEN: readInt8Unsafe(%q) = %d - looks like a valid int8, but it's silently wrong\n", overflowing, got)

	// --- FIXED: the same call, but the error is checked before trusting the value. ---
	_, err := readInt8Checked(overflowing)
	if err == nil {
		panic("expected an error from readInt8Checked on out-of-range input")
	}
	var numErr *strconv.NumError
	if !errors.As(err, &numErr) || !errors.Is(numErr.Err, strconv.ErrRange) {
		panic(fmt.Sprintf("expected a *strconv.NumError wrapping ErrRange, got %v", err))
	}
	fmt.Printf("FIXED:   readInt8Checked(%q) correctly rejected the value: %v\n", overflowing, err)

	// Valid, in-range input still works normally through the checked path.
	ok, err := readInt8Checked("100")
	if err != nil {
		panic(fmt.Sprintf("unexpected error on valid input: %v", err))
	}
	if ok != 100 {
		panic(fmt.Sprintf("readInt8Checked(\"100\") = %d, expected 100", ok))
	}

	fmt.Println("OK")
}
