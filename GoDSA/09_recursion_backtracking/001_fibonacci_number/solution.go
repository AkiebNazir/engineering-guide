package main

import (
	"fmt"
	"time"
)

/*
================================================================================
SOLUTION · LeetCode 509 · Fibonacci Number                               [Easy]
https://leetcode.com/problems/fibonacci-number/
================================================================================

THE CORE IDEA
-------------
The definition F(n) = F(n-1) + F(n-2) translates straight into a recursive
function, and that function is CORRECT -- but its call tree branches twice
per level and recomputes the same subproblems over and over, so it makes
O(phi^n) calls (phi ~ 1.618). Remembering each F(k) the first time it is
computed (memoization) visits every k once: O(n). And since F(n) only needs
the previous two values, two rolling variables give O(n) time, O(1) space.

    a, b := 0, 1            // F(0), F(1)
    for i := 0; i < n; i++ {
        a, b = b, a+b       // Go's tuple assignment evaluates the right side first
    }
    return a


================================================================================
CALL TREE for fib(6) -- where the exponential cost comes from
================================================================================
Unlike factorial, which recurses in a straight line, Fibonacci branches:
every call below the base cases splits into TWO calls.

                               fib(6)
                             /        \
                      fib(5)            fib(4)
                     /      \           /      \
                fib(4)      fib(3)   fib(3)    fib(2)
               /     \       /    \    /   \     /   \
           fib(3)  fib(2) fib(2) f(1) f(2) f(1) f(1) f(0)
           /   \    /   \  /   \      /   \
       f(2) f(1) f(1) f(0)f(1)f(0)   f(1) f(0)
       /  \
     f(1) f(0)

fib(4) is computed 2 times, fib(3) 3 times, fib(2) 5 times -- the counts are
themselves Fibonacci numbers. fib(6) makes 25 calls; fib(30) makes 2,692,537
(counted in main below). With a memo, fib(30) needs 31 distinct computations.


================================================================================
APPROACH 1 · Naive recursion (correct, exponential)
================================================================================
    func fibNaive(n int) int {
        if n < 2 { return n }            // TWO base cases: F(0)=0, F(1)=1
        return fibNaive(n-1) + fibNaive(n-2)
    }
O(phi^n) time, O(n) stack depth. Fine for n <= 30 on LeetCode, and the right
thing to write FIRST in an interview -- then price it.


================================================================================
APPROACH 2 · Top-down memoization
================================================================================
Go has no @lru_cache: write the cache by hand. A slice indexed by n beats a
map here (dense keys 0..n, no hashing), and a closure keeps it private.

    memo := make([]int, n+1); seen := make([]bool, n+1)
    var f func(int) int
    f = func(k int) int {
        if k < 2 { return k }
        if seen[k] { return memo[k] }
        memo[k], seen[k] = f(k-1)+f(k-2), true
        return memo[k]
    }
O(n) time, O(n) memo + O(n) stack.


================================================================================
APPROACH 3 · Bottom-up, two rolling variables ✅ (the answer)
================================================================================
Shown in THE CORE IDEA. O(n) time, O(1) space, no recursion at all.
(There is also an O(log n) matrix-power / fast-doubling method -- mention it
as a follow-up; for n <= 30 it is not worth the code.)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach               Time        Space            Note
    ---------------------  ----------  ---------------  ----------------------
    Naive recursion        O(phi^n)    O(n) stack       2.7M calls at n = 30
    Memoized (top-down)    O(n)        O(n) + O(n)      hand-written cache in Go
    Rolling vars ✅        O(n)        O(1)             the answer
    Fast doubling          O(log n)    O(log n) stack   follow-up only


================================================================================
EDGE CASES
================================================================================
    n = 0 -> 0    (the loop body never runs; a = 0)
    n = 1 -> 1    (forgetting the SECOND base case recurses into fib(-1)
                   forever -> goroutine stack overflow)
    n = 30 -> 832040; F(92) is the largest that fits in int64 -- F(93)
              overflows silently in Go (no exception, just a wrong number).


================================================================================
COMMON MISTAKES
================================================================================
1. One base case only (`if n == 0`) -- fib(1) calls fib(0)+fib(-1) and never
   stops.
2. `a = b; b = a + b` on two lines -- b uses the NEW a. Use the tuple
   assignment `a, b = b, a+b`, which evaluates the whole right side first.
3. Presenting the naive version as final without saying "exponential".
4. Assuming Go will optimise the recursion: the Go compiler does no tail-call
   elimination (topic guide 2.1), and this isn't tail-recursive anyway.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How many calls does the naive version make?
A: calls(n) = 1 + calls(n-1) + calls(n-2) = 2*F(n+1) - 1: 25 for n = 6,
   2,692,537 for n = 30.

Q: n up to 10^18, answer mod 1e9+7?
A: Fast doubling: F(2k) = F(k)*(2F(k+1) - F(k)), F(2k+1) = F(k)^2 + F(k+1)^2,
   O(log n) multiplications.

Q: Climbing Stairs (LC 70)?
A: The same recurrence shifted by one -- this exact loop.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 70    Climbing Stairs              -- same recurrence (topic 16)
    LC 1137  N-th Tribonacci Number       -- three rolling variables
    LC 746   Min Cost Climbing Stairs     -- same DP skeleton with a min
================================================================================
*/

