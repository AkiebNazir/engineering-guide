# Topic 07 · Queue / Deque — Python Deep Dive

> A queue answers *"who has been waiting longest?"* — <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr>, first in first out.
> A deque generalises it to *"let me push and pop from either end, both O(1)."*
> This topic sits directly after 06 · Stack (<abbr title="Last-In, First-Out. A method for processing data where the last items entered are the first to be removed, characteristic of stack data structures.">LIFO</abbr>) on purpose: the two
> disciplines are constantly confused under pressure, and half of this guide's
> value is drilling the contrast until reaching for the wrong one becomes
> impossible.

---

## Part 1 · <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr> vs <abbr title="Last-In, First-Out. A method for processing data where the last items entered are the first to be removed, characteristic of stack data structures.">LIFO</abbr> — the contrast topic 06 set up

### 1.0 Two disciplines, one interface shape

Both a stack and a queue support "add one, remove one," and both can be
implemented in ~5 lines. The entire difference is **which end you remove
from**:

```
STACK (topic 06)                 QUEUE (this topic)
  push -> top                      enqueue -> back (tail)
  pop  <- top                      dequeue <- front (head)
  LIFO: Last In, First Out         FIFO: First In, First Out

  push(1) push(2) push(3)          enqueue(1) enqueue(2) enqueue(3)
  pop() -> 3   (most recent)       dequeue() -> 1   (least recent)
  pop() -> 2                       dequeue() -> 2
  pop() -> 1                       dequeue() -> 3
```

```
STACK — one open end, LIFO           QUEUE — two ends, FIFO
                                       front                  back
   |  3  | <- top (push/pop here)     [ 1 ][ 2 ][ 3 ]
   |  2  |                             ^dequeue      ^enqueue
   |  1  |
   +-----+  (closed bottom)
```

**Why the confusion is common:** both are "restricted list access" and both
have a two-word verb pair (push/pop vs enqueue/dequeue) that candidates swap
under interview pressure. The test that never fails: *"which element leaves
next — the one I just added, or the one that's been waiting longest?"* Stack
= just added. Queue = waiting longest.

### 1.1 Where each shows up as a sub-mechanism

