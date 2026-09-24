/*
LEVEL 04 (error handling) - sort.Search's "not found" sentinel, misused for real

You will learn
  - sort.Search(n, f) binary-searches [0,n) for the smallest index i where
    f(i) is true - f must be false, then true, never back to false, which is
    exactly what "value >= target" gives you over an ascending sorted slice
  - the sort package has no dedicated error type - its one real failure mode
    is this: if f(i) is never true, Search returns n itself, ONE PAST THE
    END of the slice - indexing with that value panics with a real,
    triggerable "index out of range", not a returned error
  - the fix is the one line every correct use of Search needs: check the
    index is in range (and, for an exact-match search, that the value there
    actually equals the target) before using it

Run: go run ./GoStdLib/12_sort/level_04_search_out_of_range_error
*/

package main

import (
	"fmt"
	"sort"
)

func indexOf(sorted []int, target int) (idx int, found bool) {
	idx = sort.Search(len(sorted), func(i int) bool { return sorted[i] >= target })
	if idx < len(sorted) && sorted[idx] == target {
		return idx, true
	}
	return idx, false
}

func main() {
	sorted := []int{10, 20, 30, 40, 50}

	idx, found := indexOf(sorted, 30)
	if !found || idx != 2 {
		panic(fmt.Sprintf("indexOf(30) = (%d, %v), want (2, true)", idx, found))
	}

	// A target greater than every element: the predicate is never true, so
	// sort.Search returns len(sorted) - one index past the end, on purpose.
	rawIdx := sort.Search(len(sorted), func(i int) bool { return sorted[i] >= 999 })
	if rawIdx != len(sorted) {
		panic(fmt.Sprintf("sort.Search(999) = %d, want the not-found sentinel %d", rawIdx, len(sorted)))
	}

	// Triggered for real: indexing with the un-checked sentinel panics.
	panicked := func() (recovered bool) {
		defer func() {
			if r := recover(); r != nil {
				recovered = true
			}
		}()
		_ = sorted[rawIdx] // out of range on purpose
		return false
	}()
	if !panicked {
		panic("FAILED: indexing with the unchecked sentinel should have panicked")
	}

	// The fix: indexOf already checks the bound before indexing.
	_, found2 := indexOf(sorted, 999)
	if found2 {
		panic("indexOf(999) should report not found, not panic")
	}

	fmt.Printf("found 30 at index %d\n", idx)
	fmt.Printf("sort.Search(999) returned the sentinel %d; indexing it panicked as expected: %v\n", rawIdx, panicked)
	fmt.Println("OK")
}
