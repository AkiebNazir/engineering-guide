"""
================================================================================
LeetCode 641 · Design Circular Deque                                  [Medium]
https://leetcode.com/problems/design-circular-deque/
Topic: 07 · Queue / Deque
================================================================================

PROBLEM
-------
Design your implementation of the circular double-ended queue (deque).

Implement the `MyCircularDeque` class:

    MyCircularDeque(k)          Constructs a deque with a maximum size of k.
    boolean insertFront(value)    Adds an item at the front. Returns true
                                 if successful.
    boolean insertLast(value)      Adds an item at the rear. Returns true
                                 if successful.
    boolean deleteFront()           Deletes an item from the front. Returns
                                 true if successful.
    boolean deleteLast()             Deletes an item from the rear. Returns
                                 true if successful.
    int getFront()                    Returns the front item, or -1 if empty.
    int getRear()                      Returns the last item, or -1 if empty.
    boolean isEmpty()                    Returns true if the deque is empty.
    boolean isFull()                      Returns true if the deque is full.


EXAMPLES
--------
Example 1:
    Input:
        ["MyCircularDeque", "insertLast", "insertLast", "insertFront", "insertFront", "getRear", "isFull", "deleteLast", "insertFront", "getFront"]
        [[3], [1], [2], [3], [4], [], [], [], [4], []]
    Output:
        [null, true, true, true, false, 2, true, true, true, 4]
    Explanation:
        MyCircularDeque dq = new MyCircularDeque(3);
        dq.insertLast(1);   // true, deque = [1]
        dq.insertLast(2);   // true, deque = [1, 2]
        dq.insertFront(3);  // true, deque = [3, 1, 2]
        dq.insertFront(4);  // false, already at capacity 3
        dq.getRear();       // 2
        dq.isFull();        // true
        dq.deleteLast();    // true, deque = [3, 1]
        dq.insertFront(4);  // true, deque = [4, 3, 1]
        dq.getFront();      // 4


CONSTRAINTS
-----------
    1 <= k <= 1000
    0 <= value <= 1000
    At most 2000 calls will be made to insertFront, insertLast, deleteFront,
    deleteLast, getFront, getRear, isEmpty, isFull.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is problem 004's circular queue, generalised to insert/delete at
BOTH ends (topic guide §3.2). The same fixed-size array + `head` + `size`
design works — the only new piece is that `head` can now move BACKWARD as
well as forward, and Python's `%` is already correctly sign-normalising for
a positive modulus (topic 04 §1.5), so `(head - 1) % cap` "just works" and
wraps to `cap - 1` without any manual fix-up:

    def insertFront(value):
        if size == cap: return False
        head = (head - 1) % cap        # Python: -1 % cap == cap - 1, correctly
        buf[head] = value
        size += 1
        return True

    def insertLast(value):
        if size == cap: return False
        tail = (head + size) % cap
        buf[tail] = value
        size += 1
        return True

deleteFront is identical to problem 004's deQueue (advance head forward).
deleteLast just decrements size — the current "tail" (the slot at
`(head + size - 1) % cap`) simply falls out of the valid range without
needing to move any index backward.


WHAT TO THINK ABOUT
--------------------
1. Why does `insertFront` need `(head - 1) % cap` while `insertLast` uses
   `(head + size) % cap`? Convince yourself both formulas correctly find
   the next FREE slot on their respective side.

2. In a language without Python's sign-correct `%` (C, Java, Go), what
   extra step would `(head - 1) % cap` need? Why does Python not need it?
   (Cross-reference topic 04 §1.5 — same fact, different problem.)

3. deleteLast() doesn't touch `head` at all — why is decrementing `size`
   alone sufficient to "remove" the rear element?

4. What's the difference in cost between deleteFront (moves `head`) and
   deleteLast (doesn't)? Are both still O(1)? Why doesn't the asymmetry in
   WHICH index moves cost you anything in complexity?

5. isFull() and isEmpty() need to work the same way regardless of which
   end operations came from — verify your size-tracking approach handles a
   deque that's been filled entirely from one end, entirely from the
   other, or a mix of both, identically.


PROGRESSIVE HINTS
------------------
Hint 1: Same skeleton as problem 004 (fixed array, `head`, `size`) — you're
        extending it, not starting over.

Hint 2: insertFront moves head BACKWARD first, then writes:
        `head = (head - 1) % cap; buf[head] = value`.

Hint 3: insertLast is unchanged from 004: write to
        `(head + size) % cap`, then increment size.

Hint 4: deleteFront is unchanged from 004: advance head forward, decrement
        size. deleteLast is NEW but simpler than it looks: just decrement
        size — the old rear slot naturally falls outside
        `[head, head+size)` (mod cap) and becomes "free" without moving
        anything.

Hint 5: getRear()'s index formula is the same as 004's:
        `(head + size - 1) % cap`.


COMPLEXITY TARGET
------------------
    Time:  O(1) worst-case for every operation
    Space: O(k) — the fixed-size backing array
================================================================================
"""

from typing import List


class MyCircularDeque:
    def __init__(self, k: int):
        # YOUR CODE HERE
        pass

    def insertFront(self, value: int) -> bool:
        # YOUR CODE HERE
        pass

    def insertLast(self, value: int) -> bool:
        # YOUR CODE HERE
        pass

    def deleteFront(self) -> bool:
        # YOUR CODE HERE
        pass

    def deleteLast(self) -> bool:
        # YOUR CODE HERE
        pass

    def getFront(self) -> int:
        # YOUR CODE HERE
        pass

    def getRear(self) -> int:
        # YOUR CODE HERE
        pass

    def isEmpty(self) -> bool:
        # YOUR CODE HERE
        pass

    def isFull(self) -> bool:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 005_design_circular_deque_question.py
# ==============================================================================
def run_tests() -> None:
    passed = 0
    total = 0

    def check(name, got, want):
        nonlocal passed, total
        total += 1
        ok = got == want
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {name:<40} got={got!r}  want={want!r}")

    dq = MyCircularDeque(3)
    check("insertLast(1)", dq.insertLast(1), True)
    check("insertLast(2)", dq.insertLast(2), True)
    check("insertFront(3)", dq.insertFront(3), True)
    check("insertFront(4) when full", dq.insertFront(4), False)
    check("getRear()", dq.getRear(), 2)
    check("isFull()", dq.isFull(), True)
    check("deleteLast()", dq.deleteLast(), True)
    check("insertFront(4) after deleteLast", dq.insertFront(4), True)
    check("getFront()", dq.getFront(), 4)

    dq2 = MyCircularDeque(1)
    check("empty getFront", dq2.getFront(), -1)
    check("empty getRear", dq2.getRear(), -1)
    check("empty deleteFront", dq2.deleteFront(), False)
    check("cap1 insertFront", dq2.insertFront(7), True)
    check("cap1 isFull", dq2.isFull(), True)
    check("cap1 getFront == getRear", dq2.getFront() == dq2.getRear(), True)

    print(f"\n{passed}/{total} passed")


if __name__ == "__main__":
    run_tests()
