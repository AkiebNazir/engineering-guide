/*
LEVEL 04 (error handling) - triggering and handling a real *time.ParseError

You will learn
  - time.Parse(layout, value) fails when value's shape does not match layout -
    this level triggers that for real instead of describing it
  - the error is a concrete *time.ParseError with Layout, Value, and a
    human-readable Message describing exactly what did not match
  - errors.As unwraps it out of the plain `error` return type so you can
    inspect those fields, the same pattern as csv.ParseError in level 4 of
    the encoding/csv module

Run: go run ./GoStdLib/11_time/level_04_parse_error
*/

package main

import (
	"errors"
	"fmt"
	"time"
)

func main() {
	const layout = "2006-01-02" // date only, no time-of-day

	good, err := time.Parse(layout, "2024-03-15")
	if err != nil {
		panic(fmt.Sprintf("Parse of a well-formed date failed: %v", err))
	}
	if good.Year() != 2024 || good.Month() != time.March || good.Day() != 15 {
		panic(fmt.Sprintf("parsed date wrong: %v", good))
	}

	// The value has a time-of-day component the layout does not expect.
	_, err = time.Parse(layout, "2024-03-15 09:30:00")
	if err == nil {
		panic("FAILED: expected a parse error for a value with extra trailing text")
	}

	var parseErr *time.ParseError
	if !errors.As(err, &parseErr) {
		panic(fmt.Sprintf("expected *time.ParseError, got %T: %v", err, err))
	}
	if parseErr.Layout != layout {
		panic(fmt.Sprintf("ParseError.Layout = %q, want %q", parseErr.Layout, layout))
	}
	if parseErr.Value != "2024-03-15 09:30:00" {
		panic(fmt.Sprintf("ParseError.Value = %q, unexpected", parseErr.Value))
	}

	// The fix: use a layout whose shape actually matches the input.
	const fullLayout = "2006-01-02 15:04:05"
	fixed, err := time.Parse(fullLayout, "2024-03-15 09:30:00")
	if err != nil {
		panic(fmt.Sprintf("Parse with the matching layout should succeed: %v", err))
	}
	if fixed.Hour() != 9 || fixed.Minute() != 30 {
		panic(fmt.Sprintf("fixed parse wrong: %v", fixed))
	}

	fmt.Printf("triggered: %v\n", parseErr)
	fmt.Printf("fixed with the right layout: %v\n", fixed)
	fmt.Println("OK")
}
