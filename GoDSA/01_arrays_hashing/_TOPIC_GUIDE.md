# Topic 01 · Arrays & Hashing — Go Deep Dive

> Go exposes the machinery Python hides. An `[]int` really is 8 bytes per int in
> one contiguous block — no pointer chasing, no boxing. That makes Go faster and
> far more cache-friendly, but it also means slice aliasing and map iteration
> order will bite you if you don't know the internals. This is the document that
> stops those bugs.

---

## Part 1 · Arrays vs. Slices

### 1.1 Arrays are values. This surprises everyone.

In Go, `[5]int` is a **fixed-size value type**. The length is part of the type,
and assigning **copies the whole thing**.

```go
a := [3]int{1, 2, 3}
b := a          // FULL COPY — b is a separate 24-byte block
b[0] = 99
// a == [1 2 3], b == [99 2 3]

func f(arr [3]int) { arr[0] = 42 }   // operates on a COPY; caller unaffected
```

`[3]int` and `[4]int` are **different types**. You cannot assign one to the other.
This is why you almost never use arrays directly in Go — you use slices.

### 1.2 A slice is a 3-word header

A slice is **not** a container. It is a small struct describing a *window* onto a
backing array (`runtime/slice.go`):

```go
type slice struct {
    array unsafe.Pointer  // pointer to the first element of the window
    len   int             // number of elements you can index
    cap   int             // elements available before the backing array ends
}
```

24 bytes on a 64-bit machine. Passing a slice to a function copies **the header**,
not the data — so writes through it are visible to the caller, but `append` may
not be.

```go
s := []int{10, 20, 30, 40, 50}
t := s[1:3]              // len=2, cap=4  — shares s's backing array!

     s ──► ┌────┬────┬────┬────┬────┐
           │ 10 │ 20 │ 30 │ 40 │ 50 │   backing array (len 5)
           └────┴────┴────┴────┴────┘
                  ▲         ▲
       t ─────────┘         │
       t.len = 2 ───────────┘
       t.cap = 4 (from index 1 to the end of the array)

t[0] = 99                // ⚠️ this also changes s[1]
fmt.Println(s)           // [10 99 30 40 50]
```

> ⚠️ **The #1 Go slice bug: aliasing.** Sub-slicing does not copy. If you need an
> independent copy — and inside `append(result, current)` in *any* backtracking
> problem, you always do — you must copy explicitly:
> ```go
> cp := make([]int, len(current))
> copy(cp, current)
> result = append(result, cp)
> ```
> Forget this and every row of your result aliases the same array, and they all
> end up identical or empty. You already hit this in the recursion folder.

Use the **three-index slice** `s[low:high:max]` to cap capacity and prevent an
`append` from stomping the parent's data:
```go
t := s[1:3:3]            // len=2, cap=2 — append now MUST reallocate
```

### 1.3 How `append` grows

`append` writes into spare capacity if `len < cap`; otherwise it allocates a new,
larger backing array and copies. The growth rule (`runtime.growslice`) changed in
**Go 1.18**:

- If the needed size is more than double the current cap → use the needed size.
- Else if `cap < 256` → **double** it.
- Else → grow by roughly `1.25x`, smoothly transitioning: repeatedly apply
  `newcap += (newcap + 3*256) / 4` until it fits.

The old pre-1.18 rule had a hard cliff at 1024; the current formula ramps down
gradually. The final size is then rounded up to a size class by the allocator.

Appending one element at a time to a `[]int`, the capacity goes (measured on Go 1.24.5):

```
1  2  4  8  16  32  64  128  256  512  848  1280  1792  2560  3408 ...
                                  └─ doubling ─┘  └─ ~1.25x, tapering ─┘
```

Same amortization argument as Python: geometric growth ⇒ **O(1) amortized append**,
with individual appends occasionally O(n).

```arch
%% caption: Every append is one of two very different events. Whether other slices see your write depends on which one you hit.
grid 200x110
node a "s = append(s, x)" at 0.5,0 shape=pill
node q "len(s) < cap(s)?" at 0.5,1 shape=diamond color=amber
node w "Write in place" at 0,2 shape=card icon=edit color=orange sub="into the SAME backing array, O(1)"
node al "Shared write" at 0,3 shape=card icon=warn color=red sub="every other slice over that array can see (or be overwritten by) the write"
node g "Grow and copy" at 1,2 shape=card icon=layers sub="allocate a bigger array, copy len elements; O(n), amortized away"
node ind "New array" at 1,3 shape=card icon=check color=green sub="s now points at a NEW array; old slices are unaffected"
a -> q
q -> w : "yes: room left"
q -> g : "no: full"
w -> al
g -> ind
```

```go
s := make([]int, 0, 100)   // ✅ preallocate when you know the size —
                           //    avoids ~7 reallocations and copies
```

**Always preallocate in interviews when the output size is known.** It is a free
constant-factor win and interviewers notice.

### 1.4 The complexity table

