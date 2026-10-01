package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 448 · Find All Numbers Disappeared in an Array       [Easy]
https://leetcode.com/problems/find-all-numbers-disappeared-in-an-array/
================================================================================

THE CORE IDEA
-------------
`1 <= nums[i] <= n` is the whole problem. Values and indices share a range, so:

    THE ARRAY IS ITS OWN HASH TABLE.

Value v has a home: index v-1. To record "I saw v", mutate slot v-1 reversibly
without destroying the value stored there. All values are positive, so the SIGN
BIT is free storage.

INDEX-AS-HASH is how you reach "O(1) extra space" across a whole family
(LC 41, 442, 448, 645). It only works when values are bounded by the array
length — so checking that constraint is always step one.


================================================================================
APPROACH 1 · Set (the obvious answer)
================================================================================
    seen := make(map[int]struct{}, len(nums))
    for _, v := range nums { seen[v] = struct{}{} }
    for v := 1; v <= len(nums); v++ {
        if _, ok := seen[v]; !ok { res = append(res, v) }
    }

    Time:  O(n)      Space: O(n)

Correct, readable, fails the follow-up. State it, then improve.


================================================================================
APPROACH 2 · Sign marking (index-as-hash) ✅✅ (the follow-up answer)
================================================================================

STEP BY STEP for nums = [4, 3, 2, 7, 8, 2, 3, 1]:

    PASS 1 — for each value v, negate the slot at index |v|-1

    v= 4 -> i=3  nums[3]=7  positive -> negate  [ 4  3  2 -7  8  2  3  1]
    v= 3 -> i=2  nums[2]=2  positive -> negate  [ 4  3 -2 -7  8  2  3  1]
    v=-2 -> i=1  nums[1]=3  positive -> negate  [ 4 -3 -2 -7  8  2  3  1]
       ^^ ALREADY NEGATIVE — abs() is what saves us from a panic
    v=-7 -> i=6  nums[6]=3  positive -> negate  [ 4 -3 -2 -7  8  2 -3  1]
    v= 8 -> i=7  nums[7]=1  positive -> negate  [ 4 -3 -2 -7  8  2 -3 -1]
    v= 2 -> i=1  nums[1]=-3 already marked -> skip
    v=-3 -> i=2  nums[2]=-2 already marked -> skip
    v=-1 -> i=0  nums[0]=4  positive -> negate  [-4 -3 -2 -7  8  2 -3 -1]

    PASS 2 — positive slots were never marked

    index:   0   1   2   3   4   5   6   7
    value:  -4  -3  -2  -7   8   2  -3  -1
                             ^^  ^^
                       positive at indices 4 and 5
                       -> values 5 and 6 never appeared

    return [5, 6]   ✓

    Time:  O(n) — two passes      Space: O(1) excluding the output


⚠️  WHY abs() IS MANDATORY — AND WHY GO IS LOUDER ABOUT IT
    By the time you read nums[k], an earlier iteration may have flipped it
    negative. Without abs():

        v = -2  ->  i = v - 1 = -3

        Go:      panic: runtime error: index out of range [-3]   <- crashes
        Python:  silently reads nums[-3], i.e. from the END      <- wrong answer

    Go's crash is the better failure mode, but write the abs() rather than rely
    on the panic. You are using the value purely as an ADDRESS; the sign is
    metadata you added, and abs() strips it back off.

    Go has no builtin integer abs (math.Abs is float64 and would cost a
    conversion each way). Write the two-line helper.

⚠️  WHY THE `if nums[i] > 0` GUARD MATTERS
    Duplicates are exactly why numbers go missing. Negating twice returns a
    slot to positive, making a present value look absent. The guard makes
    marking idempotent. `nums[i] = -abs(nums[i])` is an equivalent branch-free
    form.

⚠️  IT MUTATES THE CALLER'S SLICE
    Slices are views onto a shared backing array — there is no copy. The
    caller's data comes back with scrambled signs. Say so. Restore with a third
    O(n) pass if it matters.


