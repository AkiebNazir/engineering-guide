/*
LEVEL 03 (core) - Sprintf, width, and precision combined into a small idiom

You will learn
  - fmt.Sprintf returns a formatted string instead of writing it anywhere
  - a width like %6s / %6.2f pads with spaces (left-pad by default, right-pad with -)
  - precision on floats (%6.2f) fixes the number of digits after the decimal point
  - combining these builds an aligned text table without a templating library

Run: go run ./GoStdLib/02_fmt/level_03_sprintf_building_strings
*/

package main

import (
	"fmt"
	"strings"
)

type row struct {
	name  string
	price float64
}

func main() {
	rows := []row{
		{"widget", 3.5},
		{"gadget-xl", 129.995},
		{"pin", 0.2},
	}

	var b strings.Builder
	for _, r := range rows {
		// %-10s : left-justified, padded to width 10
		// %8.2f  : right-justified, width 8, exactly 2 digits after the decimal
		line := fmt.Sprintf("%-10s %8.2f\n", r.name, r.price)
		b.WriteString(line)
	}
	table := b.String()

	want := "" +
		"widget         3.50\n" +
		"gadget-xl    130.00\n" + // 129.995 rounds to 130.00 at 2 decimal places
		"pin            0.20\n"
	if table != want {
		panic(fmt.Sprintf("table mismatch:\ngot:\n%q\nwant:\n%q", table, want))
	}

	// Width alone on an int, right-justified by default.
	numbered := fmt.Sprintf("[%4d]", 7)
	if numbered != "[   7]" {
		panic(fmt.Sprintf("width mismatch: got %q, want %q", numbered, "[   7]"))
	}

	// A "*" width/precision takes the value from an argument instead of the format string.
	dynamic := fmt.Sprintf("[%*d]", 5, 7)
	if dynamic != "[    7]" {
		panic(fmt.Sprintf("dynamic width mismatch: got %q, want %q", dynamic, "[    7]"))
	}

	fmt.Print(table)
	fmt.Println(numbered, dynamic)
	fmt.Println("OK")
}
