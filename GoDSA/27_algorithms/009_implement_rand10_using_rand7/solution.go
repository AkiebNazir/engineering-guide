package main

import (
	"fmt"
	"math/rand"
)

/*
================================================================================
SOLUTION · LeetCode 470 · Implement Rand10() Using Rand7()          [Medium]
https://leetcode.com/problems/implement-rand10-using-rand7/
================================================================================

THE CORE IDEA
-------------
Rejection sampling on a uniform grid. Two rand7() calls, read as the two
digits of a base-7 number, give a uniform integer on 1..49 (a 7 x 7 grid in
which every cell is equally likely). 40 is the largest multiple of 10 that
fits, so cells 1..40 map evenly onto 1..10 with `(idx-1)%10 + 1` -- four
cells per answer -- and cells 41..49 are rejected: loop and draw again.

    for {
        idx := (rand7()-1)*7 + rand7()   // uniform on 1..49
        if idx <= 40 {
            return (idx-1)%10 + 1        // 4 cells per value -> uniform on 1..10
        }
    }

Why the accepted values stay uniform: conditioned on idx <= 40, idx is
uniform on 1..40 (every cell had the same probability before conditioning,
and conditioning removes cells, it does not reweight the survivors).


================================================================================
EXPECTED CALLS (follow-up 1)
================================================================================
One attempt succeeds with probability p = 40/49. The number of attempts is
geometric, so E[attempts] = 1/p = 49/40 = 1.225, and each attempt costs two
rand7() calls:

    E[calls] = 2 * 49/40 = 2.45

The worst case is unbounded (every attempt could land in 41..49), but the
chance of needing more than k attempts is (9/49)^k -- about 3.4% for k = 2 and
about 0.11% for k = 4.


================================================================================
APPROACH 1 · Reject 41..49 and redraw both digits ✅ (the interview answer)
================================================================================
Shown above: rand10Basic. 2.45 expected calls, O(1) space, 6 lines.


================================================================================
APPROACH 2 · Recycle the rejected remainder (follow-up 2)
================================================================================
A rejected idx in 41..49 is still uniform on 9 values -- throwing it away
wastes entropy. Keep an accumulator `a` that is uniform on 0..span-1; each
rand7() call multiplies the span by 7. Once span >= 10, accept if `a` is
below the largest multiple of 10 that fits in the span; otherwise subtract
that multiple and keep the leftover (still uniform on a smaller span) as the
high digits of the next round.

    a, span := 0, 1
    for {
        a, span = a*7 + (rand7()-1), span*7
        if span >= 10 {
            lim := span - span%10
            if a < lim { return a%10 + 1 }
            a, span = a-lim, span-lim   // leftover is uniform on 0..span-lim-1
        }
    }

The measured cost is about 2.19 calls (see main). The information-theoretic
floor is log(10)/log(7) ~ 1.18 calls, reachable only by batching many rand10
outputs together (arithmetic-coding style) -- mention it, don't code it.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Expected rand7() calls   Space   Uniform?
    ------------------------------  -----------------------  ------  --------
    rand7() + rand7() (wrong)       2                        O(1)    NO (triangular)
    idx % 10 over all 49 (wrong)    2                        O(1)    NO (10 is rarer)
    Reject 41..49 ✅                2.45                     O(1)    yes
    Recycle the remainder           ~2.19 (measured)         O(1)    yes


================================================================================
EDGE CASES
================================================================================
    Many consecutive rejections -> just more loop iterations; never wrong.
    The value 10                -> must come from cells 10, 20, 30, 40:
                                   `(idx-1)%10 + 1`, not `idx%10` (which
                                   yields 0 for multiples of 10).
    n up to 10^5 calls          -> ~245,000 rand7() calls; trivial.


================================================================================
COMMON MISTAKES
================================================================================
1. Adding: `rand7() + rand7()` (then squeezing it into 1..10) -- sums of uniform
   variables are not uniform. Demonstrated below with a chi-square score.
2. No rejection: `idx % 10 + 1` over all 49 cells gives 1..9 five cells each
   and 10 only four -- a 20% under-representation of one value.
3. `idx%10` instead of `(idx-1)%10 + 1` -- returns 0..9, not 1..10.
4. Calling `rand.Intn(10)` directly inside rand10 -- violates the problem.
5. Rejecting on a single call: `r := rand7(); if r <= 5 { return r*2 }` only
   produces even numbers. You need a range of at least 10 cells to split.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Build rand7() from rand5().
A: Same recipe: (rand5()-1)*5 + rand5() is uniform on 1..25; accept 1..21
   (largest multiple of 7), return (idx-1)%7 + 1.

Q: Build a fair coin from a BIASED coin with unknown p.
A: Von Neumann's trick: flip twice; HT -> heads, TH -> tails, HH/TT -> retry.
   P(HT) = P(TH) = p(1-p), so the accepted outcomes are equally likely.

Q: Where does this show up in real code?
A: Go's own rand.Intn(n) does it: it draws from the generator's full range
   and rejects the top sliver that would cause modulo bias (topic guide
   Part 1.2). Uniform sampling from a non-power-of-two range is always
   rejection underneath.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 528  Random Pick with Weight        -- prefix sums + binary search
    LC 710  Random Pick with Blacklist     -- remap instead of reject
    LC 384  Shuffle an Array               -- Fisher-Yates, uniform permutations
================================================================================
*/

