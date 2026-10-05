package main

import "fmt"

/*
================================================================================
LeetCode 445 · Add Two Numbers II                                        [Medium]
https://leetcode.com/problems/add-two-numbers-ii/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
You are given two non-empty linked lists representing two non-negative
integers. The most significant digit comes first, and each node contains
a single digit. Add the two numbers and return the sum as a linked list.

You may assume the two numbers do not contain any leading zero, except
the number 0 itself.

EXAMPLES
--------
Example 1:
    Input:  l1 = [7,2,4,3], l2 = [5,6,4]
    Output: [7,8,0,7]
    Explanation: 7243 + 564 = 7807

Example 2:
    Input:  l1 = [2,4,3], l2 = [5,6,4]
    Output: [8,0,7]

Example 3:
    Input:  l1 = [0], l2 = [0]
    Output: [0]

CONSTRAINTS
-----------
    1 <= l1.length, l2.length <= 100
    0 <= l1.val, l2.val <= 9 (no leading zeros unless the number itself is 0)

FOLLOW-UP (stated on LeetCode)
-------------------------------
What if you could not modify the input lists? In other words, reversal
is not allowed.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Ordinary "add two numbers" (LC 2) stores digits LEAST-significant-first,
so addition can proceed straight from the heads with a running carry. This
variant stores digits MOST-significant-first — like adding two numbers on
paper by hand, you actually need to start from the ONES place, which is at
the END of each list.

The recursion this demands: pad the shorter list with leading zeros so
both lists have EQUAL LENGTH, then recurse to the very end of both lists
first (that's the ones place), add going forward, and let the CARRY
propagate back UP through the return values — the carry is a second piece
of information riding along with "the rest of the digits," which is
exactly the "return a pair" combine pattern the topic guide calls out.

    addSameLength(l1, l2):
        if l1 is None: return (0, None)                 <- base case: past both ends
        carry, restNode = addSameLength(l1.next, l2.next)
        total = l1.val + l2.val + carry
        node = ListNode(total % 10, restNode)
        return (total // 10, node)                        <- (new carry, node built for THIS digit)

WHAT TO THINK ABOUT
--------------------
1. Why must the two lists be padded to EQUAL length before this
   recursion can work correctly? What breaks if they're different
   lengths and you just call `addSameLength(l1, l2)` directly?
2. What TWO pieces of information does each call need to hand back to
   its caller, and why can't a single return value carry both?
3. Where does the recursion "bottom out," and what is added there? (The
   very last digits of both lists — the ones place — where the carry
   starts at 0 implicitly, since there's no digit before it yet.)
4. After the recursion fully unwinds, there might be ONE leftover carry
   from the most significant digit (e.g. 5+7=12) — where does that extra
   digit get prepended, and why can't it be handled inside the recursion
   itself?

PROGRESSIVE HINTS
------------------
Hint 1: First, compute both lists' lengths and pad the SHORTER one with
        leading zero nodes so both have equal length.
Hint 2: Base case for the equal-length addition: `l1 is None` (both lists
        exhausted simultaneously) -> return `(carry=0, node=None)`.
Hint 3: Recurse on `.next, .next` FIRST to get `(carry, restNode)` for
        everything after this digit, THEN compute
        `total = l1.val + l2.val + carry`, build a node for
        `total % 10` pointing at `restNode`, and return
        `(total // 10, thisNode)`.
Hint 4: After the top-level call returns `(finalCarry, headNode)`, if
        `finalCarry` is 1, prepend one more node with value 1 in front of
        `headNode`.

COMPLEXITY TARGET
------------------
    Recursive: O(max(m, n)) time, O(max(m, n)) space (call stack + padding)
    Iterative (using two stacks): O(m + n) time, O(m + n) space
================================================================================
*/

func main() {
	fmt.Println("Solution for Add Two Numbers II not implemented yet")
}
