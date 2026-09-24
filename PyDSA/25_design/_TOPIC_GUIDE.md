# Topic 25 · Design — Python Deep Dive

> Every prior topic organized itself around ONE data structure or ONE
> search strategy that you apply to a given input. This topic inverts
> that: **you are handed a set of REQUIRED OPERATIONS with REQUIRED
> COMPLEXITY BOUNDS, and you must choose (and usually COMBINE) the right
> data structures to hit every bound simultaneously.** No single built-in
> container — `dict`, `list`, `set`, `deque`, `heapq` — satisfies more
> than one or two of the constraints a given design problem imposes.
> The graded skill is recognizing exactly WHICH complementary pair (or
> trio) of structures closes the gap, and keeping them consistent as the
> object mutates. This is also, not coincidentally, close to how real
> system-design interviews are scored — this topic is the DSA-scale
> rehearsal for that instinct.

---

## Part 0 · The ten problems and their tricks

**Bucket array + modulus hashing, hand-built** (001 Design HashSet, 002
Design HashMap): with the built-in `dict`/`set` banned, you re-derive what
they do internally — an array of "buckets," each a small list, addressed
by `key % NUM_BUCKETS`. The graded insight isn't the bucket idea itself
(everyone reaches for it) but recognizing WHY the bucket count matters:
too few buckets and you've built an O(n) list wearing a hash table's
clothes; a prime bucket count avoids systematic clustering when keys share
common factors with it. This is topic 01's whole "hash map as O(1)
lookup" lesson, just with the machine opened up and the bucket-count
choice made explicit instead of delegated to CPython.

```arch
%% caption: A hand-built hash set: hash to a bucket, then scan the short chain.
grid 190x95
node K "key" at 0.5,0 shape=pill
node H "index = key % bucket_count" at 0.5,1 w=200
node B "bucket at index" at 0.5,2 sub="a short list"
node C "scan the chain for key" at 0.5,3 color=amber
node D "append if absent" at 0,4 color=green
node E "delete it, or report" at 1,4 color=green
K -> H -> B -> C
C -> D : "add"
C -> E : "remove or contains"
```


**Store the NEXT eligible time, not the last-used time** (003 Logger Rate
Limiter): a tiny hashmap holding `message -> next_allowed_timestamp`
turns "was this used too recently" into a single comparison per call,
with the missing-key case falling out for free via `dict.get(key,
timestamp)` — no separate "have I seen this before" branch needed. The
lesson generalizes past this one problem: whenever a check is "has enough
time/distance/count passed since X," store the THRESHOLD directly rather
than the raw last-observed value plus a recomputation at check time.

**Two sentinel nodes turn boundary cases into ordinary cases** (004
Design Linked List): a dummy head AND a dummy tail eliminate every
"is the list empty," "am I inserting at the very front/back" branch —
this is topic 08's LRU Cache idiom, applied here to INDEX-based rather
than recency-based traversal. A doubly linked list plus a maintained
`size` counter also lets you walk from whichever END is closer to the
target index, roughly halving average traversal distance for free.

**When a set can't give you random access, marry it to an array** (005
Insert Delete GetRandom O(1)): a hash set alone has no notion of "the
k-th element" — you cannot pick a uniformly random element from it in
O(1). An array alone gives O(1) random access by index but O(n) removal
by value. The fix: an array PLUS a `value -> index` dict, and the
non-obvious deletion trick — swap the target with the array's LAST
element, fix the moved element's index in the dict, then pop the last
slot. This avoids ANY shifting, and critically keeps the array physically
dense (no gaps/tombstones), which is exactly what `getRandom`'s uniform
index pick needs to stay uniform.

**A cursor into an array, not a linked list, when there's exactly one
"current position"** (006 Design Browser History): despite superficially
resembling a linked-list problem (back/forward navigation), the access
pattern here is purely index-relative with no arbitrary-node splicing
ever required — an array plus an integer cursor, with `visit` TRUNCATING
everything past the cursor before appending, is simpler and just as fast
as a doubly linked list would be. The lesson: don't reach for topic 08's
tools out of habit when the actual access pattern doesn't need them.

**deque (ordered) + set (O(1) lookup), with careful ordering of the tail
removal** (007 Design Snake Game): the snake's body needs O(1)
push-to-head/pop-from-tail (a `deque`) AND O(1) "does my new head collide
with my own body" (a mirrored `set`). The one genuinely subtle bit: the
TAIL must be freed from both structures BEFORE the collision check —
UNLESS food was just eaten (the tail stays, the snake grows) — because
moving into a cell your own tail is vacating THIS turn is legal, while
moving into a cell that's about to remain occupied is not.

