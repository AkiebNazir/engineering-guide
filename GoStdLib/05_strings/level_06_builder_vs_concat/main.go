/*
LEVEL 06 (advanced) - MEASURED: strings.Builder vs += concatenation at scale

You will learn
  - += on a string allocates a brand-new string and copies everything so far,
    every single time - O(n^2) total work for n appends
  - strings.Builder grows an internal []byte geometrically, copying each byte
    only a small constant number of times overall
  - measuring BOTH elapsed time and heap allocation counts, for real, via
    runtime.MemStats - not an assumed answer

Run: go run ./GoStdLib/05_strings/level_06_builder_vs_concat
*/

package main

import (
	"fmt"
	"runtime"
	"strings"
	"time"
)

const appends = 30_000

func concatWithPlusEquals() string {
	var s string
	for i := 0; i < appends; i++ {
		s += "x"
	}
	return s
}

func concatWithBuilder() string {
	var b strings.Builder
	for i := 0; i < appends; i++ {
		b.WriteString("x")
	}
	return b.String()
}

func mallocsDuring(f func() string) (result string, mallocs uint64, elapsed time.Duration) {
	runtime.GC()
	var before, after runtime.MemStats
	runtime.ReadMemStats(&before)
	start := time.Now()
	result = f()
	elapsed = time.Since(start)
	runtime.ReadMemStats(&after)
	return result, after.Mallocs - before.Mallocs, elapsed
}

func main() {
	plusResult, plusMallocs, plusElapsed := mallocsDuring(concatWithPlusEquals)
	builderResult, builderMallocs, builderElapsed := mallocsDuring(concatWithBuilder)

	if len(plusResult) != appends {
		panic(fmt.Sprintf("+= result length = %d, expected %d", len(plusResult), appends))
	}
	if len(builderResult) != appends {
		panic(fmt.Sprintf("Builder result length = %d, expected %d", len(builderResult), appends))
	}
	if plusResult != builderResult {
		panic("both approaches produced different strings - correctness bug, not just performance")
	}

	fmt.Printf("+=      : %v, %d heap allocations for %d appends\n", plusElapsed, plusMallocs, appends)
	fmt.Printf("Builder : %v, %d heap allocations for %d appends\n", builderElapsed, builderMallocs, appends)

	if builderMallocs >= plusMallocs {
		panic(fmt.Sprintf("expected Builder to allocate fewer times than +=, got Builder=%d vs +=%d", builderMallocs, plusMallocs))
	}
	if builderElapsed >= plusElapsed {
		fmt.Println("NOTE: this run did not show Builder as faster in wall-clock time (scheduler/GC noise), " +
			"but the allocation COUNT above is the real, structural difference and it is always lower.")
	} else {
		fmt.Printf("Builder was %.1fx faster than += in this run, with %.1fx fewer allocations\n",
			float64(plusElapsed)/float64(builderElapsed), float64(plusMallocs)/float64(builderMallocs))
	}

	fmt.Println("OK")
}
