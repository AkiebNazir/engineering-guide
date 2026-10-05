# Data Structure Internals — What Actually Happens Under the API

Every data structure you reach for by habit — a list, a dict, a heap — is a small
piece of engineering with real trade-offs baked in, not a black box that's simply
"fast." This chapter starts from first principles — what a data structure is, what
it is made of, and why memory layout decides so much — then goes as deep as a
standard Google interview question expects: "how does a hash map work under the
hood?" needs an answer that goes past "an array of buckets." It covers the structures
you use every day, how real runtimes implement them (CPython, Go, Java), two you'll
build from scratch and test (a hash map and a heap), measured costs (probe lengths,
memory per item, cache locality), and the performance consequences you can mention
in a coding round. Corrections of common myths are marked **Precision note**. A
side-by-side breakdown of what Junior through Staff+ engineers are expected to know
closes out the chapter, just before the interview checklist.

## Foundations — What Is a Data Structure, and How Does It Work?

### Why Data Structures Exist

To the hardware, memory is one long numbered row of bytes. You can read or write any
byte if you know its address, and that's all. Everything else — "a list of users",
"a map from name to phone number", "the task with the earliest deadline" — is an
arrangement *you* impose on that row of bytes, plus rules for how to use it.

The arrangement matters because the same question can be cheap or ruinously expensive
depending on it. "Is Alice in here?" on a million unsorted names means looking at up
to a million entries. On the same names in a hash table, it's a handful of memory
reads. On the same names sorted, it's about 20 comparisons (binary search). Nothing
about the data changed; only the arrangement did. A **data structure** is a chosen
arrangement that makes the operations you need cheap, at the price of making others
more expensive or using more memory.

### What a Data Structure Actually Is

It helps to separate two layers that everyday speech blurs together:

- **The abstract data type (ADT)** is the *contract*: which operations exist and what
  they mean. "A **map** lets you `put(key, value)`, `get(key)` and `delete(key)`."
  "A **priority queue** lets you `push(item)` and `pop()` the smallest." It says
  nothing about how.
- **The implementation** is the *mechanism*: the memory layout plus the algorithms
  that keep it valid. A map can be implemented as a hash table (Python `dict`) or a
  balanced tree (Java `TreeMap`); a priority queue as a binary heap (`heapq`) or a
  sorted list. Same contract, very different costs.

Every implementation keeps an **invariant** — a rule that is true between operations
and that the operations rely on. A binary heap's invariant is "every parent ≤ its
children"; a hash table's is "every key sits somewhere along its own probe path";
a balanced tree's is a bound on its height. Each operation is "do the change, then
repair the invariant", and the repair is where the cost lives (§1, §5, §6).

**What "Big-O" means here, in one sentence.** `O(1)`, `O(n)`, `O(log n)` describe how
an operation's cost grows with the amount of data `n`: `O(1)` means "roughly the same
cost no matter how much data," `O(n)` means "grows in proportion to the data," and
`O(log n)` sits far closer to `O(1)` than to `O(n)` (about 20 steps for a million
items). [Complexity Analysis](07_complexity_analysis_deep_dive.md) is the full treatment — read its
Foundations first if this is new.

### The Core Components of a Data Structure

Almost every structure in this file is assembled from the same handful of parts:

| Component | What it's responsible for | Covered deeper in |
|---|---|---|
| **Contiguous block** (array) | Values side by side in memory; position `i` is at `start + i × size`, so indexing is one calculation | §2, §5, §13 |
| **Pointers / references** | One piece of memory storing the address of another: linked lists, tree nodes, and every Python object reference | §4, §6, §13 |
| **Hash function** | Turns a key into a number, so a key can be turned directly into a position | §1, §10, §11 |
| **Invariant + repair** | The rule the structure keeps (heap order, BST order, balance) and the work to restore it after each change | §5, §6, §12 |
| **Growth policy** | What happens when the block is full: allocate a bigger one and copy, by a *factor* so the copying averages out | §1, §2 |
| **Metadata** | Lengths, capacities, colours, tombstones, per-slot control bytes that make the operations possible | §1, §6, §10 |

### How the Pieces Fit Together

What you call in code is the ADT; underneath is an implementation; underneath that is
one of two memory layouts. Most of the performance surprises in this file come from
the bottom row:

```arch
%% caption: You program against an abstract type; a runtime picks an implementation; each implementation is ultimately either one contiguous block or nodes linked by pointers.
grid 170x115
group adt "Abstract types: what you can ask" color=blue icon=code
node map "Map / Set" at 0,0 in adt shape=pill color=blue sub="put, get, delete"
node seq "Sequence" at 1,0 in adt shape=pill color=blue sub="index, append"
node pq "Priority queue" at 2,0 in adt shape=pill color=blue sub="push, pop-min"
node om "Ordered map" at 3,0 in adt shape=pill color=blue sub="floor, range scan"
group impl "Implementations: how it's built" color=purple icon=layers
node ht "Hash table" at 0,1 in impl icon=kv sub="§1, §10"
node da "Dynamic array" at 1,1 in impl icon=table sub="§2"
node bh "Binary heap" at 2,1 in impl icon=tree sub="§5, §12"
node bt "Balanced tree" at 3,1 in impl icon=tree sub="§6"
group mem "Memory layout" color=slate icon=memory
node blk "Contiguous block" at 1,2 in mem icon=memory sub="cache-friendly"
node lnk "Linked nodes" at 3,2 in mem icon=link sub="pointer chasing"
map -> ht
seq -> da
pq -> bh
om -> bt
ht -> blk
da -> blk
bh -> blk
bt -> lnk
```

A hash table, a dynamic array and a binary heap are all "a contiguous block plus
arithmetic" underneath, which is why they're fast in practice; trees and linked lists
are "nodes plus pointers", which buys flexibility (cheap splicing, ordered traversal)
at the price of following one pointer per step. B-trees (§6) are the compromise: a
tree whose nodes are themselves wide contiguous blocks.

### Why Memory Layout Matters as Much as Big-O

A CPU core doesn't fetch single bytes from RAM; it fetches whole **cache lines**
(64 bytes on x86 and most ARM servers) into small, fast caches, and a trip to RAM
costs on the order of 100 ns, versus about a nanosecond for a value already in L1
(approximate, commonly cited figures; see [Operating Systems & Hardware Symbiosis](01_operating_systems_deep_dive.md) §2).
Two consequences follow:

