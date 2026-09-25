# Topic 08 · Linked List — Python Deep Dive

> Every problem in this folder is a variation on one physical fact: a linked
> list trades away O(1) random access (arrays' superpower) for O(1) insertion
> and deletion **anywhere you already hold a reference** (arrays cannot do
> this — inserting in the middle of a Python list is O(n), a full shift).
> Nothing else in this topic is really new algorithmically; slow/fast
> pointers, dummy heads, and reversal are the entire toolbox, recombined.

---

## Part 1 · The Mechanism — Why Linked Lists Exist At All

### 1.0 The trade array people forget to state

```
Array                                  Linked list
-----                                  -----------
a[i]                O(1)               walk from head          O(n)
insert at END        O(1) amortised     insert at a KNOWN node   O(1)
insert in MIDDLE     O(n) — shift       insert at a KNOWN node   O(1)
delete in MIDDLE     O(n) — shift       delete a KNOWN node      O(1)
memory layout        contiguous         scattered, +1 pointer/node
cache behaviour       excellent          poor — pointer chasing
```

An array's `insert(i, x)` is O(n) because every element after `i` must
physically move one slot over — the underlying memory is one contiguous
block, and Python's `list.insert` really does execute that shift in C. A
linked list's node at position `i` doesn't need anyone to move: inserting
means allocating one new node and rewiring **two references**, regardless of
how long the list is — *provided you already have a reference to the node
before the insertion point*. That "provided" is the entire catch, and it's
why linked lists are frequently combined with a hashmap (Part on <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr> below)
to convert "find the node" from O(n) into O(1).

The flip side is real and worth saying out loud in an interview: **no random
access.** `nums[500000]` on a Python list is one C-level pointer arithmetic
step; the 500,000th node of a linked list needs 500,000 `.next` hops. This is
why binary search doesn't work on linked lists even though "the values are
sorted" — you cannot jump to the midpoint in O(1).

### 1.1 What a Python "reference" actually is, and where the pointer analogy holds

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
```

`node.next` in Python holds a **reference** to another `ListNode` object (or
`None`) — under the hood, CPython objects live on the heap and a variable or
attribute holding one is a pointer to that heap object, refcounted. This is
functionally the same mental model as Go's `*ListNode` (see the Go guide,
Part 1.1): "an 8-byte address, no arithmetic, follow-only." Two names can
point at the same node:

```python
a = ListNode(1)
b = a
b.val = 99
a.val    # 99 — a and b are the SAME object, not two copies
```

This is exactly the linked-list mutation model: rewiring `.next` changes what
every reference to that node "sees," because there is only one node in
memory, referenced from possibly many places.

### 1.2 Where the analogy breaks: garbage collection vs. explicit ownership

Python's references are garbage collected — a node becomes unreachable (and
eventually freed) the instant nothing points to it any more, and you never
`free()` anything by hand. This matters less for correctness than for *how
carefully you must think about wiring*:

- In **Go**, an uninitialized `*ListNode` is a real, typed `nil` — dereferencing
  it panics immediately and loudly (see the Go guide, Part 1.2–1.3).
- In **Python**, the equivalent uninitialized reference is `None`, and calling
  `.next` on it raises `AttributeError: 'NoneType' object has no attribute
  'next'` **immediately at the call site** — Python has no Go-style "nil
  receiver that doesn't panic until dereferenced" subtlety (Go Part 1.3);
  every method call in Python is itself an attribute lookup, so `None.next`
  fails the instant you write it, full stop.
- Python's cycle collector specifically exists because **refcounting alone
  cannot free a cycle** — two nodes pointing at each other never hit refcount
  zero on their own. This is invisible for LeetCode-style single-pass
  problems (you rarely build unreachable cycles by accident), but it's the
  reason `del` on an isolated cyclic structure doesn't reclaim it instantly
  the way a linear chain does; the cycle collector runs it down later.

### 1.3 The #1 bug in this entire topic: losing a reference before saving it

```arch
%% caption: Overwrite cur.next before saving it and the rest of the list becomes unreachable.
grid 150x90
group W "Wrong order" color=red
node w1 "cur.next = prev" at 0,0 in W
node w2 "cur = cur.next\n(now points backwards!)" at 1,0 in W color=red
group R "Right order" color=green
node r1 "nxt = cur.next" at 0,1 in R color=green sub="save it first"
node r2 "cur.next = prev" at 1,1 in R
node r3 "prev = cur" at 2,1 in R
node r4 "cur = nxt" at 3,1 in R
w1:R -> w2:L
r1 -> r2 -> r3 -> r4
```


```python
# ✗ WRONG — overwrites .next before the old value is saved anywhere
def reverse_broken(head):
    prev = None
    curr = head
    while curr:
        curr.next = prev      # <-- the rest of the list is GONE. curr.next
                               #     was our only reference to it, and we
                               #     just overwrote it.
        prev = curr
        curr = curr.next      # this now reads prev (just written), not the
                               # real "next" node — curr becomes prev, curr.next
                               # is prev.next, and the walk degenerates
    return prev
```

```python
# ✓ CORRECT — save the reference BEFORE destroying it
def reverse(head):
    prev = None
    curr = head
    while curr:
        nxt = curr.next       # 1. SAVE first — this is the only copy of
                               #    "the rest of the list" that will survive
                               #    the next line
        curr.next = prev      # 2. rewire (destroys the original .next)
        prev = curr            # 3. advance prev
        curr = nxt              # 4. advance curr using the SAVED reference
    return prev
```

A linked list has no index to fall back on if you drop a reference — unlike
an array, where `a[i]` still works even after you overwrite some *other*
variable. Every node beyond the one you're standing on is reachable **only**
through the `.next` pointer you're about to overwrite. Once it's gone, it's
gone: not an exception, not a crash — just silently truncated data, which is
worse, because the code keeps running and produces a *plausible-looking*
wrong answer instead of failing loudly. Problem 001's solution file runs
`reverse_broken` live on a real list and shows exactly what comes out.

---

## Part 2 · The Dummy / Sentinel Head Trick

### 2.1 The bug it prevents

Any operation that might change **which node is first** — delete the head,
insert before the head, merge two lists where one might be empty — forces
special-case branches if you operate on `head` directly:

```python
# ✗ without a dummy — deleting a value that happens to be the head needs
# its own branch, separate from every other position
def remove_elements(head, val):
    while head and head.val == val:      # strip from the FRONT — special case
        head = head.next
    if not head:
        return None
    curr = head
    while curr.next:
        if curr.next.val == val:
            curr.next = curr.next.next
        else:
            curr = curr.next
    return head
```

### 2.2 With a dummy — the special case disappears entirely

```python
def remove_elements(head, val):
    dummy = ListNode(next=head)   # dummy.next is ALWAYS "the real head"
    curr = dummy
    while curr.next:
        if curr.next.val == val:
            curr.next = curr.next.next
        else:
            curr = curr.next
    return dummy.next             # unwrap once, at the very end
```

```
dummy ──► [1] ──► [2] ──► [3] ──► None
  ▲
  curr starts HERE — one step "before" the real list, so deleting the
  real head is now identical to deleting any other node: curr.next = curr.next.next
```

One allocation (`ListNode(next=head)`), zero head-of-list branching anywhere
in the loop body. This is the single highest-leverage idiom in the topic —
reach for it any time an operation might touch, delete, or insert before the
current first node: 002 (merge — either list could be exhausted first), 005
(remove by value — the head itself might match), 009 (remove Nth from end —
the node to remove might be the head), 011 (add two numbers — building a
brand-new result list from nothing).

---

## Part 3 · Two-Pointer Patterns Unique to Linked Lists

Topic 02's two pointers *converge* (start at both ends, move toward each
other) because arrays support backward indexing. Linked lists are
forward-only, so the two useful shapes here are different: pointers moving at
**different speeds**, and pointers moving at the **same speed with a fixed
gap**.

### 3.1 Slow/fast (Floyd's tortoise and hare) — finding the middle (004)

```python
slow = fast = head
while fast and fast.next:
    slow = slow.next
    fast = fast.next.next
return slow          # fast has covered 2x the distance slow has
```

`fast` moves two nodes per step, `slow` moves one. When `fast` falls off the
end (`None` or `.next is None`), `slow` has covered exactly half the
distance — one pass, O(1) space, no need to count the length first (the
"obvious" two-pass alternative: count `n`, then walk `n // 2` steps — this
is O(1) space but two passes instead of one).