================================================================================
APPROACH 3 · Cyclic sort (swap into place)
================================================================================
    for i := 0; i < len(nums); {
        home := nums[i] - 1
        if nums[i] != nums[home] {      // compare VALUES, not indices
            nums[i], nums[home] = nums[home], nums[i]
        } else {
            i++
        }
    }
    // any index where nums[i] != i+1 is a missing value

    Time:  O(n) — each swap permanently places at least one value, so total
                  swaps <= n despite the loop looking nested
    Space: O(1)

Fully destructive (sign marking at least preserves magnitudes), but it
generalises to LC 41, 268 and 287, so it earns its place.

⚠️ The condition must be `nums[i] != nums[home]`, NOT `i != home`. With
duplicates the latter swaps forever, making no progress — an infinite loop.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach              Time    Extra space   Mutates input?
    --------------------  ------  ------------  --------------
    Set                   O(n)    O(n)          no
    Sign marking    ✅✅  O(n)    O(1)          YES (restorable)
    Cyclic sort           O(n)    O(1)          YES (destructive)


================================================================================
EDGE CASES
================================================================================
    [1]            -> [].       Present; nothing missing.
    [2, 2]         -> [1].      1 never appears.
    [1, 1]         -> [2].      Mirror.
    [1, 2, 3, 4]   -> [].       Complete permutation.
    [3, 3, 3, 3]   -> [1,2,4].  Heavy duplication — breaks any marking loop
                                without an idempotence guard.

    Return value: LeetCode accepts an empty slice. Note `var res []int` is nil,
    which encodes as `null` in JSON, while `make([]int, 0)` encodes as `[]`.
    Irrelevant to the judge here, but it matters in real APIs.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting abs() — panics in Go with index out of range.
2. Negating unconditionally, so duplicates flip slots back to positive.
3. Off-by-one: value v lives at index v-1; index i means value i+1.
4. Claiming O(1) space while building a map. Only the OUTPUT is exempt.
5. Cyclic sort with `i != home` — infinite loop on duplicates.
6. Being surprised the caller's slice was reordered. Slices alias.


================================================================================
RELATED PROBLEMS — the index-as-hash family
================================================================================
    LC 442  Find All Duplicates in an Array — same marking, collect slots you
                                              find ALREADY negative
    LC 41   First Missing Positive [Hard]   — unbounded values, so first
                                              discard anything outside [1, n]
    LC 268  Missing Number                  — one missing; XOR or Gauss sum
    LC 287  Find the Duplicate Number       — Floyd's cycle detection, because
                                              there you may NOT modify the array
    LC 645  Set Mismatch                    — one duplicate AND one missing
================================================================================
*/

// abs returns the absolute value of an int. Go has no builtin; math.Abs is
// float64 and would cost a conversion in both directions.
func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}

// findDisappearedNumbers uses sign marking. Time O(n), O(1) extra space.
// ⚠️ MUTATES the caller's slice.
func findDisappearedNumbers(nums []int) []int {
	// Pass 1: for value v, mark slot |v|-1 as seen by making it negative.
	for _, v := range nums {
		i := abs(v) - 1  // abs() — v may already have been negated
		if nums[i] > 0 { // guard keeps marking idempotent under duplicates
			nums[i] = -nums[i]
		}
	}
	// Pass 2: a still-positive slot was never marked.
	res := make([]int, 0)
	for i, v := range nums {
		if v > 0 {
			res = append(res, i+1)
		}
	}
	return res
}

// findDisappearedNumbersRestoring leaves the caller's slice exactly as found.
func findDisappearedNumbersRestoring(nums []int) []int {
	for _, v := range nums {
		i := abs(v) - 1
		nums[i] = -abs(nums[i]) // branch-free idempotent marking
	}
	res := make([]int, 0)
	for i, v := range nums {
		if v > 0 {
			res = append(res, i+1)
		}
	}
	for i := range nums { // third pass: restore
		nums[i] = abs(nums[i])
	}
	return res
}

