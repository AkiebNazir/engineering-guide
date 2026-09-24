/*
LEVEL 05 (intermediate pattern) - implementing sort.Interface yourself

You will learn
  - sort.Interface is exactly three methods: Len() int, Less(i, j int) bool,
    Swap(i, j int) - sort.Sort only ever calls these three, it never touches
    your fields directly
  - implementing it on a named slice type is the type-safe alternative to
    sort.Slice's closures - the compiler checks Less/Swap match Len, and the
    type documents its own default ordering
  - sort.Reverse works on ANY sort.Interface, including your own - it wraps
    the type and swaps the meaning of Less, so you write ascending logic once

Run: go run ./GoStdLib/12_sort/level_05_sort_interface
*/

package main

import (
	"fmt"
	"sort"
)

type track struct {
	title   string
	seconds int
}

// byDuration implements sort.Interface directly on a []track, ascending by seconds.
type byDuration []track

func (b byDuration) Len() int           { return len(b) }
func (b byDuration) Less(i, j int) bool { return b[i].seconds < b[j].seconds }
func (b byDuration) Swap(i, j int)      { b[i], b[j] = b[j], b[i] }

func main() {
	tracks := []track{
		{"Intro", 45},
		{"Main Theme", 210},
		{"Outro", 30},
		{"Bridge", 120},
	}

	sort.Sort(byDuration(tracks))
	wantAsc := []int{30, 45, 120, 210}
	for i, s := range wantAsc {
		if tracks[i].seconds != s {
			panic(fmt.Sprintf("ascending index %d: got %ds, want %ds (%v)", i, tracks[i].seconds, s, tracks))
		}
	}
	if !sort.IsSorted(byDuration(tracks)) {
		panic("sort.IsSorted should confirm the ascending order")
	}

	// sort.Reverse: the same Less, wrapped, flips the effective order.
	sort.Sort(sort.Reverse(byDuration(tracks)))
	wantDesc := []int{210, 120, 45, 30}
	for i, s := range wantDesc {
		if tracks[i].seconds != s {
			panic(fmt.Sprintf("descending index %d: got %ds, want %ds (%v)", i, tracks[i].seconds, s, tracks))
		}
	}

	fmt.Printf("ascending by duration then reversed: %v\n", tracks)
	fmt.Println("OK")
}
