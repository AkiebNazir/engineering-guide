/*
LEVEL 01 (basic) - strings.Contains, HasPrefix, HasSuffix: the single most common use

You will learn
  - strings.Contains(s, substr) reports whether substr appears anywhere in s
  - strings.HasPrefix/HasSuffix check the start/end specifically
  - all three are exact, byte-level substring checks - no patterns, no allocation

Run: go run ./GoStdLib/05_strings/level_01_contains_prefix_suffix
*/

package main

import (
	"fmt"
	"strings"
)

func main() {
	filename := "report_2026_final.pdf"

	if !strings.HasSuffix(filename, ".pdf") {
		panic(fmt.Sprintf("expected %q to have suffix .pdf", filename))
	}
	if !strings.HasPrefix(filename, "report_") {
		panic(fmt.Sprintf("expected %q to have prefix report_", filename))
	}
	if !strings.Contains(filename, "2026") {
		panic(fmt.Sprintf("expected %q to contain 2026", filename))
	}
	if strings.Contains(filename, "2027") {
		panic(fmt.Sprintf("did not expect %q to contain 2027", filename))
	}
	if strings.HasPrefix(filename, ".pdf") {
		panic("HasPrefix wrongly matched a suffix as a prefix")
	}

	fmt.Printf("%q: prefix=report_ ok, suffix=.pdf ok, contains 2026 ok\n", filename)
	fmt.Println("OK")
}
