# Topic 01 · Arrays & Hashing — Python Deep Dive

> Read this before touching a single problem in this folder. Roughly 40% of all
> interview problems reduce to "put it in a dict and look it up," and you cannot
> reason about the complexity of that move without knowing what CPython is
> actually doing underneath.

---

## Part 1 · The Array (Python `list`)

### 1.1 What a `list` actually is

Python's `list` is **not** a linked list. It is a *dynamic array*: a contiguous block
of memory holding **pointers to objects**, plus a length and a capacity.

In CPython (`Include/cpython/listobject.h`) the struct is:

```c
typedef struct {
    PyObject_VAR_HEAD        /* refcount, type pointer, and ob_size == len()  */
    PyObject **ob_item;      /* pointer to the array of object POINTERS       */
    Py_ssize_t allocated;    /* capacity: how many slots are reserved          */
} PyListObject;
```

Three consequences you must internalize:

1. **`ob_item` stores pointers, not values.** A `list[int]` is an array of
   addresses, each pointing to a heap-allocated `PyLongObject` elsewhere in
   memory. This is why Python lists are memory-hungry and cache-unfriendly
   compared to a Go `[]int` or a C array — walking a list chases pointers all
   over the heap.
2. **`len()` is O(1).** It reads `ob_size` directly. It never counts.
3. **`allocated >= ob_size`.** The gap is deliberate slack so that `append` is
   usually free.

```
my_list = [10, 20, 30]

  PyListObject                 heap
  ┌───────────────┐           ┌──────────┐
  │ ob_size   = 3 │       ┌──►│ int 10   │
  │ allocated = 4 │       │   └──────────┘
  │ ob_item ──────┼──┐    │   ┌──────────┐
  └───────────────┘  │    │┌─►│ int 20   │
                     ▼    ││  └──────────┘
              ┌────┬────┬────┬────┐   ┌──────────┐
              │ ptr│ ptr│ ptr│ -- │┌─►│ int 30   │
              └──┬─┴──┬─┴──┬─┴────┘│  └──────────┘
                 └────┘    └───────┘
                                 ▲
                          one slot of unused
                          capacity (slack)
```

### 1.2 How `append` grows — and why it's O(1) *amortized*

When `ob_size == allocated`, CPython reallocates. The growth rule lives in
`list_resize()` in `Objects/listobject.c`:

```arch
%% caption: Amortized O(1): the expensive copy is rare, and each copy buys many cheap appends.
grid 230x110
node a "Append number 5" at 0,0 color=red sub="len 4, cap 4: FULL"
node b "Allocate bigger block" at 1,0 sub="over-allocate spare slots"
node c "Copy 4 references" at 2,0 sub="O(n), but rare"
node d "len 5, cap 8" at 2,1 color=green sub="3 free slots"
node e "Write into spare slot" at 0,1 sub="O(1) each"
a -> b : "resize"
b -> c
c -> d
d -> e : "next 3 appends"
e -> a : "full again"
```


```c
new_allocated = ((size_t)newsize + (newsize >> 3) + 6) & ~(size_t)3;
```

That is roughly **newsize * 1.125 + 6**, rounded to a multiple of 4 — a much
gentler growth factor than the 2x most languages use. The resulting capacity
sequence is:

```
0, 4, 8, 16, 25, 35, 46, 58, 72, 88, ...
```

**Why growing geometrically makes append O(1) amortized:** to reach n elements
you copy on resize only, and the total work copied is
`n/8 + n/8² + n/8³ + ... < n * (1/7)` — a convergent geometric series that is
**O(n) total** across n appends, hence **O(1) per append on average**.

> ⚠️ **Interview nuance worth saying out loud:** a *single* append can be O(n)
> when it triggers a realloc. It is O(1) *amortized*, not O(1) worst-case. If a
> problem has a hard per-operation latency bound, that distinction matters.

### 1.3 The complexity table you must know cold