| Operation | Complexity | Note |
|---|:--:|---|
| `s[i]` read / write | **O(1)** | Bounds-checked; the check is often hoisted out of loops |
| `len(s)` / `cap(s)` | **O(1)** | Header fields |
| `append(s, x)` | **O(1)** amortized | May reallocate + copy |
| `s[a:b]` | **O(1)** ⚡ | Header arithmetic only — **no copy**, unlike Python |
| `copy(dst, src)` | **O(min(len))** | `memmove` |
| Delete at index `i` | **O(n)** | `append(s[:i], s[i+1:]...)` shifts |
| Prepend | **O(n)** | `append([]T{x}, s...)` |
| Linear search | **O(n)** | Go has no built-in `in` operator |
| `sort.Slice` | **O(n log n)** | pdqsort, **not stable** |
| `slices.Sort` | **O(n log n)** | Generic, faster, Go 1.21+ |

> ⚡ **Slicing is O(1) in Go but O(k) in Python.** `s[1:1000000]` in Go is three
> field assignments. In Python it copies a million pointers. This difference
> changes which algorithms are cheap in which language.

### 1.5 `nil` slices behave correctly — use them

```go
var s []int              // nil: array=nil, len=0, cap=0
len(s)                   // 0     — legal
s = append(s, 1)         // works — append allocates
for range s {}           // legal, zero iterations
s == nil                 // true
```

A `nil` slice is a perfectly good empty slice. `make([]int, 0)` is only different
in that it is non-nil — which matters solely for `== nil` checks and JSON
encoding (`null` vs `[]`). Prefer `var s []int`.

### 1.6 Go's sort

```go
sort.Ints(nums)                                       // legacy, concrete
sort.Slice(xs, func(i, j int) bool { return xs[i] < xs[j] })   // NOT stable
sort.SliceStable(xs, less)                            // stable, ~O(n log²n)
slices.Sort(nums)                                     // Go 1.21+, generic, fastest
slices.SortFunc(xs, func(a, b T) int { return a.v - b.v })
```

Since Go 1.19 the standard sort is **pdqsort** (pattern-defeating quicksort):
quicksort with median-of-three pivots, insertion sort under ~12 elements, and a
heapsort fallback when recursion goes too deep — which guarantees **O(n log n)
worst case**, unlike naive quicksort's O(n²).

> ⚠️ `sort.Slice` is **not stable**; Python's `sort` **is**. If a problem depends
> on preserving the order of equal elements, you must use `sort.SliceStable`.
> This is a real behavioural difference between your two languages.

The comparator is `less(i, j) bool` — indices, not values — because it predates
generics. `slices.SortFunc` takes values and returns an `int` (like `strcmp`),
which is the modern form.

---

## Part 2 · The Map

### 2.1 Go maps are Swiss tables (Go 1.24+)

Go 1.24 replaced the map implementation. Since then (this repo builds on Go 1.24.5) the built-in `map`
is a **Swiss table** — an *open-addressing* design from Google's Abseil library, adapted in
`internal/runtime/maps`. The API and the language guarantees are unchanged; the insides are not. Older
material (and some interviewers) describe the previous design — bucketed chaining, section 2.3 — so
know both, and say which toolchain you mean.

```arch
%% caption: The Swiss-table map, from the outside in. A small map (at most 8 entries) is ONE group and skips the directory and tables.
grid 200x100
node m "Map" at 0,0 icon=kv
node dir "Directory of tables" at 1,0 shape=card icon=folder
node t "Table" at 1,1 shape=card icon=table sub="an open-addressed array of groups, ≤ 1024 slots"
node g "Group" at 1,2 shape=card icon=grid sub="8 control bytes packed in one 64-bit word + 8 key/value slots"
node cb "Control byte" at 1,3 shape=card icon=number sub="1 bit empty / deleted / full + 7 bits of the key's hash (H2)"
m -> dir
dir -> t : "contains"
t -> g : "contains"
g -> cb : "per slot"
m:B -> g:L : "small map, ≤ 8 entries" dashed
```

```arch
%% caption: A Swiss-table lookup. The hash is split: high bits choose where to look, the low 7 bits are a cheap fingerprint tested against all 8 slots of a group at once.
grid 200x95
node k "m[key]" at 0,0 shape=pill
node h "Hash the key" at 0,1 icon=key shape=card sub="h = hash(key), seeded per map"
node t "Choose the table" at 0,2 shape=card icon=table sub="top bits choose the table (directory of tables)"
node g "Starting group" at 0,3 shape=card icon=grid sub="H1 = upper 57 bits picks the starting group"
node c "Compare H2" at 0,4 shape=card icon=filter color=blue sub="H2 = low 7 bits vs ALL 8 control bytes: a few bit operations on one word"
node m "a slot matches?" at 0,5 shape=diamond color=amber
node e "full key equal?" at 0,6 shape=diamond color=amber
node f "Found" at 0,7 shape=card icon=check color=green sub="return the value"
node x "group has an empty slot?" at 1,5 shape=diamond color=amber
node s "Quadratic probe" at 1,4 shape=card icon=sync color=orange sub="move to the next group"
node n "Absent" at 2,5 shape=card icon=check color=green sub="return the zero value"
k -> h -> t -> g -> c -> m
m -> e : "yes"
m -> x : "no"
e -> f : "yes"
e:R -> x:B : "no: 1 in 128 false positive"
x -> n : "yes"
x -> s : "no, group is full"
s -> c
```