- **Stack**: <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> (explicit stack or recursion's call stack), balanced
  brackets, "next greater element" (topic 06's monotonic stack), undo
  history, expression evaluation.
- **Queue**: <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> (level-order traversal — this is THE reason queues matter
  for interviews; every shortest-path-in-unweighted-graph problem is a queue
  underneath), rate limiters / sliding time windows (003 here), task
  scheduling, producer-consumer buffering, and — the deque generalisation —
  monotonic-window problems where you need O(1) access to BOTH ends (006
  here, and LC 239 from topic 03).

If a problem says "shortest path" or "level by level" or "minimum number of
steps," think queue/<abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> before anything else, the way "next greater/smaller"
should trigger a monotonic stack.

---

## Part 2 · Implementing One With The Other (001, 002)

### 2.0 Two stacks make a queue (001, LC 232) — the amortized argument

A stack only gives you <abbr title="Last-In, First-Out. A method for processing data where the last items entered are the first to be removed, characteristic of stack data structures.">LIFO</abbr> access, but two of them, cooperating, can
simulate <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr>. The idea: use one stack to receive new elements (`in_stack`),
and a second to serve them out in reversed — i.e. <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr> — order (`out_stack`).

```arch
%% caption: Every element moves from the in-stack to the out-stack at most once, so dequeue is O(1) amortized.
grid 140x100
node p "enqueue x" at 0,0 shape=pill
node in "in-stack" at 1,0
node out "out-stack" at 3,0 color=amber
node pop "Dequeue or peek" at 4,0 color=green sub="top of the out-stack"
p -> in
in -> out : "out-stack empty? move ALL over, reversing order"
out -> pop
```


```python
in_stack, out_stack = [], []

def enqueue(x):
    in_stack.append(x)                    # always O(1): just push

def dequeue():
    if not out_stack:                     # only refill when out_stack is EMPTY
        while in_stack:
            out_stack.append(in_stack.pop())
    return out_stack.pop()
```

Reversing a stack by popping it onto another stack **reverses the order** —
that's the entire trick. `in_stack` accumulates in arrival order top-down;
transferring it onto `out_stack` flips it so the OLDEST element ends up on
top of `out_stack`, ready to pop first.

```
enqueue(1) enqueue(2) enqueue(3):
    in_stack  = [1, 2, 3]   (3 on top — most recent)
    out_stack = []

dequeue() — out_stack is empty, so transfer ALL of in_stack:
    pop 3 -> push to out       out_stack = [3]
    pop 2 -> push to out       out_stack = [3, 2]
    pop 1 -> push to out       out_stack = [3, 2, 1]   (1 now on top!)
    in_stack = []
    pop out_stack -> 1  ✓ (the oldest element, correctly FIFO)

dequeue() again — out_stack is NOT empty, skip the transfer:
    pop out_stack -> 2  ✓   (O(1), no transfer needed)
```

**The amortization argument** (same family as topic 03's monotone-pointer
argument and topic 06's monotonic-stack argument, restated for this shape):

> Each element is pushed onto `in_stack` once, popped off `in_stack` **at
> most once**, and pushed onto `out_stack` **at most once**, and popped off
> `out_stack` **at most once**. That's at most 4 stack operations per
> element over its entire lifetime, no matter how the enqueue/dequeue calls
> are interleaved. So n operations cost O(n) total, i.e. **O(1) amortized
> per operation** — even though any INDIVIDUAL dequeue that triggers a full
> transfer costs O(current size of in_stack) in that one call.

The key phrase for an interview: *"the expensive transfer only happens when
`out_stack` is empty, and once it happens, every element it moved won't be
moved again — so the total work across all calls is bounded by 4n, not
n² ."* Contrast with a naive "shift everything on every dequeue" queue,
which really is O(n) per call, O(n²) total — 001's solution benchmarks this
live.

### 2.1 Two queues make a stack (002, LC 225) — the mirror trick

The mirror problem needs the opposite: simulate <abbr title="Last-In, First-Out. A method for processing data where the last items entered are the first to be removed, characteristic of stack data structures.">LIFO</abbr> (most-recently-added
comes out first) using only <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr> primitives. Python's `collections.deque`
gives O(1) `popleft`, so "two queues" is usually written as one queue plus a
rotation trick — push a new element, then rotate the queue so the new
element is at the front:

```python
from collections import deque

q = deque()

def push(x):
    q.append(x)                       # add to the back, as usual
    for _ in range(len(q) - 1):       # rotate everyone that was already
        q.append(q.popleft())         # there around, so x ends up in FRONT

def pop():
    return q.popleft()                # front is always the most-recently pushed
```

```
push(1):  q=[1]                      rotate 0 times -> q=[1]
push(2):  q=[1,2]                    rotate 1 time  -> pop 1,push -> q=[2,1]
push(3):  q=[2,1,3]                  rotate 2 times -> q=[1,3,2] -> q=[3,2,1]
pop() -> 3  ✓  (LIFO: most recent out first)
```

**Cost trade-off, and why this is the honest opposite of 001:** here `push`
is the expensive operation, O(current size), because every push rotates the
whole queue; `pop`/`top` are O(1). In 001, `enqueue` is O(1) and `dequeue` is
the one that's occasionally expensive but amortized O(1). **There is no way
to make BOTH operations worst-case O(1) using only the other structure's
primitives — one direction always has to pay** (either the transfer in 001,
amortized away, or the rotation in 002, paid every single push). Say this
trade-off out loud; it's a common follow-up (see 002's file).

---

## Part 3 · Circular Buffers (004, 005) — beating `list.pop(0)`

### 3.0 Why a plain Python list is the wrong container for a queue

```python
q = []
q.append(x)          # O(1) amortized — fine
q.pop(0)              # O(n) — shifts EVERY remaining element left by one
```

`list.pop(0)` is O(n) because a Python list is a contiguous array under the
hood — removing index 0 means memmove-ing everything after it. Do this in a
loop of n dequeues and you've built an O(n²) queue by accident. This is
exactly topic 03/04's "hidden quadratic" trap, applied to queues. **The
runtime demo in 004's solution file measures this directly** — see the
numbers there rather than trusting this paragraph.

### 3.1 The fixed-size circular array

A **circular buffer** (ring buffer) is a fixed-size array plus two indices,
`head` (next slot to dequeue from) and `tail` (next slot to enqueue into),
both wrapping around with modulo when they hit the array's end:

```arch
%% caption: Indices wrap with (i + 1) % capacity, so nothing is ever shifted: O(1) enqueue and dequeue, unlike list.pop(0).
route straight
grid 80x80
node s0 "slot 0" at 3,0 shape=circle color=blue
node s1 "slot 1" at 4.5,1 shape=circle color=blue
node s2 "slot 2" at 4,2.5 shape=circle color=blue
node s3 "slot 3" at 2,2.5 shape=circle color=blue
node s4 "slot 4" at 1.5,1 shape=circle color=blue
node h "head" at 6.5,1 color=green sub="next to dequeue"
node t "tail" at 0,1 color=amber sub="next free slot"
s0 -> s1 -> s2 -> s3 -> s4 -> s0
h ..> s1
t ..> s4
```


```python
class CircularQueue:
    def __init__(self, k):
        self.buf = [0] * k
        self.head = 0
        self.size = 0
        self.cap = k

    def enqueue(self, x):
        if self.size == self.cap:
            return False
        tail = (self.head + self.size) % self.cap    # next free slot
        self.buf[tail] = x
        self.size += 1
        return True

    def dequeue(self):
        if self.size == 0:
            return False
        self.head = (self.head + 1) % self.cap        # advance, DON'T shift
        self.size -= 1
        return True
```

```
cap = 4, buf = [_, _, _, _]

enqueue(1): head=0 size=0 -> tail=(0+0)%4=0   buf=[1,_,_,_]  size=1
enqueue(2): tail=(0+1)%4=1                     buf=[1,2,_,_]  size=2
enqueue(3): tail=(0+2)%4=2                     buf=[1,2,3,_]  size=3
dequeue():  head=(0+1)%4=1                     buf=[1,2,3,_]  size=2  (1 abandoned, not erased)
enqueue(4): tail=(1+2)%4=3                     buf=[1,2,3,4]  size=3
enqueue(5): tail=(1+3)%4=0  -> WRITES OVER slot 0! this is the WRAP.
                                                buf=[5,2,3,4]  size=4
            (slot 0 held the already-dequeued '1' — safe to overwrite)
```

The picture that matters: `head` and `tail` chase each other around the
array like hands on a clock. Nothing ever shifts — dequeue is a single
pointer increment (`% cap`), O(1) **always**, not amortized. That's the
whole payoff versus `list.pop(0)`.

Why not just use a Python list and let it grow? Because 004/005 specify a
**fixed capacity** (LC 622/641 are literally "design a queue that holds at
most k elements") — the circular array is the natural fit precisely because
capacity is bounded and known up front. When capacity is unbounded, reach
for `collections.deque` instead (§4).

### 3.2 The deque flavor (005, LC 641) — circular buffer, both ends

A circular *deque* needs `enqueueFront`/`enqueueRear` and
`dequeueFront`/`dequeueRear`, all O(1). Same ring buffer, but now `head` can
also move **backward** (mod `cap`, so `-1 % cap` wraps to `cap - 1` — Python
handles this natively, see topic 04 §1.5 on Python's sign-correct `%`):

```python
def enqueueFront(self, x):
    self.head = (self.head - 1) % self.cap    # Python: already wraps correctly
    self.buf[self.head] = x
    self.size += 1
```

This is the array-backed twin of `collections.deque` itself (§4) — same
capability, fixed capacity instead of dynamic.

---

## Part 4 · `collections.deque` — the standard-library payoff

Python's built-in `deque` (double-ended queue) is a doubly-linked list of
fixed-size blocks. It gives O(1) operations at **both** ends:

```python
from collections import deque
dq = deque()
dq.append(x)        # O(1) — add to right/back
dq.appendleft(x)     # O(1) — add to left/front
dq.pop()              # O(1) — remove from right/back
dq.popleft()          # O(1) — remove from left/front
dq[0]; dq[-1]          # O(1) — peek either end
dq[len(dq)//2]          # O(n) — NOT random access; it's block-linked, not flat array
```

Compare against a plain `list` used the same way:

```
list.insert(0, x)    O(n)   — shifts everything right
list.pop(0)            O(n)   — shifts everything left
list.append(x)          O(1) amortized
list.pop()                O(1)
```

A `list` is only cheap at the **right** end. A `deque` is cheap at **both**.
**This is the single-sentence reason `deque` exists and the reason "use a
deque, not a list, for a queue" is standard advice** — see the measured
benchmark in the standard-library section of 003's solution file for actual
numbers on this machine (never trust the folklore number unmeasured).

`deque` also takes an optional `maxlen` — a **fixed-size sliding window**
built in: pushing past `maxlen` silently drops from the opposite end. This
is exactly what 003 (Number of Recent Calls) can use, and it's worth
knowing as an alternative to manual eviction.

---

## Part 5 · <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr> Sliding Window (003, LC 933)

"Number of Recent Calls" asks: given a stream of timestamps, how many calls
occurred in the last 3000ms? This is a queue used as a **counting window**:
every call is enqueued, and before answering, expire (dequeue) everything
older than `t - 3000` from the front. Because timestamps arrive in
non-decreasing order, the front of the queue is always the oldest, and the
eviction loop is monotone — the exact same amortized argument as topic 03's
sliding window (§1.1 there): each timestamp is enqueued once and dequeued at
most once, so total work across all calls is O(n), not O(n) per call.

```
queue = []                                 # deque
ping(1): queue=[1]                          count=1
ping(100): queue=[1,100]                    count=2
ping(3001): evict while front < 3001-3000=1 -> nothing evicted (1 == 1, kept)
             queue=[1,100,3001]              count=3
ping(3002): evict while front < 3002-3000=2 -> evict 1  queue=[100,3001,3002]
             count=3
```

This is the <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr>-window twin of topic 03's variable window — same "expire
from the front while invalid" shape, except the container is a real queue
because you need the actual front VALUE (a timestamp), not just a count.

---

## Part 6 · The Monotonic Deque — Shortest Subarray with Sum ≥ K (006, LC 862)

This is the hard problem, and it is a direct callback to two earlier
topics: topic 03's guide names LC 862 explicitly as **the trap** where
sliding window looks applicable and is not; topic 04 supplies the tool
(prefix sums) that makes the problem tractable at all. This section
connects both.

### 6.0 Why sliding window fails here

Topic 03 §1.2: a window is only legal when validity is monotone under
shrink/grow. "Sum ≥ K" is upward-closed **only when all values are
non-negative** — growing the window can only grow the sum, so a broken
window can only be fixed by growing, never by an ambiguous choice. LC 862
allows `nums[i]` as low as `-10^5`. With negatives in play, growing the
window can make the sum go UP or DOWN, so there is no principled rule for
"should `l` advance?" — the same argument topic 03 §1.2 and topic 04 §1.1
both make, restated for the *shortest*-window direction this time (topic 04
made it for "does a subarray sum to exactly K" using prefix sum + hashmap;
here the question is an inequality over the shortest LENGTH, which needs one
more idea beyond a hashmap).

### 6.1 Prefix sums turn it into a search over the prefix array

Same setup as topic 04:

```
prefix[0] = 0
prefix[i] = nums[0] + ... + nums[i-1]

sum(nums[l..r]) = prefix[r+1] - prefix[l] >= K
              <=>  prefix[r+1] - K >= prefix[l]
```

For each right end `r+1`, you want the LARGEST `l < r+1` such that
`prefix[l] <= prefix[r+1] - K` — the closer `l` is to `r+1`, the shorter the
subarray. This is a search, not a plain lookup (unlike topic 04's "does an
exact value exist"), because you want the best `l` satisfying an
INEQUALITY, and there can be many valid `l`'s.

### 6.2 Why the answer needs a monotonic deque, not a sorted structure per se

The brute way to search "largest valid `l`" would be a sorted structure
over all previously-seen prefixes (e.g. binary search into a sorted list)
— O(n log n). The deque gets it to O(n) by discarding candidates that can
**never be useful again**, the same "dominated, so drop it forever" argument
as topic 03 §1.8's monotonic deque for window-max:

**Invariant:** maintain a deque of INDICES `i` with `prefix[i]` strictly
increasing left to right.

- **Front pruning (answers get shorter, never come back):** once
  `prefix[r+1] - prefix[dq[0]] >= K`, that front index is a valid left
  endpoint — record the length, and **pop it from the front permanently**.
  It can never produce a SHORTER answer later (later `r`'s only grow the
  candidate length from that same `l`), so it is done for good.

- **Back pruning (a later, smaller prefix dominates):** before appending
  `r+1`, pop from the back every index `j` with `prefix[j] >= prefix[r+1]`.
  Any future query would prefer `r+1` over `j` — `r+1` is BOTH more recent
  (shorter resulting subarray) AND has a smaller-or-equal prefix (at least
  as easy to satisfy the `>= K` test). `j` is dominated on both axes
  simultaneously, so it can never win again.

```python
from collections import deque

def shortestSubarray(nums, k):
    n = len(nums)
    prefix = [0] * (n + 1)
    for i, x in enumerate(nums):
        prefix[i + 1] = prefix[i] + x

    dq = deque()                       # indices into prefix[], increasing prefix values
    best = n + 1
    for i, p in enumerate(prefix):
        while dq and p - prefix[dq[0]] >= k:
            best = min(best, i - dq.popleft())     # front is DONE, pop permanently
        while dq and prefix[dq[-1]] >= p:
            dq.pop()                                 # back is DOMINATED, drop it
        dq.append(i)
    return best if best <= n else -1
```

Each index enters the deque once and leaves at most once (from either end),
so total deque work is O(n) — same accounting as every monotonic-deque
argument in this curriculum (topic 03 §1.8): "each element pushed once,
popped at most once."

### 6.3 Concrete trace with negatives (proves why negatives break sliding window)

```
nums = [2, -1, 2, -1], k = 3
prefix = [0, 2, 1, 3, 2]         (index 0..4)

i=0 p=0   dq=[]                              dq=[0]
i=1 p=2   front check: 2 - prefix[0]=2-0=2 < 3, no pop
          back check: prefix[0]=0 < 2, no pop            dq=[0,1]
i=2 p=1   front check: 1 - prefix[0]=1-0=1 < 3, no pop
          back check: prefix[1]=2 >= 1 -> pop index 1     dq=[0]
          back check: prefix[0]=0 < 1, no pop             dq=[0,2]
i=3 p=3   front check: 3 - prefix[0]=3-0=3 >= 3 -> len=3-0=3, best=3, popleft
                        dq=[2]; 3 - prefix[2]=3-1=2 < 3, stop
          back check: prefix[2]=1 < 3, no pop              dq=[2,3]
i=4 p=2   front check: 2 - prefix[2]=2-1=1 < 3, no pop
          back check: prefix[3]=3 >= 2 -> pop index 3       dq=[2]
          back check: prefix[2]=1 < 2, no pop                dq=[2,4]

best = 3   (subarray nums[0..2] = [2,-1,2], sum = 3)
```

If you tried a naive sliding window here (`while running_sum >= k: shrink`),
the negative `-1` at index 1 would let the sum dip below K after growing
past it, then rise again — there's no consistent point at which shrinking
`l` is safe forever, exactly the failure topic 03 §1.2 warns about. The
solution file benchmarks the O(n) deque approach against an O(n²) brute
force scan over all subarrays to make the complexity gap concrete.

---

## Part 7 · Pattern Decision Tree

```arch
%% caption: Which queue or deque pattern fits.
grid 290x100
node q "Queue-shaped problem" at 0,0 shape=pill
node a "Plain FIFO, only the two ends matter?" at 0,1 shape=diamond color=amber
node a1 "collections.deque" at 1,1 color=green
node b "Events in a recent time window?" at 0,2 shape=diamond color=amber
node b1 "FIFO deque" at 1,2 color=green sub="pop from the left while expired"
node c "Max or min of a sliding window?" at 0,3 shape=diamond color=amber
node c1 "Monotonic deque" at 1,3 color=green
node d "Negatives allowed, shortest subarray with sum ≥ K?" at 0,4 shape=diamond color=amber
node d1 "Prefix sums + monotonic deque" at 1,4 color=green
q -> a
a -> a1 : "yes"
a -> b : "no"
b -> b1 : "yes"
b -> c : "no"
c -> c1 : "yes"
c -> d : "no"
d -> d1 : "yes"
```


```
1. Do I need "who's been waiting LONGEST" (FIFO) or "who arrived MOST
   RECENTLY" (LIFO)?
       FIFO -> queue/deque, this topic
       LIFO -> stack, topic 06

2. Am I asked to build one discipline using ONLY the other's primitives?
       stack from queues, or queue from stacks (001, 002)
       -> one direction is O(1) always, the other is amortized/O(current
          size) — identify which operation you're allowed to make expensive
          (Part 2).

3. Do I need a FIXED-CAPACITY buffer with wraparound, one end or both?
       one end   -> circular queue (004): head/tail indices, % capacity
       both ends -> circular deque (005): head can move -1 % capacity too

4. Do I just need O(1) push/pop at both ends, capacity unbounded?
       -> collections.deque (Part 4). Never list.insert(0, ...)/list.pop(0)
          in a loop.

5. Is this "expire old entries from the front while a count/window
   condition holds," arrival order already sorted?
       -> FIFO sliding window (003): plain deque, evict from front while
          invalid, same amortized argument as topic 03.

6. Is this "shortest/longest subarray with SUM >= or <= K," and can values
   be NEGATIVE?
       NO (non-negative)  -> sliding window, topic 03 — simpler, use it.
       YES (negatives ok)  -> prefix sums (topic 04) + monotonic deque
                              (006, Part 6). NOT a sliding window — see
                              topic 03's own guide, which names this exact
                              problem as the trap.

7. Do I need the WINDOW MAXIMUM/MINIMUM as elements slide in and out (not a
   sum)?
       -> monotonic deque directly over VALUES, no prefix sum needed —
          this is topic 03 §1.8 / LC 239, a sibling pattern to 006's
          deque-over-prefix-values.
```

---

## Part 8 · Complexity Reference

| Operation | Cost | Note |
|---|---|---|
| `list.append(x)` | O(1) amortized | fine for the "back" |
| `list.pop(0)` | **O(n)** | shifts everything — never in a queue |
| `list.insert(0, x)` | **O(n)** | same problem, other end |
| `deque.append` / `appendleft` | O(1) | block-linked list |
| `deque.pop` / `popleft` | O(1) | both ends |
| `deque[i]`, `i` in the middle | O(n) | not random access |
| Two-stack queue: `enqueue` | O(1) | always |
| Two-stack queue: `dequeue` | O(1) amortized | occasional O(current size) transfer |
| Two-queue stack: `push` | O(current size) | rotation every call |
| Two-queue stack: `pop`/`top` | O(1) | always |
| Circular array enqueue/dequeue | O(1) worst-case | pointer + modulo, no shifting |
| <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr> window evict (003) | O(1) amortized/op | each element enqueued & dequeued once |
| Monotonic deque pass (006) | O(n) | each index pushed once, popped at most once |
| Brute-force shortest-subarray scan | **O(n^2)** | all `(l, r)` pairs, prefix-sum-priced |

Space: O(k) for the fixed-capacity structures (004/005), O(n) for the
prefix array and deque in 006, O(1) extra for 001/002 beyond the two
underlying containers holding up to n elements total.

---

## Part 9 · Common Mistakes Across This Topic

1. Confusing which end is "front" — dequeuing from the wrong side silently
   turns a queue into a stack and every test still "runs," it just returns
   wrong answers on anything longer than 1 element.
2. Using `list.pop(0)` for a queue instead of `collections.deque.popleft()`
   — technically correct, quadratic in practice; see the measured
   benchmark in 004/003.
3. In the two-stack queue (001): refilling `out_stack` from `in_stack` even
   when `out_stack` is non-empty. This still produces a correct answer for
   the CURRENT call but destroys the amortization argument — you'd be
   paying the transfer cost far more often than necessary.
4. In the circular array (004/005): computing the next `tail`/`head` with
   plain `+1` instead of `(x + 1) % cap`, so the index runs off the end of
   the array instead of wrapping.
5. In the circular array: conflating "empty" and "full" when `head == tail`
   — both states can produce that condition. Track an explicit `size`
   counter (as this guide does) rather than trying to distinguish empty
   from full using indices alone.
6. Reaching for a sliding window on "shortest/longest subarray with sum
   >= K" without checking whether negatives are allowed (006). If they
   are, this topic's monotonic deque over prefix sums is the tool, not
   topic 03's window.
7. In the monotonic deque (006): forgetting the FRONT pop must happen in a
   `while`, not an `if` — multiple valid left endpoints can be resolved at
   the same `r` when several early prefixes all satisfy the `>= K` test at
   once (in practice this happens after several bunched increases).
8. In the monotonic deque (006): popping the back with `>` instead of
   `>=`. Two equal prefix values both being kept wastes a later, better
   (more recent) match — dedupe with `>=` so ties always favor the newer
   index.

---

## Part 10 · The Progression in This Folder

```
  001  LC 232  Implement Queue using Stacks    two stacks, amortized O(1) dequeue
  002  LC 225  Implement Stack using Queues    the mirror trick, O(current size) push
  003  LC 933  Number of Recent Calls          FIFO sliding window, deque as a count
  004  LC 622  Design Circular Queue           fixed array + head/tail, % wraparound
  005  LC 641  Design Circular Deque           004 generalised to both ends
  006  LC 862  Shortest Subarray Sum >= K      prefix sums (topic 04) + monotonic deque
```

001 → 002 are the amortization pair (whichever operation you make expensive,
the other becomes free — there's no way to make both O(1) worst-case using
only the mirror structure's primitives). 003 → 004 → 005 build up the
container mechanics from "just use a deque" to "build the ring buffer
yourself." 006 is the capstone: it needs topic 04's prefix sums AND this
topic's monotonic-deque discipline (topic 03 §1.8's sibling) at once, and it
is explicitly the trap topic 03's own guide warns about.

---

<!-- block:07_py_1_practice -->
## Part 11 · Queues in Practice: <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> Templates, 0-1 <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>, Thread Queues and Ring Variants

The folder's problems are *designs* of queues. Real interview problems mostly *use* one — and the queue is
almost always doing one of four jobs. Every snippet was run against known answers while writing this section.

```arch
%% caption: The four jobs a queue does in interviews. The container is the same deque each time; what changes is what you put in it and when you mark things visited.
grid 180x100
node q "Why is there a queue?" at 1,0 shape=pill
node a "What does FIFO buy you?" at 1,1 shape=diamond color=amber
node b "BFS" at 0,3 color=green w=165 sub="shortest path in an unweighted graph or grid"
node c "FIFO window" at 1,3 color=green w=165 sub="recent calls, rate limiter, logs"
node d "0-1 BFS" at 2,3 color=amber w=165 sub="deque, push 0-cost neighbours to the FRONT"
node e "Producer / consumer" at 3,3 color=green w=165 sub="a blocking, bounded queue"
q -> a
a:L -> b:T : "process by distance / level"
a:B -> c:T : "process oldest first, forget the old"
a:R -> e:T : "hand work between threads"
a:R -> d:T : "0/1 edge weights"
```

### 11.1 The <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> template — and the one rule that matters

<abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> visits nodes in order of distance from the source *because* the queue is <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr>: everything at distance `d` is dequeued
before anything at `d + 1`. **Mark a node visited when you ENQUEUE it, not when you dequeue it** — otherwise the same
node can be enqueued many times before its first dequeue, and the running time (and the queue) blows up.

```python
def shortest_path(grid):                         # 0 = open, 1 = wall, 4 directions, top-left to bottom-right
    n = len(grid)
    if grid[0][0] or grid[-1][-1]: return -1
    q, seen = deque([(0, 0, 1)]), {(0, 0)}        # (row, col, distance so far)
    while q:
        r, c, d = q.popleft()
        if (r, c) == (n - 1, n - 1): return d
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and not grid[nr][nc] and (nr, nc) not in seen:
                seen.add((nr, nc))                # mark on ENQUEUE
                q.append((nr, nc, d + 1))
    return -1                                      # [[0,0,0],[1,1,0],[1,1,0]] -> 5     [[0,1],[1,0]] -> -1
```

Two variants you need: carry the distance *in the queue entry* (above), or process **level by level** with
`for _ in range(len(q))` when you only need the number of levels. **Multi-source <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>** (Rotting Oranges) starts with
*every* source already in the queue — the "time until everything is reached" is then the number of levels:

```python
q = deque(all_rotten); minutes = 0
while q and fresh:
    for _ in range(len(q)):                        # freeze the size: one level = one minute
        r, c = q.popleft()
        ...                                        # rot the neighbours, fresh -= 1, enqueue them
    minutes += 1
return minutes if fresh == 0 else -1               # [[2,1,1],[1,1,0],[0,1,1]] -> 4    [[2,1,1],[0,1,1],[1,0,1]] -> -1
```

### 11.2 0-1 <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>: a deque makes Dijkstra unnecessary for {0, 1} weights

When every edge costs 0 or 1, you do not need a priority queue. Push a **0-cost** neighbour to the **front** (it is at
the same distance as the node you are on) and a **1-cost** neighbour to the **back**. The deque stays sorted by
distance, so it acts as a heap that only ever holds two distinct values — O(V + E) instead of O(E log V).

```python
def zero_one_bfs(n, edges, src):                  # edges: (u, v, w), w in {0, 1}
    adj = [[] for _ in range(n)]
    for u, v, w in edges: adj[u].append((v, w)); adj[v].append((u, w))
    dist = [inf] * n; dist[src] = 0; dq = deque([src])
    while dq:
        u = dq.popleft()
        for v, w in adj[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                (dq.appendleft if w == 0 else dq.append)(v)
    return dist        # edges (0,1,1)(1,2,0)(0,3,1)(3,4,0)(2,4,1) -> [0, 1, 1, 1, 1]
```

This is why the topic's deque matters beyond design questions: it is the workhorse of "minimum cost to make a valid
path" grid problems (topic 15, Minimum Cost to Make at Least One Valid Path).

### 11.3 Rotation and round-robin

`deque.rotate(n)` shifts the whole deque in O(k) with no element-by-element loop — the natural tool for round-robin
scheduling and the Josephus problem (every `k`-th person leaves the circle):

```python
dq = deque(range(1, n + 1))
while len(dq) > 1:
    dq.rotate(-(k - 1)); dq.popleft()          # josephus(7, 3) -> 4     josephus(5, 2) -> 3
```

### 11.4 A queue with O(1) minimum

Keep a second deque of *candidates*: on `push(x)`, pop from its back everything **greater** than `x` (they can never be
the minimum while `x` is in the queue), then append `x`. On `pop`, remove the front of the candidate deque only if it
is the element leaving. The front of the candidate deque is always the minimum — the same monotonic-deque invariant as
Part 6, exposed as a data structure. (Two stacks with a running minimum each achieve the same.)

### 11.5 A queue *between threads* is a different tool

`collections.deque` is fast and its `append`/`popleft` are atomic under the <abbr title="Global Interpreter Lock. A mutex that protects access to Python objects, preventing multiple threads from executing Python bytecodes at once.">GIL</abbr>, but it never **blocks** and has no
notion of "full". A producer/consumer pipeline wants `queue.Queue`: `put` blocks when the queue is full
(**backpressure** — a fast producer is slowed instead of exhausting memory) and `get` blocks when it is empty.

```python
q = queue.Queue(maxsize=2)
def consumer():
    while True:
        item = q.get()
        if item is None: q.task_done(); break     # a sentinel tells the consumer to stop
        handle(item); q.task_done()
threading.Thread(target=consumer).start()
for i in range(5): q.put(i)                         # blocks when 2 items are waiting
q.put(None); q.join()                                # join() waits until every item is task_done()
```

`queue.LifoQueue` is the thread-safe stack and `queue.PriorityQueue` the thread-safe heap. Across processes use
`multiprocessing.Queue`; in `asyncio` use `asyncio.Queue` (the same <abbr title="Application Programming Interface">API</abbr>, awaitable).

### 11.6 Two kinds of "full"

A ring buffer must decide what a *full* buffer does. **Reject** (Design Circular Queue: `enQueue` returns `False`) is a
bounded queue. **Overwrite the oldest** is a *recency buffer* — the last N log lines, the last N readings — and Python
gives it to you for free:

```python
d = deque(maxlen=3)
for i in range(5): d.append(i)
list(d)              # [2, 3, 4] — the two oldest were dropped silently
```

### 11.7 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Why is <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> shortest-path correct?" | <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr> order means all nodes at distance `d` leave the queue before any at `d + 1`, so the first time a node is *reached* is by a shortest path (unweighted edges only). |
| "Weighted edges?" | 0/1 → 0-1 <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>; arbitrary non-negative → Dijkstra with a heap (topic 15). |
| "How would you do it from both ends?" | Bidirectional <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>: expand the smaller frontier each round — roughly the square root of the states. |
| "Memory is tight." | Store visited as a bitmap/array not a set; process level by level and drop old levels. |
| "The queue must never grow without bound." | Bound it (`maxsize`) and choose: block the producer, reject, or overwrite the oldest. |
| "Priority instead of arrival order." | A heap, not a queue (topic 12). |
| "Is `collections.deque` thread-safe?" | Single `append`/`popleft` are; a check-then-act (`if q: q.popleft()`) is not. Use a lock or `queue.Queue`. |

---
<!-- /block:07_py_1_practice -->

<!-- problem-map:start -->
## Part 12 · Every Problem in This Topic, by Pattern

Six problems, four moves — two "implement one with the other" designs, a <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr> window, two ring buffers and one monotonic deque. Each **Trap** is one the tests in that problem's solution file actually trigger.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Implement Queue using Stacks](PyDSA/07_queue_deque/001_implement_queue_using_stacks_solution.py) <br>LC 232 · Easy | Two stacks, one direction each | Every `push` goes on `in_stack`; when `out_stack` is empty, drain `in_stack` into it — that reverses the order, so the oldest item ends up on top. Amortised O(1). **Trap:** draining on *every* `pop` (O(n) per call); implementing `peek` by popping and forgetting to restore. |
| [002 · Implement Stack using Queues](PyDSA/07_queue_deque/002_implement_stack_using_queues_solution.py) <br>LC 225 · Easy | One queue + rotation | Append the new element, then rotate the `len(q) - 1` older elements behind it so the newest sits at the front, ready for `popleft`. `push` is O(n), `pop` O(1). **Trap:** rotating *before* appending; rotating `len(q)` times (the new element cycles back to the rear). |
| [003 · Number of Recent Calls](PyDSA/07_queue_deque/003_number_of_recent_calls_solution.py) <br>LC 933 · Easy | <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr> sliding count | Enqueue each timestamp and evict from the front while it has aged out of `[t - 3000, t]`; timestamps strictly increase, so the front is always the oldest. **Trap:** `<=` instead of `<` (evicts the inclusive boundary); `if` instead of `while` (stale entries survive a long gap). |
| [004 · Design Circular Queue](PyDSA/07_queue_deque/004_design_circular_queue_solution.py) <br>LC 622 · Medium | Fixed ring buffer | An array, a `head` and an explicit `size`; the insert slot is *derived* as `(head + size) % cap`, never stored. **Trap:** advancing with `+ 1` and no modulo; telling empty from full by `head == tail` alone (identical states). |
| [005 · Design Circular Deque](PyDSA/07_queue_deque/005_design_circular_deque_solution.py) <br>LC 641 · Medium | Ring buffer, both ends | 004 generalised so `head` can move backwards: `insertFront` sets `head = (head - 1) % cap` **before** writing; `deleteLast` just shrinks `size`. **Trap:** writing before moving `head`; assuming a negative `%` is fine in another language (Python's is; Go's and Java's are not). |
| [006 · Shortest Subarray with Sum at Least K](PyDSA/07_queue_deque/006_shortest_subarray_with_sum_at_least_k_solution.py) <br>LC 862 · Hard | Monotonic deque over prefix sums | Negatives break the sliding window, so use prefix sums plus a deque of indices with increasing prefix values: pop the front *while* the sum is big enough, pop the back while it is `>=` the new prefix. **Trap:** reaching for a window (the sign constraint *is* the problem); `if` instead of `while` on the front pop. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] I can state the <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr> vs <abbr title="Last-In, First-Out. A method for processing data where the last items entered are the first to be removed, characteristic of stack data structures.">LIFO</abbr> distinction in one sentence and never
      confuse enqueue/dequeue with push/pop under pressure.
- [ ] I can derive the two-stack queue and state exactly why `dequeue` is
      amortized O(1) — "each element moves at most 4 times total across
      its whole lifetime," not "it's usually fast."
- [ ] I know the two-queue stack pays the opposite way: `push` is O(current
      size), not `pop`, and I can explain why you can't make both free
      using only the mirror structure.
- [ ] I can write a circular buffer's `enqueue`/`dequeue` with `% cap`
      indices and an explicit `size` counter, without conflating empty and
      full.
- [ ] I know `collections.deque` beats a `list` specifically at the LEFT
      end, and `list.pop(0)`/`insert(0, ...)` are O(n) traps.
- [ ] I check the sign constraint before reaching for a sliding window on
      any "subarray sum >= / <= K" problem, and I can name LC 862 as the
      case that fails sliding window and needs prefix sums + a monotonic
      deque instead.
- [ ] I can state the monotonic deque's two pruning rules for 006 from the
      domination argument, not from memory: front pops when a valid answer
      is found (can only get worse later), back pops when a newer index
      has a smaller-or-equal prefix (strictly better on both axes).
</content>
- [ ] Say why a node is marked visited on *enqueue*, not on dequeue, in <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> <!--ca-->
- [ ] Write multi-source <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> and the level-by-level `for _ in range(len(q))` idiom <!--ca-->
- [ ] Explain 0-1 <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>: 0-cost neighbours to the front, 1-cost to the back <!--ca-->
- [ ] Say what `queue.Queue` adds over `collections.deque` (blocking, bounded, backpressure) <!--ca-->
- [ ] Choose reject vs overwrite-oldest for a full ring buffer <!--ca-->
