/*
LEVEL 04 (advanced) - handling BinarySearch's not-found result for real

You will learn
  - slices.BinarySearch(s, target) returns (index, found bool) on a SORTED
    slice: if found is true, index is where target lives; if found is
    false, index is where target WOULD be inserted to keep s sorted
  - this is the "error handling" level adapted to this package: instead of
    an error value, absence is signaled by the bool - and it must be
    checked, exactly like an error, before trusting the index

Run: go run ./GoStdLib/15_slices/level_04_binarysearch_not_found
*/

package main

import (
	"fmt"
	"slices"
)

func main() {
	sorted := []int{10, 20, 30, 40, 50}

	// Found case: index points AT the match.
	idx, found := slices.BinarySearch(sorted, 30)
	if !found {
		panic(fmt.Sprintf("slices.BinarySearch(sorted, 30) found=false, want true"))
	}
	if idx != 2 {
		panic(fmt.Sprintf("slices.BinarySearch(sorted, 30) index=%d, want 2", idx))
	}

	// Not-found case, triggered for REAL: found is false, and the index is
	// the correct insertion point, not a sentinel like -1.
	idx, found = slices.BinarySearch(sorted, 25)
	if found {
		panic("slices.BinarySearch(sorted, 25) found=true, want false: 25 is not in the slice")
	}
	if idx != 2 {
		panic(fmt.Sprintf("insertion point for 25 = %d, want 2 (between 20 and 30)", idx))
	}

	// Below everything: insertion point 0.
	idx, found = slices.BinarySearch(sorted, 5)
	if found || idx != 0 {
		panic(fmt.Sprintf("BinarySearch(sorted, 5) = (%d, %v), want (0, false)", idx, found))
	}

	// Above everything: insertion point len(s).
	idx, found = slices.BinarySearch(sorted, 999)
	if found || idx != len(sorted) {
		panic(fmt.Sprintf("BinarySearch(sorted, 999) = (%d, %v), want (%d, false)", idx, found, len(sorted)))
	}

	// The "handle it, don't just describe it" part: use the not-found result
	// to actually insert 25 in the right place and re-check.
	idx, found = slices.BinarySearch(sorted, 25)
	if found {
		panic("expected 25 to still be absent before insertion")
	}
	sorted = slices.Insert(sorted, idx, 25)
	wantAfterInsert := []int{10, 20, 25, 30, 40, 50}
	if !slices.Equal(sorted, wantAfterInsert) {
		panic(fmt.Sprintf("after inserting 25 at index %d, sorted = %v, want %v", idx, sorted, wantAfterInsert))
	}
	// Now it really is found.
	if _, found := slices.BinarySearch(sorted, 25); !found {
		panic("25 not found after inserting it at the correct sorted position")
	}

	fmt.Printf("final sorted slice: %v\n", sorted)
	fmt.Println("OK")
}