// findDisappearedNumbersSet is the obvious O(n)-space answer.
func findDisappearedNumbersSet(nums []int) []int {
	seen := make(map[int]struct{}, len(nums))
	for _, v := range nums {
		seen[v] = struct{}{}
	}
	res := make([]int, 0)
	for v := 1; v <= len(nums); v++ {
		if _, ok := seen[v]; !ok {
			res = append(res, v)
		}
	}
	return res
}

// findDisappearedNumbersCyclic puts every value in its home slot, then reads
// off the gaps.
func findDisappearedNumbersCyclic(nums []int) []int {
	for i := 0; i < len(nums); {
		home := nums[i] - 1
		if nums[i] != nums[home] { // VALUES, not indices — else infinite loop
			nums[i], nums[home] = nums[home], nums[i]
		} else {
			i++
		}
	}
	res := make([]int, 0)
	for i, v := range nums {
		if v != i+1 {
			res = append(res, i+1)
		}
	}
	return res
}

func main() {
	type testCase struct {
		nums, want []int
	}
	cases := []testCase{
		{[]int{4, 3, 2, 7, 8, 2, 3, 1}, []int{5, 6}},
		{[]int{1, 1}, []int{2}},
		{[]int{1}, []int{}},
		{[]int{2, 2}, []int{1}},
		{[]int{1, 2, 3, 4}, []int{}},
		{[]int{3, 3, 3, 3}, []int{1, 2, 4}},
		{[]int{2, 1}, []int{}},
	}

	impls := []struct {
		name string
		fn   func([]int) []int
	}{
		{"sign marking", findDisappearedNumbers},
		{"+ restoring ", findDisappearedNumbersRestoring},
		{"set         ", findDisappearedNumbersSet},
		{"cyclic sort ", findDisappearedNumbersCyclic},
	}

	allOK := true
	for _, impl := range impls {
		ok := true
		for _, tc := range cases {
			in := append([]int(nil), tc.nums...) // fresh copy: these mutate
			got := impl.fn(in)
			if len(got) != len(tc.want) {
				ok = false
				continue
			}
			for i := range got {
				if got[i] != tc.want[i] {
					ok = false
				}
			}
		}
		allOK = allOK && ok
		fmt.Printf("%s  %s (%d cases)\n", status(ok), impl.name, len(cases))
	}

	// Watch the array become its own hash table.
	fmt.Println("\n--- sign marking, pass 1 on [4,3,2,7,8,2,3,1] ---")
	nums := []int{4, 3, 2, 7, 8, 2, 3, 1}
	fmt.Printf("  start                  %v\n", nums)
	for k := range nums {
		v := nums[k] // read LIVE: v may already be negative
		i := abs(v) - 1
		if nums[i] > 0 {
			nums[i] = -nums[i]
			fmt.Printf("  v=%2d -> negate idx %d  %v\n", v, i, nums)
		} else {
			fmt.Printf("  v=%2d -> idx %d already marked, skip\n", v, i)
		}
	}
	missing := []int{}
	for i, v := range nums {
		if v > 0 {
			missing = append(missing, i+1)
		}
	}
	fmt.Printf("  positive slots -> %v\n", missing)

	// Go panics where Python silently misbehaves.
	fmt.Println("\n--- ⚠️  what happens without abs() ---")
	func() {
		defer func() {
			if r := recover(); r != nil {
				fmt.Printf("  nums[v-1] with v=-2  ->  %v\n", r)
				fmt.Println("  Go PANICS. Python would silently read from the END")
				fmt.Println("  and return a wrong answer — the nastier failure.")
			}
		}()
		bad := []int{4, 3, 2}
		v := -2
		_ = bad[v-1] // index -3
	}()

	// Mutation.
	fmt.Println("\n--- input mutation ---")
	a := []int{4, 3, 2, 7, 8, 2, 3, 1}
	findDisappearedNumbers(a)
	fmt.Printf("  after findDisappearedNumbers:           %v\n", a)
	b := []int{4, 3, 2, 7, 8, 2, 3, 1}
	findDisappearedNumbersRestoring(b)
	fmt.Printf("  after findDisappearedNumbersRestoring:  %v  <- unchanged\n", b)

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
