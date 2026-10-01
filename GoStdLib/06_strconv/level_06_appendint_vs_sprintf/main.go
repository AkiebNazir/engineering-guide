/*
LEVEL 06 (advanced) - MEASURED: strconv.AppendInt vs fmt.Sprintf in a hot loop

You will learn
  - AppendInt(dst, i, base) writes the formatted digits directly into a
    growing []byte, with no reflection and no intermediate string allocation
  - fmt.Sprintf("%d", i) goes through reflection-based formatting machinery
    and allocates a new string every call
  - measuring both, honestly, with time.Now()/time.Since() over many iterations

Run: go run ./GoStdLib/06_strconv/level_06_appendint_vs_sprintf
*/

package main

import (
	"fmt"
	"strconv"
	"time"
)

const iterations = 200_000

func buildWithAppendInt() []byte {
	buf := make([]byte, 0, iterations*7)
	for i := 0; i < iterations; i++ {
		buf = strconv.AppendInt(buf, int64(i), 10)
		buf = append(buf, ',')
	}
	return buf
}

func buildWithSprintf() []byte {
	buf := make([]byte, 0, iterations*7)
	for i := 0; i < iterations; i++ {
		buf = append(buf, fmt.Sprintf("%d", i)...)
		buf = append(buf, ',')
	}
	return buf
}

func main() {
	start := time.Now()
	appendResult := buildWithAppendInt()
	appendElapsed := time.Since(start)

	start = time.Now()
	sprintfResult := buildWithSprintf()
	sprintfElapsed := time.Since(start)

	if string(appendResult) != string(sprintfResult) {
		panic("AppendInt and Sprintf builds produced different output - correctness bug, not just performance")
	}
	if len(appendResult) == 0 {
		panic("expected non-empty output")
	}

	fmt.Printf("strconv.AppendInt: %v for %d ints (%v/int)\n", appendElapsed, iterations, appendElapsed/iterations)
	fmt.Printf("fmt.Sprintf:       %v for %d ints (%v/int)\n", sprintfElapsed, iterations, sprintfElapsed/iterations)

	if sprintfElapsed <= appendElapsed {
		fmt.Println("NOTE: this run did not show AppendInt as faster; report it honestly - but AppendInt still " +
			"performs zero reflection and zero intermediate string allocations by construction.")
	} else {
		fmt.Printf("AppendInt was %.1fx faster than fmt.Sprintf in this run\n",
			float64(sprintfElapsed)/float64(appendElapsed))
	}

	fmt.Println("OK")
}