The pieces, in the order a lookup uses them:

1. **Hash** the key with a **per-map random seed** (hardware-accelerated where the CPU allows). Every map has its own seed, so an attacker cannot precompute colliding keys —
   flooding resistance is built in, not opt-in.
2. The **top bits** index a **directory** of tables (*extendible hashing*). One table needs zero bits.
3. **H1** — the upper 57 bits — picks the starting **group** inside that table. **H2** — the low 7 bits — is stored in the
   control byte of every occupied slot, so one 64-bit compare rejects almost every non-matching slot
   without touching a key. Only a 1-in-128 false positive costs a real key comparison.
4. If the group has no match *and no empty slot*, keep going: **quadratic probing** to the next group.
   Because the table is never allowed to fill completely, a probe sequence always ends at a group with
   an empty slot, and that is what proves "absent".

**Load factor is 7/8** (a table averages 7 of every 8 slots full before it grows). Open addressing keeps
keys and values in one flat array, which is friendlier to the CPU cache than chasing overflow pointers.

### 2.2 Growth and deletion in the Swiss map

- **A table doubles until it reaches 1024 slots; after that it splits in two.** The directory doubles
  only when a table splits and the directory is already as deep as that table. Growing a table rehashes
  *that table only* — at most 1024 slots — so no single insert ever pays for the whole map.
  (The pre-1.24 map bounded the pause differently: it moved a couple of buckets per write. The goal —
  no O(n) stall inside one `m[k] = v` — is the same, and worth saying in a systems interview.)
- **Deletion needs care in open addressing.** A slot in a *full* group becomes a **tombstone** (deleted),
  because probing for another key may have walked *through* that group and must not stop early. If the
  group still has an empty slot, the deleted slot simply becomes empty. Inserts reuse tombstones first;
  a grow clears them.
- **Presizing still helps.** `make(map[K]V, n)` sizes the directory and tables up front, so the loop that
  follows never grows. Do it whenever `n` is known (Group Anagrams, Top K Frequent, Two Sum).

### 2.3 Before Go 1.24: 8-slot buckets, `tophash` and incremental evacuation

This is the map every Go release up to 1.23 shipped — and the one most articles, and many
interviewers, still describe. It was **bucketed separate chaining** (`runtime/map.go`): each bucket
holds **exactly 8** key/value pairs and chains to an overflow bucket when full. (Go 1.24 can still
build it: `GOEXPERIMENT=noswissmap go build`.)

```go
type hmap struct {
    count     int            // len(m) — O(1)
    B         uint8          // there are 2^B buckets
    buckets   unsafe.Pointer // array of 2^B bmap
    oldbuckets unsafe.Pointer // non-nil while growing (incremental evacuation)
    ...
}

type bmap struct {
    tophash [8]uint8        // top 8 bits of each key's hash
    // followed in memory by: 8 keys, then 8 values, then an overflow pointer
}
```

Lookup of key `k`:

1. `h := hash(k)`
2. Low `B` bits select the bucket: `bucket = h & (2^B - 1)`
3. **Top 8 bits** become `tophash` — compare that byte against the bucket's 8
   `tophash` entries first. This is the speed trick: 8 one-byte comparisons
   reject non-matches without ever touching the (possibly large) keys.
4. On a `tophash` hit, compare the full key.
5. If the bucket is full and the key isn't there, follow the **overflow pointer**
   to a chained bucket.

```
   hash(key) = 0x3F2A...B7
               └──┬──┘   └┬┘
          tophash│        │ low B bits → bucket index
                 ▼        ▼
   buckets[i] ┌──────────────────────────────────────┐
              │ tophash: [B7][2C][00][00][00]...     │  ← scan these 8 bytes
              ├──────────────────────────────────────┤
              │ keys:    [k0][k1][ ][ ][ ][ ][ ][ ]  │
              │ values:  [v0][v1][ ][ ][ ][ ][ ][ ]  │
              │ overflow ────────────────────────────┼──► another bmap
              └──────────────────────────────────────┘
```

**Note the layout: all 8 keys together, then all 8 values.** Not interleaved.
This avoids padding waste from alignment — e.g. `map[int64]int8` would waste
7 bytes per pair if interleaved.

**Growth and incremental evacuation.**

Go grows when the **load factor exceeds 6.5 entries per bucket** (`loadFactorNum/
loadFactorDen` = 13/2), or when there are too many overflow buckets.