| Operation | Complexity | Why |
|---|:--:|---|
| `lst[i]` read / write | **O(1)** | Pointer arithmetic: `ob_item + i` |
| `len(lst)` | **O(1)** | Reads `ob_size` |
| `lst.append(x)` | **O(1)** amortized | Slack capacity; occasional realloc |
| `lst.pop()` (from end) | **O(1)** | Just decrement `ob_size` |
| `lst.pop(0)` / `lst.insert(0, x)` | **O(n)** ⚠️ | Must `memmove` every later element |
| `lst.pop(i)` / `lst.insert(i, x)` | **O(n)** | Shifts the tail |
| `x in lst` | **O(n)** ⚠️ | Linear scan — this is the classic hidden O(n²) |
| `lst.remove(x)` | **O(n)** | Search, then shift |
| `lst.sort()` | **O(n log n)** | Timsort |
| `lst[a:b]` (slice) | **O(b-a)** | Copies pointers into a new list |
| `lst1 + lst2` | **O(n+m)** | Builds a new list |
| `min` / `max` / `sum` | **O(n)** | Full scan |
| `lst.reverse()` | **O(n)** | In-place pointer swap |

**The two lines that silently make your solution O(n²):**

```python
for x in data:
    if x in seen_list:      # ← O(n) inside an O(n) loop  ⇒ O(n²)
        ...

while queue:
    item = queue.pop(0)     # ← O(n) shift every iteration ⇒ O(n²)
```

Fix them with `set` and `collections.deque` respectively.

### 1.4 Timsort — the sort you get for free

`list.sort()` and `sorted()` use **Timsort**, a hybrid of merge sort and
insertion sort designed by Tim Peters for real-world (partially ordered) data.

- Scans for **runs** — already-ascending or already-descending stretches — and
  reverses descending ones in place.
- Extends short runs to a minimum length (32–64) using **binary insertion sort**.
- Merges runs with a stack discipline that maintains balance invariants, using
  **galloping mode** (exponential search) when one run consistently wins.

| | |
|---|---|
| Best case | **O(n)** — already sorted data is one run |
| Average / worst | **O(n log n)** |
| Space | **O(n)** |
| **Stable?** | **Yes** — equal elements keep their original relative order |

Stability is the property interviewers probe. It is what makes multi-key sorting
work by sorting on the least significant key first:

```python
people.sort(key=lambda p: p.age)    # secondary key first
people.sort(key=lambda p: p.name)   # primary key last; ties keep age order
```

`key=` is evaluated **once per element** (the decorate-sort-undecorate pattern),
so it is cheap. A `cmp` function would be called O(n log n) times — which is why
Python 3 removed it. Use `functools.cmp_to_key` only when a true comparator is
unavoidable (e.g. LeetCode 179, Largest Number).

### 1.5 Array techniques that recur constantly

**Prefix products / sums without division** (LC 238):
```python
# Two sweeps, O(1) extra space beyond the output.
res = [1] * n
pre = 1
for i in range(n):          # left-to-right: product of everything before i
    res[i] = pre
    pre *= nums[i]
post = 1
for i in range(n - 1, -1, -1):   # right-to-left: fold in everything after i
    res[i] *= post
    post *= nums[i]
```

**Index-as-hash / cyclic marking** (LC 448, 41) — when values are in `1..n`, the
array *is* the hash table. Mark presence by negating `nums[abs(v) - 1]`:
```python
for v in nums:
    i = abs(v) - 1
    if nums[i] > 0:
        nums[i] = -nums[i]      # "seen" flag stored in the sign bit
missing = [i + 1 for i, v in enumerate(nums) if v > 0]
```
This is how you hit the "O(1) extra space" constraint that rules out a set.

**Boyer–Moore majority vote** (LC 169) — O(n) time, O(1) space:
```python
count, candidate = 0, None
for v in nums:
    if count == 0:
        candidate = v
    count += 1 if v == candidate else -1
```

---

## Part 2 · The Hash Table (Python `dict` and `set`)

### 2.1 Hashing in one paragraph

A hash table converts a key into an integer (`hash(key)`), maps that integer to a
slot index (`hash & (table_size - 1)`), and stores the entry there. Lookup
repeats the computation and goes straight to the slot — **O(1) average**, no
scanning. The cost is that you need a strategy for when two keys land on the
same slot (a **collision**), and you must resize before the table gets too full.

### 2.2 What CPython actually does: open addressing + the compact layout

Most textbooks teach **separate chaining** (each slot holds a linked list).
**CPython does not do this.** It uses **open addressing**: on a collision it
probes for another slot in the same array.

