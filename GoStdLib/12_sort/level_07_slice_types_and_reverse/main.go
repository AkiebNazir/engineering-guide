/*
LEVEL 07 (second intermediate pattern) - the named slice types: IntSlice, StringSlice, Float64Slice

You will learn
  - sort.IntSlice, sort.StringSlice, and sort.Float64Slice are not just
    labels - they are concrete types with Len/Less/Swap already implemented,
    which is exactly what sort.Ints/Strings/Float64s use internally
  - each also has its own Sort() method: sort.IntSlice(x).Sort() is
    equivalent to sort.Sort(sort.IntSlice(x)), just shorter to write
  - because they already satisfy sort.Interface, sort.Reverse composes with
    them directly with zero extra code - useful when you want descending
    order but don't want to write your own Less

Run: go run ./GoStdLib/12_sort/level_07_slice_types_and_reverse
*/

package main

import (
	"fmt"
	"sort"
)

func main() {
	names := sort.StringSlice{"Marco", "Ana", "Zoe", "Bilal"}

	// A named slice type's own Sort() method - shorthand for sort.Sort(names).
	names.Sort()
	want := []string{"Ana", "Bilal", "Marco", "Zoe"}
	for i, w := range want {
		if names[i] != w {
			panic(fmt.Sprintf("names[%d] = %q, want %q", i, names[i], w))
		}
	}
	if !sort.IsSorted(names) {
		panic("sort.IsSorted(names) should be true right after Sort()")
	}

	// sort.Reverse composes with the named type with no extra Less to write.
	sort.Sort(sort.Reverse(names))
	wantDesc := []string{"Zoe", "Marco", "Bilal", "Ana"}
	for i, w := range wantDesc {
		if names[i] != w {
			panic(fmt.Sprintf("descending names[%d] = %q, want %q", i, names[i], w))
		}
	}

	scores := sort.Float64Slice{9.5, 2.1, 7.7}
	sort.Sort(sort.Reverse(scores))
	if scores[0] != 9.5 || scores[len(scores)-1] != 2.1 {
		panic(fmt.Sprintf("descending scores wrong: %v", scores))
	}

	fmt.Printf("ascending then reversed names: %v\n", names)
	fmt.Printf("scores, descending via Reverse: %v\n", []float64(scores))
	fmt.Println("OK")
}