**A doubly linked list PER FREQUENCY BUCKET, plus a running minimum
pointer** (008 LFU Cache, Hard): this is LRU Cache generalized along a
second axis. Eviction order is (frequency ascending, then recency
ascending as the tiebreaker) instead of recency alone — so instead of ONE
doubly linked list, you need ONE PER FREQUENCY VALUE, plus a `min_freq`
integer that only ever resets to 1 (new key) or increments by exactly 1
(the current minimum bucket just emptied). The reason an integer suffices
instead of a general "find current minimum" structure: frequencies only
ever increase by exactly 1 per access, so the minimum can never jump —
this is the load-bearing invariant that makes O(1) achievable at all.

**A tree of dict-of-named-children nodes, one node type wearing two
hats** (009 Design In-Memory File System, Hard): structurally identical to
a trie (topic 13) — one node per path segment, `children: dict[str,
Node]` — except each node must ALSO distinguish "I am a directory" from
"I am a file" (payload type, not just "is this a complete word"). The
whole operation set (`ls`, `mkdir`, `addContentToFile`,
`readContentFromFile`) reduces to one shared walk helper, parameterized
by whether missing directories should be CREATED along the way or not.

**A trie extended from "does this prefix exist" to "rank its top-K
completions"** (010 Design Search Autocomplete System, Hard): storing a
sentence's hot-degree only at its OWN terminal trie node (topic 13's
usual pattern) is not enough here — every INTERMEDIATE prefix node along
a sentence's path needs to know that sentence exists, so a query for any
shorter prefix can rank it. This is a genuine space-for-query-time trade
(each sentence's score gets duplicated at every one of its own prefix
nodes), made explicit and priced against the honest brute-force
alternative (rescan every historical sentence on every keystroke) rather
than assumed to be free.

---

## Part 1 · The throughline: no single structure satisfies every bound

Look at what's actually happening across all ten problems: in EVERY case,
the LeetCode-imposed complexity requirement (usually "O(1)," sometimes
"O(log n)" or "O(prefix length)") is IMPOSSIBLE with any single stock
container, because the required operations pull in different directions:

```arch
%% caption: RandomizedSet remove in O(1): the array gives random access, the map gives lookup, and swap-with-last avoids shifting. Both structures must be updated together.
grid 200x95
node R "remove(val)" at 0,0 shape=pill
node S "i = index_of[val]" at 0,1
node T "arr[i] = arr[-1]" at 0,2 sub="the last element fills the hole"
node U "index_of[arr[i]] = i" at 0,3
node V "arr.pop()\ndel index_of[val]" at 0,4 color=green
R -> S -> T -> U -> V
```


| Tension | Structure that wins one side | Structure that wins the other | The fix |
|---|---|---|---|
| lookup-by-key vs. order | hashmap | linked list | dict of node refs + doubly linked list (004, 008, and LRU Cache in topic 08) |
| lookup-by-value vs. random access by position | set | array | array + value→index dict, swap-pop deletion (005) |
| O(1) access vs. O(1) reorder-by-recency | array | linked list | same dict+DLL combination, generalized to per-bucket in 008 |
| exact-string lookup vs. ranked top-K | hashmap of exact strings | sorted structure | trie with a per-node ranking index (010) |
| membership vs. structural traversal | set | tree/array of children | tree of nodes wearing a type tag (009) |

The interview signal this topic tests is NOT "do you know what a hashmap
is" — it's "can you look at a REQUIREMENT LIST (not a single big-O target,
but several simultaneous ones across different methods) and identify
which single structure fails which requirement, then reach for its
complement." That's a categorically different skill from "pick the right
algorithm for this array," which is why this topic exists as its own
category even though every individual building block (hashing, linked
lists, tries, heaps) is taught elsewhere.

---

## Part 2 · Problem-by-problem map

| # | Problem | Difficulty | Core trick |
|---|---|---|---|
| 001 | Design HashSet | Easy | bucket array + `key % N`, separate chaining |
| 002 | Design HashMap | Easy | same, buckets hold (key, value) pairs |
| 003 | Logger Rate Limiter | Easy | dict of `message -> next_allowed_timestamp` |
| 004 | Design Linked List | Medium | doubly linked, dummy head+tail, maintained size |
| 005 | Insert Delete GetRandom O(1) | Medium | array + value→index dict, swap-pop deletion |
| 006 | Design Browser History | Medium | array + cursor, `visit` truncates forward history |
| 007 | Design Snake Game | Medium | deque (order) + set (O(1) collision), tail-vacates-first |
| 008 | LFU Cache | Hard | dict + doubly-linked-list PER frequency bucket + min_freq |
| 009 | Design In-Memory File System | Hard | tree of dict-of-children nodes, dir/file type tag |
| 010 | Design Search Autocomplete System | Hard | trie with per-node `sentence -> hot_degree` index |

