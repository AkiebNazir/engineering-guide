package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 710 · Random Pick with Blacklist                  [Hard]
https://leetcode.com/problems/random-pick-with-blacklist/
================================================================================

PROBLEM
-------
You are given an integer `n` and an array `blacklist` of UNIQUE integers,
each in the range `[0, n - 1]`, and an integer that is banned. Design a
class to pick a random integer in the range `[0, n - 1]` that is NOT in
`blacklist`, such that every valid number has an EQUAL probability of being
returned.

Optimize your solution so that it minimizes the number of calls to the
built-in random function of your language.

Implement the `Solution` class:
    Solution(n, blacklist)  initializes the object with n and blacklist.
    pick()                  returns a random integer in [0, n - 1] excluding
                             blacklist, each with equal probability.


EXAMPLES
--------
Example 1:
    Input:
        ["Solution", "pick", "pick", "pick", "pick", "pick", "pick", "pick"]
        [[7, [2, 3, 5]], [], [], [], [], [], [], []]
    Output:
        [null, 0, 4, 1, 6, 1, 0, 4]
    Explanation: n=7, blacklist=[2,3,5]. Every call to pick() must return
    one of {0, 1, 4, 6} uniformly at random (order of the sample output is
    just one valid realization).


CONSTRAINTS
-----------
    1 <= n <= 10^9
    0 <= blacklist.length <= min(10^5, n - 1)
    0 <= blacklist[i] < n
    All values in blacklist are unique.
    At most 2 * 10^4 calls will be made to pick().

FOLLOW-UP: n can be up to 10^9 -- you cannot materialize the full whitelist
array. Minimize both preprocessing cost and the number of random() calls
per pick().


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The naive idea -- "pick a random index in [0, n-1], reject and resample if
it's blacklisted" -- is CORRECT (uniform over the whitelist) but its expected
number of random() calls per pick blows up as `len(blacklist) / n` approaches
1: with a 99%-blacklisted range, each pick needs ~100 random() calls on
average, and there is no upper bound on any single call (arbitrarily many
misses are possible, just increasingly unlikely). The elegant fix: pick
uniformly from a SHRUNK range `[0, whitelist_size - 1]` where
`whitelist_size = n - len(blacklist)`, so every draw is a hit by
construction -- and REMAP the draw only when it happens to land on a
blacklisted number inside that shrunk range, forwarding it to some
non-blacklisted number OUTSIDE the shrunk range. Building that remap table
costs O(B) preprocessing (B = len(blacklist)); every pick() afterward is O(1)
with EXACTLY ONE random() call.

PROGRESSIVE HINTS
------------------
Hint 1: Reject-and-resample (draw uniformly from [0, n-1], redraw if
        blacklisted) is correct but can need an unbounded number of
        random() calls per pick when the blacklist covers most of the
        range -- price it, don't ship it as your final answer if n can be
        adversarial.
Hint 2: Define `whitelist_size = n - len(blacklist)`. If you could draw
        uniformly from `[0, whitelist_size - 1]` and guarantee every value
        in that smaller range maps to a DISTINCT non-blacklisted number,
        every pick would need exactly one random() call, no rejection ever.
Hint 3: Only blacklisted numbers that fall INSIDE `[0, whitelist_size - 1]`
        are a problem (a blacklisted number already outside that range
        doesn't interfere with draws restricted to the shrunk range). For
        each such number, you need to remap it to some valid, non-
        blacklisted number that lies AT OR ABOVE `whitelist_size`.
Hint 4: Build the remap once, in the constructor: walk the numbers at or
        above `whitelist_size` that are NOT in blacklist, and pair them off
        (in order) with the blacklisted numbers that fall below
        `whitelist_size`. Store this as a dict; `pick()` draws in
        `[0, whitelist_size - 1]` and looks up the dict (default: the draw
        itself) in O(1).

COMPLEXITY TARGET
------------------
    Time:  O(B) constructor, O(1) per pick() -- exactly one random() call
    Space: O(B) for the remap table
================================================================================
*/

func main() {
	fmt.Println("Solution for Random Pick with Blacklist not implemented yet")
}
