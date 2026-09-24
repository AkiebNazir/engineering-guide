# Topic 06 · Stack — Python Deep Dive

> A stack answers one structural question extremely well: *"what is the most
> recently opened thing I have not yet closed?"* That is LIFO discipline, and
> it shows up in three disguises in this folder: **matching/nesting**
> (parentheses, generated parentheses), **deferred evaluation** (a running
> computation whose most recent partial result you may need to undo or
> consume), and — the pattern that carries the most weight here — the
> **monotonic stack**, which answers "what is the nearest bigger/smaller
> thing?" for every element in an array, for all elements, in O(n) total.

---

## Part 1 · The Mechanism

### 1.0 LIFO, and why it is the right structure for nesting

A stack supports exactly two O(1) operations: `push` (add to the top) and
`pop` (remove from the top). No random access, no peeking below the top
without popping through everything above it.

```arch
%% caption: Bracket matching: the most recently opened bracket is always the next one that must close.
grid 210x100
node a "Read next char c" at 1,0 shape=pill
node b "Opening bracket?" at 1,1 shape=diamond color=amber
node c "push c" at 0,1
node d "Stack empty, or top does not match c?" at 1,2 shape=diamond color=amber
node f "pop" at 0,2
node e "invalid" at 1,3 color=red
node g "Stack empty?" at 2,1 shape=diamond color=amber
node h "valid" at 2,2 color=green
a -> b
b -> c : "yes"
b -> d : "no"
d -> e : "yes"
d -> f : "no"
c:T -> a:L
f:L -> a:L
a:R -> g:T : "end of input"
g -> h : "yes"
g:R -> e:R : "no"
```


```
push(3); push(5); push(8)      stack: [3, 5, 8]      (top is the right end)
pop() -> 8                      stack: [3, 5]
pop() -> 5                      stack: [3]
```

**Why nesting wants this exact discipline.** In `"([{}])"`, the `]` that
closes must match the `[` that is *most recently still open* — not the
oldest open bracket, the newest. That is precisely "last in, first out."
Any structure that can only see its most recent unclosed item — and forgets
about it the instant it is closed — is a stack by definition. Python's
`list` already has O(1) `append`/`pop` at the end, so it needs no special
container; `list.pop(0)` (the *front*) is the O(n) trap topic 03 already
warned about, and it is just as much a trap here — always push/pop the
**same** end.

### 1.1 The three shapes this topic covers

```
1. MATCHING / NESTING          "does this structure of opens/closes balance?"
   001 Valid Parentheses         push opens, pop-and-check on every close
   006 Generate Parentheses      backtracking with an implicit stack depth
                                  (open count - close count IS the stack depth)

2. DEFERRED EVALUATION          "the most recent partial result may need to
                                  be consumed, replaced, or combined next"
   002 Baseball Game             each new record depends on the last 1-2 scores
   005 Reverse Polish Notation   an operator consumes the two most recent operands

3. MONOTONIC STACK               "for every element, what is the nearest
                                  bigger/smaller element (in position or time)?"
   003 Next Greater Element I    the canonical template, static array
   007 Daily Temperatures        same template, "distance" instead of "value"
   008 Car Fleet                 disguised: monotonic stack over transformed data
   009 Online Stock Span         same template, but the array arrives ONE
                                  element at a time (streaming/online)
   010 Largest Rectangle          same template, stack tracks (height, width)
       in Histogram                pairs instead of raw values — the hardest one

   (004 Min Stack is a fourth, separate idea: O(1) auxiliary state via a
   second stack. See §1.5.)
```

The monotonic stack is worth more of your attention than the other two
combined — it is reused, with small variations, in five of the ten problems.

---

## Part 2 · The Monotonic Stack, Rigorously

### 2.0 What invariant it maintains

A monotonic stack keeps its elements in **strictly increasing** (or
strictly decreasing) order from bottom to top, by refusing to push
anything that would break that order — instead, it pops everything that
would be out of order first.

```arch
%% caption: Next-greater-element: the stack stays in decreasing order, and each pop is the moment an element finds its answer. Every element is pushed once and popped once.
grid 240x100
node a "Next element x" at 1,0 shape=pill
node b "Stack not empty and top is smaller than x?" at 1,1 shape=diamond color=amber
node c "Pop the top" at 2,1 color=amber sub="its next greater element is x"
node d "push x" at 0,1
a -> b
b -> c : "yes"
c:B -> b:B
b -> d : "no"
d:T -> a:L
```


