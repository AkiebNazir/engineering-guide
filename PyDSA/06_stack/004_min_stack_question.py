"""
================================================================================
LeetCode 155 · Min Stack                                               [Medium]
https://leetcode.com/problems/min-stack/
Topic: 06 · Stack
================================================================================

PROBLEM
-------
Design a stack that supports push, pop, top, and retrieving the minimum
element in constant time.

Implement the `MinStack` class:
    MinStack()          initializes the stack object.
    void push(int val)   pushes val onto the stack.
    void pop()            removes the element on top of the stack.
    int top()             gets the top element.
    int getMin()          retrieves the minimum element in the stack.

You must implement a solution with O(1) time complexity for EACH function.


EXAMPLES
--------
Example 1:
    Input:
        ["MinStack","push","push","push","getMin","pop","top","getMin"]
        [[],[-2],[0],[-3],[],[],[],[]]
    Output:
        [null,null,null,null,-3,null,0,-2]
    Explanation:
        MinStack minStack = new MinStack();
        minStack.push(-2);
        minStack.push(0);
        minStack.push(-3);
        minStack.getMin();   // return -3
        minStack.pop();
        minStack.top();      // return 0
        minStack.getMin();   // return -2


CONSTRAINTS
-----------
    -2^31 <= val <= 2^31 - 1
    Methods pop, top and getMin will always be called on non-empty stacks.
    At most 3*10^4 calls will be made to push, pop, top, and getMin.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

The obvious approach — call `min(self.stack)` inside `getMin()` — is O(n)
per call, because it rescans the whole stack every time. The requirement is
O(1) for EVERY method, including getMin, so that shortcut is disallowed.

The fix: maintain a SECOND stack, in lockstep with the first, where each
entry records "the minimum of everything pushed so far, AT THIS DEPTH."
Pushing to both stacks together, and popping from both together, keeps
`min_stack[-1]` always correct in O(1) — no rescanning, ever.


WHAT TO THINK ABOUT
--------------------
1. When you push a value that is NOT a new minimum, does the min-stack
   still get something pushed to it? What breaks if it doesn't?
2. When you pop, do both stacks pop together, or only the main one?
3. Trace pushing 5, then 3, then popping, then checking getMin() — does the
   minimum correctly "revert" to what it was before the 3 was pushed?


PROGRESSIVE HINTS
------------------
Hint 1: `self.stack = []`, `self.min_stack = []`. On push, append to both —
        `min_stack` gets `min(val, min_stack[-1])` if non-empty, else `val`.

Hint 2: On pop, pop from BOTH stacks — this keeps them the same length, so
        `min_stack[-1]` always reflects the minimum of exactly what remains
        in `stack`.

Hint 3: `top()` returns `stack[-1]`. `getMin()` returns `min_stack[-1]`.
        Both are O(1) reads, no scanning.


COMPLEXITY TARGET
------------------
    Time:  O(1) for push, pop, top, and getMin — every operation
    Space: O(n) — two parallel stacks, each up to n entries
================================================================================
"""


class MinStack:
    def __init__(self):
        # YOUR CODE HERE
        pass

    def push(self, val: int) -> None:
        # YOUR CODE HERE
        pass

    def pop(self) -> None:
        # YOUR CODE HERE
        pass

    def top(self) -> int:
        # YOUR CODE HERE
        pass

    def getMin(self) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 004_min_stack_question.py
# ==============================================================================
def run_tests() -> None:
    ms = MinStack()
    ops = [
        ("push", -2), ("push", 0), ("push", -3),
        ("getMin", None), ("pop", None), ("top", None), ("getMin", None),
    ]
    expected = [None, None, None, -3, None, 0, -2]

    passed = 0
    results = []
    for (name, arg), want in zip(ops, expected):
        method = getattr(ms, name)
        got = method(arg) if arg is not None else method()
        results.append(got)
        ok = got == want
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}({'' if arg is None else arg}) -> {got}  (want {want})")

    print(f"\n{passed}/{len(expected)} passed")

    # A second scenario: interleaved pushes of equal minimums.
    ms2 = MinStack()
    ms2.push(1)
    ms2.push(1)
    ms2.push(2)
    assert ms2.getMin() == 1
    ms2.pop()
    assert ms2.getMin() == 1
    ms2.pop()
    assert ms2.getMin() == 1
    ms2.pop()
    print("Second scenario (duplicate minimums) OK")


if __name__ == "__main__":
    run_tests()
