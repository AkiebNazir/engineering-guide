/*
LEVEL 02 (core) - SortFunc, Reverse, Equal - and the pre-1.21 loop they replace

You will learn
  - slices.SortFunc(s, cmp) sorts by a custom comparator returning an int
    (negative/zero/positive), the only way to sort a slice of STRUCTS, which
    have no natural ordering
  - slices.Reverse(s) reverses a slice in place
  - slices.Equal(a, b) compares two slices element-by-element - the generic
    replacement for a hand-written length+loop comparison

Run: go run ./GoStdLib/15_slices/level_02_sortfunc_reverse_equal
*/

package main

import (
	"fmt"
	"slices"
)

type person struct {
	name string
	age  int
}

func main() {
	people := []person{
		{"Carol", 35},
		{"Alice", 30},
		{"Bob", 25},
	}

	// SortFunc: negative means a sorts before b, zero means equal, positive
	// means a sorts after b - sort by age, ascending.
	slices.SortFunc(people, func(a, b person) int {
		return a.age - b.age
	})
	wantOrder := []string{"Bob", "Alice", "Carol"}
	for i, name := range wantOrder {
		if people[i].name != name {
			panic(fmt.Sprintf("people[%d].name = %q, want %q (order: %v)", i, people[i].name, name, people))
		}
	}

	// Reverse: in place, no return value.
	slices.Reverse(people)
	wantReversed := []string{"Carol", "Alice", "Bob"}
	for i, name := range wantReversed {
		if people[i].name != name {
			panic(fmt.Sprintf("after Reverse, people[%d].name = %q, want %q", i, people[i].name, name))
		}
	}

	// Equal: element-by-element comparison for comparable element types.
	a := []int{1, 2, 3}
	b := []int{1, 2, 3}
	c := []int{1, 2, 4}
	if !slices.Equal(a, b) {
		panic(fmt.Sprintf("slices.Equal(%v, %v) = false, want true", a, b))
	}
	if slices.Equal(a, c) {
		panic(fmt.Sprintf("slices.Equal(%v, %v) = true, want false", a, c))
	}

	// --- pre-1.21 contrast: what Equal and Reverse looked like by hand.
	manualEqual := func(x, y []int) bool {
		if len(x) != len(y) {
			return false
		}
		for i := range x {
			if x[i] != y[i] {
				return false
			}
		}
		return true
	} // 8 lines
	if manualEqual(a, b) != slices.Equal(a, b) {
		panic("manualEqual and slices.Equal disagree on (a, b)")
	}

	manualReverse := func(s []int) {
		for i, j := 0, len(s)-1; i < j; i, j = i+1, j-1 {
			s[i], s[j] = s[j], s[i]
		}
	} // 4 lines, vs slices.Reverse's 1
	nums := []int{1, 2, 3, 4}
	manualReverse(nums)
	if !slices.Equal(nums, []int{4, 3, 2, 1}) {
		panic(fmt.Sprintf("manualReverse produced %v, want [4 3 2 1]", nums))
	}

	fmt.Printf("sorted then reversed by age: %v\n", people)
	fmt.Println("OK")
}
