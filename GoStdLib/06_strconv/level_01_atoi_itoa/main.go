/*
LEVEL 01 (basic) - strconv.Atoi and Itoa: the single most common conversion

You will learn
  - Atoi(s) parses a base-10 string into an int, returning an error on failure
  - Itoa(i) is the exact reverse: an int formatted as a base-10 string
  - Atoi is just a thin wrapper: ParseInt(s, 10, 0) sized to the platform int

Run: go run ./GoStdLib/06_strconv/level_01_atoi_itoa
*/

package main

import (
	"fmt"
	"strconv"
)

func main() {
	n, err := strconv.Atoi("42")
	if err != nil {
		panic(fmt.Sprintf("Atoi failed: %v", err))
	}
	if n != 42 {
		panic(fmt.Sprintf("Atoi(\"42\") = %d, expected 42", n))
	}

	s := strconv.Itoa(n)
	if s != "42" {
		panic(fmt.Sprintf("Itoa(%d) = %q, expected %q", n, s, "42"))
	}

	// Negative numbers round-trip too.
	neg, err := strconv.Atoi("-17")
	if err != nil {
		panic(fmt.Sprintf("Atoi failed on negative: %v", err))
	}
	if strconv.Itoa(neg) != "-17" {
		panic(fmt.Sprintf("Itoa(%d) = %q, expected %q", neg, strconv.Itoa(neg), "-17"))
	}

	// A non-numeric string is a real error, not a zero value to trust blindly.
	if _, err := strconv.Atoi("not-a-number"); err == nil {
		panic("expected Atoi to fail on \"not-a-number\"")
	}

	fmt.Printf("Atoi(\"42\")=%d, Itoa(42)=%q, round trip of -17 = %q\n", n, s, strconv.Itoa(neg))
	fmt.Println("OK")
}
