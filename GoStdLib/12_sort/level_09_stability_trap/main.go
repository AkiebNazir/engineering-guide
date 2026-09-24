/*
LEVEL 09 (production trap) - sort.Slice silently scrambles equal-key order

You will learn
  - "sorted by score" looks like a complete spec, but says nothing about what
    happens to rows that TIE on score - that hidden assumption is the trap
  - sort.Slice is NOT guaranteed stable: it is free to reorder elements the
    Less closure calls equal, and its real implementation does exactly that
    once the slice is big enough to leave the small-slice insertion-sort path
  - sort.SliceStable costs a bit more but keeps equal elements in their
    original input order, by contract - this level measures the actual,
    observed scrambling on THIS run rather than asserting it from memory

Run: go run ./GoStdLib/12_sort/level_09_stability_trap
*/

package main

import (
	"fmt"
	"sort"
)

// item's `seq` is the original input position - the secondary, observable
// field that a stable sort must preserve among equal `key`s and an unstable
// sort has no obligation to.
type item struct {
	key int
	seq int
}

func main() {
	const n = 64
	base := make([]item, n)
	for i := range base {
		base[i] = item{key: i % 4, seq: i} // only 4 distinct keys -> long tie runs
	}

	stable := append([]item(nil), base...)
	unstable := append([]item(nil), base...)

	less := func(data []item) func(i, j int) bool {
		return func(i, j int) bool { return data[i].key < data[j].key }
	}
	sort.SliceStable(stable, less(stable))
	sort.Slice(unstable, less(unstable))

	// Both must still be correctly sorted by key - stability is about ties,
	// not correctness of the primary order.
	if !sort.SliceIsSorted(stable, less(stable)) {
		panic("SliceStable result is not sorted by key")
	}
	if !sort.SliceIsSorted(unstable, less(unstable)) {
		panic("Slice result is not sorted by key")
	}

	// SliceStable's contract: within each key, seq must stay strictly
	// increasing (the original input order), always, on every Go version.
	for i := 1; i < len(stable); i++ {
		if stable[i].key == stable[i-1].key && stable[i].seq < stable[i-1].seq {
			panic(fmt.Sprintf("SliceStable broke its own contract at index %d: %v then %v", i, stable[i-1], stable[i]))
		}
	}

	// The trap, observed rather than assumed: sort.Slice's tie order differs
	// from SliceStable's tie order somewhere in this run's output.
	scrambled := false
	for i := range stable {
		if stable[i] != unstable[i] {
			scrambled = true
			break
		}
	}
	if !scrambled {
		panic("FAILED to observe the trap: sort.Slice happened to match SliceStable exactly - increase n or change the key distribution")
	}

	fmt.Println("stable   (first key-0 run):", firstRun(stable, 0))
	fmt.Println("unstable (first key-0 run):", firstRun(unstable, 0))
	fmt.Println("sort.Slice reordered equal-key rows that SliceStable kept in input order")
	fmt.Println("OK")
}

func firstRun(items []item, key int) []int {
	var seqs []int
	for _, it := range items {
		if it.key == key {
			seqs = append(seqs, it.seq)
		}
	}
	return seqs
}
