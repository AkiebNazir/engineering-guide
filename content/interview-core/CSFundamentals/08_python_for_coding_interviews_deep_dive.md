# Python for Coding Interviews — The Standard Library, Cold

This file is a reference, not a narrative read: dip into whichever section you need.
If `O(1)`/`O(n)` or "hash map" feel unfamiliar, read [Complexity Analysis](07_complexity_analysis_deep_dive.md)
and [Data Structure Internals](06_data_structure_internals_deep_dive.md) first — this file assumes that
vocabulary and turns it into exact Python tool choices. Python is this curriculum's
interview language. The plan's mastery check: **write Dijkstra, an LRU cache, and a
trie in a plain doc with zero syntax lookups.** This file is the complete toolkit,
with the complexity and the traps for each tool. Every snippet here runs on Python
3.10+ (verified on 3.13).

If you're newer to Python (or have used it without ever asking what a line actually
costs), start with the **Foundations** section: what the interpreter is doing under
your code, what its components are, and why names, references and mutability explain
most of the bugs in §9. The numbered sections after it are the original reference,
now with a few added subsections (sorting guarantees, how `heapq` lays a heap out in a
list, an iterative DFS, Union-Find and Kahn's algorithm written out). A side-by-side
breakdown of what Junior through Staff+ engineers are expected to know closes the
chapter, just before the interview checklist.

## Foundations — What Python Is Doing Under Your Interview Code

### Why a Language Chapter Exists at All

An interview problem is graded on the algorithm, but the algorithm only exists as
code in one specific language. Every abstract structure you learn in
[Data Structure Internals](06_data_structure_internals_deep_dive.md) (a queue, a hash map, a priority queue)
becomes a concrete Python type or module the moment you start typing, and each of
those types has a cost that the syntax hides. `x in a` looks identical whether `a` is
a `list` (O(n) scan) or a `set` (O(1) average hash lookup). `a.pop()` and `a.pop(0)`
differ by one character and by a factor of n. A candidate who knows the algorithm but
not the tool ends up either writing an O(n²) solution by accident or burning ten
minutes reinventing `heapq`. This chapter closes that gap: the right tool, its cost,
and its traps, cold.

### What Python Actually Is (When You Run It)

"Python" is a language specification; what runs your code is almost always
**CPython**, the reference implementation, written in C. When you run a file, three
things happen:

1. The **compiler** turns your source text into **bytecode**: a compact list of simple
   instructions (`LOAD_FAST`, `BINARY_OP`, `CALL`, ...). This happens once per file
   and is cached in `__pycache__`.
2. The **interpreter loop** (the "eval loop") executes that bytecode one instruction
   at a time. Every Python-level step (a loop iteration, an attribute lookup, a
   function call) is several of these instructions, each with dispatch and type-check
   overhead. That is why a plain Python loop is far slower per step than the same
   loop in C, Go or Java.
3. Every value the code touches is an **object on the heap**: a C struct carrying a
   type pointer and a **reference count**, plus the value itself. Memory is freed when
   the count drops to zero, with a separate cycle collector for objects that reference
   each other.

The practical consequence for interviews: the **built-in types and many standard
library modules are implemented in C**. `sorted`, `sum`, `dict` lookups,
`deque.popleft`, `heapq.heappush` and `bisect_left` each run as one call into
compiled code instead of many bytecode steps. Big-O is what the interviewer grades;
leaning on built-ins also keeps the constant factor low.

### The Core Components You Actually Use

| Component | What it's responsible for | Covered deeper in |
|---|---|---|
| **Interpreter (CPython)** | Compiles source to bytecode and runs it; sets the per-step cost and the recursion limit | Foundations, §6 |
| **Object model** | Every value is a heap object; variables are *names* bound to objects, never boxes holding copies | Foundations, §9 |
| **Built-in types** | `list`, `dict`, `set`, `str`, `int`, `tuple`: the C-implemented workhorses with known costs | §1 |
| **`collections`** | `deque`, `Counter`, `defaultdict`, `OrderedDict`: the specialised containers | §2 |
| **`heapq` and `bisect`** | Algorithms that operate on a plain `list` (a heap, a sorted array) rather than new types | §3, §4 |
| **`itertools`, `functools`, `math`** | Combinatorics, memoization, custom sort comparators, number theory | §5 |
| **The call stack** | One frame per Python call; recursion depth is capped (default 1000) | §6 |

### How the Pieces Fit Together

```arch
%% caption: Source is compiled to bytecode and run by the interpreter loop; the fast paths are the C-implemented built-ins, and every value lives on the object heap.
grid 170x110
node src "your_solution.py" at 1,0 icon=code sub="source text"
node comp "Compiler" at 1,1 icon=process sub="source to bytecode"
node loop "Interpreter loop" at 1,2 icon=cpu sub="one bytecode at a time"
group c "Implemented in C: one call, no per-step overhead" color=green icon=layers
node bi "Built-in types" at 0,3 in c icon=table sub="list, dict, set, str"
node std "Accelerated stdlib" at 1,3 in c icon=package sub="heapq, deque, bisect"
node fns "Built-in functions" at 2,3 in c icon=function sub="sorted, sum, min, max"
node heap "Object heap" at 1,4 icon=memory sub="refcounts + cycle GC"
src -> comp -> loop
loop -> bi
loop -> std
loop -> fns
bi -> heap
std -> heap
fns -> heap
```

A quick measurement makes the "built-ins are C" point concrete (numbers vary by
machine; on a typical 2020s laptop the built-in is several times faster):

```python
import timeit

nums = list(range(1_000_000))

def manual_sum():
    total = 0
    for x in nums:          # ~1M trips through the interpreter loop
        total += x
    return total

print("loop:", timeit.timeit(manual_sum, number=10))
print("sum():", timeit.timeit(lambda: sum(nums), number=10))   # one C call per run
```

The rule of thumb from [Complexity Analysis](07_complexity_analysis_deep_dive.md) §8 (roughly 10^7 simple
Python operations per second, versus roughly 10^8 in C++/Java/Go) comes from exactly
this per-step overhead. It is approximate; the point is the order of magnitude.

### Names, References and Mutability: the Distinction This Whole File Assumes

In Python, `x = [1, 2]` does not put a list *into* `x`. It creates a list object on the
heap and binds the **name** `x` to it. `y = x` binds a second name to the *same*
object; nothing is copied. Whether that matters depends on whether the object is
**mutable** (can change in place: `list`, `dict`, `set`, your own classes) or
**immutable** (cannot: `int`, `str`, `tuple`, `frozenset`).

```python
a = [1, 2, 3]
b = a                  # a second name for the SAME list
b.append(4)
print(a)               # [1, 2, 3, 4]: a changed too
c = a[:]               # a shallow copy: a NEW list holding the same elements
c.append(5)
print(a, c)            # [1, 2, 3, 4] [1, 2, 3, 4, 5]

grid = [[0] * 3] * 2   # a list holding two references to ONE inner list
grid[0][0] = 9
print(grid)            # [[9, 0, 0], [9, 0, 0]]: both "rows" changed

s = "abc"
t = s
t += "d"               # strings are immutable: += builds a NEW string, rebinds t
print(s, t)            # abc abcd
```

Almost every trap in §9 is this one idea in disguise: `[[0] * m] * n`, appending
`path` instead of `path[:]` in backtracking, the mutable default argument, and
closure late binding all come from two names sharing one mutable object.

**Hashability follows from mutability.** A `dict` or `set` finds a key by its hash
and then confirms with `==`. If a key could change after insertion, its hash would
change and the entry would be lost in the wrong slot. So only immutable values are
hashable: `tuple`, `str`, `int` and `frozenset` can be keys; `list`, `dict` and `set`
cannot. That is why a grid position is the tuple `(r, c)` and a "set of sets" needs
`frozenset`.

### Which Python Tool for Which Abstract Structure

| You need (from `06`) | Python tool | Core costs |
|---|---|---|
| Dynamic array, stack | `list` | index O(1); `append`/`pop()` O(1) amortized; insert/delete at front O(n) |
| Queue, deque | `collections.deque` | `append`/`popleft`/`appendleft`/`pop` O(1); indexing the middle O(n) |
| Hash map | `dict` | get/set/delete O(1) average |
| Hash set | `set` | add/remove/membership O(1) average |
| Multiset, frequency table | `collections.Counter` | increment O(1) average |
| Min priority queue | `heapq` on a `list` | push/pop O(log n), peek O(1), heapify O(n) |
| Sorted array + binary search | `list` + `bisect` | search O(log n); insert O(n) (shifting) |
| Graph (adjacency list) | `defaultdict(list)` or `dict[node, list]` | add edge O(1); iterate neighbours O(degree) |
| Trie | nested `dict`s or a small node class | O(word length) per operation |
| Record / composite key | `tuple`, `NamedTuple`, `@dataclass(frozen=True)` | hashable if all fields are |

**Precision note:** the standard library has **no balanced BST or ordered map** (no
equivalent of Java's `TreeMap` or C++'s `std::map`). When a problem needs "insert,
delete, and find the next-larger key" in O(log n), your options are a heap with lazy
deletion (§3), a sorted list with `bisect` (O(n) inserts, often fast enough for
n ≤ 10^5 because the shift is a C `memmove`), or the third-party `sortedcontainers`
package, which many online judges provide but a plain-doc interview may not. Say
which one you're using and why.

### Laziness: Iterators and Generators

`range`, `zip`, `enumerate`, `map`, `filter`, `reversed`, `dict.items()` and
generator expressions don't build a list; they produce values one at a time on
demand. `sum(x * x for x in nums)` uses O(1) extra memory; `sum([x * x for x in nums])`
builds an O(n) list first. Two consequences worth knowing: an iterator can be consumed
only once (a second loop over the same `zip` object sees nothing), and a function
containing `yield` is a **generator**, which is the idiomatic way to write
`neighbors(r, c)` helpers without building lists.

### Vocabulary You'll Meet Below, in One Table

| Term | One-line meaning |
|---|---|
| CPython | The standard Python implementation: a bytecode interpreter written in C |
| Bytecode | The simple instructions your source compiles to; the interpreter loop runs them |
| Name / reference | A variable is a label bound to an object; assignment never copies |
| Mutable / immutable | Whether an object can change in place after creation |
| Hashable | Has a hash that never changes and a consistent `==`; required for dict keys and set members |
| Shallow vs deep copy | `a[:]` copies the outer container; inner objects are still shared (`copy.deepcopy` copies all) |
| Amortized O(1) | Occasionally expensive (a list resize) but constant on average over many calls |
| Stable sort | Equal keys keep their original relative order |
| Iterator / generator | Produces values lazily, one at a time; consumed once |
| Dunder method | `__lt__`, `__eq__`, `__hash__`, `__len__`: how your classes plug into built-in operators |

With the interpreter model, the reference semantics and the tool map in place, the
sections below are the exact reference: every operation's cost and every trap, per
module.

## 1. Built-in Types: Costs and Traps

### list
```python
a = [0] * n                    # O(n); fine for immutables
grid = [[0] * m for _ in range(n)]   # correct 2D init
bad  = [[0] * m] * n           # WRONG: n references to the SAME row
a.append(x); a.pop()           # O(1) amortized — use as a stack
a.pop(0); a.insert(0, x)       # O(n) — never in a loop; use deque
a[i:j]                         # O(j - i) copy
a[::-1]; a.reverse()           # copy vs in-place, both O(n)
x in a                         # O(n)
a.sort(key=..., reverse=True)  # in place, stable, O(n log n)
sorted(iterable)               # returns a new list
a.index(x)                     # O(n), raises ValueError if absent
```

### dict and set
```python
d = {}
d[k] = v; d.get(k, default)    # O(1) average
d.setdefault(k, []).append(v)  # get-or-insert
d.pop(k, None)                 # delete without KeyError
for k, v in d.items(): ...     # insertion order is guaranteed (3.7+)
s = set(); s.add(x); s.discard(x)   # discard doesn't raise
a & b, a | b, a - b, a ^ b     # set algebra, O(len) each
frozenset(s)                   # hashable set (use as dict key)
```
Keys must be hashable: `tuple`, `str`, `int`, `frozenset` — not `list`, `dict`, `set`. For a grid position use `(r, c)`.

### str
```python
s.split(), s.split(","), " ".join(words)
s.strip(), s.lower(), s.isalnum(), s.isdigit(), s.isalpha()
s.startswith(p), s.find(sub)   # find returns -1; index raises
ord("a"), chr(97)              # char <-> code point
ord(c) - ord("a")              # letter index 0..25
"".join(reversed(s)), s[::-1]
f"{x:>5}", f"{val:.2f}"
```
Never build strings with `+=` in a loop; collect parts and `"".join(parts)`.

### int
- Arbitrary precision: **no overflow**. Say so, and mention that Java/C++/Go would need `long`/modular arithmetic.
- `//` floors toward negative infinity: `-7 // 2 == -4`. `%` has the sign of the divisor: `-7 % 3 == 2`. For truncation toward zero: `int(a / b)` for small values, or sign-aware integer division (see `PyDSA/06_stack/011`).
- `float("inf")`, `-float("inf")` for sentinels; `math.inf` too.
- `divmod(a, b)`, `pow(base, exp, mod)` (fast modular exponentiation), `abs`, `round` (banker's rounding: `round(2.5) == 2`).
- `x.bit_length()`, `x.bit_count()` (3.10+), `bin(x)`.

### tuple
```python
r, c, x = 2, 3, 7
p = (r, c)                     # immutable, hashable if its items are: a dict key or set member
r, c = p                       # unpacking
(1, 2) < (1, 3) < (2, 0)       # compared element by element: why heap entries are tuples
single = (x,)                  # the comma makes a tuple, not the parentheses
```
Use a tuple for fixed-shape records and composite keys; use a list when the length
changes. `collections.namedtuple` / `typing.NamedTuple` add field names at no cost.

### Sorting: what `sort` actually guarantees
```python
people = [("ana", 31), ("bo", 25), ("cy", 31), ("di", 25)]
by_age = sorted(people, key=lambda p: p[1])
# [('bo', 25), ('di', 25), ('ana', 31), ('cy', 31)]: equal ages keep input order (stable)

by_age_desc_then_name = sorted(people, key=lambda p: (-p[1], p[0]))
# [('ana', 31), ('cy', 31), ('bo', 25), ('di', 25)]

# Multi-key sort using stability: sort by the SECONDARY key first, then the primary.
tmp = sorted(people, key=lambda p: p[0])             # by name
tmp.sort(key=lambda p: p[1], reverse=True)           # by age desc; names stay sorted within ties
assert tmp == by_age_desc_then_name
```
- CPython's sort is **Timsort** (since 3.11 with the "powersort" merge policy): stable,
  O(n log n) worst case, and close to O(n) on input that is already mostly sorted,
  because it detects existing runs.
- `key=` is computed **once per element**, not once per comparison, so an expensive
  key is fine. `reverse=True` preserves stability (it is not "sort then reverse").
- Negating a key (`-p[1]`) only works for numbers. For "descending by string" use the
  two-pass stable trick above, or `cmp_to_key` (§5).

## 2. `collections`

```python
from collections import deque, Counter, defaultdict, OrderedDict

q = deque([start]); q.append(x); q.popleft()     # BFS queue, O(1) both ends
q.appendleft(x); q.pop(); q.rotate(k)
window = deque(maxlen=k)                         # auto-evicts from the left

cnt = Counter(s)                                 # char -> count
cnt.most_common(k)                               # O(n log k)
cnt["z"]                                         # 0 for missing keys, no KeyError
cnt1 == cnt2; cnt1 - cnt2                        # compare / subtract (drops <= 0)

graph = defaultdict(list)                        # adjacency list
graph[u].append(v)
groups = defaultdict(list); groups[key].append(item)

od = OrderedDict()                               # LRU in 6 lines:
od.move_to_end(key)                              # O(1) mark as recently used
od.popitem(last=False)                           # O(1) evict least recently used
```
```arch
%% caption: A deque is implemented as a doubly linked list of fixed-size blocks, allowing O(1) appends and pops from both ends without shifting elements.
group d "collections.deque" color=slate style=dashed
node head "Head Block" at 0,1 in d icon=package color=blue
node mid "Middle Block" at 2,1 in d icon=package color=blue
node tail "Tail Block" at 4,1 in d icon=package color=blue

head <-> mid
mid <-> tail

node pl "popleft()\nO(1)" at 0,0 shape=pill color=green
node p "pop()\nO(1)" at 4,0 shape=pill color=green

pl -> head
p -> tail
```

Trap: reading `defaultdict[missing]` **inserts** the key. Use `key in d` to test without inserting.

## 3. `heapq` — Min-Heap Only

```python
import heapq
h = []
heapq.heappush(h, (dist, node))       # tuples compare element by element
d, node = heapq.heappop(h)
h[0]                                  # peek min, O(1)
heapq.heapify(arr)                    # O(n), in place
heapq.heappushpop(h, x)               # push then pop, faster than two calls
heapq.nlargest(k, xs, key=...)        # O(n log k)

heapq.heappush(h, -x)                 # MAX-heap: negate
heapq.heappush(h, (-score, name))     # max by score, min by name on ties
heapq.heappush(h, (priority, next(counter), task))   # tie-breaker when items aren't comparable
```
`itertools.count()` gives the counter. No decrease-key: push a new entry and skip stale ones when popped (lazy deletion).

### How `heapq` stores a heap inside a plain list
`heapq` doesn't create a heap type; it keeps an ordinary `list` in **heap order**:
for every index `i`, `h[i] <= h[2*i + 1]` and `h[i] <= h[2*i + 2]`. The minimum is
always `h[0]`; the rest of the list is *not* sorted.

```python
import heapq
from dataclasses import dataclass, field

h = [5, 3, 8, 1, 9, 2]
heapq.heapify(h)                   # O(n) bottom-up, in place
print(h)                           # [1, 3, 2, 5, 9, 8]: heap order, not sorted order
for i in range(len(h)):
    for child in (2 * i + 1, 2 * i + 2):
        if child < len(h):
            assert h[i] <= h[child]

@dataclass(order=True)
class Task:                        # ordered by (priority, seq) only
    priority: int
    seq: int
    name: str = field(compare=False)   # never compared, so it needn't be orderable

tasks = []
heapq.heappush(tasks, Task(2, 0, "write"))
heapq.heappush(tasks, Task(1, 1, "read"))
print(heapq.heappop(tasks).name)   # read
```
Push appends at the end and **sifts up** (swap with parent while smaller); pop moves
the last element to the root and **sifts down**. Both touch one root-to-leaf path:
O(log n). The internals are in [Data Structure Internals](06_data_structure_internals_deep_dive.md) §5.

## 4. `bisect` — Binary Search on Sorted Lists

```python
from bisect import bisect_left, bisect_right, insort
i = bisect_left(a, x)     # first index with a[i] >= x   (insertion point before equals)
j = bisect_right(a, x)    # first index with a[j] >  x   (insertion point after equals)
count_x = bisect_right(a, x) - bisect_left(a, x)
exists = i < len(a) and a[i] == x
floor_idx = bisect_right(a, x) - 1          # last element <= x (if >= 0)
ceil_idx  = bisect_left(a, x)               # first element >= x (if < len)
insort(a, x)                                # O(log n) search + O(n) insert
bisect_left(a, x, key=lambda e: e[0])       # key= on 3.10+ (x is already a key)
```
For "binary search on the answer", write your own loop with a clear invariant:
```python
lo, hi = 1, max_possible            # answer is in [lo, hi]
while lo < hi:
    mid = (lo + hi) // 2
    if feasible(mid):
        hi = mid                    # mid works; look for smaller
    else:
        lo = mid + 1
return lo                           # first feasible value
```

## 5. `itertools`, `functools`, `math`

```python
from itertools import permutations, combinations, product, accumulate, groupby, chain, pairwise, zip_longest
permutations(xs, r); combinations(xs, r); product("ab", repeat=3)
list(accumulate(nums))                 # prefix sums
list(accumulate(nums, initial=0))      # prefix sums with a leading 0 (3.8+)
for key, grp in groupby(sorted(xs)): ...   # groups CONSECUTIVE equal keys only
pairwise([1, 2, 3])                    # (1,2), (2,3)   (3.10+)

from functools import cache, lru_cache, cmp_to_key, reduce
@cache                                 # unbounded memoization (3.9+)
def dp(i, j): ...
dp.cache_clear()                       # between test cases!
sorted(words, key=cmp_to_key(lambda a, b: -1 if a + b > b + a else 1))  # custom comparator

import math
math.gcd(a, b), math.lcm(a, b)         # lcm 3.9+
math.comb(n, k), math.perm(n, k), math.factorial(n)
math.isqrt(n)                          # exact integer sqrt
math.inf, math.isclose(a, b)
```
`@cache` arguments must be hashable (convert lists to tuples). Deep memoized recursion still hits the recursion limit.

## 6. Recursion Limit

```python
import sys
sys.setrecursionlimit(10**6)   # raises Python's limit, not the C stack; can still segfault
```
Safer: write DFS iteratively with an explicit stack when depth can exceed ~1000 (degenerate trees, long paths, big grids).

The iterative version replaces the call stack with a list you control. It has no
depth limit and is the default for grid and graph DFS in Python:

```python
def count_reachable(graph, start):
    """Iterative DFS: graph is {node: [neighbours]}. Returns nodes reachable from start."""
    seen = {start}
    stack = [start]
    while stack:
        node = stack.pop()             # LIFO: depth-first
        for nxt in graph.get(node, ()):
            if nxt not in seen:
                seen.add(nxt)          # mark on push, so a node is stacked at most once
                stack.append(nxt)
    return len(seen)

chain = {i: [i + 1] for i in range(100_000)}   # recursive DFS would blow the default limit
print(count_reachable(chain, 0))               # 100001
```
Visit order differs from recursive DFS (neighbours come off the stack in reverse), which
matters only when the problem asks for a specific order: push neighbours in reverse to
match it.

## 7. Idioms That Make Interview Code Clean

```python
for i, x in enumerate(nums): ...
for a, b in zip(xs, ys): ...
DIRS = ((0, 1), (1, 0), (0, -1), (-1, 0))
for dr, dc in DIRS:
    r2, c2 = r + dr, c + dc
    if 0 <= r2 < rows and 0 <= c2 < cols: ...
best = max(best, cur)
a, b = b, a + b                     # tuple swap
nums.sort(key=lambda p: (p[0], -p[1]))
any(pred(x) for x in xs); all(...)
m = {v: i for i, v in enumerate(nums)}   # value -> index
count = sum(1 for x in xs if pred(x))
```

## 8. The Three Must-Write-Cold Implementations

### Dijkstra
```python
import heapq
from collections import defaultdict

def dijkstra(n, edges, src):
    graph = defaultdict(list)
    for u, v, w in edges:
        graph[u].append((v, w))
    dist = [float("inf")] * n
    dist[src] = 0
    heap = [(0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue                    # stale entry (lazy deletion)
        for v, w in graph[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return dist
```
Marking visited on **pop** (or the `d > dist[u]` check) is correct; finalizing on push is wrong because a shorter path may be discovered later. O((V + E) log V). Wrong with negative edges.

### LRU cache (hash map + doubly linked list)
```python
class Node:
    __slots__ = ("key", "val", "prev", "next")
    def __init__(self, key=0, val=0):
        self.key, self.val, self.prev, self.next = key, val, None, None

class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.map = {}
        self.head, self.tail = Node(), Node()      # sentinels: no edge cases
        self.head.next, self.tail.prev = self.tail, self.head

    def _remove(self, node):
        node.prev.next, node.next.prev = node.next, node.prev

    def _add_front(self, node):
        node.prev, node.next = self.head, self.head.next
        self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        node = self.map.get(key)
        if not node:
            return -1
        self._remove(node); self._add_front(node)
        return node.val

    def put(self, key: int, value: int) -> None:
        if key in self.map:
            self._remove(self.map[key])
        node = Node(key, value)
        self.map[key] = node
        self._add_front(node)
        if len(self.map) > self.cap:
            lru = self.tail.prev
            self._remove(lru)
            del self.map[lru.key]                  # why the node stores its key
```

### Trie
```python
class Trie:
    def __init__(self):
        self.root = {}

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            node = node.setdefault(ch, {})
        node["$"] = True                           # end-of-word marker

    def _walk(self, s: str):
        node = self.root
        for ch in s:
            if ch not in node:
                return None
            node = node[ch]
        return node

    def search(self, word: str) -> bool:
        node = self._walk(word)
        return node is not None and "$" in node

    def startsWith(self, prefix: str) -> bool:
        return self._walk(prefix) is not None
```

### Also be able to write cold
Union-Find (path compression + union by rank), Kahn's topological sort, binary search (section 4), BFS on a grid, quickselect, Fenwick tree. All are in the PyDSA topic folders with explanations; the readiness checklist in [Google Interview Master Study Plan (L5 / Senior SWE)](../../study-plans/GOOGLE_INTERVIEW_PREP.md) lists them.

### Two more worth writing cold: Union-Find and Kahn's topological sort
```python
from collections import deque

class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.components = n

    def find(self, x: int) -> int:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:              # path compression, iteratively
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False                           # already connected: an edge here closes a cycle
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra                       # union by rank
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        self.components -= 1
        return True

def topo_sort(n: int, edges: list[tuple[int, int]]) -> list[int]:
    """Kahn's algorithm. edges are (u, v) meaning u must come before v. [] if there is a cycle."""
    graph = [[] for _ in range(n)]
    indegree = [0] * n
    for u, v in edges:
        graph[u].append(v)
        indegree[v] += 1
    q = deque(i for i in range(n) if indegree[i] == 0)
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in graph[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                q.append(v)
    return order if len(order) == n else []       # leftover nodes sit on a cycle

uf = UnionFind(5)
uf.union(0, 1); uf.union(3, 4)
assert uf.components == 3 and uf.find(1) == uf.find(0) and not uf.union(1, 0)
assert topo_sort(4, [(0, 1), (1, 2), (0, 3)]) == [0, 1, 3, 2]
assert topo_sort(2, [(0, 1), (1, 0)]) == []
```
Union-Find with both optimisations is O(α(n)) amortized per operation, effectively
constant. Kahn's is O(V + E), and "fewer than n nodes came out" is the cycle test.

## 9. Python Traps Interviewers Notice

| Trap | Example | Fix |
|---|---|---|
| Mutable default argument | `def f(path=[])` shared across calls | `def f(path=None): path = path or []` |
| Shared inner lists | `[[0] * m] * n` | list comprehension |
| Closure late binding | `[lambda: i for i in range(3)]` all return 2 | default arg `lambda i=i: i` |
| Appending a reference in backtracking | `res.append(path)` then mutating `path` | `res.append(path[:])` |
| `is` vs `==` | `a is 1000` | use `==` for values |
| Modifying a dict/set while iterating | RuntimeError | iterate over `list(d)` |
| Integer division sign | `-3 // 2 == -2` | know which rounding the problem wants |
| `@cache` across test cases | stale results | `cache_clear()` or define inside the method |
| Recursion depth | RecursionError at ~1000 | iterative stack |
| `sort()` returns None | `x = a.sort()` | `sorted(a)` |

## 10. Writing Without an IDE

The plan's second foundation: at least one round is in person or in a plain doc.
- Practice in a plain text editor with no autocomplete and no running code; then run it and count the bugs.
- Mastery check: three problems written in a plain doc that run correctly on the first try.
- Habits that prevent bugs without a compiler: name helpers for every sub-idea (`in_bounds`, `neighbors`), write the function signature and a one-line contract first, use consistent 4-space indentation, trace one example by hand before saying "done."

## What Each Engineering Level Should Know

The coding bar in a Python interview does not rise forever with level: from Senior
upward, the *code* is expected to be about equally fluent, and the extra signal comes
from judgment (choosing the right structure without prompting, spotting production
concerns, explaining the cost model). This table maps the chapter onto a standard
industry ladder and the Google-style ladder side by side. The title-to-level mapping
is approximate and varies by company; the depth described in each cell is the useful
part. Read down a column as a syllabus, or find the cell that matches you as a
self-assessment.

| Topic in this chapter | Junior / New Grad (Google L3) | Mid-Level (Google L4) | Senior (Google L5) | Staff+ (Google L6–L7) |
|---|---|---|---|---|
| **Interpreter & object model** (Foundations) | Knows Python is interpreted and slower per step than compiled languages | Knows names are references and can explain the `[[0] * m] * n` bug | Explains mutability, hashability and shallow vs deep copy precisely, and why built-ins beat hand-written loops | Reasons about CPython costs in production code (allocation churn, the GIL and the free-threaded build, when to drop to C/Rust or vectorise) |
| **Built-in types & costs** (§1) | Uses `list`, `dict`, `set` correctly; knows `in` on a list is slow | States the cost of every common operation, including `pop(0)`, slicing and string `+=` | Knows sort stability and `key=` semantics, and picks the structure from the operations the problem needs before coding | Spots accidental quadratic behaviour in a code review from the data structures alone |
| **`collections`, `heapq`, `bisect`** (§2–§4) | Has used `Counter` and `deque` | Uses `heapq` with tuples, `defaultdict` for graphs, `bisect` for lookups | Uses lazy deletion, tie-breaker counters and `bisect_left` vs `bisect_right` without hesitation; knows the stdlib has no ordered map and what to do instead | Chooses between a heap, a sorted list and a third-party structure based on real update/query ratios and dependency policy |
| **`itertools`, `functools`, recursion** (§5–§6) | Writes recursive solutions; may hit the recursion limit | Uses `@cache` for memoization; knows the default limit (~1000) | Converts recursion to an explicit stack when depth can exceed the limit; clears caches between test cases | Knows when memoization's memory cost outweighs its benefit and designs the iterative DP instead |
| **Must-write-cold implementations** (§8) | Can write BFS and binary search with some lookups | Writes Dijkstra and an LRU cache correctly with a little debugging | Writes Dijkstra, LRU, trie, Union-Find and Kahn's cold, in minutes, with correct complexity and edge cases | Same fluency, plus the follow-ups: thread safety, sharding, TTLs ([Google-Style Follow-Ups — Scaling a Coding Answer](10_google_follow_ups_deep_dive.md)) |
| **Traps & writing without an IDE** (§9–§10) | Hits several traps and finds them by running the code | Avoids most traps; finds the rest by tracing | Avoids all ten automatically and produces code that runs first time from a plain doc | Writes code others can review and extend: clear helpers, contracts, and tests described up front |

**Reading this table as a study plan:** for a Senior/L5 loop, the target is the whole
Senior column, which sections 1–10 cover completely. The Staff+ column is mostly the
same code with more production judgment; in practice Staff loops shift weight from
coding to system design, so don't over-invest here at the expense of `content/interview-core/SystemDesign/`.

## Interview checklist

- [ ] I know the complexity of every operation in sections 1–5 without looking.
- [ ] I can write Dijkstra, LRU cache, and trie cold in under 15 minutes each.
- [ ] I can explain `bisect_left` vs `bisect_right` with a duplicate example.
- [ ] I avoid all ten traps in section 9 automatically.
- [ ] I can explain what CPython does with my source (bytecode, interpreter loop, heap objects) and why built-ins beat equivalent hand-written loops.
- [ ] I can explain names vs objects, mutability and hashability, and use that to explain three of the traps in section 9.
- [ ] I can map every structure in `06` to its Python tool, and say what to do given there is no built-in ordered map.
- [ ] I can explain sort stability, and write Union-Find and Kahn's topological sort cold.

Related: [Data Structure Internals](06_data_structure_internals_deep_dive.md), [Complexity Analysis](07_complexity_analysis_deep_dive.md), [Running the 45-Minute Coding Round](09_coding_round_execution_deep_dive.md), `content/languages/PyEngineering/`, `content/languages/PyStdLib/`.