Critically, Go **does not rehash everything at once**. It allocates the new bucket
array, keeps the old one in `oldbuckets`, and **evacuates one or two buckets per
write operation**. This spreads the O(n) rehash cost across many operations so no
single insert stalls — important for latency-sensitive services, and a genuinely
good thing to mention in a systems interview.

### 2.4 Map complexity and the gotchas

| Operation | Average | Worst |
|---|:--:|:--:|
| `m[k]` lookup | **O(1)** | O(n) |
| `m[k] = v` | **O(1)** amortized | O(n) |
| `delete(m, k)` | **O(1)** | O(n) |
| `len(m)` | **O(1)** | O(1) |
| Iterate | O(n) | O(n) |

**The comma-ok idiom** — Go returns the zero value for a missing key, so you
cannot distinguish "absent" from "present with value 0" without it:

```go
v := m["missing"]           // 0 — is it absent, or stored as 0?
v, ok := m["missing"]       // ok == false  ← always use this form
if _, seen := set[x]; seen { ... }
```

> ⚠️ **Map iteration order is deliberately randomized.** Go picks a random start
> bucket and offset on every `range`. This is not "unspecified but stable" — it
> genuinely differs run to run, to stop anyone depending on it. If you need
> deterministic output, collect keys and sort them:
> ```go
> keys := make([]string, 0, len(m))
> for k := range m { keys = append(keys, k) }
> slices.Sort(keys)
> ```
> This bites people whose LeetCode submission passes locally and fails on the
> judge. Python dicts *are* insertion-ordered; Go maps are not. Do not port that
> assumption across.

**Other rules:**
- Keys must be **comparable** (`==` defined): no slices, maps, or functions.
  Arrays and structs of comparable types work — `map[[2]int]bool` is a great
  way to key a grid coordinate.
- **You cannot take the address of a map element** (`&m[k]` is a compile error)
  because growth moves entries. Read, modify, write back.
- **You cannot assign to a struct field through a map**: `m[k].field = v` fails
  for a value-typed struct. Use `map[K]*Struct`, or read-modify-write.
- A `nil` map **reads fine** (returns zero) but **panics on write**. Always
  `make(map[K]V)` before writing.

### 2.5 Go has no set — use `map[T]struct{}`

```go
set := make(map[int]struct{})
set[x] = struct{}{}                 // add
_, exists := set[x]                 // contains
delete(set, x)                      // remove
len(set)                            // size
```

`struct{}` occupies **zero bytes**, so this costs nothing beyond the keys.
`map[int]bool` is more readable and lets you write `if set[x]` directly, at the
cost of 1 byte per entry. Both are accepted in interviews — say which tradeoff
you picked and why.

### 2.6 Counting and grouping

Go has no `Counter` or `defaultdict`, but the zero value makes it painless:

```go
freq := make(map[rune]int)
for _, c := range s {
    freq[c]++              // missing key reads as 0, then increments — no init
}

groups := make(map[string][]string)
for _, w := range words {
    k := canonical(w)
    groups[k] = append(groups[k], w)   // append to a nil slice works
}
```

Both idioms lean on Go's zero values: `int` → 0, and `nil` slice → valid empty
slice. This is the direct equivalent of `defaultdict(int)` and `defaultdict(list)`.

### 2.7 Strings, bytes, and runes — the trap in every string problem

A Go `string` is an **immutable read-only byte slice**, not a character array.

```go
s := "héllo"
len(s)                  // 6 — BYTES, not characters! é is 2 bytes in UTF-8
s[1]                    // 0xC3 — a byte, of type byte (uint8), not a character
for i, r := range s {}  // r is a RUNE (int32 codepoint); i jumps 1→3 across é
[]rune(s)               // O(n) decode into 5 codepoints — index this for chars
[]byte(s)               // O(n) copy of the raw bytes
```

| You want | Use |
|---|---|
| ASCII-only problems (most of LeetCode) | `s[i]` as `byte`, and `s[i] - 'a'` |
| Unicode-correct character access | `[]rune(s)` |
| Building a string in a loop | `strings.Builder` — **never** `s += x` |

> ⚠️ `s += x` in a loop is **O(n²)**: strings are immutable, so each `+=`
> allocates and copies the whole accumulated string. `strings.Builder` amortizes
> to O(n):
> ```go
> var sb strings.Builder
> sb.Grow(n)                  // preallocate if you know the size
> for _, w := range parts { sb.WriteString(w) }
> return sb.String()          // no final copy — unsafe-casts the buffer
> ```

For frequency counting over ASCII, prefer a fixed array to a map — it is
dramatically faster and allocation-free:
```go
var freq [26]int
for i := 0; i < len(s); i++ { freq[s[i]-'a']++ }
```

---

