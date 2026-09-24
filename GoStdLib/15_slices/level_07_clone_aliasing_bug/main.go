/*
LEVEL 07 (advanced) - design concern: slice aliasing, and Clone as the fix

You will learn
  - a slice header is just (pointer, length, capacity) - assigning it, or
    reslicing it, copies the HEADER, not the underlying array
  - "making a copy to mutate safely" by writing cp := s (or cp := s[:len(s)])
    does NOT give you an independent array - mutating cp mutates s too
  - slices.Clone(s) allocates a genuinely new backing array and copies the
    elements into it - THAT is what makes mutation safe
  - this level demonstrates the bug ACTUALLY HAPPENING (not just described),
    then fixes it

Run: go run ./GoStdLib/15_slices/level_07_clone_aliasing_bug
*/

package main

import (
	"fmt"
	"slices"
)

func main() {
	original := []int{1, 2, 3, 4, 5}

	// --- THE BUG: this "copy" is not a copy at all.
	fakeCopy := original // just copies the (pointer, len, cap) header
	fakeCopy[0] = 999

	// The mutation through fakeCopy is visible through `original` too,
	// because both headers point at the SAME backing array. This is the bug
	// actually happening, not a claim about it.
	if original[0] != 999 {
		panic(fmt.Sprintf("expected the aliasing bug to have mutated original[0] to 999, got %d - test setup is wrong", original[0]))
	}
	fmt.Printf("after mutating fakeCopy[0]: original = %v (bug: it changed too!)\n", original)

	// Reslicing exhibits the exact same aliasing - a sub-slice still shares
	// the parent's backing array.
	original = []int{1, 2, 3, 4, 5} // reset
	sub := original[1:3]            // {2, 3}, but backed by original's array
	sub[0] = 777
	if original[1] != 777 {
		panic(fmt.Sprintf("expected reslicing aliasing to have mutated original[1] to 777, got %d", original[1]))
	}
	fmt.Printf("after mutating sub[0]: original = %v (same bug via reslicing)\n", original)

	// --- THE FIX: slices.Clone allocates a real, independent backing array.
	original = []int{1, 2, 3, 4, 5} // reset again
	realCopy := slices.Clone(original)
	realCopy[0] = 999

	if original[0] != 1 {
		panic(fmt.Sprintf("original[0] = %d, want 1 (unchanged) after mutating a real Clone", original[0]))
	}
	if realCopy[0] != 999 {
		panic(fmt.Sprintf("realCopy[0] = %d, want 999", realCopy[0]))
	}
	if slices.Equal(original, realCopy) {
		panic("original and realCopy are equal after mutating the clone, want them to differ")
	}

	// Clone of a nil slice is nil, not an empty non-nil slice - worth
	// knowing since it affects == nil checks downstream.
	var nilSlice []int
	if cloned := slices.Clone(nilSlice); cloned != nil {
		panic(fmt.Sprintf("slices.Clone(nil) = %v, want nil", cloned))
	}

	fmt.Printf("original stayed %v, independent clone became modified\n", original)
	fmt.Println("OK")
}
