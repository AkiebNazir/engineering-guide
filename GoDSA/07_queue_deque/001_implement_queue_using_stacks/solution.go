package main

import "fmt"

/*
================================================================================
LeetCode 232 · Implement Queue using Stacks                             [Easy]
https://leetcode.com/problems/implement-queue-using-stacks/
Topic: 07 · Queue / Deque
================================================================================

PROBLEM
-------
Implement a first-in-first-out (FIFO) queue using only two stacks. The
implemented queue should support all the functions of a normal queue
(`push`, `peek`, `pop`, and `empty`), using only standard stack operations
(`push`, `pop`, `peek`/`top`, `is_empty`).

    void push(int x)     Push element x to the back of the queue.
    int pop()             Removes the element from the front of the queue
                          and returns it.
    int peek()             Returns the element at the front of the queue.
    boolean empty()         Returns true if the queue is empty, false otherwise.


EXAMPLES
--------
Example 1:
    Input:
        ["MyQueue", "push", "push", "peek", "pop", "empty"]
        [[], [1], [2], [], [], []]
    Output:
        [null, null, null, 1, 1, false]
    Explanation:
        MyQueue myQueue = new MyQueue();
        myQueue.push(1);  // queue is: [1]
        myQueue.push(2);  // queue is: [1, 2] (leftmost is front)
        myQueue.peek();   // return 1
        myQueue.pop();    // return 1, queue is [2]
        myQueue.empty();  // return false


CONSTRAINTS
-----------
    1 <= x <= 9
    At most 100 calls will be made to push, pop, peek, and empty.
    All the calls to pop and peek are valid (queue is non-empty).


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

You're only allowed to use STACK primitives — push, pop, peek, is-empty,
each strictly last-in-first-out. But you need to produce FIFO behavior.

The insight: popping every element off one stack and pushing each onto a
second stack REVERSES their order. Push 1, 2, 3 onto stack A — 3 ends up on
top. Pop all three off A and push each onto stack B, and now 1 ends up on
top of B — arrival order is restored on B. So B, popped, gives you FIFO
order.

Use two stacks:
    in_stack  — every push() goes straight here, always O(1)
    out_stack — dequeue-facing; only refilled from in_stack when IT is empty

    def push(x):
        in_stack.append(x)

    def pop():
        if not out_stack:
            while in_stack:
                out_stack.append(in_stack.pop())
        return out_stack.pop()

THE KEY RULE: only transfer from in_stack to out_stack when out_stack is
EMPTY. Do it any more often and you throw away the amortized O(1) argument
(see below) — the answer stays correct, but every dequeue would redo work
that a previous dequeue already paid for.


WHAT TO THINK ABOUT
--------------------
1. Why does popping stack A completely and pushing each element onto stack
   B reverse the order? Trace it by hand for [1, 2, 3].

2. Why must the transfer only happen when out_stack is EMPTY, not on every
   pop() call? What breaks (not correctness — cost) if you transfer on
   every pop regardless?

3. What is the worst-case cost of a SINGLE pop() call? What is the total
   cost of n pushes followed by n pops? Are these the same order of growth?
   This is the amortized-vs-worst-case distinction — be ready to state
   which one the interviewer is asking about.

4. peek() needs the front element without removing it. Can you implement it
   by calling pop() then pushing the result back onto out_stack? Is that
   still O(1) amortized?

5. What if push() were the expensive operation instead — could you flip the
   trick (transfer eagerly on push instead of lazily on pop)? What would
   the complexity trade-off become? (This connects directly to 002 — the
   mirror problem — where the "expensive" operation is push instead.)


PROGRESSIVE HINTS
------------------
Hint 1: You need two stacks. One receives everything you push. The other is
        what you actually pop from.

Hint 2: Reversing a stack by moving it onto a second stack, one pop/push at
        a time, restores arrival order on the second stack.

Hint 3:
    def push(x):
        in_stack.append(x)

    def pop():
        if not out_stack:
            while in_stack:
                out_stack.append(in_stack.pop())
        return out_stack.pop()

Hint 4: LAZY transfer — only refill out_stack when it's completely empty.
        This is what makes dequeue amortized O(1) instead of O(n) every
        time.

Hint 5: peek() can reuse pop()'s refill logic: ensure out_stack is
        non-empty (refill if needed), then just look at out_stack[-1]
        without popping it.


COMPLEXITY TARGET
------------------
    Time:  O(1) amortized per operation (push, pop, peek, empty)
    Space: O(n) — n elements live across the two stacks at any time
================================================================================
*/

func main() {
	fmt.Println("Solution for Implement Queue using Stacks not implemented yet")
}