## Part 3 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| Dynamic array | `list` (array of **pointers**) | `[]T` (array of **values**) |
| Slicing | **O(k)** copy | **O(1)** view, **aliases** |
| Growth factor | ~1.125x | 2x under 256, then ~1.25x |
| Hash collisions | Open addressing, perturbed probe | Open addressing in 8-slot groups (Swiss table, Go 1.24+); chained buckets before |
| Map ordering | Insertion-ordered (3.7+) | **Randomized** |
| Rehash | All at once | **Bounded**: one table (≤ 1024 slots) at a time |
| Set type | Built-in `set` | `map[T]struct{}` |
| Sort stability | **Stable** (Timsort) | **Unstable** (`sort.Slice`) |
| String indexing | Characters | **Bytes** |
| Missing map key | `KeyError` | **Zero value** (use comma-ok) |
| Integer overflow | Never (arbitrary precision) | **Wraps** at 64 bits ⚠️ |

That last row matters: `left + (right-left)/2` in Go is not paranoia the way it is
in Python — `(left+right)/2` genuinely overflows for large indices. Write the
safe form by habit.

---

## Part 4 · Algorithms Owned by This Topic

| Algorithm | Time | Space | Problem |
|---|:--:|:--:|---|
| Single pass / linear scan | O(n) | O(1) | Most Easy problems |
| Hash-map complement lookup | O(n) | O(n) | LC 1 Two Sum |
| Frequency array (ASCII) | O(n) | O(1) | LC 242, 383 |
| Canonical-key grouping | O(n·k) | O(n·k) | LC 49 Group Anagrams |
| Bucket sort by frequency | O(n) | O(n) | LC 347 Top K Frequent |
| Prefix/suffix product sweep | O(n) | O(1)* | LC 238 |
| Index-as-hash sign marking | O(n) | O(1) | LC 41, 448 |
| Boyer–Moore majority vote | O(n) | O(1) | LC 169 |
| Set-based sequence walk | O(n) | O(n) | LC 128 |
| pdqsort | O(n log n) | O(log n) | Any "sort first" solution |

\* excluding the output slice

---

## Part 5 · Building a Hash Map From Scratch (LC 706)

```go
package main

const (
    initialCapacity = 1024
    maxLoadFactor   = 0.75
)

type entry struct {
    key, value int
    next       *entry      // chaining
}

type MyHashMap struct {
    buckets []*entry
    size    int
}

func Constructor() MyHashMap {
    return MyHashMap{buckets: make([]*entry, initialCapacity)}
}

// index masks instead of using %, which requires a power-of-two capacity.
func (m *MyHashMap) index(key int) int {
    h := key * 0x9E3779B1              // Knuth multiplicative hash (2^32 / phi)
    if h < 0 {
        h = -h
    }
    return h & (len(m.buckets) - 1)
}

func (m *MyHashMap) Put(key, value int) {
    i := m.index(key)
    for e := m.buckets[i]; e != nil; e = e.next {
        if e.key == key {
            e.value = value            // overwrite
            return
        }
    }
    m.buckets[i] = &entry{key: key, value: value, next: m.buckets[i]}  // prepend
    m.size++
    if float64(m.size)/float64(len(m.buckets)) > maxLoadFactor {
        m.resize()
    }
}

func (m *MyHashMap) Get(key int) int {
    for e := m.buckets[m.index(key)]; e != nil; e = e.next {
        if e.key == key {
            return e.value
        }
    }
    return -1
}

func (m *MyHashMap) Remove(key int) {
    i := m.index(key)
    var prev *entry
    for e := m.buckets[i]; e != nil; e = e.next {
        if e.key == key {
            if prev == nil {
                m.buckets[i] = e.next
            } else {
                prev.next = e.next
            }
            m.size--
            return
        }
        prev = e
    }
}

func (m *MyHashMap) resize() {
    old := m.buckets
    m.buckets = make([]*entry, len(old)*2)
    m.size = 0
    for _, head := range old {
        for e := head; e != nil; e = e.next {
            m.Put(e.key, e.value)      // rehash: index depends on capacity
        }
    }
}
```

**Talk track while writing:** prepending to the chain is O(1) and avoids walking
to the tail; capacity stays a power of two so `&` replaces `%`; the load factor
is the time-space dial; resize is O(n) but amortizes away.

---

<!-- block:01_go_1_choose -->
## Part 6 · Choosing the Structure in Go

```arch
%% caption: Which Go container fits the question being asked. Go has no built-in set, Counter or deque, so the answer is always a slice, an array or a map.
grid 190x100
node q "What do you need from the data?" at 1,0 shape=pill
node a "Only: have I seen this before?" at 1,1 shape=diamond color=amber
node s "Set" at 0,1 shape=card icon=check color=green sub="map[T]struct{} or map[T]bool"
node b "A value or count per key?" at 1,2 shape=diamond color=amber
node c "[26]int array" at 0,3 shape=card icon=counter color=green sub="e.g. a-z; no hashing, no allocation"
node d "map[K]V" at 2,3 shape=card icon=kv color=green sub="arrays and structs are valid keys"
node e "Position or order matters?" at 1,4 shape=diamond color=amber
node f "[]T slice" at 0,5 shape=card icon=table color=green
node g "Sort, then search" at 1,5 shape=card icon=sort color=green sub="slices.Sort once, then slices.BinarySearch"
node hp "container/heap" at 2,5 shape=card icon=tree color=green
q -> a
a -> s : "yes"
a -> b : "no"
b -> c : "key in a small fixed range"
b -> d : "any comparable key"
b -> e : "neither"
e -> f : "by index"
e -> g : "sorted order, ranges"
e -> hp : "repeated min or max"
```

