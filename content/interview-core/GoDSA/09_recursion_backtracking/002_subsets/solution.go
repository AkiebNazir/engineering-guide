package main

import (
	"fmt"
	"sort"
)

/*
================================================================================
SOLUTION · LeetCode 78 · Subsets                                       [Medium]
https://leetcode.com/problems/subsets/
================================================================================

THE CORE IDEA
-------------
Every element gets exactly one binary decision: INCLUDE it or EXCLUDE it.
Walking the elements in order and branching on that decision produces a
binary tree whose 2^n leaves are exactly the 2^n subsets. The only real
difficulty in Go is SLICE ALIASING: the path you are building shares one
backing array across the whole recursion, so every recorded subset must be
a fresh copy.

    var backtrack func(i int)
    backtrack = func(i int) {
        if i == len(nums) {                  // decided about every element
            res = append(res, append([]int(nil), path...))   // COPY
            return
        }
        path = append(path, nums[i])         // choose: INCLUDE nums[i]
        backtrack(i + 1)
        path = path[:len(path)-1]            // un-choose ("pop")
        backtrack(i + 1)                      // EXCLUDE nums[i]
    }


================================================================================
CALL TREE for nums = [1, 2]
================================================================================
                            backtrack(0, [])
                              /          \
                  INCLUDE 1 /              \ EXCLUDE 1
              backtrack(1, [1])            backtrack(1, [])
                /           \                /           \
        INCLUDE 2       EXCLUDE 2     INCLUDE 2       EXCLUDE 2
   backtrack(2,[1,2]) backtrack(2,[1]) backtrack(2,[2]) backtrack(2,[])
      record [1,2]     record [1]       record [2]       record []

How "popping" works in Go: after the far-left branch returns to
backtrack(1, [1]), path is [1, 2]. `path = path[:len(path)-1]` reslices it
back to [1] -- the capacity (and the 2 still sitting in the backing array)
stays, which is exactly why a recorded subset that ALIASES path would later
be overwritten. Then the EXCLUDE branch runs. Undoing the choice before
trying the other branch is what makes it "backtracking".


================================================================================
APPROACH 1 · Include / exclude per element ✅
================================================================================
Shown above. Records only at the leaves (i == len(nums)).


================================================================================
APPROACH 2 · Combinations-style: record at every node
================================================================================
    var bt func(start int)
    bt = func(start int) {
        res = append(res, append([]int(nil), path...))  // every node is a subset
        for j := start; j < len(nums); j++ {
            path = append(path, nums[j])
            bt(j + 1)
            path = path[:len(path)-1]
        }
    }
Same 2^n subsets, generated in size-growing order along each branch. This is
the template Combinations (006) and Subsets II (003, add a duplicate-skip)
reuse, so know both shapes.


================================================================================
APPROACH 3 · Bitmask, no recursion
================================================================================
For mask in 0 .. 2^n - 1, include nums[i] iff bit i of mask is set:
`mask>>i&1 == 1`. n <= 10, so 1024 masks. Iterative and easy to reason about;
the backtracking shapes above generalise to pruning, bitmasks do not.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                 Time         Aux space      Output
    -----------------------  -----------  -------------  -----------
    Include / exclude ✅     O(n * 2^n)   O(n) stack+path  O(n * 2^n)
    Combinations-style       O(n * 2^n)   O(n)           O(n * 2^n)
    Bitmask                  O(n * 2^n)   O(1)           O(n * 2^n)
The output itself has 2^n entries of average length n/2, so O(n * 2^n) is a
floor, not something to optimise away.


================================================================================
EDGE CASES
================================================================================
    nums = [0]      -> [[], [0]]  (the empty subset is always included)
    n = 10          -> 1024 subsets; still instant
    negative values -> irrelevant; subsets depend on positions, not values


================================================================================
COMMON MISTAKES
================================================================================
1. `res = append(res, path)` without a copy -- every entry aliases the same
   backing array and later writes corrupt earlier subsets. Demonstrated LIVE
   in main below.
2. Forgetting the un-choose line -- path keeps growing and the EXCLUDE
   branch sees elements it never chose.
3. Recording at every node in Approach 1 (instead of only at i == n) --
   duplicates, because the EXCLUDE chain re-reaches the same path.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: nums may contain duplicates (LC 90)?
A: Sort, then in the combinations-style loop skip nums[j] when
   j > start && nums[j] == nums[j-1].

Q: Only subsets of size k (LC 77)?
A: Combinations-style, record only when len(path) == k, and prune when not
   enough elements remain.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 90   Subsets II             -- duplicates: sort + skip (problem 003)
    LC 46   Permutations           -- "which unused element next" (problem 004)
    LC 77   Combinations           -- fixed-size subsets (problem 006)
================================================================================
*/