```arch
%% caption: Insert and lookup follow the same probe sequence, so a key is always found where it was placed. Long probe chains are what turn O(1) into O(n).
grid 240x100
node k "key" at 1,0 shape=pill
node h "h = hash(key)" at 1,1
node i "i = h and mask" at 1,2 sub="first probe slot"
node q "Look at slot i" at 1,3 shape=diamond color=amber
node ins "Insert (key, value)" at 0,4 color=green
node upd "Found" at 1,4 color=green sub="read or overwrite value"
node p "Perturb" at 2,3 color=amber sub="pick the next slot"
k -> h -> i -> q
q -> ins : "empty"
q -> upd : "same hash and key =="
q:R -> p:L : "other key"
p:T -> q:T
```


Since Python 3.6 a dict is **two** structures — the "compact dict" design:

```
d = {"a": 1, "b": 2, "c": 3}

  indices  (sparse, small ints)      entries (dense, insertion-ordered)
  ┌────┬────┬────┬────┬────┬────┐    ┌──────────────────────────────┐
  │ -1 │  0 │ -1 │  2 │  1 │ -1 │  0 │ hash("a") │ "a" │ 1          │
  └────┴────┴────┴────┴────┴────┘    ├──────────────────────────────┤
     ▲                             1 │ hash("b") │ "b" │ 2          │
     │                               ├──────────────────────────────┤
  -1 = DKIX_EMPTY                  2 │ hash("c") │ "c" │ 3          │
                                     └──────────────────────────────┘
```

- The **indices** array is sparse and holds only small integers (int8 → int32 as
  the dict grows), so the wasted space is tiny.
- The **entries** array is dense and append-only, which is *why dicts preserve
  insertion order* — that ordering is an implementation artifact that became a
  language guarantee in Python 3.7.
- This layout cut dict memory by ~30% versus Python 3.5.

**Probing.** CPython's probe sequence is not linear — it is a perturbed recurrence
(`Objects/dictobject.c`):

```c
perturb >>= PERTURB_SHIFT;                 /* PERTURB_SHIFT == 5 */
i = (i * 5 + perturb + 1) & mask;
```

Mixing in the *high* bits of the hash (via `perturb`) avoids the primary
clustering that plain linear probing suffers from, while still touching nearby
cache lines early.

**Resizing.** CPython grows when the table is **2/3 full**, to
`used * 3` rounded up to a power of two. Growth is by powers of two so the
modulo becomes a bitmask (`& mask`) instead of a division.

### 2.3 The O(1) that is really "O(1) average"

| Operation | Average | Worst case |
|---|:--:|:--:|
| `d[k]` lookup | **O(1)** | O(n) |
| `d[k] = v` insert | **O(1)** amortized | O(n) |
| `del d[k]` | **O(1)** | O(n) |
| `k in d` | **O(1)** | O(n) |
| Iterate | O(n) | O(n) |

Worst case is O(n) when every key collides. In practice this only happens with
**adversarial input**, which is why CPython enables **hash randomization** by
default (`PYTHONHASHSEED`): `hash("abc")` differs between processes so an
attacker cannot pre-compute a colliding key set and DoS your service.

> ⚠️ Randomization applies to `str` and `bytes`, **not** to `int`.
> `hash(n) == n` for small ints — an interview-worthy detail, and the reason
> `{i * 2**20 for i in range(k)}` can degrade.

**In an interview, say "O(1) average" and name the worst case.** Saying a flat
"O(1)" is the single most common complexity error candidates make.

### 2.4 Hashability, `__hash__`, and `__eq__`

A key must be **hashable**: it needs `__hash__` and must be immutable enough that
its hash never changes while it is in a table.

```python
hash((1, 2))      # ✅ tuples of hashables are hashable
hash([1, 2])      # ❌ TypeError: unhashable type: 'list'
hash(frozenset()) # ✅  frozenset is; set is not
```

The contract binding the two dunders:

> **If `a == b` then `hash(a) == hash(b)`.** The converse need not hold.

Break it and your objects vanish inside dicts. When you define `__eq__` on a
class, Python sets `__hash__ = None` (making instances unhashable) unless you
define `__hash__` too — a deliberate guard against exactly this bug.

