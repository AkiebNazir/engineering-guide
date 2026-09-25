# Python for Coding Interviews — The Standard Library, Cold

This file is a reference, not a narrative read: dip into whichever section you need.
If `O(1)`/`O(n)` or "hash map" feel unfamiliar, read `07_complexity_analysis_deep_dive.md`
and `06_data_structure_internals_deep_dive.md` first — this file assumes that
vocabulary and turns it into exact Python tool choices. Python is this curriculum's
interview language. The plan's mastery check: **write Dijkstra, an <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr> cache, and a
trie in a plain doc with zero syntax lookups.** This file is the complete toolkit,
with the complexity and the traps for each tool. Every snippet here runs on Python
3.10+ (verified on 3.13).

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
Safer: write <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> iteratively with an explicit stack when depth can exceed ~1000 (degenerate trees, long paths, big grids).

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

### <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr> cache (hash map + doubly linked list)
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
Union-Find (path compression + union by rank), Kahn's topological sort, binary search (section 4), <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> on a grid, quickselect, Fenwick tree. All are in the PyDSA topic folders with explanations; the readiness checklist in `GOOGLE_INTERVIEW_PREP.md` lists them.

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

## 10. Writing Without an <abbr title="Integrated Development Environment. A software application that provides comprehensive facilities to computer programmers for software development.">IDE</abbr>

The plan's second foundation: at least one round is in person or in a plain doc.
- Practice in a plain text editor with no autocomplete and no running code; then run it and count the bugs.
- Mastery check: three problems written in a plain doc that run correctly on the first try.
- Habits that prevent bugs without a compiler: name helpers for every sub-idea (`in_bounds`, `neighbors`), write the function signature and a one-line contract first, use consistent 4-space indentation, trace one example by hand before saying "done."

## Checklist

- [ ] I know the complexity of every operation in sections 1–5 without looking.
- [ ] I can write Dijkstra, <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr> cache, and trie cold in under 15 minutes each.
- [ ] I can explain `bisect_left` vs `bisect_right` with a duplicate example.
- [ ] I avoid all ten traps in section 9 automatically.