| You need | Python | Go |
|---|---|---|
| "Have I seen this?" | `set` | `map[T]struct{}` |
| Frequencies | `Counter` | `map[T]int` — or `[26]int` for lowercase ASCII |
| Group by a property | `defaultdict(list)` | `map[K][]V` (append to a nil slice just works) |
| A composite key | `tuple` | an **array** (`[26]int`, `[2]int`) or a **struct** — both comparable |
| A queue | `deque` | a slice with a head index (topic 07) |
| Repeated min / max | `heapq` | `container/heap` (topic 12) |
| Ordered traversal of keys | `sorted(d)` | `slices.Sorted(maps.Keys(m))` (Go 1.23+) |

**Space-time tradeoff, stated for interviews:** a map buys O(1) lookup for O(n) extra memory. When the
interviewer says "now in O(1) space", they are removing the map — pivot to sorting (`slices.Sort`,
O(n log n), reorders the input), two pointers, or index-as-hash.

---
<!-- /block:01_go_1_choose -->

<!-- block:01_go_2_traps -->
## Part 7 · The Traps That Live in This Topic

Every one of these compiles and runs. Each was reproduced on Go 1.24.5 while writing this section.

### 7.1 `append` can write into someone else's array — not only via sub-slices

```go
a := []int{1, 2, 3, 4}
b := append(a[:2], 99)      // a[:2] has len 2, cap 4: there is ROOM, so append writes in place
// a == [1 2 99 4]   ← the caller's slice changed
// b == [1 2 99]

c := append(a[:2:2], 77)    // three-index slice: cap 2, so append MUST reallocate
// a is untouched
```

The rule to internalise: **`append` mutates the backing array whenever `len < cap`.** Any time you
append to a slice you did not just create, ask "who else shares this array?". `append(nums, nums...)`
on a caller's slice is exactly this bug (LC 1929). `slices.Clone(s)` is the one-line safe copy.

### 7.2 `range` over an array copies the array; over a slice it does not

```go
arr := [3]int{1, 2, 3}
for i, v := range arr { arr[2] = 100; if i == 2 { fmt.Println(v) } }   // prints 3 — ranged over a COPY

sl := []int{1, 2, 3}
for i, v := range sl { sl[2] = 100; if i == 2 { fmt.Println(v) } }     // prints 100 — same backing array
```

Arrays are values, so ranging one evaluates a copy first (cheap for `[26]int`, expensive for a large
array — range `&arr` or `arr[:]` to avoid it). This is the same value-vs-header split as section 1.1.

### 7.3 Loop variables are per-iteration since Go 1.22

```go
var ptrs []*int
for i := 0; i < 3; i++ { ptrs = append(ptrs, &i) }
fmt.Println(*ptrs[0], *ptrs[1], *ptrs[2])     // 0 1 2 on Go 1.22+   (was 3 3 3 before)
```

Before 1.22 every iteration shared one variable, so `&i`, closures and goroutines all saw the final
value. The new behaviour applies when the module's `go.mod` says `go 1.22` or later (this repo's does).
If you read older answers that write `i := i` "to be safe", that is why.

### 7.4 Deleting while ranging a map is **legal** (unlike Python)

```go
for k := range m { if k%2 == 0 { delete(m, k) } }     // fine: a deleted, not-yet-reached entry is never produced
```

Go allows it and defines it: an entry you delete before reaching it is not produced; an entry you
*add* during the loop **may or may not** be produced, and which it is can change run to run. So
delete freely, but never depend on seeing (or not seeing) what you insert. (Python raises
`RuntimeError` instead.)

### 7.5 Comparison rules

| Type | `==`? | Use instead |
|---|---|---|
| array `[N]T`, struct of comparable fields | ✅ | — (this is why they work as map keys) |
| slice, map, func | ❌ compile error (only `== nil`) | `slices.Equal(a, b)`, `maps.Equal(a, b)`, `reflect.DeepEqual` |

The payoff is Group Anagrams: `map[[26]int][]string` uses the letter-count *array itself* as the key,
so there is no key string to build.

```go
var k [26]int
for i := 0; i < len(w); i++ { k[w[i]-'a']++ }
groups[k] = append(groups[k], w)
```

### 7.6 Integer overflow wraps silently

`int` is 64 bits on a 64-bit machine, and arithmetic wraps with **no panic and no flag**:

```go
var x int64 = math.MaxInt64
x++            // -9223372036854775808
```

