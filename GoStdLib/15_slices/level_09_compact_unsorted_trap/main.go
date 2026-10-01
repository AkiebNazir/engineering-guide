/*
LEVEL 09 (advanced) - production trap: Compact on an unsorted slice looks fine, isn't

You will learn
  - slices.Compact only removes ADJACENT duplicates - it never looks further
    than the immediate neighbor
  - calling Compact on unsorted data compiles, runs, panics on nothing, and
    returns a WRONG answer: non-adjacent duplicates survive silently
  - the fix is always Sort before Compact (level 3) - there is no
    "Compact that also sorts" to reach for by mistake

Run: go run ./GoStdLib/15_slices/level_09_compact_unsorted_trap
*/

package main

import (
	"fmt"
	"slices"
)

func main() {
	// 1 and 3 each appear twice, but NOT adjacently.
	unsorted := []int{1, 3, 1, 2, 3}

	// --- THE TRAP: this runs cleanly and returns something that LOOKS like
	// a deduped slice, but isn't - it silently misbehaves.
	buggy := slices.Compact(slices.Clone(unsorted))
	if len(buggy) != len(unsorted) {
		panic(fmt.Sprintf("expected Compact on unsorted input to remove NOTHING here (no adjacent dupes), got len %d from %v -> %v", len(buggy), unsorted, buggy))
	}
	// The duplicates are still there - just not caught, because none of
	// them were adjacent in the original order.
	count1, count3 := 0, 0
	for _, v := range buggy {
		if v == 1 {
			count1++
		}
		if v == 3 {
			count3++
		}
	}
	if count1 != 2 || count3 != 2 {
		panic(fmt.Sprintf("expected duplicates to survive Compact on unsorted input: buggy=%v count1=%d count3=%d", buggy, count1, count3))
	}
	fmt.Printf("BUG demonstrated: Compact on unsorted %v gave %v - duplicates of 1 and 3 both survived\n", unsorted, buggy)

	// --- THE FIX: sort first, so equal elements become adjacent, then Compact.
	fixed := slices.Clone(unsorted)
	slices.Sort(fixed)
	fixed = slices.Compact(fixed)
	want := []int{1, 2, 3}
	if !slices.Equal(fixed, want) {
		panic(fmt.Sprintf("Sort+Compact gave %v, want %v", fixed, want))
	}

	fmt.Printf("FIXED: Sort then Compact on %v gave %v\n", unsorted, fixed)
	fmt.Println("OK")
}
