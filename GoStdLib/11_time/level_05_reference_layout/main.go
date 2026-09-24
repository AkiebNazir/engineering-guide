/*
LEVEL 05 (intermediate pattern) - the reference-date layout string

You will learn
  - Go formats/parses time using an EXAMPLE, not verbs like "%Y-%m-%d" - you
    write the reference date/time in the shape you want, and Format/Parse
    match against that shape
  - the reference instant is Mon Jan 2 15:04:05 MST 2006, because its
    components are 1, 2, 3, 4, 5, 6, 7 in order: month=01, day=02, hour=03
    (15 in 24h form), minute=04, second=05, year=06, and the timezone offset
    -0700 reads as "MST" is 7 hours behind - it is deliberately the sequence
    "1 2 3 4 5 6 7", chosen to be memorable, not a real historical event
  - "2006-01-02 15:04:05" is that same reference date written in the shape
    you want your own timestamps to have - Format emits that shape, Parse
    reads it back, and the two are exact inverses

Run: go run ./GoStdLib/11_time/level_05_reference_layout
*/

package main

import (
	"fmt"
	"time"
)

func main() {
	// The reference instant itself, spelled out with time.Date - this is
	// what "2006-01-02 15:04:05" refers to under the hood.
	reference := time.Date(2006, time.January, 2, 15, 4, 5, 0, time.UTC)

	const layout = "2006-01-02 15:04:05"
	formatted := reference.Format(layout)
	if formatted != "2006-01-02 15:04:05" {
		panic(fmt.Sprintf("formatting the reference date with its own layout should echo it back: got %q", formatted))
	}

	// Round trip: an arbitrary timestamp, formatted then parsed, must survive intact.
	original := time.Date(2024, time.November, 3, 8, 15, 30, 0, time.UTC)
	text := original.Format(layout)
	parsed, err := time.Parse(layout, text)
	if err != nil {
		panic(fmt.Sprintf("Parse failed: %v", err))
	}
	if !parsed.Equal(original) {
		panic(fmt.Sprintf("round trip mismatch: got %v, want %v", parsed, original))
	}

	// The layout's shape is what matters, not the specific digits: swapping
	// the separator in the layout changes the expected shape of the OUTPUT.
	const dashLayout = "02-01-2006"
	dmy := original.Format(dashLayout)
	if dmy != "03-11-2024" {
		panic(fmt.Sprintf("day-month-year format = %q, want %q", dmy, "03-11-2024"))
	}

	// time.RFC3339 is just a pre-defined constant built the same way.
	if time.RFC3339 != "2006-01-02T15:04:05Z07:00" {
		panic(fmt.Sprintf("time.RFC3339 = %q, unexpected value", time.RFC3339))
	}
	rfc, err := time.Parse(time.RFC3339, original.Format(time.RFC3339))
	if err != nil {
		panic(fmt.Sprintf("RFC3339 round trip failed: %v", err))
	}
	if !rfc.Equal(original) {
		panic(fmt.Sprintf("RFC3339 round trip mismatch: got %v, want %v", rfc, original))
	}

	fmt.Printf("reference date formatted with itself: %q\n", formatted)
	fmt.Printf("custom layout round trip: %q -> %v\n", text, parsed)
	fmt.Printf("day-month-year layout: %q\n", dmy)
	fmt.Println("OK")
}
