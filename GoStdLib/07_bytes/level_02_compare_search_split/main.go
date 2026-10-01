/*
LEVEL 02 (core) - the bytes free-function toolkit: Compare/Equal/Contains/Index/Split/Join/Fields

You will learn
  - Compare/Equal for ordering and equality of []byte
  - Contains/Index for substring search
  - Split/Join for round-tripping a []byte through a separator
  - Fields for splitting on runs of whitespace

Run: go run ./GoStdLib/07_bytes/level_02_compare_search_split
*/

package main

import (
	"bytes"
	"fmt"
)

func main() {
	a := []byte("banana")
	b := []byte("banana")
	c := []byte("cherry")

	// Equal is the idiomatic way to compare []byte for equality - never use ==,
	// which does not compile for slices anyway.
	if !bytes.Equal(a, b) {
		panic("Equal(a, b) = false, want true")
	}

	// Compare returns -1/0/1 like strings.Compare, usable for sorting.
	if cmp := bytes.Compare(a, c); cmp != -1 {
		panic(fmt.Sprintf("Compare(banana, cherry) = %d, want -1", cmp))
	}
	if cmp := bytes.Compare(a, a); cmp != 0 {
		panic(fmt.Sprintf("Compare(a, a) = %d, want 0", cmp))
	}

	// Contains and Index for substring search.
	line := []byte("2026-09-22 ERROR db connection lost")
	if !bytes.Contains(line, []byte("ERROR")) {
		panic("Contains did not find ERROR")
	}
	idx := bytes.Index(line, []byte("ERROR"))
	if idx != 11 {
		panic(fmt.Sprintf("Index(ERROR) = %d, want 11", idx))
	}
	if bytes.Index(line, []byte("WARN")) != -1 {
		panic("Index(WARN) should be -1: not present")
	}

	// Split breaks on a literal separator; Join is its inverse.
	csv := []byte("id,name,role")
	parts := bytes.Split(csv, []byte(","))
	if len(parts) != 3 {
		panic(fmt.Sprintf("Split produced %d parts, want 3", len(parts)))
	}
	wantParts := [][]byte{[]byte("id"), []byte("name"), []byte("role")}
	for i, p := range parts {
		if !bytes.Equal(p, wantParts[i]) {
			panic(fmt.Sprintf("part %d = %q, want %q", i, p, wantParts[i]))
		}
	}
	rejoined := bytes.Join(parts, []byte(","))
	if !bytes.Equal(rejoined, csv) {
		panic(fmt.Sprintf("Join(Split(x)) = %q, want %q", rejoined, csv))
	}

	// Fields splits on runs of whitespace and drops empty results - unlike
	// Split(b, []byte(" ")), which would produce empty strings for each extra space.
	messy := []byte("  the    quick brown   fox  ")
	words := bytes.Fields(messy)
	if len(words) != 4 {
		panic(fmt.Sprintf("Fields produced %d words, want 4: %q", len(words), words))
	}
	naive := bytes.Split(messy, []byte(" "))
	if len(naive) <= len(words) {
		panic(fmt.Sprintf("expected naive Split (%d parts) to have MORE (empty) parts than Fields (%d)", len(naive), len(words)))
	}

	fmt.Printf("Fields found %d words; naive Split on \" \" found %d parts (with empties)\n", len(words), len(naive))
	fmt.Println("OK")
}
