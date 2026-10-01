/*
LEVEL 05 (advanced) - Insert and Delete: maintaining an ordered slice

You will learn
  - slices.Insert(s, i, values...) inserts values at index i, shifting
    everything from i onward to the right (may reallocate if capacity is
    exceeded)
  - slices.Delete(s, i, j) removes elements [i:j), shifting everything after
    j left to fill the gap - it returns the shortened slice; the original
    slice header's length is now stale and must be replaced with the result
  - combined with BinarySearch (level 4), this is how you maintain a sorted
    slice as a simple, allocation-light alternative to a balanced tree for
    small/medium N

Run: go run ./GoStdLib/15_slices/level_05_insert_delete
*/

package main

import (
	"fmt"
	"slices"
)

func main() {
	s := []string{"a", "b", "d", "e"}

	// Insert "c" at index 2, between "b" and "d".
	s = slices.Insert(s, 2, "c")
	want := []string{"a", "b", "c", "d", "e"}
	if !slices.Equal(s, want) {
		panic(fmt.Sprintf("after Insert, s = %v, want %v", s, want))
	}

	// Insert can take multiple values at once, all landing at index i in order.
	s = slices.Insert(s, 0, "x", "y")
	want = []string{"x", "y", "a", "b", "c", "d", "e"}
	if !slices.Equal(s, want) {
		panic(fmt.Sprintf("after multi-value Insert, s = %v, want %v", s, want))
	}

	// Delete [0:2) removes "x" and "y" - note j is exclusive, same as a slice
	// expression s[i:j].
	s = slices.Delete(s, 0, 2)
	want = []string{"a", "b", "c", "d", "e"}
	if !slices.Equal(s, want) {
		panic(fmt.Sprintf("after Delete(s, 0, 2), s = %v, want %v", s, want))
	}

	// Deleting a single element uses Delete(s, i, i+1).
	s = slices.Delete(s, 2, 3) // removes "c"
	want = []string{"a", "b", "d", "e"}
	if !slices.Equal(s, want) {
		panic(fmt.Sprintf("after Delete(s, 2, 3), s = %v, want %v", s, want))
	}

	// The trap Delete guards against: you MUST reassign the result. Delete
	// shifts elements left and zeroes the freed tail slot IN PLACE, on the
	// SAME backing array s already points at - so even though we assign the
	// return value to a new name below, `s`'s own backing array is mutated
	// by this call. Prove it for real: after calling Delete without
	// reassigning s, reading s directly already shows the shifted, zeroed
	// content, not the pre-call state.
	before := len(s)
	beforeContent := slices.Clone(s) // snapshot, since s's backing array is about to mutate
	after := slices.Delete(s, 0, 1)  // removes "a"; mutates s's backing array as a side effect
	if len(after) != before-1 {
		panic(fmt.Sprintf("len(after) = %d, want %d", len(after), before-1))
	}
	if slices.Equal(s, beforeContent) {
		panic(fmt.Sprintf("expected s's backing array to be mutated by Delete even though s itself wasn't reassigned: still %v", s))
	}

	// The fix: reassign, exactly as done at every earlier step in this file.
	s = after
	want = []string{"b", "d", "e"}
	if !slices.Equal(s, want) {
		panic(fmt.Sprintf("after reassigning s = after, s = %v, want %v", s, want))
	}

	fmt.Printf("final slice: %v\n", s)
	fmt.Println("OK")
}