**The canonical interview trick — grouping by a canonical key** (LC 49):
```python
groups = defaultdict(list)
for word in words:
    key = tuple(sorted(word))          # O(k log k) — or:
    # counts = [0]*26; for c in word: counts[ord(c)-97] += 1
    # key = tuple(counts)              # O(k), better when k is large
    groups[key].append(word)
```
Anagrams share a canonical form, so the dict does the grouping for free.

### 2.5 `set` — the same machinery, no values

`set` is a hash table storing keys only. Same average O(1) membership, same
worst case.

| Operation | Complexity |
|---|:--:|
| `x in s` | O(1) avg |
| `s.add(x)` / `s.discard(x)` | O(1) avg |
| `a \| b` (union) | O(len(a) + len(b)) |
| `a & b` (intersection) | O(min(len(a), len(b))) |
| `a - b` (difference) | O(len(a)) |

> `set` does **not** guarantee insertion order (unlike `dict`). If you need
> ordered-unique, use `dict.fromkeys(items)`.

**The pattern that turns O(n²) into O(n)** (LC 128, Longest Consecutive Sequence):
```python
s = set(nums)
best = 0
for v in s:
    if v - 1 not in s:            # only start counting at a sequence HEAD
        length = 1
        while v + length in s:
            length += 1
        best = max(best, length)
```
The `v - 1 not in s` guard is the whole trick: without it you re-walk every
sequence from every member (O(n²)); with it each element is visited at most twice.

### 2.6 The `collections` toolkit

```python
from collections import Counter, defaultdict, deque, OrderedDict
```

| Type | Use it for | Note |
|---|---|---|
| `Counter` | Frequency maps | `Counter(s)`, `.most_common(k)` (a heap, O(n log k)) |
| `defaultdict(list)` | Grouping without `if key not in d` | Missing key auto-creates |
| `deque` | Queues, sliding-window maxima | **O(1) `popleft()`** — a list's is O(n) |
| `OrderedDict` | <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr> caches | `.move_to_end()`, `.popitem(last=False)` |

`Counter` comparison is a one-line anagram check: `Counter(a) == Counter(b)`.
Interviewers often want the manual `dict` version too — know both.

---

## Part 3 · Choosing the Structure

```arch
%% caption: Which container fits the question being asked.
grid 270x100
node q "What do you need from the data?" at 1,0 shape=pill
node a "Only: have I seen this before?" at 1,1 shape=diamond color=amber
node s "set" at 2,1 color=green sub="O(1) membership"
node b "A value or count per key?" at 1,2 shape=diamond color=amber
node c "Counter" at 0,2 color=green
node d "dict" at 2,2 sub="or defaultdict" color=green
node e "Position or order matters?" at 1,3 shape=diamond color=amber
node f "list" at 0,4 color=green
node g "Sort once, then bisect" at 1,4 color=green
node hh "heap" at 2,4 color=green
q -> a
a -> s : "yes"
a -> b : "no"
b -> c : "count"
b -> d : "lookup or group"
b -> e : "neither"
e -> f : "by index"
e -> g : "sorted order, ranges"
e -> hh : "repeated min or max"
```


```
Need index/position access?  ─────────────► list
Need "have I seen this?"     ─────────────► set
Need "what maps to what?"    ─────────────► dict
Need counts?                 ─────────────► Counter
Need FIFO / both ends?       ─────────────► deque
Need sorted + fast insert?   ─────────────► heapq, or keep a list + bisect
Need O(1) space on 1..n data?─────────────► index-as-hash (sign marking)
```

**Space-time tradeoff, stated for interviews:** a hash map buys O(1) lookup with
O(n) extra memory. When the interviewer adds "now do it in O(1) space," they are
removing the hash map — pivot to sorting (O(n log n), reorders input), two
pointers, or index-as-hash.

---

## Part 4 · Algorithms Owned by This Topic

| Algorithm | Time | Space | Problem |
|---|:--:|:--:|---|
| Linear scan / single pass | O(n) | O(1) | Nearly all Easy array problems |
| Hash-map complement lookup | O(n) | O(n) | LC 1 Two Sum |
| Frequency counting | O(n) | O(k) | LC 242, 383 |
| Canonical-key grouping | O(n·k) | O(n·k) | LC 49 Group Anagrams |
| Bucket sort by frequency | O(n) | O(n) | LC 347 Top K Frequent |
| Prefix/suffix product sweep | O(n) | O(1)* | LC 238 |
| Index-as-hash sign marking | O(n) | O(1) | LC 41, 448 |
| Boyer–Moore majority vote | O(n) | O(1) | LC 169 |
| Set-based sequence walk | O(n) | O(n) | LC 128 |
| Timsort | O(n log n) | O(n) | Any "sort first" solution |

