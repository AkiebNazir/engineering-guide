package main

import (
	"fmt"
	"sort"
	"time"
)

/*
================================================================================
SOLUTION · LeetCode 217 · Contains Duplicate                             [Easy]
https://leetcode.com/problems/contains-duplicate/
================================================================================

THE CORE IDEA
-------------
You are asking one question repeatedly: "have I seen this value before?"

That question has one good answer: a HASH SET. It turns an O(n) membership scan
into an O(1) average lookup, collapsing the problem from O(n^2) to O(n).

In Go there is no set type, so you build one from a map. That detail is the
whole Go-specific lesson here.


================================================================================
THE GO SET IDIOM
================================================================================

    seen := make(map[int]struct{}, len(nums))   // preallocate!
    seen[x] = struct{}{}                        // add
    _, exists := seen[x]                        // contains  (comma-ok)
    delete(seen, x)                             // remove
    len(seen)                                   // size

Why `struct{}` and not `bool`?

    struct{}  occupies ZERO bytes. The map stores only keys, so
              map[int]struct{} is a true set with no per-entry value overhead.
    bool      occupies 1 byte, but lets you write `if seen[x] { ... }`
              directly, which is shorter and reads better.

For 10^5 ints the difference is 100 KB versus 0 — irrelevant here, meaningful at
scale. Both are accepted; state your reasoning and move on.

⚠️ WHY COMMA-OK IS MANDATORY: a Go map returns the ZERO VALUE for a missing key,
not an error and not nil.

    counts := map[string]int{"a": 0}
    v := counts["a"]        // 0  — present, value 0
    v = counts["zzz"]       // 0  — ABSENT. Indistinguishable!
    v, ok := counts["zzz"]  // 0, false  ← the only way to tell

This is one of the top Go bugs in interviews. Build the comma-ok reflex.


================================================================================
APPROACH 1 · Brute force (state it, do NOT code it)
================================================================================
    for i := 0; i < n; i++ {
        for j := i + 1; j < n; j++ {
            if nums[i] == nums[j] { return true }
        }
    }

    Time:  O(n^2)  — n(n-1)/2 comparisons
    Space: O(1)

At n = 10^5 that is ~5x10^9 comparisons. Go is fast, but that is still many
seconds — well past the limit. Say this out loud, give the complexity, then
improve it. Do not spend interview time typing it.


================================================================================
APPROACH 2 · Hash set, single pass ✅ (the answer)
================================================================================

STEP BY STEP for nums = [1, 2, 3, 1]:

    seen = {}

    x = 1:  _, ok := seen[1]  ->  ok == false   ->  seen[1] = struct{}{}
            seen = {1}
    x = 2:  ok == false                         ->  seen = {1, 2}
    x = 3:  ok == false                         ->  seen = {1, 2, 3}
    x = 1:  ok == TRUE                          ->  return true   ✓

And for nums = [1, 2, 3, 4]: four misses, loop ends, return false.  ✓

    Time:  O(n)  — one pass, O(1) average per lookup + insert
    Space: O(n)  — up to n keys

THE EARLY RETURN MATTERS: on [1,1,1,...,1] this returns after 2 elements
instead of scanning 10^5. Same big-O, very different real behaviour.

PREALLOCATION MATTERS TOO: `make(map[int]struct{}, len(nums))` sizes the bucket
array once. Without the hint, Go starts at 1 bucket and grows through
~log2(n/6.5) doublings, each triggering incremental evacuation of every key.
Same O(n) amortized, noticeably better constant.


================================================================================
APPROACH 3 · Sort first — the O(1) SPACE answer
================================================================================

    sort.Ints(nums)
    for i := 1; i < len(nums); i++ {
        if nums[i] == nums[i-1] { return true }
    }

After sorting, equal values are adjacent, so one neighbour scan suffices.

    Time:  O(n log n)   — pdqsort
    Space: O(log n)     — pdqsort's recursion stack; effectively O(1)

⚠️ It MUTATES the caller's slice. Slices are views onto a shared backing array,
so `sort.Ints(nums)` reorders the CALLER's data — there is no copy. If the
caller still needs the original order you must clone first, and then you are
back to O(n) space. Raise this yourself; it is exactly the kind of side effect
interviewers probe for.

This is the answer to "now do it without extra space."


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach          Time         Space      Early exit?  Mutates input?
    ----------------  -----------  ---------  -----------  --------------
    Brute force       O(n^2)       O(1)       yes          no
    Hash set     ✅   O(n)         O(n)       yes          no
    Sort + scan       O(n log n)   O(log n)   yes          YES


================================================================================
EDGE CASES
================================================================================
    [1]           -> false.  Single element cannot duplicate.
    [1, 1]        -> true.   Smallest true case.
    [-1, -1]      -> true.   Negative keys hash fine.
    All distinct  -> false.  Worst case for Approach 2 (full scan).
    All identical -> true.   Best case (exits at i=1).
    nil / empty   -> Constraints say n >= 1; the loop simply does not run and
                     returns false, which is correct anyway.


================================================================================
COMMON MISTAKES
================================================================================
1. Using a SLICE for `seen` and doing a linear search inside the loop —
   O(n) inside O(n) is O(n^2). Looks almost identical to the correct code.

2. Inserting before checking:
       seen[x] = struct{}{}
       if _, ok := seen[x]; ok { return true }   // ← always true immediately
   Check, THEN insert.

3. Writing `if seen[x]` on a map[int]struct{} — does not compile; struct{} is
   not a boolean. Either use comma-ok, or switch to map[int]bool.

4. Writing to a nil map:
       var seen map[int]struct{}     // nil
       seen[1] = struct{}{}          // PANIC: assignment to entry in nil map
   Reading a nil map is fine; writing panics. Always `make` it.

5. Saying lookup is "O(1)". It is O(1) AVERAGE. Say the word.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
    "Already sorted?"          -> Skip the map; scan neighbours. O(n) / O(1).
    "Values guaranteed 1..n?"  -> Index-as-hash with sign marking. O(1) space.
    "Doesn't fit in memory?"   -> External sort, or a Bloom filter (no false
                                  negatives, some false positives).
    "Return the duplicate?"    -> Same scan, return x. See LC 287.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 219  Contains Duplicate II   — within index distance k
    LC 220  Contains Duplicate III  — within value distance t (bucketing)
    LC 287  Find the Duplicate Number — O(1) space via Floyd's cycle detection
    LC 442  Find All Duplicates in an Array — index-as-hash
================================================================================
*/

