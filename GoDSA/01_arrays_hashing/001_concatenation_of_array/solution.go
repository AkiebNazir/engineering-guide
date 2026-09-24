package main

import (
	"fmt"
	"reflect"
)

/*
================================================================================
SOLUTION · LeetCode 1929 · Concatenation of Array                        [Easy]
https://leetcode.com/problems/concatenation-of-array/
================================================================================

THE CORE IDEA
-------------
The output length is known before you start: exactly 2n. Preallocate and fill.

The index mapping is the only real content:

    output index  ->  source index
    ------------      -------------
    i        (i < n)   nums[i]
    i + n              nums[i]

Equivalently, for output index j in [0, 2n): ans[j] = nums[j % n]. The modulo
view generalises to "repeat k times" and to circular-array problems (LC 503).


================================================================================
⚠️  THE GO TRAP — read this even if you solved it
================================================================================
The tempting one-liner is:

    return append(nums, nums...)

This is WRONG, and it is wrong in a way that passes the LeetCode judge while
being a genuine bug in real code. Here is why.

`append` writes into the existing backing array when there is spare capacity,
and only allocates a new array when there is not. So:

    nums := make([]int, 3, 10)   // len=3, cap=10  <- 7 spare slots
    nums = []int{1, 2, 1}        // (conceptually)

    ans := append(nums, nums...)

    BEFORE:
      backing ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
              │  1 │  2 │  1 │ -- │ -- │ -- │ -- │ -- │ -- │ -- │
              └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
      nums ───► len=3, cap=10

    AFTER append (cap was sufficient — NO new allocation):
      backing ┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐
              │  1 │  2 │  1 │  1 │  2 │  1 │ -- │ -- │ -- │ -- │
              └────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
      nums ───► len=3  (unchanged view, but SAME array)
      ans  ───► len=6  (aliases nums!)

    Now `ans[0] = 99` also changes `nums[0]`. The caller's data is corrupted.

It "works" on LeetCode only because the judge passes a slice whose cap == len,
forcing a reallocation. Rely on that and you have written a latent bug.

**Rule: never `append` to a slice you did not create, if the caller still uses
it.** Either allocate your own, or cap the capacity with a three-index slice
(`nums[:len(nums):len(nums)]`) to force allocation.


================================================================================
APPROACH 1 · One loop, preallocated (the version to write in an interview)
================================================================================

STEP BY STEP for nums = [1, 2, 1], n = 3:

    ans := make([]int, 6)           // zeroed, exact final size

    i = 0:  ans[0]   = nums[0] = 1   ->  [1 0 0 0 0 0]
            ans[0+3] = nums[0] = 1   ->  [1 0 0 1 0 0]

    i = 1:  ans[1]   = nums[1] = 2   ->  [1 2 0 1 0 0]
            ans[1+3] = nums[1] = 2   ->  [1 2 0 1 2 0]

    i = 2:  ans[2]   = nums[2] = 1   ->  [1 2 1 1 2 0]
            ans[2+3] = nums[2] = 1   ->  [1 2 1 1 2 1]

    return [1 2 1 1 2 1]   ✓

`make([]int, 2*n)` is one allocation. Growing from nil via append would
reallocate ~log(2n) times (doubling under cap 256), copying each time. Both are
O(n), but one allocation beats twenty.


================================================================================
APPROACH 2 · Two copy() calls (most idiomatic Go)
================================================================================
    ans := make([]int, 2*n)
    copy(ans, nums)        // fills ans[0:n]
    copy(ans[n:], nums)    // fills ans[n:2n]

`copy` compiles down to `runtime.memmove` — a single bulk move per call, far
faster than an element-by-element loop. `copy` returns the number of elements
copied (min of the two lengths), which also makes it safe by construction: it
can never overflow the destination.

This is the version most Go reviewers would prefer.


================================================================================
APPROACH 3 · Safe append (when you want the one-liner)
================================================================================
    ans := make([]int, 0, 2*n)     // our OWN backing array, right-sized
    ans = append(ans, nums...)
    ans = append(ans, nums...)
    return ans

Because `ans` starts with cap 2n, neither append reallocates, and because we
allocated it ourselves there is no aliasing with the caller. This is the correct
way to express the "concatenate" intent.


================================================================================
COMPLEXITY
================================================================================
    All approaches:
      Time:  O(n)   — each element written a constant number of times
      Space: O(n)   — the output slice (required by the problem)

    Extra space beyond the output: O(1).

    Approach 2 has the best constant factor: two memmoves, no per-element
    bounds checks.


================================================================================
EDGE CASES
================================================================================
    n = 1            -> [x, x].            Loop runs once. Fine.
    All identical    -> [7,7] -> [7,7,7,7]. Nothing special.
    nil / empty      -> Constraints say n >= 1. But make([]int, 0) and two
                        copies of nothing still produce an empty slice, so all
                        three approaches are correct anyway.


================================================================================
COMMON MISTAKES
================================================================================
1. `return append(nums, nums...)` — aliases and can mutate the caller. See the
   trap section above. This is THE lesson of this problem.

2. `var ans []int` then appending 2n times — correct but does ~11 reallocations
   for n=1000 where 1 would do.

3. `for i := 0; i < 2*n; i++ { ans[i] = nums[i] }` — index out of range once
   i >= n. You need `nums[i%n]`.

4. Declaring `ans := make([]int, 0, 2*n)` and then INDEXING `ans[i]` — panics,
   because len is 0. `make([]int, 2*n)` sets len; `make([]int, 0, 2*n)` sets
   only cap. Know which one you wrote.


================================================================================
RELATED PROBLEMS (the "+n offset" / doubled-array idea)
================================================================================
    LC 503  Next Greater Element II   — iterate 2n, use i%n for a circle
    LC 189  Rotate Array              — index arithmetic with an offset
    LC 213  House Robber II           — circular constraint handled by splitting
================================================================================
*/