\* excluding the output array

**Bucket sort deserves its own note** (LC 347). Counting frequencies gives values
in `1..n`, so you can index an array *by frequency* and read it back descending —
**O(n)**, beating the O(n log n) sort and the O(n log k) heap:

```python
freq = Counter(nums)
buckets = [[] for _ in range(len(nums) + 1)]   # index == frequency
for val, count in freq.items():
    buckets[count].append(val)
res = []
for count in range(len(buckets) - 1, 0, -1):
    for val in buckets[count]:
        res.append(val)
        if len(res) == k:
            return res
```

---

## Part 5 · Building a Hash Map From Scratch

You will be asked this (LC 706). Separate chaining is the version to write —
it is far easier to get right under pressure than open addressing.

```python
class MyHashMap:
    def __init__(self, capacity: int = 1024):
        self.capacity = capacity
        self.size = 0
        self.buckets: list[list[tuple[int, int]]] = [[] for _ in range(capacity)]

    def _index(self, key: int) -> int:
        return hash(key) % self.capacity        # real impl: & (capacity - 1)

    def put(self, key: int, value: int) -> None:
        bucket = self.buckets[self._index(key)]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)        # overwrite existing
                return
        bucket.append((key, value))
        self.size += 1
        if self.size / self.capacity > 0.75:    # load factor threshold
            self._resize()

    def get(self, key: int) -> int:
        for k, v in self.buckets[self._index(key)]:
            if k == key:
                return v
        return -1

    def remove(self, key: int) -> None:
        bucket = self.buckets[self._index(key)]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket.pop(i)
                self.size -= 1
                return

    def _resize(self) -> None:
        old = self.buckets
        self.capacity *= 2
        self.buckets = [[] for _ in range(self.capacity)]
        self.size = 0
        for bucket in old:                      # rehash everything
            for k, v in bucket:
                self.put(k, v)
```

**Points to state while writing it:** the load factor (0.75) is the time-space
dial; resizing is O(n) but amortizes to O(1) per insert; and every key must be
rehashed on resize because the index depends on `capacity`.

---

<!-- block:01_py_1_traps -->
## Part 6 · The Traps That Live in This Topic

Every bug below is **silent** — no exception, just a wrong answer. Each one was reproduced on
CPython 3.13 while writing this section.

### 6.1 Aliasing: one list, many names

```python
grid = [[0] * 3] * 2                 # ❌ two references to ONE row
grid[0][0] = 1                       # [[1, 0, 0], [1, 0, 0]]

grid = [[0] * 3 for _ in range(2)]   # ✅ a fresh row per iteration
```

`[x] * n` copies the *reference* `n` times. That is harmless for ints and strings (immutable) and
fatal for lists and dicts. It is the same root cause as `a = b = []`, as a mutable default argument
(`def f(acc=[])`), and as `b = a[:]` on a nested list — a *shallow* copy makes a new outer list that
still shares every inner row. Use `[row[:] for row in a]` or `copy.deepcopy(a)`.

### 6.2 Mutating while you iterate

| Container | What happens | Why |
|---|---|---|
| `dict` / `set` | `RuntimeError: dictionary changed size during iteration` | The iterator checks the size on every step — loud and safe. Changing the *value* of an existing key is allowed. |
| `list` | **Silently skips elements** | The iterator holds a hidden index. Removing shifts the tail left, then the index advances past the element that slid into the gap. |

```python
lst = [1, 2, 2, 3]
for x in lst:
    if x == 2:
        lst.remove(x)
# lst == [1, 2, 3]  — one of the 2s survived
```

Build a new list (`[x for x in lst if x != 2]`), iterate a snapshot (`for x in list(lst)`), or use a
write index (Remove Element, topic 02).

### 6.3 Keys that are "equal" are the same key

```python
{1: "a", 1.0: "b", True: "c"}        # {1: 'c'}  — ONE entry
```

