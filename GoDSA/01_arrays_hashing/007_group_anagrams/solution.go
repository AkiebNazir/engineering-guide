package main

import (
	"fmt"
	"reflect"
	"sort"
	"strings"
)

/*
================================================================================
SOLUTION · LeetCode 49 · Group Anagrams                                  [Medium]
https://leetcode.com/problems/group-anagrams/
================================================================================

THE CORE IDEA
-------------
Grouping by a property means hashing by a CANONICAL FORM — a function that
collapses every member of a group onto one identical representative:

    f(s1) == f(s2)   ⟺   s1 and s2 are anagrams

Pick f, then the algorithm is mechanical:

    buckets := make(map[K][]string)
    for _, s := range strs {
        buckets[f(s)] = append(buckets[f(s)], s)
    }

That skeleton — *canonical key → map → return values* — solves an entire family
of problems. The only design decision is f.


================================================================================
WHAT TO THINK ABOUT (Go specifically)
================================================================================
In Python you use `tuple(counts)` as a key. In Go, you can use an array!

    var counts [26]int

An array `[26]int` (unlike a slice `[]int`) is a value type in Go. It is
comparable, and therefore it can be used directly as a map key.

    buckets := make(map[[26]int][]string)

This is extremely powerful. The `O(k)` count vector is trivial to express in Go.


================================================================================
APPROACH 1 · Count-vector key ✅✅ (the optimal one)
================================================================================
Counting is O(k). Two strings are anagrams exactly when their letter-count
vectors are equal.

    Time:  O(n · k)          <- n strings of max length k
    Space: O(n · k)

In Go, we just declare `var counts [26]int`, populate it, and use it as the
map key.


================================================================================
APPROACH 2 · Sorted-string key ✅ (the fallback)
================================================================================
An anagram is a PERMUTATION. Every permutation of a multiset of characters has
exactly one sorted ordering, so sorting IS the canonical form.

    Time:  O(n · k log k)
    Space: O(n · k)

Go strings are immutable, so to sort a string, you must convert it to a
`[]rune` or `[]byte`, sort it, and convert back. This adds overhead and
verbosity compared to the array-key approach.
*/

// groupAnagrams uses a [26]int array as the map key.
// Time: O(n*k), Space: O(n*k)
func groupAnagrams(strs []string) [][]string {
	buckets := make(map[[26]int][]string)

	for _, s := range strs {
		var counts [26]int // fresh array (value type) for each string
		for i := 0; i < len(s); i++ {
			counts[s[i]-'a']++
		}
		// [26]int is comparable, so it works as a map key!
		buckets[counts] = append(buckets[counts], s)
	}

	ans := make([][]string, 0, len(buckets))
	for _, group := range buckets {
		ans = append(ans, group)
	}
	return ans
}

// -----------------------------------------------------------------------------
// APPROACH 2: Sorted String Key
// -----------------------------------------------------------------------------

type sortRunes []rune

func (s sortRunes) Less(i, j int) bool { return s[i] < s[j] }
func (s sortRunes) Swap(i, j int)      { s[i], s[j] = s[j], s[i] }
func (s sortRunes) Len() int           { return len(s) }

func sortString(s string) string {
	r := []rune(s)
	sort.Sort(sortRunes(r))
	return string(r)
}

func groupAnagramsSorted(strs []string) [][]string {
	buckets := make(map[string][]string)
	for _, s := range strs {
		key := sortString(s)
		buckets[key] = append(buckets[key], s)
	}

	ans := make([][]string, 0, len(buckets))
	for _, group := range buckets {
		ans = append(ans, group)
	}
	return ans
}

// =============================================================================
// TESTS
// =============================================================================

func normalize(groups [][]string) {
	for _, g := range groups {
		sort.Strings(g)
	}
	sort.Slice(groups, func(i, j int) bool {
		if len(groups[i]) == 0 {
			return true
		}
		if len(groups[j]) == 0 {
			return false
		}
		return strings.Join(groups[i], ",") < strings.Join(groups[j], ",")
	})
}

func main() {
	cases := []struct {
		strs []string
		want [][]string
	}{
		{
			strs: []string{"eat", "tea", "tan", "ate", "nat", "bat"},
			want: [][]string{{"ate", "eat", "tea"}, {"bat"}, {"nat", "tan"}},
		},
		{
			strs: []string{""},
			want: [][]string{{""}},
		},
		{
			strs: []string{"a"},
			want: [][]string{{"a"}},
		},
		{
			strs: []string{"abc", "cba", "bac", "xyz"},
			want: [][]string{{"abc", "bac", "cba"}, {"xyz"}},
		},
	}

	impls := []struct {
		name string
		fn   func([]string) [][]string
	}{
		{"count vector", groupAnagrams},
		{"sorted key", groupAnagramsSorted},
	}

	allOK := true
	for _, impl := range impls {
		ok := true
		for _, tc := range cases {
			got := impl.fn(tc.strs)
			
			// Deep copy want so we can normalize it safely
			wantCopy := make([][]string, len(tc.want))
			for i, g := range tc.want {
				wantCopy[i] = append([]string(nil), g...)
			}
			
			normalize(got)
			normalize(wantCopy)
			
			if !reflect.DeepEqual(got, wantCopy) {
				ok = false
				fmt.Printf("FAIL: %s\n  Input: %v\n  Got:  %v\n  Want: %v\n", impl.name, tc.strs, got, wantCopy)
			}
		}
		if ok {
			fmt.Printf("PASS: %s (%d cases)\n", impl.name, len(cases))
		}
		allOK = allOK && ok
	}
	
	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