// subsets is the interview answer: include/exclude backtracking.
// Time O(n * 2^n), aux space O(n).
func subsets(nums []int) [][]int {
	res := make([][]int, 0, 1<<len(nums))
	path := make([]int, 0, len(nums))
	var backtrack func(i int)
	backtrack = func(i int) {
		if i == len(nums) {
			cp := make([]int, len(path))
			copy(cp, path) // COPY: path's backing array is reused by every branch
			res = append(res, cp)
			return
		}
		path = append(path, nums[i]) // INCLUDE nums[i]
		backtrack(i + 1)
		path = path[:len(path)-1] // un-choose
		backtrack(i + 1)          // EXCLUDE nums[i]
	}
	backtrack(0)
	return res
}

// subsetsCombos records at every node (the Combinations template).
func subsetsCombos(nums []int) [][]int {
	var res [][]int
	var path []int
	var bt func(start int)
	bt = func(start int) {
		res = append(res, append([]int(nil), path...))
		for j := start; j < len(nums); j++ {
			path = append(path, nums[j])
			bt(j + 1)
			path = path[:len(path)-1]
		}
	}
	bt(0)
	return res
}

// subsetsBitmask enumerates masks 0..2^n-1 without recursion.
func subsetsBitmask(nums []int) [][]int {
	n := len(nums)
	res := make([][]int, 0, 1<<n)
	for mask := 0; mask < 1<<n; mask++ {
		var s []int
		for i := 0; i < n; i++ {
			if mask>>i&1 == 1 {
				s = append(s, nums[i])
			}
		}
		res = append(res, s)
	}
	return res
}

// subsetsAliasBug is BROKEN ON PURPOSE: it appends path itself, not a copy.
func subsetsAliasBug(nums []int) [][]int {
	var res [][]int
	path := make([]int, 0, len(nums)) // one backing array for the whole run
	var backtrack func(i int)
	backtrack = func(i int) {
		if i == len(nums) {
			res = append(res, path) // <-- aliases the shared backing array
			return
		}
		path = append(path, nums[i])
		backtrack(i + 1)
		path = path[:len(path)-1]
		backtrack(i + 1)
	}
	backtrack(0)
	return res
}

// ---------------------------------------------------------------------------
// Test helpers: canonical form = each subset sorted, then the list sorted.
// ---------------------------------------------------------------------------

func canonical(sets [][]int) string {
	keys := make([]string, len(sets))
	for i, s := range sets {
		c := append([]int(nil), s...)
		sort.Ints(c)
		keys[i] = fmt.Sprint(c)
	}
	sort.Strings(keys)
	return fmt.Sprint(keys)
}

func status(ok bool) string {
	if ok {
		return "PASS"
	}
	return "FAIL"
}

func main() {
	cases := []struct {
		nums []int
		want [][]int
	}{
		{[]int{1, 2, 3}, [][]int{{}, {1}, {2}, {1, 2}, {3}, {1, 3}, {2, 3}, {1, 2, 3}}},
		{[]int{0}, [][]int{{}, {0}}},
		{[]int{-1, 5}, [][]int{{}, {-1}, {5}, {-1, 5}}},
	}
	allOK := true

	fmt.Println("--- correctness: three approaches, compared as sets ---")
	for _, c := range cases {
		want := canonical(c.want)
		got := subsets(c.nums)
		ok := canonical(got) == want &&
			canonical(subsetsCombos(c.nums)) == want &&
			canonical(subsetsBitmask(c.nums)) == want
		allOK = allOK && ok
		fmt.Printf("%s  %-10s -> %v\n", status(ok), fmt.Sprint(c.nums), got)
	}

	fmt.Println("\n--- size check: 2^n subsets for n = 10 ---")
	ten := []int{0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
	n10 := len(subsets(ten))
	ok := n10 == 1024 && canonical(subsets(ten)) == canonical(subsetsBitmask(ten))
	allOK = allOK && ok
	fmt.Printf("%s  len(subsets(0..9)) = %d\n", status(ok), n10)

	fmt.Println("\n--- the #1 Go mistake: appending path without copying ---")
	bad := subsetsAliasBug([]int{1, 2, 3})
	fmt.Printf("  subsetsAliasBug([1 2 3]) -> %v\n", bad)
	fmt.Println("  every entry is a view of ONE backing array, so later writes rewrote")
	fmt.Println("  earlier results: the last values written (3s) leak into every entry")
	corrupted := canonical(bad) != canonical(cases[0].want)
	allOK = allOK && corrupted
	fmt.Printf("%s  alias bug produced a wrong answer: %v\n", status(corrupted), corrupted)

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