`1 == 1.0 == True` and they hash the same, so the dict treats them as a single key: the **first key
object is kept, the last value wins**. It bites when keys come from mixed sources (<abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> numbers, a
`bool` column, a `Counter` over mixed data).

`float("nan")` is stranger: `nan != nan`, yet `{nan: 1}[nan]` succeeds, because CPython compares
*identity* before equality. A *different* NaN object is never found. (And `hash(-1) == hash(-2) == -2`,
because `-1` is reserved as an error value in the C code.)

### 6.4 Reads that write — and arithmetic that deletes

```python
from collections import Counter, defaultdict

d = defaultdict(int)
if d["x"]: ...          # ❌ the READ inserted d["x"] = 0.  Use `"x" in d` or d.get("x").

c = Counter("aab")
c["z"]                  # 0 — and z is NOT inserted (Counter is the opposite of defaultdict)

Counter(a=3, b=1) - Counter(a=1, b=5)   # Counter({'a': 2})  — b vanished, not -4
```

`Counter` `+` and `-` **drop every entry whose count is ≤ 0**. That is exactly what you want for
"does the magazine cover the ransom note" (`not (need - have)`), and exactly what you do *not* want
if you need the negative counts — use `.subtract()` for that.

### 6.5 `sort()` returns `None`

```python
nums = nums.sort()      # ❌ nums is now None
nums.sort()             # ✅ in place, returns None
ordered = sorted(nums)  # ✅ a new list, input untouched
```

`sorted()` accepts any iterable and always returns a list; `.sort()` exists only on lists. If the
problem says "do not modify the input", reach for `sorted`.

### 6.6 String building

`s += ch` inside a loop *looks* linear on CPython, because the interpreter can grow the string in
place when nothing else references it. That is an implementation detail, not a language guarantee —
it disappears the moment the string has a second reference, and other interpreters do not do it. The
answer that is always O(n) is to collect pieces in a list and `"".join(pieces)` once.

---
<!-- /block:01_py_1_traps -->

<!-- block:01_py_2_followups -->
## Part 7 · Follow-ups the Interviewer Reaches For

The first solution is rarely the last question. These are the standard escalations for this topic
and the shape of the answer to each.

| Follow-up | What changes | The answer |
|---|---|---|
| "The data does not fit in memory." | You cannot hold one big map. | **Hash-partition**: send each item to file `hash(x) % k`, so equal items land together, then process one partition at a time. For *approximate* answers: a Bloom filter (membership, never a false negative) or a Count-Min sketch (frequency, only ever over-counts). |
| "It is a stream — you see each item once." | No sorting, no second pass. | Keep the set/counter incrementally. Boyer–Moore generalises to **Misra–Gries**: `k − 1` counters find every element that occurs more than `n/k` times (Boyer–Moore is `k = 2`). |
| "The array is already sorted." | Order is free information. | Drop the hash map: two pointers in O(1) space (topic 02) or binary search (topic 05). |
| "Now in O(1) extra space." | The map is forbidden. | Sort in place (O(n log n), reorders the input), index-as-hash when values are `1..n`, or a write-index pass. |
| "Implement the hash map yourself." | You own the internals. | Part 5: chaining, a power-of-two capacity, a load-factor threshold, and a full rehash on resize. Open addressing needs tombstones for deletes. |
| "Keys are adversarial." | Hash flooding turns O(1) into O(n). | CPython randomises `str`/`bytes` hashes per process (`PYTHONHASHSEED`) but **not** `int` hashes; Java falls back to tree bins. State the mitigation, not just the risk. |
| "Not just `a–z`." | The 26-slot array breaks. | Use a `dict`/`Counter`. For Unicode also ask about **normalisation**: `"é"` can be one code point or two (`e` + combining accent) and compare unequal. |
| "Return all pairs / all groups." | Output size dominates. | Say the complexity in terms of the output as well as the input. |
| "Can the same element be used twice?" | Changes the check order. | Look up the complement *before* inserting the current value; otherwise `[3]`, target `6` returns a pair of one element. |

---
<!-- /block:01_py_2_followups -->

<!-- problem-map:start -->
## Part 8 · Every Problem in This Topic, by Pattern