// fib is the interview answer: two rolling variables. O(n) time, O(1) space.
func fib(n int) int {
	a, b := 0, 1
	for i := 0; i < n; i++ {
		a, b = b, a+b
	}
	return a
}

// naiveCalls counts calls made by fibNaive so main can show the blow-up.
var naiveCalls int

// fibNaive follows the definition literally. O(phi^n) time, O(n) stack.
func fibNaive(n int) int {
	naiveCalls++
	if n == 0 || n == 1 {
		return n
	}
	return fibNaive(n-1) + fibNaive(n-2)
}

// fibMemo is top-down recursion with a hand-written cache. O(n) time and space.
func fibMemo(n int) int {
	memo := make([]int, n+1)
	seen := make([]bool, n+1)
	var f func(int) int
	f = func(k int) int {
		if k < 2 {
			return k
		}
		if seen[k] {
			return memo[k]
		}
		memo[k], seen[k] = f(k-1)+f(k-2), true
		return memo[k]
	}
	return f(n)
}

func status(ok bool) string {
	if ok {
		return "PASS"
	}
	return "FAIL"
}

func main() {
	cases := []struct{ n, want int }{
		{0, 0}, {1, 1}, {2, 1}, {3, 2}, {4, 3}, {10, 55}, {20, 6765}, {30, 832040},
	}
	allOK := true

	fmt.Println("--- correctness: all three approaches agree ---")
	for _, c := range cases {
		naiveCalls = 0
		gotNaive := fibNaive(c.n)
		gotMemo, gotIter := fibMemo(c.n), fib(c.n)
		ok := gotNaive == c.want && gotMemo == c.want && gotIter == c.want
		allOK = allOK && ok
		fmt.Printf("%s  n=%-3d naive=%-7d memo=%-7d iter=%-7d want=%d\n",
			status(ok), c.n, gotNaive, gotMemo, gotIter, c.want)
	}

	fmt.Println("\n--- the exponential blow-up, counted (calls = 2*F(n+1) - 1) ---")
	for _, n := range []int{6, 10, 20, 30} {
		naiveCalls = 0
		start := time.Now()
		fibNaive(n)
		elapsed := time.Since(start)
		want := 2*fib(n+1) - 1
		ok := naiveCalls == want
		allOK = allOK && ok
		fmt.Printf("%s  fibNaive(%2d): %9d calls (formula %9d)  %v\n", status(ok), n, naiveCalls, want, elapsed.Round(time.Microsecond))
	}
	fmt.Println("      fib(30) with memo or the loop: 31 distinct values computed")

	fmt.Println("\n--- int64 limit: F(92) fits, F(93) overflows silently ---")
	f92, f93 := fib(92), fib(93)
	ok := f92 == 7540113804746346429 && f93 < 0
	allOK = allOK && ok
	fmt.Printf("%s  fib(92)=%d  fib(93)=%d (wrapped negative)\n", status(ok), f92, f93)

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
