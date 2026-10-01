package main

import (
	"fmt"
	"sort"
)

/*
================================================================================
SOLUTION · LeetCode 169 · Majority Element                               [Easy]
https://leetcode.com/problems/majority-element/
================================================================================

THE CORE IDEA
-------------
Everything hinges on one phrase: the majority element appears MORE THAN ⌊n/2⌋
times. Strictly more than half. Therefore:

    count(majority)  >  count(everything else COMBINED)

Repeatedly cancel one majority element against one non-majority element and you
run out of non-majority elements first. The majority is the last one standing.


================================================================================
APPROACH 1 · Map counting
================================================================================
    counts := make(map[int]int, len(nums))
    for _, v := range nums { counts[v]++ }
    // then take the key with the largest count

    Time:  O(n)      Space: O(n)

Correct and obvious; fails the follow-up on space. Note `counts[v]++` needs no
initialisation — Go's zero value for int is 0, the same trick that replaces
Python's defaultdict(int).


================================================================================
APPROACH 2 · Sort and take the middle
================================================================================
    sort.Ints(nums)
    return nums[len(nums)/2]

    Time:  O(n log n)   Space: O(log n) for pdqsort's stack
    ⚠️ MUTATES the caller's slice.

WHY IT WORKS — be ready to justify this:
an element occupying more than half the positions forms, once sorted, a
contiguous block longer than n/2. A block longer than half the array cannot
avoid covering index n/2, wherever it starts.

    n = 7, majority appears 4 times, block length 4 in 7 slots:
      earliest start:  [M M M M _ _ _]   covers index 3 ✓
      latest start:    [_ _ _ M M M M]   covers index 3 ✓
    Every 4-block in a 7-array straddles index 3.


================================================================================
APPROACH 3 · Boyer–Moore Majority Vote ✅✅ (the follow-up answer)
================================================================================

    count, candidate := 0, 0
    for _, v := range nums {
        if count == 0 { candidate = v }
        if v == candidate { count++ } else { count-- }
    }
    return candidate

THE MENTAL MODEL — a battle where opposites annihilate:
each element is a soldier; soldiers of different armies kill each other
one-for-one. The majority army outnumbers all others combined, so only majority
soldiers can remain when the dust settles.

`count` is "how many soldiers of the current candidate's army remain
unopposed." At 0 the candidate has been fully cancelled, so we adopt whoever
comes next.

STEP BY STEP for nums = [2, 2, 1, 1, 1, 2, 2]:

    idx  v   count==0?  candidate  count   note
    ---  --  ---------  ---------  -----   ----------------------------
      0   2  yes        2          1       adopt 2
      1   2  no         2          2       matches, +1
      2   1  no         2          1       differs, -1  (a 1 kills a 2)
      3   1  no         2          0       differs, -1  (candidate wiped out)
      4   1  yes        1          1       adopt 1
      5   2  no         1          0       differs, -1  (candidate wiped out)
      6   2  yes        2          1       adopt 2

    return 2   ✓   (2 appears 4 of 7 times — a true majority)

The candidate changed three times. That is expected. The algorithm does NOT
track "most frequent so far"; the invariant is subtler:

    after any prefix, if a majority exists in the FULL array it is either the
    current candidate, or its surplus was spent cancelling an equal number of
    non-majority elements in the discarded prefix — and the remaining suffix
    still holds it as a majority.

Every cancellation removes one majority and one non-majority element. Since the
majority strictly outnumbers all others, cancellations exhaust the others first.

    Time:  O(n)   — single pass, no allocation
    Space: O(1)   — two ints

⚠️ CRITICAL CAVEAT: this returns a CANDIDATE, not a verified majority. With no
majority present it returns garbage. The problem guarantees one exists, so one
pass suffices here. Remove that guarantee (LC 229, or real code) and you MUST
verify:

    occurrences := 0
    for _, v := range nums { if v == candidate { occurrences++ } }
    if occurrences > len(nums)/2 { return candidate }
    return -1

Still O(n) time, O(1) space. Volunteering this caveat is what separates
understanding the algorithm from reciting it.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach              Time         Space     Mutates?  Needs guarantee?
    --------------------  -----------  --------  --------  ----------------
    Map counting          O(n)         O(n)      no        no
    Sort + middle         O(n log n)   O(log n)  YES       no
    Boyer–Moore     ✅✅  O(n)         O(1)      no        YES (or verify)


================================================================================
EDGE CASES
================================================================================
    [1]              -> 1.  One element is trivially a majority (1 > 0).
    [1, 2, 1]        -> 1.  Candidate flips, then recovers.
    [6, 5, 5]        -> 5.  Majority is NOT the first element — catches anyone
                            who forgot to re-adopt when count hits 0.
    [-1,-1,-1,2,3]   -> -1. Negatives are fine; only equality is tested.
    All identical    -> that element; count only increments.


================================================================================
COMMON MISTAKES
================================================================================
1. Returning `count` instead of `candidate`. The counter is scaffolding.

2. Adopting a candidate only at i == 0. You must re-adopt EVERY time count
   reaches 0 — see [6, 5, 5], where the first candidate is wrong.

3. Believing the candidate is the most frequent element seen so far. It is not
   at intermediate steps; only the final value is meaningful.

4. Using bare Boyer–Moore where no majority is guaranteed. It returns nonsense
   with total confidence.

5. `sort.Ints(nums)` and then being surprised the caller's slice is reordered.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 229  Majority Element II — elements appearing > n/3 times. Generalised
                                  Boyer–Moore with TWO candidates and two
                                  counters, plus a MANDATORY verification pass.
                                  (For > n/k you need k-1 candidates.)
    LC 1150 Check If a Number Is Majority Element in a Sorted Array
================================================================================
*/

