/*
LEVEL 06 (advanced) - MEASURED: building a big string with Sprintf+concat vs strings.Builder

You will learn
  - repeated string concatenation (s = s + fmt.Sprintf(...)) reallocates and
    copies the whole string on every iteration - O(n^2) total work
  - strings.Builder grows a backing buffer and writes formatted output straight
    into it via fmt.Fprintf, avoiding the repeated copies
  - how to time real code with time.Now()/time.Since() and report real numbers,
    without assuming the "obvious" answer before measuring it

Run: go run ./GoStdLib/02_fmt/level_06_measured_sprintf_vs_builder
*/

package main

import (
	"fmt"
	"strings"
	"time"
)

const lines = 20000

func concatWithSprintf() string {
	s := ""
	for i := 0; i < lines; i++ {
		s = s + fmt.Sprintf("line %d: value=%d\n", i, i*i)
	}
	return s
}

func buildWithBuilder() string {
	var b strings.Builder
	for i := 0; i < lines; i++ {
		fmt.Fprintf(&b, "line %d: value=%d\n", i, i*i)
	}
	return b.String()
}

func main() {
	start := time.Now()
	concatResult := concatWithSprintf()
	concatElapsed := time.Since(start)

	start = time.Now()
	builderResult := buildWithBuilder()
	builderElapsed := time.Since(start)

	if concatResult != builderResult {
		panic("both approaches should produce byte-identical output")
	}
	if len(concatResult) == 0 {
		panic("expected non-empty output")
	}

	fmt.Printf("string concat + Sprintf (%d lines): %v\n", lines, concatElapsed)
	fmt.Printf("strings.Builder + Fprintf (%d lines): %v\n", lines, builderElapsed)

	if builderElapsed < concatElapsed {
		fmt.Printf("strings.Builder was %.1fx faster in this run\n",
			float64(concatElapsed)/float64(builderElapsed))
	} else {
		// Report honestly even if it didn't come out the "expected" way this run.
		fmt.Println("NOTE: strings.Builder was not faster in this run - report what was actually measured.")
	}

	fmt.Println("OK")
}