### 3.2 Slow/fast for cycle detection (003) — the proof, not just the recipe

```arch
%% caption: Slow moves 1, fast moves 2, and they meet inside the cycle. Restart one pointer at head and move both one step at a time: they meet at the cycle entry.
grid 170x110
node H "head" at 0,0 shape=pill
node E "cycle entry" at 1,0 color=amber
node M "meeting point" at 2,0 color=green
H -> E : "a steps"
E:R -> M:L : "b steps"
M:B -> E:B : "c - b steps (rest of cycle)"
```


```python
slow = fast = head
while fast and fast.next:
    slow = slow.next
    fast = fast.next.next
    if slow is fast:        # IDENTITY, not equality — same node object
        return True
return False
```

**Why they are guaranteed to meet if a cycle exists — the "closing the gap by
one" argument.** Once `slow` enters the cycle, think of the distance between
`fast` and `slow`, measured *forward around the cycle*, as a gap `g` (0 ≤ g <
cycle length). Every step, `slow` advances 1 and `fast` advances 2 — both
moving in the same direction around the same finite loop — so the gap
shrinks by exactly 1 each iteration: `g, g-1, g-2, ..., 1, 0`. It cannot skip
over 0, because it only ever decreases by 1 at a time and the cycle is
finite, so `slow is fast` becomes true in at most (cycle length) more steps.
Contrast this with two runners on an *infinite straight line* at different
speeds — there the gap only grows and they never meet; the cycle being
**finite and closed** is exactly what turns "gap shrinks by 1 forever" into
"gap must hit exactly 0."

