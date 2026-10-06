package main

import (
	"fmt"
	"math/rand"
	"sort"
	"time"
)

/*
================================================================================
SOLUTION · LeetCode 287 · Find the Duplicate Number                    [Medium]
https://leetcode.com/problems/find-the-duplicate-number/
================================================================================

THE CORE IDEA
--------------
Topic 08's "surprise" problem: nums[i] is always a valid index (values in
[1,n], slots 0..n), so define next(i) = nums[i] and walk from index 0 — this
is exactly a linked-list walk with nums[i] standing in for .Next. Pigeonhole
(n+1 values drawn from range [1,n]) guarantees this walk enters a cycle, and
the cycle's ENTRANCE is exactly the duplicate value: every index equal to the
duplicate points INTO the same shared node, giving that node in-degree >= 2,
which is precisely what makes it a cycle entrance rather than an ordinary
chain node (every non-duplicate value has in-degree <= 1). Reuse Floyd's
cycle detection (problem 003) verbatim, then the cycle-entrance phase.


================================================================================
APPROACH 1 · Sort a copy (baseline, disallowed by O(1)-space rule)
================================================================================
    Time:  O(n log n)     Space: O(n) (must copy — can't mutate nums)

================================================================================
APPROACH 2 · Hash set (baseline, disallowed by O(1)-space rule)
================================================================================
    Time:  O(n)     Space: O(n)  — a map[int]bool of up to n keys

================================================================================
APPROACH 3 · Floyd's cycle detection on the implicit list ✅ (the answer)
================================================================================
PHASE 1: slow, fast both start at INDEX 0 and take a first step before any
comparison (do-while shape — comparing before stepping would trivially
"meet" at 0 == 0):

    slow, fast := 0, 0
    for {
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast {
            break
        }
    }

PHASE 2: reset slow2 to index 0; advance both one step at a time until they
meet — that meeting point is the cycle entrance, the duplicate value.

    Time:  O(n)     Space: O(1), nums not modified


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                Time         Space   Mutates input?   Note
    -----------------------  -----------  ------  ---------------  ----------------
    Sort a copy              O(n log n)  O(n)    no               simple, wrong space class
    Hash set                 O(n)        O(n)    no               "obvious" O(n) answer
    Floyd's (pointer-chase)  O(n)        O(1)    no               meets the follow-up


================================================================================
EDGE CASES
================================================================================
    [1,1]                  -> 1   n=1, self-loop at index 1.
    [x,x,x,...,x]           -> x   duplicate repeats many times, not just twice.
    duplicate is the largest value (n)  -- no special-casing needed, walk is
                             index-based, not magnitude-based.


================================================================================
COMMON MISTAKES
================================================================================
1. Comparing slow == fast BEFORE either has moved — both start at 0, so the
   comparison trivially holds at the start unless a do-while shape is used.
2. Confusing this with needing SORTED input — it does not; the trick only
   needs values to be valid indices into the same array.
3. Mutating nums to mark visited slots (the negation trick from
   "Find All Numbers Disappeared") — that problem allows mutation, this one
   forbids it.
4. Returning the phase-1 meeting point as the final answer instead of
   running phase 2 — the meeting point is generally NOT the duplicate.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Prove a duplicate must exist -> pigeonhole, n+1 values in range [1,n].
Q: More than one duplicate value possible? -> Floyd's no longer identifies a
   unique answer; use binary search on the value range with a counting
   predicate instead (O(n log n) time, O(1) space, no cycle assumption).
Q: Binary search alternative? -> for candidate m, count elements <= m; if
   count > m the duplicate is in [1,m], else in (m,n].


================================================================================
RELATED PROBLEMS
================================================================================
    LC 141  Linked List Cycle
    LC 142  Linked List Cycle II            — cycle entrance, phase 2's math
    LC 448  Find All Numbers Disappeared    — same "value as index" trick,
                                              mutation IS allowed there
    LC 442  Find All Duplicates in an Array — same family, allows mutation
================================================================================
*/

// findDuplicate is the interview answer: Floyd's on the implicit linked list.
// O(n) time, O(1) space, nums is not modified.
func findDuplicate(nums []int) int {
	slow, fast := 0, 0
	for {
		slow = nums[slow]
		fast = nums[nums[fast]]
		if slow == fast {
			break
		}
	}
	slow2 := 0
	for slow2 != slow {
		slow2 = nums[slow2]
		slow = nums[slow]
	}
	return slow2
}

// findDuplicateSort is O(n log n) time, O(n) space (copy to avoid mutating nums).
func findDuplicateSort(nums []int) int {
	arr := make([]int, len(nums))
	copy(arr, nums)
	sort.Ints(arr)
	for i := 1; i < len(arr); i++ {
		if arr[i] == arr[i-1] {
			return arr[i]
		}
	}
	return -1 // unreachable per constraints
}

// findDuplicateHashSet is O(n) time, O(n) space — the "obvious" answer.
func findDuplicateHashSet(nums []int) int {
	seen := make(map[int]bool, len(nums))
	for _, x := range nums {
		if seen[x] {
			return x
		}
		seen[x] = true
	}
	return -1 // unreachable per constraints
}

// findDuplicateBinarySearch is O(n log n) time, O(1) space — an alternative
// that meets the space bound without pointer-chasing.
func findDuplicateBinarySearch(nums []int) int {
	lo, hi := 1, len(nums)-1
	for lo < hi {
		mid := (lo + hi) / 2
		count := 0
		for _, x := range nums {
			if x <= mid {
				count++
			}
		}
		if count > mid {
			hi = mid
		} else {
			lo = mid + 1
		}
	}
	return lo
}