// containsDuplicate is the interview answer: one pass over a hash set,
// with an early return. Time O(n) average, space O(n).
func containsDuplicate(nums []int) bool {
	seen := make(map[int]struct{}, len(nums)) // preallocate: avoids regrowth
	for _, x := range nums {
		if _, exists := seen[x]; exists { // comma-ok: the Go membership test
			return true
		}
		seen[x] = struct{}{} // struct{} costs zero bytes
	}
	return false
}

// containsDuplicateBoolMap is the same algorithm with map[int]bool: 1 byte per
// entry, but the membership test reads better.
func containsDuplicateBoolMap(nums []int) bool {
	seen := make(map[int]bool, len(nums))
	for _, x := range nums {
		if seen[x] { // zero value false == "not seen", so this is safe here
			return true
		}
		seen[x] = true
	}
	return false
}

// containsDuplicateSort trades time for space. O(n log n), O(log n) space,
// and it MUTATES the caller's slice.
func containsDuplicateSort(nums []int) bool {
	sort.Ints(nums)
	for i := 1; i < len(nums); i++ {
		if nums[i] == nums[i-1] {
			return true
		}
	}
	return false
}

// containsDuplicateBruteForce is O(n^2). Contrast only — never submit this.
func containsDuplicateBruteForce(nums []int) bool {
	for i := 0; i < len(nums); i++ {
		for j := i + 1; j < len(nums); j++ {
			if nums[i] == nums[j] {
				return true
			}
		}
	}
	return false
}

func main() {
	type testCase struct {
		nums []int
		want bool
	}
	cases := []testCase{
		{[]int{1, 2, 3, 1}, true},
		{[]int{1, 2, 3, 4}, false},
		{[]int{1, 1, 1, 3, 3, 4, 3, 2, 4, 2}, true},
		{[]int{1}, false},
		{[]int{-1, -1}, true},
		{[]int{0, 1, -1, 2, -2}, false},
		{[]int{2, 2}, true},
	}

	impls := []struct {
		name string
		fn   func([]int) bool
	}{
		{"hash set (struct{})", containsDuplicate},
		{"hash set (bool)    ", containsDuplicateBoolMap},
		{"sort + scan        ", containsDuplicateSort},
		{"brute force        ", containsDuplicateBruteForce},
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

	// Demonstrate that sort mutates the caller's slice.
	fmt.Println("\n--- sort.Ints mutates the caller's slice ---")
	data := []int{3, 1, 2}
	containsDuplicateSort(data)
	fmt.Printf("caller's slice after containsDuplicateSort: %v (reordered: %t)\n",
		data, data[0] != 3)

	// Show the O(n) vs O(n^2) gap the constraint protects you from.
	fmt.Println("\n--- why the brute force is ruled out (all-distinct input) ---")
	for _, n := range []int{10_000, 40_000} {
		in := make([]int, n)
		for i := range in {
			in[i] = i
		}
		t0 := time.Now()
		containsDuplicate(append([]int(nil), in...))
		tSet := time.Since(t0)

		t0 = time.Now()
		containsDuplicateBruteForce(append([]int(nil), in...))
		tBF := time.Since(t0)

		fmt.Printf("  n=%6d  hash set %8v   brute force %10v   (%.0fx slower)\n",
			n, tSet.Round(time.Microsecond), tBF.Round(time.Microsecond),
			float64(tBF)/float64(tSet))
	}
	fmt.Println("  (brute force scales x4 when n doubles; the hash set scales x2)")

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
