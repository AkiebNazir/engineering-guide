package main

/*
================================================================================
QUESTION · LeetCode 990 · Satisfiability of Equality Equations        [Medium]
https://leetcode.com/problems/satisfiability-of-equality-equations/
================================================================================

PROBLEM
-------
You are given an array of strings `equations` that represent relationships
between variables where each string equations[i] is of length 4 and takes
one of two different forms: "xi==yi" or "xi!=yi". Here, xi and yi are
lowercase letters (not necessarily different) that represent one-letter
variable names.

Return true if it is possible to assign integers to variable names so as
to satisfy all the given equations, or false otherwise.


EXAMPLES
--------
Example 1:
    Input:  ["a==b","b!=a"]
    Output: false
    Explanation: If we assign say, a = 1 and b = 1, then the first equation
    is satisfied, but not the second. There is no way to assign the
    variables to satisfy both equations.

Example 2:
    Input:  ["b==a","a==b"]
    Output: true
    Explanation: We could assign a = 1 and b = 1 to satisfy both equations.

Example 3:
    Input:  ["a==b","b==c","a==c"]
    Output: true

Example 4:
    Input:  ["a==b","b!=c","c==a"]
    Output: false

Example 5:
    Input:  ["c==c","b==d","x!=z"]
    Output: true


CONSTRAINTS
-----------
    1 <= equations.length <= 500
    equations[i].length == 4
    equations[i][0] is a lowercase letter.
    equations[i][1] is either '=' or '!'.
    equations[i][2] is '='.
    equations[i][3] is a lowercase letter.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"==" is an EQUIVALENCE relation (reflexive, symmetric, transitive) -- exactly
what Union-Find models: group everything that must be equal into one set.
"!=" is then just a CONSTRAINT that two particular variables must land in
DIFFERENT sets.

The two-pass structure this suggests:
    Pass 1: union every pair joined by "==". This decides which letters are
            forced to be equal, following transitivity for free (Union-Find
            IS transitive closure).
    Pass 2: for every "!=" pair, check whether Union-Find has (incorrectly)
            placed them in the same set. If it has, the equations are
            jointly unsatisfiable.

Order matters: "==" must ALL be processed before ANY "!=" check, because a
"!=" pair might only become same-set after a LATER "==" union runs (see
Example 4: a==b, then b!=c, then c==a -- checking b!=c before c==a runs
would miss that a and c end up equal).

PROGRESSIVE HINTS
------------------
Hint 1: There are only 26 possible variables ('a'..'z') -- fixed-size
        Union-Find, map each letter to an index with `ord(ch) - ord('a')`.
Hint 2: Do a full pass unioning every "==" equation first.
Hint 3: THEN do a second pass over the "!=" equations, and return False the
        moment any pair's `find` values match.
Hint 4: An equation like "a!=a" is a contradiction on its own (a variable
        can never differ from itself) -- make sure your check does not need
        a special case, since find('a') == find('a') is always true.

COMPLEXITY TARGET
------------------
    Time:  O(n) -- n equations, each processed in near-O(1) with Union-Find
    Space: O(1) -- at most 26 variables
================================================================================
*/

// TODO: Implement the stub