Fourteen problems, seven moves. The number is the folder sequence — open any problem from the pattern page. Read the last column *before* you code: each trap is one the tests in that problem's solution file actually trigger.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Concatenation of Array](PyDSA/01_arrays_hashing/001_concatenation_of_array_solution.py) <br>LC 1929 · Easy | Preallocate + index map | The output length is known (2n), so fill `ans[j] = nums[j % n]` instead of growing by guessing; the modulo view generalises to "repeat k times" and circular arrays. **Trap:** `ans = nums` then `ans.extend(nums)` mutates the caller's list — both names are one object. |
| [002 · Contains Duplicate](PyDSA/01_arrays_hashing/002_contains_duplicate_solution.py) <br>LC 217 · Easy | Seen-set | One repeated question — "have I seen this?" — answered by a hash set: O(n²) becomes O(n). **Trap:** a `list` for `seen` (a silent O(n²)), or adding before checking (always `True` on the first element). |
| [003 · Valid Anagram](PyDSA/01_arrays_hashing/003_valid_anagram_solution.py) <br>LC 242 · Easy | Frequency count | An anagram is an identical character *multiset*, so counts matter, not membership. Compare two `Counter`s, or count up and down after a length check. **Trap:** `set(s) == set(t)` calls `"aacc"`/`"ccac"` anagrams; skipping the length check lets `"ab"`/`"a"` drain cleanly to `True`. |
| [004 · Two Sum](PyDSA/01_arrays_hashing/004_two_sum_solution.py) <br>LC 1 · Easy | Complement lookup | Fix `nums[i]` and the partner is forced (`target - nums[i]`), so the pair search collapses to one map lookup. **Trap:** inserting before checking lets an element pair with itself; returning values when the problem wants indices. |
| [005 · Majority Element](PyDSA/01_arrays_hashing/005_majority_element_solution.py) <br>LC 169 · Easy | Boyer–Moore vote | The majority (> n/2) outnumbers everything else combined, so pairwise cancellation leaves it standing — O(n) time, O(1) space. **Trap:** returning `count` instead of `candidate`; adopting a candidate only once instead of every time the count hits 0 (`[6, 5, 5]`). |
| [006 · Find All Numbers Disappeared in an Array](PyDSA/01_arrays_hashing/006_find_all_numbers_disappeared_in_an_array_solution.py) <br>LC 448 · Easy | Index-as-hash | Values live in `1..n`, so slot `v-1` is value `v`'s home: mark presence with the sign bit, then read off the slots that stayed positive. **Trap:** forgetting `abs()` (Python silently indexes from the end), and negating unconditionally so a duplicate flips a slot back. |
| [007 · Group Anagrams](PyDSA/01_arrays_hashing/007_group_anagrams_solution.py) <br>LC 49 · Medium | Canonical-key grouping | Grouping by a property means hashing by a form that every group member shares: *canonical key → `defaultdict(list)` → `.values()`*. **Trap:** a list as the key (`unhashable type`) — use `tuple(counts)` or `"".join(sorted(s))`. |
| [008 · Top K Frequent Elements](PyDSA/01_arrays_hashing/008_top_k_frequent_elements_solution.py) <br>LC 347 · Medium | Bucket by frequency | A frequency is a bounded integer in `[1, n]`, so index an array *by frequency* — O(n) beats the O(n log n) sort and the O(n log k) heap. **Trap:** sizing the buckets `len(nums)` (needs `len(nums) + 1`); pushing every item on a heap, which is just a rewritten sort. |
| [009 · Encode and Decode Strings](PyDSA/01_arrays_hashing/009_encode_and_decode_strings_solution.py) <br>LC 271 · Medium | Length-prefix framing | No delimiter is safe when the data may contain every byte, so say *how long* the payload is, then say it: `"4#neet"`. The decoder jumps past payloads without ever scanning them. **Trap:** `"#".join` / `split` breaks on data containing `#` and cannot tell `[]` from `[""]`. |
| [010 · Product of Array Except Self](PyDSA/01_arrays_hashing/010_product_of_array_except_self_solution.py) <br>LC 238 · Medium | Prefix × suffix sweep | `answer[i] = (product left of i) × (product right of i)` — `nums[i]` is excluded by construction, so "no division" becomes a hint. **Trap:** starting the running product at 0 (the empty product is 1); updating the runner *before* writing, so the prefix includes `nums[i]`. |
| [011 · Valid Sudoku](PyDSA/01_arrays_hashing/011_valid_sudoku_solution.py) <br>LC 36 · Medium | Set-per-group check | Every cell belongs to exactly three groups (row, column, box); one pass with 27 sets is Contains Duplicate wearing a costume. **Trap:** `r % 3` instead of `r // 3` in the box index — it mixes distant boxes yet passes many boards. |
| [012 · Longest Consecutive Sequence](PyDSA/01_arrays_hashing/012_longest_consecutive_sequence_solution.py) <br>LC 128 · Medium | Set + sequence heads | A set makes "what comes next?" O(1); the whole trick is walking only from a *head* (`x - 1 not in seen`). **Trap:** omit the guard and it is still correct but O(n²) — invisible on small tests, a hang on `[1..100000]`; `max()` of an empty input raises. |
| [013 · Next Permutation](PyDSA/01_arrays_hashing/013_next_permutation_solution.py) <br>LC 31 · Medium | Right-to-left scan | The next arrangement changes digits as far *right* as possible: find the pivot, swap with the smallest bigger tail value, reverse the (decreasing) tail. **Trap:** a non-strict comparison swaps equal values and `[1, 2, 1]` goes *backwards*; sorting the tail is right but hides that you understood it. |
| [014 · Isomorphic Strings](PyDSA/01_arrays_hashing/014_isomorphic_strings_solution.py) <br>LC 205 · Easy | Bijection = two maps | Isomorphism needs `s→t` *and* `t→s`; the reusable idea is the *shape key* (replace each char with the index of its first occurrence). **Trap:** one map accepts `"badc"`/`"baba"`; comparing set sizes alone accepts `"aab"`/`"abb"`. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] Explain why `append` is O(1) *amortized* and not O(1)
- [ ] Explain why `lst.pop(0)` is O(n) and what to use instead
- [ ] Explain open addressing vs. chaining, and which CPython uses
- [ ] State dict lookup as "O(1) average, O(n) worst" without prompting
- [ ] Explain why dicts are insertion-ordered since 3.7
- [ ] State the `__eq__`/`__hash__` contract
- [ ] Write a hash map from scratch with resizing in under 15 minutes
- [ ] Know when the interviewer's "O(1) space" removes your hash map, and what replaces it
- [ ] Spot `[[0] * n] * m` and mutation-while-iterating on sight, and say what each does <!--ca-->
- [ ] Explain why `1`, `1.0` and `True` are one dict key <!--ca-->
- [ ] Say what "doesn't fit in memory" and "it's a stream" change about the solution <!--ca-->
- [ ] Pick the right row of the problem table above from the *wording* of a statement, before coding <!--ca-->

