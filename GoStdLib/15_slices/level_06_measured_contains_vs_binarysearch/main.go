/*
LEVEL 06 (advanced) - MEASURED: linear Contains vs. BinarySearch on a big sorted slice

You will learn
  - slices.Contains is O(n): it scans from the start until it finds a match
    or runs out of slice
  - slices.BinarySearch is O(log n) but REQUIRES sorted input
  - this level builds one large sorted slice and times looking up the SAME
    set of values with both approaches, with time.Now()/time.Since() - real
    numbers from this run, not an assumed Big-O story

Run: go run ./GoStdLib/15_slices/level_06_measured_contains_vs_binarysearch
*/

package main

import (
	"fmt"
	"slices"
	"time"
)

func main() {
	const n = 1_000_000
	const lookups = 2_000

	sorted := make([]int, n)
	for i := range sorted {
		sorted[i] = i * 2 // sorted, evenly spaced, so half the lookups miss
	}

	// Look up `lookups` values scattered across the whole range.
	targets := make([]int, lookups)
	for i := range targets {
		targets[i] = (i * 997) % (n * 2) // spread across [0, 2n), some present, some not
	}

	// Correctness check before timing: both must agree on every target.
	for _, t := range targets {
		wantFound := t%2 == 0 && t/2 < n
		gotContains := slices.Contains(sorted, t)
		_, gotBinary := slices.BinarySearch(sorted, t)
		if gotContains != wantFound {
			panic(fmt.Sprintf("slices.Contains(sorted, %d) = %v, want %v", t, gotContains, wantFound))
		}
		if gotBinary != wantFound {
			panic(fmt.Sprintf("slices.BinarySearch(sorted, %d) found=%v, want %v", t, gotBinary, wantFound))
		}
	}

	linearHits := 0
	startLinear := time.Now()
	for _, t := range targets {
		if slices.Contains(sorted, t) {
			linearHits++
		}
	}
	durLinear := time.Since(startLinear)

	binaryHits := 0
	startBinary := time.Now()
	for _, t := range targets {
		if _, ok := slices.BinarySearch(sorted, t); ok {
			binaryHits++
		}
	}
	durBinary := time.Since(startBinary)

	// Both timing passes must have found the same number of matches - keeps
	// the benchmark honest (not just fast because it stopped checking).
	if linearHits != binaryHits {
		panic(fmt.Sprintf("linearHits=%d binaryHits=%d, want equal", linearHits, binaryHits))
	}

	fmt.Printf("slices.Contains,    %d lookups over %d elements: %v (%v/op)\n", lookups, n, durLinear, durLinear/lookups)
	fmt.Printf("slices.BinarySearch, %d lookups over %d elements: %v (%v/op)\n", lookups, n, durBinary, durBinary/lookups)

	if durBinary > durLinear {
		panic(fmt.Sprintf("BinarySearch (%v) was slower than linear Contains (%v) on %d elements; expected the opposite at this scale", durBinary, durLinear, n))
	}

	speedup := float64(durLinear) / float64(durBinary)
	fmt.Printf("BinarySearch was %.0fx faster in this run\n", speedup)
	fmt.Println("OK")
}