func main() {
	cases := []struct {
		nums []int
		want int
	}{
		{[]int{1, 3, 4, 2, 2}, 2},
		{[]int{3, 1, 3, 4, 2}, 3},
		{[]int{3, 3, 3, 3, 3}, 3},
		{[]int{1, 1}, 1},
		{[]int{2, 2, 2, 2, 2}, 2},
		{[]int{1, 2, 3, 4, 4}, 4},
		{[]int{2, 1, 3, 4, 5, 6, 7, 8, 9, 10, 5}, 5},
		{[]int{5, 4, 3, 2, 1, 1}, 1},
	}

	allOK := true
	fmt.Println("--- correctness: Floyd's vs sort vs hashset vs binary-search oracles ---")
	for _, tc := range cases {
		before := make([]int, len(tc.nums))
		copy(before, tc.nums)

		gotFloyd := findDuplicate(append([]int(nil), tc.nums...))
		gotSort := findDuplicateSort(tc.nums)
		gotSet := findDuplicateHashSet(tc.nums)
		gotBSearch := findDuplicateBinarySearch(tc.nums)

		untouched := true
		for i := range tc.nums {
			if tc.nums[i] != before[i] {
				untouched = false
			}
		}
		ok := gotFloyd == tc.want && gotSort == tc.want && gotSet == tc.want &&
			gotBSearch == tc.want && untouched
		allOK = allOK && ok
		fmt.Printf("%s  nums=%-40v floyd=%d sort=%d set=%d bsearch=%d (want %d, untouched=%v)\n",
			status(ok), tc.nums, gotFloyd, gotSort, gotSet, gotBSearch, tc.want, untouched)
	}

	// ------------------------------------------------------------------
	// nums as an implicit linked list, pointer-chasing i -> nums[i].
	// ------------------------------------------------------------------
	fmt.Println("\n--- nums as an implicit linked list: index -> nums[index] ---")
	nums := []int{1, 3, 4, 2, 2}
	fmt.Printf("  nums = %v\n", nums)
	fmt.Print("  index: ")
	for i := range nums {
		fmt.Printf("%3d", i)
	}
	fmt.Println()
	fmt.Print("  value: ")
	for _, v := range nums {
		fmt.Printf("%3d", v)
	}
	fmt.Println()
	fmt.Println("  walk from index 0, following i -> nums[i]:")
	path := []int{0}
	cur := 0
	seenIdx := map[int]bool{0: true}
	for i := 0; i < 10; i++ {
		cur = nums[cur]
		path = append(path, cur)
		if seenIdx[cur] {
			break
		}
		seenIdx[cur] = true
	}
	for i, p := range path {
		if i > 0 {
			fmt.Print(" -> ")
		}
		fmt.Print(p)
	}
	fmt.Println()
	fmt.Printf("  cycle detected at repeated node %d — this IS the duplicate value\n", path[len(path)-1])

	fmt.Println("\n  Floyd's phase-by-phase trace on this array:")
	slow, fast := 0, 0
	fmt.Printf("  %4s %6s %6s\n", "step", "slow", "fast")
	fmt.Printf("  %4s %6d %6d\n", "init", slow, fast)
	step := 0
	for {
		slow = nums[slow]
		fast = nums[nums[fast]]
		step++
		fmt.Printf("  %4d %6d %6d\n", step, slow, fast)
		if slow == fast {
			break
		}
	}
	fmt.Printf("  phase 1 meeting point: %d\n", slow)
	slow2 := 0
	step2 := 0
	fmt.Printf("  %4s %6s %6s\n", "step", "slow2", "slow")
	fmt.Printf("  %4d %6d %6d\n", step2, slow2, slow)
	for slow2 != slow {
		slow2 = nums[slow2]
		slow = nums[slow]
		step2++
		fmt.Printf("  %4d %6d %6d\n", step2, slow2, slow)
	}
	fmt.Printf("  phase 2 converges at: %d  == duplicate value (%d)\n", slow2, findDuplicate(nums))

	// ------------------------------------------------------------------
	// Space accounting: measured, not assumed.
	// ------------------------------------------------------------------
	fmt.Println("\n--- space accounting: O(1) Floyd's vs O(n) hashset (same n) ---")
	n := 50000
	big := make([]int, 0, n+1)
	for i := 1; i <= n; i++ {
		big = append(big, i)
	}
	big = append(big, 17)
	rand.New(rand.NewSource(42)).Shuffle(len(big), func(i, j int) {
		big[i], big[j] = big[j], big[i]
	})

	t0 := time.Now()
	ansFloyd := findDuplicate(big)
	t1 := time.Now()
	ansSet := findDuplicateHashSet(big)
	t2 := time.Now()
	fmt.Printf("  n=%d: floyd -> %d in %v (O(1) extra space)\n", n, ansFloyd, t1.Sub(t0))
	fmt.Printf("  n=%d: hashset -> %d in %v (O(n) extra space: a map[int]bool)\n", n, ansSet, t2.Sub(t1))
	fmt.Println("  The point of Floyd's here is the SPACE bound the problem demands, not")
	fmt.Println("  necessarily a wall-clock win — name the trade-off explicitly.")
	allOK = allOK && ansFloyd == 17 && ansSet == 17

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