Prefix/suffix products (LC 238), running sums and hash mixing can all overflow. LeetCode guarantees
32-bit answers, so it never fires there — but say so out loud, and use `math/bits` or `math/big`
when the interviewer changes the constraints.

### 7.7 `strings.Builder` must not be copied after use

```go
var sb strings.Builder
sb.WriteString("x")
sb2 := sb                // copying a non-zero Builder…
sb2.WriteString("y")     // …panics: "strings: illegal use of non-zero Builder copied by value"
```

Pass `*strings.Builder` (or keep it in a struct you only pass by pointer).

### 7.8 Maps are not safe for concurrent use

Concurrent reads are fine. A write concurrent with anything else is a data race, and the runtime
detects many of them and **kills the program** with `fatal error: concurrent map writes` — a fatal
error, not a panic, so `recover` cannot catch it. Guard the map with a `sync.Mutex` / `sync.RWMutex`,
or use `sync.Map` for the read-mostly / disjoint-keys case. Worth a sentence whenever the interviewer
says "now make it thread-safe".

---
<!-- /block:01_go_2_traps -->

<!-- block:01_go_3_followups -->
## Part 8 · Follow-ups the Interviewer Reaches For

| Follow-up | The answer, in Go terms |
|---|---|
| "The data does not fit in memory." | **Hash-partition** to `k` files by `hash(x) % k` (`hash/maphash` or `hash/fnv`), then process one partition at a time. Approximate: a Bloom filter (membership, no false negatives) or a Count-Min sketch (frequency, over-counts only). |
| "It is a stream." | Incremental `map`/counter; **Misra–Gries** generalises Boyer–Moore — `k − 1` counters find every element occurring more than `n/k` times. |
| "The slice is already sorted." | Drop the map: two pointers in O(1) space (topic 02) or `slices.BinarySearch` (topic 05). |
| "O(1) extra space." | `slices.Sort` in place (O(n log n), **reorders the caller's slice**), index-as-hash for values in `1..n`, or a write-index pass. |
| "Implement the map yourself." | Part 5: chaining, power-of-two capacity, load factor, full rehash on resize. Open addressing needs tombstones — Go's own map does exactly that. |
| "Keys are adversarial." | Go seeds every map's hash randomly, so precomputed collisions do not work; for your *own* table use `hash/maphash` (Go 1.24's `maphash.Comparable` hashes any comparable value). |
| "Not just `a–z`." | `[26]int` → `map[rune]int`; range over the string for runes, not `s[i]`. Ask about normalisation (`é` as one code point or two). |
| "Return every pair." | Output size dominates — state the complexity in terms of it. |
| "Can an element be used twice?" | Look up the complement *before* inserting the current value. |
| "Make it thread-safe." | `sync.RWMutex` around the map, or `sync.Map`; the built-in map crashes on concurrent writes (the Traps part, item 8). |

---
<!-- /block:01_go_3_followups -->

<!-- problem-map:start -->
## Part 9 · Every Problem in This Topic, by Pattern

