/*
LEVEL 03 (core) - idiom: FormatInt with bases 2/8/16, and parsing them back

You will learn
  - FormatInt(n, base) for bases other than 10 - binary, octal, hex
  - ParseInt(s, 0, bitSize) auto-detects 0b/0o/0x prefixes on the way back in
  - a realistic idiom: formatting a permission-like bitmask for display, and
    parsing a prefixed literal back into a number

Run: go run ./GoStdLib/06_strconv/level_03_bases_idiom
*/

package main

import (
	"fmt"
	"strconv"
)

// describeBits formats n in binary, octal, and hex, each with its
// conventional Go-syntax prefix.
func describeBits(n int64) (binary, octal, hex string) {
	return "0b" + strconv.FormatInt(n, 2),
		"0o" + strconv.FormatInt(n, 8),
		"0x" + strconv.FormatInt(n, 16)
}

func main() {
	const perm int64 = 0o750 // rwxr-x---, written here in Go's own octal literal syntax

	binary, octal, hex := describeBits(perm)
	if binary != "0b111101000" {
		panic(fmt.Sprintf("binary = %q, expected %q", binary, "0b111101000"))
	}
	if octal != "0o750" {
		panic(fmt.Sprintf("octal = %q, expected %q", octal, "0o750"))
	}
	if hex != "0x1e8" {
		panic(fmt.Sprintf("hex = %q, expected %q", hex, "0x1e8"))
	}

	// Round-trip each prefixed literal back through ParseInt with base 0.
	for _, literal := range []string{binary, octal, hex} {
		back, err := strconv.ParseInt(literal, 0, 64)
		if err != nil {
			panic(fmt.Sprintf("ParseInt(%q, 0, 64) failed: %v", literal, err))
		}
		if back != perm {
			panic(fmt.Sprintf("ParseInt(%q) = %d, expected %d", literal, back, perm))
		}
	}

	fmt.Printf("%d in binary=%s octal=%s hex=%s (all round-trip back to %d)\n", perm, binary, octal, hex, perm)
	fmt.Println("OK")
}