**Decreasing stack** (top is always the *smallest* element still "active")
finds, for every element, the **next greater element to its right**:

```python
def next_greater(nums):
    n = len(nums)
    ans = [-1] * n
    stack = []                      # indices, values strictly DECREASING top-down... 
                                     # ...meaning bottom-to-top the stack DECREASES,
                                     # so nums[stack[-1]] is always the smallest "waiting" value
    for i, x in enumerate(nums):
        while stack and nums[stack[-1]] < x:
            j = stack.pop()
            ans[j] = x               # x is the first thing bigger than nums[j]
        stack.append(i)
    return ans
```

Walk `[2, 1, 2, 4, 3]`:

```
i=0 x=2   stack: []              -> push 0            stack: [0]
i=1 x=1   1 < 2, no pop          -> push 1             stack: [0, 1]
i=2 x=2   nums[1]=1 < 2, pop 1, ans[1]=2
          nums[0]=2, not < 2, stop -> push 2           stack: [0, 2]
i=3 x=4   nums[2]=2 < 4, pop 2, ans[2]=4
          nums[0]=2 < 4, pop 0, ans[0]=4
          stack empty            -> push 3             stack: [3]
i=4 x=3   nums[3]=4, not < 3, stop -> push 4            stack: [3, 4]
end: indices 3,4 never popped -> ans[3]=ans[4]=-1

ans = [4, 2, 4, -1, -1]
```

The stack, at every moment, holds exactly the indices that are **still
waiting** for their next-greater element — in increasing order of value
from bottom to top (the bottom is the largest unresolved value, the top is
the smallest). An element that is popped has *found* its answer; an
element that survives to the end never gets one (`-1`).

### 2.1 Why every element is pushed and popped AT MOST ONCE (the O(n) argument)

This is the same style of amortized argument as topic 03's guide §1.1 for
the sliding-window inner `while` — restate it explicitly, because the code
shape looks identical (an outer `for` with a nested `while`) and the
justification is identical in spirit:

```
    Every index is PUSHED exactly once — once per iteration of the outer for.
    Every index is POPPED at most once — once it is popped, it is gone
    forever; nothing ever gets pushed back onto the stack.

    Total pushes across the whole run  = n   (one per element)
    Total pops across the whole run   <= n   (each index popped at most once)

    The while loop's total iterations across the ENTIRE run, summed over
    every i, is bounded by the total number of pops, which is <= n.
```

Say it in an interview exactly like topic 03's sentence, adapted:

> *"The while loop isn't nested work — every index is pushed once and can
> only be popped once, ever, so across all n iterations of the outer loop
> the inner while fires at most n times TOTAL, not n times per iteration.
> n pushes, at most n pops: O(n)."*

⚠️ The word doing the work is **at most once**. If your monotonic-stack
code ever pushes an index back after popping it, or pops without
permanently resolving that index, the argument breaks and so does the
complexity.

### 2.2 The complexity win, stated plainly

The brute-force version of "next greater element" checks, for every
index, a forward (or backward) scan for the first bigger value:

```python
def next_greater_brute(nums):
    n = len(nums)
    ans = [-1] * n
    for i in range(n):
        for j in range(i + 1, n):
            if nums[j] > nums[i]:
                ans[i] = nums[j]
                break
    return ans
```

That is **O(n²)** worst case (strictly decreasing input: every inner scan
runs to completion). The monotonic stack computes the exact same answer in
**O(n)** — this is the single biggest complexity win in the entire topic,
and it is worth stating explicitly whenever "next greater/smaller" language
appears in a problem: *"this smells like O(n²) pairwise comparison, but a
monotonic stack gets it to O(n) because each element is only ever compared
against — and consumed by — its immediate resolvers, not the whole rest of
the array."* Problem 003's solution file benchmarks this crossover with
real numbers.

### 2.3 The template, and how each problem is the same skeleton with a different payload

```python
stack = []
for i, x in enumerate(data):
    while stack and CONDITION(stack[-1], x):
        item = stack.pop()
        RESOLVE(item, x)          # x is item's answer
    stack.append(i)               # or (i, x), or a transformed tuple
```

