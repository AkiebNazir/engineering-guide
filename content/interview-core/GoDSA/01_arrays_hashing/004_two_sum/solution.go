package main

import (
	"fmt"
	"sort"
)

/*
================================================================================
SOLUTION · LeetCode 1 · Two Sum                                          [Easy]
https://leetcode.com/problems/two-sum/
================================================================================

THE CORE IDEA
-------------
Brute force treats this as "find a PAIR" — n^2 possibilities. It is not a pair
search:

    once you fix nums[i], the partner is FORCED:  complement = target - nums[i]

The question at each index collapses from "which other element works?" to
"have I already seen this one specific value?" — which a map answers in O(1).

This is the smallest example of the highest-value move in interview algorithms:
TRADE SPACE FOR TIME BY REMEMBERING WHAT YOU HAVE SEEN. Recognise it here and
you will recognise it in LC 15 (3Sum) and LC 560 (Subarray Sum Equals K).


================================================================================
⚠️  THE GO TRAP — comma-ok, and why index 0 makes this vicious
================================================================================
A Go map returns the ZERO VALUE for a missing key. For map[int]int that zero is
0 — which is also a completely legitimate array index. So:

    j := seen[complement]
    if j != 0 { ... }              // ← BROKEN

is wrong in two directions at once:

    - complement genuinely stored at index 0  ->  j == 0  ->  you SKIP a real
      answer. nums = [2,7,...], target 9 fails: 2 lives at index 0.
    - complement absent                       ->  j == 0  ->  you may ACCEPT a
      pair that does not exist.

The only correct form is comma-ok:

    if j, ok := seen[complement]; ok { return []int{j, i} }

Two Sum is the problem where Go's zero-value semantics hurt most, precisely
because 0 is meaningful here. Build the reflex.


================================================================================
APPROACH 1 · Brute force (state it, then improve)
================================================================================
    for i := 0; i < n; i++ {
        for j := i + 1; j < n; j++ {
            if nums[i]+nums[j] == target { return []int{i, j} }
        }
    }

    Time:  O(n^2)     Space: O(1)

At n = 10^4 that is ~5x10^7 comparisons — fast in Go, but it is the answer that
ends the interview. The follow-up explicitly asks for better. Say it, price it,
improve it.


================================================================================
APPROACH 2 · One-pass map ✅ (the answer)
================================================================================

STEP BY STEP for nums = [2, 7, 11, 15], target = 9:

    seen = {}

    i=0  n=2   complement = 7    7 in seen? NO    seen = {2:0}
    i=1  n=7   complement = 2    2 in seen? YES at 0
               -> return [0, 1]   ✓

STEP BY STEP for nums = [3, 2, 4], target = 6  (the case that catches people):

    i=0  n=3   complement = 3    3 in seen? NO    seen = {3:0}
    i=1  n=2   complement = 4    4 in seen? NO    seen = {3:0, 2:1}
    i=2  n=4   complement = 2    2 in seen? YES at 1
               -> return [1, 2]   ✓

    It did NOT return [0,0]. Checking BEFORE inserting is what prevents the 3
    from pairing with itself.

STEP BY STEP for nums = [3, 3], target = 6  (duplicates):

    i=0  n=3   complement = 3    3 in seen? NO    seen = {3:0}
    i=1  n=3   complement = 3    3 in seen? YES at 0
               -> return [0, 1]   ✓

    The second 3 finds the first. `seen[3] = 1` would overwrite index 0, but we
    return before that happens — and the "exactly one solution" guarantee means
    a later overwrite could never cost us the answer anyway.

    Time:  O(n) average     Space: O(n)


================================================================================
⚠️  WHY CHECK-BEFORE-INSERT IS NOT OPTIONAL
================================================================================
Flip the two statements and it breaks:

    seen[n] = i                              // WRONG ORDER
    if j, ok := seen[target-n]; ok { ... }

    nums = [3, 2, 4], target = 6
    i=0: seen = {3:0}; complement 3 IS present — it is the element itself
         -> returns [0, 0], using nums[0] twice. Violates the problem.

Checking first guarantees the map holds only STRICTLY EARLIER elements, so any
hit is a genuine second element. State this reasoning out loud; it shows you
argued correctness rather than recalled a snippet.


================================================================================
APPROACH 3 · Sort + two pointers (usually WRONG here)
================================================================================
Sorting destroys the indices the problem asks for, so you must carry them:

    type pair struct{ val, idx int }

    Time:  O(n log n)   Space: O(n) — for the index-carrying copy

Slower, and still O(n) space *because indices are required*. If the problem
asked for VALUES it would be O(n log n) / O(1); if the input were already
sorted it would be O(n) / O(1) — which is precisely LC 167, Two Sum II.

Knowing when it wins matters more than the code:
    already sorted?          -> two pointers, O(n) time, O(1) space
    need values not indices? -> two pointers viable
    unsorted + need indices? -> hash map


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach              Time         Space   Notes
    --------------------  -----------  ------  ---------------------------
    Brute force           O(n^2)       O(1)    ends the interview
    One-pass map    ✅    O(n)         O(n)    the expected answer
    Sort + 2 pointers     O(n log n)   O(n)    O(1) space only if values


================================================================================
EDGE CASES
================================================================================
    [3,3], target 6         -> [0,1]. Duplicates handled by check-before-insert.
    [0,4,3,0], target 0     -> [0,3]. Zero values AND a zero target — the case
                               that destroys any `!= 0` membership test.
    [-1,-2,-3,-4,-5], -8    -> [2,4]. Negative keys hash fine.
    len(nums) == 2          -> minimum input.

    No solution cannot occur (guaranteed exactly one). Returning nil after the
    loop is defensive; say that you know it is unreachable.


================================================================================
COMMON MISTAKES
================================================================================
1. `if seen[c] != 0` instead of comma-ok. Broken both ways — see the trap
   section. THE Go-specific bug in this problem.

2. Inserting before checking — lets an element pair with itself, returns [0,0].

3. Returning values instead of indices.

4. Linear-scanning a slice for `seen` — that is O(n) inside O(n), i.e. the
   brute force with extra steps.

5. Two-pass without a self-match guard. If you build the whole map first you
   must check `j != i`; the one-pass version needs no such guard, which is why
   it is preferred.

6. `var seen map[int]int` then writing to it — panic: assignment to entry in
   nil map. Always make() it.


================================================================================
RELATED PROBLEMS — the complement family
================================================================================
    LC 167  Two Sum II (sorted)   — two pointers, O(1) space
    LC 15   3Sum                  — fix one, two-pointer the rest
    LC 18   4Sum                  — fix two, two-pointer the rest
    LC 454  4Sum II               — hash the pairwise sums
    LC 560  Subarray Sum Equals K — the same complement trick on PREFIX SUMS
================================================================================
*/

