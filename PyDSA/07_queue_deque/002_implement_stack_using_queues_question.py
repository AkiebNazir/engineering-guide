"""
================================================================================
LeetCode 225 · Implement Stack using Queues                             [Easy]
https://leetcode.com/problems/implement-stack-using-queues/
Topic: 07 · Queue / Deque
================================================================================

PROBLEM
-------
Implement a last-in-first-out (LIFO) stack using only queues. The
implemented stack should support all the functions of a normal stack
(`push`, `top`, `pop`, and `empty`), using only standard queue operations
(push to back, peek/pop from front, size, is-empty).

    void push(int x)     Pushes element x to the top of the stack.
    int pop()              Removes the element on the top of the stack and
                           returns it.
    int top()               Returns the element on the top of the stack.
    boolean empty()          Returns true if the stack is empty, false otherwise.


EXAMPLES
--------
Example 1:
    Input:
        ["MyStack", "push", "push", "top", "pop", "empty"]
        [[], [1], [2], [], [], []]
    Output:
        [null, null, null, 2, 2, false]
    Explanation:
        MyStack myStack = new MyStack();
        myStack.push(1);
        myStack.push(2);
        myStack.top();   // return 2
        myStack.pop();   // return 2
        myStack.empty(); // return false


CONSTRAINTS
-----------
    1 <= x <= 9
    At most 100 calls will be made to push, pop, top, and empty.
    All the calls to pop and top are valid.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is the mirror image of problem 001. There you built FIFO from LIFO
primitives; here you build LIFO from FIFO primitives. The trick is
different in shape, and — this is the point of doing both — the EXPENSIVE
operation moves to the opposite end.

A queue only lets you add to the back and remove from the front. To make
the MOST RECENTLY pushed element come out FIRST (LIFO), you can push the
new element, then rotate everyone who was already in the queue around it so
the new element ends up at the FRONT:

    from collections import deque
    q = deque()

    def push(x):
        q.append(x)                     # add to the back, as normal
        for _ in range(len(q) - 1):     # rotate all OLDER elements around it
            q.append(q.popleft())

    def pop():
        return q.popleft()              # front is always the most recent push

Unlike problem 001, there is no "only when needed" optimization available
here — every single push() must rotate, because a stack read (top/pop) has
to be O(1) and correct immediately, with no lazy deferral possible (there's
only ever one queue's worth of state, and you can't tell in advance which
future pushes will happen before the next pop).


WHAT TO THINK ABOUT
--------------------
1. Trace push(1), push(2), push(3) by hand: what does the queue look like
   after each push, including the rotation step?

2. Why must ALL of the older elements rotate around the new one, every
   single push — why can't this be made lazy/amortized the way problem
   001's dequeue was?

3. What is the time complexity of push() here, in terms of the CURRENT
   size of the stack? What is pop()'s complexity?

4. Compare this problem's cost profile to problem 001's. Which operation is
   "free" here that was expensive there, and vice versa? Is there a way to
   make BOTH push and pop O(1) using only queue primitives?

5. Two-queue version: instead of rotating in place, some implementations
   use a second queue as scratch space — push onto queue 2, drain queue 1
   into queue 2, then swap names. Is this asymptotically different from
   the single-queue rotation? (Hint: count total element moves either way.)


PROGRESSIVE HINTS
------------------
Hint 1: Use `collections.deque`. `append` adds to the back; `popleft`
        removes from the front — these are your only allowed primitives.

Hint 2: After appending the new element, the queue looks like
        [old..., new]. You want [new, old...]. A queue only lets you move
        things from front to back, so do that len(q)-1 times.

Hint 3:
    def push(x):
        q.append(x)
        for _ in range(len(q) - 1):
            q.append(q.popleft())

Hint 4: pop() and top() are then trivial: `q.popleft()` and `q[0]`
        respectively — the front is ALWAYS the most recently pushed
        element, by construction.

Hint 5: This costs O(current size) per push, O(1) per pop/top — the exact
        opposite trade-off from problem 001's two-stack queue.


COMPLEXITY TARGET
------------------
    Time:  push O(n), pop O(1), top O(1), empty O(1)   (n = current size)
    Space: O(n)
================================================================================
"""

from collections import deque
from typing import List


class MyStack:
    def __init__(self):
        # YOUR CODE HERE
        pass

    def push(self, x: int) -> None:
        # YOUR CODE HERE
        pass

    def pop(self) -> int:
        # YOUR CODE HERE
        pass

    def top(self) -> int:
        # YOUR CODE HERE
        pass

    def empty(self) -> bool:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 002_implement_stack_using_queues_question.py
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

    s = MyStack()
    s.push(1)
    s.push(2)
    check("top after push(1), push(2)", s.top(), 2)
    check("pop after push(1), push(2)", s.pop(), 2)
    check("empty after one pop", s.empty(), False)
    check("pop remaining", s.pop(), 1)
    check("empty after both popped", s.empty(), True)

    s2 = MyStack()
    for x in (5, 6, 7, 8):
        s2.push(x)
    check("LIFO order", [s2.pop(), s2.pop(), s2.pop(), s2.pop()], [8, 7, 6, 5])

    s3 = MyStack()
    s3.push(1)
    s3.push(2)
    check("pop 2", s3.pop(), 2)
    s3.push(3)
    check("pop 3 (interleaved push mid-drain)", s3.pop(), 3)
    check("pop 1", s3.pop(), 1)
    check("empty at end", s3.empty(), True)

    print(f"\n{passed}/{total} passed")


if __name__ == "__main__":
    run_tests()
