/*
LEVEL 08 (advanced) - slices + sort interop: SortFunc vs. the older sort.Slice

You will learn
  - the old standard way to sort a struct slice was sort.Slice(s, less),
    where less takes two INDEXES and returns a bool - it needs a closure
    capturing s to index into it
  - slices.SortFunc(s, cmp) takes the two ELEMENTS directly and returns an
    int (negative/zero/positive) - no indexing, no closure capture needed
  - both sort the SAME data the SAME way; this level runs both and checks
    they agree, then contrasts the code shape

Run: go run ./GoStdLib/15_slices/level_08_interop_sort_package
*/

package main

import (
	"cmp"
	"fmt"
	"slices"
	"sort"
)

type task struct {
	name     string
	priority int
}

func main() {
	tasksA := []task{
		{"deploy", 2},
		{"write tests", 1},
		{"fix bug", 3},
		{"review PR", 1},
	}
	tasksB := slices.Clone(tasksA) // independent copy - see level 7 for why Clone matters here

	// --- the pre-1.21 way: sort.Slice, index-based less func, closure over s.
	sort.Slice(tasksA, func(i, j int) bool {
		return tasksA[i].priority < tasksA[j].priority
	}) // 3 lines, indexes into the closed-over slice

	// --- the slices-package way: SortFunc, element-based comparator.
	slices.SortFunc(tasksB, func(a, b task) int {
		return cmp.Compare(a.priority, b.priority)
	}) // 3 lines too, but a, b are the elements themselves - no indexing

	// Both must produce the identical order for identical input.
	for i := range tasksA {
		if tasksA[i] != tasksB[i] {
			panic(fmt.Sprintf("tasksA[%d] = %+v, tasksB[%d] = %+v, want equal", i, tasksA[i], i, tasksB[i]))
		}
	}

	wantOrder := []string{"write tests", "review PR", "deploy", "fix bug"}
	for i, name := range wantOrder {
		if tasksA[i].name != name {
			panic(fmt.Sprintf("tasksA[%d].name = %q, want %q (full: %v)", i, tasksA[i].name, name, tasksA))
		}
	}

	// sort.Slice is NOT stable - equal-priority items ("write tests" and
	// "review PR", both priority 1) may or may not keep their original
	// relative order. slices.SortStableFunc exists for when that matters;
	// plain SortFunc makes the same no-stability trade-off as sort.Slice.
	stableB := slices.Clone(tasksA)
	slices.SortStableFunc(stableB, func(a, b task) int {
		return cmp.Compare(a.priority, b.priority)
	})
	// With a stable sort, "write tests" (originally before "review PR" in
	// the ORIGINAL input) must still precede it after sorting by priority.
	idxWriteTests := slices.IndexFunc(stableB, func(t task) bool { return t.name == "write tests" })
	idxReviewPR := slices.IndexFunc(stableB, func(t task) bool { return t.name == "review PR" })
	if idxWriteTests > idxReviewPR {
		panic(fmt.Sprintf("stable sort put write tests (%d) after review PR (%d), want stable original order preserved", idxWriteTests, idxReviewPR))
	}

	fmt.Printf("sorted by priority (SortFunc): %v\n", tasksB)
	fmt.Println("OK")
}
