/*
LEVEL 02 (core) - the core API: ParseInt/ParseFloat/ParseBool and Format*

You will learn
  - ParseInt(s, base, bitSize): base 10 with explicit bitSize, and base 0 for
    "auto-detect from a 0x/0o/0b prefix"
  - ParseFloat(s, bitSize) and ParseBool(s) (accepts "1","t","T","TRUE","true","True" etc.)
  - the Format* counterparts that go the other way: FormatInt, FormatFloat, FormatBool

Run: go run ./GoStdLib/06_strconv/level_02_core_api
*/

package main

import (
	"fmt"
	"strconv"
)

func main() {
	i64, err := strconv.ParseInt("12345", 10, 64)
	if err != nil {
		panic(fmt.Sprintf("ParseInt failed: %v", err))
	}
	if i64 != 12345 {
		panic(fmt.Sprintf("ParseInt = %d, expected 12345", i64))
	}

	// Base 0 auto-detects the prefix.
	hexAuto, err := strconv.ParseInt("0x1F", 0, 64)
	if err != nil {
		panic(fmt.Sprintf("ParseInt(base 0) failed: %v", err))
	}
	if hexAuto != 31 {
		panic(fmt.Sprintf("ParseInt(\"0x1F\", 0, 64) = %d, expected 31", hexAuto))
	}

	f64, err := strconv.ParseFloat("3.14159", 64)
	if err != nil {
		panic(fmt.Sprintf("ParseFloat failed: %v", err))
	}
	if f64 < 3.14 || f64 > 3.15 {
		panic(fmt.Sprintf("ParseFloat = %v, expected ~3.14159", f64))
	}

	b, err := strconv.ParseBool("TRUE")
	if err != nil {
		panic(fmt.Sprintf("ParseBool failed: %v", err))
	}
	if !b {
		panic("ParseBool(\"TRUE\") should be true")
	}

	// Format* goes the other way.
	if got := strconv.FormatInt(12345, 10); got != "12345" {
		panic(fmt.Sprintf("FormatInt = %q, expected %q", got, "12345"))
	}
	if got := strconv.FormatFloat(3.5, 'f', 2, 64); got != "3.50" {
		panic(fmt.Sprintf("FormatFloat = %q, expected %q", got, "3.50"))
	}
	if got := strconv.FormatBool(true); got != "true" {
		panic(fmt.Sprintf("FormatBool = %q, expected %q", got, "true"))
	}

	fmt.Printf("parsed int=%d hexAuto=%d float=%.5f bool=%v\n", i64, hexAuto, f64, b)
	fmt.Println("OK")
}
