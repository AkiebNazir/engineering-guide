/*
LEVEL 07 (advanced) - intermediate pattern: Compare and EqualFold

You will learn
  - strings.Compare(a, b) returns -1/0/1 like a classic three-way comparator,
    usable directly as a sort.Slice less-function building block
  - strings.EqualFold(a, b) does Unicode case-insensitive equality WITHOUT
    allocating a lower/upper-cased copy of either string
  - a realistic use: case-insensitive deduplication plus deterministic sorting

Run: go run ./GoStdLib/05_strings/level_07_compare_equalfold
*/

package main

import (
	"fmt"
	"sort"
	"strings"
)

// dedupCaseInsensitive returns the input with case-insensitive duplicates
// removed (first occurrence wins) and the result sorted case-sensitively.
func dedupCaseInsensitive(names []string) []string {
	seen := make([]string, 0, len(names)) // folded keys already kept
	var out []string
	for _, name := range names {
		duplicate := false
		for _, s := range seen {
			if strings.EqualFold(s, name) {
				duplicate = true
				break
			}
		}
		if !duplicate {
			seen = append(seen, name)
			out = append(out, name)
		}
	}
	sort.Slice(out, func(i, j int) bool {
		return strings.Compare(out[i], out[j]) < 0
	})
	return out
}

func main() {
	if strings.Compare("apple", "banana") != -1 {
		panic("Compare(apple, banana) should be -1")
	}
	if strings.Compare("banana", "apple") != 1 {
		panic("Compare(banana, apple) should be 1")
	}
	if strings.Compare("apple", "apple") != 0 {
		panic("Compare(apple, apple) should be 0")
	}

	if !strings.EqualFold("GoLang", "golang") {
		panic("EqualFold(GoLang, golang) should be true")
	}
	if strings.EqualFold("GoLang", "golanguage") {
		panic("EqualFold should not match different-length strings")
	}

	names := []string{"Bob", "alice", "ALICE", "charlie", "Alice", "bob"}
	result := dedupCaseInsensitive(names)
	expected := []string{"Bob", "alice", "charlie"}
	if len(result) != len(expected) {
		panic(fmt.Sprintf("got %d names, expected %d: %v", len(result), len(expected), result))
	}
	for i, want := range expected {
		if result[i] != want {
			panic(fmt.Sprintf("result[%d] = %q, expected %q (full: %v)", i, result[i], want, result))
		}
	}

	fmt.Printf("deduped+sorted %d names down to %v\n", len(names), result)
	fmt.Println("OK")
}
