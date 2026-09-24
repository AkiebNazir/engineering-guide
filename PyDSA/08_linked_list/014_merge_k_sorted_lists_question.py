"""
================================================================================
LeetCode 23 · Merge k Sorted Lists                                     [Hard]
https://leetcode.com/problems/merge-k-sorted-lists/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
You are given an array of k linked-lists `lists`, each linked-list is sorted
in ascending order. Merge all the linked-lists into ONE sorted linked-list
and return it.


EXAMPLES
--------
Example 1:
    Input:  lists = [[1,4,5],[1,3,4],[2,6]]
    Output: [1,1,2,3,4,4,5,6]

Example 2:
    Input:  lists = []
    Output: []

Example 3:
    Input:  lists = [[]]
    Output: []


CONSTRAINTS
-----------
    k == lists.length
    0 <= k <= 10^4
    0 <= lists[i].length <= 500
    -10^4 <= lists[i][j] <= 10^4
    lists[i] is sorted in ascending order.
    The sum of lists[i].length will not exceed 10^4.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This generalizes problem 002 (merge TWO sorted lists) to k lists. The naive
extension — merge list 0 into a running result, then merge list 1 into that,
then list 2, ... — works but does O(N*k) total work (N = total node count
across all lists), because each successive merge touches an ever-growing
result. Two shapes beat that, both landing at O(N log k):

1. A min-heap holding one "current front" node per list — pop the smallest,
   splice it onto the output, push its `.next` back in. The heap never
   holds more than k items, so each pop/push is O(log k).

2. Divide and conquer — merge lists in pairs, halving the list count each
   round (using problem 002's merge as the primitive), for log2(k) rounds.


WHAT TO THINK ABOUT
--------------------
1. Why is the naive sequential merge O(N*k) and not O(N)? Trace what the
   running "result" list's length looks like after each of the k merges.

2. A heap of k current-front nodes never grows past size k — why does that
   bound every heap operation's cost by O(log k) regardless of how large N
   (total nodes) gets?

3. ListNode has no `__lt__` defined — what happens if you push `(node.val,
   node)` tuples onto a heap and two nodes tie on `.val`?


PROGRESSIVE HINTS
------------------
Hint 1: Reuse problem 002's two-pointer merge as your primitive — the only
        new question is HOW to combine k of them efficiently instead of
        pairwise-and-sequentially.

Hint 2: Keep exactly one candidate node per list in a min-heap keyed by
        `.val`, with a tiebreaker (e.g. the list's index) as the heap key's
        second element to avoid comparing ListNode objects directly.

Hint 3: Alternatively, merge lists pairwise and repeat on the merged
        results — this halves the list count each round, giving log2(k)
        rounds of O(N) work each.


COMPLEXITY TARGET
------------------
    Time:  O(N log k)   where N = total nodes across all lists
    Space: O(k) (heap) or O(log k) (recursive divide and conquer)
================================================================================
"""

from typing import List, Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def mergeKLists(self, lists: List[Optional[ListNode]]) -> Optional[ListNode]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build_list(values):
    dummy = tail = ListNode()
    for v in values:
        tail.next = ListNode(v)
        tail = tail.next
    return dummy.next


def to_list(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


# ==============================================================================
# TESTS — run:  python 014_merge_k_sorted_lists_question.py
# ==============================================================================
CASES = [
    [[1, 4, 5], [1, 3, 4], [2, 6]],
    [],
    [[]],
    [[], [], []],
    [[1, 2, 3]],
    [[], [1]],
    [[-5, -1, 0], [-4, -4, 3], [2]],
    [[1, 1, 1], [1, 1], [1]],
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for lists in CASES:
        want = sorted(v for lst in lists for v in lst)
        got = to_list(sol.mergeKLists([build_list(lst) for lst in lists]))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  lists={lists!r:<38} -> {got}  (want {want})")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