- **Scanning a contiguous array is close to the best case.** Each cache line brings
  the next several elements along for free, and the hardware prefetcher sees the
  pattern and fetches ahead.
- **Following pointers to nodes scattered around the heap is close to the worst
  case.** Each step may be a cache miss, and the next address isn't known until the
  current load finishes, so nothing can be fetched ahead.

Two structures with the same Big-O can therefore differ by one to two orders of
magnitude in wall-clock time. §13 measures exactly this.

**Try it: the same loop in two orders.** The matrix below is stored row by row. Run the row-order loop, then the column-order loop with a 4-line cache, then grow the cache to 8 lines. The Big-O never changes (64 accesses every time) but the hit rate goes from 75% to 0% and back to 75%. That gap is what “memory layout matters as much as Big-O” means.

<div class="lab" data-viz="cs-locality"></div>

### The Three Basic Shapes, in One Table

Nearly every structure in this file is a variation on one of these:

| Shape | What it looks like | Strength | Weakness |
|---|---|---|---|
| **Array** (Python `list`, Go slice) | Values sitting next to each other in memory, accessed by position | Instant access by index (`O(1)`); very cache-friendly | Inserting/removing in the middle means shifting everything (`O(n)`) |
| **Linked structure** (linked list, tree) | Each value points to the next (or to children) | Insert/remove is cheap *once you're at the right spot* | Finding that spot means following pointers one at a time — no jumping to "position 5" |
| **Hash map** (Python `dict`, Go `map`) | Values found by computing a number from the key, then jumping straight there | Near-instant lookup by key regardless of how much data (`O(1)` average) | No natural order; a bad key distribution can degrade this badly |

**Why a hash map's lookup is (usually) instant.** Instead of searching for a key, a
hash map runs it through a **hash function** — a calculation that turns any key into
a number — and uses that number to jump almost straight to where the value lives.
Compare that to an array, where finding a *value* (not an index) means checking
every slot one by one. §1 is the precise version: how that jump actually works, what
happens when two different keys hash to the same spot, and how real languages
implement it; §10 builds one.

**Why some operations that look free actually aren't.** An array's `append` is
usually instant, but "usually" is doing real work there — occasionally the array
runs out of room and the whole thing must be copied to a bigger block. §2 explains
why that occasional expensive copy still averages out to "cheap every time"
(**amortized** cost — also covered from the complexity side in `07` §6), and shows
CPython doing it.

### Vocabulary You'll Meet Below, in One Table

| Term | One-line meaning |
|---|---|
| ADT | The contract (operations and their meaning), independent of implementation |
| Invariant | A rule the structure keeps true between operations (heap order, balance) |
| Hash function | Maps a key to an integer; equal keys must give equal hashes |
| Collision | Two different keys landing on the same slot |
| Load factor | Entries ÷ slots in a hash table; higher saves memory but lengthens probes |
| Probe sequence | The order of slots an open-addressing table tries for a key |
| Tombstone | A "deleted" marker that keeps probe sequences intact |
| Capacity vs. length | Slots allocated vs. slots in use in a dynamic array |
| Amortized cost | Total cost of a sequence of operations ÷ number of operations |
| Cache line | The 64-byte unit a CPU cache moves; the reason contiguity is fast |
| Sift up / sift down | Moving a heap element toward the root / leaves to restore heap order |
| Rotation | Local pointer rearrangement that rebalances a search tree |

With those parts, the ADT/implementation split and the memory-layout rule in mind,
the rest of this chapter is the precise, implementation-level version: how CPython,
Go and Java actually build each structure, and the performance consequences worth
knowing.

## 1. Hash Maps

### The core mechanism
1. Compute `hash(key)` → an integer.
2. Map it to a slot: `index = hash & (capacity - 1)` (capacity a power of two) or `hash % capacity`.
3. Handle **collisions**, because different keys can land in the same slot.
4. When the table gets too full (the **load factor** threshold), allocate a bigger table and **rehash** every entry.

Average O(1) lookup relies on a good hash function and a bounded load factor. Worst case is O(n) when many keys collide.

```arch
%% caption: Hash map lookups compute an index, then probe slots until the key is found or an empty slot proves it is missing.
route straight
grid 160x140
node hash "hash('foo') % 4 = 1" at 1,0 shape=pill color=amber
group array "Table Array" color=slate style=dashed
node s0 "Slot 0" at 0,1 in array icon=file color=slate
node s1 "Slot 1" at 1,1 in array icon=db color=blue sub="occupied: 'bar'"
node s2 "Slot 2" at 2,1 in array icon=db color=green sub="target: 'foo'"
node s3 "Slot 3" at 3,1 in array icon=file color=slate

hash -> s1 : "probe 1 (collision)"
s1 -> s2 : "probe 2 (match)"
```

### Collision strategies

| Strategy | How | Pros | Cons |
|---|---|---|---|
| Separate chaining | Each slot holds a list (or tree) of entries | Simple; tolerates high load | Pointer chasing, poor cache locality |
| Open addressing: linear probing | On collision, try the next slot | Excellent cache locality | Primary clustering; deletion needs tombstones |
| Open addressing: perturbed / pseudo-random probing | Probe sequence derived from more hash bits | Less clustering | Less locality than linear |
| Robin Hood hashing | Evict entries that are closer to their home slot | Low variance in probe length | More complex inserts |
| Swiss table | Groups of slots with a metadata byte per slot; SIMD compares 7 hash bits for a whole group at once | Very fast lookups, high load factors | Complex |

**Try it: make keys collide.** Insert keys one at a time and check each `k mod capacity` by hand. With linear probing, watch occupied runs merge into clusters and the probe count climb as the load factor nears 1; then set resizing to *never* and fill the table. Delete a key and look up a key past its tombstone. Switch to chaining and compare: the table never fills, but chains grow instead.

<div class="lab" data-viz="cs-hashtable"></div>

### How real runtimes do it

| Runtime | Implementation | Details worth mentioning |
|---|---|---|
| CPython `dict` | Open addressing with perturbed probing + a separate dense **entries array** ("compact dict", 3.6+) | Load factor kept at or below 2/3; entries array preserves **insertion order** (guaranteed since 3.7); the sparse index table holds small ints so the table is memory-efficient |
| Java `HashMap` | Separate chaining | Default load factor 0.75; capacity power of two; a bucket turns into a **red-black tree** once it holds 8 entries (and the table is large enough), capping worst-case bucket lookups at O(log n) |
| Go `map` (1.24+) | **Swiss table** design | Before 1.24: buckets of 8 entries with overflow buckets. Iteration order is deliberately randomized; maps aren't safe for concurrent writes (the runtime detects some and crashes) |
| C++ `std::unordered_map` | Chaining (node-based) | Reference stability requirements force nodes; `absl::flat_hash_map` (Swiss table) is Google's faster alternative |

