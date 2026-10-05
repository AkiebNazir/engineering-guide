package main

/*
================================================================================
LeetCode 622 · Design Circular Queue                                  [Medium]
https://leetcode.com/problems/design-circular-queue/
Topic: 07 · Queue / Deque
================================================================================

PROBLEM
-------
Design your implementation of a circular queue. A circular queue is a
linear data structure that operates on the FIFO principle, and the last
position is connected back to the first to make a circle. It's also called
"Ring Buffer."

Implement the `MyCircularQueue` class:

    MyCircularQueue(k)      Initializes the object with the size of the
                            queue to be k.
    boolean enQueue(value)   Inserts an element into the circular queue.
                            Returns true if successful.
    boolean deQueue()         Deletes an element from the circular queue.
                            Returns true if successful.
    int Front()                Gets the front item. Returns -1 if the queue
                            is empty.
    int Rear()                  Gets the last item. Returns -1 if the queue
                            is empty.
    boolean isEmpty()             Checks whether the circular queue is empty.
    boolean isFull()                Checks whether the circular queue is full.

You must solve the problem WITHOUT using the built-in queue collection in
your language.


EXAMPLES
--------
Example 1:
    Input:
        ["MyCircularQueue", "enQueue", "enQueue", "enQueue", "enQueue", "Rear", "isFull", "deQueue", "enQueue", "Rear"]
        [[3], [1], [2], [3], [4], [], [], [], [4], []]
    Output:
        [null, true, true, true, false, 3, true, true, true, 4]
    Explanation:
        MyCircularQueue q = new MyCircularQueue(3);
        q.enQueue(1);   // true
        q.enQueue(2);   // true
        q.enQueue(3);   // true
        q.enQueue(4);   // false, queue is full (capacity 3)
        q.Rear();       // 3
        q.isFull();     // true
        q.deQueue();    // true, removes 1
        q.enQueue(4);   // true
        q.Rear();       // 4


CONSTRAINTS
-----------
    1 <= k <= 1000
    0 <= value <= 1000
    At most 3000 calls will be made to enQueue, deQueue, Front, Rear,
    isEmpty, and isFull.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

The problem explicitly forbids the built-in queue collection, which is the
point: you're implementing the ring buffer mechanism directly (topic guide
§3.1). Use a fixed-size array plus two indices:

    head — index of the current FRONT element
    size — how many elements are currently stored (avoids the classic
           "head == tail means empty OR full, which is it?" ambiguity)

    def enQueue(value):
        if size == capacity: return False
        tail = (head + size) % capacity
        buf[tail] = value
        size += 1
        return True

    def deQueue():
        if size == 0: return False
        head = (head + 1) % capacity      # advance, DON'T shift the array
        size -= 1
        return True

The whole point versus a plain Python list: `deQueue` never shifts any
elements — it's a single index increment with a modulo wrap. Compare this
against a list-based queue using `list.pop(0)`, which is O(n) because it
DOES shift everything. The runtime demo below measures this gap directly,
growing n, rather than asserting it.


WHAT TO THINK ABOUT
--------------------
1. Why does tracking an explicit `size` counter avoid ambiguity that
   comparing `head` and `tail` indices alone would create? What two
   distinct states can `head == tail` represent, and how would you tell
   them apart without `size`?

2. Derive the formula for the position to insert into on enQueue, in terms
   of `head`, `size`, and capacity. Why does it need `% capacity`?

3. On deQueue, why is it enough to just advance `head` and decrement
   `size` — you never touch the actual stored value. Is this "deleting"
   the data in any meaningful sense, and does that matter?

4. What is the worst-case time complexity of enQueue/deQueue here, and how
   does it compare to a Python list used as `list.append` + `list.pop(0)`?
   Is the circular array's advantage amortized, or worst-case, every call?

5. Front() and Rear() need to read, not remove. Rear() is trickier than
   Front() — work out the index formula for the last occupied slot, not
   just `head`.


PROGRESSIVE HINTS
------------------
Hint 1: Preallocate `self.buf = [0] * k`. Track `self.head = 0` and
        `self.size = 0` (not a separate `tail` — you can derive it).

Hint 2: enQueue's insertion index: `(self.head + self.size) % k`.

Hint 3: deQueue: `self.head = (self.head + 1) % k`, then `self.size -= 1`.
        No shifting, no data movement.

Hint 4: Front() is just `self.buf[self.head]` (guarded by
        `not self.isEmpty()`). Rear() needs the LAST occupied index:
        `(self.head + self.size - 1) % k`.

Hint 5: isEmpty() is `self.size == 0`; isFull() is `self.size == self.cap`.
        Because you track `size` explicitly, these are unambiguous even
        when `head` and `tail` coincide.


COMPLEXITY TARGET
------------------
    Time:  O(1) for every operation (enQueue, deQueue, Front, Rear,
           isEmpty, isFull) — worst-case, not amortized
    Space: O(k) — the fixed-size backing array
================================================================================
*/

// TODO: Implement the stub
