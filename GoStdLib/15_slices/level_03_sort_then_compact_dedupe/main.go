/*
LEVEL 03 (advanced) - the standard dedupe idiom: Sort, then Compact

You will learn
  - slices.Compact(s) removes ADJACENT duplicate elements in place, returning
    the shortened slice
  - Compact does NOT sort for you - it only collapses duplicates that are
    already next to each other, so the idiom is always Sort THEN Compact,
    same requirement as Python's itertools.groupby
  - this level proves both halves: Compact alone on unsorted input misses
    duplicates; Sort first, then Compact, catches all of them

Run: go run ./GoStdLib/15_slices/level_03_sort_then_compact_dedupe
*/

package main

import (
	"fmt"
	"slices"
)

func main() {
	raw := []int{3, 1, 2, 3, 1, 4, 2}

	// The correct idiom: Sort first, so equal elements become adjacent...
	sorted := slices.Clone(raw) // Clone so we still have `raw` untouched below
	slices.Sort(sorted)
	wantSorted := []int{1, 1, 2, 2, 3, 3, 4}
	if !slices.Equal(sorted, wantSorted) {
		panic(fmt.Sprintf("sorted = %v, want %v", sorted, wantSorted))
	}

	// ...THEN Compact collapses every run of adjacent equal values to one.
	// NOTE: Compact works IN PLACE on sorted's backing array and, per its
	// documented contract, zeroes the elements between the new and old
	// length - so `sorted` itself becomes stale/observably changed after
	// this call. Always use the returned slice, never the pre-Compact
	// variable, for anything past this point.
	deduped := slices.Compact(sorted)
	wantDeduped := []int{1, 2, 3, 4}
	if !slices.Equal(deduped, wantDeduped) {
		panic(fmt.Sprintf("slices.Compact(sorted) = %v, want %v", deduped, wantDeduped))
	}
	// Prove the documented zeroing behavior for real: the ORIGINAL 7-element
	// backing array now reads as the 4 deduped values followed by zeros.
	if sorted[0] != 1 || sorted[3] != 4 {
		panic(fmt.Sprintf("expected sorted's backing array to start with the deduped values, got %v", sorted))
	}
	if sorted[4] != 0 || sorted[5] != 0 || sorted[6] != 0 {
		panic(fmt.Sprintf("expected Compact to zero the tail of sorted's backing array, got %v", sorted))
	}

	// A slice with no duplicates at all is returned unchanged in content
	// (length equal, same elements).
	noDupes := []string{"a", "b", "c"}
	compactedNoDupes := slices.Compact(noDupes)
	if !slices.Equal(compactedNoDupes, []string{"a", "b", "c"}) {
		panic(fmt.Sprintf("Compact on a no-duplicate slice changed content: %v", compactedNoDupes))
	}

	// An empty slice is handled without panicking.
	var empty []int
	if got := slices.Compact(empty); len(got) != 0 {
		panic(fmt.Sprintf("slices.Compact(empty) = %v, want empty", got))
	}

	fmt.Printf("raw:                    %v\n", raw)
	fmt.Printf("sorted (now stale):     %v\n", sorted)
	fmt.Printf("deduped (use this one): %v\n", deduped)
	fmt.Println("OK")
}
