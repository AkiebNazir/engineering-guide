/*
LEVEL 08 (interop) - sorting []time.Time with sort.Slice and .Before()

You will learn
  - time.Time cannot be compared with < or > (see GoStdLib/11_time) - a
    Less closure for sort.Slice must call t.Before(other) instead
  - this is the general lesson for sorting ANY non-primitive value: the
    comparator lives in sort's closure, the comparison itself lives on the
    value's own type

Run: go run ./GoStdLib/12_sort/level_08_sort_time_values
*/

package main

import (
	"fmt"
	"sort"
	"time"
)

type event struct {
	name string
	at   time.Time
}

func main() {
	base := time.Date(2024, time.January, 1, 0, 0, 0, 0, time.UTC)
	events := []event{
		{"launch", base.Add(48 * time.Hour)},
		{"kickoff", base},
		{"review", base.Add(24 * time.Hour)},
		{"retro", base.Add(72 * time.Hour)},
	}

	sort.Slice(events, func(i, j int) bool {
		return events[i].at.Before(events[j].at)
	})

	want := []string{"kickoff", "review", "launch", "retro"}
	for i, name := range want {
		if events[i].name != name {
			panic(fmt.Sprintf("index %d: got %q, want %q (order: %v)", i, events[i].name, name, events))
		}
	}
	for i := 1; i < len(events); i++ {
		if !events[i].at.After(events[i-1].at) {
			panic(fmt.Sprintf("events not strictly increasing at index %d: %v then %v", i, events[i-1].at, events[i].at))
		}
	}

	// sort.SliceIsSorted works the same way against a time-based Less.
	if !sort.SliceIsSorted(events, func(i, j int) bool { return events[i].at.Before(events[j].at) }) {
		panic("SliceIsSorted should confirm the chronological order")
	}

	for _, e := range events {
		fmt.Printf("%-8s %s\n", e.name, e.at.Format("2006-01-02 15:04:05"))
	}
	fmt.Println("OK")
}