---

## Part 3 · Cross-references worth remembering

- **001/002 ↔ topic 01** (Arrays & Hashing): this topic hand-builds, from
  first principles, exactly the machinery topic 01's problems take for
  granted every time they reach for a Python `dict`/`set`. If separate
  chaining or open addressing ever feels unfamiliar, topic 01's problems
  are the "what it's FOR" half of this topic's "how it WORKS" half.
- **004, 008 ↔ topic 08** (Linked List): 004 is a direct generalization of
  topic 08's splicing discipline to index-based (not reference-based)
  access; 008's per-frequency doubly linked lists are literally N copies
  of LRU Cache's (013) dummy-head/tail list, one per frequency value —
  if LRU Cache isn't automatic, LFU Cache will be much harder than it
  needs to be.
- **009 ↔ topic 13** (Trie): identical `children: dict[str, Node]` node
  shape; the only addition is a directory/file type tag on top of what a
  trie node already looks like.
- **010 ↔ topic 13** (Trie) **and topic 12** (Heap): the trie structure is
  topic 13's bread and butter; the "top-K instead of exact top-1"
  ranking question this problem raises in its follow-ups (bound each
  node's index to a fixed-size min-heap instead of an unbounded dict) is
  topic 12's territory, applied per-trie-node instead of globally.
- **005 ↔ topic 27** (Classic Algorithms): `getRandom`'s uniform-index
  pick is the simplest case of the "pick with correctness guarantees"
  family that topic 27 develops much further (weighted picks, reservoir
  sampling, blacklist remapping) — 005 is where that family's simplest
  member lives.

---

## Part 4 · A general checklist for any design problem

When a design problem hands you a class with several methods and a
per-method complexity target, work through these questions in order
before writing any code:

```arch
%% caption: The design-problem routine: bounds first, then structures, then the invariant that keeps them in sync.
grid 260x100
node A "List every operation and its required bound" at 0,0 w=230
node B "For each one: which structure gives that bound?" at 0,1 w=230
node C "One structure covers all of them?" at 0,2 shape=diamond color=amber
node D "use it" at 1,2 color=green
node E "Combine structures" at 0,3 color=amber sub="map + list, map + heap, map + linked list" w=230
node F "State the invariant that ties them together" at 0,4 w=230
node G "Update BOTH on every mutation" at 0,5 w=230
A -> B -> C
C -> D : "yes"
C -> E : "no"
E -> F -> G
```


1. **List every required operation and its target complexity, side by
   side.** Don't start coding until you can see them all at once — the
   TENSION between them is usually visible immediately once they're
   listed together (e.g. "O(1) lookup" next to "O(1) in-order eviction"
   is the LRU/LFU tension; "O(1) random access" next to "O(1) removal by
   value" is the RandomizedSet tension).

2. **For each operation, ask: which SINGLE structure gives me this for
   free?** Usually more than one operation maps to the same structure —
   group them.

3. **Where two operations map to DIFFERENT structures, you need BOTH,
   kept in sync.** This is the single most common bug source in this
   entire topic: updating one structure (the dict) on an operation and
   forgetting the other (the linked list / array / trie index) needs the
   SAME update. Every solution file's COMMON MISTAKES section in this
   topic has at least one instance of exactly this bug.

4. **Identify the ONE invariant that makes an O(1)/O(log n) shortcut
   valid**, and state it explicitly — e.g. LFU's "frequency only ever
   increases by 1 per access" is why a plain integer `min_freq` suffices
   instead of a general "find current minimum" structure; RandomizedSet's
   "the array is always physically dense, no tombstones" is why a uniform
   index pick stays uniform. If you can't name the invariant, you
   probably haven't found the O(1) design yet — you've found an O(n) or
   O(log n) one that happens to look similar.

5. **Trace the FIRST few calls by hand before trusting the code.** Every
   solution file in this topic includes a real STEP BY STEP trace with
   actual values for exactly this reason — design bugs are almost always
   ordering bugs (update A before B, or check X before mutating Y), and
   those are far easier to catch by hand-tracing 5-10 calls than by
   staring at the code structurally.

---

## Part 5 · Where this topic ends

Ten problems, spanning Easy through Hard, but all teaching the same
underlying move: **read the full method list and its complexity
requirements as ONE combined constraint, not as separate problems to
solve method-by-method.** The specific structures combined here — hash
tables, doubly linked lists, arrays with index maps, tries — are all
built elsewhere in the curriculum; what's new here is the DISCIPLINE of
keeping two or three of them consistent under mutation while hitting
every method's complexity bound simultaneously. That discipline is the
direct DSA-scale rehearsal for the "design X" round of a real interview
loop, which is exactly why this topic sits where it does in the plan.

---

## Part 6 · Added Problems (011–013) — Three Patterns Straight From Production Systems

Added 16 Sep 2026 from the Google prep plan. Part 0 above covers the original ten.

| # | Problem | Structure | The production system it's a miniature of |
|---|---|---|---|
| 011 | Design Hit Counter | 300 circular buckets tagged with their second | Rate limiters and metrics counters: memory fixed per window, not per event |
| 012 | Snapshot Array | per-index history of (snap_id, value) + bisect | MVCC / copy-on-write: store only what changed, versioned |
| 013 | Stock Price Fluctuation | dict as source of truth + two heaps with lazy validation | Derived indexes that tolerate stale entries and validate on read |

Measured in the files:

- **Hit counter**, 1,000,000 hits in one window: queue of timestamps peaked at ~39 MiB; 300 buckets at
  ~18 KiB. That's the follow-up the question is really about.
- **Snapshot array**, length 50,000 with 1,000 snaps: copy-on-snap peaked at ~382 MiB; per-index history
  at ~3.6 MiB.
- **Stock price**, 50,000 updates with interleaved max/min: scanning the dict took ~3.2 s; lazy heaps
  ~16 ms.

The throughline from Part 1 still holds: no single structure answers every query, so pair a source of
truth with one index per query shape, and decide how each index stays correct under updates.

- [ ] I can explain bucketed windows vs event queues, versioned histories vs copies, and lazy validation.

<!-- block:25_py_1_blocks -->
## Part 7 · The Building Blocks, Priced — Hash Tables, `OrderedDict`, Heaps with Lazy Deletion, Bisect

Part 1 says each design problem pairs two structures. This Part prices the parts you pair, so you can say *why* a combination meets a bound, and shows the stdlib shortcuts. All snippets ran on
CPython 3.13; timings are best of three.

```arch
%% caption: What the operation list demands picks the structure pair. Each row is one design problem's move.
grid 230x80
node Q "A design class with a list of operations" at 0,0 shape=pill w=210
node A "Which operation is the hard one?" at 0,1 shape=diamond color=amber
node pb "evict / reorder by recency" at 1,2 shape=pill w=210
node pc "uniform random pick + delete by value" at 1,3 shape=pill w=210
node pd "max/min under updates or corrections" at 1,4 shape=pill w=210
node pe "value as of a past time or version" at 1,5 shape=pill w=210
node pf "count in a sliding window" at 1,6 shape=pill w=210
node pg "top K completions of a prefix" at 1,7 shape=pill w=210
node B "hash map to nodes + doubly linked list" at 2,2 color=green sub="OrderedDict does both in C" w=250
node C "array + value to index map" at 2,3 color=green sub="swap-with-last delete" w=250
node D "source-of-truth map + heap" at 2,4 color=amber sub="lazy validation on read" w=250
node E "append-only history per key + bisect" at 2,5 color=green w=250
node F "fixed ring of time-tagged buckets" at 2,6 color=green w=250
node G "trie" at 2,7 color=amber sub="every node indexes the sentences through it" w=250
Q -> A
A -> pb:L
A -> pc:L
A -> pd:L
A -> pe:L
A -> pf:L
A -> pg:L
pb -> B
pc -> C
pd -> D
pe -> E
pf -> F
pg -> G
```

### 7.1 Hash tables: the bucket count is a design decision (Problems 001–002)

With `index = key % buckets`, keys that share a factor with the bucket count pile into few buckets. Measured with 1,000 keys that are multiples of 1,000 (and then of 1,024):

| Keys | Buckets | Longest chain |
|---|--:|--:|
| multiples of 1,000 | 1,000 | **1,000** — every key in one bucket |
| multiples of 1,000 | 1,009 (prime) | 1 |
| multiples of 1,024 | 1,024 | **1,000** |
| multiples of 1,024 | 1,009 (prime) | 1 |

A "round" bucket count turns the table into one linked list that still *works* — the reason Problem 001's traps call out a non-prime count. Real tables also **resize**: doubling the bucket array whenever
the load factor passes 0.75 costs 1,572,876 element moves over 10⁶ inserts (1.57 per insert) — amortised O(1), the same argument as list `append`. Python's `%` returns a non-negative result for a positive divisor, so
a negative key is safe here (`-5 % 1009 == 1004`); in Go it is not (see the Go guide).

### 7.2 `OrderedDict` is the LRU building block

`OrderedDict` is a hash map whose entries are also a doubly linked list, with `move_to_end(key)` and `popitem(last=False)` in O(1):

```python
from collections import OrderedDict

class LRU:
    def __init__(self, cap): self.cap, self.d = cap, OrderedDict()
    def get(self, k):
        if k not in self.d: return -1
        self.d.move_to_end(k); return self.d[k]          # most recent goes to the end
    def put(self, k, v):
        if k in self.d: self.d.move_to_end(k)
        self.d[k] = v
        if len(self.d) > self.cap: self.d.popitem(last=False)   # the front is the least recently used
```

It matched a list-based reference on 400 random operation sequences. Because it is implemented in C it beat a hand-built pure-Python doubly linked list: **34 ms** against **51 ms** for 300,000 operations at
capacity 1,000. Know both — an interviewer usually wants the linked list built by hand (topic 08), and `OrderedDict` is what you would ship. `functools.lru_cache(maxsize=…)` wraps this for pure functions:
after `f(1); f(2); f(1); f(3); f(1)` with `maxsize=2` its `cache_info()` reads `hits=2, misses=3, currsize=2`.

Plain `dict` is insertion-ordered (3.7+), so `next(iter(d))` is the oldest key and `d.popitem()` removes the *newest* — but a plain `dict` has no `move_to_end`. Mutating a dict while iterating it raises
`RuntimeError: dictionary changed size during iteration`.

### 7.3 Heaps have no delete — use lazy validation (Problem 013)

`heapq` gives push and pop-min in O(log n) and nothing else: no search, no arbitrary delete. When an entry becomes stale (a price was corrected), do not hunt for it — leave it, keep the authoritative value in a
dict, and **validate when you read the top**:

```python
prices = {}                                   # timestamp -> price: the source of truth
max_heap, min_heap = [], []                   # (-price, ts) and (price, ts): may contain stale entries
def update(ts, p):
    prices[ts] = p; heapq.heappush(max_heap, (-p, ts)); heapq.heappush(min_heap, (p, ts))
def maximum():
    while prices[max_heap[0][1]] != -max_heap[0][0]: heapq.heappop(max_heap)   # discard corrected-away entries
    return -max_heap[0][0]
```

Each entry is pushed once and popped at most once, so the total cost stays O(log n) amortised per update. The alternative — `list.remove` plus `heapify` — is O(n) per correction (Problem 013's fourth trap). Max-heaps are
done by negating the key. `bisect` is the other workhorse: since Python 3.10 it takes `key=`, so `bisect.bisect_right(h, snap_id, key=lambda e: e[0])` searches a list of `(snap_id, value)` pairs directly — the last entry at or before
`snap_id` is `h[i - 1]` (Problem 012), and `i == 0` means "no value yet".

### 7.4 What the ring buffer buys (Problem 011)

A queue of timestamps costs memory proportional to the *hits*; a ring of 300 time-tagged buckets costs memory proportional to the *window* (300 slots), whatever the hit rate. The tag matters: a slot is reused every 300
seconds, so a read must check that the slot's stored second is inside `(t − 300, t]`, otherwise last cycle's count leaks in (the second documented trap). The solution file measured the difference on one million hits in one window: about
39 MiB for the queue against about 18 KiB for the buckets.

---
<!-- /block:25_py_1_blocks -->

<!-- block:25_py_2_beyond -->
## Part 8 · Beyond the Thirteen — Rate Limiters, Duplicates in RandomizedSet, TimeMap, TicTacToe, and Testing a Design Class

The classic design questions that *follow* these thirteen reuse the same moves. Each snippet below was run and checked against a brute-force reference.

### 8.1 Rate limiters: the same "next allowed time" idea, four ways

Problem 003 stores the next allowed time per message. Rate limiters for *counts* have four standard designs; the trade-off is memory against accuracy at window edges:

```python
class FixedWindow:                       # O(1) memory: one counter per window
    def __init__(self, limit, size): self.l, self.s, self.w, self.c = limit, size, None, 0
    def allow(self, t):
        w = t // self.s
        if w != self.w: self.w, self.c = w, 0
        if self.c < self.l: self.c += 1; return True
        return False

class SlidingLog:                        # exact, but O(limit) memory per key
    def __init__(self, limit, size): self.l, self.s, self.q = limit, size, deque()
    def allow(self, t):
        while self.q and self.q[0] <= t - self.s: self.q.popleft()
        if len(self.q) < self.l: self.q.append(t); return True
        return False

class TokenBucket:                       # allows bursts up to `cap`, average rate `rate`
    def __init__(self, rate, cap): self.rate, self.cap, self.tok, self.last = rate, cap, cap, 0.0
    def allow(self, t):
        self.tok = min(self.cap, self.tok + (t - self.last) * self.rate); self.last = t
        if self.tok >= 1: self.tok -= 1; return True
        return False
```

Measured with a limit of 5 per 10 seconds, five requests at `t = 9` then five at `t = 10`: the **fixed window allowed all 10** (two different windows, so two fresh counters — twice the limit in two seconds),
the sliding log allowed 5. A token bucket of rate 0.5/s and capacity 5 allowed a burst of 5 out of 8 simultaneous requests, and two more after 4 seconds (two tokens refilled). A *sliding-window counter* (weight the previous window by the
overlap) approximates the log in O(1) memory. The hit counter (Problem 011) is the same counting problem with a ring of buckets.

### 8.2 RandomizedCollection: duplicates (LC 381)

With duplicates a value maps to a *set of indices*, and swap-with-last must move one index between sets:

```python
class RSDup:
    def __init__(self): self.a, self.pos = [], defaultdict(set)
    def insert(self, v):
        self.pos[v].add(len(self.a)); self.a.append(v); return len(self.pos[v]) == 1     # True if v was new
    def remove(self, v):
        if not self.pos.get(v): return False
        i = self.pos[v].pop(); last = self.a[-1]
        self.a[i] = last
        if i != len(self.a) - 1:                       # the last element moves into slot i
            self.pos[last].discard(len(self.a) - 1); self.pos[last].add(i)
        self.a.pop()
        if not self.pos[v]: del self.pos[v]
        return True
```

The `i != len(self.a) - 1` guard covers removing the last slot itself (nothing moves). It kept every set of indices consistent with the array on 500 random sequences. `getRandom` stays `random.choice(self.a)`, so a value with two copies is twice as likely — which is what the problem asks.

### 8.3 TimeMap (LC 981) and Tic-Tac-Toe (LC 348)

```python
class TimeMap:                                   # values arrive with increasing timestamps
    def __init__(self): self.d = defaultdict(list)
    def set(self, k, v, t): self.d[k].append((t, v))
    def get(self, k, t):
        h = self.d.get(k, [])
        i = bisect.bisect_right(h, (t, chr(0x10ffff)))     # first entry with timestamp > t (the sentinel value wins ties)
        return h[i - 1][1] if i else ''

class TicTacToe:                                 # O(1) per move: a running sum per row, column and diagonal
    def __init__(self, n): self.n, self.rows, self.cols, self.d, self.a = n, [0] * n, [0] * n, 0, 0
    def move(self, r, c, p):
        s = 1 if p == 1 else -1
        self.rows[r] += s; self.cols[c] += s
        if r == c: self.d += s
        if r + c == self.n - 1: self.a += s
        return p if self.n in (abs(self.rows[r]), abs(self.cols[c]), abs(self.d), abs(self.a)) else 0
```

`TimeMap` returned `'bar'` for `get('foo', 1)` and `get('foo', 3)` after `set('foo','bar',1)`, `''` for `get('foo', 0)`, and matched a reference on 500 random sequences. `TicTacToe` matched a full-board win check on 600 random games (sizes 2–4).
Both are the same pattern as the thirteen: pick the structure that makes the *query* cheap (a sorted history you can bisect; a sum you can update).

### 8.4 Testing a design class: differential testing

Design bugs are ordering bugs (Part 4, step 5), and they hide from hand-picked examples. Run the class and a slow obviously-correct reference side by side on random operation sequences, and compare after **every** operation:

```python
def diff_test(cls, trials=500, ops=40):
    caught = 0
    for _ in range(trials):
        s, ref = cls(), set(); ok = True
        try:
            for _ in range(ops):
                v = random.randrange(8)                       # a small key space forces collisions and removals
                if random.random() < .5:
                    if s.insert(v) == (v in ref): ok = False
                    ref.add(v)
                else:
                    if s.remove(v) != (v in ref): ok = False
                    ref.discard(v)
                if sorted(s.a) != sorted(ref): ok = False     # the internal array must match the reference set
        except Exception: ok = False
        caught += (not ok)
    return caught
```

On 500 random 40-operation sequences the correct `RandomizedSet` was flagged **0** times and a version that forgot to update the moved element's index (`self.pos[last] = i`) was flagged **445** times — usually through an `IndexError` or `KeyError` a few
operations later, not at the faulty line. Keeping the key space tiny (8 values) is what makes duplicates and removals of the *last* slot common.

### 8.5 Thread-safety: the GIL does not make check-then-act atomic

Every structure in this topic assumes one thread. Shared between threads, an `OrderedDict` LRU with `if k not in d: return -1; d.move_to_end(k)` has a window between the check and the act. With the switch interval lowered
(`sys.setswitchinterval(1e-6)`) and 4 threads doing 100,000 random gets and puts each on a capacity-10 cache, the unsynchronised class raised **288 `KeyError`s** (another thread evicted the key between the check and `move_to_end`). Guard each
public method with one `threading.Lock`. (A plain `d['n'] += 1` did *not* lose updates in the same experiment — CPython only switches threads at certain instructions, so single statements are often accidentally atomic. That is an implementation detail, not a
guarantee, and it does not extend to check-then-act.)

### 8.6 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Make the LRU thread-safe." | One lock around every method (each one reorders); `RLock` only if methods call each other. |
| "LRU with a time-to-live." | Store an expiry per entry; expire lazily on `get`, plus a heap or the LRU order to sweep. |
| "Hit counter for millions of hits per second." | The ring of buckets (memory fixed per window); shard by key for very high rates. |
| "Snapshot array with millions of snaps." | Per-index history + `bisect` — memory grows with *changes*, not with `length × snaps`. |
| "Rate limit per user." | A dict from user to a limiter; evict idle users (an LRU of limiters). |
| "`getRandom` must be weighted." | Prefix sums + `bisect` (topic 27). |

---
<!-- /block:25_py_2_beyond -->

<!-- problem-map:start -->
## Part 9 · Every Problem in This Topic, by Pattern

Thirteen problems, one move: pair a source of truth with the index each operation needs, and keep both in sync on every mutation. Each **Trap** is a mistake documented in that problem's solution file.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Design HashSet](PyDSA/25_design/001_design_hashset_solution.py) <br>LC 705 · Easy | Bucket array with chaining | `key % buckets` picks a bucket; scan the short chain; `add` checks for the key first. **Trap:** one bucket (an O(n) list in disguise); a round bucket count with structured keys (1,000 keys in one chain — measured); appending a duplicate; treating key `0` as falsy; clearing a slot in open addressing without a tombstone. |
| [002 · Design HashMap](PyDSA/25_design/002_design_hashmap_solution.py) <br>LC 706 · Easy | The same, storing pairs | Buckets hold `(key, value)`; `put` overwrites an existing key. **Trap:** appending a second pair for an existing key; `0` as the not-found sentinel (use `-1`); leaving a `[key, None]` ghost after `remove`. |
| [003 · Logger Rate Limiter](PyDSA/25_design/003_logger_rate_limiter_solution.py) <br>LC 359 · Easy | Store the next allowed time | `next_allowed.get(msg, ts) <= ts` → allow and store `ts + 10`. **Trap:** `<=` instead of `<` on the suppress test (exactly `t + 10` must be allowed); a separate first-seen branch that forgets the write; assuming unique timestamps; evicting old entries nobody asked about. |
| [004 · Design Linked List](PyDSA/25_design/004_design_linked_list_solution.py) <br>LC 707 · Medium | Dummy head and tail, walk from the nearer end | Sentinels remove every empty-list branch; `size` decides which end to start from. **Trap:** the three `addAtIndex` boundaries (`< 0`, `== size`, `> size`); a stale `size`; always walking from the head; special-casing `head is None`; walking to a node at `index == size`. |
| [005 · Insert Delete GetRandom O(1)](PyDSA/25_design/005_insert_delete_getrandom_o1_solution.py) <br>LC 380 · Medium | Array + value→index map, swap-pop | Swap the target with the last element, fix the moved element's index, pop. **Trap:** `pop(i)` on a middle index (O(n)); not updating `index[last]`; deleting `index[val]` before reading it; tombstones (non-uniform `getRandom`); a non-uniform pick. |
| [006 · Design Browser History](PyDSA/25_design/006_design_browser_history_solution.py) <br>LC 1472 · Medium | Array + cursor | `visit` truncates to `cursor + 1` then appends; `back`/`forward` clamp. **Trap:** appending without truncating; `del history[cursor:]` (deletes the current page too); not clamping (Python's negative index wraps silently); a linked list out of habit; forgetting the homepage is entry 0. |
| [007 · Design Snake Game](PyDSA/25_design/007_design_snake_game_solution.py) <br>LC 353 · Medium | Deque + set, tail leaves first | Free the tail from both structures *before* the collision test, unless food was just eaten. **Trap:** testing collision before removing the tail (wrong in 133 of 3,000 random games on boards up to 4 × 4 — measured); a set with no order; list-vs-tuple comparison; `food_index` past the end; mutating before the bounds check. |
| [008 · LFU Cache](PyDSA/25_design/008_lfu_cache_solution.py) <br>LC 460 · Hard | A list per frequency + `min_freq` | `get`/`put` on an existing key bump its frequency; `min_freq` advances only when the emptied bucket *was* the minimum; a new key resets it to 1. **Trap:** `put` on an existing key not bumping; advancing `min_freq` on any empty bucket; assuming it is always the true minimum; a plain list per bucket (`remove` is O(n)). |
| [009 · Design In-Memory File System](PyDSA/25_design/009_design_in_memory_file_system_solution.py) <br>LC 588 · Hard | A tree of named children | One walk helper (`create=True/False`); an explicit `is_file` flag; sort `ls`. **Trap:** not filtering the empty first segment of `"/a/b".split('/')`; `ls` of a file returning `[]`; overwriting instead of appending; the wrong parent path for a top-level file; `children = None` as the file marker; unsorted `ls`. |
| [010 · Design Search Autocomplete System](PyDSA/25_design/010_design_search_autocomplete_system_solution.py) <br>LC 642 · Hard | Trie with a per-node ranking index | Every node on a sentence's path stores `sentence → hot`; persistent `buffer` and `node` state; rank by `(-hot, sentence)`. **Trap:** treating each `input` as stateless; resurrecting matches after `node` became `None`; no lexicographic tiebreak; resetting before saving on `'#'`; recording hot only at the terminal node. |
| [011 · Design Hit Counter](PyDSA/25_design/011_design_hit_counter_solution.py) <br>LC 362 · Medium | A ring of 300 time-tagged buckets | Slot `t % 300` holds `(second, count)`; reuse resets it; read only slots within `(t - 300, t]`. **Trap:** `t - s <= 300` (off by one); not checking the slot's second on read; clearing all 300 buckets per call; ignoring the high-rate follow-up. |
| [012 · Snapshot Array](PyDSA/25_design/012_snapshot_array_solution.py) <br>LC 1146 · Medium | Per-index history + bisect | Append `(snap_id, value)` (overwrite within the same snap); `get` finds the last entry with `snap <= id`. **Trap:** copying the array per snap; `bisect_left` landing on the first value of a snap; writing under `snap_id - 1`; indexing `history[i][-1]` for an untouched index. |
| [013 · Stock Price Fluctuation](PyDSA/25_design/013_stock_price_fluctuation_solution.py) <br>LC 2034 · Medium | Source-of-truth map + two lazy heaps | Update the map and push to both heaps; `maximum()`/`minimum()` pop entries whose price no longer matches the map; `current` is the price at the largest timestamp. **Trap:** heaps without validation (returns a corrected-away price); `current` from the last *call* rather than the largest timestamp; a Counter validity check never decremented; `list.remove` + `heapify` (O(n)). |

---
<!-- problem-map:end -->


## Checklist Before Leaving This Topic <!--ca-->

- [ ] Choose a bucket count deliberately and reproduce the failure: multiples of 1,000 into 1,000 buckets give a chain of 1,000 <!--ca-->
- [ ] Build an LRU with `OrderedDict` (`move_to_end`, `popitem(last=False)`) and by hand with a doubly linked list, and say which you would ship <!--ca-->
- [ ] Use lazy validation for a heap whose entries can go stale, and say why `list.remove` + `heapify` is the wrong repair <!--ca-->
- [ ] Use `bisect` (with `key=` on 3.10+) for versioned history, and handle "no entry yet" <!--ca-->
- [ ] State the four rate-limiter designs and show the fixed-window boundary burst (10 allowed for a limit of 5) <!--ca-->
- [ ] Extend RandomizedSet to duplicates with a set of indices per value <!--ca-->
- [ ] Differential-test a design class against a brute-force reference after every operation <!--ca-->
- [ ] Explain why the GIL does not make check-then-act atomic, and where the lock goes <!--ca-->
