/*
LEVEL 01 (basic) - slices.Sort, slices.Contains, slices.Index

You will learn
  - slices.Sort(s) sorts a slice of any ordered type (numbers, strings) IN
    PLACE, ascending - no comparator needed for built-in ordered types
  - slices.Contains(s, v) reports whether v is anywhere in s
  - slices.Index(s, v) returns the first index of v, or -1 if absent - the
    generic replacement for a hand-rolled linear search

Run: go run ./GoStdLib/15_slices/level_01_sort_contains_index
*/

package main

import (
	"fmt"
	"slices"
)

func main() {
	nums := []int{5, 3, 1, 4, 2}

	// The single most common use: sort in place, ascending.
	slices.Sort(nums)
	want := []int{1, 2, 3, 4, 5}
	if !slices.Equal(nums, want) {
		panic(fmt.Sprintf("after Sort, nums = %v, want %v", nums, want))
	}

	// Contains: a plain membership check.
	if !slices.Contains(nums, 3) {
		panic("slices.Contains(nums, 3) = false, want true")
	}
	if slices.Contains(nums, 99) {
		panic("slices.Contains(nums, 99) = true, want false")
	}

	// Index: position of the first match, or -1.
	if idx := slices.Index(nums, 4); idx != 3 {
		panic(fmt.Sprintf("slices.Index(nums, 4) = %d, want 3", idx))
	}
	if idx := slices.Index(nums, 99); idx != -1 {
		panic(fmt.Sprintf("slices.Index(nums, 99) = %d, want -1", idx))
	}

	// Works identically for strings - same generic functions, no reimplementing.
	words := []string{"banana", "apple", "cherry"}
	slices.Sort(words)
	wantWords := []string{"apple", "banana", "cherry"}
	if !slices.Equal(words, wantWords) {
		panic(fmt.Sprintf("after Sort, words = %v, want %v", words, wantWords))
	}

	fmt.Printf("sorted nums:  %v\n", nums)
	fmt.Printf("sorted words: %v\n", words)
	fmt.Println("OK")
}
