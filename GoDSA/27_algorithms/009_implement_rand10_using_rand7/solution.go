package implement_rand10_using_rand7

/*
================================================================================
SOLUTION · LeetCode 470 · Implement Rand10() Using Rand7()          [Medium]
https://leetcode.com/problems/implement-rand10-using-rand7/
================================================================================

THE CORE IDEA
--------------
Rejection Sampling. 
If we want a random number between 1 and 10 uniformly, we can generate a random
number in a larger uniform range (like 1 to 49), map the first 40 outcomes 
uniformly to 1..10, and simply "reject" and try again if we hit an outcome 
above 40. 

To generate a uniform number between 1 and 49 using rand7(), we can conceptualize
it as a 7x7 grid. The row is chosen by `rand7()` and the column is chosen by 
another `rand7()`. The formula `idx = (row - 1) * 7 + col` maps every unique 
pair `(row, col)` to a unique integer from 1 to 49. Since both row and col 
are uniform, every number from 1 to 49 is equally likely.

If `idx` is between 1 and 40, we map it to 1..10 by doing `(idx - 1) % 10 + 1`.
If `idx` is 41..49, we reject it and loop again. 

EXPECTED CALLS (MATH)
---------------------
The probability of a success (an index <= 40) is 40/49.
The number of attempts follows a geometric distribution where p = 40/49.
The expected number of attempts E(x) is 1/p = 49/40 = 1.225.
Since each attempt costs two calls to rand7(), the expected calls is 2.45.
*/

func rand10Solution() int {
	for {
		row := rand7()
		col := rand7()

		// This generates a uniform random integer from 1 to 49
		idx := (row-1)*7 + col

		// If the number is within our desired 1 to 40 uniform range, map it!
		if idx <= 40 {
			return (idx-1)%10 + 1
		}
	}
}