// rng is the one source of randomness; seeded so the demo output is
// reproducible. rand7 is the judge's API -- nothing else may touch rng.
var (
	rng        = rand.New(rand.NewSource(470))
	rand7Calls int
)

func rand7() int {
	rand7Calls++
	return rng.Intn(7) + 1 // Intn is EXCLUSIVE: 0..6, shifted to 1..7
}

// rand10Basic is the interview answer: rejection sampling on the 7x7 grid.
// Expected rand7() calls: 2 * 49/40 = 2.45. Space O(1).
func rand10Basic() int {
	for {
		idx := (rand7()-1)*7 + rand7() // uniform on 1..49
		if idx <= 40 {
			return (idx-1)%10 + 1
		}
	}
}

// rand10Recycle keeps the rejected remainder as extra entropy.
// Invariant: a is uniform on 0..span-1. Expected calls ~2.19 (measured).
func rand10Recycle() int {
	a, span := 0, 1
	for {
		a, span = a*7+(rand7()-1), span*7
		if span >= 10 {
			lim := span - span%10 // largest multiple of 10 that fits in span
			if a < lim {
				return a%10 + 1
			}
			a, span = a-lim, span-lim // leftover is still uniform: keep it
		}
	}
}

// rand10Sum is WRONG ON PURPOSE: a sum of two rand7 calls is triangular.
// Mapped into 1..10 it still cannot be uniform.
func rand10Sum() int {
	return (rand7()+rand7()-2)%10 + 1
}

// rand10NoReject is WRONG ON PURPOSE: all 49 cells reduced mod 10, so the
// value 10 gets 4 cells while 1..9 get 5 each.
func rand10NoReject() int {
	idx := (rand7()-1)*7 + rand7()
	return (idx-1)%10 + 1
}

// ---------------------------------------------------------------------------
// Test helpers.
// ---------------------------------------------------------------------------

// chiSquare draws `trials` values from f, checks every value is in 1..10,
// and returns the chi-square statistic against the uniform distribution
// plus the average number of rand7() calls per draw.
func chiSquare(f func() int, trials int) (chi2 float64, callsPerDraw float64, inRange bool) {
	var counts [11]int
	rand7Calls = 0
	inRange = true
	for i := 0; i < trials; i++ {
		v := f()
		if v < 1 || v > 10 {
			inRange = false
			continue
		}
		counts[v]++
	}
	expected := float64(trials) / 10
	for v := 1; v <= 10; v++ {
		d := float64(counts[v]) - expected
		chi2 += d * d / expected
	}
	return chi2, float64(rand7Calls) / float64(trials), inRange
}

func status(ok bool) string {
	if ok {
		return "PASS"
	}
	return "FAIL"
}

func main() {
	const trials = 200_000
	// df = 9: the 99.9th percentile of chi-square is ~27.9. A correct
	// algorithm scores ~9 on average; a biased one scores in the hundreds+.
	const critical = 27.9
	allOK := true

	fmt.Println("--- correct implementations (expect chi2 well below 27.9) ---")
	for _, tc := range []struct {
		name      string
		f         func() int
		wantCalls float64
	}{
		{"rand10Basic  ", rand10Basic, 2.45},
		{"rand10Recycle", rand10Recycle, 2.19},
	} {
		chi2, calls, inRange := chiSquare(tc.f, trials)
		ok := inRange && chi2 < critical && calls > tc.wantCalls-0.05 && calls < tc.wantCalls+0.05
		allOK = allOK && ok
		fmt.Printf("%s  %s  chi2=%7.2f  rand7 calls/draw=%.3f (expected ~%.2f)\n",
			status(ok), tc.name, chi2, calls, tc.wantCalls)
	}

	fmt.Println("\n--- the tempting wrong answers (expect chi2 far above 27.9) ---")
	for _, tc := range []struct {
		name string
		f    func() int
	}{
		{"rand7()+rand7()     ", rand10Sum},
		{"idx%10, no rejection", rand10NoReject},
	} {
		chi2, _, _ := chiSquare(tc.f, trials)
		detected := chi2 > critical
		allOK = allOK && detected
		fmt.Printf("%s  %s  chi2=%9.2f  bias detected=%v\n", status(detected), tc.name, chi2, detected)
	}

	fmt.Println("\n--- the 7x7 grid: cells per output value when accepting 1..40 ---")
	var cells [11]int
	for a := 1; a <= 7; a++ {
		for b := 1; b <= 7; b++ {
			if idx := (a-1)*7 + b; idx <= 40 {
				cells[(idx-1)%10+1]++
			}
		}
	}
	gridOK := true
	for v := 1; v <= 10; v++ {
		gridOK = gridOK && cells[v] == 4
	}
	allOK = allOK && gridOK
	fmt.Printf("%s  cells per value 1..10: %v (every value exactly 4)\n", status(gridOK), cells[1:])

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
