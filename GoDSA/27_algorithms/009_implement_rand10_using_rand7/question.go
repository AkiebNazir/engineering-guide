package main

/*
================================================================================
QUESTION · LeetCode 470 · Implement Rand10() Using Rand7()          [Medium]
https://leetcode.com/problems/implement-rand10-using-rand7/
================================================================================

PROBLEM
-------
Given the API `rand7()` that generates a uniform random integer in the range
`[1, 7]`, write a function `rand10()` that generates a uniform random integer
in the range `[1, 10]`. You can only call the API `rand7()`, and you
shouldn't call any other API. Please do not use a language's built-in random
API.

Each integer should have equal probability of being returned.


EXAMPLES
--------
Example 1:
    Input:  n = 1
    Output: [2]

Example 2:
    Input:  n = 2
    Output: [2,8]

Example 3:
    Input:  n = 3
    Output: [3,8,10]

    (n is the number of times rand10() is called by the judge; the outputs
    are one valid random realization, not the only correct answer.)


CONSTRAINTS
-----------
    1 <= n <= 10^5

FOLLOW-UP
---------
    1. What is the expected value for the number of calls to rand7()?
    2. Could you minimize the number of calls to rand7()?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
You need to turn a uniform source over 7 outcomes into a uniform source over
10 outcomes. No fixed number of rand7() calls can do it EXACTLY: k calls give
7^k equally likely outcomes, and 7^k is never divisible by 10 (7^k has no
factor of 2 or 5). So any exact answer must sometimes throw an outcome away
and try again -- the running time is a random variable with a small expected
value, not a constant.

The trick is to build a BIGGER uniform range first. Two calls read as the two
digits of a base-7 number give 49 equally likely outcomes:

    idx = (rand7() - 1) * 7 + rand7()          // uniform on 1..49

     rand7() #2 ->  1   2   3   4   5   6   7
    rand7() #1
         1          1   2   3   4   5   6   7
         2          8   9  10  11  12  13  14
         ...
         6         36  37  38  39  40 |41  42      <- 41..49 are the
         7         43  44  45  46  47  48  49         rejected cells

Keep only the outcomes you can split evenly into 10 buckets, reject the rest.

WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. `rand.Intn(n)` is EXCLUSIVE of n: the harness's rand7 is
   `rand.Intn(7) + 1`. You must not call rand.* yourself in rand10.
2. Test the DISTRIBUTION, not one draw: count 10 buckets over many calls and
   run a chi-square check (topic guide Part 1.3). A fixed seed only checks
   one outcome sequence.
3. Count rand7() calls with a package-level counter to answer follow-up 1
   with a measurement, not only with algebra.


PROGRESSIVE HINTS
------------------
Hint 1: rand7() + rand7() is NOT uniform on 2..14 -- it is triangular (7 is
        the most likely sum). Adding random variables is not the way.
Hint 2: Treat two calls as a 2-digit base-7 number: `(a-1)*7 + b` is uniform
        on 1..49 because every (a, b) pair maps to a distinct cell.
Hint 3: 40 is the largest multiple of 10 that is <= 49. Accept 1..40 and
        return `(idx-1)%10 + 1`; on 41..49, loop and draw again. Reducing
        all 49 outcomes % 10 would make 10 rarer than 1..9 (4 cells vs 5).
Hint 4 (follow-up 2): a rejected idx in 41..49 is itself uniform on 9
        values -- keep it as the high digit of the next draw instead of
        throwing its randomness away.


COMPLEXITY TARGET
------------------
    Time:  O(1) expected -- 2 / (40/49) = 2.45 expected rand7() calls
           (about 2.19 with the remainder-recycling follow-up)
    Space: O(1)
================================================================================
*/

// rand7 is the only randomness you may use; it is defined in solution.go
// (the judge's API) so this file and the solution compile as one package.

// YourRand10 is your attempt.
// Implement it, then run:  cd GoDSA && go run ./27_algorithms/009_implement_rand10_using_rand7
func YourRand10() int {
	// YOUR CODE HERE
	return 0
}