---

## Part 9 · Added Problems (013–014) — two patterns the original twelve didn't cover

Added 16 Sep 2026 to close gaps against the Google prep plan.

### 013 Next Permutation — the right-to-left scan

The array is treated as a number. The smallest bigger arrangement changes digits as far RIGHT as
possible, so every step scans from the right:

```
pivot    rightmost i with nums[i] < nums[i+1]     (the tail after i is decreasing)
swap     rightmost j with nums[j] > nums[i]        (smallest tail value bigger than the pivot)
reverse  nums[i+1:]                                (decreasing -> increasing, O(n), no sort)
```

The comparisons must be STRICT on both searches; with duplicates, a non-strict swap target swaps
equal values and the result goes backwards (`[1,2,1]` -> `[1,1,2]`). The solution file runs that bug.

### 014 Isomorphic Strings — a bijection needs two maps

"Consistent mapping" (one dict s->t) is only half the definition. The other half, "no two characters
map to the same character", needs the reverse dict t->s. One map returns True for `"badc"/"baba"`.

The reusable idea is the **shape key**: replace each character with the index of its first
occurrence (`"paper"` -> `[0,1,0,3,4]`). Equal shapes = isomorphic, and `tuple(shape)` is a dict key
for grouping many strings by structure — the same canonical-key trick as Group Anagrams (007).

### Checklist additions

- [ ] I can find the pivot, swap target, and reverse for Next Permutation, and say why reversing
      (not sorting) the tail is enough.
- [ ] I can explain why isomorphism needs both s->t and t->s, and give the shape-key alternative.
