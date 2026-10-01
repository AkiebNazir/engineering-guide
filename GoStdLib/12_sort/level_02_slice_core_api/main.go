/*
LEVEL 02 (core) - Slice, SliceStable, Sort, Reverse, IsSorted: 90% of real usage

You will learn
  - sort.Slice(x, less) sorts any slice with a closure comparator - no type
    needs to implement anything, "less" just takes two indexes
  - sort.SliceStable is the same, but equal elements keep their relative
    input order (level 9 shows a case where that difference is observable)
  - sort.Sort(data) takes anything implementing sort.Interface (Len/Less/Swap)
    - sort.IntSlice/StringSlice/Float64Slice are built-in Interface
    implementations over plain slices (level 7 goes deeper on these)
  - sort.Reverse(data) wraps any sort.Interface and flips Less - it does NOT
    sort descending itself, it makes the wrapped type look reversed to Sort
  - sort.SliceIsSorted(x, less) checks without sorting, mirroring IsSorted

Run: go run ./GoStdLib/12_sort/level_02_slice_core_api
*/

package main

import (
	"fmt"
	"sort"
)

type person struct {
	name string
	age  int
}

func main() {
	people := []person{
		{"Grace", 34}, {"Ada", 28}, {"Alan", 41}, {"Katherine", 28},
	}

	if sort.SliceIsSorted(people, func(i, j int) bool { return people[i].age < people[j].age }) {
		panic("FAILED to set up the example: people should start unsorted by age")
	}

	sort.Slice(people, func(i, j int) bool { return people[i].age < people[j].age })
	for i := 1; i < len(people); i++ {
		if people[i].age < people[i-1].age {
			panic(fmt.Sprintf("not sorted at index %d: %v", i, people))
		}
	}
	if !sort.SliceIsSorted(people, func(i, j int) bool { return people[i].age < people[j].age }) {
		panic("SliceIsSorted should be true right after sort.Slice")
	}

	// SliceStable: same comparator, but ties keep their relative input order.
	byName := []person{{"Bob", 1}, {"Amy", 1}, {"Cid", 1}}
	sort.SliceStable(byName, func(i, j int) bool { return byName[i].age < byName[j].age })
	if byName[0].name != "Bob" || byName[1].name != "Amy" || byName[2].name != "Cid" {
		panic(fmt.Sprintf("SliceStable should preserve input order among equal ages, got %v", byName))
	}

	// sort.Sort + sort.Reverse over a built-in Interface implementation.
	ages := sort.IntSlice{34, 28, 41, 28}
	sort.Sort(ages)
	if ages[0] != 28 || ages[len(ages)-1] != 41 {
		panic(fmt.Sprintf("ascending sort wrong: %v", ages))
	}
	sort.Sort(sort.Reverse(ages))
	if ages[0] != 41 || ages[len(ages)-1] != 28 {
		panic(fmt.Sprintf("sort.Reverse should flip to descending: %v", ages))
	}

	fmt.Printf("people by age: %v\n", people)
	fmt.Printf("stable ties preserved: %v\n", byName)
	fmt.Printf("ages descending via Reverse: %v\n", ages)
	fmt.Println("OK")
}