// getConcatenation is the interview answer: one pass, preallocated.
// Time O(n), space O(n) for the output.
func getConcatenation(nums []int) []int {
	n := len(nums)
	ans := make([]int, 2*n) // single allocation, exact final size
	for i := 0; i < n; i++ {
		ans[i] = nums[i]   // first copy
		ans[i+n] = nums[i] // second copy, shifted by n
	}
	return ans
}

// getConcatenationCopy is the most idiomatic Go version: two memmoves.
func getConcatenationCopy(nums []int) []int {
	n := len(nums)
	ans := make([]int, 2*n)
	copy(ans, nums)
	copy(ans[n:], nums)
	return ans
}

// getConcatenationAppend is the safe form of the append one-liner: we own the
// backing array, so there is no aliasing with the caller.
func getConcatenationAppend(nums []int) []int {
	ans := make([]int, 0, 2*len(nums))
	ans = append(ans, nums...)
	ans = append(ans, nums...)
	return ans
}

// getConcatenationModulo shows the circular-array view that generalises to
// "repeat k times".
func getConcatenationModulo(nums []int) []int {
	n := len(nums)
	ans := make([]int, 2*n)
	for j := range ans {
		ans[j] = nums[j%n]
	}
	return ans
}

func main() {
	type testCase struct {
		nums, want []int
	}
	cases := []testCase{
		{[]int{1, 2, 1}, []int{1, 2, 1, 1, 2, 1}},
		{[]int{1, 3, 2, 1}, []int{1, 3, 2, 1, 1, 3, 2, 1}},
		{[]int{1}, []int{1, 1}},
		{[]int{7, 7}, []int{7, 7, 7, 7}},
	}

	impls := []struct {
		name string
		fn   func([]int) []int
	}{
		{"preallocated", getConcatenation},
		{"copy()      ", getConcatenationCopy},
		{"safe append ", getConcatenationAppend},
		{"modulo      ", getConcatenationModulo},
	}

	allOK := true
	for _, impl := range impls {
		ok := true
		for _, tc := range cases {
			in := append([]int(nil), tc.nums...) // defensive copy per run
			if !reflect.DeepEqual(impl.fn(in), tc.want) {
				ok = false
			}
		}
		allOK = allOK && ok
		fmt.Printf("%s  %s (%d cases)\n", status(ok), impl.name, len(cases))
	}

	// Demonstrate the aliasing trap concretely.
	fmt.Println("\n--- the append(nums, nums...) trap ---")
	backing := make([]int, 3, 10) // cap > len, as real code often has
	copy(backing, []int{1, 2, 1})
	aliased := append(backing, backing...) // DANGEROUS
	aliased[0] = 99
	fmt.Printf("after aliased[0]=99 -> caller's slice is %v (corrupted: %t)\n",
		backing, backing[0] == 99)

	safe := make([]int, 3, 10)
	copy(safe, []int{1, 2, 1})
	result := getConcatenation(safe)
	result[0] = 99
	fmt.Printf("with getConcatenation -> caller's slice is %v (corrupted: %t)\n",
		safe, safe[0] == 99)

	// Confirm no implementation mutates its input.
	orig := []int{1, 2, 3}
	getConcatenation(orig)
	mutOK := reflect.DeepEqual(orig, []int{1, 2, 3})
	allOK = allOK && mutOK
	fmt.Printf("\n%s  input not mutated\n", status(mutOK))

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