// twoSum is the interview answer: one pass, map of value -> index.
// Time O(n) average, space O(n).
func twoSum(nums []int, target int) []int {
	seen := make(map[int]int, len(nums)) // value -> index; preallocated
	for i, n := range nums {
		complement := target - n
		if j, ok := seen[complement]; ok { // comma-ok, NOT `!= 0`
			return []int{j, i}
		}
		seen[n] = i // insert AFTER checking
	}
	return nil // unreachable given the constraints
}

// twoSumTwoPass builds the map first, so it needs an explicit self-match guard.
func twoSumTwoPass(nums []int, target int) []int {
	seen := make(map[int]int, len(nums))
	for i, n := range nums {
		seen[n] = i
	}
	for i, n := range nums {
		if j, ok := seen[target-n]; ok && j != i { // the guard one-pass avoids
			return []int{i, j}
		}
	}
	return nil
}

// twoSumSortTwoPointers is O(n log n) and must carry indices through the sort.
func twoSumSortTwoPointers(nums []int, target int) []int {
	type pair struct{ val, idx int }
	ps := make([]pair, len(nums))
	for i, v := range nums {
		ps[i] = pair{v, i}
	}
	sort.Slice(ps, func(i, j int) bool { return ps[i].val < ps[j].val })

	lo, hi := 0, len(ps)-1
	for lo < hi {
		switch s := ps[lo].val + ps[hi].val; {
		case s == target:
			a, b := ps[lo].idx, ps[hi].idx
			if a > b {
				a, b = b, a
			}
			return []int{a, b}
		case s < target:
			lo++
		default:
			hi--
		}
	}
	return nil
}