If there is **no** cycle, `fast` simply reaches `None` (or a node whose
`.next` is `None`) and the loop condition `fast and fast.next` ends it — no
false positive is possible, because `slow is fast` can only become true
*inside* a shared cycle (two distinct forward-only chains that never
rejoin cannot cross paths, since `fast` is always further along the *same*
path `slow* is on, never a different one).

### 3.3 Fixed-gap two pointers — Nth from the end (009)

```python
dummy = ListNode(next=head)
fast = slow = dummy
for _ in range(n):          # open up a gap of exactly n nodes
    fast = fast.next
while fast.next:            # slide the gap to the end
    fast = fast.next
    slow = slow.next
slow.next = slow.next.next  # slow is now the node BEFORE the one to remove
return dummy.next
```

Unlike 3.1/3.2, both pointers move at the **same speed** — the trick is
opening a fixed head start of `n` nodes for `fast` before the walk begins.
When `fast` reaches the last node, `slow` is exactly `n` nodes behind it,
i.e. sitting right before the node that is `n` from the end. This finds a
target position in **one pass** instead of the "obvious" two-pass approach
(count the length, then walk `length - n` steps) — same O(n) time, but one
walk instead of two, and it generalises (windowed two-pointer gaps show up
again in later topics).

---

## Part 4 · Reversal As a Template

### 4.1 The three-pointer dance (001) — memorise this verbatim

```arch
%% caption: Reversal: every next pointer is flipped once, in a single pass, O(1) extra space.
route straight
grid 90x100
group B "before" color=slate
node a1 "1" at 0,0 in B shape=circle color=blue
node a2 "2" at 1,0 in B shape=circle color=blue
node a3 "3" at 2,0 in B shape=circle color=blue
node a4 "None" at 3,0 in B shape=pill
group A "after" color=green
node b3 "3" at 0,1 in A shape=circle color=green
node b2 "2" at 1,1 in A shape=circle color=green
node b1 "1" at 2,1 in A shape=circle color=green
node b0 "None" at 3,1 in A shape=pill
a1 -> a2 -> a3 -> a4
b3 -> b2 -> b1 -> b0
a1 ==> b3
```


```python
def reverse(head):
    prev = None
    curr = head
    while curr:
        nxt = curr.next     # 1. SAVE
        curr.next = prev    # 2. REWIRE
        prev = curr          # 3. ADVANCE prev
        curr = nxt            # 4. ADVANCE curr
    return prev
```

```
Before:  None <- prev   curr
                          [1] -> [2] -> [3] -> None

step 1:  nxt = [2]
step 2:  [1].next = None      prev  curr
         None <- [1]           [1]   [1]  -> [2] -> [3] -> None   (curr.next now None)
step 3:  prev = [1]
step 4:  curr = [2]

Repeat:  None <- [1] <- [2]          [3] -> None
                          prev curr

Repeat:  None <- [1] <- [2] <- [3]         None
                                 prev curr(=None, loop ends)

return prev = [3] -> [2] -> [1] -> None
```

O(n) time, **O(1) space** — no recursion frame, no auxiliary structure. A
recursive version exists (mirrors Go guide Part 4.2) but costs O(n) call
stack frames and CPython's default recursion limit (~1000) makes it
**actually fail**, not just theoretically worse, on lists longer than that —
default to iterative.

### 4.2 008 Reorder List = 001 composed with 004 and a merge

Reorder `L0 -> L1 -> ... -> Ln` into `L0 -> Ln -> L1 -> Ln-1 -> ...` without
extra space beyond a few pointers. This is not a new technique — it is three
techniques from this guide, chained:

```
1. find the middle              (§3.1, slow/fast)
2. reverse the second half      (§4.1, the reversal template)
3. merge the two halves,
   alternating one node from each
```

```
1 -> 2 -> 3 -> 4 -> 5

split at middle (§3.1):    1 -> 2 -> 3        4 -> 5
reverse second half (§4.1): 1 -> 2 -> 3        5 -> 4
merge alternating:          1 -> 5 -> 2 -> 4 -> 3
```

Seeing 008 as "001 and 004 back to back plus a zip" instead of a new
algorithm is the whole point of learning reversal as a *template* rather than
a one-off trick.

### 4.3 015 Reverse Nodes in k-Group = 001 applied repeatedly, with bookkeeping

Reverse every consecutive group of `k` nodes; leave a trailing group shorter
than `k` untouched. The core reversal loop is **exactly** §4.1's three-pointer
dance, run on a bounded sub-list of length `k` instead of the whole list —
the added work is (a) checking there are actually `k` nodes left before
committing to reverse them, and (b) reconnecting the reversed group's new
head/tail to the group before and after it (a job the dummy-head trick from
Part 2 simplifies, since "the node before the first group" needs the same
treatment as any other "node before an insertion point").

---

## Part 5 · Pattern Decision Tree

```
1. Does the operation touch or might it change THE HEAD
   (delete head, insert before head, merge lists of unequal presence)?
       YES -> use a dummy/sentinel node (Part 2). Always.
       NO  -> continue.

2. Am I looking for a POSITION relative to list length
   (middle, kth-from-end, detect a cycle)?
       middle                    -> slow/fast, same start (§3.1)
       cycle exists?              -> slow/fast, same start, IDENTITY compare (§3.2)
       kth from the end           -> fixed-gap two pointers (§3.3)

3. Am I inverting some or all of the pointer direction?
       whole list                 -> the reversal template (§4.1)
       reorder / interleave        -> reversal + merge, composed (§4.2)
       reverse in fixed-size groups -> reversal applied repeatedly + bookkeeping (§4.3)

4. Do I need O(1) removal/reorder by KEY, not by position
   (most-recently-used eviction, arbitrary node removal by identity)?
       YES -> doubly linked list + hashmap (Part 6) — neither alone is enough:
              a hashmap has no notion of order, a SINGLY linked list can't
              unlink a node in O(1) without its predecessor.

5. Am I copying a list that has EXTRA pointers beyond .next
   (e.g. a random pointer to an arbitrary other node, problem 010)?
       YES -> the interleave-and-split trick: splice a copy of each node
              directly after its original (so "the copy of X.random" is
              always "X.random.next"), fix up random pointers in one pass,
              then split the two interleaved lists apart. O(n) time, O(1)
              extra space (no hashmap needed) — see problem 010's solution
              file for the full trace.
```

---

## Part 6 · Building Toward LRU Cache (013) — Why Two Structures, Not One

O(1) `get`/`put` needs **both** a hashmap (O(1) lookup by key) and a doubly
linked list (O(1) reordering to "most recent," O(1) eviction of "least
recent"). Neither alone is sufficient:

```arch
%% caption: LRU cache: the hash map gives O(1) lookup, the doubly linked list gives O(1) reorder and eviction.
grid 120x100
group HM "hash map: key to node" color=purple
node k3 "key 3" at 1,0 in HM shape=pill
node k1 "key 1" at 2,0 in HM shape=pill
node k2 "key 2" at 3,0 in HM shape=pill
group DLL "doubly linked list: order of use" color=blue
node H "head" at 0,1 in DLL sub="sentinel"
node N3 "node 3" at 1,1 in DLL color=green sub="most recent"
node N1 "node 1" at 2,1 in DLL
node N2 "node 2" at 3,1 in DLL color=red sub="least recent"
node T "tail" at 4,1 in DLL sub="sentinel"
H <-> N3 <-> N1 <-> N2 <-> T
k1 ..> N1
k2 ..> N2
k3 ..> N3
```


- A plain `dict` has no notion of *order* — nothing in it tells you which key
  was used longest ago.
- A **singly** linked list cannot delete an arbitrary node in O(1): unlinking
  `node` requires updating `node.prev.next`, but a singly linked list only
  gives you `.next` — finding the predecessor needs an O(n) scan from the
  head, unless you keep a *separate* reference to it (which is exactly what
  "doubly" linked buys you for free, on every node, at all times).

The map stores **node references** (`dict[key] -> Node`), not values, so
promoting or evicting a key mutates the *same* node object the map already
points at — no need to touch the map on every reorder, only on insert and
eviction. Full walkthrough, including two sentinel nodes (head and tail) that
eliminate empty-list/single-node branching the same way Part 2's dummy head
does, lives in problem 013's solution file.

---

## Part 7 · Complexity Reference for This Topic

| Operation | Complexity | Mutates input? | Note |
|---|:--:|:--:|---|
| Access by index | O(n) | no | must walk from head — no random access |
| Search by value | O(n) | no | linear scan |
| Insert/delete at a KNOWN node | O(1) | yes | given the reference, just rewire `.next` |
| Insert/delete by value | O(n) find + O(1) rewire | yes | the O(n) is the search, not the edit |
| Reversal (iterative) | O(n) time, O(1) space | yes (rewires every `.next`) | §4.1 |
| Reversal (recursive) | O(n) time, O(n) space | yes | one call frame per node — CPython's ~1000 limit is a REAL ceiling, not just "worse asymptotically" |
| Cycle detection (Floyd's) | O(n) time, O(1) space | no | vs. O(n) time/space with a `set` of visited nodes |
| Find the middle | O(n), one pass | no | vs. two-pass count-then-walk, also O(n) but two walks |
| Copy w/ random pointer, hashmap | O(n) time, **O(n)** space | no (builds new list) | old-node -> new-node map |
| Copy w/ random pointer, interleave | O(n) time, **O(1)** space | temporarily yes, restored | Part 5 §5, problem 010 |
| LRU get/put | O(1) time, O(capacity) space | yes | doubly linked list + hashmap, Part 6 |

**"Mutates input?" matters more here than almost anywhere else in the
curriculum.** Several of these problems have a clean O(n)-extra-space
solution (build a new list, or use a hashmap/array of visited nodes) sitting
right next to an O(1)-extra-space in-place solution that reuses the existing
nodes — always name both, then justify which one you're writing.

---

## Part 8 · Common Mistakes Across This Topic

1. **Overwriting `.next` before saving it** (Part 1.3) — the single most
   common bug in this entire topic. If you cannot articulate why `nxt =
   curr.next` must be the *first* line of a reversal loop body, you will
   write this bug under pressure.
2. Forgetting a dummy/sentinel head on any operation that might delete or
   insert before the first node — reintroduces exactly the head-of-list
   special case Part 2 exists to eliminate.
3. Comparing node **values** (`slow.val == fast.val`) instead of node
   **identity** (`slow is fast`) when detecting a cycle — two different nodes
   can legitimately hold the same value; only reference identity proves
   they're the same node.
4. Off-by-one on the fixed-gap two-pointer (§3.3) — opening the gap `n`
   steps vs. `n - 1` steps changes whether `slow` ends up on the target node
   or one before it. Always re-derive from the dummy-head picture, don't
   recall it from memory.
5. Recursing to reverse or process a list without checking length against
   CPython's recursion limit — correct on small inputs, `RecursionError` on
   large ones. State the ceiling explicitly if you choose recursion.
6. For "copy list with random pointer" (010): building the copy with a
   hashmap and forgetting that `random` pointers may point at nodes **not
   yet copied** (forward references) — must map *all* nodes first, or use
   the interleave trick which sidesteps the ordering problem entirely.
7. Losing the original list's structure while transforming it in place (008
   reorder, 015 k-group reverse) because a rewiring step reused a variable
   name that still held a "before" reference needed later in the same
   function.
8. For LRU (013): updating only the hashmap or only the linked list on an
   eviction, not both — the two structures must always agree on membership.

---

## Part 9 · The Progression in This Folder

```
  001  LC 206   Reverse Linked List             the reversal template — learn this cold
  002  LC 21    Merge Two Sorted Lists          dummy head + two-pointer merge
  003  LC 141   Linked List Cycle               slow/fast, the meeting-point proof
  004  LC 876   Middle of the Linked List       slow/fast, one pass, no cycle involved
  005  LC 203   Remove Linked List Elements     dummy head removes the head special-case
  006  LC 83    Remove Duplicates from Sorted   adjacent-pointer scan, sorted input only
  007  LC 234   Palindrome Linked List          004 + 001 composed, then compare
  008  LC 143   Reorder List                    004 + 001 + merge, composed (§4.2)
  009  LC 19    Remove Nth From End             fixed-gap two pointers (§3.3)
  010  LC 138   Copy List with Random Pointer   hashmap vs. O(1)-space interleave trick
  011  LC 2     Add Two Numbers                 dummy head + carry propagation
  012  LC 287   Find the Duplicate Number       array-as-implicit-linked-list, Floyd's reused
  013  LC 146   LRU Cache                       doubly linked list + hashmap (Part 6)
  014  LC 23    Merge k Sorted Lists            heap-based k-way merge of 002
  015  LC 25    Reverse Nodes in k-Group        001 applied repeatedly (§4.3)
```

007 and 008 both reuse 001 and 004 directly — treat them as composition
exercises, not new algorithms. 012 is the surprise of the folder: it looks
like a pure array problem, but treating `nums[i] -> nums[nums[i]]` as a
`.next` pointer turns it into a disguised instance of 003's cycle detection.

---

<!-- block:08_py_1_beyond -->
## Part 10 · Beyond the Fifteen: Intersection, Sort, Rearrangement and Templates

The fifteen problems teach the toolbox; these recombine it. Every snippet was run against LeetCode's own examples
while writing this section.

### 10.1 Where does the cycle *start*? (LC 142)

Detection (Part 3.2) tells you a cycle exists. To find the **entry**: when `slow` and `fast` first meet, restart one
pointer at `head` and move *both one step at a time* — they meet again exactly at the entry.

```python
def detect_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
        if slow is fast:
            p = head
            while p is not slow: p, slow = p.next, slow.next
            return p                      # the entry node
    return None
```

**Why.** Let `a` = head → entry, `b` = entry → meeting point, `c` = the rest of the loop. `slow` walked `a + b`; `fast`
walked twice that, and also `a + b + n(b + c)` for `n` extra laps. Equate them: `a + b = n(b + c)`, so
`a = (n − 1)(b + c) + c`. Walking `a` from the head and `c` (then whole laps) from the meeting point land on the same
node. The same algebra is why Find the Duplicate Number (LC 287) works on an array.

### 10.2 Intersection of two lists (LC 160): equalise the paths by swapping

Two lists merge into one shared tail; find the first shared *node* (by identity). Walk two pointers, and when one runs
off the end, **restart it on the other list's head**. Both then travel `len(A) + len(B)` nodes, so they arrive at the
intersection at the same moment — or both reach `None` together if there is none:

```python
def get_intersection(a, b):
    p, q = a, b
    while p is not q:
        p = p.next if p else b
        q = q.next if q else a
    return p          # the shared node, or None
```

O(m + n) time, O(1) space (the alternative is a hash set of nodes, O(m) space). Compare with `is`, never `==` on values.

### 10.3 Sort a linked list (LC 148): merge sort is the natural fit

Merge sort needs no random access, and merging linked lists is O(1) space — so linked lists are where merge sort beats
quicksort. Find the middle with slow/fast (start `fast` one node ahead so `slow` lands at the **end of the first
half**), **cut** the list there, sort both halves, merge:

```python
def sort_list(head):
    if not head or not head.next: return head
    slow, fast = head, head.next
    while fast and fast.next: slow, fast = slow.next, fast.next.next
    second, slow.next = slow.next, None     # CUT — without this the recursion never shrinks
    return merge(sort_list(head), sort_list(second))     # merge(): Problem 002
```

O(n log n) time; **O(log n) stack** for the top-down form (a bottom-up merge sort achieves O(1) extra space). It also
answers "sort with O(1) extra space" where an array-copy sort cannot.

### 10.3b Rearranging without allocating: two dummy heads

Many "reorder the list" problems are *"build two lists with two dummies, then join them"*. **Partition List (LC 86)**:

```python
def partition(head, x):
    lo, hi = ListNode(), ListNode(); a, b = lo, hi
    while head:
        if head.val < x: a.next = head; a = a.next
        else:            b.next = head; b = b.next
        head = head.next
    b.next = None            # CUT the tail, or it still points into the old list and forms a cycle
    a.next = hi.next
    return lo.next           # [1,4,3,2,5,2], 3 -> [1,2,2,4,3,5]
```

**Odd Even List (LC 328)** is the same idea in place (`odd.next = even.next`, then `even.next = odd.next`, finally
`odd.next = even_head`): `[1,2,3,4,5]` → `[1,3,5,2,4]`. **Rotate List (LC 61)**: find the length, close the list into a
ring, walk `n − k − 1` steps to the new tail, and cut (`k %= n` first): `[1,2,3,4,5]`, 2 → `[4,5,1,2,3]`. **Swap Nodes in
Pairs (LC 24)** rewires three pointers per pair behind a dummy: `[1,2,3,4]` → `[2,1,4,3]`.

The failure they all share: **forgetting to null the new tail**, which leaves a stale `next` into the old chain and a
cycle. Print or traverse only after you have cut.

### 10.4 Doubly linked list: the O(1) templates

Given a node you hold, `remove` and `insert` are O(1) because the node knows both neighbours. With **two sentinels**
(head and tail) there is no empty-list or single-node branch:

```python
def remove(n):                       # unlink n from wherever it is
    n.prev.next, n.next.prev = n.next, n.prev
def insert_after(node, n):           # splice n in right after `node`
    n.prev, n.next = node, node.next
    node.next.prev = n
    node.next = n
```

LRU Cache (013) is this plus a dict; LFU Cache (topic 25) adds a *list per frequency*. `collections.OrderedDict`
gives LRU in ten lines (`move_to_end`, `popitem(last=False)`) — write the manual version first, then mention it.

### 10.5 Testing pitfalls specific to linked lists

| Pitfall | What happens | Habit |
|---|---|---|
| Printing a list that contains a cycle | An infinite loop (or a truncated print if you cap it). | Build cyclic inputs deliberately, and test them with the detection function — never `print` them. |
| `==` on nodes | Without `__eq__`, `==` is identity; with a value-based `__eq__` it is wrong for cycle checks. | Always `is` / `is not` for node comparisons. |
| Recursive reversal on a long list | `RecursionError` at depth 1000 — a 3,000-node list fails. | Default to the iterative version; recursion is O(n) stack. |
| Building test lists | Hand-wiring `.next` invites off-by-ones. | A `build(vals)` helper (dummy head) and a `to_list(head)` helper; assert on Python lists. |
| Mutating inputs used in two tests | A reversed list is not the list you started with. | Rebuild the input per assertion. |

### 10.6 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "O(1) extra space?" | Two pointers, reversal in place, or Floyd — say which trade you made (e.g. Palindrome: reverse the second half, compare, and *restore it*). |
| "Recursively?" | Fine for clarity, but O(n) stack — and Python fails at ~1000. State the cost, then write the loop. |
| "Doubly linked?" | Then a tail pointer and `prev` make `pop` and reverse-iteration O(1) at both ends (a deque). |
| "Why would anyone use a linked list?" | O(1) splice at a known node and stable handles (LRU, free lists, intrusive lists). For plain iteration a contiguous array wins on cache behaviour — say so. |
| "Skip lists / XOR lists?" | A skip list layers express lanes over a sorted list for O(log n) search; an XOR list stores `prev ^ next` to halve pointer memory (not expressible in safe Python). |
| "Thread safety?" | Pointer rewiring is not atomic — a lock, or lock-free CAS on the head for a stack. |

---
<!-- /block:08_py_1_beyond -->

<!-- problem-map:start -->
## Part 11 · Every Problem in This Topic, by Pattern

Fifteen problems, six moves (reversal · dummy head · fast/slow · fixed gap · composition · two structures). Each **Trap** is one the tests in that problem's solution file actually trigger.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Reverse Linked List](PyDSA/08_linked_list/001_reverse_linked_list_solution.py) <br>LC 206 · Easy | Three-pointer rewiring | Walk the list rewiring each `.next` backward; `nxt = curr.next` must be saved *first*, and `prev` is the new head. **Trap:** overwriting `curr.next` before saving it (silently truncates, never crashes); returning `head` (now the tail). |
| [002 · Merge Two Sorted Lists](PyDSA/08_linked_list/002_merge_two_sorted_lists_solution.py) <br>LC 21 · Easy | Dummy head + merge | The merge step of merge sort with no array: compare only the two front nodes and splice the winner; a dummy head removes the "first node of the result" case. **Trap:** no dummy; a tie-break that disagrees with the advance logic. |
| [003 · Linked List Cycle](PyDSA/08_linked_list/003_linked_list_cycle_solution.py) <br>LC 141 · Easy | Floyd cycle detection | `slow` moves 1, `fast` moves 2; a cycle forces them to meet because the gap closes by exactly 1 each step. **Trap:** guarding only `fast` (check `fast` *and* `fast.next` first); comparing `.val` instead of identity. |
| [004 · Middle of the Linked List](PyDSA/08_linked_list/004_middle_of_the_linked_list_solution.py) <br>LC 876 · Easy | Slow/fast midpoint | One pass with `while fast and fast.next`; on an even length `slow` lands on the *second* middle. **Trap:** `while fast:` (AttributeError); starting `fast` one ahead returns the first middle. |
| [005 · Remove Linked List Elements](PyDSA/08_linked_list/005_remove_linked_list_elements_solution.py) <br>LC 203 · Easy | Dummy head + delete | `curr.next = curr.next.next` needs a node *before* the target — the dummy supplies one for the head. Advance only when you did **not** delete. **Trap:** advancing after a deletion skips the new `next` (fails on runs of 2+ matches). |
| [006 · Remove Duplicates from Sorted List](PyDSA/08_linked_list/006_remove_duplicates_from_sorted_list_solution.py) <br>LC 83 · Easy | Adjacent scan (sorted) | Sorted ⇒ duplicates are adjacent, so splice out `curr.next` while it equals `curr`. **Trap:** running it on an *unsorted* list — only adjacent duplicates vanish. |
| [007 · Palindrome Linked List](PyDSA/08_linked_list/007_palindrome_linked_list_solution.py) <br>LC 234 · Easy | Reverse the second half | Find the middle, reverse the second half in place, compare halves — O(1) space (copying to an array is the O(n)-space alternative). **Trap:** a direct two-pointer scan (a singly linked list cannot step backward); leaving the list reversed. |
| [008 · Reorder List](PyDSA/08_linked_list/008_reorder_list_solution.py) <br>LC 143 · Medium | Middle + reverse + weave | A composition of 004, 001 and a merge — not a new algorithm. **Trap:** reversing before finding the split; not cutting the first half (`slow.next = None`), which creates a cycle. |
| [009 · Remove Nth Node From End of List](PyDSA/08_linked_list/009_remove_nth_node_from_end_of_list_solution.py) <br>LC 19 · Medium | Fixed-gap pointers | From a dummy, open a gap of `n` between `fast` and `slow`, then walk together; `slow` stops just *before* the node to delete. **Trap:** a gap of `n - 1`; no dummy (a separate case for `n == length`). |
| [010 · Copy List with Random Pointer](PyDSA/08_linked_list/010_copy_list_with_random_pointer_solution.py) <br>LC 138 · Medium | Two-pass or interleave | `random` may point *forward* to a node not yet copied: build all copies first (a dict), then wire; or splice copies between originals for O(1) extra space. **Trap:** wiring `random` in the same pass as `next`; `mapping[x]` on `None` (KeyError) — use `.get`. |
| [011 · Add Two Numbers](PyDSA/08_linked_list/011_add_two_numbers_solution.py) <br>LC 2 · Medium | Carry propagation | Least-significant-first is the order column addition wants: `d1 + d2 + carry`, emit `% 10`, carry `// 10`. **Trap:** `while l1 and l2` drops the longer list's tail; `while l1 or l2` drops the final carry (`999 + 1`). |
| [012 · Find the Duplicate Number](PyDSA/08_linked_list/012_find_the_duplicate_number_solution.py) <br>LC 287 · Medium | Floyd on an array | Treat `nums[i]` as a `.next` pointer: values in `1..n` form a functional graph with a cycle, and the duplicate is its entry. **Trap:** comparing `slow == fast` before either has moved; believing the array must be sorted. |
| [013 · LRU Cache](PyDSA/08_linked_list/013_lru_cache_solution.py) <br>LC 146 · Medium | Map + doubly linked list | The map gives O(1) lookup, the list gives O(1) reorder and eviction; two sentinels remove every empty-list branch. **Trap:** evicting from only one structure; `put` on an *existing* key must also promote it to most-recent. |
| [014 · Merge k Sorted Lists](PyDSA/08_linked_list/014_merge_k_sorted_lists_solution.py) <br>LC 23 · Hard | Heap of list heads | k-way merge with a min-heap of each list's current head: O(N log k), not the O(N·k) of repeated pairwise merges. **Trap:** pushing `(node.val, node)` with no tiebreaker (`TypeError` on equal values — `ListNode` has no `__lt__`). |
| [015 · Reverse Nodes in k-Group](PyDSA/08_linked_list/015_reverse_nodes_in_k_group_solution.py) <br>LC 25 · Hard | Reverse in k-groups | 001 applied to consecutive groups; check that `k` nodes exist **before** rewiring; seed `prev` with the node after the group. **Trap:** reversing a short final group; seeding `prev = None` (truncates the rest of the list). |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] I can state the array-vs-linked-list trade-off (O(1) random access vs.
      O(1) insert/delete at a known node) without hedging.
