/*
LEVEL 01 (basic) - the convenience wrappers: Ints, Strings, Float64s

You will learn
  - sort.Ints/sort.Strings/sort.Float64s sort a []int/[]string/[]float64 in
    place, ascending - the single most common use of the sort package
  - each has an -AreSorted check (sort.IntsAreSorted etc.) to test without mutating
  - these are thin wrappers around sort.Sort with a built-in ordering - they
    exist so the overwhelmingly common case needs no comparator at all

Run: go run ./GoStdLib/12_sort/level_01_ints_strings_float64s
*/

package main

import (
	"fmt"
	"sort"
)

func main() {
	ints := []int{5, 2, 4, 1, 3}
	if sort.IntsAreSorted(ints) {
		panic("FAILED to set up the example: ints should start unsorted")
	}
	sort.Ints(ints)
	wantInts := []int{1, 2, 3, 4, 5}
	for i := range wantInts {
		if ints[i] != wantInts[i] {
			panic(fmt.Sprintf("ints[%d] = %d, want %d", i, ints[i], wantInts[i]))
		}
	}
	if !sort.IntsAreSorted(ints) {
		panic("IntsAreSorted should be true after sort.Ints")
	}

	strs := []string{"banana", "apple", "cherry"}
	sort.Strings(strs)
	wantStrs := []string{"apple", "banana", "cherry"}
	for i := range wantStrs {
		if strs[i] != wantStrs[i] {
			panic(fmt.Sprintf("strs[%d] = %q, want %q", i, strs[i], wantStrs[i]))
		}
	}

	floats := []float64{3.3, 1.1, 2.2}
	sort.Float64s(floats)
	wantFloats := []float64{1.1, 2.2, 3.3}
	for i := range wantFloats {
		if floats[i] != wantFloats[i] {
			panic(fmt.Sprintf("floats[%d] = %v, want %v", i, floats[i], wantFloats[i]))
		}
	}

	fmt.Printf("ints=%v strings=%v floats=%v\n", ints, strs, floats)
	fmt.Println("OK")
}