// twoSumBruteForce is O(n^2). Contrast only.
func twoSumBruteForce(nums []int, target int) []int {
	for i := 0; i < len(nums); i++ {
		for j := i + 1; j < len(nums); j++ {
			if nums[i]+nums[j] == target {
				return []int{i, j}
			}
		}
	}
	return nil
}

func main() {
	type testCase struct {
		nums   []int
		target int
	}
	cases := []testCase{
		{[]int{2, 7, 11, 15}, 9},
		{[]int{3, 2, 4}, 6},
		{[]int{3, 3}, 6},
		{[]int{-1, -2, -3, -4, -5}, -8},
		{[]int{0, 4, 3, 0}, 0},
		{[]int{1, 2}, 3},
	}

	impls := []struct {
		name string
		fn   func([]int, int) []int
	}{
		{"one-pass map ", twoSum},
		{"two-pass map ", twoSumTwoPass},
		{"sort + 2ptr  ", twoSumSortTwoPointers},
		{"brute force  ", twoSumBruteForce},
	}

	allOK := true
	for _, impl := range impls {
		ok := true
		for _, tc := range cases {
			got := impl.fn(tc.nums, tc.target)
			// Verify the ANSWER, not a fixed index pair: two distinct indices
			// whose values sum to target.
			if len(got) != 2 || got[0] == got[1] ||
				tc.nums[got[0]]+tc.nums[got[1]] != tc.target {
				ok = false
			}
		}
		allOK = allOK && ok
		fmt.Printf("%s  %s (%d cases, verified by summing)\n",
			status(ok), impl.name, len(cases))
	}

	// The Go-specific bug: `!= 0` instead of comma-ok.
	fmt.Println("\n--- why comma-ok is mandatory (not `!= 0`) ---")
	brokenZeroTest := func(nums []int, target int) []int {
		seen := make(map[int]int)
		for i, n := range nums {
			if j := seen[target-n]; j != 0 { // BROKEN membership test
				return []int{j, i}
			}
			seen[n] = i
		}
		return nil
	}
	nums, target := []int{2, 7, 11, 15}, 9
	fmt.Printf("  nums=%v target=%d\n", nums, target)
	fmt.Printf("  `!= 0` test  -> %v  <- MISSES it: the 2 lives at index 0\n",
		brokenZeroTest(nums, target))
	fmt.Printf("  comma-ok     -> %v  <- correct\n", twoSum(nums, target))

	// The ordering bug.
	fmt.Println("\n--- why check-before-insert is not optional ---")
	brokenOrder := func(nums []int, target int) []int {
		seen := make(map[int]int)
		for i, n := range nums {
			seen[n] = i // WRONG: insert first
			if j, ok := seen[target-n]; ok {
				return []int{j, i}
			}
		}
		return nil
	}
	nums2, target2 := []int{3, 2, 4}, 6
	fmt.Printf("  nums=%v target=%d\n", nums2, target2)
	fmt.Printf("  insert-then-check -> %v  <- uses nums[0] TWICE (3+3), invalid\n",
		brokenOrder(nums2, target2))
	fmt.Printf("  check-then-insert -> %v  <- nums[1]+nums[2] = 2+4 = 6 ✓\n",
		twoSum(nums2, target2))

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}

func status(ok bool) string {
	if ok {
		return "PASS"
	}
	return "FAIL"
}
