/*
LEVEL 10 (advanced) - capstone: a small record pipeline

You will learn
  - nothing new - this wires up levels 1-9 into one small realistic program:
    ingest records (possibly with duplicate IDs), Clone before mutating
    (level 7), Sort + Compact to dedupe by ID (levels 3/9), SortFunc to
    order by a different field (levels 2/8), BinarySearch for a lookup
    (levels 4/6), and Insert/Delete to apply an update (level 5)

Run: go run ./GoStdLib/15_slices/level_10_capstone_record_pipeline
*/

package main

import (
	"cmp"
	"fmt"
	"slices"
)

type record struct {
	id    int
	name  string
	score int
}

func main() {
	incoming := []record{
		{3, "carol", 88},
		{1, "alice", 95},
		{2, "bob", 70},
		{1, "alice", 95}, // duplicate ingest of the same record
		{4, "dave", 60},
	}

	// Never mutate the caller's slice in place - clone first (level 7).
	records := slices.Clone(incoming)

	// Dedupe by full equality: sort by id (so duplicates become adjacent),
	// then Compact removes the exact repeat of {1, alice, 95} (levels 3/9).
	slices.SortFunc(records, func(a, b record) int {
		return cmp.Compare(a.id, b.id)
	})
	records = slices.CompactFunc(records, func(a, b record) bool {
		return a == b
	})
	if len(records) != 4 {
		panic(fmt.Sprintf("len(records) after dedupe = %d, want 4: %v", len(records), records))
	}

	// Confirm sorted-by-id order and no leftover duplicate id 1.
	wantIDs := []int{1, 2, 3, 4}
	for i, id := range wantIDs {
		if records[i].id != id {
			panic(fmt.Sprintf("records[%d].id = %d, want %d (full: %v)", i, records[i].id, id, records))
		}
	}

	// Sorted by id -> BinarySearch to look up a record by id (levels 4/6).
	idx, found := slices.BinarySearchFunc(records, 3, func(r record, id int) int {
		return cmp.Compare(r.id, id)
	})
	if !found {
		panic("expected to find record with id 3")
	}
	if records[idx].name != "carol" {
		panic(fmt.Sprintf("records[idx].name = %q, want %q", records[idx].name, "carol"))
	}

	// Apply an update: remove dave (id 4, low score) and insert a new
	// record with id 5, keeping the slice sorted by id throughout (level 5).
	delIdx, found := slices.BinarySearchFunc(records, 4, func(r record, id int) int {
		return cmp.Compare(r.id, id)
	})
	if !found {
		panic("expected to find record with id 4 before deleting it")
	}
	records = slices.Delete(records, delIdx, delIdx+1)

	newRecord := record{5, "erin", 91}
	insIdx, found := slices.BinarySearchFunc(records, newRecord.id, func(r record, id int) int {
		return cmp.Compare(r.id, id)
	})
	if found {
		panic("expected id 5 to be absent before inserting it")
	}
	records = slices.Insert(records, insIdx, newRecord)

	wantFinalIDs := []int{1, 2, 3, 5}
	if len(records) != len(wantFinalIDs) {
		panic(fmt.Sprintf("final len(records) = %d, want %d: %v", len(records), len(wantFinalIDs), records))
	}
	for i, id := range wantFinalIDs {
		if records[i].id != id {
			panic(fmt.Sprintf("final records[%d].id = %d, want %d (full: %v)", i, records[i].id, id, records))
		}
	}

	// Finally, rank by score descending for a leaderboard view - a
	// completely different ordering of the SAME records (levels 2/8).
	leaderboard := slices.Clone(records)
	slices.SortFunc(leaderboard, func(a, b record) int {
		return cmp.Compare(b.score, a.score) // descending
	})
	if leaderboard[0].name != "alice" || leaderboard[0].score != 95 {
		panic(fmt.Sprintf("leaderboard[0] = %+v, want alice with score 95 on top", leaderboard[0]))
	}

	// The two views are independent slices (Clone did its job): reordering
	// leaderboard must not have touched records' id-sorted order.
	for i, id := range wantFinalIDs {
		if records[i].id != id {
			panic(fmt.Sprintf("records order was mutated by sorting leaderboard: records[%d].id = %d, want %d", i, records[i].id, id))
		}
	}

	fmt.Printf("records (by id):        %v\n", records)
	fmt.Printf("leaderboard (by score): %v\n", leaderboard)
	fmt.Println("OK")
}