### Consequences to say out loud
- **Resize cost:** a single insert that triggers a resize is O(n); the *amortized* cost stays O(1) because capacity grows geometrically (section 2's argument). Latency-critical systems pre-size maps.
- **Keys must be immutable for their hash:** mutate a key after inserting and you can't find it. That's why Python lists aren't hashable and tuples are.
- **`__eq__` and `__hash__` must agree:** equal objects must have equal hashes. Java's `equals`/`hashCode` contract is the same rule.
- **Hash flooding (algorithmic DoS):** an attacker who can predict the hash sends many colliding keys, turning O(1) into O(n) per operation. Defenses: randomized/keyed hashing (Python randomizes `str`/`bytes` hashes per process with SipHash; `PYTHONHASHSEED`), treeified buckets (Java).
- **Python ints hash to themselves** (mostly), so integer keys are cheap and predictable, which is also why integer keys can be attacked if the input is adversarial.
- **Memory:** a hash map of n entries costs far more than an array of n values. Counting 26 lowercase letters with a list of 26 ints beats a dict (see `PyDSA/01_arrays_hashing/003`'s measured benchmark).

### Hash set
A hash map without values. Same complexity, same internals (CPython `set` is a separate implementation with its own tuning, but the same open-addressing idea).

§10 builds an open-addressing map from scratch and §11 measures how probe length grows
with the load factor. The live flow below follows one lookup, one collision and one
resize through CPython's two-array layout.

<div class="lab" data-viz="flow-dict-lookup"></div>

## 2. Dynamic Arrays (Python `list`, Go slice, Java `ArrayList`, C++ `vector`)

- A contiguous block with **length** (used) and **capacity** (allocated).
- `append` writes into spare capacity in O(1). When full, allocate a larger block, **copy everything**, then append.
- **Growth must be geometric** (multiply capacity by a constant factor > 1). Then total copy work over n appends is at most c·n: each element is copied O(1) times on average → **amortized O(1)**. Growing by a constant amount instead gives O(n²) total.

| Runtime | Growth policy |
|---|---|
| CPython `list` | Over-allocates about 12.5% plus a small constant (`newsize + (newsize >> 3) + 6`, rounded) — modest growth keeps memory tight |
| Go slices | Roughly doubles for small slices, transitioning smoothly toward ~1.25x above 256 elements |
| Java `ArrayList` | 1.5x |
| C++ `std::vector` | Implementation-defined; commonly 2x (libstdc++) or 1.5x (MSVC) |

Consequences:
- **Insert/delete at the front or middle is O(n)** (shifts everything). `list.pop(0)` in a BFS loop is a quadratic trap; use `collections.deque`.
- **Slicing copies** in Python (`a[1:]` is O(n) time and memory). Recursion that passes `nums[1:]` is O(n²).
- **Go slice aliasing:** slices share a backing array; `append` may or may not reallocate, so two slices can silently overwrite each other (demonstrated live in `GoDSA/01_arrays_hashing/001`).
- **Cache locality:** contiguous arrays are dramatically faster to scan than linked structures of the same Big-O.

**See it happen.** `sys.getsizeof` reports a container's current allocation, so you
can watch CPython over-allocate a list and rebuild a dict (`python3 growth.py`):

```python
"""Watch CPython resize a list and a dict as you append/insert."""
import sys

lst, last = [], sys.getsizeof([])
print("list: len at which the allocation grew -> bytes")
for i in range(40):
    lst.append(i)
    size = sys.getsizeof(lst)
    if size != last:
        print(f"  len={len(lst):3}  {size} bytes  (room for {(size - sys.getsizeof([])) // 8} pointers)")
        last = size

d, last = {}, sys.getsizeof({})
print("dict: len at which the table was rebuilt -> bytes")
for i in range(200):
    d[i] = i
    size = sys.getsizeof(d)
    if size != last:
        print(f"  len={len(d):3}  {size} bytes")
        last = size
```

Output (verified with CPython 3.11; exact sizes differ between versions):

```text
list: len at which the allocation grew -> bytes
  len=  1  88 bytes  (room for 4 pointers)
  len=  5  120 bytes  (room for 8 pointers)
  len=  9  184 bytes  (room for 16 pointers)
  len= 17  248 bytes  (room for 24 pointers)
  len= 25  312 bytes  (room for 32 pointers)
  len= 33  376 bytes  (room for 40 pointers)
dict: len at which the table was rebuilt -> bytes
  len=  1  224 bytes
  len=  6  352 bytes
  len= 11  632 bytes
  len= 22  1168 bytes
  len= 43  2264 bytes
  len= 86  4688 bytes
  len=171  9304 bytes
```

The list grows in steps of 4, 8, 16, 24, 32, 40 pointers: small lists round up
aggressively, larger ones by the ~12.5% rule above, so most appends just fill a spare
slot. The dict rebuilds its table when it passes 5, 10, 21, 42, 85 and 170 entries:
exactly 2/3 of 8, 16, 32, 64, 128 and 256 slots, which is §1's load-factor limit
made visible. Each rebuild re-inserts every entry (one O(n) insert), and because the
table size doubles, the total work stays O(n) over all inserts.

**Try it: compare growth rules.** The printout above is CPython's real growth pattern. The lab below runs three growth rules over the same 96 appends, so you can watch the amortized cost settle (doubling, ×1.5) or climb without limit (a constant increment).

<div class="lab" data-viz="cs-amortized"></div>

## 3. Strings

| Language | Mutability | Concatenation in a loop |
|---|---|---|
| Python `str` | Immutable (sequence of code points; compact 1/2/4-byte representation per string, PEP 393) | `s += x` is O(n) per step in general → O(n²) total; use `"".join(parts)`. (CPython sometimes resizes in place when the refcount is 1 — don't rely on it) |
| Go `string` | Immutable bytes (UTF-8); `s[i]` is a byte, `range` yields runes | Use `strings.Builder` |
| Java `String` | Immutable (UTF-16 or Latin-1 compact strings) | Use `StringBuilder` |

Unicode matters: `len("école")` is 5 in Python and 6 bytes in Go; indexing by position assumes a representation.

## 4. Linked Lists and Deques

- Singly/doubly linked lists: O(1) insert/delete **given the node**, O(n) search, poor cache locality, per-node pointer overhead. In practice they win only when you already hold node references (LRU cache: hash map → node).
- **CPython `collections.deque`:** a doubly linked list of **fixed-size blocks** (64 slots each), so appends/pops at both ends are O(1) with decent locality; indexing the middle is O(n).
- **Ring buffer (circular array):** fixed capacity, O(1) push/pop at both ends, excellent locality. Used in kernels (NIC queues, io_uring), logging, audio, and bounded queues.

## 5. Binary Heaps (Python `heapq`, Java `PriorityQueue`, Go `container/heap`)

- A **complete binary tree stored in an array**: children of i at `2i+1` and `2i+2`, parent at `(i-1)//2`. No pointers.
- **push:** append at the end, sift up: O(log n). **pop:** move the last element to the root, sift down: O(log n). **peek:** O(1).
- **heapify** an array: O(n), not O(n log n) — most nodes are near the bottom and sift down only a short distance (the sum of heights is O(n)).
- **Python's `heapq` is a min-heap only.** Max-heap: push negated values. For ties, push tuples `(priority, counter, item)` so items never get compared.
- **No efficient arbitrary delete or decrease-key** → lazy deletion (see `PyDSA/12_heap_priority_queue/012`) or an indexed heap.
- `heapq.nlargest(k, xs)` is O(n log k); sorting is O(n log n) but CPython's C-level sort often wins in wall-clock time for moderate n — measure.

**Try it: push, pop and heapify.** The tree and the array below are the same data. Push a small value and follow it sifting up (compare with the parent at `(i-1)//2`, swap while smaller); pop and follow the last leaf sinking down from the root. Then build a heap from 15 values and count the swaps: far fewer than n log n, which is §12's O(n) heapify proof in action.

<div class="lab" data-viz="cs-heap"></div>

## 6. Balanced Search Trees and Ordered Maps

Needed when you want ordered operations: floor/ceiling, range queries, min/max with deletions.

| Structure | Balance rule | Where it's used |
|---|---|---|
| Red-black tree | Colors + rotations; height ≤ 2 log(n+1) | Java `TreeMap`, C++ `std::map`, Linux CFS run queue, Java HashMap treeified buckets |
| AVL tree | Height difference ≤ 1; stricter, faster lookups, more rotations | Read-heavy in-memory indexes |
| B-tree / B+ tree | High fan-out nodes sized to a disk or cache page | Databases and filesystems (see [Database Storage Engines & Advanced Structures](03_databases_deep_dive.md)); `absl::btree_map` in memory for cache locality |
| Skip list | Randomized levels; expected O(log n) | **Redis sorted sets** (skip list + hash map), LevelDB/RocksDB MemTable — easy to make concurrent |
| Treap | Random priorities + BST order | Competitive programming, simple balanced BSTs |

**Python has no built-in balanced BST.** Options in an interview: `bisect` on a sorted list (O(log n) search, O(n) insert/delete via memmove — often fine and fast for n up to ~10^5), a heap if you only need min/max, or say "I'd use `sortedcontainers.SortedList` in production."

**Try it: grow a B+ tree.** With three keys per page, insert until a leaf overflows and splits, then until the root splits and the tree gains a level. Growth happens at the top, so every leaf stays at the same depth; that is how B-trees stay balanced without rotations. Then insert increasing keys (like an auto-increment ID) and watch every split land on the right edge.

<div class="lab" data-viz="cs-btree"></div>

## 7. Tries and Radix Trees

- Trie: one node per character; O(L) insert/search for a key of length L, independent of how many keys are stored. Memory-heavy (a dict or 26-slot array per node).
- **Radix (compressed) trie:** chains of single-child nodes collapsed into one edge labeled with a substring. Used in routers (IP longest-prefix match), HTTP routers, and Linux's page cache (XArray).
- Store extra data at nodes for autocomplete (top-k suggestions, counts): `PyDSA/13_trie/007`.

## 8. Graph Representations

| Representation | Space | Edge check | Iterate neighbors | Use when |
|---|---|---|---|---|
| Adjacency list | O(V + E) | O(degree) | O(degree) | Sparse graphs (almost always) |
| Adjacency matrix | O(V²) | O(1) | O(V) | Dense graphs, small V, Floyd-Warshall |
| Edge list | O(E) | O(E) | O(E) | Kruskal's MST, Bellman-Ford |
| CSR (compressed sparse row) | O(V + E), contiguous | O(log degree) if sorted | O(degree), cache-friendly | Large static graphs, graph analytics |

## 9. Quick Reference: Big-O of Built-ins

| Operation | Python | Go | Java |
|---|---|---|---|
| Index array | `a[i]` O(1) | `s[i]` O(1) | `list.get(i)` O(1) |
| Append | `append` O(1) amortized | `append` O(1) amortized | `add` O(1) amortized |
| Insert at front | `insert(0, x)` O(n) | copy O(n) | `add(0, x)` O(n) |
| Hash lookup | `x in d` O(1) avg | `m[k]` O(1) avg | `get` O(1) avg |
| Membership in list | `x in lst` O(n) | loop O(n) | `contains` O(n) |
| Sort | `sorted` O(n log n), stable (Timsort/Powersort) | `slices.Sort` O(n log n), not stable (`slices.SortStableFunc` is) | `Collections.sort` stable |
| Deque both ends | `deque` O(1) | slice/`container/list` | `ArrayDeque` O(1) |
| Heap push/pop | `heapq` O(log n) | `container/heap` O(log n) | `PriorityQueue` O(log n) |
| Ordered floor/ceiling | `bisect` O(log n) search | `slices.BinarySearch` | `TreeMap.floorKey` O(log n) |

## 10. Build One: an Open-Addressing Hash Map

"Implement a hash map without using the built-in one" (LeetCode 706) is a real
interview question, and writing it once makes §1's vocabulary concrete. This version
uses the same family of design as CPython's `dict`: **open addressing** (entries live
in the table itself, no chains), a power-of-two capacity so `hash & mask` replaces
`%`, a **2/3 load-factor limit**, and **tombstones** for deletion. It uses linear
probing for readability; CPython perturbs the probe sequence with higher hash bits to
avoid clustering (§1's table). Verified against `dict` over 200,000 random
operations (`python3 hashmap.py`):

```python
"""An open-addressing hash map with linear probing, tombstones and geometric resizing."""
import random

_EMPTY, _TOMBSTONE = object(), object()     # two distinct sentinels


class HashMap:
    def __init__(self, capacity=8):
        self._slots = [_EMPTY] * capacity    # each slot: _EMPTY, _TOMBSTONE, or (key, value)
        self._size = 0                       # live entries
        self._used = 0                       # live entries + tombstones (both lengthen probes)

    def _probe(self, key):
        """Yield slot indexes in probe order: home slot, then the next one, wrapping around."""
        mask = len(self._slots) - 1          # capacity is a power of two, so & replaces %
        i = hash(key) & mask
        while True:
            yield i
            i = (i + 1) & mask

    def get(self, key, default=None):
        for i in self._probe(key):
            slot = self._slots[i]
            if slot is _EMPTY:
                return default               # an empty slot ends the probe: key is absent
            if slot is not _TOMBSTONE and slot[0] == key:
                return slot[1]

    def put(self, key, value):
        if (self._used + 1) * 3 > len(self._slots) * 2:     # keep load (incl. tombstones) <= 2/3
            self._resize(len(self._slots) * 2 if self._size * 3 >= len(self._slots) else len(self._slots))
        first_tomb = None
        for i in self._probe(key):
            slot = self._slots[i]
            if slot is _EMPTY:
                if first_tomb is not None:   # reuse the earliest tombstone on the path
                    i = first_tomb
                else:
                    self._used += 1
                self._slots[i] = (key, value)
                self._size += 1
                return
            if slot is _TOMBSTONE:
                if first_tomb is None:
                    first_tomb = i
            elif slot[0] == key:
                self._slots[i] = (key, value)  # overwrite in place
                return

    def delete(self, key):
        for i in self._probe(key):
            slot = self._slots[i]
            if slot is _EMPTY:
                raise KeyError(key)
            if slot is not _TOMBSTONE and slot[0] == key:
                self._slots[i] = _TOMBSTONE  # NOT _EMPTY: that would cut other keys' probe paths
                self._size -= 1
                return

    def _resize(self, new_capacity):
        old = self._slots
        self._slots, self._size, self._used = [_EMPTY] * new_capacity, 0, 0
        for slot in old:                     # rehash every live entry; tombstones are dropped
            if slot is not _EMPTY and slot is not _TOMBSTONE:
                self.put(*slot)

    def __len__(self):
        return self._size


if __name__ == "__main__":
    rng = random.Random(42)
    mine, ref = HashMap(), {}
    for _ in range(200_000):                 # random mix of puts, gets and deletes, checked against dict
        k, op = rng.randrange(5_000), rng.random()
        if op < 0.5:
            mine.put(k, op); ref[k] = op
        elif op < 0.8:
            assert mine.get(k) == ref.get(k)
        elif k in ref:
            mine.delete(k); del ref[k]
    assert len(mine) == len(ref) and all(mine.get(k) == v for k, v in ref.items())
    print(f"200,000 random ops agree with dict; {len(mine)} keys in {len(mine._slots)} slots")

    # Why deletion needs tombstones: 0 and 8 share home slot 0 in an 8-slot table.
    m = HashMap(); m.put(0, "a"); m.put(8, "b"); m.delete(0)
    print("after deleting 0, get(8) =", m.get(8))
```

Output (verified with Python 3.11):

```text
200,000 random ops agree with dict; 3588 keys in 8192 slots
after deleting 0, get(8) = b
```

The details an interviewer will probe:

- **Why an empty slot ends a lookup.** Insertion walks the probe sequence and stops at
  the first free slot, so if a key were present it would sit *before* the first empty
  slot on its path. Reaching an empty slot proves absence.
- **Why deletion can't just empty the slot.** Keys 0 and 8 share home slot 0 in an
  8-slot table, so 8 lands in slot 1. Emptying slot 0 on `delete(0)` would make
  `get(8)` stop at slot 0 and wrongly report "missing". The tombstone says "keep
  probing past me" to lookups and "you may reuse me" to inserts.
- **Why tombstones count toward the load factor.** They lengthen probe sequences just
  like live entries. A table with heavy delete churn fills with tombstones; the
  resize rebuilds it and drops them (here, at the same capacity when few entries are
  live).
- **Why capacity is a power of two.** `hash & (capacity - 1)` is one instruction;
  `%` is a division. The price is that only the low bits of the hash choose the slot,
  so the hash function must mix well into those bits (Java's `HashMap` XORs the high
  16 bits into the low ones for exactly this reason).
- **Separate chaining instead** (a list per slot, as Java's `HashMap` does) makes
  deletion trivial and tolerates load factors near or above 1, at the cost of a
  pointer hop per entry. Both are acceptable interview answers; say which and why.

## 11. Load Factor and Probe Length, Measured

Why 2/3 (CPython) or 0.75 (Java) and not 0.95? Because probe length explodes as the
table fills. For linear probing, Knuth's classic analysis gives an expected
unsuccessful-search length of about ½(1 + 1/(1 − α)²) probes at load factor α. This
script fills a 65,536-slot table with random keys and measures it
(`python3 probes.py`):

```python
"""Average probe length of linear probing as the table fills, vs Knuth's formulas."""
import random

def measure(load, capacity=1 << 16, trials=20_000, seed=1):
    rng = random.Random(seed)
    table = [None] * capacity
    mask = capacity - 1
    for _ in range(int(load * capacity)):             # insert random keys with linear probing
        i = rng.getrandbits(64) & mask
        while table[i] is not None:
            i = (i + 1) & mask
        table[i] = True
    total = 0
    for _ in range(trials):                            # unsuccessful search: probe until an empty slot
        i, probes = rng.getrandbits(64) & mask, 1
        while table[i] is not None:
            i, probes = (i + 1) & mask, probes + 1
        total += probes
    return total / trials

print("load  measured  Knuth ~ (1 + 1/(1-a)^2) / 2")
for a in (0.25, 0.5, 2 / 3, 0.75, 0.9, 0.95):
    print(f"{a:4.2f}  {measure(a):8.1f}  {(1 + 1 / (1 - a) ** 2) / 2:8.1f}")
```

Output (verified with Python 3.11):

```text
load  measured  Knuth ~ (1 + 1/(1-a)^2) / 2
0.25       1.4       1.4
0.50       2.5       2.5
0.67       5.1       5.0
0.75       8.8       8.5
0.90      48.5      50.5
0.95     171.8     200.5
```

Up to about 2/3 a miss costs a few probes, all in adjacent slots (often the same
cache line). Past 0.9 it's dozens to hundreds. That's the trade: a lower load factor
spends memory to buy short, predictable probes. Swiss tables (Go 1.24+ maps,
`absl::flat_hash_map`) run at up to 7/8 load because their probing compares 8–16
one-byte tags at once with SIMD instructions, which makes long runs cheap to skip;
chained tables (Java) tolerate higher load because a collision costs a list step, not
a longer run shared by everyone.

**Precision note:** "hash map lookup is O(1)" silently assumes (a) hashing the key is
O(1) — false for a long string, which costs O(length) to hash (CPython caches a
`str`'s hash after the first time), (b) the load factor is bounded, and (c) keys are
not adversarial (§1's hash flooding). Say "O(1) expected, assuming a good hash and a
bounded load factor" and you've pre-empted the follow-up.

## 12. Build One: a Binary Heap, and Proof That Heapify Is O(n)

§5 states that building a heap from n items bottom-up is O(n), not O(n log n). The
argument: half the nodes are leaves and never move, a quarter can sift down at most
one level, an eighth at most two, and so on — n·(1/4·1 + 1/8·2 + 1/16·3 + …) = n·1 =
O(n). This heap counts its swaps so you can check the argument against the alternative
of pushing items one at a time (`python3 heap.py`):

```python
"""A binary min-heap on a plain list, and a count showing heapify is O(n), not O(n log n)."""
import math
import random


class MinHeap:
    def __init__(self, items=()):
        self.a = list(items)
        self.swaps = 0
        for i in range(len(self.a) // 2 - 1, -1, -1):   # heapify: sift down every internal node, bottom-up
            self._sift_down(i)

    def push(self, x):
        self.a.append(x)
        self._sift_up(len(self.a) - 1)

    def pop(self):
        a = self.a
        a[0], a[-1] = a[-1], a[0]                         # move the last leaf to the root...
        smallest = a.pop()
        if a:
            self._sift_down(0)                            # ...and let it sink to its place
        return smallest

    def _sift_up(self, i):
        a = self.a
        while i > 0 and a[i] < a[(i - 1) // 2]:           # parent of i is (i - 1) // 2
            p = (i - 1) // 2
            a[i], a[p] = a[p], a[i]
            self.swaps += 1
            i = p

    def _sift_down(self, i):
        a, n = self.a, len(self.a)
        while True:
            l, r, m = 2 * i + 1, 2 * i + 2, i              # children of i are 2i+1 and 2i+2
            if l < n and a[l] < a[m]: m = l
            if r < n and a[r] < a[m]: m = r
            if m == i:
                return
            a[i], a[m] = a[m], a[i]
            self.swaps += 1
            i = m


rng = random.Random(7)
xs = [rng.random() for _ in range(10_000)]
h = MinHeap(xs)
assert [h.pop() for _ in range(len(xs))] == sorted(xs)
print("heap sort of 10,000 floats matches sorted()")

print("       n   heapify swaps   swaps/n   n*log2(n)/n   one-by-one push swaps")
for n in (1_000, 10_000, 100_000, 1_000_000):
    data = list(range(n, 0, -1))                          # descending: worst case for a min-heap
    bulk = MinHeap(data)
    one = MinHeap()
    for x in data:
        one.push(x)
    print(f"{n:8}  {bulk.swaps:14}  {bulk.swaps / n:8.2f}  {math.log2(n):12.1f}  {one.swaps:22}")
```

Output (verified with Python 3.11):

```text
heap sort of 10,000 floats matches sorted()
       n   heapify swaps   swaps/n   n*log2(n)/n   one-by-one push swaps
    1000             992      0.99          10.0                    7987
   10000            9992      1.00          13.3                  113631
  100000           99990      1.00          16.6                 1468946
 1000000          999988      1.00          19.9                17951445
```

Bottom-up heapify on descending input (the worst case for a min-heap) makes just
under one swap per element at every size: linear. Pushing the same items one at a
time makes roughly n·log₂(n) swaps, because each new, smaller element sifts all the
way to the root. That's why `heapq.heapify(xs)` beats a loop of `heappush` and why
"build a heap from the array, then pop k times" is O(n + k log n).

The array-as-tree trick is what makes the heap fast in practice: no node objects, no
pointers, children found by arithmetic (`2i + 1`, `2i + 2`), and the top levels of the
tree sit in the same few cache lines.

## 13. Memory Layout: Locality and Per-Object Overhead

Big-O counts steps. It doesn't see that some steps are a cache hit and others a
100-ns trip to RAM, or that a "list of a million ints" in Python is a million
separate objects. Two measurements make this concrete.

**Locality.** The same O(n) sum over ten million `int64`s, stored three ways: a slice,
a linked list whose nodes happen to be in memory order, and the same list with its
links shuffled so consecutive nodes are far apart (`go run .` in a module with this
`main.go`):

```go
// Same O(n) sum, three memory layouts: a contiguous slice, a linked list whose nodes
// happen to sit in order, and the same list with its nodes scattered around the heap.
package main

import (
	"fmt"
	"math/rand"
	"time"
)

type node struct {
	val  int64
	next *node
}

func sumSlice(xs []int64) (s int64) {
	for _, x := range xs {
		s += x
	}
	return
}

func sumList(head *node) (s int64) {
	for n := head; n != nil; n = n.next {
		s += n.val
	}
	return
}

// buildList links the nodes of pool in the order given by order.
func buildList(pool []node, order []int) *node {
	for i := 0; i < len(order)-1; i++ {
		pool[order[i]].next = &pool[order[i+1]]
	}
	pool[order[len(order)-1]].next = nil
	return &pool[order[0]]
}

func timeIt(f func() int64) (time.Duration, int64) {
	best, res := time.Duration(1<<62), int64(0)
	for r := 0; r < 5; r++ { // best of 5 runs
		start := time.Now()
		res = f()
		if d := time.Since(start); d < best {
			best = d
		}
	}
	return best, res
}

func main() {
	const n = 10_000_000 // ~80 MB of slice, ~160 MB of nodes: far bigger than any CPU cache
	xs := make([]int64, n)
	pool := make([]node, n)
	order := make([]int, n)
	for i := range xs {
		xs[i], pool[i].val, order[i] = int64(i), int64(i), i
	}
	seq := buildList(pool, order)
	tSlice, a := timeIt(func() int64 { return sumSlice(xs) })
	tSeq, b := timeIt(func() int64 { return sumList(seq) })

	rand.New(rand.NewSource(1)).Shuffle(n, func(i, j int) { order[i], order[j] = order[j], order[i] })
	scattered := buildList(pool, order)
	tRand, c := timeIt(func() int64 { return sumList(scattered) })

	if a != b || b != c {
		panic("sums differ")
	}
	fmt.Printf("slice                %7.1f ms\n", float64(tSlice.Microseconds())/1000)
	fmt.Printf("list, nodes in order %7.1f ms  (%.1fx the slice)\n", float64(tSeq.Microseconds())/1000, float64(tSeq)/float64(tSlice))
	fmt.Printf("list, nodes shuffled %7.1f ms  (%.1fx the slice)\n", float64(tRand.Microseconds())/1000, float64(tRand)/float64(tSlice))
}
```

One run on a cloud VM (Go 1.24, linux/amd64); your absolute times and ratios will
differ with the CPU's cache sizes and memory latency:

```text
slice                   12.4 ms
list, nodes in order    68.3 ms  (5.5x the slice)
list, nodes shuffled  2284.7 ms  (183.5x the slice)
```

All three loops are O(n) and do the same additions. The in-order list is several
times slower because every step is a dependent load (the CPU can't fetch node i+1
until it has read node i's `next`), and the loop can't be unrolled or vectorised. The
shuffled list is two orders of magnitude slower because nearly every step is also a
cache and TLB miss. This is why linked lists lose to arrays in practice even for
operations where they win on paper, why B-trees (wide nodes) beat binary trees in
databases and increasingly in memory (`absl::btree_map`), and why a garbage collector
that compacts objects can make linked structures faster.

**Per-object overhead (CPython).** Everything in a Python container is a pointer to a
separately allocated object. Measuring one million integers held five ways with
`tracemalloc` (`python3 memory.py`):

```python
"""What one million integers cost in memory, held five different ways (CPython)."""
import array
import tracemalloc

N = 1_000_000

def cost(build):
    tracemalloc.start()
    obj = build()                                      # keep a reference while measuring
    current, _ = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return current / N, obj

rows = [
    ("array('q') of ints", lambda: array.array("q", range(N))),
    ("list of ints", lambda: list(range(N))),
    ("set of ints", lambda: set(range(N))),
    ("dict int -> int", lambda: {i: i for i in range(N)}),
    ("list of 1-tuples", lambda: [(i,) for i in range(N)]),
]
for name, build in rows:
    per_item, _ = cost(build)
    print(f"{name:20} {per_item:6.1f} bytes per item")
```

Output (verified with CPython 3.11, 64-bit):

```text
array('q') of ints      8.2 bytes per item
list of ints           40.0 bytes per item
set of ints            65.5 bytes per item
dict int -> int        73.9 bytes per item
list of 1-tuples       88.4 bytes per item
```

A `list` of ints costs 8 bytes of pointer plus a 28-byte `int` object (rounded to 32
by the allocator) per item; `array('q')` stores the raw 8-byte values, five times
smaller and contiguous. A `set` or `dict` adds a hash table (kept at most 2/3 full,
§1) on top of the objects themselves, and a tuple per item adds another object. At
10⁸ items this is the difference between fitting in RAM or not, which is why
numerical Python lives in NumPy arrays and why "just use a dict" is an answer to
defend with numbers in a design discussion.

## 14. Concurrent and Persistent Structures

Two follow-ups push past the single-threaded, mutable structures above.

**"Make it thread-safe" (see [Concurrency](05_concurrency_deep_dive.md) §7 for locking patterns).**

| Structure | How it's made concurrent | Trade-off |
|---|---|---|
| Java `ConcurrentHashMap` (Java 8+) | CAS to install the first node in an empty bin; a lock on the bin's first node for other updates; lock-free reads; concurrent, cooperative resizing | Scales with cores; iterators are weakly consistent (they may or may not see concurrent updates) |
| Go `sync.Map` | Since Go 1.24 a concurrent hash-trie; before that, a lock-free read-only map plus a mutex-guarded dirty map promoted after enough misses | Built for keys written once and read many times, or disjoint keys per goroutine; the docs recommend a plain `map` with your own locking for most other code, which also keeps type safety |
| Sharded map (lock striping) | N independent maps, each with its own lock, chosen by `hash(key) % N` | Simple and effective; cross-shard operations (size, iteration) need all locks or give approximate answers |
| Lock-free skip list (Java `ConcurrentSkipListMap`) | CAS on individual forward pointers | An ordered concurrent map without a global lock; the reason skip lists (§6) are popular in concurrent code |
| Ring buffer (single producer, single consumer) | Two indices, each written by only one side, published with atomic stores | The fastest queue there is, but only for exactly one writer per index (LMAX Disruptor, kernel rings) |

**Precision note:** CPython's GIL keeps a `dict` from being corrupted by concurrent
threads, but it does not make *your* read-modify-write (`d[k] = d.get(k, 0) + 1`)
atomic; free-threaded CPython (3.13+) uses per-object locks with the same guarantee.
A Go `map` written by two goroutines without a lock is a data race, and the runtime
may abort with `fatal error: concurrent map writes`.

**"Keep the old version too" — persistent (immutable) structures.** A persistent
structure never mutates; an "update" returns a new version that **shares** all
unchanged parts with the old one. Updating one element of a balanced tree copies only
the O(log n) nodes on the path from the root (**path copying**); every other node is
shared. Clojure's and Scala's vectors and maps (hash array mapped tries, 32-way
branching) make that path very short, so updates are effectively O(1) in practice
and each version is a cheap, thread-safe snapshot. The same idea appears at larger
scale in copy-on-write B-trees (LMDB, Btrfs), Git's object graph, and MVCC row
versions ([Database Storage Engines & Advanced Structures](03_databases_deep_dive.md) §2). It's the principled answer to "readers
must never block on writers" and to undo/history features.

## 15. Choosing a Structure From the Operations

In an interview, pick the structure by listing the operations the problem needs and
their frequency, then choose the cheapest structure that supports all of them. The
common decision path:

```arch
%% caption: Start from the operations you need; each question rules structures in or out.
grid 180x110
node q "Which operations dominate?" at 1,0 shape=pill color=slate
node d1 "Lookup by key only?" at 1,1 shape=diamond color=amber
node hm "Hash map / set" at 0,1 shape=card icon=kv sub="O(1) expected"
node d2 "Min or max only?" at 1,2 shape=diamond color=amber
node hp "Binary heap" at 0,2 shape=card icon=tree sub="O(log n) push/pop"
node d3 "Order, floor, ranges?" at 1,3 shape=diamond color=amber
node bst "Sorted list / balanced tree" at 0,3 shape=card icon=sort sub="bisect or TreeMap"
node d4 "Ends of a sequence?" at 1,4 shape=diamond color=amber
node dq "Deque / ring buffer" at 0,4 shape=card icon=queue sub="O(1) both ends"
node arr "Array" at 2,4 shape=card icon=table sub="index + scan"
node tr "Trie" at 2,3 shape=card icon=search sub="prefix queries (§7)"
q -> d1
d1 -> hm : "yes"
d1 -> d2 : "no"
d2 -> hp : "yes"
d2 -> d3 : "no"
d3 -> bst : "yes"
d3 -> tr : "prefixes"
d3 -> d4 : "no"
d4 -> dq : "yes"
d4 -> arr : "no"
```

Most real problems combine two: **LRU cache** = hash map (find the node) + doubly
linked list (reorder it in O(1)); **LFU** adds a map from frequency to list;
**sliding-window maximum** = deque of indices kept monotonic; **Dijkstra** = heap +
distance map; **Redis sorted set** = skip list (order) + hash map (score by member);
**top-k frequent** = counter + size-k heap. When you name a composite like this, say
which invariant ties the two parts together (the map's node and the list's node are
the same object) — that's the part a thread-safety follow-up will lock (§14).

## What Each Engineering Level Should Know

Not everyone reading this file needs every sentence of it cold. This table maps this
chapter's material onto a standard industry ladder *and* the Google-style ladder this
repo's interview content is written against, side by side. The mapping between
company-specific titles and levels is approximate and varies by company, but the
*depth of understanding* described in each row is a reliable signal regardless of
which company uses which label. Use it as a syllabus (read down a column) or as a
self-assessment (find the cell that matches where a real interview would place you).

| Topic in this chapter | Junior / New Grad (Google L3) | Mid-Level (Google L4) | Senior (Google L5) | Staff+ (Google L6–L7) |
|---|---|---|---|---|
| **ADTs, invariants, layouts** (Foundations) | Knows list vs. dict vs. set and when to use each | Separates the ADT from its implementation (map as hash table or tree) | Explains every structure as layout + invariant + repair cost, and why contiguous beats linked in practice | Chooses representations for a system's hot paths from memory and access-pattern numbers |
| **Hash maps** (§1, §10–§11) | Knows lookup is "O(1)" and keys must be hashable | Explains collisions, load factor and resizing | Implements open addressing with tombstones cold; explains CPython/Java/Go designs, probe-length vs. load, and hash flooding | Picks hash-table designs and hash functions for latency-critical or adversarial workloads (Swiss tables, keyed hashing) |
| **Dynamic arrays & strings** (§2–§3) | Uses `append` and knows `insert(0, x)` is slow | Explains amortized O(1) append and quadratic string `+=` | Proves the geometric-growth bound, names each runtime's growth factor, spots slicing and aliasing costs in code | Sizes buffers and pre-allocates deliberately in latency-sensitive services |
| **Heaps, trees, tries, graphs** (§4–§8, §12) | Uses `heapq` and a dict-of-lists graph | Knows heap array indexing and why balanced trees exist | Writes a heap cold, proves O(n) heapify, names the tree behind `TreeMap`, Redis sorted sets and DB indexes | Chooses B-trees vs. skip lists vs. LSM-style structures for a storage or indexing system |
| **Memory & locality** (§13) | Unaware that layout affects speed | Knows arrays are cache-friendly and Python objects are large | Explains cache misses, dependent loads and per-object overhead with rough numbers, and measures instead of guessing | Designs data layouts (struct-of-arrays, compact encodings) for fleet-level memory and CPU savings |
| **Concurrent & persistent** (§14) | Knows shared structures need a lock | Wraps a structure in a mutex correctly | Explains `ConcurrentHashMap`, `sync.Map`, lock striping, and path copying, with their trade-offs | Chooses snapshot/copy-on-write vs. lock-based designs for read-heavy shared state across a platform |
| **Choosing a structure** (§15) | Picks from memory of similar problems | Picks from the operations the problem needs | Combines structures (LRU, LFU, sorted set) and names the invariant that ties them together | Evaluates structure choices by memory, tail latency and operability, not only Big-O |

**Reading this table as a study plan:** if you're aiming at a Senior/L5 bar, your
target is the whole "Senior" column, which the numbered sections (1–15) deliver in
full. The Foundations section alone takes you to roughly the "Mid-Level" column. The
"Staff+" column is judgment that mostly comes from operating real systems at scale;
this file gives you the vocabulary to have that conversation, not a substitute for
having had it.

## Interview checklist

- [ ] I can separate an ADT from its implementation and name each structure's invariant.
- [ ] I can explain hashing, collisions, load factor, and resizing, and describe CPython dict, Java HashMap, and Go map specifically.
- [ ] I can implement an open-addressing hash map with tombstones and explain why deletion can't just empty the slot.
- [ ] I can say why load factors stay near 2/3–0.75 and what "O(1) lookup" assumes.
- [ ] I can prove amortized O(1) append with geometric growth.
- [ ] I can explain why string concatenation in a loop is quadratic and what to use instead.
- [ ] I can implement a binary heap on an array and explain O(n) heapify.
- [ ] I can say which balanced tree backs `TreeMap`, Redis sorted sets, and database indexes, and what Python offers instead.
- [ ] I can explain why a linked list loses to an array at the same Big-O, and what a Python int costs in memory.
- [ ] I can describe how `ConcurrentHashMap` or a sharded map stays thread-safe, and what path copying is.
- [ ] I can pick a structure (or a combination) from the operations a problem needs.

Related: [Complexity Analysis](07_complexity_analysis_deep_dive.md) §6 (amortized analysis), [Python for Coding Interviews](08_python_for_coding_interviews_deep_dive.md) §1–§4, [Operating Systems & Hardware Symbiosis](01_operating_systems_deep_dive.md) §2 (cache lines), [Database Storage Engines & Advanced Structures](03_databases_deep_dive.md) §1 (B+ trees, LSM trees), [Specialized Data Structures and Indexes](../SystemDesign/building_blocks/20_specialized_data_structures.md); `content/interview-core/PyDSA/` and `content/interview-core/GoDSA/` for practice.
