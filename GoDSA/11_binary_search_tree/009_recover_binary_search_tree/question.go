package main

/*
================================================================================
QUESTION · LeetCode 99 · Recover Binary Search Tree                     [Hard]
https://leetcode.com/problems/recover-binary-search-tree/
================================================================================

PROBLEM
-------
You are given the `root` of a binary search tree (BST), where the values of
EXACTLY TWO nodes were swapped by mistake. Recover the tree without
changing its structure.


EXAMPLES
--------
Example 1:
    Input:  root = [1,3,null,null,2]
    Output: [3,1,null,null,2]

    Before (broken):        After (recovered):
          1                        3
        ╱                        ╱
      3                        1
        ╲                        ╲
          2                        2

    Explanation: 3 cannot be a left child of 1 because 3 > 1. Swapping the
    values of 1 and 3 makes the BST valid.

Example 2:
    Input:  root = [3,1,4,null,null,2]
    Output: [2,1,4,null,null,3]

              3                        2
            ╱   ╲                    ╱   ╲
          1       4                1       4
                ╱                        ╱
              2                        3

    Explanation: 2 cannot be in the right subtree of 3 because 2 < 3.
    Swapping the values of 2 and 3 makes the BST valid.


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [2, 1000].
    -2^31 <= Node.val <= 2^31 - 1
    It is GUARANTEED that the tree was a valid BST before exactly two of
    its nodes were swapped.

Follow up: A solution using O(n) space is pretty straightforward. Could you
devise a constant O(1) space solution?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is problem 006 (Validate BST) run in reverse: instead of asking "is
the in-order sequence sorted?", it asks "the in-order sequence is ALMOST
sorted except for one corruption — find and undo it."

Picture the correct in-order sequence as strictly increasing, then imagine
someone swapped the VALUES held by two of those positions (not their tree
positions — their values). Walking the in-order sequence and comparing each
value to the one before it, a swap shows up as either ONE dip (if the two
swapped nodes are ADJACENT in the in-order sequence) or TWO dips (if they
are far apart):

    correct:        1  2  3  4  5  6  7
    adjacent swap:   1  2  4  3  5  6  7        <- one dip: (4,3)
                                ^--- 4 > 3, one violation
    far swap:        1  6  3  4  5  2  7        <- two dips: (6,3) and (5,2)
                          ^                  ^
                  first dip's FIRST element  second dip's SECOND element
                  is the true smaller value  is the true larger value

The pattern that recovers both cases with one rule: scan in-order, and at
EVERY dip (`prev.val > curr.val`), remember `prev` if it's the FIRST dip
seen, and always remember `curr` as the (possibly updated) second culprit.
After the scan, swap `first.val` and `second.val`.


PROGRESSIVE HINTS
------------------
Hint 1: This is problem 006's in-order-strictly-increasing check, but
        instead of returning False at the first violation, you need to
        REMEMBER which two nodes are involved.

Hint 2: Walk in-order (iteratively, with a stack — same pattern as 006/007/
        008) tracking `prev`. At each step, if `prev.val > curr.val`,
        you've found a "dip." There can be ONE dip (adjacent swap) or TWO
        dips (non-adjacent swap) — work out on paper which node in the
        SECOND dip is part of the true answer.

Hint 3: `first` is set only on the FIRST dip's `prev`. `second` is updated
        on EVERY dip's `curr` — so if there are two dips, `second` ends up
        holding the value from the SECOND one.

Hint 4: Once you've found `first` and `second` (both TreeNode references,
        not values), the fix is one line: swap `first.val` and
        `second.val`. Do not touch any pointers — the problem explicitly
        says "without changing its structure."

Hint 5: For the O(1)-space follow-up, look up Morris in-order traversal —
        it achieves the same walk without a stack or recursion by
        temporarily threading `null` right pointers.


COMPLEXITY TARGET
------------------
    Time:  O(n) — a single in-order pass
    Space: O(h) with an explicit stack (the straightforward target);
           O(1) is the stated follow-up (Morris traversal)
================================================================================
*/

// TODO: Implement the stub