// majorityElement is the follow-up answer: Boyer–Moore vote.
// Time O(n), space O(1), zero allocations.
func majorityElement(nums []int) int {
	count, candidate := 0, 0
	for _, v := range nums {
		if count == 0 { // current candidate fully cancelled
			candidate = v // adopt whoever we see next
		}
		if v == candidate {
			count++
		} else {
			count--
		}
	}
	return candidate
}

// majorityElementVerified adds the second pass. Use this whenever a majority is
// NOT guaranteed. Returns -1 when none exists. Still O(n) time, O(1) space.
func majorityElementVerified(nums []int) int {
	candidate := majorityElement(nums)
	occurrences := 0
	for _, v := range nums {
		if v == candidate {
			occurrences++
		}
	}
	if occurrences > len(nums)/2 {
		return candidate
	}
	return -1
}

// majorityElementMap is O(n) time, O(n) space. Needs no guarantee.
func majorityElementMap(nums []int) int {
	counts := make(map[int]int, len(nums))
	best, bestCount := 0, 0
	for _, v := range nums {
		counts[v]++ // zero value means no init branch needed
		if counts[v] > bestCount {
			best, bestCount = v, counts[v]
		}
	}
	return best
}

// majorityElementSort relies on a >n/2 block always covering index n/2.
// ⚠️ MUTATES the caller's slice.
func majorityElementSort(nums []int) int {
	sort.Ints(nums)
	return nums[len(nums)/2]
}

func main() {
	type testCase struct {
		nums []int
		want int
	}
	cases := []testCase{
		{[]int{3, 2, 3}, 3},
		{[]int{2, 2, 1, 1, 1, 2, 2}, 2},
		{[]int{1}, 1},
		{[]int{1, 2, 1}, 1},
		{[]int{6, 5, 5}, 5},
		{[]int{-1, -1, -1, 2, 3}, -1},
		{[]int{8, 8, 7, 7, 7}, 7},
	}

	impls := []struct {
		name string
		fn   func([]int) int
	}{
		{"Boyer-Moore", majorityElement},
		{"BM+verify  ", majorityElementVerified},
		{"map count  ", majorityElementMap},
		{"sort+middle", majorityElementSort},
	}

	allOK := true
	for _, impl := range impls {
		ok := true
		for _, tc := range cases {
			in := append([]int(nil), tc.nums...) // fresh copy: sort mutates
			if impl.fn(in) != tc.want {
				ok = false
			}
		}
		allOK = allOK && ok
		fmt.Printf("%s  %s (%d cases)\n", status(ok), impl.name, len(cases))
	}

	// Trace the candidate flipping — the unintuitive part.
	fmt.Println("\n--- Boyer-Moore trace: [2,2,1,1,1,2,2] ---")
	fmt.Println("  idx  v   candidate  count  note")
	count, candidate := 0, 0
	for i, v := range []int{2, 2, 1, 1, 1, 2, 2} {
		note := ""
		if count == 0 {
			candidate = v
			note = fmt.Sprintf("adopt %d", v)
		}
		if v == candidate {
			count++
		} else {
			count--
		}
		if count == 0 && note == "" {
			note = "candidate wiped out"
		}
		fmt.Printf("  %3d  %d   %9d  %5d  %s\n", i, v, candidate, count, note)
	}
	fmt.Printf("  -> returns %d\n", candidate)

	// The caveat, demonstrated.
	fmt.Println("\n--- ⚠️  no majority exists: the candidate is meaningless ---")
	noMaj := []int{1, 2, 3, 4}
	fmt.Printf("  nums=%v  (nothing appears more than 2 times)\n", noMaj)
	fmt.Printf("  bare Boyer-Moore  -> %d  <- GARBAGE\n", majorityElement(noMaj))
	fmt.Printf("  with verification -> %d  <- correctly reports 'none'\n",
		majorityElementVerified(noMaj))

	// sort mutates.
	fmt.Println("\n--- sort.Ints mutates the caller's slice ---")
	data := []int{3, 2, 3}
	majorityElementSort(data)
	fmt.Printf("  caller's slice after majorityElementSort: %v (reordered)\n", data)

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