- [ ] I save `nxt = curr.next` before writing `curr.next = ...`, every time,
      reflexively — and I can produce the broken version from memory to show
      why the order matters.
- [ ] I reach for a dummy/sentinel head automatically whenever an operation
      might touch, delete, or insert before the current head.
- [ ] I can derive — not recite — why slow/fast pointers must meet inside a
      cycle: the gap shrinks by exactly 1 each step and cannot skip past 0.
- [ ] I know the fixed-gap two-pointer pattern for "Nth from the end" and can
      re-derive the gap size from a dummy-head picture.
- [ ] I can write the three-pointer reversal (`prev`/`curr`/`nxt`, in that
      order) cold, and explain why it's O(1) space vs. the recursive O(n).
- [ ] I see 008 and 015 as compositions of 001 with other techniques, not as
      new algorithms to memorise separately.
- [ ] I compare nodes with `is`, never `==`/value equality, when the question
      is about identity (cycles, "is this the same node").
- [ ] I can explain why <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr> needs BOTH a hashmap and a doubly linked list,
      and why singly linked isn't enough.
- [ ] I know the O(n)-space (hashmap) vs. O(1)-space (interleave) solutions
      to "copy with random pointer" and can explain the ordering problem the
      interleave trick sidesteps.
</content>
- [ ] Find the cycle *entry* (LC 142) and state why restarting one pointer at `head` works <!--ca-->
- [ ] Find the intersection of two lists with the path-swap trick, and say why it is O(1) space <!--ca-->
- [ ] Sort a linked list with merge sort, cutting at the middle (and say why not quicksort) <!--ca-->
- [ ] Rearrange with two dummy heads, and remember to null the new tail <!--ca-->
- [ ] Say why recursion on a 3,000-node list fails in CPython and what you would write instead <!--ca-->