| Problem | `data` | `CONDITION` | `RESOLVE` does | Payload on the stack |
|---|---|---|---|---|
| 003 Next Greater Element I | `nums2` | `stack top < x` | record `x` as the next-greater value | index (or value) |
| 007 Daily Temperatures | `temperatures` | `temp[top] < x` | record `i - top` (a **distance**, not the value) | index |
| 009 Online Stock Span | one price at a time | `price[top] <= x` | accumulate a **span/count**, not a single value | (price, span) pairs |
| 008 Car Fleet | cars sorted by position, processed back-to-front | `arrival_time[top] <= x` | merge into the same fleet (or don't) | arrival times — see §2.4 for the disguise |
| 010 Largest Rectangle in Histogram | bar heights | `height[top] >= x` (note: `>=`, decreasing-or-equal) | compute an **area** using `(width) * height[top]` | (index, height) — see §2.5 |

Every row is "push while waiting, pop-and-resolve when the current element
answers the question for something on the stack." The only things that
change are what counts as "resolved" and what value gets recorded.

### 2.4 Car Fleet — the disguise, explained

LC 853 does not mention a stack anywhere in its statement, which is exactly
why it is the problem candidates most often fail to recognize. The reframe:

1. Sort cars by starting **position**, descending (closest to the
   destination first).
2. For each car, compute the **time to reach the destination** assuming no
   traffic ahead: `(target - position) / speed`.
3. Walk the cars from closest-to-target to farthest. Maintain a stack of
   **arrival times** of fleets already formed. A car that would arrive
   **sooner** than the fleet currently in front of it (top of stack) is
   caught by that fleet and merges into it — its own arrival time is
   irrelevant, it now moves at the front car's pace. A car that arrives
   **later** than the fleet ahead can never catch up (it is behind and
   slower-or-equal-effective-speed to arrive), so it forms its own new
   fleet, pushed on top.

The stack invariant is *decreasing arrival time from bottom to top, read in
processing order* — a fleet only ever pushes a new, LARGER arrival time
than everything already resolved in front of it, and a car that would
create a smaller-or-equal arrival time than the fleet ahead simply gets
absorbed (never pushed at all). This is a monotonic stack where the
"resolve" step is "discard the merged car, don't push it" rather than
"pop and record" — the polarity is inverted from 003/007, but the
amortized argument is identical: each car is processed once and pushed at
most once. The **count of fleets** is just the final stack size.

### 2.5 Largest Rectangle in Histogram — the hardest instance

Brute force: for every bar, expand left and right until you find a shorter
bar, tracking the min height along the way — **O(n²)**. The monotonic
stack computes the same answer in **O(n)** by tracking, for every bar, its
**nearest strictly-shorter bar on the left and right** — because the
largest rectangle that uses bar `i` as its limiting (shortest) height
spans exactly from just-after its nearest-shorter-on-the-left to
just-before its nearest-shorter-on-the-right.

The stack holds **indices of bars in strictly increasing height**, bottom
to top. When a new bar `x` is shorter than the top of the stack, the top
bar's rectangle is now fully determined — it cannot extend any further
right (this bar stops it), and its left boundary is whatever is now
exposed below it on the stack (the previous stack entry, or the true start
of the array if the stack is empty):

```python
def largest_rectangle(heights):
    stack = []                       # indices, heights strictly increasing
    best = 0
    for i, h in enumerate(heights + [0]):   # sentinel 0 flushes everything at the end
        while stack and heights[stack[-1]] >= h:
            height = heights[stack.pop()]
            width = i if not stack else i - stack[-1] - 1
            best = max(best, height * width)
        stack.append(i)
    return best
```

The width formula is the part everyone gets wrong under pressure:
`i - stack[-1] - 1` — the popped bar's rectangle spans from one past the
*new* top of the stack (its nearest shorter bar on the left) to one before
`i` (its nearest shorter bar on the right, exclusive). Problem 010's
solution file traces this bar-by-bar with the stack contents drawn at
every step, because this is the trace to have memorized before an
interview.

---

## Part 3 · Min Stack — A Different Pattern (004)

004 is not a monotonic stack — it is a **different** O(1)-per-operation
trick: maintain a **second, parallel stack** that tracks the running
minimum at each depth.

```python
class MinStack:
    def __init__(self):
        self.stack = []
        self.min_stack = []          # min_stack[i] = min of stack[0..i]

    def push(self, val):
        self.stack.append(val)
        m = val if not self.min_stack else min(val, self.min_stack[-1])
        self.min_stack.append(m)     # ALWAYS push, even if val isn't the new min

    def pop(self):
        self.stack.pop()
        self.min_stack.pop()         # pop in lockstep — keeps depths aligned

    def getMin(self):
        return self.min_stack[-1]    # O(1), no scan
```

**The naive alternative** — do not maintain `min_stack` at all, just call
`min(self.stack)` inside `getMin()` — is O(1) *push*/*pop* but **O(n)**
per `getMin()` call, because `min()` rescans the whole stack every time.
For a workload with many interleaved `getMin()` calls, that is O(n) per
query versus O(1) — the same "pay a little extra space to make every
future query O(1)" trade topic 04's prefix sums made, just with a stack
instead of an array. Problem 004's solution file benchmarks this directly
over many calls.

The key correctness point: `min_stack` must be pushed to **on every single
push**, even when the new value is not a new minimum — it stores the
min-so-far *at that depth*, not just new record minimums, so that popping
back to any earlier depth instantly restores the correct historical
minimum. A space-optimized variant (store only deltas, or push to
`min_stack` only on new records paired with a counter) is a legitimate
follow-up (see problem 004's file) but is not needed for correctness at
this quality bar.

---

## Part 4 · Pattern Decision Tree

```arch
%% caption: Which stack pattern fits.
grid 290x100
node q "Stack problem?" at 0,0 shape=pill
node a "Matching or nesting?" at 0,1 shape=diamond color=amber sub="brackets, tags, decode string"
node a1 "Plain stack" at 1,1 color=green sub="push openers, pop on closers"
node b "Next greater or smaller, span, histogram area?" at 0,2 shape=diamond color=amber
node b1 "Monotonic stack" at 1,2 color=green
node c "Min or max in O(1) at any moment?" at 0,3 shape=diamond color=amber
node c1 "Stack of (value, running min)" at 1,3 color=green
node d "Evaluate an expression?" at 0,4 shape=diamond color=amber
node d1 "Operand stack" at 1,4 color=green sub="plus an operator stack"
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
1. Does the problem involve matching/balancing opens against closes
   (brackets, tags, nested structure)?
       YES -> push opens, pop-and-check on every close (001). If GENERATING
              all valid nestings rather than validating one, it's backtracking
              where the running (open_count - close_count) IS the stack depth
              you must never let go negative (006).
       NO  -> continue.

2. Does each new input depend only on the one or two MOST RECENT results,
   consumed/replaced as you go (not looked up by value or index)?
       YES -> deferred evaluation: push results, pop to consume (002, 005).
       NO  -> continue.

3. For EVERY element, do you need the nearest element to its
   left/right that is bigger / smaller / first-to-violate-some-order?
   (Or a running "how far back does this streak go" / "how many
   consecutive weaker things came before this" question?)
       YES -> monotonic stack (§2). Decide increasing vs decreasing by
              asking "am I looking for the next SMALLER or next GREATER?":
                  next GREATER on the right -> decreasing stack, pop while
                      top < current (003, 007)
                  next SMALLER (or >=) on either side, area/width payload
                      -> 010's shape
                  streaming "how many before me are <= me" -> 009's shape
                      (online: one item at a time, no future lookahead)
              If the "next greater/smaller" language isn't explicit, check
              whether the problem reduces to it after a transform (008 —
              sort + per-element derived value, see §2.4).
       NO  -> continue.

4. Do you need O(1) access to an AGGREGATE (min/max) of everything
   currently on the stack, updated as things push and pop?
       YES -> auxiliary parallel stack tracking the running aggregate (004).
       NO  -> plain stack/list is probably enough, or this isn't a stack
              problem at all — reconsider (queue? topic 07).
```

---

## Part 5 · Complexity Reference for This Topic

| Operation | Cost | Note |
|---|---|---|
| `list.append(x)` / `list.pop()` | O(1) amortized | the stack itself |
| `list.pop(0)` / `list.insert(0, x)` | **O(n)** | wrong end — never in a loop |
| Matching/nesting pass (001) | O(n) | one pass, O(1) work per char |
| Monotonic stack pass (003/007/009/010) | **O(n)** total | each index pushed once, popped at most once — §2.1 |
| Brute-force "next greater/smaller" | **O(n²)** | nested scan per element — §2.2 |
| Min Stack `push`/`pop`/`getMin` | O(1) each | parallel min-stack, §3 |
| Min Stack `getMin` via `min(stack)` | **O(n)** per call | the naive alternative — never in a hot loop |
| RPN evaluation (005) | O(n) | one pass, O(1) push/pop/compute per token |
| Generate Parentheses (006) | O(4ⁿ / √n) time, output-bound | Catalan-number count of valid strings |

Space is **O(n)** for the stack itself in every problem here (worst case
every element is pushed before anything pops — e.g. a strictly increasing
array for 003/007, or a strictly increasing histogram for 010).

---

## Part 6 · The Progression in This Folder

```
  001  LC 20   Valid Parentheses              the mechanism, bare: push/pop/match
  002  LC 682  Baseball Game                  deferred eval: consume the last 1-2 results
  003  LC 496  Next Greater Element I         the monotonic-stack TEMPLATE (§2.0-2.3)
  004  LC 155  Min Stack                      different pattern: aux stack, O(1) aggregate
  005  LC 150  Evaluate Reverse Polish Not.   deferred eval: operators consume operands
  006  LC 22   Generate Parentheses           backtracking; stack depth = open - close
  007  LC 739  Daily Temperatures             003's template, payload = distance not value
  008  LC 853  Car Fleet                      003's template, DISGUISED (§2.4)
  009  LC 901  Online Stock Span              003's template, STREAMING/online (§2.3)
  010  LC 84   Largest Rectangle in Histogram 003's template, payload = area (§2.5), hardest
```

003 is the fulcrum of the whole topic: 007, 008, 009, and 010 are all the
same push/pop/resolve skeleton wearing a different payload. Do 003 first,
slowly, until the O(n) argument in §2.1 is automatic, then the rest of the
monotonic-stack problems will feel like variations, not new ideas.

---

<!-- block:06_py_1_more -->
## Part 7 · More Stack Shapes: Four Directions, Reduction, Contexts and Parsing

Part 1's three shapes cover the folder. These recur constantly in interviews; every snippet was run against
LeetCode's own examples while writing this section.

### 7.1 The monotonic stack has four faces — one template

"Nearest bigger/smaller on the left/right" is four questions, and they differ in exactly two decisions: **which way
you scan** and **which comparison pops**.

| I want, for each `i`… | Scan | Pop while `arr[top]` is… | The stack is (bottom → top) | Answer for `i` |
|---|---|---|---|---|
| **next greater** (right) | right → left | `<= arr[i]` | strictly decreasing | top after popping |
| **previous greater** (left) | left → right | `<= arr[i]` | strictly decreasing | top after popping |
| **next smaller** (right) | right → left | `>= arr[i]` | strictly increasing | top after popping |
| **previous smaller** (left) | left → right | `>= arr[i]` | strictly increasing | top after popping |

(The one-pass "resolve on pop" form in Part 2 is the same thing seen from the popped element's side.) Store
**indices**, and read `-1` / `n` when the stack is empty:

```python
def nearest(arr, direction, kind):        # direction 'next'|'prev', kind 'greater'|'smaller'
    n = len(arr); res = [-1] * n if direction == "prev" else [n] * n
    st = []
    for i in (range(n) if direction == "prev" else range(n - 1, -1, -1)):
        if kind == "greater":
            while st and arr[st[-1]] <= arr[i]: st.pop()
        else:
            while st and arr[st[-1]] >= arr[i]: st.pop()
        if st: res[i] = st[-1]
        st.append(i)
    return res
# [2,1,5,6,2,3]: next smaller -> [1, 6, 4, 4, 6, 6]     previous smaller -> [-1, -1, 1, 2, 1, 4]
```

**The duplicate rule.** When you *count* things (Sum of Subarray Minimums — see *The contribution technique* in the Added Problems part), use a **strict** comparison on one
side and a **non-strict** one on the other, so a tie is credited to exactly one element. Strict on both sides counts
`[2, 2]` twice; non-strict on both counts it never.

### 7.2 Circular arrays (LC 503)

Loop over `2n` positions with `i % n`, but **push only during the first pass** — the second pass exists only to resolve
what is still waiting:

```python
def next_greater_circular(nums):
    n = len(nums); res = [-1] * n; st = []
    for i in range(2 * n):
        x = nums[i % n]
        while st and nums[st[-1]] < x:
            res[st.pop()] = x
        if i < n: st.append(i)
    return res           # [1,2,1] -> [2,-1,2]     [1,2,3,4,3] -> [2,3,4,-1,4]
```

### 7.3 Reduction stacks: cancel and carry on

If any adjacent pair can annihilate (`abba` → `aa` → ``), a stack that compares the incoming item with the top does it in
one pass. Remove All Adjacent Duplicates (LC 1047), Backspace String Compare (`#` pops) and Asteroid Collision (topic
06, 012) are all this:

```python
st = []
for ch in s:
    if st and st[-1] == ch: st.pop()
    else:                    st.append(ch)
"".join(st)              # "abbaca" -> "ca"
```

### 7.4 Context stacks: save the state on the way in, restore it on the way out

When brackets carry *state*, push the whole state on `[` / `(` and pop it on the matching close.

**Decode String (LC 394)** — the context is `(text so far, repeat count)`:

```python
def decode_string(s):
    st, cur, num = [], "", 0
    for ch in s:
        if ch.isdigit():   num = num * 10 + int(ch)
        elif ch == "[":    st.append((cur, num)); cur, num = "", 0      # save, start fresh
        elif ch == "]":    prev, k = st.pop(); cur = prev + cur * k      # restore, then expand
        else:              cur += ch
    return cur           # "3[a2[c]]" -> "accaccacc"     "2[abc]3[cd]ef" -> "abcabccdcdcdef"
```

**Basic Calculator (LC 224, with parentheses and unary minus)** — the context is `(result so far, sign in front of the
bracket)`:

```python
def calculate(s):
    res, sign, num, st = 0, 1, 0, []
    for ch in s:
        if ch.isdigit():   num = num * 10 + int(ch)
        elif ch in "+-":   res += sign * num; num = 0; sign = 1 if ch == "+" else -1
        elif ch == "(":    st.append((res, sign)); res, sign = 0, 1
        elif ch == ")":
            res += sign * num; num = 0
            prev, psign = st.pop(); res = prev + psign * res
    return res + sign * num      # "(1+(4+5+2)-3)+(6+8)" -> 23     "2-(5-6)" -> 3
```

Precedence (`*` `/` above `+` `-`, LC 227, topic 06 011) needs the *term* stack from that problem; both together need
the operator stack of the shunting-yard algorithm — say its name, then write the simpler one.

### 7.5 An index stack with a sentinel base (LC 32, LC 71)

Push **indices**, seeded with `-1` as the "wall" before the array. On `)`, pop; if the stack is now empty, the `)` is
unmatched and becomes the new base; otherwise the valid run is `i - st[-1]`:

```python
def longest_valid(s):
    st, best = [-1], 0
    for i, ch in enumerate(s):
        if ch == "(": st.append(i)
        else:
            st.pop()
            if not st: st.append(i)                # unmatched ')' — new base
            else:      best = max(best, i - st[-1])
    return best          # "(()" -> 2     ")()())" -> 4     "" -> 0
```

Simplify Path is the same idea over path components: `..` pops, `.` and empty segments are skipped, everything else
pushes (`"/a/./b/../../c/"` → `"/c"`).

### 7.6 The histogram engine reused: Maximal Rectangle (LC 85)

Turn each row into a histogram of "consecutive 1s ending here" and run Largest Rectangle on it row by row —
O(rows × cols):

```python
heights = [0] * cols
for row in matrix:
    heights = [h + 1 if c == "1" else 0 for h, c in zip(heights, row)]
    best = max(best, largest_rectangle(heights))          # the 4x5 example -> 6
```

### 7.7 The call stack *is* a stack — and Python's is 1000 deep

Every recursive call is a push, every return a pop, and CPython caps the depth (`sys.getrecursionlimit() == 1000`).
`depth(5000)` raises `RecursionError`. The conversion is mechanical: the recursion's *locals* become the elements of an
explicit stack. For a DFS: push the root, then loop `pop → visit → push children` — push the **right** child before the
left to visit left first (topic 10 has the three traversal orders). Raising the limit with `setrecursionlimit` trades a
clean error for a possible interpreter crash; an explicit stack has neither problem.

### 7.8 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Min Stack in O(1) *extra* space." | Store `value - current_min` (or `2*value - min`) instead of a parallel stack; it works, and it is fragile — mention overflow in fixed-width languages. |
| "Max Stack with `popMax`." | Two stacks make `popMax` O(n); a heap with lazy deletion (or a doubly linked list + sorted map) makes every operation O(log n). |
| "Implement a queue with two stacks / a stack with two queues." | Topic 07 — amortised O(1) vs O(n) push. |
| "Do it without recursion." | The explicit stack of 7.7. |
| "What if the input is a stream?" | A monotonic stack is already online (Online Stock Span): one element at a time, no lookahead. |
| "Why is the nested `while` still O(n)?" | Each index is pushed once and popped at most once — Part 2.1. |
| "Thread safety." | `list.append`/`pop` are atomic under the GIL but a check-then-pop is not; use a lock or `queue.LifoQueue`. |

---
<!-- /block:06_py_1_more -->

<!-- problem-map:start -->
## Part 8 · Every Problem in This Topic, by Pattern

Fourteen problems, five moves (matching · deferred evaluation · monotonic stack · auxiliary state · contribution). Each **Trap** is one the tests in that problem's solution file actually trigger.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Valid Parentheses](PyDSA/06_stack/001_valid_parentheses_solution.py) <br>LC 20 · Easy | Matching stack | A close bracket is valid only if it matches the most recent still-open one — LIFO. Push opens; on each close, check the top and pop. **Trap:** comparing bracket *counts* instead of order (`"([)]"`); reading `stack[-1]` on an empty stack. |
| [002 · Baseball Game](PyDSA/06_stack/002_baseball_game_solution.py) <br>LC 682 · Easy | Deferred evaluation | Every record depends on the top one or two entries, and `C` is literally "undo the last push". **Trap:** `+` as "pop two, push sum" (deletes two real scores) instead of *peek* two and push a third; `D` doubling in place instead of pushing a new score. |
| [003 · Next Greater Element I](PyDSA/06_stack/003_next_greater_element_i_solution.py) <br>LC 496 · Easy | Monotonic stack | "Next greater" is a property of `nums2` alone: compute it once with one pass, then look each query up. **Trap:** re-scanning `nums2` per query; `<= x` vs `< x` (harmless here only because the values are distinct). |
| [004 · Min Stack](PyDSA/06_stack/004_min_stack_solution.py) <br>LC 155 · Medium | Auxiliary parallel stack | Keep a second stack holding the running minimum *at each depth*, pushed and popped in lockstep. **Trap:** pushing to `min_stack` only on a new minimum (the stacks desync after a pop); popping one stack but not the other. |
| [005 · Evaluate Reverse Polish Notation](PyDSA/06_stack/005_evaluate_reverse_polish_notation_solution.py) <br>LC 150 · Medium | Operand stack | An operator's two operands are always the two most recent values. **Trap:** popping in the wrong order for `-` and `/` (`b - a`); `a // b` floors — the problem wants `int(a / b)` (truncation toward zero). |
| [006 · Generate Parentheses](PyDSA/06_stack/006_generate_parentheses_solution.py) <br>LC 22 · Medium | Backtracking with implicit depth | `open_count − close_count` *is* the stack depth: place `(` while opens remain, `)` while it would not go negative. **Trap:** forgetting `path.pop()` after the recursive call; `close <= open` instead of `<`. |
| [007 · Daily Temperatures](PyDSA/06_stack/007_daily_temperatures_solution.py) <br>LC 739 · Medium | Monotonic stack (distance) | 003's template with the payload swapped from a value to `i - j`; the stack holds *indices* still waiting for a warmer day. **Trap:** pushing temperatures instead of indices; `<=` instead of `<` (all-equal input catches it). |
| [008 · Car Fleet](PyDSA/06_stack/008_car_fleet_solution.py) <br>LC 853 · Medium | Sort, then monotonic stack | The transform *is* the problem: turn each car into an arrival time, sort by position descending, and a slower car ahead absorbs everyone behind. **Trap:** sorting ascending (plausible wrong answer, no error); `<` instead of `<=` (equal arrival times are one fleet). |
| [009 · Online Stock Span](PyDSA/06_stack/009_online_stock_span_solution.py) <br>LC 901 · Medium | Online stack with span collapsing | "Days back with price `<=` today" is "distance to the previous *strictly greater* price"; store `(price, span)` and absorb spans on pop. **Trap:** pushing bare prices and returning `1 + pops` (`[1,1,1,2,1,3,3]`, not `[1,1,1,2,1,4,6]`); `<` instead of `<=`. |
| [010 · Largest Rectangle in Histogram](PyDSA/06_stack/010_largest_rectangle_in_histogram_solution.py) <br>LC 84 · Hard | Monotonic stack (width) | Every rectangle is capped by its shortest bar; pop on a shorter bar and the width is measured between the two *boundaries*. **Trap:** no sentinel/drain (a strictly increasing histogram returns 0); `width = i - j - 1` using the *popped* index. |
| [011 · Basic Calculator II](PyDSA/06_stack/011_basic_calculator_ii_solution.py) <br>LC 227 · Medium | Term stack | Treat the expression as a sum of signed terms: `+`/`-` push a term, `*`/`/` fold into the top one. **Trap:** `//` (floors; `"14-3/2"` gives 12, not 13); `int(a / b)` on huge operands (float precision). |
| [012 · Asteroid Collision](PyDSA/06_stack/012_asteroid_collision_solution.py) <br>LC 735 · Medium | Collision stack | The only collision is a right-mover on top meeting an incoming left-mover; resolve it in a loop. **Trap:** colliding on *any* sign difference (`[-2, 1]` fly apart); `if` instead of `while` (`[1,2,3,-10]`). |
| [013 · Remove K Digits](PyDSA/06_stack/013_remove_k_digits_solution.py) <br>LC 402 · Medium | Greedy monotonic stack | Pop the top whenever a smaller digit arrives and deletions remain — deleting a "peak" improves a more significant position. **Trap:** forgetting the leftover-`k` chop from the end; forgetting to strip leading zeros (`"10200"`, k=1). |
| [014 · Sum of Subarray Minimums](PyDSA/06_stack/014_sum_of_subarray_minimums_solution.py) <br>LC 907 · Medium | Contribution technique | `arr[i]` is the minimum of `left[i] × right[i]` subarrays, where one side is strict and the other non-strict. **Trap:** strict on both sides counts `[2, 2]` twice (8, not 6); non-strict on both counts it never. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] I can push/pop from the correct end of a Python `list` and explain why
      `pop(0)`/`insert(0, x)` are O(n) traps.
- [ ] I can state the amortized O(n) argument for a monotonic stack's nested
      `while` — "pushed once, popped at most once" — in one sentence, the
      same way topic 03's guide states it for the sliding window.
- [ ] I can state the O(n²) brute force vs O(n) monotonic stack contrast for
      "next greater/smaller element" without hesitating.
- [ ] I can write the next-greater-element template from memory and adapt
      its `CONDITION`/`RESOLVE` for daily temperatures, online stock span,
      and largest rectangle.
- [ ] I can explain the Car Fleet disguise: sort by position, compute
      arrival time, and recognize "later arrival time absorbed by an
      earlier one ahead" as a monotonic-stack merge.
- [ ] I can derive the width formula `i - stack[-1] - 1` for largest
      rectangle from the picture of nearest-shorter-bar boundaries, not
      from memory.
- [ ] I know Min Stack needs a value pushed to the auxiliary stack on
      EVERY push (not just new minimums) and can say why popping breaks
      otherwise.
- [ ] I can tell, from a fresh problem statement, whether it is nesting,
      deferred evaluation, or a monotonic stack — using Part 4's decision
      tree — before writing any code.
- [ ] Fill in the four-directions table (next/previous × greater/smaller) from memory, including the pop comparison <!--ca-->
- [ ] Handle a circular array with a `2n` loop that pushes only in the first pass <!--ca-->
- [ ] Write Decode String or Basic Calculator with a context stack <!--ca-->
- [ ] Convert a recursive DFS into an explicit stack, and say why CPython's 1000-frame limit forces it <!--ca-->

---

## Part 9 · Added Problems (011–014) — four more stack shapes Google likes

Added 16 Sep 2026 from the Google prep plan.

| # | Problem | Shape | The one idea |
|---|---|---|---|
| 011 | Basic Calculator II | deferred evaluation | Stack of signed TERMS: `+`/`-` push, `*`/`/` modify the top; answer = sum. Truncate toward zero, not floor |
| 012 | Asteroid Collision | nesting / cancellation | Collide only when top > 0 > incoming; resolve in a `while`; `while ... else` pushes survivors |
| 013 | Remove K Digits | monotonic stack as GREEDY | Pop a bigger digit when a smaller one arrives (delete the leftmost peak); chop leftovers from the end; strip zeros |
| 014 | Sum of Subarray Minimums | monotonic stack for CONTRIBUTION | Each element is the min of `left * right` subarrays; strict on one side, non-strict on the other |

### The contribution technique (014) deserves its own name

"Sum of f(subarray) over all subarrays" is O(n^2) subarrays. Flip it: for each element, count the
subarrays where it is the answer, then multiply. Previous/next smaller elements (this topic's
monotonic stack) give those counts in O(n). The tie-break is the whole difficulty: strict-both
double-counts `[2,2]` (returns 8, not 6).

The same boundaries power Largest Rectangle (010), Sum of Subarray Ranges (LC 2104), and Maximum
Subarray Min-Product (LC 1856).

### Python trap from 011

`-3 // 2 == -2` (floor). Problems that say "truncate toward zero" need
`q = abs(a) // abs(b); q if same sign else -q`. `int(a / b)` happens to work under 32-bit constraints
because the values fit exactly in a float, and fails for big integers (demonstrated in the file).

### Checklist additions

- [ ] I can evaluate `+ - * /` without parentheses with a stack of terms, and in O(1) space.
- [ ] I can state the Remove K Digits greedy ("delete the leftmost peak") and its three cleanup steps.
- [ ] I can explain the contribution technique and the strict/non-strict tie-break.
