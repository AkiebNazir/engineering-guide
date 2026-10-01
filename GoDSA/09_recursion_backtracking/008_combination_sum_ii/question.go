package main

/*
================================================================================
LeetCode 40 · Combination Sum II                                        [Medium]
https://leetcode.com/problems/combination-sum-ii/
Topic: 09 · Recursion / Backtracking
================================================================================
PROBLEM
-------
Given a collection of candidate numbers `candidates` (which MAY CONTAIN
DUPLICATES) and a target number `target`, find all UNIQUE combinations in
`candidates` where the candidate numbers sum to `target`.

Each number in `candidates` may be used ONCE ONLY in each combination.

Note: the solution set must not contain duplicate combinations.

EXAMPLES
--------
Example 1:
    Input:  candidates = [10,1,2,7,6,1,5], target = 8
    Output: [[1,1,6],[1,2,5],[1,7],[2,6]]
    Explanation:
        There are TWO 1s in the input, so [1,1,6] is legal — it uses both.
        But [1,7] must appear ONCE, not twice, even though either 1 could
        have been the one used.

Example 2:
    Input:  candidates = [2,5,2,1,2], target = 5
    Output: [[1,2,2],[5]]
    Explanation: three 2s are available, so [1,2,2] is legal; [5] uses the
    single 5.

CONSTRAINTS
-----------
    1 <= candidates.length <= 100
    1 <= candidates[i] <= 50
    1 <= target <= 30

    Compare against LC 39's constraints, because both differences matter:
      LC 39: candidates DISTINCT, candidates[i] >= 2, unlimited reuse
      LC 40: candidates MAY REPEAT, candidates[i] >= 1, each used ONCE

    `candidates[i] >= 1` is enough to guarantee termination here, because
    each element is consumed at most once — there is no reuse to run away
    with. That is why LC 39 needed `>= 2` and this one does not.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This problem is the intersection of two things you have already done:

    problem 007 (LC 39)  sum target, reuse allowed, distinct input
    problem 003 (LC 90)  duplicates in input, each element used once

LC 40 is 003's dedupe rule plus 007's sum target. TWO changes from 007, and
missing either one gives a wrong answer:

    1. `backtrack(i + 1)` instead of `backtrack(i)`  — no reuse
    2. the duplicate-SIBLING skip                     — no duplicate results

           if i > start and candidates[i] == candidates[i - 1]:
               continue

Change 1 alone leaves duplicate combinations in the output (the two 1s in
example 1 are different indices, so [1,7] arrives twice). Change 2 alone
would still let a single element be reused. You need both.

THE CRITICAL DISTINCTION
-------------------------
"Each number may be used once" refers to each ELEMENT (each array position),
not each VALUE. `[1,1,6]` is a legal answer for example 1 because the input
really does contain two separate 1s. What is forbidden is emitting the SAME
combination twice because two equal values sat at different indices.

So the rule cannot be "never pick a value you have already picked". It has to
be "never pick a value as a SIBLING CHOICE at the same tree node when an
equal value was already tried there" — that is exactly what `i > start`
expresses, and why `i > 0` is wrong. Problem 003's guide and solution work
through that guard in detail; re-read them before writing this.

WHY SORTING IS NOT OPTIONAL
----------------------------
The skip test compares `candidates[i]` with `candidates[i - 1]` — its ONLY
notion of "an equal value was already tried here" is adjacency. On
`[2,5,2,1,2]` the three 2s are not adjacent, so nothing is caught and
duplicates slip straight through. Sorting is what makes equal values
adjacent, and therefore what makes the guard mean anything.

Sorting buys a second thing for free: ascending order lets you `break` out of
the loop the moment `candidates[i] > remaining`, exactly as in 007.

WHAT TO THINK ABOUT
--------------------
1. Write down 007's solution and 003's solution side by side. This problem's
   solution is a literal merge of the two. Which line comes from which?

2. On input `[1,1,6]` with target 8, trace the tree. At the ROOT, i=0 picks
   the first 1 and i=1 must be SKIPPED. But one level down (start=1), i=1
   picks the second 1 and is allowed. Same index, different decision, because
   `start` differs. Make sure you can say why both are correct.

3. What is the maximum recursion depth? Each element is used at most once, so
   it is bounded by `len(candidates)` — and also by
   `target // min(candidates)`. Which bound is tighter for the given
   constraints (n <= 100, target <= 30, values >= 1)?

4. Would `set(tuple(sorted(c)) for c in results)` at the end also work? Yes.
   Price it: how many branches does it build and then throw away on an input
   like `[1] * 18` with target 9?

5. Do you need a `used[]` array? No — `start` already prevents reuse of an
   index, exactly as in 006/007. `used[]` belongs to the permutation shape
   (004/005), where there is no "only look forward" rule to lean on.

PROGRESSIVE HINTS
------------------
Hint 1: Sort `candidates` first. Everything below assumes ascending order.

Hint 2: Start from 007's solution and change the recursive call from
        `backtrack(i, ...)` to `backtrack(i + 1, ...)`. Run the examples: you
        will now get duplicate combinations, which is the next hint's job.

Hint 3: Add, as the FIRST statement inside the loop:
            if i > start and candidates[i] == candidates[i - 1]:
                continue
        Note it is `continue`, not `break` — you are skipping this one
        sibling, not abandoning the rest of the loop.

Hint 4: Keep 007's `break` too, but as a separate test:
            if candidates[i] > remaining:
                break
        One `continue` (duplicate sibling) and one `break` (too big, and so
        is everything after it). They do different jobs; keep both.

Hint 5: `results.append(path[:])`, never `results.append(path)`.

COMPLEXITY TARGET
------------------
    Time:  O(2^n) worst case in the number of nodes — each element is either
           in or out, so the tree is the subsets tree with a sum test at the
           leaves. With sorting, the `break`, and the sibling skip, the tree
           actually walked is far smaller; the sibling skip in particular
           collapses runs of equal values from `2^k` branches to `k + 1`.
    Space: O(n) for the recursion stack and `path`, excluding output.
================================================================================
*/

// TODO: Implement the stub