Fourteen problems, seven moves — the same ones as the Python guide, with the Go spelling of each and the Go-only traps. Problems 001–006 have full Go solutions in the folder; 007–014 are Python-first, so treat the Go column as the plan you would write.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Concatenation of Array](GoDSA/01_arrays_hashing/001_concatenation_of_array/solution.go) <br>LC 1929 · Easy | Preallocate + `copy` | `ans := make([]int, 2*n); copy(ans, nums); copy(ans[n:], nums)` — one allocation, no aliasing. **Trap:** `append(nums, nums...)` writes into the caller's spare capacity; `make([]int, 0, 2*n)` then *indexing* panics (that sets cap, not len). |
| [002 · Contains Duplicate](GoDSA/01_arrays_hashing/002_contains_duplicate/solution.go) <br>LC 217 · Easy | Seen-set | `map[int]struct{}` (or `map[int]bool`) turns O(n²) into O(n). **Trap:** check *then* insert; `if seen[x]` does not compile on `struct{}` values; writing to a `nil` map panics — `make` it. |
| [003 · Valid Anagram](GoDSA/01_arrays_hashing/003_valid_anagram/solution.go) <br>LC 242 · Easy | Fixed array counts | `var counts [26]int` — no hashing, no heap allocation; switch to `map[rune]int` only for Unicode. **Trap:** `len(s)` counts *bytes*; `for i := range s` then `s[i]` silently brings byte semantics back; forgetting the length guard. |
| [004 · Two Sum](GoDSA/01_arrays_hashing/004_two_sum/solution.go) <br>LC 1 · Easy | Complement lookup | One pass, comma-ok: `if j, ok := seen[target-x]; ok`. **Trap:** `seen[c] != 0` fails *both ways* — index 0 is a valid answer and an absent key also reads 0. |
| [005 · Majority Element](GoDSA/01_arrays_hashing/005_majority_element/solution.go) <br>LC 169 · Easy | Boyer–Moore vote | O(n) time, O(1) space; the majority outnumbers everything else combined. **Trap:** with no guaranteed majority it returns garbage with total confidence; `sort.Ints` reorders the caller's slice (slices alias). |
| [006 · Find All Numbers Disappeared in an Array](GoDSA/01_arrays_hashing/006_find_all_numbers_disappeared_in_an_array/solution.go) <br>LC 448 · Easy | Index-as-hash | Negate `nums[\|v\|-1]`; Go has no integer `abs` (`math.Abs` is float), so write `if v < 0 { v = -v }`. **Trap:** skip it and you get `panic: index out of range` — Python would silently index from the end. |
| [007 · Group Anagrams](GoDSA/01_arrays_hashing/007_group_anagrams/solution.go) <br>LC 49 · Medium | Comparable-array key | `map[[26]int][]string` uses the count array itself as the key — no key string to build; for Unicode, sort the runes. **Trap:** slices are not valid map keys (compile error); sorting the input word in place mutates the caller's data. |
| [008 · Top K Frequent Elements](GoDSA/01_arrays_hashing/008_top_k_frequent_elements/solution.go) <br>LC 347 · Medium | Bucket by frequency | `map[int]int` for counts, then `buckets := make([][]int, n+1)` indexed by frequency. **Trap:** `n` vs `n+1` buckets; map order is random, so ties come out in a different order every run — never assert on it. |
| [009 · Encode and Decode Strings](GoDSA/01_arrays_hashing/009_encode_and_decode_strings/solution.go) <br>LC 271 · Medium | Length-prefix framing | `strconv.Itoa(len(s)) + "#" + s`; decode with `strings.IndexByte` and `strconv.Atoi`, jumping past each payload. **Trap:** lengths are *bytes* in Go — stay in bytes on both sides; mixing `len(s)` with `[]rune` indexing corrupts non-ASCII payloads. |
| [010 · Product of Array Except Self](GoDSA/01_arrays_hashing/010_product_of_array_except_self/solution.go) <br>LC 238 · Medium | Prefix × suffix | Two sweeps writing into the result slice, O(1) extra space. **Trap:** a running product that starts at 0 (the empty product is 1); updating the runner before writing; `int` overflow wraps silently. |
| [011 · Valid Sudoku](GoDSA/01_arrays_hashing/011_valid_sudoku/solution.go) <br>LC 36 · Medium | Fixed boolean grids | `[9][9]bool` per row/column/box — arrays are values, zeroed, allocation-free; box index `(r/3)*3 + c/3` with integer division. **Trap:** `%` instead of `/` mixes distant boxes yet passes many boards. |
| [012 · Longest Consecutive Sequence](GoDSA/01_arrays_hashing/012_longest_consecutive_sequence/solution.go) <br>LC 128 · Medium | Set + sequence heads | `map[int]struct{}`; walk only when `x-1` is absent, and range over the *set* so duplicates cost nothing. **Trap:** drop the guard and it is still correct but O(n²). |
| [013 · Next Permutation](GoDSA/01_arrays_hashing/013_next_permutation/solution.go) <br>LC 31 · Medium | Right-to-left scan | Find the pivot, swap, then `slices.Reverse(nums[i+1:])` — reversing a *sub-slice* in place is aliasing used on purpose. **Trap:** a non-strict comparison swaps equal values and the permutation goes backwards. |
| [014 · Isomorphic Strings](GoDSA/01_arrays_hashing/014_isomorphic_strings/solution.go) <br>LC 205 · Easy | Bijection = two maps | ASCII: two `[256]byte` tables (0 = unmapped); Unicode: `map[rune]rune`. **Trap:** checking only `s→t` accepts `"badc"`/`"baba"`. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] Draw the 3-word slice header and explain `len` vs `cap`
- [ ] Explain why sub-slicing aliases, and when you must `copy`
- [ ] Explain why `append` is O(1) *amortized*, and Go's growth rule
- [ ] Explain the Swiss-table map (groups, H1/H2, 7/8 load) — and the pre-1.24 bucket + `tophash` layout
- [ ] Explain why growth is bounded (tables split at 1024 slots) and why that helps tail latency
- [ ] Say why map iteration order is randomized — and how to get determinism
- [ ] Use comma-ok reflexively
- [ ] Explain `len(s)` on a string returning bytes, not characters
- [ ] Know that `sort.Slice` is unstable but Python's `sort` is stable
- [ ] Write a hash map with chaining and resizing in under 15 minutes
- [ ] Say when `append` writes into a shared backing array, and fix it with `slices.Clone` or a three-index slice <!--ca-->
- [ ] Know that `range` over an array copies it, and that Go 1.22 made loop variables per-iteration <!--ca-->
- [ ] Use an array (`[26]int`) as a map key for Group Anagrams <!--ca-->
- [ ] Say what changes when a map is used from two goroutines <!--ca-->
- [ ] Pick the row of the problem table above from the *wording* of a statement, before coding <!--ca-->
