# Data Structure Internals — What Actually Happens Under the <abbr title="Application Programming Interface">API</abbr>

Every data structure you reach for by habit — a list, a dict, a heap — is a small
piece of engineering with real trade-offs baked in, not a black box that's simply
"fast." This file starts with the basic vocabulary, then goes as deep as a standard
Google interview question expects: "how does a hash map work under the hood?" needs
a good answer that goes past "an array of buckets." This file covers the structures
you use every day, how real runtimes implement them (CPython, Go, Java), and the
performance consequences you can mention in a coding round.

## Foundations — Start Here If You're New to Data Structures

**What "Big-O" means, in one sentence.** You'll see `O(1)`, `O(n)`, `O(log n)` all
over this file — they describe how an operation's cost grows as the amount of data
(`n`) grows: `O(1)` means "roughly the same cost no matter how much data,"
`O(n)` means "cost grows in direct proportion to the data," and `O(log n)` sits far
closer to `O(1)` than to `O(n)` as data grows. `07_complexity_analysis_deep_dive.md`
is the full, precise treatment — read it first if this is new; everything below
assumes you can read these symbols comfortably.

**The three basic shapes, in one table** — nearly every structure in this file is a
variation on one of these:

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
implement it.

**Why some operations that look free actually aren't.** An array's `append` is
usually instant, but "usually" is doing real work there — occasionally the array
runs out of room and the whole thing must be copied to a bigger block. §2 explains
why that occasional expensive copy still averages out to "cheap every time"
(**amortized** cost — also covered from the complexity side in `07` §6).

With those three shapes and the idea of a hash function in mind, the rest of this
file is the precise, implementation-level version: how CPython, Go, and Java
actually build each structure, and the performance consequences worth knowing.

## 1. Hash Maps

### The core mechanism
1. Compute `hash(key)` → an integer.
2. Map it to a slot: `index = hash & (capacity - 1)` (capacity a power of two) or `hash % capacity`.
3. Handle **collisions**, because different keys can land in the same slot.
4. When the table gets too full (the **load factor** threshold), allocate a bigger table and **rehash** every entry.

Average O(1) lookup relies on a good hash function and a bounded load factor. Worst case is O(n) when many keys collide.

### Collision strategies

| Strategy | How | Pros | Cons |
|---|---|---|---|
| Separate chaining | Each slot holds a list (or tree) of entries | Simple; tolerates high load | Pointer chasing, poor cache locality |
| Open addressing: linear probing | On collision, try the next slot | Excellent cache locality | Primary clustering; deletion needs tombstones |
| Open addressing: perturbed / pseudo-random probing | Probe sequence derived from more hash bits | Less clustering | Less locality than linear |
| Robin Hood hashing | Evict entries that are closer to their home slot | Low variance in probe length | More complex inserts |
| Swiss table | Groups of slots with a metadata byte per slot; SIMD compares 7 hash bits for a whole group at once | Very fast lookups, high load factors | Complex |

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

## 6. Balanced Search Trees and Ordered Maps

Needed when you want ordered operations: floor/ceiling, range queries, min/max with deletions.

| Structure | Balance rule | Where it's used |
|---|---|---|
| Red-black tree | Colors + rotations; height ≤ 2 log(n+1) | Java `TreeMap`, C++ `std::map`, Linux CFS run queue, Java HashMap treeified buckets |
| AVL tree | Height difference ≤ 1; stricter, faster lookups, more rotations | Read-heavy in-memory indexes |
| B-tree / B+ tree | High fan-out nodes sized to a disk or cache page | Databases and filesystems (see `03_databases_deep_dive.md`); `absl::btree_map` in memory for cache locality |
| Skip list | Randomized levels; expected O(log n) | **Redis sorted sets** (skip list + hash map), LevelDB/RocksDB MemTable — easy to make concurrent |
| Treap | Random priorities + BST order | Competitive programming, simple balanced BSTs |

**Python has no built-in balanced BST.** Options in an interview: `bisect` on a sorted list (O(log n) search, O(n) insert/delete via memmove — often fine and fast for n up to ~10^5), a heap if you only need min/max, or say "I'd use `sortedcontainers.SortedList` in production."

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

## Interview checklist

- [ ] I can explain hashing, collisions, load factor, and resizing, and describe CPython dict, Java HashMap, and Go map specifically.
- [ ] I can prove amortized O(1) append with geometric growth.
- [ ] I can explain why string concatenation in a loop is quadratic and what to use instead.
- [ ] I can implement a binary heap on an array and explain O(n) heapify.
- [ ] I can say which balanced tree backs `TreeMap`, Redis sorted sets, and database indexes, and what Python offers instead.
